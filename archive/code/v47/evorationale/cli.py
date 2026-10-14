"""EvoRationale command-line workflows with reproducible outputs and explicit modes."""
from __future__ import annotations
import argparse
import hashlib
import json
import os
from pathlib import Path
from typing import Any

from .agent import EvoRationaleAgent
from .planning import OpenAIQueryPlanner
from .analysis import OpenAIActionPlanner
from .budget import Budget
from .formal import AlloyAnalyzer, NoAlloy
from .github import GitHubClient, normalize_github_export
from .linking import ExplicitTextLinker, OpenAILinker
from .memory import FileMemory, MongoMemory
from .retrieval import LocalHybridRetriever, ElasticsearchHybridRetriever, BgeM3Embedder
from .state_builder import approve_draft, draft_from_anchor
from .verification import EvidenceVerifier, ExplicitCueJudge, OpenAISemanticJudge
from .model import validate_state, normalize_history


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def sha256_file(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def audit_snapshot_provenance(history: list[dict[str, Any]]) -> dict[str, Any]:
    """Describe data eligibility separately from historical replay suitability.

    A current API capture of an edited PR body is an auditable *present*
    version, not automatically proof of what that body said in 2025.
    This diagnostic makes no claims about completeness of repository search.
    """
    total=len(history)
    categories={"explicitly_historical_safe":0,"explicitly_unsafe":0,"unknown":0}
    current_snapshots=0
    truncated=0
    for item in history:
        metadata=item.get("metadata") if isinstance(item.get("metadata"),dict) else {}
        status=metadata.get("historical_replay_safe")
        if status is True: categories["explicitly_historical_safe"]+=1
        elif status is False: categories["explicitly_unsafe"]+=1
        else: categories["unknown"]+=1
        if str(metadata.get("source_kind","")).startswith("CURRENT_"):
            current_snapshots+=1
        if metadata.get("excerpt_truncated") is True: truncated+=1
    return {
        "artifact_versions":total,
        "source_version_categories":categories,
        "current_snapshot_bodies":current_snapshots,
        "truncated_source_records":truncated,
        "complete_repository_history_established":False,
        "independently_adjudicated_ground_truth_available":False,
        "historical_replay_certified":total>0 and categories["explicitly_historical_safe"]==total,
        "warning":"This input is a bounded snapshot; a valid current source hash does not establish historical body availability or decision correctness.",
    }



def build_agent(args: argparse.Namespace) -> EvoRationaleAgent:
    profile = getattr(args, "investigation_profile", "targeted")
    event_profile = profile in {"event-complete", "event-delta", "event-evidence", "event-grounded"}
    nomination_mode = getattr(args, "delta_nomination", "none")
    if nomination_mode not in {"none", "model"}:
        raise RuntimeError("Unknown delta nomination mode")
    if nomination_mode == "model" and profile != "event-delta":
        raise RuntimeError("--delta-nomination model requires the event-delta profile")
    output_limit = getattr(args, "max_output_tokens", None)
    if not event_profile and output_limit is not None:
        raise RuntimeError("--max-output-tokens is supported only by the event-complete profile, the event-delta profile, the event-evidence profile or the event-grounded profile")
    if output_limit is None:
        output_limit = 16384 if event_profile else 4096
    budget = Budget(max_rounds=args.max_rounds, max_queries=args.max_queries,
                    max_artifact_reads=args.max_reads, max_input_tokens=args.max_input_tokens,
                    max_output_tokens=output_limit)
    if event_profile:
        if args.mode != "api" or args.backend != "local":
            raise RuntimeError(f"{profile} requires API mode and the local immutable-history backend")
        if not getattr(args, "allow_repository_text_to_api", False):
            raise RuntimeError("API mode requires explicit --allow-repository-text-to-api consent")
        model = args.model or os.getenv("OPENAI_MODEL")
        judge_model = args.judge_model or os.getenv("OPENAI_JUDGE_MODEL")
        if not model or not judge_model or not os.getenv("OPENAI_API_KEY"):
            raise RuntimeError("API mode requires OPENAI_API_KEY, model and a separately configured judge model")
        from .event_agent import EventReviewAgent
        from .event_linking import EventLinker
        from .event_verification import EventSemanticJudge
        if profile == "event-grounded":
            from .delta_linking import NoNomination
            from .grounded_trace_verification import GroundedTraceSemanticJudge
            linker, judge = NoNomination(), GroundedTraceSemanticJudge(judge_model)
        elif profile == "event-evidence":
            from .delta_linking import NoNomination
            from .evidence_trace_verification import EvidenceTraceSemanticJudge
            linker, judge = NoNomination(), EvidenceTraceSemanticJudge(judge_model)
        elif profile == "event-delta":
            from .delta_linking import DeltaLinker, NoNomination
            from .delta_verification import DeltaSemanticJudge
            linker = DeltaLinker(model) if nomination_mode == "model" else NoNomination()
            judge = DeltaSemanticJudge(judge_model)
        else:
            linker, judge = EventLinker(model), EventSemanticJudge(judge_model)
        event_store = (MongoMemory(os.getenv("MONGODB_URI", "mongodb://localhost:27017"),
                                   os.getenv("MONGODB_DATABASE", "evorationale"))
                       if args.memory == "mongo" else FileMemory(args.memory_dir))
        return EventReviewAgent(linker=linker, judge=judge, profile=profile,
                                store=event_store, budget=budget,
                                formal_analyzer=AlloyAnalyzer(args.alloy_jar) if args.alloy_jar else NoAlloy())
    if args.mode == "offline":
        linker, judge, embedder = ExplicitTextLinker(), ExplicitCueJudge(), None
    else:
        if not getattr(args,"allow_repository_text_to_api",False):
            raise RuntimeError("API mode requires explicit --allow-repository-text-to-api consent")
        model = args.model or os.getenv("OPENAI_MODEL")
        judge_model = args.judge_model or os.getenv("OPENAI_JUDGE_MODEL")
        if not model or not judge_model or not os.getenv("OPENAI_API_KEY"):
            raise RuntimeError("API mode requires OPENAI_API_KEY, model and a separately configured judge model")
        linker, judge = OpenAILinker(model), OpenAISemanticJudge(judge_model)
        embedder = None
        if args.embedding_revision:
            embedder = BgeM3Embedder(args.embedding_revision)
    if args.backend == "elasticsearch":
        if not embedder:
            raise RuntimeError("Elasticsearch backend requires pinned BGE-M3 embedding revision")
        retriever = ElasticsearchHybridRetriever(os.getenv("ELASTICSEARCH_URL", "http://localhost:9200"),
                                                 os.getenv("ELASTICSEARCH_INDEX", "evorationale-versions-v2"), embedder)
    else:
        retriever = LocalHybridRetriever(embedder)
    store = (MongoMemory(os.getenv("MONGODB_URI", "mongodb://localhost:27017"),
                         os.getenv("MONGODB_DATABASE", "evorationale"))
             if args.memory == "mongo" else FileMemory(args.memory_dir))
    formal = AlloyAnalyzer(args.alloy_jar) if args.alloy_jar else NoAlloy()
    planner = (OpenAIQueryPlanner(model, budget) if args.mode == "api" else None)
    action_planner = (OpenAIActionPlanner(model, budget=budget) if args.mode == "api" else None)
    return EvoRationaleAgent(retriever=retriever, linker=linker,
                             evidence_verifier=EvidenceVerifier(judge),
                             store=store, formal_analyzer=formal, budget=budget,
                             planner=planner, action_planner=action_planner)


def main() -> None:
    parser = argparse.ArgumentParser(prog="evorationale", description="Auditable decision-centered software architecture revalidation")
    subs = parser.add_subparsers(required=True, dest="command")
    demo = subs.add_parser("demo", help="Run the offline Redis example with full report and manifest")
    demo.add_argument("--output", type=Path, default=Path("outputs/demo"))
    run = subs.add_parser("run", help="Run on approved S0 and immutable archived artifacts")
    run.add_argument("--decision", required=True, type=Path)
    run.add_argument("--history", required=True, type=Path)
    run.add_argument("--output", required=True, type=Path)
    run.add_argument("--mode", choices=["offline", "api"], default="offline")
    run.add_argument("--investigation-profile", choices=["targeted", "event-complete", "event-delta", "event-evidence", "event-grounded"], default="targeted",
                     help="Opt-in complete artifact review using source-owned event context")
    run.add_argument("--delta-nomination", choices=["none", "model"], default="none",
                     help="Event-delta optional target nomination audit; default none saves unused provider work")
    run.add_argument("--allow-repository-text-to-api", action="store_true", help="Explicit permission required for hosted-model mode")
    run.add_argument("--backend", choices=["local", "elasticsearch"], default="local")
    run.add_argument("--memory", choices=["file", "mongo"], default="file")
    run.add_argument("--memory-dir", type=Path, default=Path("outputs/checkpoints"))
    run.add_argument("--model", default="")
    run.add_argument("--judge-model", default="")
    run.add_argument("--embedding-revision", default="", help="Pinned BGE-M3 model revision")
    run.add_argument("--alloy-jar", default="", help="Path to Alloy 6.2 distribution JAR")
    run.add_argument("--max-rounds", type=int, default=3)
    run.add_argument("--max-queries", type=int, default=12)
    run.add_argument("--max-reads", type=int, default=24)
    run.add_argument("--max-input-tokens", type=int, default=64_000)
    run.add_argument("--max-output-tokens", type=int, default=None,
                     help="Event review per-request output ceiling; default 16384")
    val = subs.add_parser("validate", help="Validate decision and exact-version artifact records")
    val.add_argument("--decision", type=Path, required=True)
    val.add_argument("--history", type=Path, required=True)
    draft = subs.add_parser("draft-state", help="Generate unapproved S0 from section-labeled ADR")
    draft.add_argument("--anchor", required=True, type=Path)
    draft.add_argument("--cutoff", required=True)
    draft.add_argument("--episode-id", required=True)
    draft.add_argument("--output", required=True, type=Path)
    appr = subs.add_parser("approve-state", help="Human-operated approval, after source review")
    appr.add_argument("--draft", type=Path, required=True)
    appr.add_argument("--central-ids", required=True, nargs="+")
    appr.add_argument("--output", type=Path, required=True)
    gh = subs.add_parser("ingest-github", help="Capture current snapshot; does NOT reconstruct prior versions")
    gh.add_argument("--repo", required=True)
    gh.add_argument("--output", required=True, type=Path)
    imp = subs.add_parser("import-github-export", help="Normalize already captured GitHub JSON export")
    imp.add_argument("--repo", required=True)
    imp.add_argument("--json", required=True, type=Path)
    imp.add_argument("--captured-at", required=True)
    imp.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    if args.command == "demo":
        here = Path(__file__).resolve().parent.parent
        state = here / "examples/redis/decision_state.json"
        history = here / "examples/redis/history.jsonl"
        args = argparse.Namespace(**{**vars(args), "mode": "offline", "backend": "local",
          "memory": "file", "memory_dir": args.output / "checkpoints", "model": "", "judge_model": "",
          "embedding_revision": "", "alloy_jar": "", "max_rounds": 3,
          "max_queries": 12, "max_reads": 24, "max_input_tokens": 64_000,
          "decision": state, "history": history})
        _run(args)
    elif args.command == "run":
        _run(args)
    elif args.command == "validate":
        s = validate_state(read_json(args.decision))
        h = normalize_history(read_jsonl(args.history))
        print(json.dumps({"status": "PASS", "repository": s["repository"],
                          "artifact_versions": len(h)}, indent=2))
    elif args.command == "draft-state":
        write_json(args.output, draft_from_anchor(read_json(args.anchor), args.cutoff, args.episode_id))
    elif args.command == "approve-state":
        write_json(args.output, approve_draft(read_json(args.draft), args.central_ids))
    elif args.command in {"ingest-github", "import-github-export"}:
        if args.command == "ingest-github":
            rows = GitHubClient().capture(args.repo)
        else:
            rows = normalize_github_export(args.repo, read_json(args.json), args.captured_at)
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text("".join(json.dumps(x, ensure_ascii=False, sort_keys=True) + "\n" for x in rows), encoding="utf-8")
        print(json.dumps({"versions": len(rows), "output": str(args.output)}, indent=2))


def _run(args: argparse.Namespace) -> None:
    state = read_json(args.decision)
    history = read_jsonl(args.history)
    # Check inputs and destination before constructing a hosted agent or doing
    # any paid work. The development wrappers already guard experiment paths;
    # direct CLI users need the same protection for their existing reports.
    validate_state(state)
    normalize_history(history)
    out = args.output
    if out.exists() and not out.is_dir():
        raise FileExistsError("Run output must be a directory: " + str(out))
    names = ("report.json", "trace.json", "data_audit.json", "manifest.json")
    if any((out / name).exists() for name in names):
        raise FileExistsError("Run output already contains experiment files; choose a new directory: " + str(out))
    out.mkdir(parents=True, exist_ok=True)
    agent = build_agent(args)
    run = agent.run(state, history)
    def write_run_json(name: str, data: Any) -> None:
        # Exclusive writes also protect a destination changed concurrently
        # after the preflight. Other CLI workflows retain their existing API.
        with (out / name).open("x", encoding="utf-8") as output:
            output.write(json.dumps(data, ensure_ascii=False, indent=2, sort_keys=True) + "\n")
    write_run_json("report.json", run.report)
    write_run_json("trace.json", run.trace)
    # Preserve a separate, independently calculable input-data warning.
    audit = audit_snapshot_provenance(history)
    write_run_json("data_audit.json", audit)
    write_run_json("manifest.json", {
        "run_id": run.run_id, "status": run.status,
        "mode": args.mode, "retrieval_backend": args.backend,
        "investigation_profile": getattr(args, "investigation_profile", "targeted"),
        "nomination_mode": getattr(args, "delta_nomination", "none")
                           if getattr(args, "investigation_profile", "targeted") in {"event-delta", "event-evidence", "event-grounded"} else "not_applicable",
        "data_audit_sha256": sha256_file(out / "data_audit.json"),
        "historical_replay_certified": audit["historical_replay_certified"],
        "decision_sha256": sha256_file(args.decision),
        "history_sha256": sha256_file(args.history),
        "report_sha256": sha256_file(out / "report.json"),
        "disclosure": ("DETERMINISTIC EXTRACTIVE DEMONSTRATOR, NOT SANER STUDY RESULTS"
                       if args.mode == "offline" else "MODEL-ASSISTED OUTPUT REQUIRES HUMAN AUDIT"),
    })
    print(json.dumps({"run_id": run.run_id, "status": run.status,
                      "outcome": run.report["recommended_outcome"],
                      "verification": run.report["verification"]["status"],
                      "output": str(out / "report.json")}, indent=2))


if __name__ == "__main__":
    main()

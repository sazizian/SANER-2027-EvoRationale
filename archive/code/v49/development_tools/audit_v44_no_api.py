#!/usr/bin/env python3
"""Replay source selection and synthetic request envelopes without a provider.

The CLI reads only a prepared evaluation's two unlabeled inputs and preparation
manifest. It imports no provider SDK, reads no reference labels, and never makes
a network call. Fake replies are transport fixtures, not semantic assessments.
An estimate for one candidate per selected artifact is a scenario, not a token
upper bound, an F1 prediction, a provider price, or a promise of run completion.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import sys
from types import SimpleNamespace
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from evorationale.budget import Budget
from evorationale.diff_context import DIFF_SOURCE_TYPES, _lines
from evorationale.event_context import (
    event_context_view, exact_event_passages, quotable_event_passages, redact_event_source,
    select_event_batches,
)
from evorationale.event_linking import EventLinker
from evorationale.event_verification import EventSemanticJudge
from evorationale.model import artifact_key, eligible, normalize_history, validate_state
from evorationale.redaction import redact

DECISION_NAME = "S0_RETROSPECTIVE_RUNTIME.json"
HISTORY_NAME = "POST_S0_EVIDENCE_RETROSPECTIVE_53.jsonl"
_REASON = "SYNTHETIC TRANSPORT FIXTURE: no source relation has been assessed."


def _sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


class _FakeResponses:
    """Local object with the same callable surface; no SDK or network access."""

    def __init__(self) -> None:
        self.requests: list[dict[str, Any]] = []

    def create(self, **request: Any) -> SimpleNamespace:
        self.requests.append(request)
        payload = json.loads(request["input"])
        if "artifacts" in payload:
            ids = [e["id"] for e in payload["decision_state"]["elements"]]
            rows = []
            for artifact in payload["artifacts"]:
                passages = artifact["passages"]
                # An arbitrary relation and arbitrary first target exercise the
                # request path. They never assert a real relationship.
                links = ([{"passage_handle": passages[0]["passage_handle"],
                           "element_id": ids[0], "relation": "supersedes",
                           "confidence": 0.5}] if passages else [])
                rows.append({"artifact_handle": artifact["artifact_handle"],
                             "considered_element_ids": ids,
                             "status": "relation_found" if links else "insufficient_evidence",
                             "reason": _REASON, "links": links})
            result = {"reviews": rows}
        else:
            result = {"decisions": [{
                "proposal_id": proposal["proposal_id"], "reason": _REASON,
                "affected_subclaim": "SYNTHETIC FIXTURE ONLY",
                "claim_scope": "material_subclaim", "source_role": "unknown",
                "supported": False, "whole_element_supported": False,
                "scope_match": False, "replacement_is_explicit": False,
                "material_change": False, "surviving_clause_masks_replacement": False,
            } for proposal in payload["proposals"]]}
        return SimpleNamespace(status="completed", output_text=json.dumps(result))


def audit_sources(state_input: dict[str, Any], history_input: list[dict[str, Any]],
                  models: dict[str, str], budgets: dict[str, int], *,
                  require_approved: bool = True) -> dict[str, Any]:
    """Structural audit; require_approved=False is for offline source fixtures.

    The input approval flag is never set or modified. The public CLI always
    requires an approved runtime state. No fake result enters an evaluation.
    """
    if (not isinstance(models, dict) or set(models) != {"linker", "judge"}
            or any(not isinstance(v, str) or not v.strip() for v in models.values())):
        raise ValueError("Expected explicit opaque linker and judge model IDs")
    names = ("max_rounds", "max_queries", "max_reads", "max_input_tokens")
    if any(type(budgets.get(n)) is not int or budgets[n] < 1 for n in names):
        raise ValueError("Expected positive integer evaluation budgets")
    state = validate_state(state_input, require_approved=require_approved)
    history = normalize_history(history_input)
    allowed = [a for a in history if eligible(state, a)]
    selected = select_event_batches(state, history, budgets["max_reads"])
    active = selected[:min(budgets["max_rounds"], budgets["max_queries"])]
    fake = _FakeResponses()
    client = SimpleNamespace(responses=fake)
    linker = EventLinker(models["linker"], client=client)
    judge = EventSemanticJudge(models["judge"], client=client)
    rows = []
    envelopes = []
    cumulative = 0
    first_unaffordable = None
    reviewed_keys = set()
    for number, batch in enumerate(active, 1):
        context = event_context_view(batch)
        raw_passages = {artifact_key(a): exact_event_passages(a) for a in batch}
        safe_catalogs = {artifact_key(a): quotable_event_passages(a) for a in batch}
        safe_passages = {key: quotes for key, (quotes, _) in safe_catalogs.items()}
        changed = []
        for artifact in batch:
            passages = raw_passages[artifact_key(artifact)]
            if not all(p in artifact["content"] and len(p) <= 650 for p in passages):
                raise ValueError("Non-exact or oversized source-owned citation window")
            if not all(p in artifact["content"] and len(p) <= 650
                       and redact(p, max_chars=len(p)) == p
                       for p in safe_passages[artifact_key(artifact)]):
                raise ValueError("Unsafe or non-exact outbound citation window")
            if artifact["source_type"] in DIFF_SOURCE_TYPES:
                # Use the same canonical role parser as the runtime, preserving
                # separate occurrences without matching unchanged equal text.
                lines = [line.rstrip("\r\n") for _, _, role, line in (_lines(artifact) or [])
                         if role in {"added", "removed"}]
                covered = [line for line in lines if any(line in p for p in passages)]
                if len(covered) != len(lines):
                    raise ValueError("Source passage coverage failure: " + artifact["artifact_id"])
                safe_lines = [line for line in lines if redact(line, max_chars=len(line)) == line]
                safe_covered = [line for line in safe_lines
                                if any(line in p for p in safe_passages[artifact_key(artifact)])]
                changed.append({"artifact_id": artifact["artifact_id"],
                                "changed_source_lines": len(lines),
                                "covered_changed_source_lines": len(covered),
                                "individually_unredacted_changed_source_lines": len(safe_lines),
                                "safely_quotable_changed_source_lines": len(safe_covered),
                                "covered_safely_quotable_changed_source_lines": len(safe_covered),
                                "unquoted_individually_unredacted_changed_source_lines":
                                    len(safe_lines) - len(safe_covered),
                                "redacted_changed_source_lines": len(lines) - len(safe_lines)})
        before = len(fake.requests)
        proposals = linker.propose_event(state, batch)
        payload = json.loads(fake.requests[-1]["input"])
        by_identity = {(a["artifact_id"], a["content_sha256"]): a for a in batch}
        by_handle = {f"A{i:04d}": a for i, a in enumerate(batch, 1)}
        reconstructed_sources = {}
        for entry in payload["event_context"]["canonical_artifacts"]:
            numbered = entry["numbered_source"].splitlines(keepends=True)
            reconstructed = ""
            for index, line in enumerate(numbered, 1):
                prefix = f"{index}: "
                if not line.startswith(prefix):
                    raise ValueError("Invalid code-owned source numbering")
                reconstructed += line[len(prefix):]
            source = by_identity[(entry["artifact_id"], entry["content_sha256"])]
            if "artifact_handle" in entry:
                bound = by_handle[entry["artifact_handle"]]
                if (bound["artifact_id"], bound["content_sha256"]) != (entry["artifact_id"], entry["content_sha256"]):
                    raise ValueError("Numbered source handle differs from canonical source identity")
                source = bound
            expected = redact_event_source(source["content"])
            if reconstructed != expected:
                raise ValueError("Numbered source does not reconstruct canonical redacted source")
            reconstructed_sources[entry.get("artifact_handle", artifact_key(source))] = reconstructed
        checked_diff_ranges = 0
        for artifact_view in payload["artifacts"]:
            source = by_handle[artifact_view["artifact_handle"]]
            if artifact_view["artifact_id"] != source["artifact_id"]:
                raise ValueError("Artifact handle differs from its canonical source identity")
            source_lines = source["content"].splitlines(keepends=True)
            for passage in artifact_view["passages"]:
                start, end = passage["source_line_start"], passage["source_line_end"]
                if (type(start) is not int or type(end) is not int
                        or not 1 <= start <= end <= len(source_lines)):
                    raise ValueError("Invalid code-owned passage line range")
                if source["source_type"] in DIFF_SOURCE_TYPES:
                    visible_quote = "".join(source_lines[start - 1:end]).rstrip("\r\n")
                    if visible_quote not in safe_passages[artifact_key(source)]:
                        raise ValueError("Diff handle range differs from source-exact citation")
                    checked_diff_ranges += 1
                elif passage.get("text") not in safe_passages[artifact_key(source)]:
                    raise ValueError("Prose handle literal differs from source-exact citation")
        accepted, _ = judge.review_event(state, batch, proposals)
        if accepted:
            raise AssertionError("A synthetic audit must never accept source evidence")
        requests = fake.requests[before:]
        totals = {}
        for request in requests:
            stage = ("linker" if request["text"]["format"]["name"] == "complete_event_artifact_review"
                     else "judge")
            estimate = Budget.estimate_tokens(request)
            cumulative += estimate
            if first_unaffordable is None and cumulative > budgets["max_input_tokens"]:
                first_unaffordable = {"batch": number, "stage": stage,
                                      "cumulative_estimated_input_tokens": cumulative}
            record = {"batch": number, "stage": stage,
                      "estimated_input_tokens": estimate,
                      "cumulative_estimated_input_tokens": cumulative,
                      "max_output_tokens": request["max_output_tokens"],
                      "model": request["model"],
                      "request_sha256": _sha(json.dumps(request, sort_keys=True,
                                                        ensure_ascii=False).encode("utf-8")),
                      "includes_full_schema_and_instructions": True,
                      "mock_response_received": True}
            envelopes.append(record)
            totals[stage] = estimate
        reviewed_keys.update(artifact_key(a) for a in batch)
        rows.append({"batch": number, "artifact_ids": [a["artifact_id"] for a in batch],
                     "artifact_versions": len(batch), "source_bytes": context["source_bytes"],
                     "event_context_complete": context["complete"],
                     "source_passages": sum(len(p) for p in raw_passages.values()),
                     "safely_quotable_source_passages": sum(len(p) for p in safe_passages.values()),
                     "recovered_safe_passages": sum(p not in raw_passages[key]
                                                     for key, quotes in safe_passages.items() for p in quotes),
                     "outbound_safe_passages": sum(len(a["passages"]) for a in payload["artifacts"]),
                     "omitted_sensitive_passages": sum(omitted for _, omitted in safe_catalogs.values()),
                     "synthetic_candidates": len(proposals),
                     "numbered_source_reconstructions_checked": len(reconstructed_sources),
                     "exact_diff_handle_line_ranges_checked": checked_diff_ranges,
                     "all_source_artifacts_visible": len(payload["artifacts"]) == len(batch),
                     "all_outbound_citation_coverage_complete": all(
                         a["citation_coverage_complete"] for a in payload["artifacts"]),
                     "incomplete_outbound_citation_artifact_ids": [
                         a["artifact_id"] for a in payload["artifacts"]
                         if not a["citation_coverage_complete"]],
                     "all_s0_elements_considered": all(len(r["considered_element_ids"])
                                                         == len(payload["decision_state"]["elements"])
                                                         for r in linker.last_reviews),
                     "changed_line_coverage": changed,
                     "request_envelope_estimates": totals})
    return {
        "status": "SOURCE_ONLY_SYNTHETIC_PREFLIGHT_COMPLETED_NO_API_CALLED",
        "semantic_result_available": False, "gold_labels_read": False,
        "provider_calls": 0, "mock_transport_calls": len(fake.requests),
        "approval_mode": ("APPROVED_RUNTIME_INPUT_REQUIRED" if require_approved
                          else "UNAPPROVED_SOURCE_STRUCTURAL_FIXTURE_ONLY"),
        "input_human_approved": state_input.get("human_approved"),
        "state_approval_changed": False,
        "scenario": "ONE_ARBITRARY_SYNTHETIC_CANDIDATE_PER_ARTIFACT_WITH_SAFE_QUOTE_NO_RETRIES",
        "budget_estimator": "FULL_REQUEST_ENVELOPE_UTF8_ESTIMATE_NOT_PROVIDER_TOKENIZER_OR_PRICE",
        "models": models, "nominal_budgets": budgets,
        "eligible_artifact_versions": len(allowed), "selected_batches": len(selected),
        "round_and_query_bounded_batches": len(active),
        "structurally_reviewable_artifact_versions": len(reviewed_keys),
        "structurally_reviewable_diff_versions": sum(a["source_type"] in DIFF_SOURCE_TYPES
                                                       and artifact_key(a) in reviewed_keys for a in allowed),
        "outside_round_query_read_selection_ids": [a["artifact_id"] for a in allowed
                                                   if artifact_key(a) not in reviewed_keys],
        "scenario_estimated_input_tokens": cumulative,
        "scenario_within_nominal_estimate_budget": cumulative <= budgets["max_input_tokens"],
        "first_unaffordable_envelope_in_scenario": first_unaffordable,
        "request_envelopes": envelopes, "batches": rows,
        "limitations": [
            "Source and transport checks do not assess any real architectural relation or F1.",
            "Real proposal counts, reasoning output, provider tokenization and retries can differ.",
            "An estimate below the configured limit does not guarantee the hosted run will finish.",
            "Sensitive windows use safe source-exact subwindows where possible; canonical context is redacted.",
            "Redaction also includes URLs and email addresses; omitted lines do not prove credentials were present.",
        ],
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--evaluation", type=Path, required=True)
    parser.add_argument("--output", type=Path, help="New JSON report; existing files are never overwritten")
    args = parser.parse_args()
    evaluation = args.evaluation.resolve()
    cfg = json.loads((evaluation / "DEV_PREP_MANIFEST.json").read_text(encoding="utf-8"))
    if (cfg.get("kind") != "DEVELOPMENT_ONLY_V44_EVENT_COMPLETE_COMPARISON"
            or cfg.get("investigation_profile") != "event-complete"
            or cfg.get("gold_labels_in_agent_inputs") is not False):
        raise ValueError("Expected a prepared v4.4 unlabeled event-complete evaluation")
    decision_bytes = (evaluation / "inputs" / DECISION_NAME).read_bytes()
    history_bytes = (evaluation / "inputs" / HISTORY_NAME).read_bytes()
    if (_sha(decision_bytes) != cfg.get("runtime_s0_sha256")
            or _sha(history_bytes) != cfg.get("history_sha256")):
        raise ValueError("Prepared input digests do not match; no audit performed")
    report = audit_sources(json.loads(decision_bytes),
                           [json.loads(line) for line in history_bytes.decode("utf-8").splitlines() if line.strip()],
                           cfg["models"], cfg["budgets"])
    report["input_sha256"] = {"runtime_s0": _sha(decision_bytes), "history": _sha(history_bytes)}
    rendered = json.dumps(report, indent=2, ensure_ascii=False, sort_keys=True) + "\n"
    if args.output is None:
        print(rendered, end="")
    else:
        target = args.output.resolve()
        target.parent.mkdir(parents=True, exist_ok=True)
        with target.open("x", encoding="utf-8") as output:
            output.write(rendered)
        print(json.dumps({"status": report["status"], "output": str(target),
                          "scenario_estimated_input_tokens": report["scenario_estimated_input_tokens"],
                          "scenario_within_nominal_estimate_budget": report["scenario_within_nominal_estimate_budget"]}, indent=2))


if __name__ == "__main__":
    main()

"""Offline preparation/scoring integration with synthetic hashed fixtures.

No provider is contacted. Completed-run receipts below are explicitly simulated
test data; their scores are not experimental results.
"""
import csv
import hashlib
import json
from pathlib import Path
import subprocess
import sys

import pytest

ROOT = Path(__file__).resolve().parent.parent
DECISION = "S0_RETROSPECTIVE_RUNTIME.json"
HISTORY = "POST_S0_EVIDENCE_RETROSPECTIVE_53.jsonl"
PARENT_HASH = "ab892cc339348fc6db243ecbdb18cb6df3a4959d5636332d5f2cdb7945fbdd09"


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, sort_keys=True), encoding="utf-8")


def command(script, args):
    if script == "prepare_v43.py":
        # Exercise legacy preparation against this synthetic fixture source. The
        # production helper must keep its real v4.3 package hash pin unchanged.
        wrapper = (f"import sys; sys.path.insert(0, {str(ROOT/'development_tools')!r}); "
                   "import prepare_v43; from _score_core import code_tree_hash; "
                   f"prepare_v43.EXPECTED_V43_CODE_SHA256 = code_tree_hash({str(ROOT)!r}); "
                   "prepare_v43.main()")
        return subprocess.run([sys.executable, "-c", wrapper, *map(str, args)],
                              cwd=ROOT, capture_output=True, text=True)
    return subprocess.run([sys.executable, str(ROOT/"development_tools"/script), *map(str, args)],
                          cwd=ROOT, capture_output=True, text=True)


@pytest.fixture
def prepared_inputs(tmp_path, approved_state):
    api, offline, frozen, parent, evaluation = [tmp_path/name for name in
                                               ("api41", "offline41", "frozen", "parent42", "evaluation43")]
    write(frozen/"S0_ATOMIC_REVIEWER_CONFIRMED.json", approved_state)
    ref = frozen/"reference"/"HUNK_RELATIONS_CANDIDATE.csv"
    ref.parent.mkdir(parents=True)
    with ref.open("w", newline="", encoding="utf-8") as out:
        writer = csv.DictWriter(out, fieldnames=["hunk_id", "relation_candidate", "related_atomic_s0_ids",
                                               "temporal_basis_inherited_from_event", "review_note"])
        writer.writeheader()
        writer.writerows({"hunk_id": f"synthetic-{i}", "relation_candidate": "UNRELATED",
                          "related_atomic_s0_ids": "", "temporal_basis_inherited_from_event": "BASELINE",
                          "review_note": "PRIVATE_GOLD_MARKER_NOT_AGENT_INPUT"} for i in range(30))
    fm = {"s0_sha256": sha(frozen/"S0_ATOMIC_REVIEWER_CONFIRMED.json"),
          "reference_sha256": {ref.name: sha(ref)}}
    write(frozen/"FREEZE_MANIFEST.json", fm)
    write(api/"inputs"/DECISION, approved_state)
    history = api/"inputs"/HISTORY
    history.write_text("".join(json.dumps({"artifact_id": f"synthetic-{i}", "content": "Unlabeled fixture."})
                               + "\n" for i in range(53)), encoding="utf-8")
    off_prep = {"runtime_s0_sha256": sha(api/"inputs"/DECISION), "history_sha256": sha(history)}
    write(offline/"PREP_MANIFEST.json", off_prep)
    result = {"evaluated_hunks": 30, "gold_positive_exact_triples": 0, "f1": 0.0}
    metrics = {"results": {"baseline": result, "all": result}}
    write(offline/"score"/"metrics.json", metrics)
    prep = {**off_prep, "frozen_manifest_sha256": sha(frozen/"FREEZE_MANIFEST.json"),
            "frozen_s0_sha256": fm["s0_sha256"], "baseline_score_sha256": sha(offline/"score"/"metrics.json"),
            "evorationale_python_tree_sha256": "fixture-parent41-hash"}
    write(api/"PREP_MANIFEST.json", prep)
    cfg = {"protocol": "PRESPECIFIED_RETROSPECTIVE_API_DEVELOPMENT_COMPARISON",
           "linker_model": "fixture-old-linker", "judge_model": "fixture-old-judge",
           "budgets": {"max_rounds": 6, "max_queries": 12, "max_reads": 36, "max_input_tokens": 100000}}
    write(api/"API_CONFIG.json", cfg)
    report = {"verified_evidence": [], "verification": {"status": "UNRESOLVED"}}
    write(api/"run"/"report.json", report)
    write(api/"RUN_RECEIPT.json", {"status": "HOSTED_MODEL_RUN_COMPLETED_AND_HASHED",
                                  "prep_manifest_sha256": sha(api/"PREP_MANIFEST.json"),
                                  "api_config_sha256": sha(api/"API_CONFIG.json"),
                                  "run_report_sha256": sha(api/"run"/"report.json")})
    write(api/"score"/"metrics.json", {**metrics, "run_sha256": sha(api/"run"/"report.json")})
    models = {"linker": "fixture-reused-linker", "judge": "fixture-reused-judge"}
    write(parent/"DEV_PREP_MANIFEST.json", {"kind": "DEVELOPMENT_ONLY_V42_CONTROLLED_COMPARISON",
                                           "v42_python_sha256": PARENT_HASH, "models": models,
                                           "frozen_s0_sha256": fm["s0_sha256"]})
    write(parent/"run"/"report.json", report)
    write(parent/"run"/"manifest.json", {"mode": "api", "run_id": "simulated-parent42"})
    for name in (DECISION, HISTORY):
        target = parent/"inputs"/name
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes((api/"inputs"/name).read_bytes())
    write(parent/"RUN_RECEIPT.json", {"status": "V42_DEV_HOSTED_RUN_COMPLETED_AND_HASHED", "mode": "api",
                                      "code_tree_sha256": PARENT_HASH, "run_id": "simulated-parent42",
                                      "model": models, "prep_sha256": sha(parent/"DEV_PREP_MANIFEST.json"),
                                      "run_manifest_sha256": sha(parent/"run"/"manifest.json"),
                                      "run_report_sha256": sha(parent/"run"/"report.json")})
    write(parent/"score"/"metrics.json", {**metrics, "frozen_s0_sha256": fm["s0_sha256"],
                                          "v42_run_report_sha256": sha(parent/"run"/"report.json")})
    before = {str(p): sha(p) for directory in (api, offline, frozen, parent)
              for p in directory.rglob("*") if p.is_file()}
    args = ["--original-api", api, "--original-offline", offline, "--frozen", frozen,
            "--code-root", ROOT, "--output", evaluation, "--models-from-evaluation", parent]
    return api, offline, frozen, parent, evaluation, args, before


def test_preparation_and_dry_run_preserve_sources_and_copy_no_reference(prepared_inputs):
    *_, evaluation, args, before = prepared_inputs
    prepared = command("prepare_v43.py", args)
    assert prepared.returncode == 0, prepared.stderr
    assert json.loads(prepared.stdout)["status"] == "READY_FOR_V43_DEVELOPMENT_ONLY_NO_API_CALLED"
    cfg = json.loads((evaluation/"DEV_PREP_MANIFEST.json").read_text())
    assert cfg["models"] == {"linker": "fixture-reused-linker", "judge": "fixture-reused-judge"}
    assert sorted(p.name for p in (evaluation/"inputs").iterdir()) == sorted([DECISION, HISTORY])
    assert "PRIVATE_GOLD_MARKER" not in "".join(p.read_text() for p in evaluation.rglob("*") if p.is_file())
    dry = command("run_v43.py", ["--evaluation", evaluation, "--code-root", ROOT, "--dry-run"])
    assert dry.returncode == 0, dry.stderr
    assert json.loads(dry.stdout)["status"] == "DRY_RUN_NO_API_CALLED"
    assert not (evaluation/"run").exists() and not (evaluation/"checkpoints").exists()
    assert all(sha(Path(path)) == expected for path, expected in before.items())
    (evaluation/"inputs"/HISTORY).write_text("tampered input")
    refused = command("run_v43.py", ["--evaluation", evaluation, "--code-root", ROOT, "--dry-run"])
    assert refused.returncode != 0 and "Hash mismatch" in refused.stderr
    assert not (evaluation/"run").exists()


def test_modified_previous_model_configuration_is_rejected_before_preparation(prepared_inputs):
    _, _, _, parent, evaluation, args, _ = prepared_inputs
    path = parent/"DEV_PREP_MANIFEST.json"
    cfg = json.loads(path.read_text())
    cfg["models"]["judge"] = "fixture-tampered-model"
    write(path, cfg)
    refused = command("prepare_v43.py", args)
    assert refused.returncode != 0 and "Hash mismatch" in refused.stderr
    assert not evaluation.exists()


def test_post_run_scorer_uses_same_population_and_preserves_previous_scores(prepared_inputs):
    api, offline, frozen, parent, evaluation, args, before = prepared_inputs
    prepared = command("prepare_v43.py", args)
    assert prepared.returncode == 0, prepared.stderr
    cfg = json.loads((evaluation/"DEV_PREP_MANIFEST.json").read_text())
    # Simulate a completed empty run strictly to test scorer provenance checks.
    write(evaluation/"run"/"report.json", {"verified_evidence": [], "verification": {"status": "UNRESOLVED"}})
    write(evaluation/"run"/"manifest.json", {"run_id": "simulated43", "mode": "api",
                                           "decision_sha256": cfg["runtime_s0_sha256"],
                                           "history_sha256": cfg["history_sha256"]})
    write(evaluation/"RUN_RECEIPT.json", {"status": "V43_DEV_HOSTED_RUN_COMPLETED_AND_HASHED", "mode": "api",
                                         "run_id": "simulated43", "model": cfg["models"],
                                         "prep_sha256": sha(evaluation/"DEV_PREP_MANIFEST.json"),
                                         "code_tree_sha256": cfg["v43_python_sha256"],
                                         "run_manifest_sha256": sha(evaluation/"run"/"manifest.json"),
                                         "run_report_sha256": sha(evaluation/"run"/"report.json")})
    scored = command("score_v43.py", ["--evaluation", evaluation, "--frozen", frozen, "--code-root", ROOT,
                                      "--original-api", api, "--original-offline", offline, "--previous-v42", parent])
    assert scored.returncode == 0, scored.stderr
    metrics = json.loads((evaluation/"score"/"metrics.json").read_text())
    assert metrics["results"]["all"]["evaluated_hunks"] == 30
    assert metrics["comparison"]["all"]["delta_v43_minus_v42"] == 0.0
    assert all(sha(Path(path)) == expected for path, expected in before.items())

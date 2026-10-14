"""Offline preparation/scoring integration with synthetic hashed fixtures.

No provider is contacted. Completed-run receipts below are explicitly simulated
test data; their scores are not experimental results.
"""
import csv
import hashlib
import json
import importlib.util
import shutil
from pathlib import Path
import subprocess
import sys

import pytest

ROOT = Path(__file__).resolve().parent.parent
DECISION = "S0_RETROSPECTIVE_RUNTIME.json"
HISTORY = "POST_S0_EVIDENCE_RETROSPECTIVE_53.jsonl"
PARENT_HASH = "b53989d04604b68d76eddd92412db89b0b33025637e42649abda27714ee53d94"


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, sort_keys=True), encoding="utf-8")


def command(script, args):
    if script == "prepare_v44.py":
        # Exercise preparation against this synthetic fixture source. The
        # production helper must keep its real v4.4 package hash pin unchanged.
        wrapper = (f"import sys; sys.path.insert(0, {str(ROOT/'development_tools')!r}); "
                   "import prepare_v44; from _score_core import code_tree_hash; "
                   f"prepare_v44.EXPECTED_V44_CODE_SHA256 = code_tree_hash({str(ROOT)!r}); "
                   "prepare_v44.main()")
        return subprocess.run([sys.executable, "-c", wrapper, *map(str, args)],
                              cwd=ROOT, capture_output=True, text=True)
    return subprocess.run([sys.executable, str(ROOT/"development_tools"/script), *map(str, args)],
                          cwd=ROOT, capture_output=True, text=True)


@pytest.fixture
def prepared_inputs(tmp_path, approved_state):
    api, offline, frozen, parent, evaluation = [tmp_path/name for name in
                                               ("api41", "offline41", "frozen", "parent43", "evaluation44")]
    write(frozen/"S0_ATOMIC_REVIEWER_CONFIRMED.json", approved_state)
    ref = frozen/"reference"/"HUNK_RELATIONS_CANDIDATE.csv"
    ref.parent.mkdir(parents=True)
    with ref.open("w", newline="", encoding="utf-8") as out:
        writer = csv.DictWriter(out, fieldnames=["hunk_id", "relation_candidate", "related_atomic_s0_ids",
                                               "temporal_basis_inherited_from_event", "review_note"])
        writer.writeheader()
        writer.writerows({"hunk_id": f"synthetic-{i}", "relation_candidate": "SUPPORTS" if i == 0 else "UNRELATED",
                          "related_atomic_s0_ids": "synthetic-requirement" if i == 0 else "",
                          "temporal_basis_inherited_from_event": "BASELINE",
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
    result = {"evaluated_hunks": 30, "gold_positive_exact_triples": 1, "f1": 0.0}
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
    write(parent/"DEV_PREP_MANIFEST.json", {"kind": "DEVELOPMENT_ONLY_V43_CONTROLLED_COMPARISON",
                                           "v43_python_sha256": PARENT_HASH, "models": models,
                                           "frozen_manifest_sha256": sha(frozen/"FREEZE_MANIFEST.json"),
                                           "frozen_s0_sha256": fm["s0_sha256"], **off_prep, "budgets": cfg["budgets"]})
    write(parent/"run"/"report.json", report)
    write(parent/"run"/"manifest.json", {"mode": "api", "run_id": "simulated-parent43",
                                         "decision_sha256": off_prep["runtime_s0_sha256"],
                                         "history_sha256": off_prep["history_sha256"],
                                         "report_sha256": sha(parent/"run"/"report.json")})
    for name in (DECISION, HISTORY):
        target = parent/"inputs"/name
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes((api/"inputs"/name).read_bytes())
    write(parent/"RUN_RECEIPT.json", {"status": "V43_DEV_HOSTED_RUN_COMPLETED_AND_HASHED", "mode": "api",
                                      "code_tree_sha256": PARENT_HASH, "run_id": "simulated-parent43",
                                      "model": models, "prep_sha256": sha(parent/"DEV_PREP_MANIFEST.json"),
                                      "run_manifest_sha256": sha(parent/"run"/"manifest.json"),
                                      "run_report_sha256": sha(parent/"run"/"report.json")})
    write(parent/"score"/"metrics.json", {**metrics, "frozen_s0_sha256": fm["s0_sha256"],
                                          "v43_run_report_sha256": sha(parent/"run"/"report.json")})
    before = {str(p): sha(p) for directory in (api, offline, frozen, parent)
              for p in directory.rglob("*") if p.is_file()}
    args = ["--original-api", api, "--original-offline", offline, "--frozen", frozen,
            "--code-root", ROOT, "--output", evaluation, "--previous-v43", parent]
    return api, offline, frozen, parent, evaluation, args, before


def test_preparation_and_dry_run_preserve_sources_and_copy_no_reference(prepared_inputs):
    *_, evaluation, args, before = prepared_inputs
    prepared = command("prepare_v44.py", args)
    assert prepared.returncode == 0, prepared.stderr
    assert json.loads(prepared.stdout)["status"] == "READY_FOR_V44_DEVELOPMENT_ONLY_NO_API_CALLED"
    cfg = json.loads((evaluation/"DEV_PREP_MANIFEST.json").read_text())
    assert cfg["budgets"] == {"max_rounds": 6, "max_queries": 12, "max_reads": 36, "max_input_tokens": 100000}
    assert cfg["investigation_profile"] == "event-complete"
    assert cfg["previous_v43"]["config_sha256"]
    assert cfg["previous_v43"]["runtime_s0_sha256"] == cfg["runtime_s0_sha256"]
    assert cfg["models"] == {"linker": "fixture-reused-linker", "judge": "fixture-reused-judge"}
    assert sorted(p.name for p in (evaluation/"inputs").iterdir()) == sorted([DECISION, HISTORY])
    assert "PRIVATE_GOLD_MARKER" not in "".join(p.read_text() for p in evaluation.rglob("*") if p.is_file())
    dry = command("run_v44.py", ["--evaluation", evaluation, "--code-root", ROOT, "--dry-run"])
    assert dry.returncode == 0, dry.stderr
    assert json.loads(dry.stdout)["status"] == "DRY_RUN_NO_API_CALLED"
    assert not (evaluation/"run").exists() and not (evaluation/"checkpoints").exists()
    assert json.loads(dry.stdout)["investigation_profile"] == "event-complete"
    command_args = json.loads(dry.stdout)["command"]
    assert command_args[command_args.index("--investigation-profile")+1] == "event-complete"
    assert "accounting differ" in json.loads(dry.stdout)["comparison_note"]
    assert all(sha(Path(path)) == expected for path, expected in before.items())
    (evaluation/"inputs"/HISTORY).write_text("tampered input")
    refused = command("run_v44.py", ["--evaluation", evaluation, "--code-root", ROOT, "--dry-run"])
    assert refused.returncode != 0 and "Hash mismatch" in refused.stderr
    assert not (evaluation/"run").exists()


def test_modified_previous_model_configuration_is_rejected_before_preparation(prepared_inputs):
    _, _, _, parent, evaluation, args, _ = prepared_inputs
    path = parent/"DEV_PREP_MANIFEST.json"
    cfg = json.loads(path.read_text())
    cfg["models"]["judge"] = "fixture-tampered-model"
    write(path, cfg)
    refused = command("prepare_v44.py", args)
    assert refused.returncode != 0 and "Hash mismatch" in refused.stderr
    assert not evaluation.exists()


def test_previous_different_freeze_manifest_is_rejected_before_preparation(prepared_inputs):
    _, _, _, parent, evaluation, args, _ = prepared_inputs
    config_path = parent/"DEV_PREP_MANIFEST.json"
    cfg = json.loads(config_path.read_text())
    cfg["frozen_manifest_sha256"] = "different-reference-same-s0"
    write(config_path, cfg)
    receipt_path = parent/"RUN_RECEIPT.json"
    receipt = json.loads(receipt_path.read_text())
    receipt["prep_sha256"] = sha(config_path)
    write(receipt_path, receipt)
    refused = command("prepare_v44.py", args)
    assert refused.returncode != 0 and "Previous inputs, reference, or models mismatch" in refused.stderr
    assert not evaluation.exists()


def test_post_run_scorer_uses_same_population_and_preserves_previous_scores(prepared_inputs):
    api, offline, frozen, parent, evaluation, args, before = prepared_inputs
    prepared = command("prepare_v44.py", args)
    assert prepared.returncode == 0, prepared.stderr
    cfg = json.loads((evaluation/"DEV_PREP_MANIFEST.json").read_text())
    # Simulate a completed empty run strictly to test scorer provenance checks.
    write(evaluation/"run"/"report.json", {"verified_evidence": [], "verification": {"status": "UNRESOLVED"}})
    write(evaluation/"run"/"manifest.json", {"run_id": "simulated44", "mode": "api", "investigation_profile": "event-complete",
                                           "decision_sha256": cfg["runtime_s0_sha256"],
                                           "history_sha256": cfg["history_sha256"], "report_sha256": sha(evaluation/"run"/"report.json")})
    write(evaluation/"RUN_RECEIPT.json", {"status": "V44_DEV_HOSTED_RUN_COMPLETED_AND_HASHED", "mode": "api",
                                         "run_id": "simulated44", "model": cfg["models"], "investigation_profile": "event-complete",
                                         "prep_sha256": sha(evaluation/"DEV_PREP_MANIFEST.json"),
                                         "code_tree_sha256": cfg["v44_python_sha256"],
                                         "run_manifest_sha256": sha(evaluation/"run"/"manifest.json"),
                                         "run_report_sha256": sha(evaluation/"run"/"report.json")})
    scored = command("score_v44.py", ["--evaluation", evaluation, "--frozen", frozen, "--code-root", ROOT,
                                      "--original-api", api, "--original-offline", offline, "--previous-v43", parent])
    assert scored.returncode == 0, scored.stderr
    metrics = json.loads((evaluation/"score"/"metrics.json").read_text())
    assert metrics["results"]["all"]["evaluated_hunks"] == 30
    assert metrics["comparison"]["all"]["delta_v44_minus_v43"] == 0.0
    assert all(sha(Path(path)) == expected for path, expected in before.items())


def complete_simulated_run(evaluation, evidence=None):
    cfg = json.loads((evaluation/"DEV_PREP_MANIFEST.json").read_text())
    write(evaluation/"run"/"report.json", {"verified_evidence": evidence or [],
                                           "verification": {"status": "UNRESOLVED"}})
    write(evaluation/"run"/"manifest.json", {"run_id": "simulated44", "mode": "api", "investigation_profile": "event-complete",
                                             "decision_sha256": cfg["runtime_s0_sha256"],
                                             "history_sha256": cfg["history_sha256"],
                                             "report_sha256": sha(evaluation/"run"/"report.json")})
    write(evaluation/"RUN_RECEIPT.json", {"status": "V44_DEV_HOSTED_RUN_COMPLETED_AND_HASHED", "mode": "api",
                                          "run_id": "simulated44", "model": cfg["models"],
                                          "investigation_profile": "event-complete",
                                          "prep_sha256": sha(evaluation/"DEV_PREP_MANIFEST.json"),
                                          "code_tree_sha256": cfg["v44_python_sha256"],
                                          "run_manifest_sha256": sha(evaluation/"run"/"manifest.json"),
                                          "run_report_sha256": sha(evaluation/"run"/"report.json")})


def scoring_args(inputs):
    api, offline, frozen, parent, evaluation, *_ = inputs
    return ["--evaluation", evaluation, "--frozen", frozen, "--code-root", ROOT,
            "--original-api", api, "--original-offline", offline, "--previous-v43", parent]


@pytest.mark.parametrize("relative", ["DEV_PREP_MANIFEST.json", "run/report.json", "score/metrics.json",
                                     "inputs/"+HISTORY])
def test_previous_comparison_tamper_blocked_after_preparation(prepared_inputs, relative):
    _, _, _, parent, evaluation, args, _ = prepared_inputs
    prepared = command("prepare_v44.py", args)
    assert prepared.returncode == 0, prepared.stderr
    complete_simulated_run(evaluation)
    target = parent/relative
    target.write_bytes(target.read_bytes() + b"\n ")
    refused = command("score_v44.py", scoring_args(prepared_inputs))
    assert refused.returncode != 0 and "Hash mismatch" in refused.stderr
    assert not (evaluation/"score").exists()


@pytest.mark.parametrize("existing", ["run", "checkpoints", "score", "RUN_RECEIPT.json"])
def test_run_refuses_overwriting_any_existing_output(prepared_inputs, existing):
    *_, evaluation, args, _ = prepared_inputs
    prepared = command("prepare_v44.py", args)
    assert prepared.returncode == 0, prepared.stderr
    path = evaluation/existing
    if existing.endswith(".json"):
        path.write_text("fixture-preserve")
    else:
        path.mkdir()
        (path/"preserve.txt").write_text("fixture-preserve")
    refused = command("run_v44.py", ["--evaluation", evaluation, "--code-root", ROOT, "--dry-run"])
    assert refused.returncode != 0 and "Refuse overwriting" in refused.stderr
    assert (path if existing.endswith(".json") else path/"preserve.txt").read_text() == "fixture-preserve"


def test_exact_triple_scoring_deduplicates_simulated_links_and_refuses_overwrite(prepared_inputs):
    *_, evaluation, args, _ = prepared_inputs
    prepared = command("prepare_v44.py", args)
    assert prepared.returncode == 0, prepared.stderr
    link = {"artifact_id": "synthetic-0", "decision_element_id": "synthetic-requirement", "relation": "supports"}
    complete_simulated_run(evaluation, [link, link])
    scored = command("score_v44.py", scoring_args(prepared_inputs))
    assert scored.returncode == 0, scored.stderr
    metrics = json.loads((evaluation/"score"/"metrics.json").read_text())
    assert metrics["results"]["all"]["tp"] == 1
    assert metrics["results"]["all"]["predicted_exact_triples"] == 1
    assert metrics["verified_evidence_links"] == 2
    before = sha(evaluation/"score"/"metrics.json")
    refused = command("score_v44.py", scoring_args(prepared_inputs))
    assert refused.returncode != 0 and "overwrite" in refused.stderr
    assert sha(evaluation/"score"/"metrics.json") == before


def test_previous_nominal_budgets_are_reused_without_original_fallback(prepared_inputs):
    _, _, _, parent, evaluation, args, _ = prepared_inputs
    config_path = parent/"DEV_PREP_MANIFEST.json"
    parent_config = json.loads(config_path.read_text())
    parent_config["budgets"]["max_input_tokens"] = 98765
    write(config_path, parent_config)
    receipt_path = parent/"RUN_RECEIPT.json"
    receipt = json.loads(receipt_path.read_text())
    receipt["prep_sha256"] = sha(config_path)
    write(receipt_path, receipt)
    prepared = command("prepare_v44.py", args)
    assert prepared.returncode == 0, prepared.stderr
    assert json.loads((evaluation/"DEV_PREP_MANIFEST.json").read_text())["budgets"]["max_input_tokens"] == 98765


@pytest.mark.parametrize("profile", [None, "element-centered"])
def test_scorer_rejects_missing_or_wrong_core_profile(prepared_inputs, profile):
    *_, evaluation, args, _ = prepared_inputs
    prepared = command("prepare_v44.py", args)
    assert prepared.returncode == 0, prepared.stderr
    complete_simulated_run(evaluation)
    manifest_path = evaluation/"run"/"manifest.json"
    manifest = json.loads(manifest_path.read_text())
    if profile is None:
        manifest.pop("investigation_profile")
    else:
        manifest["investigation_profile"] = profile
    write(manifest_path, manifest)
    receipt_path = evaluation/"RUN_RECEIPT.json"
    receipt = json.loads(receipt_path.read_text())
    receipt["run_manifest_sha256"] = sha(manifest_path)
    write(receipt_path, receipt)
    refused = command("score_v44.py", scoring_args(prepared_inputs))
    assert refused.returncode != 0 and "Run provenance mismatch" in refused.stderr
    assert not (evaluation/"score").exists()


@pytest.mark.parametrize("profile", [None, "element-centered", "event-complete"])
def test_run_receipt_requires_actual_core_profile_without_provider_calls(prepared_inputs, monkeypatch, profile):
    *_, evaluation, args, _ = prepared_inputs
    prepared = command("prepare_v44.py", args)
    assert prepared.returncode == 0, prepared.stderr
    cfg = json.loads((evaluation/"DEV_PREP_MANIFEST.json").read_text())
    monkeypatch.syspath_prepend(str(ROOT/"development_tools"))
    spec = importlib.util.spec_from_file_location("v44_run_test_module", ROOT/"development_tools"/"run_v44.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    def simulated_local_subprocess(arguments, **kwargs):
        assert arguments[arguments.index("--investigation-profile")+1] == "event-complete"
        write(evaluation/"run"/"report.json", {"verified_evidence": []})
        manifest = {"run_id": "simulated44", "mode": "api",
                    "decision_sha256": cfg["runtime_s0_sha256"], "history_sha256": cfg["history_sha256"],
                    "report_sha256": sha(evaluation/"run"/"report.json")}
        if profile is not None:
            manifest["investigation_profile"] = profile
        write(evaluation/"run"/"manifest.json", manifest)
    monkeypatch.setattr(module.subprocess, "run", simulated_local_subprocess)
    monkeypatch.setenv("OPENAI_API_KEY", "synthetic-unused-no-provider-call")
    monkeypatch.setattr(sys, "argv", ["run_v44.py", "--evaluation", str(evaluation), "--code-root", str(ROOT),
                                      "--i-approve-public-repository-excerpts-to-openai"])
    if profile == "event-complete":
        module.main()
        receipt = json.loads((evaluation/"RUN_RECEIPT.json").read_text())
        assert receipt["investigation_profile"] == "event-complete"
        assert "synthetic-unused" not in json.dumps(receipt)
    else:
        with pytest.raises(ValueError, match="run manifest provenance mismatch"):
            module.main()
        assert not (evaluation/"RUN_RECEIPT.json").exists()


def test_optional_previous_v42_is_pinned_and_compared(prepared_inputs):
    _, _, _, parent, evaluation, args, _ = prepared_inputs
    older = parent.parent/"optional-parent42"
    shutil.copytree(parent, older)
    old_hash = "ab892cc339348fc6db243ecbdb18cb6df3a4959d5636332d5f2cdb7945fbdd09"
    old_config = json.loads((older/"DEV_PREP_MANIFEST.json").read_text())
    old_config["kind"] = "DEVELOPMENT_ONLY_V42_CONTROLLED_COMPARISON"
    old_config["v42_python_sha256"] = old_hash
    old_config.pop("v43_python_sha256")
    write(older/"DEV_PREP_MANIFEST.json", old_config)
    old_receipt = json.loads((older/"RUN_RECEIPT.json").read_text())
    old_receipt["status"] = "V42_DEV_HOSTED_RUN_COMPLETED_AND_HASHED"
    old_receipt["code_tree_sha256"] = old_hash
    old_receipt["prep_sha256"] = sha(older/"DEV_PREP_MANIFEST.json")
    write(older/"RUN_RECEIPT.json", old_receipt)
    old_metrics = json.loads((older/"score"/"metrics.json").read_text())
    old_metrics["v42_run_report_sha256"] = old_metrics.pop("v43_run_report_sha256")
    write(older/"score"/"metrics.json", old_metrics)
    prepared = command("prepare_v44.py", [*args, "--previous-v42", older])
    assert prepared.returncode == 0, prepared.stderr
    config = json.loads((evaluation/"DEV_PREP_MANIFEST.json").read_text())
    assert config["previous_v42"]["score_sha256"] == sha(older/"score"/"metrics.json")
    complete_simulated_run(evaluation)
    scored = command("score_v44.py", [*scoring_args(prepared_inputs), "--previous-v42", older])
    assert scored.returncode == 0, scored.stderr
    metrics = json.loads((evaluation/"score"/"metrics.json").read_text())
    assert metrics["comparison"]["all"]["delta_v44_minus_v42"] == 0.0


def test_start_only_invokes_tests_preparation_and_dry_run(prepared_inputs, monkeypatch, capsys):
    api, offline, frozen, parent, evaluation, *_ = prepared_inputs
    monkeypatch.syspath_prepend(str(ROOT/"development_tools"))
    spec = importlib.util.spec_from_file_location("v44_start_test_module", ROOT/"development_tools"/"start_v44_no_api.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    from _score_core import code_tree_hash
    monkeypatch.setattr(module, "EXPECTED_V44_CODE_SHA256", code_tree_hash(ROOT))
    commands = []
    def fake_run(arguments, **kwargs):
        commands.append(arguments)
        assert kwargs["check"] is True
    monkeypatch.setattr(module.subprocess, "run", fake_run)
    monkeypatch.setattr(sys, "argv", ["start_v44_no_api.py", "--original-api", str(api),
                                      "--original-offline", str(offline), "--frozen", str(frozen),
                                      "--previous-v43", str(parent), "--evaluation", str(evaluation)])
    module.main()
    assert len(commands) == 3
    assert commands[0][1:] == ["-m", "pytest", "-q"]
    assert "prepare_v44.py" in commands[1][1]
    assert commands[2][-1] == "--dry-run"
    assert all("--i-approve-public-repository-excerpts-to-openai" not in c for c in commands)
    assert not evaluation.exists()
    assert "V44_TESTS_AND_DRY_RUN_COMPLETED_NO_API_CALLED" in capsys.readouterr().out

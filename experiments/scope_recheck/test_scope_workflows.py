"""Portable provenance/workflow checks using synthetic sources and transports.

No hosted provider is called. Artificial reference rows test scoring transactions
and never enter model inputs; fixture success is not a semantic accuracy result.
"""
from copy import deepcopy
import builtins
import csv
import hashlib
import json
from pathlib import Path
import sys
from types import SimpleNamespace
import zipfile

import pytest

import evorationale
import _kit_common as common
import run_scope_recheck as runner
import score_scope_recheck as scorer
from test_scope_checker import synthetic_cache_fixture, scope_decision

CORE_ROOT = Path(evorationale.__file__).resolve().parent.parent
PRIVATE_MARKER = "PRIVATE_GOLD_MARKER_ONLY_FOR_SCORER_TEST"


def _sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def _write(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _snapshot(folder):
    return {str(p.relative_to(folder)): (p.read_bytes(), p.stat().st_mtime_ns)
            for p in folder.rglob("*") if p.is_file()}


@pytest.fixture
def synthetic_parent(tmp_path):
    """Build a portable consistent parent receipt, not an attested real API run."""
    sys.path.insert(0, str(CORE_ROOT / "development_tools"))
    from prepare_v49 import KIND, PROFILE, SEMANTIC_PHASE_CONFIG, POLICY_CHANGE_NOTE
    from _score_core import HUNK_FILE, EVAL_SCOPES, evaluate
    state, history, checkpoint = synthetic_cache_fixture()
    evaluation, frozen = tmp_path / "original49", tmp_path / "synthetic-freeze"
    _write(evaluation / "inputs" / common.INPUT_NAMES[0], state)
    history_file = evaluation / "inputs" / common.INPUT_NAMES[1]
    history_file.write_text("".join(json.dumps(a, sort_keys=True) + "\n" for a in history), encoding="utf-8")
    _write(frozen / "S0_ATOMIC_REVIEWER_CONFIRMED.json", state)
    reference_file = frozen / "reference" / HUNK_FILE
    reference_file.parent.mkdir(parents=True)
    rows = [{"hunk_id": history[0]["artifact_id"], "relation_candidate": "SUPPORTS",
             "related_atomic_s0_ids": "T_REPORT", "temporal_basis_inherited_from_event": "BASELINE_2023",
             "private_review_note": PRIVATE_MARKER}]
    rows += [{"hunk_id": f"synthetic-unused-{n:02d}", "relation_candidate": "UNRELATED",
              "related_atomic_s0_ids": "", "temporal_basis_inherited_from_event": "BASELINE_2023",
              "private_review_note": PRIVATE_MARKER} for n in range(1, 30)]
    with reference_file.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader(); writer.writerows(rows)
    _write(frozen / "FREEZE_MANIFEST.json", {
        "s0_sha256": _sha(frozen / "S0_ATOMIC_REVIEWER_CONFIRMED.json"),
        "reference_sha256": {HUNK_FILE: _sha(reference_file)}})
    models = {"judge": "synthetic-no-api-model", "linker": "synthetic-no-api-model"}
    old_budget = {"max_rounds": 1, "max_queries": 1, "max_reads": 36, "max_input_tokens": 100000}
    budget = {**old_budget, "max_input_tokens": 400000, "max_provider_requests": 36}
    cfg = {"kind": KIND, "investigation_profile": PROFILE, "nomination_mode": "none",
        "models": models, "budgets": budget, "parent_v46_budgets": old_budget,
        **{name: deepcopy(models) for name in ["parent_v44_models", "parent_v45_models", "parent_v46_models",
                                               "parent_v47_models", "parent_v48_models"]},
        "semantic_phase_config": deepcopy(SEMANTIC_PHASE_CONFIG), "policy_change_note": POLICY_CHANGE_NOTE,
        "v49_python_sha256": common.PARENT_CORE_SHA256,
        "runtime_s0_sha256": _sha(evaluation / "inputs" / common.INPUT_NAMES[0]),
        "history_sha256": _sha(history_file),
        "frozen_s0_sha256": _sha(frozen / "S0_ATOMIC_REVIEWER_CONFIRMED.json"),
        "frozen_manifest_sha256": _sha(frozen / "FREEZE_MANIFEST.json"),
        "gold_labels_in_agent_inputs": False}
    _write(evaluation / "DEV_PREP_MANIFEST.json", cfg)
    run_id = checkpoint["run_id"]
    checkpoint_name = "checkpoints/" + run_id + ".json"
    _write(evaluation / checkpoint_name, checkpoint)
    _write(evaluation / "run/report.json", checkpoint["report"])
    report_hash = _sha(evaluation / "run/report.json")
    _write(evaluation / "run/manifest.json", {"run_id": run_id, "mode": "api",
        "investigation_profile": PROFILE, "nomination_mode": "none", "max_provider_requests": 36,
        "decision_sha256": cfg["runtime_s0_sha256"], "history_sha256": cfg["history_sha256"],
        "report_sha256": report_hash})
    _write(evaluation / "RUN_RECEIPT.json", {"status": "V49_DEV_HOSTED_RUN_COMPLETED_AND_HASHED",
        "run_id": run_id, "mode": "api", "investigation_profile": PROFILE, "nomination_mode": "none",
        "code_tree_sha256": cfg["v49_python_sha256"], "model": models, "nominal_budgets": budget,
        **{name: cfg[name] for name in ["parent_v44_models", "parent_v45_models", "parent_v46_models",
            "parent_v47_models", "parent_v48_models", "semantic_phase_config", "policy_change_note"]},
        "prep_sha256": _sha(evaluation / "DEV_PREP_MANIFEST.json"), "run_report_sha256": report_hash,
        "run_manifest_sha256": _sha(evaluation / "run/manifest.json"),
        "checkpoint_relative_path": checkpoint_name, "checkpoint_sha256": _sha(evaluation / checkpoint_name)})
    metrics = {"status": "V49_DEVELOPMENT_ONLY_POST_RUN_REFERENCE_COMPARISON",
        "v49_run_report_sha256": report_hash, "v49_code_sha256": cfg["v49_python_sha256"],
        "frozen_s0_sha256": cfg["frozen_s0_sha256"], "nomination_mode": "none", "nominal_budgets": budget,
        "semantic_phase_config": deepcopy(SEMANTIC_PHASE_CONFIG),
        "results": {scope: evaluate(rows, checkpoint["report"], scope)[0] for scope in EVAL_SCOPES}}
    _write(evaluation / "score/metrics.json", metrics)
    (evaluation / "score/link_errors.csv").write_text(
        "scope,verdict,hunk_id,atomic_s0_id,relation,reference_hunk_relation,temporal_basis\n", encoding="utf-8")
    _write(evaluation / "score/SCORE_RECEIPT.json", {"status": "V49_SCORE_COMMITTED",
        "run_report_sha256": report_hash, "core_sha256": cfg["v49_python_sha256"],
        "frozen_manifest_sha256": cfg["frozen_manifest_sha256"],
        "metrics_sha256": _sha(evaluation / "score/metrics.json"),
        "link_errors_sha256": _sha(evaluation / "score/link_errors.csv")})
    verified = common.verified_parent(CORE_ROOT, evaluation)
    assert verified["checkpoint"] == checkpoint
    return SimpleNamespace(evaluation=evaluation, frozen=frozen, config=cfg, state=state,
        history=history, checkpoint=checkpoint, verified=verified,
        before=_snapshot(evaluation), frozen_before=_snapshot(frozen))


def _invoke(monkeypatch, module, args):
    monkeypatch.setattr(sys, "argv", [str(Path(module.__file__)), *map(str, args)])
    return module.main()


def _run_args(parent, output, mode=None, allow=False):
    args = ["--code-root", CORE_ROOT, "--evaluation", parent.evaluation, "--output", output]
    if mode is not None:
        args += ["--mode", mode]
    if allow:
        args += ["--allow-repository-text-to-api"]
    return args


def _deny_sdk_import(monkeypatch):
    original_import = builtins.__import__
    def guarded(name, *args, **kwargs):
        if name == "openai" or name.startswith("openai."):
            raise AssertionError("Read-only workflow imported a hosted SDK")
        return original_import(name, *args, **kwargs)
    monkeypatch.setattr(builtins, "__import__", guarded)


class CompletingChecker:
    def __init__(self):
        self.calls = []
    def create(self, **request):
        self.calls.append(deepcopy(request))
        assert PRIVATE_MARKER not in request["input"]
        props = request["text"]["format"]["schema"]["properties"]
        assert set(props) == {"decisions"}
        ids = props["decisions"]["items"]["properties"]["candidate_id"]["enum"]
        response = {"decisions": [dict(scope_decision(), candidate_id=identifier) for identifier in ids]}
        return SimpleNamespace(status="completed", output_text=json.dumps(response),
                               usage={"input_tokens": 37, "output_tokens": 29, "total_tokens": 66})


@pytest.fixture
def completed_experiment(monkeypatch, synthetic_parent, tmp_path):
    provider = CompletingChecker()
    constructors = []
    def sdk(**kwargs):
        constructors.append(kwargs)
        return SimpleNamespace(responses=provider)
    monkeypatch.setitem(sys.modules, "openai", SimpleNamespace(OpenAI=sdk))
    monkeypatch.setenv("OPENAI_API_KEY", "synthetic-unused-key")
    output = tmp_path / "new-scope-experiment"
    _invoke(monkeypatch, runner, _run_args(synthetic_parent, output, mode="api", allow=True))
    assert constructors == [{"max_retries": 0}]
    assert len(provider.calls) == 1
    assert _snapshot(synthetic_parent.evaluation) == synthetic_parent.before
    assert _snapshot(synthetic_parent.frozen) == synthetic_parent.frozen_before
    snapshot = common.output_snapshot(output, CORE_ROOT)
    return SimpleNamespace(parent=synthetic_parent, output=output, provider=provider, snapshot=snapshot)


def test_default_dry_run_needs_no_key_or_sdk_and_writes_nothing(monkeypatch, synthetic_parent, tmp_path, capsys):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    _deny_sdk_import(monkeypatch)
    output = tmp_path / "never-created"
    _invoke(monkeypatch, runner, _run_args(synthetic_parent, output))
    result = json.loads(capsys.readouterr().out)
    assert result["status"] == "SCOPE_RECHECK_DRY_RUN_NO_API_CALLED"
    assert result["new_primary_api_requests"] == 0 and result["mock_checker_requests"] == 1
    assert result["output_created"] is False and result["hosted_accuracy_available"] is False
    assert not output.exists()
    assert _snapshot(synthetic_parent.evaluation) == synthetic_parent.before
    assert _snapshot(synthetic_parent.frozen) == synthetic_parent.frozen_before


def test_missing_key_does_not_claim_output_or_import_sdk(monkeypatch, synthetic_parent, tmp_path):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    _deny_sdk_import(monkeypatch)
    output = tmp_path / "never-claimed"
    with pytest.raises(RuntimeError, match="OPENAI_API_KEY"):
        _invoke(monkeypatch, runner, _run_args(synthetic_parent, output, mode="api", allow=True))
    assert not output.exists()
    assert _snapshot(synthetic_parent.evaluation) == synthetic_parent.before


def test_api_without_repository_consent_stops_before_output_or_sdk(monkeypatch, synthetic_parent, tmp_path):
    monkeypatch.setenv("OPENAI_API_KEY", "synthetic-unused-key")
    _deny_sdk_import(monkeypatch)
    output = tmp_path / "never-claimed"
    with pytest.raises(PermissionError, match="allow-repository-text-to-api"):
        _invoke(monkeypatch, runner, _run_args(synthetic_parent, output, mode="api"))
    assert not output.exists()


def test_partial_api_output_is_preserved_before_key_or_sdk(monkeypatch, synthetic_parent, tmp_path):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    _deny_sdk_import(monkeypatch)
    output = tmp_path / "interrupted"
    output.mkdir()
    sentinel = output / "RUN_ATTEMPT.json"
    sentinel.write_text("preserve this interrupted experiment", encoding="utf-8")
    before = _snapshot(output)
    with pytest.raises(FileExistsError, match="incomplete scope experiment"):
        _invoke(monkeypatch, runner, _run_args(synthetic_parent, output, mode="api", allow=True))
    assert _snapshot(output) == before


def test_fake_completion_is_labelled_cached_and_copies_only_unlabelled_inputs(completed_experiment):
    _, _, receipt, protocol, report = completed_experiment.snapshot
    assert receipt["experiment_kind"] == common.EXPERIMENT and receipt["mode"] == "api"
    assert protocol["source_run_id"] == completed_experiment.parent.checkpoint["run_id"]
    assert protocol["new_primary_api_requests"] == report["new_primary_api_requests"] == 0
    assert protocol["gold_labels_in_agent_inputs"] is False
    assert report["primary_prediction_origin"] == "CACHED_V49_PRIMARY"
    assert report["budget_usage"]["max_provider_requests"] == common.MAX_PROVIDER_REQUESTS
    assert report["budget_usage"]["provider_requests_reserved"] == 1
    assert len(report["verified_evidence"]) == 1
    working_path = completed_experiment.output / "working_checkpoints" / (receipt["run_id"] + ".json")
    assert working_path.is_file()
    working = common.read(working_path)
    assert working["run_id"] == receipt["run_id"]
    assert working["initial_state"] == completed_experiment.parent.state
    assert working["trace"][0]["pair_review_trace"][0]["phase"] == "cached_pair_classification"
    assert sorted(p.name for p in (completed_experiment.output / "inputs").iterdir()) == sorted(common.INPUT_NAMES)
    assert PRIVATE_MARKER not in "".join(p.read_text(encoding="utf-8")
                                        for p in (completed_experiment.output / "inputs").iterdir())
    assert PRIVATE_MARKER not in "".join(request["input"] for request in completed_experiment.provider.calls)


def test_completed_checker_reuse_needs_no_key_or_sdk_or_mutation(monkeypatch, completed_experiment, capsys):
    capsys.readouterr()
    before = _snapshot(completed_experiment.output)
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    _deny_sdk_import(monkeypatch)
    _invoke(monkeypatch, runner, _run_args(completed_experiment.parent, completed_experiment.output, mode="api"))
    assert "EXISTING_SCOPE_EXPERIMENT_VERIFIED_NO_API_CALLED" in capsys.readouterr().out
    assert _snapshot(completed_experiment.output) == before


@pytest.mark.parametrize("relative", ["PROTOCOL.json", "inputs/" + common.INPUT_NAMES[0],
    "inputs/" + common.INPUT_NAMES[1], "inputs/" + common.INPUT_NAMES[2], "run/report.json", "checkpoint"])
def test_completed_snapshot_rejects_byte_changed_member(completed_experiment, relative):
    if relative == "checkpoint":
        relative = completed_experiment.snapshot[2]["checkpoint_relative_path"]
    path = completed_experiment.output / relative
    path.write_bytes(path.read_bytes() + b"\n ")
    with pytest.raises(ValueError, match="hash mismatch"):
        common.output_snapshot(completed_experiment.output, CORE_ROOT)


def _score_args(completed, bundle=None):
    args = ["--code-root", CORE_ROOT, "--evaluation", completed.output,
            "--frozen", completed.parent.frozen]
    if bundle is not None:
        args += ["--output-bundle", bundle]
    return args


def test_scoring_commits_reuses_and_bundles_without_reference_leak(monkeypatch, completed_experiment, tmp_path, capsys):
    _deny_sdk_import(monkeypatch)
    capsys.readouterr()
    bundle = tmp_path / "scope-diagnostics.zip"
    _invoke(monkeypatch, scorer, _score_args(completed_experiment, bundle))
    metrics = common.read(completed_experiment.output / "score/metrics.json")
    assert metrics["experiment_kind"] == common.EXPERIMENT
    assert metrics["cached_primary_cost_is_not_zero"] is True and metrics["new_primary_api_requests"] == 0
    assert metrics["results"]["all"]["tp"] == metrics["results"]["baseline"]["tp"] == 1
    assert metrics["comparison"]["all"]["delta_recheck_minus_v49"] == 0
    assert len(completed_experiment.provider.calls) == 1
    common.output_snapshot(completed_experiment.output, CORE_ROOT)
    with zipfile.ZipFile(bundle) as archive:
        manifest = json.loads(archive.read("DIAGNOSTIC_BUNDLE_MANIFEST.json"))
        for name, digest in manifest["member_sha256"].items():
            assert hashlib.sha256(archive.read(name)).hexdigest() == digest
        assert "score/SCORE_RECEIPT.json" in archive.namelist()
        assert not any("HUNK_RELATIONS" in name for name in archive.namelist())
    before = _snapshot(completed_experiment.output)
    _invoke(monkeypatch, scorer, _score_args(completed_experiment))
    assert "EXISTING_SCOPE_SCORE_VERIFIED_NO_API_CALLED" in capsys.readouterr().out
    assert _snapshot(completed_experiment.output) == before
    assert _snapshot(completed_experiment.parent.evaluation) == completed_experiment.parent.before
    assert _snapshot(completed_experiment.parent.frozen) == completed_experiment.parent.frozen_before


def test_tampered_committed_score_cannot_be_reused_or_bundled(monkeypatch, completed_experiment, tmp_path):
    _invoke(monkeypatch, scorer, _score_args(completed_experiment))
    metrics = completed_experiment.output / "score/metrics.json"
    metrics.write_bytes(metrics.read_bytes() + b"\n ")
    destination = tmp_path / "never-created.zip"
    with pytest.raises(ValueError, match="hash mismatch"):
        _invoke(monkeypatch, scorer, _score_args(completed_experiment, destination))
    assert not destination.exists()


def test_interrupted_score_attempt_is_preserved_without_score_creation(monkeypatch, completed_experiment):
    attempt = completed_experiment.output / "SCORE_ATTEMPT.json"
    attempt.write_text("preserve interrupted scoring", encoding="utf-8")
    before = _snapshot(completed_experiment.output)
    with pytest.raises(FileExistsError, match="interrupted scope score"):
        _invoke(monkeypatch, scorer, _score_args(completed_experiment))
    assert not (completed_experiment.output / "score").exists()
    assert _snapshot(completed_experiment.output) == before


def test_incomplete_experiment_never_reads_reference_rows(monkeypatch, synthetic_parent, tmp_path):
    from _score_core import HUNK_FILE
    incomplete = tmp_path / "incomplete-experiment"
    incomplete.mkdir()
    original_open = Path.open
    def guarded(path, *args, **kwargs):
        if path.name == HUNK_FILE:
            pytest.fail("Reference rows read before a completed checker experiment")
        return original_open(path, *args, **kwargs)
    monkeypatch.setattr(Path, "open", guarded)
    args = ["--code-root", CORE_ROOT, "--evaluation", incomplete, "--frozen", synthetic_parent.frozen]
    with pytest.raises(ValueError, match="Missing/nonregular experiment file"):
        _invoke(monkeypatch, scorer, args)
    assert not (incomplete / "score").exists() and not (incomplete / "SCORE_ATTEMPT.json").exists()


def test_receipt_cannot_claim_a_different_cached_primary_run(completed_experiment):
    path = completed_experiment.output / "RUN_RECEIPT.json"
    receipt = common.read(path)
    receipt["source_run_id"] = "synthetic-different-primary"
    _write(path, receipt)
    with pytest.raises(ValueError, match="(?:source|primary|protocol|provenance).*mismatch"):
        common.output_snapshot(completed_experiment.output, CORE_ROOT)


def test_unscored_parent_stops_before_output_or_sdk(monkeypatch, synthetic_parent, tmp_path):
    for name in ["metrics.json", "link_errors.csv", "SCORE_RECEIPT.json"]:
        (synthetic_parent.evaluation / "score" / name).unlink()
    before = _snapshot(synthetic_parent.evaluation)
    monkeypatch.setenv("OPENAI_API_KEY", "synthetic-unused-key")
    _deny_sdk_import(monkeypatch)
    output = tmp_path / "never-claimed-unscored-parent"
    with pytest.raises(ValueError, match="(?i)score"):
        _invoke(monkeypatch, runner, _run_args(synthetic_parent, output, mode="api", allow=True))
    assert not output.exists()
    assert _snapshot(synthetic_parent.evaluation) == before


@pytest.mark.parametrize("name", ["_score_core.py", "prepare_v49.py", "bundle_v49_diagnostics.py"])
def test_changed_parent_helper_is_rejected_before_helper_import(monkeypatch, tmp_path, name):
    fake_root = tmp_path / "untrusted-parent-code"
    helpers = fake_root / "development_tools"
    helpers.mkdir(parents=True)
    for helper in common.PARENT_HELPER_SHA256:
        (helpers / helper).write_bytes((CORE_ROOT / "development_tools" / helper).read_bytes())
    changed = helpers / name
    changed.write_bytes(changed.read_bytes() + b"\n# synthetic byte drift\n")
    original_import = builtins.__import__
    def guarded(module_name, *args, **kwargs):
        if module_name in {"_score_core", "prepare_v49", "bundle_v49_diagnostics"}:
            pytest.fail("Untrusted parent helper imported before byte identity was verified")
        return original_import(module_name, *args, **kwargs)
    monkeypatch.setattr(builtins, "__import__", guarded)
    monkeypatch.setattr(sys, "path", sys.path.copy())
    with pytest.raises(ValueError, match="unchanged original v4.9 helper"):
        common.load_code(fake_root)


def test_committed_score_reuse_rechecks_unchanged_reference(monkeypatch, completed_experiment, tmp_path):
    from _score_core import HUNK_FILE
    _invoke(monkeypatch, scorer, _score_args(completed_experiment))
    before = _snapshot(completed_experiment.output)
    reference = completed_experiment.parent.frozen / "reference" / HUNK_FILE
    reference.write_bytes(reference.read_bytes() + b"\n")
    original_open = Path.open
    def guarded(path, *args, **kwargs):
        mode = args[0] if args else kwargs.get("mode", "r")
        if path.name == HUNK_FILE and "b" not in mode:
            pytest.fail("Changed reference rows interpreted before frozen byte identity passed")
        return original_open(path, *args, **kwargs)
    monkeypatch.setattr(Path, "open", guarded)
    _deny_sdk_import(monkeypatch)
    destination = tmp_path / "never-created-changed-reference.zip"
    with pytest.raises(ValueError, match="Hash mismatch for original frozen reference"):
        _invoke(monkeypatch, scorer, _score_args(completed_experiment, destination))
    assert not destination.exists()
    assert _snapshot(completed_experiment.output) == before


def test_incomplete_dry_forecast_does_not_claim_ready_or_create_output(monkeypatch, synthetic_parent, tmp_path, capsys):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    _deny_sdk_import(monkeypatch)
    monkeypatch.setattr(runner, "MAX_INPUT_TOKENS", 1)
    output = tmp_path / "never-created-failed-forecast"
    with pytest.raises(RuntimeError, match="forecast did not finish"):
        _invoke(monkeypatch, runner, _run_args(synthetic_parent, output))
    result = json.loads(capsys.readouterr().out)
    assert result["forecast_complete"] is False
    assert result["forecast_within_input_ceiling"] is False
    assert result["stopping_reason"] == "cumulative_input_token_limit"
    assert result["mock_checker_requests"] == 0 and result["new_primary_api_requests"] == 0
    assert result["output_created"] is False and not output.exists()
    assert _snapshot(synthetic_parent.evaluation) == synthetic_parent.before
    assert _snapshot(synthetic_parent.frozen) == synthetic_parent.frozen_before

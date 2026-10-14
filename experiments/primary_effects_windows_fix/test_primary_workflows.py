"""Portable fresh-classification workflow/provenance tests with fake transports.

Artificial reference notes never enter provider inputs. These tests verify the
transactions, projection and bounds, not a model's semantic accuracy or F1.
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
import _experiment_common as common
import run_primary_effect as runner
import score_primary_effect as scorer
import checkpoint_store as checkpoints
from test_effect_classifier import case, effect, reply

CORE_ROOT = Path(evorationale.__file__).resolve().parent.parent
PRIVATE_MARKER = "PRIVATE_GOLD_MARKER_ONLY_FOR_PRIMARY_SCORER_TEST"
CACHED_MARKER = "CACHED_OLD_PRIMARY_PROSE_NOT_FRESH_CLASSIFIER_INPUT"


def _sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def _write(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _snapshot(folder):
    return {str(p.relative_to(folder)): (p.read_bytes(), p.stat().st_mtime_ns)
            for p in folder.rglob("*") if p.is_file()}


class _ParentReplies:
    """A copied local adapter for the historical v4.9 response contract."""
    def __init__(self, responses):
        self.responses = list(responses)

    def create(self, **request):
        return SimpleNamespace(status="completed", output_text=json.dumps(self.responses.pop(0)))


def _old_parent_payload(state, history):
    """Construct a v4.9 checkpoint using only that released core, not scope kit."""
    from evorationale.delta_context import build_delta_catalog
    from evorationale.event_context import select_event_batches
    from evorationale.model import element_by_id
    from evorationale.pair_review_verification import PairReviewSemanticJudge
    batch = select_event_batches(state, history, 36)[0]
    catalog = build_delta_catalog(state, batch)
    old_effect = {"passage_handle": next(iter(catalog["passages"])), "element_id": "T1",
        "s0_claim_quote": state["implementation_scope"][0]["text"], "before_line_handles": [],
        "after_line_handles": list(catalog["lines"]), "context_line_handles": [],
        "before_claim": "There is no corresponding local source statement.",
        "after_claim": "The controller publishes admitted and applied allocations through WorkerStatus.",
        "change_kind": "documented_support", "source_role": "adopted_design",
        "claim_scope": "material_subclaim", "whole_element_supported": False, "scope_match": True,
        "material_target_delta": False, "replacement_is_explicit": False,
        "surviving_clause_masks_replacement": False, "confidence": .7,
        "evidence_basis": "adopted_design_statement", "qualification": "Source evidence, not deployment proof.",
        "reason": CACHED_MARKER, "effect_basis": "current_design_statement",
        "local_contribution": CACHED_MARKER, "current_claim_entailed": True,
        "context_establishes_replacement": False}
    primary = {"considered_element_ids": list(element_by_id(state)), "reviews": [{
        "artifact_handle": "A0001", "status": "relation_found", "reason": "All target pairs reviewed.",
        "support_reason": "Source support assessed.", "change_reason": "Contract drift assessed.",
        "links": [old_effect], "pair_outcomes": [{"element_id": key,
            "outcome": "relation_found" if key == "T1" else "no_relation",
            "reason": "Exact predicate reviewed.", "relations": ["supports"] if key == "T1" else []}
            for key in element_by_id(state)]}]}
    decision = {"candidate_id": "C0001", "verdict": "confirm", "reason": "Qualified source support assessed.",
        "predicate_reason": "The exact published contract is stated.",
        "contribution_reason": "The local statement adds qualified evidence.",
        "authority_reason": "The adopted source authority matches the hypothesis."}
    judge = PairReviewSemanticJudge("synthetic-no-api-model",
        client=SimpleNamespace(responses=_ParentReplies([primary, {"decisions": [decision]}])))
    accepted, rejected = judge.review_event(state, batch, [])
    assert len(accepted) == 1 and not any(x.get("failure_class") == "technical_verification_failure" for x in rejected)
    checkpoint = {"run_id": "synthetic-v49-primary-parent", "initial_state": deepcopy(state),
        "verified_links": accepted, "rejected_interpretations": rejected,
        "report": {"investigation_profile": "event-pair-reviewed", "verified_evidence": deepcopy(accepted)},
        "trace": [{"round": 1, "profile": "event-pair-reviewed", "verification": "EVENT_REVIEW_COMPLETED",
            "retrieved_artifact_keys": catalog["context"]["artifact_keys"],
            "independent_artifact_reviews": deepcopy(judge.last_reviews),
            "pair_review_trace": deepcopy(judge.last_pair_review_trace)}]}
    return checkpoint


@pytest.fixture
def synthetic_parent(tmp_path):
    """A internally consistent artificial parent receipt and private reference."""
    sys.path.insert(0, str(CORE_ROOT / "development_tools"))
    from prepare_v49 import KIND, PROFILE, SEMANTIC_PHASE_CONFIG, POLICY_CHANGE_NOTE
    from _score_core import HUNK_FILE, EVAL_SCOPES, evaluate
    from evorationale.model import validate_state
    state, history, _ = case()
    baseline_raw = ("# Synthetic historical contract\n"
                    + state["implementation_scope"][0]["text"] + "\n"
                    + state["requirements"][0]["text"] + "\n"
                    + "Historical context only; not post-baseline proof.\n").encode("utf-8")
    state["baseline_git_commit"] = "a" * 40
    state["baseline_readme_git_blob_sha1"] = hashlib.sha1(
        b"blob " + str(len(baseline_raw)).encode("ascii") + b"\0" + baseline_raw).hexdigest()
    for group in ["implementation_scope", "requirements"]:
        for target in state[group]:
            target["source"] = "https://github.com/synthetic/contracts/blob/" + "a" * 40 + "/README.md#L2-L3"
    state = validate_state(state)
    checkpoint = _old_parent_payload(state, history)
    evaluation, frozen = tmp_path / "original49", tmp_path / "synthetic-freeze"
    baseline_path = tmp_path / "public-baseline_README.md"
    baseline_path.write_bytes(baseline_raw)
    _write(evaluation / "inputs" / common.INPUT_NAMES[0], state)
    history_file = evaluation / "inputs" / common.INPUT_NAMES[1]
    history_file.write_text("".join(json.dumps(a, sort_keys=True) + "\n" for a in history), encoding="utf-8")
    _write(frozen / "S0_ATOMIC_REVIEWER_CONFIRMED.json", state)
    reference_file = frozen / "reference" / HUNK_FILE
    reference_file.parent.mkdir(parents=True)
    rows = [{"hunk_id": history[0]["artifact_id"], "relation_candidate": "SUPPORTS",
             "related_atomic_s0_ids": "T1", "temporal_basis_inherited_from_event": "BASELINE_2023",
             "private_review_note": PRIVATE_MARKER}]
    rows += [{"hunk_id": f"synthetic-unused-{n:02d}", "relation_candidate": "UNRELATED",
              "related_atomic_s0_ids": "", "temporal_basis_inherited_from_event": "BASELINE_2023",
              "private_review_note": PRIVATE_MARKER} for n in range(1, 30)]
    with reference_file.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    _write(frozen / "FREEZE_MANIFEST.json", {"s0_sha256": _sha(frozen / "S0_ATOMIC_REVIEWER_CONFIRMED.json"),
        "reference_sha256": {HUNK_FILE: _sha(reference_file)}})
    models = {"judge": "synthetic-no-api-model", "linker": "synthetic-no-api-model"}
    old_budget = {"max_rounds": 1, "max_queries": 1, "max_reads": 36, "max_input_tokens": 100000}
    budget = {**old_budget, "max_input_tokens": 400000, "max_provider_requests": 36}
    cfg = {"kind": KIND, "investigation_profile": PROFILE, "nomination_mode": "none", "models": models,
        "budgets": budget, "parent_v46_budgets": old_budget,
        **{name: deepcopy(models) for name in ["parent_v44_models", "parent_v45_models", "parent_v46_models",
            "parent_v47_models", "parent_v48_models"]}, "semantic_phase_config": deepcopy(SEMANTIC_PHASE_CONFIG),
        "policy_change_note": POLICY_CHANGE_NOTE, "v49_python_sha256": common.PARENT_CORE_SHA256,
        "runtime_s0_sha256": _sha(evaluation / "inputs" / common.INPUT_NAMES[0]), "history_sha256": _sha(history_file),
        "frozen_s0_sha256": _sha(frozen / "S0_ATOMIC_REVIEWER_CONFIRMED.json"),
        "frozen_manifest_sha256": _sha(frozen / "FREEZE_MANIFEST.json"), "gold_labels_in_agent_inputs": False}
    _write(evaluation / "DEV_PREP_MANIFEST.json", cfg)
    run_id = checkpoint["run_id"]
    checkpoint_name = "checkpoints/" + run_id + ".json"
    _write(evaluation / checkpoint_name, checkpoint)
    _write(evaluation / "run/report.json", checkpoint["report"])
    report_hash = _sha(evaluation / "run/report.json")
    _write(evaluation / "run/manifest.json", {"run_id": run_id, "mode": "api", "investigation_profile": PROFILE,
        "nomination_mode": "none", "max_provider_requests": 36, "decision_sha256": cfg["runtime_s0_sha256"],
        "history_sha256": cfg["history_sha256"], "report_sha256": report_hash})
    _write(evaluation / "RUN_RECEIPT.json", {"status": "V49_DEV_HOSTED_RUN_COMPLETED_AND_HASHED", "run_id": run_id,
        "mode": "api", "investigation_profile": PROFILE, "nomination_mode": "none",
        "code_tree_sha256": cfg["v49_python_sha256"], "model": models, "nominal_budgets": budget,
        **{name: cfg[name] for name in ["parent_v44_models", "parent_v45_models", "parent_v46_models",
            "parent_v47_models", "parent_v48_models", "semantic_phase_config", "policy_change_note"]},
        "prep_sha256": _sha(evaluation / "DEV_PREP_MANIFEST.json"), "run_report_sha256": report_hash,
        "run_manifest_sha256": _sha(evaluation / "run/manifest.json"), "checkpoint_relative_path": checkpoint_name,
        "checkpoint_sha256": _sha(evaluation / checkpoint_name)})
    metrics = {"status": "V49_DEVELOPMENT_ONLY_POST_RUN_REFERENCE_COMPARISON", "v49_run_report_sha256": report_hash,
        "v49_code_sha256": cfg["v49_python_sha256"], "frozen_s0_sha256": cfg["frozen_s0_sha256"],
        "nomination_mode": "none", "nominal_budgets": budget, "semantic_phase_config": deepcopy(SEMANTIC_PHASE_CONFIG),
        "results": {scope: evaluate(rows, checkpoint["report"], scope)[0] for scope in EVAL_SCOPES}}
    _write(evaluation / "score/metrics.json", metrics)
    (evaluation / "score/link_errors.csv").write_text(
        "scope,verdict,hunk_id,atomic_s0_id,relation,reference_hunk_relation,temporal_basis\n", encoding="utf-8")
    _write(evaluation / "score/SCORE_RECEIPT.json", {"status": "V49_SCORE_COMMITTED", "run_report_sha256": report_hash,
        "core_sha256": cfg["v49_python_sha256"], "frozen_manifest_sha256": cfg["frozen_manifest_sha256"],
        "metrics_sha256": _sha(evaluation / "score/metrics.json"), "link_errors_sha256": _sha(evaluation / "score/link_errors.csv")})
    verified = common.verified_parent(CORE_ROOT, evaluation)
    assert verified["checkpoint"] == checkpoint
    return SimpleNamespace(evaluation=evaluation, frozen=frozen, state=state, history=history, config=cfg,
        checkpoint=checkpoint, verified=verified, baseline_path=baseline_path, baseline_raw=baseline_raw,
        before=_snapshot(evaluation), frozen_before=_snapshot(frozen))


def _invoke(monkeypatch, module, args):
    monkeypatch.setattr(sys, "argv", [str(Path(module.__file__)), *map(str, args)])
    return module.main()


def _run_args(parent, output, mode=None, allow=False):
    args = ["--code-root", CORE_ROOT, "--evaluation", parent.evaluation, "--output", output,
            "--baseline-readme", parent.baseline_path]
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


class CompletingPrimary:
    def __init__(self, parent, effect_changes=None, fail=False):
        from evorationale.delta_context import build_delta_catalog
        self.state = parent.state
        self.catalog = build_delta_catalog(parent.state, parent.history)
        self.changes, self.fail, self.calls = effect_changes or {}, fail, []

    def create(self, **request):
        self.calls.append(deepcopy(request))
        assert PRIVATE_MARKER not in request["input"] and CACHED_MARKER not in request["input"]
        assert request["text"]["format"]["name"] == "primary_hunk_effect_review"
        if self.fail:
            raise RuntimeError("TRANSPORT_PRIVATE_TEXT_MUST_NOT_BE_PRINTED")
        first = effect(self.state, self.catalog, **self.changes)
        secondary = effect(self.state, self.catalog, element_id="T2",
            target_quote=self.state["requirements"][0]["text"])
        response = reply(self.catalog, [first], [secondary])
        return SimpleNamespace(status="completed", output_text=json.dumps(response),
            usage={"input_tokens": 61, "output_tokens": 47, "total_tokens": 108})


def _complete(monkeypatch, parent, output, provider=None):
    provider = provider or CompletingPrimary(parent)
    constructors = []
    def sdk(**kwargs):
        constructors.append(kwargs)
        return SimpleNamespace(responses=provider)
    monkeypatch.setitem(sys.modules, "openai", SimpleNamespace(OpenAI=sdk))
    monkeypatch.setenv("OPENAI_API_KEY", "synthetic-unused-key")
    _invoke(monkeypatch, runner, _run_args(parent, output, mode="api", allow=True))
    assert constructors == [{"max_retries": 0}]
    return SimpleNamespace(parent=parent, output=output, provider=provider,
        snapshot=common.output_snapshot(output, CORE_ROOT))


@pytest.fixture
def completed_experiment(monkeypatch, synthetic_parent, tmp_path):
    completed = _complete(monkeypatch, synthetic_parent, tmp_path / "new-primary-experiment")
    assert _snapshot(synthetic_parent.evaluation) == synthetic_parent.before
    assert _snapshot(synthetic_parent.frozen) == synthetic_parent.frozen_before
    return completed


def _score_args(completed, bundle=None):
    args = ["--code-root", CORE_ROOT, "--evaluation", completed.output, "--frozen", completed.parent.frozen]
    if bundle is not None:
        args += ["--output-bundle", bundle]
    return args


def test_default_dry_run_has_no_sdk_key_or_output(monkeypatch, synthetic_parent, tmp_path, capsys):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    _deny_sdk_import(monkeypatch)
    output = tmp_path / "never-created"
    _invoke(monkeypatch, runner, _run_args(synthetic_parent, output))
    result = json.loads(capsys.readouterr().out)
    assert result["status"] == "PRIMARY_EFFECT_DRY_RUN_NO_API_CALLED"
    assert result["mock_primary_requests"] == 1 and result["independent_critic_requests"] == 0
    assert result["forecast_complete"] is True and result["hosted_accuracy_available"] is False
    assert result["output_created"] is False and not output.exists()
    assert _snapshot(synthetic_parent.evaluation) == synthetic_parent.before
    assert _snapshot(synthetic_parent.frozen) == synthetic_parent.frozen_before


def test_changed_raw_baseline_fails_before_sdk_or_output(monkeypatch, synthetic_parent, tmp_path):
    synthetic_parent.baseline_path.write_bytes(synthetic_parent.baseline_raw + b"\n")
    _deny_sdk_import(monkeypatch)
    output = tmp_path / "never-claimed-bad-baseline"
    with pytest.raises(ValueError, match="Git blob"):
        _invoke(monkeypatch, runner, _run_args(synthetic_parent, output, mode="api", allow=True))
    assert not output.exists()


def test_incomplete_dry_forecast_does_not_claim_ready_or_output(monkeypatch, synthetic_parent, tmp_path, capsys):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    _deny_sdk_import(monkeypatch)
    monkeypatch.setattr(runner, "MAX_INPUT_TOKENS", 1)
    output = tmp_path / "never-created-bounded-forecast"
    with pytest.raises(RuntimeError, match="Forecast incomplete"):
        _invoke(monkeypatch, runner, _run_args(synthetic_parent, output))
    result = json.loads(capsys.readouterr().out)
    assert result["forecast_complete"] is False and result["forecast_within_input_ceiling"] is False
    assert result["mock_primary_requests"] == 0 and result["output_created"] is False
    assert not output.exists()


@pytest.mark.parametrize("allow,key,error", [(True, "", RuntimeError), (True, "   ", RuntimeError),
                                             (False, "synthetic-unused-key", PermissionError)])
def test_credential_and_consent_guards_precede_sdk_and_claim(monkeypatch, synthetic_parent, tmp_path, allow, key, error):
    monkeypatch.setenv("OPENAI_API_KEY", key)
    _deny_sdk_import(monkeypatch)
    output = tmp_path / "never-claimed-credential-guard"
    with pytest.raises(error):
        _invoke(monkeypatch, runner, _run_args(synthetic_parent, output, mode="api", allow=allow))
    assert not output.exists()


def test_partial_api_output_is_preserved_before_sdk(monkeypatch, synthetic_parent, tmp_path):
    output = tmp_path / "partial-experiment"
    output.mkdir()
    (output / "RUN_ATTEMPT.json").write_text("preserve interrupted experiment", encoding="utf-8")
    before = _snapshot(output)
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    _deny_sdk_import(monkeypatch)
    with pytest.raises(FileExistsError, match="Preserve partial experiment"):
        _invoke(monkeypatch, runner, _run_args(synthetic_parent, output, mode="api", allow=True))
    assert _snapshot(output) == before


def test_fresh_completion_scored_projection_preserves_secondary_and_context_privacy(completed_experiment):
    data, _, receipt, protocol, report = completed_experiment.snapshot
    assert protocol["gold_labels_in_agent_inputs"] is False
    assert protocol["prediction_unit"] == "ONE_PRIMARY_RELATION_TYPE_PER_HUNK_WITH_PRIMARY_TARGET_IDS"
    assert protocol["secondary_relations_scored"] is report["secondary_effects_scored"] is False
    assert report["new_primary_classification"] is True and report["independent_semantic_critic"] is False
    assert report["secondary_effect_count"] == 1
    assert report["budget_usage"]["provider_requests_reserved"] == 1
    assert report["budget_usage"]["max_provider_requests"] == 24
    assert len(report["verified_evidence"]) == 1
    link = report["verified_evidence"][0]
    assert link["decision_element_id"] == "T1" and link["prediction_projection"] == "PRIMARY_HUNK_EFFECT"
    assert link["target_version"] == "fixed_s0" and link["baseline_change_asserted"] is False
    assert link["semantic_assessment"]["epistemic_status"] == "MODEL_ASSESSED"
    assert report["architecture_outcome"] == "NOT_EVALUATED"
    working = common.read(completed_experiment.output / "working_checkpoints" / (receipt["run_id"] + ".json"))
    chunk = working["trace"][0]["focused_chunks"][0]
    assert chunk["status"] == "VALIDATED"
    assert len(chunk["reviews"][0]["primary_effects"]) == len(chunk["reviews"][0]["secondary_effects"]) == 1
    assert working["initial_state"] == completed_experiment.parent.state
    assert sorted(p.name for p in (completed_experiment.output / "inputs").iterdir()) == sorted(common.INPUT_NAMES)
    assert data["inputs/" + common.INPUT_NAMES[2]] == completed_experiment.parent.baseline_raw
    inputs = "".join(raw.decode() for name, raw in data.items() if name.startswith("inputs/"))
    assert PRIVATE_MARKER not in inputs and CACHED_MARKER not in inputs
    assert PRIVATE_MARKER not in json.dumps(protocol)
    payload = json.loads(completed_experiment.provider.calls[0]["input"])
    assert payload["baseline_context"]["fresh_post_s0_evidence"] is False
    assert payload["baseline_context"]["all_fixed_target_ranges_selected"] is True
    assert payload["baseline_context"]["role"] == "BASELINE_CONTEXT_ONLY_NOT_FRESH_POST_S0_PROOF"
    assert CACHED_MARKER not in json.dumps(payload) and PRIVATE_MARKER not in json.dumps(payload)


def test_false_fresh_contribution_is_recorded_and_cannot_be_scored_as_primary(monkeypatch, synthetic_parent, tmp_path):
    provider = CompletingPrimary(synthetic_parent, {"fresh_contribution": False})
    completed = _complete(monkeypatch, synthetic_parent, tmp_path / "guarded-primary", provider)
    report = completed.snapshot[-1]
    assert report["coverage"]["planned_review_complete"] is True and not report["verified_evidence"]
    assert report["secondary_effect_count"] == 1 and not report["technical_failures"]
    checkpoint = common.read(completed.output / completed.snapshot[2]["checkpoint_relative_path"])
    feedback = checkpoint["trace"][0]["focused_chunks"][0]["source_feedback"]
    assert "MODEL_ASSESSED:primary_effect_scope_or_fresh_contribution_not_established" in feedback[0]["reasons"]
    _invoke(monkeypatch, scorer, _score_args(completed))
    metrics = common.read(completed.output / "score/metrics.json")
    assert metrics["results"]["all"]["tp"] == metrics["results"]["all"]["fp"] == 0
    assert metrics["results"]["all"]["fn"] == 1


def test_transport_failure_preserves_checkpoint_and_never_reuses_or_scores(monkeypatch, synthetic_parent, tmp_path, capsys):
    provider = CompletingPrimary(synthetic_parent, fail=True)
    monkeypatch.setitem(sys.modules, "openai", SimpleNamespace(OpenAI=lambda **kw: SimpleNamespace(responses=provider)))
    monkeypatch.setenv("OPENAI_API_KEY", "synthetic-unused-key")
    output = tmp_path / "failed-fresh-experiment"
    with pytest.raises(RuntimeError, match="Incomplete classification preserved"):
        _invoke(monkeypatch, runner, _run_args(synthetic_parent, output, mode="api", allow=True))
    assert "TRANSPORT_PRIVATE_TEXT_MUST_NOT_BE_PRINTED" not in capsys.readouterr().out
    _, _, receipt, _, report = common.output_snapshot(output, CORE_ROOT)
    assert report["status"] == "EXPERIMENT_INCOMPLETE" and report["coverage"]["planned_review_complete"] is False
    assert report["technical_failures"][0]["failure_class"] == "RuntimeError"
    assert (output / "working_checkpoints" / (receipt["run_id"] + ".json")).is_file()
    before = _snapshot(output)
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    _deny_sdk_import(monkeypatch)
    with pytest.raises(FileExistsError, match="Preserve incomplete experiment"):
        _invoke(monkeypatch, runner, _run_args(synthetic_parent, output, mode="api", allow=True))
    from _score_core import HUNK_FILE
    original_open = Path.open
    def guarded(path, *args, **kwargs):
        mode = args[0] if args else kwargs.get("mode", "r")
        if path.name == HUNK_FILE and "b" not in mode:
            pytest.fail("Reference rows interpreted before complete classification")
        return original_open(path, *args, **kwargs)
    monkeypatch.setattr(Path, "open", guarded)
    with pytest.raises(ValueError, match="Incomplete primary-effect experiment"):
        _invoke(monkeypatch, scorer, ["--code-root", CORE_ROOT, "--evaluation", output, "--frozen", synthetic_parent.frozen])
    assert _snapshot(output) == before and not (output / "score").exists()


def test_completed_reuse_needs_no_key_sdk_or_mutation(monkeypatch, completed_experiment, capsys):
    capsys.readouterr()
    before = _snapshot(completed_experiment.output)
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    _deny_sdk_import(monkeypatch)
    _invoke(monkeypatch, runner, _run_args(completed_experiment.parent, completed_experiment.output, mode="api"))
    assert "EXISTING_PRIMARY_EFFECT_EXPERIMENT_VERIFIED_NO_API_CALLED" in capsys.readouterr().out
    assert _snapshot(completed_experiment.output) == before


def test_completed_reuse_pins_all_original_source_members(monkeypatch, completed_experiment):
    parent = completed_experiment.parent
    path = parent.evaluation / "score/link_errors.csv"
    path.write_bytes(path.read_bytes() + b"\n")
    receipt_path = parent.evaluation / "score/SCORE_RECEIPT.json"
    receipt = common.read(receipt_path)
    receipt["link_errors_sha256"] = _sha(path)
    _write(receipt_path, receipt)
    before = _snapshot(completed_experiment.output)
    _deny_sdk_import(monkeypatch)
    with pytest.raises(ValueError, match="different source/context"):
        _invoke(monkeypatch, runner, _run_args(parent, completed_experiment.output, mode="api"))
    assert _snapshot(completed_experiment.output) == before


@pytest.mark.parametrize("relative", ["PROTOCOL.json", "inputs/" + common.INPUT_NAMES[0],
    "inputs/" + common.INPUT_NAMES[1], "inputs/" + common.INPUT_NAMES[2], "run/report.json", "checkpoint"])
def test_snapshot_rejects_changed_input_context_or_result(completed_experiment, relative):
    if relative == "checkpoint":
        relative = completed_experiment.snapshot[2]["checkpoint_relative_path"]
    path = completed_experiment.output / relative
    path.write_bytes(path.read_bytes() + b"\n ")
    with pytest.raises(ValueError, match="hash mismatch"):
        common.output_snapshot(completed_experiment.output, CORE_ROOT)


@pytest.mark.parametrize("field,value", [("source_run_id", "different-parent"), ("mode", "dry-run")])
def test_receipt_identity_or_mode_cannot_be_forged(completed_experiment, field, value):
    path = completed_experiment.output / "RUN_RECEIPT.json"
    record = common.read(path)
    record[field] = value
    _write(path, record)
    with pytest.raises(ValueError, match="(?i)(?:protocol mismatch|completed real)"):
        common.output_snapshot(completed_experiment.output, CORE_ROOT)


def test_scoring_commits_primary_only_with_unchanged_scorer_and_bundle_hashes(monkeypatch, completed_experiment, tmp_path, capsys):
    _deny_sdk_import(monkeypatch)
    bundle = tmp_path / "primary-diagnostics.zip"
    _invoke(monkeypatch, scorer, _score_args(completed_experiment, bundle))
    metrics = common.read(completed_experiment.output / "score/metrics.json")
    assert metrics["experiment_kind"] == common.EXPERIMENT
    assert metrics["independent_critic_api_requests"] == 0 and metrics["new_primary_api_requests"] == 1
    assert metrics["results"]["all"]["tp"] == metrics["results"]["baseline"]["tp"] == 1
    assert metrics["results"]["all"]["fp"] == 0
    assert metrics["results"]["all"]["predicted_exact_triples"] == 1
    assert metrics["comparison"]["all"]["delta_primary_minus_v49"] == 0
    assert "projection" in " ".join(metrics["limitations"]).lower()
    common.output_snapshot(completed_experiment.output, CORE_ROOT)
    with zipfile.ZipFile(bundle) as archive:
        manifest = json.loads(archive.read("DIAGNOSTIC_BUNDLE_MANIFEST.json"))
        for name, digest in manifest["member_sha256"].items():
            assert hashlib.sha256(archive.read(name)).hexdigest() == digest
        assert "score/SCORE_RECEIPT.json" in archive.namelist()
        assert not any("HUNK_RELATIONS" in name for name in archive.namelist())
        assert PRIVATE_MARKER not in "".join(archive.read(name).decode() for name in archive.namelist())
    before = _snapshot(completed_experiment.output)
    _invoke(monkeypatch, scorer, _score_args(completed_experiment))
    assert "EXISTING_PRIMARY_EFFECT_SCORE_VERIFIED_NO_API_CALLED" in capsys.readouterr().out
    assert _snapshot(completed_experiment.output) == before
    assert _snapshot(completed_experiment.parent.evaluation) == completed_experiment.parent.before
    assert _snapshot(completed_experiment.parent.frozen) == completed_experiment.parent.frozen_before


def test_denominator_change_prevents_atomic_score_commit(monkeypatch, synthetic_parent, tmp_path):
    path = synthetic_parent.evaluation / "score/metrics.json"
    metrics = common.read(path)
    for result in metrics["results"].values():
        result["gold_positive_exact_triples"] += 1
    _write(path, metrics)
    receipt_path = synthetic_parent.evaluation / "score/SCORE_RECEIPT.json"
    receipt = common.read(receipt_path)
    receipt["metrics_sha256"] = _sha(path)
    _write(receipt_path, receipt)
    synthetic_parent.before = _snapshot(synthetic_parent.evaluation)
    completed = _complete(monkeypatch, synthetic_parent, tmp_path / "denominator-run")
    with pytest.raises(ValueError, match="denominator changed"):
        _invoke(monkeypatch, scorer, _score_args(completed))
    assert not (completed.output / "score").exists()
    assert (completed.output / "SCORE_ATTEMPT.json").is_file()


def test_committed_score_or_frozen_s0_tamper_prevents_reuse(monkeypatch, completed_experiment):
    _invoke(monkeypatch, scorer, _score_args(completed_experiment))
    frozen_s0 = completed_experiment.parent.frozen / "S0_ATOMIC_REVIEWER_CONFIRMED.json"
    frozen_s0.write_bytes(frozen_s0.read_bytes() + b"\n")
    before = _snapshot(completed_experiment.output)
    with pytest.raises(ValueError, match="Hash mismatch for original frozen S0"):
        _invoke(monkeypatch, scorer, _score_args(completed_experiment))
    assert _snapshot(completed_experiment.output) == before


def test_changed_committed_score_cannot_be_bundled(monkeypatch, completed_experiment, tmp_path):
    _invoke(monkeypatch, scorer, _score_args(completed_experiment))
    path = completed_experiment.output / "score/metrics.json"
    path.write_bytes(path.read_bytes() + b"\n")
    destination = tmp_path / "never-created.zip"
    with pytest.raises(ValueError, match="hash mismatch"):
        _invoke(monkeypatch, scorer, _score_args(completed_experiment, destination))
    assert not destination.exists()


def test_interrupted_score_attempt_is_preserved(monkeypatch, completed_experiment):
    path = completed_experiment.output / "SCORE_ATTEMPT.json"
    path.write_text("preserve interrupted score", encoding="utf-8")
    before = _snapshot(completed_experiment.output)
    with pytest.raises(FileExistsError, match="interrupted primary-effect score"):
        _invoke(monkeypatch, scorer, _score_args(completed_experiment))
    assert not (completed_experiment.output / "score").exists()
    assert _snapshot(completed_experiment.output) == before


def test_unscored_parent_fails_before_sdk_or_claim(monkeypatch, synthetic_parent, tmp_path):
    for name in ["metrics.json", "link_errors.csv", "SCORE_RECEIPT.json"]:
        (synthetic_parent.evaluation / "score" / name).unlink()
    before = _snapshot(synthetic_parent.evaluation)
    _deny_sdk_import(monkeypatch)
    output = tmp_path / "never-claimed-unscored-parent"
    with pytest.raises(ValueError, match="(?i)score"):
        _invoke(monkeypatch, runner, _run_args(synthetic_parent, output, mode="api", allow=True))
    assert not output.exists() and _snapshot(synthetic_parent.evaluation) == before


@pytest.mark.parametrize("name", ["_score_core.py", "prepare_v49.py", "bundle_v49_diagnostics.py"])
def test_changed_original_helper_fails_before_import(monkeypatch, tmp_path, name):
    fake_root = tmp_path / "untrusted-code"
    helpers = fake_root / "development_tools"
    helpers.mkdir(parents=True)
    for helper in common.PARENT_HELPER_SHA256:
        (helpers / helper).write_bytes((CORE_ROOT / "development_tools" / helper).read_bytes())
    changed = helpers / name
    changed.write_bytes(changed.read_bytes() + b"\n# synthetic helper drift\n")
    original_import = builtins.__import__
    def guarded(module_name, *args, **kwargs):
        if module_name in {"_score_core", "prepare_v49", "bundle_v49_diagnostics"}:
            pytest.fail("Untrusted helper imported before its byte identity check")
        return original_import(module_name, *args, **kwargs)
    monkeypatch.setattr(builtins, "__import__", guarded)
    monkeypatch.setattr(sys, "path", sys.path.copy())
    with pytest.raises(ValueError, match="unchanged original v4.9 helper"):
        common.load_code(fake_root)


def _checkpoint_lock_error():
    error = PermissionError(13, "Injected Windows checkpoint sharing denial")
    error.winerror = 5
    return error


def test_checkpoint_transient_retry_keeps_single_provider_response(monkeypatch, synthetic_parent, tmp_path):
    provider = CompletingPrimary(synthetic_parent)
    original_replace = checkpoints._replace
    denied, sleeps, pending_bytes = [], [], []

    def commit(pending, destination):
        if provider.calls and len(denied) < 2:
            denied.append(Path(pending))
            pending_bytes.append(Path(pending).read_bytes())
            raise _checkpoint_lock_error()
        return original_replace(pending, destination)

    monkeypatch.setattr(checkpoints, "_replace", commit)
    monkeypatch.setattr(checkpoints, "_sleep", sleeps.append)
    completed = _complete(monkeypatch, synthetic_parent, tmp_path / "transient-checkpoint", provider)
    assert len(provider.calls) == 1
    assert denied[0] == denied[1] and pending_bytes[0] == pending_bytes[1]
    assert sleeps == list(checkpoints.RETRY_DELAYS[:2])
    _, _, receipt, protocol, report = completed.snapshot
    assert report["coverage"]["planned_review_complete"] is True
    assert report["budget_usage"]["provider_requests_reserved"] == 1
    assert protocol["checkpoint_write_policy"] == checkpoints.CHECKPOINT_POLICY
    working = common.read(completed.output / "working_checkpoints" / (receipt["run_id"] + ".json"))
    assert working["trace"][0]["focused_chunks"][0]["status"] == "VALIDATED"
    assert not list((completed.output / "working_checkpoints").glob("*.pending"))
    assert _snapshot(synthetic_parent.evaluation) == synthetic_parent.before
    assert _snapshot(synthetic_parent.frozen) == synthetic_parent.frozen_before


@pytest.mark.parametrize("after_response", [False, True])
def test_checkpoint_persistent_failure_stops_and_refuses_api_replay(monkeypatch, synthetic_parent,
                                                                  tmp_path, after_response):
    provider = CompletingPrimary(synthetic_parent)
    output = tmp_path / ("locked-after-response" if after_response else "locked-initial-save")
    original_replace = checkpoints._replace
    denied, sleeps, previous_bytes = [], [], []

    def commit(pending, destination):
        if after_response and not provider.calls:
            result = original_replace(pending, destination)
            previous_bytes.append(Path(destination).read_bytes())
            return result
        denied.append(Path(pending))
        raise _checkpoint_lock_error()

    monkeypatch.setattr(checkpoints, "_replace", commit)
    monkeypatch.setattr(checkpoints, "_sleep", sleeps.append)
    with pytest.raises(checkpoints.CheckpointWriteError) as failed:
        _complete(monkeypatch, synthetic_parent, output, provider)
    error = failed.value
    assert len(denied) == error.attempts == len(checkpoints.RETRY_DELAYS) + 1
    assert sleeps == list(checkpoints.RETRY_DELAYS)
    assert len(provider.calls) == int(after_response)
    assert (output / "RUN_ATTEMPT.json").is_file()
    assert not (output / "RUN_RECEIPT.json").exists()
    pending = common.read(error.pending_path)
    assert pending["status"] == "RUNNING"
    if after_response:
        assert error.checkpoint_path.read_bytes() == previous_bytes[0]
        old = common.read(error.checkpoint_path)
        assert old["trace"] == [] and old["verified_links"] == []
        chunk = pending["trace"][0]["focused_chunks"][0]
        assert chunk["status"] == "VALIDATED" and chunk["reviews"][0]["primary_effects"]
        assert len(pending["verified_links"]) == 1
    else:
        assert not error.checkpoint_path.exists()
        assert pending["trace"] == [] and pending["verified_links"] == []
    before = _snapshot(output)
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    _deny_sdk_import(monkeypatch)
    with pytest.raises(FileExistsError, match="Preserve partial experiment"):
        _invoke(monkeypatch, runner, _run_args(synthetic_parent, output, mode="api", allow=True))
    assert len(provider.calls) == int(after_response)
    assert _snapshot(output) == before
    assert _snapshot(synthetic_parent.evaluation) == synthetic_parent.before
    assert _snapshot(synthetic_parent.frozen) == synthetic_parent.frozen_before

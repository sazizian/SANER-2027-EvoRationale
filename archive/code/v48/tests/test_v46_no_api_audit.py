"""Canonical source and no-provider transport preflight; no semantic gold data."""
from copy import deepcopy
import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import sys

import pytest

from evorationale.delta_context import build_delta_catalog
from evorationale.event_context import select_event_batches
from evorationale.model import ValidationError, normalize_artifact

TOOL = Path(__file__).resolve().parents[1] / "development_tools" / "audit_v46_no_api.py"
spec = importlib.util.spec_from_file_location("audit_v46_no_api_fixture", TOOL)
audit = importlib.util.module_from_spec(spec)
spec.loader.exec_module(audit)
MODELS = {"linker": "opaque-fixture-proposer", "judge": "opaque-fixture-independent"}
BUDGETS = {"max_rounds": 2, "max_queries": 2, "max_reads": 2,
           "max_input_tokens": 100000, "max_output_tokens": 1100}


def source(state, name="edit", commit="a" * 40, content=None):
    return normalize_artifact({"artifact_id": name, "repository": state["repository"],
        "source_type": "git_commit_diff_hunk", "source_location": "fixture://source",
        "source_commit_sha": commit, "source_file": "design.md", "title": "Source edit",
        "timestamp": "2024-02-01T00:00:00Z",
        "content": content or "@@ -1 +1 @@\n-Previous statement.\n+New statement.\n"})


def prepared(tmp_path, state):
    root = tmp_path / "prepared evaluation"
    inputs = root / "inputs"
    inputs.mkdir(parents=True)
    decision_bytes = (json.dumps(state) + "\n").encode()
    history_bytes = (json.dumps(source(state)) + "\n").encode()
    (inputs / audit.DECISION_NAME).write_bytes(decision_bytes)
    (inputs / audit.HISTORY_NAME).write_bytes(history_bytes)
    config = {"kind": "DEVELOPMENT_ONLY_V46_EVENT_EVIDENCE_COMPARISON",
              "investigation_profile": "event-evidence", "gold_labels_in_agent_inputs": False,
              "runtime_s0_sha256": hashlib.sha256(decision_bytes).hexdigest(),
              "history_sha256": hashlib.sha256(history_bytes).hexdigest(),
              "models": MODELS, "budgets": BUDGETS}
    (root / "DEV_PREP_MANIFEST.json").write_text(json.dumps(config), encoding="utf-8")
    return root


def test_negative_fixture_calls_independent_judge_for_every_batch_without_nominations(approved_state):
    state = deepcopy(approved_state)
    history = [source(state), source(state, "second", "b" * 40)]
    before = deepcopy((state, history))
    result = audit.audit_sources(state, history, MODELS, BUDGETS)
    assert (state, history) == before
    assert result["provider_calls"] == 0 and result["mock_transport_calls"] == 2
    assert result["nomination_mode"] == "none" and result["mock_nomination_requests"] == 0
    assert result["mock_independent_classifier_requests"] == 2
    assert result["semantic_result_available"] is False and result["gold_labels_read"] is False
    assert result["state_approval_changed"] is False
    assert result["structurally_reviewable_diff_versions"] == 2
    assert result["scenario_within_nominal_estimate_budget"]
    assert [r["stage"] for r in result["request_envelopes"]] == ["judge"] * 2
    assert all(r["max_output_tokens"] <= 1100 and r["includes_full_schema_and_instructions"]
               for r in result["request_envelopes"])
    assert all(b["all_source_artifacts_visible"] and b["all_s0_elements_considered_by_mock_judge"]
               and not b["nomination_model_review_performed"]
               and b["independent_judge_called_with_empty_nominations"] and b["synthetic_nominations"] == 0
               for b in result["batches"])


def test_optional_nomination_model_scenario_preserves_both_full_envelopes(approved_state):
    history = [source(approved_state), source(approved_state, "second", "b" * 40)]
    result = audit.audit_sources(approved_state, history, MODELS, BUDGETS, nomination_mode="model")
    direct = audit.audit_sources(approved_state, history, MODELS, BUDGETS)
    assert result["provider_calls"] == 0 and result["mock_transport_calls"] == 4
    assert result["mock_nomination_requests"] == result["mock_independent_classifier_requests"] == 2
    assert [r["stage"] for r in result["request_envelopes"]] == ["linker", "judge"] * 2
    assert all(b["nomination_model_review_performed"] and b["all_s0_elements_considered_by_both_mock_stages"]
               for b in result["batches"])
    assert [r["request_sha256"] for r in result["request_envelopes"] if r["stage"] == "judge"] == [
        r["request_sha256"] for r in direct["request_envelopes"]]
    assert result["scenario_estimated_input_tokens"] - direct["scenario_estimated_input_tokens"] == sum(
        r["estimated_input_tokens"] for r in result["request_envelopes"] if r["stage"] == "linker")


def test_oversize_forecast_still_reports_both_envelopes_and_first_unaffordable(approved_state):
    result = audit.audit_sources(approved_state, [source(approved_state)], MODELS,
                                 {**BUDGETS, "max_input_tokens": 1}, nomination_mode="model")
    assert result["mock_transport_calls"] == 2
    assert not result["scenario_within_nominal_estimate_budget"]
    assert result["first_unaffordable_envelope_in_scenario"]["stage"] == "linker"
    assert result["scenario_estimated_input_tokens"] == sum(
        r["estimated_input_tokens"] for r in result["request_envelopes"])


def test_source_screening_preserves_crlf_positions_and_safe_changed_line_coverage(approved_state):
    patch = "@@ -2,2 +2,2 @@\r\n-Old safe statement.\r\n+New safe statement.\r\n Contact user@example.com\r\n"
    result = audit.audit_sources(approved_state, [source(approved_state, content=patch)], MODELS, BUDGETS)
    batch = result["batches"][0]
    changed = batch["changed_line_coverage"][0]
    assert batch["numbered_source_reconstructions_checked"] == 1
    assert changed["changed_source_lines"] == changed["covered_safe_changed_source_lines"] == 2
    assert changed["safe_changed_line_handles_checked"] == 2
    assert "user@example.com" not in json.dumps(result)


def test_protected_changed_lines_remain_explicit_incomplete_citation_coverage(approved_state):
    patch = "@@ -1 +1 @@\n-Contact old@example.com\n+Contact new@example.com\n"
    result = audit.audit_sources(approved_state, [source(approved_state, content=patch)], MODELS, BUDGETS)
    batch = result["batches"][0]
    assert batch["incomplete_outbound_citation_artifact_ids"] == ["edit"]
    assert not batch["all_outbound_citation_coverage_complete"]
    assert batch["changed_line_coverage"][0]["unquotable_changed_source_lines"] == 2


def test_multiline_credential_continuation_is_not_a_safe_line_handle(approved_state):
    patch = ("@@ -1,3 +1,3 @@\r\n secret =\r\n protected-value\r\n"
             "-Old safe statement.\r\n+New safe statement.\r\n")
    batch = select_event_batches(approved_state, [source(approved_state, content=patch)], 2)[0]
    catalog = build_delta_catalog(approved_state, batch)
    checks = audit.validate_catalog(catalog, batch)
    assert "A0001:L0002" not in catalog["lines"] and "A0001:L0003" not in catalog["lines"]
    assert "protected-value" not in json.dumps(catalog["payload"])
    assert checks["changed_line_coverage"][0]["covered_safe_changed_source_lines"] == 2


def test_identical_changed_windows_in_separate_hunks_keep_each_original_position(approved_state):
    patch = ("@@ -1 +1 @@\n-Previous statement.\n+New statement.\n"
             "@@ -7 +7 @@\n-Previous statement.\n+New statement.\n")
    batch = select_event_batches(approved_state, [source(approved_state, content=patch)], 2)[0]
    catalog = build_delta_catalog(approved_state, batch)
    checks = audit.validate_catalog(catalog, batch)
    changed = checks["changed_line_coverage"][0]
    assert changed["changed_source_lines"] == changed["covered_safe_changed_source_lines"] == 4
    assert checks["exact_passage_handles_checked"] >= 2


@pytest.mark.parametrize("tamper", ["source_identity", "passage_span", "line_role", "line_position", "passage_columns"])
def test_catalog_rejects_misbound_original_versions_ranges_and_mechanical_roles(approved_state, tamper):
    batch = select_event_batches(approved_state, [source(approved_state)], 2)[0]
    catalog = build_delta_catalog(approved_state, batch)
    if tamper == "source_identity":
        catalog["payload"]["event_context"]["canonical_artifacts"][0]["content_sha256"] = "0" * 64
    elif tamper == "passage_span":
        next(iter(catalog["passages"].values()))["start"] += 1
    elif tamper == "line_role":
        row = catalog["payload"]["artifacts"][0]
        row["line_roles"]["unchanged"] = row["line_roles"].pop("removed")
    elif tamper == "line_position":
        next(iter(catalog["lines"].values()))["start"] += 1
    else:
        next(iter(catalog["payload"]["artifacts"][0]["passages"].values()))[2] += 1
    with pytest.raises(ValueError):
        audit.validate_catalog(catalog, batch)


def test_same_artifact_id_and_content_still_bind_separate_canonical_versions(approved_state):
    first = source(approved_state)
    second = deepcopy(first)
    second["timestamp"] = "2024-02-02T00:00:00Z"
    second["first_auditable_at"] = second["timestamp"]
    second.pop("version_id")
    result = audit.audit_sources(approved_state, [first, second], MODELS, BUDGETS)
    assert result["structurally_reviewable_artifact_versions"] == 2
    assert result["mock_transport_calls"] == 2
    assert len({b["changed_line_coverage"][0]["artifact_key"] for b in result["batches"]}) == 2


def test_identical_id_hash_and_capture_in_one_batch_remain_version_bound(approved_state):
    first = source(approved_state)
    second = deepcopy(first)
    first["version_id"], second["version_id"] = "first-canonical-version", "second-canonical-version"
    batch = select_event_batches(approved_state, [first, second], 2)[0]
    catalog = build_delta_catalog(approved_state, batch)
    checks = audit.validate_catalog(catalog, batch)
    assert checks["numbered_source_reconstructions_checked"] == 2
    assert catalog["artifacts"]["A0001"]["version_id"] != catalog["artifacts"]["A0002"]["version_id"]
    assert all(p["artifact_handle"] == h.split(":")[0] for h, p in catalog["passages"].items())
    wrong_binding = deepcopy(catalog)
    wrong_binding["artifacts"]["A0002"] = wrong_binding["artifacts"]["A0001"]
    with pytest.raises(ValueError, match="Canonical artifact handle map"):
        audit.validate_catalog(wrong_binding, batch)


def test_catalog_cross_event_batch_is_rejected(approved_state):
    with pytest.raises(ValueError, match="cross_identity"):
        build_delta_catalog(approved_state, [source(approved_state), source(approved_state, "second", "b" * 40)])


def test_audit_rejects_unapproved_source_without_mutating_approval(approved_state):
    state = deepcopy(approved_state)
    state["human_approved"] = False
    with pytest.raises(ValidationError):
        audit.audit_sources(state, [source(state)], MODELS, BUDGETS)
    assert state["human_approved"] is False


def test_cli_direct_sources_preserves_bytes_and_refuses_report_overwrite(tmp_path, approved_state):
    root = prepared(tmp_path, approved_state)
    decision, history = root / "inputs" / audit.DECISION_NAME, root / "inputs" / audit.HISTORY_NAME
    before = (decision.read_bytes(), history.read_bytes())
    output = tmp_path / "preflight.json"
    command = [sys.executable, str(TOOL), "--decision", str(decision), "--history", str(history),
               "--model", MODELS["linker"], "--judge-model", MODELS["judge"], "--output", str(output)]
    result = subprocess.run(command, capture_output=True, text=True)
    assert result.returncode == 0, result.stderr
    report = json.loads(output.read_text())
    assert report["provider_calls"] == 0 and report["mock_transport_calls"] == 1
    assert report["nomination_mode"] == "none" and report["mock_nomination_requests"] == 0
    assert report["models"] == MODELS and report["input_human_approved"] is True
    assert (decision.read_bytes(), history.read_bytes()) == before
    existing = output.read_bytes()
    repeated = subprocess.run(command, capture_output=True, text=True)
    assert repeated.returncode != 0 and output.read_bytes() == existing


def test_prepared_cli_verifies_input_hashes_before_audit(tmp_path, approved_state):
    root = prepared(tmp_path, approved_state)
    (root / "inputs" / audit.HISTORY_NAME).write_text("[]\n", encoding="utf-8")
    result = subprocess.run([sys.executable, str(TOOL), "--evaluation", str(root)], capture_output=True, text=True)
    assert result.returncode != 0 and "input digests do not match" in result.stderr


def test_prepared_cli_accepts_only_approved_inputs(tmp_path, approved_state):
    state = deepcopy(approved_state)
    state["human_approved"] = False
    root = prepared(tmp_path, state)
    result = subprocess.run([sys.executable, str(TOOL), "--evaluation", str(root)], capture_output=True, text=True)
    assert result.returncode != 0 and "human_approved=true" in result.stderr

"""Source-only transport preflight tests; fixtures contain no labels or API calls."""
from copy import deepcopy
import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import sys

import pytest

from evorationale.model import ValidationError, normalize_artifact

TOOL = Path(__file__).resolve().parents[1] / "development_tools" / "audit_v44_no_api.py"
spec = importlib.util.spec_from_file_location("audit_v44_no_api_fixture", TOOL)
audit = importlib.util.module_from_spec(spec)
spec.loader.exec_module(audit)
MODELS = {"linker": "fixture-linker", "judge": "fixture-judge"}
BUDGETS = {"max_rounds": 2, "max_queries": 2, "max_reads": 2,
           "max_input_tokens": 100000}


def source(state, name="change", commit="a" * 40, content=None):
    return normalize_artifact({"artifact_id": name, "repository": state["repository"],
        "source_type": "git_commit_diff_hunk", "source_location": "fixture://source",
        "source_commit_sha": commit, "source_file": "design.md", "title": "Source edit",
        "timestamp": "2024-02-01T00:00:00Z",
        "content": content or "@@ -1 +1 @@\n-Previous statement.\n+New statement.\n"})


def prepare(tmp_path, state):
    root = tmp_path / "evaluation"
    inputs = root / "inputs"
    inputs.mkdir(parents=True)
    state_bytes = (json.dumps(state) + "\n").encode()
    history_bytes = (json.dumps(source(state)) + "\n").encode()
    (inputs / audit.DECISION_NAME).write_bytes(state_bytes)
    (inputs / audit.HISTORY_NAME).write_bytes(history_bytes)
    config = {"kind": "DEVELOPMENT_ONLY_V44_EVENT_COMPLETE_COMPARISON",
              "investigation_profile": "event-complete", "gold_labels_in_agent_inputs": False,
              "runtime_s0_sha256": hashlib.sha256(state_bytes).hexdigest(),
              "history_sha256": hashlib.sha256(history_bytes).hexdigest(),
              "models": MODELS, "budgets": BUDGETS}
    (root / "DEV_PREP_MANIFEST.json").write_text(json.dumps(config), encoding="utf-8")
    return root


def test_source_only_scenario_preserves_inputs_and_is_not_semantic(approved_state):
    state = deepcopy(approved_state)
    history = [source(state), source(state, "second", "b" * 40)]
    before = deepcopy((state, history))
    result = audit.audit_sources(state, history, MODELS, BUDGETS)
    assert (state, history) == before
    assert result["provider_calls"] == 0 and result["mock_transport_calls"] == 4
    assert result["semantic_result_available"] is False and result["gold_labels_read"] is False
    assert result["state_approval_changed"] is False
    assert result["structurally_reviewable_diff_versions"] == 2
    assert result["scenario_within_nominal_estimate_budget"]
    assert all(b["all_source_artifacts_visible"] and b["all_s0_elements_considered"]
               and b["exact_diff_handle_line_ranges_checked"] for b in result["batches"])
    assert all(r["includes_full_schema_and_instructions"] for r in result["request_envelopes"])


def test_unapproved_source_fixture_is_explicit_and_never_approved(approved_state):
    state = deepcopy(approved_state)
    state["human_approved"] = False
    with pytest.raises(ValidationError):
        audit.audit_sources(state, [source(state)], MODELS, BUDGETS)
    result = audit.audit_sources(state, [source(state)], MODELS, BUDGETS, require_approved=False)
    assert state["human_approved"] is False
    assert result["input_human_approved"] is False
    assert result["approval_mode"] == "UNAPPROVED_SOURCE_STRUCTURAL_FIXTURE_ONLY"


def test_budget_forecast_remains_complete_and_explicit_when_too_small(approved_state):
    result = audit.audit_sources(approved_state, [source(approved_state)], MODELS,
                                 {**BUDGETS, "max_input_tokens": 1})
    assert result["mock_transport_calls"] == 2
    assert not result["scenario_within_nominal_estimate_budget"]
    assert result["first_unaffordable_envelope_in_scenario"]["stage"] == "linker"


def test_sensitive_windows_are_counted_without_source_disclosure_to_mock(approved_state):
    patch = "@@ -2,2 +2,2 @@\n-Old safe statement.\n+New safe statement.\n Contact user@example.com\n"
    result = audit.audit_sources(approved_state, [source(approved_state, content=patch)], MODELS, BUDGETS)
    assert result["batches"][0]["omitted_sensitive_passages"] >= 1
    assert result["provider_calls"] == 0


def test_cli_writes_new_report_and_refuses_overwrite(tmp_path, approved_state):
    root = prepare(tmp_path, approved_state)
    output = tmp_path / "preflight.json"
    command = [sys.executable, str(TOOL), "--evaluation", str(root), "--output", str(output)]
    result = subprocess.run(command, capture_output=True, text=True)
    assert result.returncode == 0, result.stderr
    report = json.loads(output.read_text())
    assert report["provider_calls"] == 0
    existing = output.read_bytes()
    repeat = subprocess.run(command, capture_output=True, text=True)
    assert repeat.returncode != 0 and output.read_bytes() == existing


def test_cli_input_tampering_fails_before_preflight(tmp_path, approved_state):
    root = prepare(tmp_path, approved_state)
    (root / "inputs" / audit.HISTORY_NAME).write_text("[]\n", encoding="utf-8")
    result = subprocess.run([sys.executable, str(TOOL), "--evaluation", str(root)],
                            capture_output=True, text=True)
    assert result.returncode != 0 and "input digests do not match" in result.stderr


def test_cli_never_accepts_unapproved_evaluation_input(tmp_path, approved_state):
    state = deepcopy(approved_state)
    state["human_approved"] = False
    root = prepare(tmp_path, state)
    result = subprocess.run([sys.executable, str(TOOL), "--evaluation", str(root)],
                            capture_output=True, text=True)
    assert result.returncode != 0 and "human_approved=true" in result.stderr

"""Canonical pair coverage and positive checker transport, never accuracy tests."""
from copy import deepcopy
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
from types import SimpleNamespace

import pytest

from evorationale.delta_context import build_delta_catalog
from evorationale.model import elements
from evorationale.pair_review_verification import PairReviewSemanticJudge
from test_v46_evidence_trace_verification import case, effect, support_fields
from test_v46_no_api_audit import MODELS, prepared, source

TOOL = Path(__file__).resolve().parents[1] / "development_tools" / "audit_v49_no_api.py"
spec = importlib.util.spec_from_file_location("v49_no_api_audit_fixture", TOOL)
audit = importlib.util.module_from_spec(spec)
spec.loader.exec_module(audit)
BUDGETS = {"max_rounds": 6, "max_queries": 12, "max_reads": 36,
           "max_input_tokens": 400000, "max_output_tokens": 16384, "max_provider_requests": 36}


def prepared49(tmp_path, state):
    root = prepared(tmp_path, state)
    path = root / "DEV_PREP_MANIFEST.json"
    cfg = json.loads(path.read_text())
    from prepare_v49 import SEMANTIC_PHASE_CONFIG
    parent_budgets = {name: value for name, value in BUDGETS.items()
                      if name not in {"max_output_tokens", "max_provider_requests"}}
    parent_budgets["max_input_tokens"] = 100000
    cfg.update(kind=audit.KIND, investigation_profile=audit.PROFILE, nomination_mode="none",
               budgets={**parent_budgets, "max_input_tokens": 400000, "max_provider_requests": 36},
               parent_v46_models=MODELS, parent_v48_models=MODELS, parent_v46_budgets=parent_budgets,
               semantic_phase_config=SEMANTIC_PHASE_CONFIG)
    path.write_text(json.dumps(cfg), encoding="utf-8")
    return root


def test_source_audit_chunks_focus_keeps_full_context_and_all_explicit_pairs(approved_state):
    history = [source(approved_state, name=f"source-{number}") for number in range(4)]
    before = deepcopy((approved_state, history))
    report = audit.audit_sources(approved_state, history, MODELS, BUDGETS)
    assert (approved_state, history) == before
    assert report["provider_calls"] == report["mock_retries"] == report["mock_nomination_requests"] == 0
    assert report["mock_primary_requests"] == 2 and report["mock_checker_requests"] == 0
    assert report["negative_scenario_mock_transport_calls"] == 2
    assert report["mock_transport_calls"] == 3 and report["mock_checker_capacity_forecast_requests"] == 1
    assert report["semantic_result_available"] is report["f1_available"] is report["gold_labels_read"] is False
    assert report["input_human_approved"] is True and report["state_approval_changed"] is False
    assert report["input_budget_increased_from_v48"] and report["input_budget_change"] == 300000
    requests = report["request_envelopes"]
    assert [r["focused_artifacts"] for r in requests] == [["A0001", "A0002", "A0003"], ["A0004"]]
    assert sum(r["expected_pair_rows"] for r in requests) == 4 * len(elements(approved_state))
    assert all(r["all_same_event_source_artifacts_visible"] for r in requests)
    assert report["batches"][0]["explicit_pair_rows"] == 4 * len(elements(approved_state))
    assert report["batches"][0]["numbered_source_reconstructions_checked"] == 4


def test_source_audit_forecasts_independent_checker_capacity_separately(approved_state):
    report = audit.audit_sources(approved_state, [source(approved_state)], MODELS, BUDGETS)
    forecast = report["checker_capacity_forecast"]
    assert forecast["provider_calls"] == forecast["accepted_evidence"] == forecast["mock_retries"] == 0
    assert forecast["mock_checker_calls"] == 1 and forecast["gold_labels_read"] is False
    assert forecast["estimated_checker_input_tokens"] > 0
    assert forecast["combined_primary_and_checker_input_estimate"] == (
        report["phase_estimated_input_tokens"]["primary"] + forecast["estimated_checker_input_tokens"])
    assert forecast["conditional_provider_requests_without_retries"] == 2
    assert forecast["conditional_provider_requests_with_one_retry_per_phase"] == 4
    assert forecast["combined_input_estimate_with_one_retry_per_phase"] >= 2 * report["scenario_estimated_input_tokens"]
    assert report["checker_capacity_forecast_envelopes"][0]["fixture_verdicts"] == "ALL_REJECT"
    assert forecast["primary_output_capacity_guaranteed"] is False
    assert report["conditional_phase_estimated_input_tokens"]["checker"] == forecast["estimated_checker_input_tokens"]


def test_forecast_exposes_input_and_provider_capacity_without_hiding_envelopes(approved_state):
    history = [source(approved_state, name=f"source-{number}") for number in range(4)]
    report = audit.audit_sources(approved_state, history, MODELS,
        {**BUDGETS, "max_input_tokens": 1, "max_provider_requests": 1})
    assert report["mock_primary_requests"] == 2
    assert report["scenario_within_nominal_estimate_budget"] is False
    assert report["scenario_within_provider_request_budget"] is False
    assert report["first_unaffordable_envelope_in_scenario"]["stage"] == "primary"
    assert report["first_provider_request_over_limit_in_scenario"]["provider_request_number"] == 2
    assert report["checker_capacity_forecast"]["combined_within_input_budget"] is False
    assert report["checker_capacity_forecast"]["retry_request_capacity_within_provider_budget"] is False


class PositiveThenCheck:
    """One generic exact-source witness; checker confirmation is still a fixture."""

    def __init__(self, state, catalog, verdict):
        self.state, self.catalog, self.verdict, self.requests = state, catalog, verdict, []

    def create(self, **request):
        self.requests.append(deepcopy(request))
        payload = json.loads(request["input"])
        if request["text"]["format"]["name"] == audit.PRIMARY_NAME:
            ids = [target["id"] for target in payload["fixed_s0"]["elements"]]
            item = effect(self.state, self.catalog, **support_fields())
            result = {"considered_element_ids": ids,
                "reviews": [{"artifact_handle": "A0001", "status": "relation_found", "reason": "Fixture witness.",
                    "support_reason": "Added exact contract statement.", "change_reason": "Existing design corroborated.",
                    "links": [item], "pair_outcomes": [{"element_id": target,
                        "outcome": "relation_found" if target == "TRACE_TARGET" else "no_relation",
                        "relations": ["supports"] if target == "TRACE_TARGET" else [],
                        "reason": "Generic synthetic persistence contract fixture."} for target in ids]}]}
        else:
            assert payload["original_catalog"] == self.catalog["payload"]
            candidates = payload["candidate_hypotheses"]
            assert len(candidates) == 1 and candidates[0]["element_id"] == "TRACE_TARGET"
            assert not {"reason", "confidence", "local_contribution", "before_claim", "after_claim",
                        "qualification", "current_claim_entailed"}.intersection(candidates[0])
            result = {"decisions": [{"candidate_id": candidates[0]["candidate_id"], "verdict": self.verdict,
                "reason": "Independent local fixture check.", "predicate_reason": "The exact persistence clause is stated.",
                "contribution_reason": "The contract statement is added locally.",
                "authority_reason": "Synthetic adopted design statement, not deployed validation."}]}
        return SimpleNamespace(status="completed", output_text=json.dumps(result))


@pytest.mark.parametrize("verdict", ["confirm", "reject"])
def test_generic_positive_source_exercises_real_primary_and_checker_path(approved_state, verdict):
    state, batch = case(approved_state,
        "@@ -1,0 +1 @@\n+Approved orders are persisted through CentralQueue by the order writer.\n")
    catalog = build_delta_catalog(state, batch)
    fake = PositiveThenCheck(state, catalog, verdict)
    judge = PairReviewSemanticJudge("opaque-local-fixture", client=SimpleNamespace(responses=fake))
    accepted, rejected = judge.review_event(state, batch, [])
    assert [r["text"]["format"]["name"] for r in fake.requests] == [audit.PRIMARY_NAME, audit.CHECKER_NAME]
    assert all(r["max_output_tokens"] == 12000 for r in fake.requests)
    if verdict == "confirm":
        assert len(accepted) == 1 and not rejected
        assert accepted[0]["relation"] == "supports"
        assert accepted[0]["semantic_assessment"]["candidate_check_epistemic_status"] == "MODEL_ASSESSED"
    else:
        assert not accepted and any("candidate_review_rejected" in reason
            for item in rejected for reason in item["reasons"])


def test_prepared_cli_checks_identity_digests_and_refuses_report_overwrite(tmp_path, approved_state):
    root = prepared49(tmp_path, approved_state)
    output = tmp_path / "pair-audit.json"
    command = [sys.executable, str(TOOL), "--evaluation", str(root), "--output", str(output)]
    result = subprocess.run(command, capture_output=True, text=True)
    assert result.returncode == 0, result.stderr
    before = output.read_bytes()
    report = json.loads(before)
    assert report["provider_calls"] == 0 and report["investigation_profile"] == audit.PROFILE
    repeated = subprocess.run(command, capture_output=True, text=True)
    assert repeated.returncode != 0 and output.read_bytes() == before
    (root / "inputs" / audit.HISTORY_NAME).write_text("[]\n", encoding="utf-8")
    invalid = subprocess.run([sys.executable, str(TOOL), "--evaluation", str(root)], capture_output=True, text=True)
    assert invalid.returncode != 0 and "input digests do not match" in invalid.stderr


def test_audit_rejects_nomination_and_missing_provider_request_budget(approved_state):
    history = [source(approved_state)]
    with pytest.raises(ValueError, match="nomination mode none"):
        audit.audit_sources(approved_state, history, MODELS, BUDGETS, nomination_mode="model")
    missing = dict(BUDGETS)
    del missing["max_provider_requests"]
    with pytest.raises(ValueError, match="provider-request budgets"):
        audit.audit_sources(approved_state, history, MODELS, missing)

"""Generic source-scope regressions; fake responses are not accuracy measurements."""
from copy import deepcopy
from types import SimpleNamespace

import pytest

from evorationale.delta_context import build_delta_catalog
from evorationale.evidence_trace_verification import EvidenceTraceSemanticJudge
from evorationale.grounded_trace_verification import GroundedTraceSemanticJudge
from test_v46_evidence_trace_verification import case, effect, response, Replies, support_fields


def evaluate47(state, batch, changes=None, transform=None, charge=None):
    catalog = build_delta_catalog(state, batch)
    item = effect(state, catalog, **(changes or {}))
    item.setdefault("target_contribution", "direct_target_change")
    item.setdefault("predicate_line_handles", [])
    reply = response(state, catalog, {"A0001": [item]})
    if transform:
        transform(reply, catalog)
    fake = Replies(reply)
    judge = GroundedTraceSemanticJudge("fixture", client=SimpleNamespace(responses=fake))
    accepted, feedback = judge.review_event(state, batch, [], charge=charge)
    return accepted, feedback, judge, fake


def predicate(reply, catalog):
    item = reply["reviews"][0]["links"][0]
    item["predicate_line_handles"] = [h for h in item["after_line_handles"]
                                     if catalog["lines"][h]["role"] in {"added", "statement"}]


def direct_support(approved_state, changes=None, transform=predicate, source_type="git_commit_diff_hunk"):
    patch = "@@ -1,0 +1 @@\n+Approved orders are persisted through CentralQueue by the order writer.\n"
    if source_type == "document":
        patch = "Approved orders are persisted through CentralQueue by the order writer."
    state, batch = case(approved_state, patch, source_type=source_type)
    values = support_fields(**{"target_contribution": "direct_predicate_evidence", **(changes or {})})
    return evaluate47(state, batch, values, transform)


def test_direct_current_predicate_support_and_metadata(approved_state):
    accepted, feedback, judge, fake = direct_support(approved_state)
    assert len(accepted) == 1 and not feedback and len(fake.calls) == 1
    assert accepted[0]["semantic_assessment"]["semantic_policy"] == "predicate-grounded"
    assert accepted[0]["semantic_assessment"]["deployed_behavior_verified"] is False
    assert judge.last_reviews[0]["assessment_origin"].endswith("GROUNDED_TRACE_REVIEW")
    schema = fake.calls[0]["text"]["format"]["schema"]
    fields = schema["properties"]["reviews"]["items"]["properties"]["links"]["items"]
    assert {"target_contribution", "predicate_line_handles"} <= set(fields["required"])


@pytest.mark.parametrize("contribution", ["mere_dependency_use", "implementation_of_retained_rule", "unclear",
                                         "direct_target_tradeoff", "dependent_target_change"])
def test_support_cannot_be_established_by_indirect_use(approved_state, contribution):
    accepted, feedback, _, _ = direct_support(approved_state, {"target_contribution": contribution})
    assert not accepted
    assert "MODEL_ASSESSED:grounded_trace_has_no_direct_target_contribution" in feedback[0]["reasons"]


@pytest.mark.parametrize("change", ["empty", "unknown", "removed", "foreign", "duplicate", "not_after", "not_string"])
def test_predicate_proof_is_current_local_and_source_owned(approved_state, change):
    state, batch = case(approved_state, sibling="@@ -20,0 +20 @@\n+An unrelated controller stores metadata.\n")
    def altered(reply, catalog):
        item = reply["reviews"][0]["links"][0]
        current = next(h for h, line in catalog["lines"].items()
                       if line["artifact_handle"] == "A0001" and line["role"] == "added")
        removed = next(h for h, line in catalog["lines"].items()
                       if line["artifact_handle"] == "A0001" and line["role"] == "removed")
        foreign = next(h for h, line in catalog["lines"].items() if line["artifact_handle"] == "A0002")
        item["predicate_line_handles"] = {"empty": [], "unknown": ["A9999:L9999"], "removed": [removed],
                                          "foreign": [foreign], "duplicate": [current, current],
                                          "not_after": [current], "not_string": [None]}[change]
        if change == "not_after":
            item["after_line_handles"] = []
    values = support_fields(target_contribution="direct_predicate_evidence")
    accepted, feedback, _, _ = evaluate47(state, batch, values, altered)
    assert not accepted and feedback


def test_rebound_witness_preserves_predicate_while_changing_grounding(approved_state):
    patch = ("@@ -1 +1 @@\n-Commit succeeds when requested == Queue.recorded == applied.\n"
             "+Commit succeeds when requested == committed snapshot == applied.\n")
    state, batch = case(approved_state, patch,
                        target="Distinguish requested order quantities from committed quantities and applied quantities.")
    values = support_fields(change_kind="operational_witness", effect_basis="operational_witness",
                            target_contribution="rebound_predicate_evidence", before_claim="Old recorded operand.",
                            after_claim="New committed snapshot operand.")
    accepted, feedback, _, _ = evaluate47(state, batch, values, predicate)
    assert len(accepted) == 1 and not feedback


@pytest.mark.parametrize("change", [{"before_line_handles": []}, {"change_kind": "documented_support",
                                                                 "effect_basis": "current_design_statement"}])
def test_rebound_witness_requires_both_local_sides(approved_state, change):
    accepted, feedback, _, _ = direct_support(approved_state,
        {"target_contribution": "rebound_predicate_evidence", **change})
    assert not accepted and any("rebound_witness_has_no_old_predicate_proof" in r
                               for f in feedback for r in f["reasons"])


CONTEXT_REPLACEMENT = ("@@ -1,2 +1,4 @@\n-Orders persist through CentralQueue.\n Records record timestamps.\n+\n"
                       "+LocalLedger replaces CentralQueue for ordinary order persistence.\n"
                       "+CentralQueue remains an optional legacy route.\n")


def context_replacement(approved_state, changes=None, altered=None, cls=GroundedTraceSemanticJudge):
    state, batch = case(approved_state, CONTEXT_REPLACEMENT)
    catalog = build_delta_catalog(state, batch)
    retained = [h for h, line in catalog["lines"].items() if line["role"] == "unchanged"]
    added = [h for h, line in catalog["lines"].items() if line["role"] == "added" and line["text"].strip("+ ")]
    values = {"change_kind": "mechanism_replacement", "effect_basis": "direct_delta",
              "after_line_handles": retained, "context_line_handles": added,
              "target_contribution": "direct_target_change", **(changes or {})}
    if cls is GroundedTraceSemanticJudge:
        return evaluate47(state, batch, values, altered)
    item = effect(state, catalog, **values)
    del item["target_contribution"]
    fake = Replies(response(state, catalog, {"A0001": [item]}))
    judge = cls("fixture", client=SimpleNamespace(responses=fake))
    accepted, feedback = judge.review_event(state, batch, [])
    return accepted, feedback, judge, fake


def test_same_artifact_added_contract_can_supply_replacement_new_side(approved_state):
    accepted, feedback, _, _ = context_replacement(approved_state)
    assert len(accepted) == 1 and not feedback
    assert accepted[0]["semantic_assessment"]["replacement_current_proof_origin"] == "SAME_ARTIFACT_ADDED_CONTEXT"
    assert accepted[0]["relation"] == "supersedes"
    legacy, rejected, _, _ = context_replacement(approved_state, cls=EvidenceTraceSemanticJudge)
    assert not legacy and "MODEL_ASSESSED:replacement_lacks_both_source_sides" in rejected[0]["reasons"]


@pytest.mark.parametrize("changes", [
    {"context_line_handles": []}, {"context_establishes_replacement": False}, {"replacement_is_explicit": False},
    {"source_role": "proposal_or_alternative"}, {"evidence_basis": "unknown"}, {"scope_match": False},
    {"material_target_delta": False}, {"before_line_handles": []},
    {"target_contribution": "mere_dependency_use"},
])
def test_current_context_cannot_rescue_unestablished_replacement(approved_state, changes):
    accepted, feedback, _, _ = context_replacement(approved_state, changes)
    assert not accepted and feedback


def test_other_artifact_added_context_cannot_supply_direct_replacement_new_side(approved_state):
    state, batch = case(approved_state, "@@ -1,2 +1 @@\n-Orders persist through CentralQueue.\n Records record timestamps.\n",
                        sibling="@@ -20,0 +20 @@\n+LocalLedger replaces CentralQueue for ordinary order persistence.\n")
    def shifted(reply, catalog):
        item = reply["reviews"][0]["links"][0]
        item["context_line_handles"] = [h for h, line in catalog["lines"].items()
                                        if line["artifact_handle"] == "A0002" and line["role"] == "added"]
    values = {"change_kind": "mechanism_replacement", "effect_basis": "direct_delta",
              "target_contribution": "direct_target_change"}
    accepted, feedback, _, _ = evaluate47(state, batch, values, shifted)
    assert not accepted and "MODEL_ASSESSED:replacement_lacks_both_source_sides" in feedback[0]["reasons"]


@pytest.mark.parametrize("field,value", [("target_contribution", []), ("target_contribution", "unexpected"),
                                         ("predicate_line_handles", None)])
def test_invalid_contribution_contract_fails_closed(approved_state, field, value):
    def malformed(reply, catalog):
        predicate(reply, catalog)
        reply["reviews"][0]["links"][0][field] = value
    accepted, feedback, _, _ = direct_support(approved_state, transform=malformed)
    assert not accepted and feedback[0]["failure_class"] == "technical_verification_failure"


def test_grounded_response_allowance_is_bounded_and_exceeds_small_review_ceiling(approved_state):
    _, _, _, fake = direct_support(approved_state)
    assert fake.calls[0]["max_output_tokens"] >= 6144
    judge = GroundedTraceSemanticJudge("fixture", client=SimpleNamespace(responses=Replies({})))
    assert judge._initial_output_tokens(100) == 16384
    assert EvidenceTraceSemanticJudge._initial_output_tokens(judge, 5) == 4800


def test_grounded_request_respects_explicit_lower_budget_ceiling(approved_state):
    state, batch = case(approved_state)
    charged = []
    class Charge:
        budget = SimpleNamespace(max_output_tokens=3000)
        def __call__(self, request): charged.append(deepcopy(request))
    evaluate47(state, batch, charge=Charge())
    assert len(charged) == 1 and charged[0]["max_output_tokens"] == 3000


def test_generic_instructions_distinguish_boundaries_from_costs_and_consumers(approved_state):
    _, _, _, fake = direct_support(approved_state)
    request = fake.calls[0]
    assert "implementation_of_retained_rule" in request["instructions"]
    assert "fixed" in request["instructions"] and "predicate" in request["instructions"]
    assert "no-goal-label" not in str(request)

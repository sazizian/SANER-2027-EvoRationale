"""Synthetic independent-classification and exact-proof contract regressions.

Fake providers test mechanical boundaries and honest provenance, not accuracy
of architectural language judgments. No pilot identifier or gold label occurs.
"""
from copy import deepcopy
import json
from types import SimpleNamespace

import pytest

from evorationale.budget import BudgetExhausted
from evorationale.delta_context import build_delta_catalog
from evorationale.delta_verification import DeltaSemanticJudge
from evorationale.model import artifact_key, element_by_id, normalize_artifact


TARGET = "Persist approved orders through CentralQueue."
PATCH = ("@@ -1 +1 @@\n-CentralQueue persists approved orders.\n"
         "+LocalLedger persists approved orders; CentralQueue remains in optional preview.\n")


def case(approved_state, content=PATCH, *, source_type="git_commit_diff_hunk", field="implementation_scope", target=TARGET):
    state = deepcopy(approved_state)
    state[field].append({"id": "DELTA_TARGET", "source": "fixture://target", "text": target})
    artifact = normalize_artifact({"artifact_id": "synthetic-order-change", "repository": state["repository"],
                                   "title": "Order persistence update", "source_type": source_type,
                                   "source_location": "fixture://orders", "timestamp": "2024-02-01T00:00:00Z",
                                   "content": content})
    return state, [artifact]


def effect(state, catalog, handle="A0001", **changes):
    owned = [(name, value) for name, value in catalog["lines"].items() if value["artifact_handle"] == handle]
    before = [name for name, value in owned if value["role"] in {"removed", "unchanged"}]
    after = [name for name, value in owned if value["role"] in {"added", "unchanged", "statement"}]
    passage = next(name for name, value in catalog["passages"].items() if value["artifact_handle"] == handle)
    return {"passage_handle": passage, "element_id": "DELTA_TARGET",
            "s0_claim_quote": element_by_id(state)["DELTA_TARGET"]["text"],
            "before_line_handles": before, "after_line_handles": after, "context_line_handles": [],
            "before_claim": "The ordinary order authority is CentralQueue.",
            "after_claim": "The ordinary authority is LocalLedger; optional preview CentralQueue persists.",
            "change_kind": "mechanism_replacement", "source_role": "adopted_design",
            "claim_scope": "material_subclaim", "whole_element_supported": False,
            "scope_match": True, "material_target_delta": True, "replacement_is_explicit": True,
            "surviving_clause_masks_replacement": False,
            "qualification": "Optional preview path remains; only the ordinary mechanism changes.",
            "reason": "The exact source replaces the ordinary order mechanism with qualified legacy retention.",
            "confidence": .8, "evidence_basis": "adopted_design_statement", **changes}


def response(state, catalog, effects=None):
    effects = effects or {}
    return {"considered_element_ids": list(element_by_id(state)),
            "reviews": [{"artifact_handle": handle,
                         "status": "relation_found" if any(x["change_kind"] not in {"none", "invariant", "implementation_only", "uncertain"}
                                                            for x in effects.get(handle, [])) else "no_material_relation",
                         "reason": "Reviewed all fixed targets independently.", "links": effects.get(handle, [])}
                        for handle in catalog["artifacts"]]}


class Replies:
    def __init__(self, reply, incomplete=0):
        self.reply, self.incomplete, self.calls = reply, incomplete, []

    def create(self, **kwargs):
        self.calls.append(deepcopy(kwargs))
        if len(self.calls) <= self.incomplete:
            return SimpleNamespace(status="incomplete", output_text="")
        return SimpleNamespace(status="completed", output_text=json.dumps(self.reply))


def judge(fake):
    return DeltaSemanticJudge("fixture", client=SimpleNamespace(responses=fake))


def run_case(state, batch, changes=None, nominees=None, transform=None):
    catalog = build_delta_catalog(state, batch)
    reply = response(state, catalog, {"A0001": [effect(state, catalog, **(changes or {}))]})
    if transform:
        reply = transform(reply, catalog)
    fake = Replies(reply)
    accepted, feedback = judge(fake).review_event(state, batch, nominees or [])
    return accepted, feedback, fake, catalog


def test_empty_nominees_do_not_gate_independent_recovery_or_anchor_relation(approved_state):
    state, batch = case(approved_state)
    catalog = build_delta_catalog(state, batch)
    fake = Replies(response(state, catalog, {"A0001": [effect(state, catalog)]}))
    reviewer = judge(fake)
    accepted, feedback = reviewer.review_event(state, batch, [])
    assert len(accepted) == 1 and not feedback
    assert accepted[0]["relation"] == "supersedes"
    assert accepted[0]["semantic_assessment"]["proposal_origin"] == "independent_recovery"
    assert accepted[0]["semantic_assessment"]["epistemic_status"] == "MODEL_ASSESSED"
    assert "optional preview" in accepted[0]["semantic_assessment"]["qualification"].lower()
    sent = json.loads(fake.calls[0]["input"])
    assert "nominees" not in sent and "proposals" not in sent
    assert len(reviewer.last_reviews) == 1
    assert reviewer.last_reviews[0]["considered_element_ids"] == list(element_by_id(state))


def test_nomination_affects_audit_origin_only(approved_state):
    state, batch = case(approved_state)
    nominees = [{"artifact_key": artifact_key(batch[0]), "artifact_id": batch[0]["artifact_id"],
                 "decision_element_id": "DELTA_TARGET"}]
    accepted, feedback, _, _ = run_case(state, batch, nominees=nominees)
    assert len(accepted) == 1 and not feedback
    assert accepted[0]["semantic_assessment"]["proposal_origin"] == "nomination"
    assert accepted[0]["semantic_assessment"]["exact_before_source_lines"] == ["-CentralQueue persists approved orders."]


@pytest.mark.parametrize("changes,code", [
    ({"s0_claim_quote": "Permit appending policies for new orders."}, "invalid_exact_s0_claim_anchor"),
    ({"s0_claim_quote": "CentralQueue"}, "invalid_exact_s0_claim_anchor"),
    ({"whole_element_supported": "false"}, "invalid_delta_effect_fields"),
    ({"confidence": True}, "invalid_delta_effect_fields"),
    ({"confidence": 2.0}, "invalid_delta_effect_fields"),
    ({"before_line_handles": ["invented"]}, "invalid_delta_before_handles"),
    ({"after_line_handles": ["invented"]}, "invalid_delta_after_handles"),
    ({"context_line_handles": ["invented"]}, "invalid_delta_context_handles"),
    ({"passage_handle": "invented"}, "invalid_delta_effect_fields"),
    ({"before_claim": ""}, "missing_delta_before_claim"),
])
def test_invalid_claim_or_source_contract_is_technical_not_negative(approved_state, changes, code):
    state, batch = case(approved_state)
    accepted, feedback, fake, _ = run_case(state, batch, changes)
    assert not accepted and len(fake.calls) == 1
    assert feedback[0]["reasons"] == ["semantic_judge_error:" + code]
    assert feedback[0]["failure_class"] == "technical_verification_failure"
    assert "semantic_assessment" not in feedback[0]


@pytest.mark.parametrize("direction", ["before", "after"])
def test_side_roles_are_validated_exactly(approved_state, direction):
    state, batch = case(approved_state)
    catalog = build_delta_catalog(state, batch)
    wrong = [name for name, value in catalog["lines"].items()
             if value["role"] == ("added" if direction == "before" else "removed")]
    accepted, feedback, _, _ = run_case(state, batch, {direction + "_line_handles": wrong})
    assert not accepted
    assert feedback[0]["reasons"] == ["semantic_judge_error:wrong_source_or_side_in_" + direction + "_proof"]


@pytest.mark.parametrize("changes,reason", [
    ({"material_target_delta": False}, "no_material_target_delta"),
    ({"scope_match": False}, "target_scope_mismatch"),
    ({"replacement_is_explicit": False}, "replacement_not_established"),
    ({"source_role": "implementation_detail"}, "source_role_does_not_establish_rationale"),
    ({"before_line_handles": []}, "replacement_lacks_both_source_sides"),
    ({"after_line_handles": []}, "quote_has_no_current_target_local_proof"),
    ({"before_claim": "Unchanged target.", "after_claim": "Unchanged target."}, "identical_before_after_target_claims"),
])
def test_affirmative_effect_cannot_bypass_target_delta_guards(approved_state, changes, reason):
    state, batch = case(approved_state)
    accepted, feedback, _, _ = run_case(state, batch, changes)
    assert not accepted and any(reason in x for x in feedback[0]["reasons"])
    assert feedback[0]["semantic_assessment"]["epistemic_status"] == "MODEL_ASSESSED"
    assert "failure_class" not in feedback[0]


def test_blank_only_change_is_not_material_proof(approved_state):
    patch = "@@ -1,2 +1,2 @@\n-\n+ \n CentralQueue persists approved orders.\n"
    state, batch = case(approved_state, patch)
    accepted, feedback, _, _ = run_case(state, batch, {"change_kind": "new_corroboration",
                                                    "replacement_is_explicit": False})
    assert not accepted
    assert "MODEL_ASSESSED:quote_has_no_target_local_changed_proof" in feedback[0]["reasons"]


@pytest.mark.parametrize("change_kind,relation", [
    ("new_corroboration", "supports"), ("new_operationalisation", "supports"),
    ("direct_rationale", "supports"), ("mechanism_replacement", "supersedes"),
    ("claim_retirement", "supersedes"), ("incompatibility", "contradicts"),
    ("reduced_justification", "weakens"),
])
def test_relation_mapping_is_code_owned(approved_state, change_kind, relation):
    state, batch = case(approved_state)
    accepted, feedback, _, _ = run_case(state, batch, {"change_kind": change_kind})
    assert len(accepted) == 1 and not feedback and accepted[0]["relation"] == relation


def test_partial_support_remains_partial_and_surviving_clause_cannot_mask_replacement(approved_state):
    state, batch = case(approved_state)
    accepted, feedback, _, _ = run_case(state, batch, {"change_kind": "direct_rationale"})
    assert len(accepted) == 1 and not feedback
    assert accepted[0]["claim_scope"] == "material_subclaim"
    accepted, feedback, _, _ = run_case(state, batch, {"change_kind": "direct_rationale",
                                                    "surviving_clause_masks_replacement": True})
    assert not accepted and "MODEL_ASSESSED:surviving_clause_masks_replacement" in feedback[0]["reasons"]


@pytest.mark.parametrize("change_kind,basis,role,accepted_expected", [
    ("direct_rationale", "direct_rationale_argument", "proposal_or_alternative", True),
    ("new_operationalisation", "adopted_design_statement", "proposal_or_alternative", False),
    ("direct_rationale", "hypothetical_benefit", "proposal_or_alternative", False),
    ("reduced_justification", "direct_rationale_argument", "proposal_or_alternative", True),
    ("mechanism_replacement", "direct_rationale_argument", "proposal_or_alternative", False),
])
def test_direct_policy_argument_differs_from_hypothetical_fulfillment(approved_state, change_kind, basis, role, accepted_expected):
    state, batch = case(approved_state, field="goals", target="Leave failed-order lifecycle decisions to the initiating actor.")
    accepted, feedback, _, _ = run_case(state, batch, {"change_kind": change_kind, "evidence_basis": basis,
                                                    "source_role": role})
    assert bool(accepted) is accepted_expected
    if accepted_expected:
        assert not feedback and accepted[0]["evidence_scope"] == "discussion"
        assert accepted[0]["semantic_assessment"]["whole_element_supported"] is False


def test_ordinary_new_rationale_uses_statement_without_fabricated_before(approved_state):
    state, batch = case(approved_state, "Experiments newly confirm the documented forecasting benefit.", source_type="issue_comment")
    accepted, feedback, _, _ = run_case(state, batch, {"change_kind": "new_corroboration",
                                                    "before_claim": "", "replacement_is_explicit": False,
                                                    "evidence_basis": "observed_validation"})
    assert len(accepted) == 1 and not feedback
    assert accepted[0]["semantic_assessment"]["exact_before_source_lines"] == []


@pytest.mark.parametrize("transform,code", [
    (lambda r, _: {**r, "considered_element_ids": []}, "incomplete_delta_element_review"),
    (lambda r, _: {**r, "reviews": []}, "incomplete_delta_artifact_review"),
    (lambda r, _: {**r, "unexpected": True}, "invalid_delta_review_object"),
    (lambda r, _: {**r, "reviews": [{**r["reviews"][0], "status": "no_material_relation"}]}, "inconsistent_delta_review_status"),
    (lambda r, _: {**r, "reviews": [{**r["reviews"][0], "links": r["reviews"][0]["links"] * 2}]}, "duplicate_delta_relation"),
])
def test_incomplete_or_inconsistent_response_fails_atomically(approved_state, transform, code):
    state, batch = case(approved_state)
    accepted, feedback, _, _ = run_case(state, batch, transform=transform)
    assert not accepted and feedback[0]["reasons"] == ["semantic_judge_error:" + code]


def test_empty_no_relation_review_still_consumes_and_reports_independent_coverage(approved_state):
    state, batch = case(approved_state)
    catalog = build_delta_catalog(state, batch)
    fake = Replies(response(state, catalog))
    reviewer = judge(fake)
    assert reviewer.review_event(state, batch, []) == ([], [])
    assert len(fake.calls) == 1 and len(reviewer.last_reviews) == 1
    assert reviewer.last_reviews[0]["status"] == "no_material_relation"


def test_budget_reservation_precedes_every_call_and_retry_uses_configured_ceiling(approved_state):
    state, batch = case(approved_state)
    catalog = build_delta_catalog(state, batch)
    fake = Replies(response(state, catalog), incomplete=1)

    class Charge:
        budget = SimpleNamespace(max_output_tokens=700)

        def __init__(self):
            self.charges, self.observed = [], []

        def __call__(self, request):
            self.charges.append(deepcopy(request))

        def record_response(self, response):
            self.observed.append(response)

    charge = Charge()
    assert judge(fake).review_event(state, batch, [], charge=charge) == ([], [])
    assert fake.calls == charge.charges and len(charge.observed) == 2
    assert [request["max_output_tokens"] for request in fake.calls] == [700, 700]
    assert all(request["instructions"] and request["text"]["format"]["schema"] for request in charge.charges)


def test_input_budget_exhaustion_is_never_a_semantic_no_effect(approved_state):
    state, batch = case(approved_state)
    catalog = build_delta_catalog(state, batch)
    fake = Replies(response(state, catalog))

    def charge(_):
        raise BudgetExhausted("fixture_token_limit")

    with pytest.raises(BudgetExhausted):
        judge(fake).review_event(state, batch, [], charge=charge)
    assert not fake.calls


def test_corrupt_or_unauthorized_context_never_reaches_provider(approved_state):
    state, batch = case(approved_state)
    fake = Replies({})
    tampered = deepcopy(batch)
    tampered[0]["content"] = "Tampered source."
    accepted, feedback = judge(fake).review_event(state, tampered, [])
    assert not accepted and not fake.calls and feedback[0]["failure_class"] == "technical_verification_failure"
    foreign = normalize_artifact({**batch[0], "repository": "foreign/repository"})
    accepted, feedback = judge(fake).review_event(state, [foreign], [])
    assert not accepted and not fake.calls


def test_cross_version_passage_and_line_references_cannot_be_swapped(approved_state):
    state, batch = case(approved_state)
    first = normalize_artifact({**batch[0], "version_id": "capture-one"})
    second = normalize_artifact({**batch[0], "version_id": "capture-two"})
    batch = [first, second]
    for source in batch:
        source.update(source_commit_sha="a" * 40, source_file="docs/orders.md", _event_batch_complete=True,
                      _event_group_artifact_keys=[artifact_key(a) for a in batch])
    catalog = build_delta_catalog(state, batch)
    wrong_passage = next(name for name, value in catalog["passages"].items() if value["artifact_handle"] == "A0002")
    fake = Replies(response(state, catalog, {"A0001": [effect(state, catalog, passage_handle=wrong_passage)]}))
    accepted, feedback = judge(fake).review_event(state, batch, [])
    assert not accepted and len(feedback) == 2
    assert all(x["reasons"] == ["semantic_judge_error:cross_artifact_delta_passage"] for x in feedback)
    fake = Replies(response(state, catalog, {"A0001": [effect(state, catalog)],
                                           "A0002": [effect(state, catalog, "A0002")]}))
    accepted, feedback = judge(fake).review_event(state, batch, [])
    assert len(accepted) == 2 and not feedback
    assert [x["semantic_assessment"]["canonical_artifact_key"] for x in accepted] == [artifact_key(a) for a in batch]


def test_sensitive_context_is_screened_without_creating_source_quotes(approved_state):
    content = "Forecast validation passed.\nPassword:\nfixture-private-value"
    state, batch = case(approved_state, content, source_type="issue_comment")
    catalog = build_delta_catalog(state, batch)
    fake = Replies(response(state, catalog))
    assert judge(fake).review_event(state, batch, []) == ([], [])
    assert "fixture-private-value" not in fake.calls[0]["input"]
    assert all("fixture-private-value" not in p["quote"] for p in catalog["passages"].values())


@pytest.mark.parametrize("quote_kind", ["prefix_only", "unchanged_outside_delta"])
def test_proof_requires_full_meaningful_changed_line_in_own_quote(approved_state, monkeypatch, quote_kind):
    from evorationale import delta_verification

    patch = "@@ -1,2 +1,2 @@\n-CentralQueue persists approved orders.\n+LocalLedger persists approved orders.\n Stable publication context.\n"
    state, batch = case(approved_state, patch)
    catalog = build_delta_catalog(state, batch)
    passage_handle = next(iter(catalog["passages"]))
    quote = "+" if quote_kind == "prefix_only" else " Stable publication context."
    start = batch[0]["content"].index(quote, batch[0]["content"].index("\n") + 1)
    catalog["passages"][passage_handle] = {"artifact_handle": "A0001", "quote": quote,
                                           "start": start, "end": start + len(quote)}
    fake = Replies(response(state, catalog, {"A0001": [effect(state, catalog, passage_handle=passage_handle)]}))
    monkeypatch.setattr(delta_verification, "build_delta_catalog", lambda *_: catalog)
    accepted, feedback = judge(fake).review_event(state, batch, [])
    assert not accepted
    assert "MODEL_ASSESSED:quote_has_no_target_local_changed_proof" in feedback[0]["reasons"]


def test_pure_retirement_needs_explicit_same_event_current_source(approved_state):
    state, first_batch = case(approved_state, "@@ -1 +0,0 @@\n-CentralQueue persists approved orders.\n")
    first = first_batch[0]
    sibling = normalize_artifact({**first, "artifact_id": "synthetic-retirement-justification",
                                  "version_id": "retirement-statement", "content_sha256": "",
                                  "content": "@@ -20,0 +20 @@\n+CentralQueue is retired; approved orders now persist through LocalLedger.\n"})
    batch = [first, sibling]
    for source in batch:
        source.update(source_commit_sha="a" * 40, source_file="docs/orders.md", _event_batch_complete=True,
                      _event_group_artifact_keys=[artifact_key(a) for a in batch])
    catalog = build_delta_catalog(state, batch)
    current = [name for name, line in catalog["lines"].items()
               if line["artifact_handle"] == "A0002" and line["role"] == "added"]
    classified = effect(state, catalog, change_kind="claim_retirement", context_line_handles=current,
                        after_claim="Same-event source explicitly retires CentralQueue in favor of LocalLedger.",
                        qualification="The local deletion has an explicit same-event retirement statement.")
    fake = Replies(response(state, catalog, {"A0001": [classified]}))
    accepted, feedback = judge(fake).review_event(state, batch, [])
    assert len(accepted) == 1 and not feedback
    assert accepted[0]["relation"] == "supersedes"
    assert accepted[0]["semantic_assessment"]["exact_after_source_lines"] == []
    assert accepted[0]["semantic_assessment"]["exact_context_source_lines"] == [
        "+CentralQueue is retired; approved orders now persist through LocalLedger."]
    fake = Replies(response(state, catalog, {"A0001": [{**classified, "context_line_handles": []}]}))
    accepted, feedback = judge(fake).review_event(state, batch, [])
    assert not accepted and "MODEL_ASSESSED:replacement_lacks_both_source_sides" in feedback[0]["reasons"]


def test_invalid_second_review_prevents_partial_batch_acceptance(approved_state):
    state, original = case(approved_state)
    first = original[0]
    second = normalize_artifact({**first, "artifact_id": "synthetic-other-order-change", "version_id": "second-capture"})
    batch = [first, second]
    for source in batch:
        source.update(source_commit_sha="a" * 40, source_file="docs/orders.md", _event_batch_complete=True,
                      _event_group_artifact_keys=[artifact_key(a) for a in batch])
    catalog = build_delta_catalog(state, batch)
    invalid = effect(state, catalog, "A0002", s0_claim_quote="A target policy that S0 never stated.")
    fake = Replies(response(state, catalog, {"A0001": [effect(state, catalog)], "A0002": [invalid]}))
    reviewer = judge(fake)
    accepted, feedback = reviewer.review_event(state, batch, [])
    assert not accepted and not reviewer.last_reviews and len(feedback) == 2
    assert all(x["failure_class"] == "technical_verification_failure" for x in feedback)


def test_very_short_complete_s0_target_is_quotable(approved_state):
    state, batch = case(approved_state, target="Use Queue.")
    accepted, feedback, _, _ = run_case(state, batch)
    assert len(accepted) == 1 and not feedback
    assert accepted[0]["semantic_assessment"]["s0_claim_quote"] == "Use Queue."

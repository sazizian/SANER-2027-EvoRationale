"""Synthetic evidence-trace contract checks; fake judgments do not measure F1."""
from copy import deepcopy
import json
from types import SimpleNamespace

import pytest

from evorationale.delta_context import build_delta_catalog
from evorationale.delta_verification import DeltaSemanticJudge
from evorationale.evidence_trace_verification import EvidenceTraceSemanticJudge
from evorationale.model import artifact_key, element_by_id, normalize_artifact


TARGET = "Persist approved orders through CentralQueue."
LOCAL = "@@ -1 +1 @@\n-Consumer reads approved orders from CentralQueue.\n+Consumer reads approved orders from LocalLedger.\n"
CONTRACT = "@@ -20 +20 @@\n-CentralQueue is the ordinary persistence authority.\n+LocalLedger replaces CentralQueue as ordinary persistence authority; CentralQueue remains optional.\n"


def case(approved_state, content=LOCAL, sibling=None, source_type="git_commit_diff_hunk", target=TARGET):
    state = deepcopy(approved_state)
    state["implementation_scope"].append({"id": "TRACE_TARGET", "source": "fixture://design", "text": target})
    first = normalize_artifact({"artifact_id": "synthetic-order-consumer", "repository": state["repository"],
                                "title": "Order persistence evidence", "source_type": source_type,
                                "source_location": "fixture://orders", "timestamp": "2024-02-01T00:00:00Z",
                                "content": content})
    batch = [first]
    if sibling:
        batch.append(normalize_artifact({**first, "artifact_id": "synthetic-order-contract", "version_id": "contract",
                                         "content_sha256": "", "content": sibling}))
        for artifact in batch:
            artifact.update(source_commit_sha="a" * 40, source_file="docs/orders.md", _event_batch_complete=True,
                            _event_group_artifact_keys=[artifact_key(a) for a in batch])
    return state, batch


def effect(state, catalog, **changes):
    own = [(handle, line) for handle, line in catalog["lines"].items() if line["artifact_handle"] == "A0001"]
    return {"passage_handle": next(h for h, p in catalog["passages"].items() if p["artifact_handle"] == "A0001"),
            "element_id": "TRACE_TARGET", "s0_claim_quote": element_by_id(state)["TRACE_TARGET"]["text"],
            "before_line_handles": [h for h, line in own if line["role"] in {"removed", "unchanged"}],
            "after_line_handles": [h for h, line in own if line["role"] in {"added", "unchanged", "statement"}],
            "context_line_handles": [], "before_claim": "Orders persist in CentralQueue.",
            "after_claim": "Orders persist in LocalLedger with an optional CentralQueue path.",
            "change_kind": "dependent_replacement", "source_role": "adopted_design",
            "claim_scope": "material_subclaim", "whole_element_supported": False,
            "scope_match": True, "material_target_delta": True, "replacement_is_explicit": True,
            "surviving_clause_masks_replacement": False, "confidence": .8,
            "evidence_basis": "adopted_design_statement", "qualification": "Ordinary path changes; optional legacy path remains.",
            "reason": "The local consumer migration depends on the explicit captured persistence contract.",
            "effect_basis": "dependent_migration", "local_contribution": "Consumer switches its persistence dependency.",
            "current_claim_entailed": False, "context_establishes_replacement": True, **changes}


def response(state, catalog, effects=None):
    effects = effects or {}
    return {"considered_element_ids": list(element_by_id(state)),
            "reviews": [{"artifact_handle": handle, "status": "relation_found" if effects.get(handle) else "no_material_relation",
                         "reason": "All fixed targets independently considered.",
                         "support_reason": "Current supporting source statements separately assessed.",
                         "change_reason": "Novel design changes separately assessed.",
                         "links": effects.get(handle, [])} for handle in catalog["artifacts"]]}


class Replies:
    def __init__(self, reply):
        self.reply, self.calls = reply, []

    def create(self, **request):
        self.calls.append(deepcopy(request))
        return SimpleNamespace(status="completed", output_text=json.dumps(self.reply))


def evaluate(state, batch, changes=None, transform=None):
    changes = changes or {}
    catalog = build_delta_catalog(state, batch)
    item = effect(state, catalog, **(changes or {}))
    if item["change_kind"] == "dependent_replacement" and len(batch) > 1 and "context_line_handles" not in changes:
        item["context_line_handles"] = [h for h, line in catalog["lines"].items()
                                       if line["artifact_handle"] == "A0002" and line["role"] == "added"]
    reply = response(state, catalog, {"A0001": [item]})
    if transform:
        transform(reply, catalog)
    fake = Replies(reply)
    judge = EvidenceTraceSemanticJudge("fixture", client=SimpleNamespace(responses=fake))
    accepted, feedback = judge.review_event(state, batch, [])
    return accepted, feedback, judge, fake


def support_fields(**changes):
    return {"change_kind": "documented_support", "effect_basis": "current_design_statement",
            "before_claim": "Approved orders persist through CentralQueue.",
            "after_claim": "Approved orders persist through CentralQueue.",
            "material_target_delta": False, "replacement_is_explicit": False,
            "current_claim_entailed": True, "context_establishes_replacement": False,
            "qualification": "New concrete source evidence for an existing design, not deployed validation.",
            "reason": "The added source assertion documents the exact fixed persistence design.",
            "local_contribution": "The newly added persistence statement directly states the fixed mechanism.",
            **changes}


def test_new_current_statement_supports_existing_design_without_new_drift(approved_state):
    patch = "@@ -1,0 +1 @@\n+Approved orders are persisted through CentralQueue by the order writer.\n"
    state, batch = case(approved_state, patch)
    accepted, feedback, judge, fake = evaluate(state, batch, support_fields())
    assert len(accepted) == 1 and not feedback and len(fake.calls) == 1
    assessment = accepted[0]["semantic_assessment"]
    assert accepted[0]["relation"] == "supports" and assessment["architectural_change"] is False
    assert assessment["assessment_kind"] == "CURRENT_SOURCE_EVIDENCE_TRACE"
    assert assessment["deployed_behavior_verified"] is False and assessment["semantic_policy"] == "evidence-trace"
    assert judge.last_reviews[0]["support_reason"] and judge.last_reviews[0]["change_reason"]


def test_operational_witness_has_code_owned_relation_and_basis(approved_state):
    patch = "@@ -1,0 +1 @@\n+The order persistence counter increments after an approved order is committed through CentralQueue.\n"
    state, batch = case(approved_state, patch)
    accepted, feedback, _, _ = evaluate(state, batch, support_fields(change_kind="operational_witness", effect_basis="operational_witness"))
    assert len(accepted) == 1 and not feedback and accepted[0]["relation"] == "supports"


def test_dependent_replacement_needs_exact_external_current_contract(approved_state):
    state, batch = case(approved_state, sibling=CONTRACT)
    accepted, feedback, _, _ = evaluate(state, batch, {})
    assert len(accepted) == 1 and not feedback and accepted[0]["relation"] == "supersedes"
    assert accepted[0]["semantic_assessment"]["exact_context_source_lines"] == [CONTRACT.splitlines()[2]]


@pytest.mark.parametrize("changes,reason", [
    ({"context_line_handles": []}, "no_current_external_contract"),
    ({"context_establishes_replacement": False}, "no_current_external_contract"),
    ({"before_line_handles": []}, "no_local_migration_sides"),
    ({"after_line_handles": []}, "no_local_migration_sides"),
    ({"replacement_is_explicit": False}, "replacement_not_established"),
    ({"scope_match": False}, "target_scope_mismatch"),
    ({"local_contribution": ""}, "invalid_evidence_trace_effect_basis"),
])
def test_dependent_replacement_cannot_borrow_unestablished_contract(approved_state, changes, reason):
    state, batch = case(approved_state, sibling=CONTRACT)
    accepted, feedback, _, _ = evaluate(state, batch, changes)
    assert not accepted and any(reason in item for entry in feedback for item in entry["reasons"])


def test_own_context_does_not_meet_external_replacement_contract(approved_state):
    state, batch = case(approved_state, sibling=CONTRACT)
    def own_context(reply, catalog):
        reply["reviews"][0]["links"][0]["context_line_handles"] = [h for h, line in catalog["lines"].items()
                                                                      if line["artifact_handle"] == "A0001" and line["role"] == "added"]
    accepted, feedback, _, _ = evaluate(state, batch, {}, own_context)
    assert not accepted and "MODEL_ASSESSED:dependent_replacement_has_no_current_external_contract" in feedback[0]["reasons"]


def test_unrelated_consumer_cannot_override_scope_assessment(approved_state):
    unrelated = "@@ -1 +1 @@\n-Consumer uses scheduling weight 5.\n+Consumer uses scheduling weight 6.\n"
    state, batch = case(approved_state, unrelated, sibling=CONTRACT)
    accepted, feedback, _, _ = evaluate(state, batch, {"scope_match": False,
                                                     "local_contribution": "This unrelated scheduling edit does not migrate persistence."})
    assert not accepted and "MODEL_ASSESSED:target_scope_mismatch" in feedback[0]["reasons"]


def test_current_proposal_context_cannot_be_promoted_to_adopted_replacement(approved_state):
    proposal = "@@ -20,0 +20 @@\n+We could someday replace CentralQueue with LocalLedger.\n"
    state, batch = case(approved_state, sibling=proposal)
    accepted, feedback, _, _ = evaluate(state, batch, {"source_role": "proposal_or_alternative",
                                                     "context_establishes_replacement": False,
                                                     "qualification": "This current discussion proposes, but does not adopt, the replacement."})
    assert not accepted
    assert "MODEL_ASSESSED:proposal_is_not_adopted_replacement" in feedback[0]["reasons"]
    assert "MODEL_ASSESSED:dependent_replacement_has_no_current_external_contract" in feedback[0]["reasons"]


@pytest.mark.parametrize("changes,reason", [
    ({"current_claim_entailed": False}, "current_fixed_claim_not_entailed"),
    ({"effect_basis": "dependent_migration"}, "kind_basis_mismatch"),
    ({"scope_match": False}, "target_scope_mismatch"),
    ({"source_role": "proposal_or_alternative"}, "discussion_is_not_qualified_direct_rationale"),
    ({"evidence_basis": "hypothetical_benefit"}, "does_not_corroborate_target"),
    ({"claim_scope": "whole_element", "whole_element_supported": False}, "whole_scope_without_whole_element_support"),
    ({"qualification": ""}, "missing_qualification"),
])
def test_trace_support_still_requires_entailment_scope_authority_and_qualification(approved_state, changes, reason):
    state, batch = case(approved_state, "@@ -1,0 +1 @@\n+Approved orders persist through CentralQueue.\n")
    accepted, feedback, _, _ = evaluate(state, batch, support_fields(**changes))
    assert not accepted and any(reason in item for entry in feedback for item in entry["reasons"])


def test_unchanged_context_cannot_gain_support_from_unrelated_changed_line(approved_state):
    patch = "@@ -1,2 +1,2 @@\n-Documentation revision 5.\n+Documentation revision 6.\n Approved orders persist through CentralQueue.\n"
    state, batch = case(approved_state, patch)
    def unchanged_proof(reply, catalog):
        reply["reviews"][0]["links"][0]["after_line_handles"] = [h for h, line in catalog["lines"].items() if line["role"] == "unchanged"]
    accepted, feedback, _, _ = evaluate(state, batch, support_fields(), unchanged_proof)
    assert not accepted and "MODEL_ASSESSED:evidence_trace_support_has_no_added_local_proof" in feedback[0]["reasons"]


@pytest.mark.parametrize("old,new", [
    ("Approved orders persist through CentralQueue,", "Approved orders persist through CentralQueue."),
    ("Approved orders persist through `CentralQueue`.", "Approved orders persist through CentralQueue."),
])
def test_model_flags_cannot_turn_formatting_into_support(approved_state, old, new):
    state, batch = case(approved_state, "@@ -1 +1 @@\n-" + old + "\n+" + new + "\n")
    accepted, feedback, _, _ = evaluate(state, batch, support_fields())
    assert not accepted
    assert "MODEL_ASSESSED:evidence_trace_has_no_substantive_local_change" in feedback[0]["reasons"]


@pytest.mark.parametrize("reverse_proof_order", [False, True])
def test_reflow_with_unrelated_revision_and_omitted_old_handles_cannot_create_support(approved_state, reverse_proof_order):
    patch = ("@@ -1,2 +1,3 @@\n-Approved orders persist through CentralQueue.\n"
             "+Approved orders persist\n+through CentralQueue.\n"
             "-Documentation revision 5.\n+Documentation revision 6.\n")
    state, batch = case(approved_state, patch)
    def target_only_proof(reply, catalog):
        item = reply["reviews"][0]["links"][0]
        item["before_line_handles"] = []
        item["after_line_handles"] = [h for h, line in catalog["lines"].items()
                                      if line["role"] == "added" and "revision" not in line["text"]]
        if reverse_proof_order:
            item["after_line_handles"].reverse()
    accepted, feedback, _, _ = evaluate(state, batch, support_fields(), target_only_proof)
    assert not accepted
    assert "MODEL_ASSESSED:evidence_trace_support_has_no_added_local_proof" in feedback[0]["reasons"]


def test_direct_policy_sketch_can_support_qualified_actor_control_without_adoption(approved_state):
    target = "Leave failed-order lifecycle decisions to the initiating actor."
    patch = "@@ -1,0 +1 @@\n+In the proposed recovery policy, the initiating actor chooses whether failed orders are retried or recreated.\n"
    state, batch = case(approved_state, patch, target=target)
    accepted, feedback, _, _ = evaluate(state, batch, support_fields(
        change_kind="direct_rationale", effect_basis="direct_rationale_argument",
        evidence_basis="direct_rationale_argument", source_role="proposal_or_alternative",
        before_claim="The discussion contains no proposed failure recovery policy.",
        after_claim="The proposed failure recovery policy places retry or recreation decisions with the actor.",
        local_contribution="The new conditional policy directly argues for actor-owned recovery decisions.",
        qualification="A proposed policy argument supports actor ownership, without establishing deployed recovery behavior."))
    assert len(accepted) == 1 and not feedback
    assert accepted[0]["evidence_scope"] == "discussion"
    assert accepted[0]["semantic_assessment"]["whole_element_supported"] is False


def test_documented_cost_can_weaken_actual_chosen_mechanism_without_adopting_alternative(approved_state):
    patch = "@@ -1,0 +1 @@\n+CentralQueue persistence incurs durable queue migration costs; LocalLedger is only an alternative under discussion.\n"
    state, batch = case(approved_state, patch)
    accepted, feedback, _, _ = evaluate(state, batch, {
        "change_kind": "reduced_justification", "effect_basis": "documented_tradeoff",
        "evidence_basis": "direct_rationale_argument", "source_role": "proposal_or_alternative",
        "before_claim": "The discussion contains no statement of queue migration costs.",
        "after_claim": "The discussion explicitly identifies migration costs of the chosen CentralQueue persistence mechanism.",
        "replacement_is_explicit": False, "context_establishes_replacement": False,
        "qualification": "Documented costs weaken the existing mechanism; the alternative is not adopted.",
        "local_contribution": "The added cost statement directly concerns the chosen persistence mechanism."})
    assert len(accepted) == 1 and not feedback and accepted[0]["relation"] == "weakens"


def test_separate_support_and_change_reasons_are_required_even_for_no_effects(approved_state):
    state, batch = case(approved_state)
    catalog = build_delta_catalog(state, batch)
    reply = response(state, catalog)
    del reply["reviews"][0]["support_reason"]
    fake = Replies(reply)
    accepted, feedback = EvidenceTraceSemanticJudge("fixture", client=SimpleNamespace(responses=fake)).review_event(state, batch, [])
    assert not accepted and feedback[0]["failure_class"] == "technical_verification_failure"
    assert feedback[0]["reasons"] == ["semantic_judge_error:invalid_evidence_trace_review_reasons"]


def test_unknown_target_and_invented_interim_claim_remain_technical_failure(approved_state):
    state, batch = case(approved_state)
    accepted, feedback, _, _ = evaluate(state, batch, support_fields(s0_claim_quote="Existing order policies may be modified later."))
    assert not accepted and feedback[0]["reasons"] == ["semantic_judge_error:invalid_exact_s0_claim_anchor"]


def test_v45_schema_and_semantics_remain_separate(approved_state):
    state, batch = case(approved_state)
    catalog = build_delta_catalog(state, batch)
    old = DeltaSemanticJudge("fixture", client=SimpleNamespace(responses=Replies({})))
    schema = old._response_schema(catalog, list(element_by_id(state)))
    review = schema["properties"]["reviews"]["items"]
    link = review["properties"]["links"]["items"]
    assert "support_reason" not in review["properties"] and "effect_basis" not in link["properties"]
    assert "documented_support" not in link["properties"]["change_kind"]["enum"]


def test_plain_current_document_needs_no_fabricated_before_side(approved_state):
    state, batch = case(approved_state, "Approved orders persist through CentralQueue.", source_type="issue_comment")
    accepted, feedback, _, _ = evaluate(state, batch, support_fields(before_claim=""))
    assert len(accepted) == 1 and not feedback
    assert accepted[0]["semantic_assessment"]["exact_before_source_lines"] == []

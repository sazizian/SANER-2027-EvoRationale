"""Synthetic source-event judge contract tests; fake providers, no reference labels."""
from copy import deepcopy
import json
from types import SimpleNamespace

import pytest

from evorationale.budget import BudgetExhausted
from evorationale.event_verification import EventSemanticJudge
from evorationale.linking import candidate_link
from evorationale.model import artifact_key, element_by_id, normalize_artifact


PATCH = ("@@ -1 +1 @@\n"
         "-Status publishes reserved and applied budgets.\n"
         "+Status publishes applied budgets.\n")


def decision(proposal_id, **changes):
    return {"proposal_id": proposal_id, "supported": True,
            "reason": "The adopted source establishes this qualified claim.",
            "whole_element_supported": True, "scope_match": True,
            "replacement_is_explicit": False, "material_change": True,
            "surviving_clause_masks_replacement": False,
            "affected_subclaim": "Publish budgets in Status.", "claim_scope": "whole_element",
            "source_role": "adopted_design", **changes}


class FakeResponses:
    def __init__(self, overrides=None, transform=None, incomplete=0):
        self.overrides = overrides or {}
        self.transform = transform
        self.incomplete = incomplete
        self.calls = []

    def create(self, **kwargs):
        self.calls.append(deepcopy(kwargs))
        if len(self.calls) <= self.incomplete:
            return SimpleNamespace(status="incomplete", output_text="")
        payload = json.loads(kwargs["input"])
        result = {"decisions": [decision(p["proposal_id"], **self.overrides)
                                for p in payload["proposals"]]}
        if self.transform:
            result = self.transform(result)
        return SimpleNamespace(status="completed", output_text=json.dumps(result))


def case(approved_state, content=PATCH, *, source_type="git_commit_diff_hunk",
         relation="supersedes", element_type="implementation_scope", quote=None):
    state = deepcopy(approved_state)
    state[element_type].append({"id": "SYNTHETIC_TARGET", "source": "fixture://state",
                               "text": "Publish reserved and applied budgets in Status."})
    artifact = normalize_artifact({
        "artifact_id": "synthetic-status-change", "repository": state["repository"],
        "source_type": source_type, "source_location": "fixture://change",
        "title": "Synthetic status design update", "timestamp": "2024-02-01T00:00:00Z",
        "content": content,
    })
    link = candidate_link(artifact, element_by_id(state)["SYNTHETIC_TARGET"], relation,
                          quote if quote is not None else content.strip(), 0.9)
    return state, [artifact], link


def judge(fake):
    return EventSemanticJudge("fixture-model", client=SimpleNamespace(responses=fake))


def test_event_judge_uses_full_s0_and_all_siblings(approved_state):
    state, batch, link = case(approved_state)
    sibling = normalize_artifact({**batch[0], "artifact_id": "synthetic-local-storage",
                                 "content": "@@ -20,0 +20 @@\n+Reserved budgets are checkpointed locally in preview.\n",
                                 "content_sha256": "", "version_id": "sibling-version"})
    # Pinned source context is explicitly selected as a complete event group.
    batch.append(sibling)
    for artifact in batch:
        artifact.update(source_commit_sha="a" * 40, source_file="docs/status.md",
                        _event_batch_complete=True,
                        _event_group_artifact_keys=[artifact_key(a) for a in batch])
    fake = FakeResponses(overrides={"replacement_is_explicit": True,
                                    "whole_element_supported": False,
                                    "claim_scope": "material_subclaim"})
    accepted, feedback = judge(fake).review_event(state, batch, [link])
    assert len(accepted) == 1 and not feedback
    payload = json.loads(fake.calls[0]["input"])
    assert len(payload["fixed_s0"]["elements"]) == len(element_by_id(state))
    assert "reserved and applied" in json.dumps(payload["same_event_context"])
    assert "checkpointed locally in preview" in json.dumps(payload["same_event_context"])
    assert accepted[0]["semantic_assessment"]["canonical_content_sha256"] == batch[0]["content_sha256"]
    assert accepted[0]["semantic_assessment"]["event_artifact_keys"] == [artifact_key(a) for a in batch]


def test_proposal_ids_are_code_owned_and_all_decisions_are_mapped(approved_state):
    state, batch, link = case(approved_state)
    second = {**link, "relation": "weakens", "proposal_id": "model-controlled-id"}
    fake = FakeResponses(overrides={"replacement_is_explicit": True})
    accepted, feedback = judge(fake).review_event(state, batch, [link, second])
    assert len(accepted) == 2 and not feedback
    assert [p["proposal_id"] for p in json.loads(fake.calls[0]["input"])["proposals"]] == ["P0001", "P0002"]
    assert [a["semantic_assessment"]["proposal_id"] for a in accepted] == ["P0001", "P0002"]


@pytest.mark.parametrize("overrides", [
    {"artifact_key": "unknown"}, {"artifact_key": []}, {"repository": "another/repository"},
    {"content_sha256": "bad"}, {"timestamp": "2024-02-02T00:00:00Z"},
    {"first_auditable_at": "2024-02-02T00:00:00Z"}, {"version_id": "wrong-version"},
    {"source_type": "wrong-type"}, {"source_location": "wrong-location"},
    {"decision_element_type": "requirements"}, {"decision_element_id": []},
    {"relation": "improves"}, {"relation": []}, {"relation_confidence": True},
    {"relation_confidence": float("nan")}, {"relation_confidence": 1.01},
    {"quote": "an invented source sentence"},
])
def test_bad_provenance_never_reaches_provider(approved_state, overrides):
    state, batch, link = case(approved_state)
    fake = FakeResponses()
    accepted, feedback = judge(fake).review_event(state, batch, [{**link, **overrides}])
    assert not accepted and feedback and not fake.calls
    assert all("semantic_assessment" not in item for item in feedback)


def test_bad_proposal_does_not_hide_other_valid_proposals(approved_state):
    state, batch, link = case(approved_state)
    fake = FakeResponses(overrides={"replacement_is_explicit": True})
    accepted, feedback = judge(fake).review_event(state, batch, [{**link, "quote": "invented"}, link])
    assert len(accepted) == 1 and len(feedback) == 1
    assert accepted[0]["semantic_assessment"]["proposal_id"] == "P0002"


def test_removed_only_support_is_rejected_before_hosted_request(approved_state):
    state, batch, link = case(approved_state, relation="supports",
                              quote="-Status publishes reserved and applied budgets.")
    fake = FakeResponses()
    accepted, feedback = judge(fake).review_event(state, batch, [link])
    assert not accepted and not fake.calls
    assert "removed_text_is_not_current_support" in feedback[0]["reasons"]


def test_partial_support_is_explicit_and_does_not_certify_whole(approved_state):
    state, batch, link = case(approved_state,
                              content="@@ -1 +1 @@\n-Status is empty.\n+Status publishes applied budgets.\n",
                              relation="supports", quote="+Status publishes applied budgets.")
    fake = FakeResponses(overrides={"whole_element_supported": False,
                                    "claim_scope": "material_subclaim",
                                    "affected_subclaim": "Publish applied budgets in Status."})
    accepted, feedback = judge(fake).review_event(state, batch, [link])
    assert len(accepted) == 1 and not feedback
    assert accepted[0]["claim_scope"] == "material_subclaim"
    assert accepted[0]["semantic_assessment"]["whole_element_supported"] is False


@pytest.mark.parametrize("overrides,reason", [
    ({"surviving_clause_masks_replacement": True}, "surviving_clause_masks_replacement"),
    ({"whole_element_supported": False}, "whole_scope_without_whole_element_support"),
    ({"whole_element_supported": False, "claim_scope": "material_subclaim", "affected_subclaim": ""},
     "invalid_partial_support_scope"),
    ({"claim_scope": "material_subclaim"}, "invalid_partial_support_scope"),
])
def test_positive_model_vote_cannot_bypass_support_scope_guards(approved_state, overrides, reason):
    state, batch, link = case(approved_state, relation="supports",
                              quote="+Status publishes applied budgets.")
    fake = FakeResponses(overrides=overrides)
    accepted, feedback = judge(fake).review_event(state, batch, [link])
    assert not accepted and any(reason in item for item in feedback[0]["reasons"])


@pytest.mark.parametrize("overrides,reason", [
    ({"scope_match": False}, "target_scope_mismatch"),
    ({"material_change": False}, "no_material_change_in_target_hunk"),
    ({"replacement_is_explicit": False}, "replacement_not_established"),
    ({"affected_subclaim": ""}, "missing_affected_subclaim"),
    ({"source_role": "implementation_detail"}, "source_role_does_not_establish_rationale"),
    ({"source_role": "unknown"}, "source_role_does_not_establish_rationale"),
    ({"source_role": "proposal_or_alternative"}, "proposal_is_not_adopted_replacement"),
])
def test_positive_model_vote_cannot_bypass_event_relation_guards(approved_state, overrides, reason):
    state, batch, link = case(approved_state)
    fake = FakeResponses(overrides={"replacement_is_explicit": True, **overrides})
    accepted, feedback = judge(fake).review_event(state, batch, [link])
    assert not accepted and any(reason in item for item in feedback[0]["reasons"])
    assert "semantic_assessment" in feedback[0] and "failure_class" not in feedback[0]


def test_ordinary_source_does_not_require_changed_baseline(approved_state):
    state, batch, link = case(approved_state, content="Status publishes reserved and applied budgets.",
                              source_type="pull_request_body", relation="supports")
    fake = FakeResponses(overrides={"material_change": False})
    accepted, feedback = judge(fake).review_event(state, batch, [link])
    assert len(accepted) == 1 and not feedback


def test_discussion_support_preserves_evidence_scope(approved_state):
    state, batch, link = case(approved_state, content="Proposal: separating budgets would simplify diagnosis.",
                              source_type="issue_comment", relation="supports", element_type="requirements")
    fake = FakeResponses(overrides={"source_role": "proposal_or_alternative",
                                    "reason": "The proposal discusses support, without establishing adoption."})
    accepted, feedback = judge(fake).review_event(state, batch, [link])
    assert len(accepted) == 1 and not feedback
    assert accepted[0]["evidence_scope"] == "discussion"
    assert "without establishing adoption" in accepted[0]["semantic_check"]


def test_proposal_cannot_establish_adopted_implementation(approved_state):
    state, batch, link = case(approved_state, content="Proposal: Status could publish these budgets.",
                              source_type="issue_comment", relation="supports")
    fake = FakeResponses(overrides={"source_role": "proposal_or_alternative"})
    accepted, feedback = judge(fake).review_event(state, batch, [link])
    assert not accepted and "MODEL_ASSESSED:proposal_does_not_establish_adopted_implementation" in feedback[0]["reasons"]


@pytest.mark.parametrize("field", ["supported", "whole_element_supported", "scope_match",
                                   "replacement_is_explicit", "material_change",
                                   "surviving_clause_masks_replacement"])
def test_non_boolean_fields_are_technical_not_semantic_rejections(approved_state, field):
    state, batch, link = case(approved_state)
    fake = FakeResponses(overrides={field: "true"})
    accepted, feedback = judge(fake).review_event(state, batch, [link])
    assert not accepted
    assert feedback[0]["reasons"] == ["semantic_judge_error:invalid_event_judge_fields"]
    assert feedback[0]["failure_class"] == "technical_verification_failure"
    assert "semantic_assessment" not in feedback[0]


@pytest.mark.parametrize("transform,code", [
    (lambda r: {"decisions": []}, "missing_event_judge_proposal_id"),
    (lambda r: {"decisions": r["decisions"] * 2}, "duplicate_event_judge_proposal_id"),
    (lambda r: {"decisions": [{**r["decisions"][0], "proposal_id": "UNKNOWN"}]},
     "unknown_event_judge_proposal_id"),
    (lambda r: {"decisions": [{**r["decisions"][0], "reason": []}]}, "invalid_event_judge_fields"),
    (lambda r: {"decisions": [{**r["decisions"][0], "claim_scope": "discussion"}]}, "invalid_event_judge_fields"),
    (lambda r: {"decisions": [{**r["decisions"][0], "source_role": "approved"}]}, "invalid_event_judge_fields"),
    (lambda r: {"decisions": [{**r["decisions"][0], "unexpected": True}]}, "invalid_event_judge_fields"),
    (lambda r: {"decisions": r["decisions"], "unexpected": True}, "invalid_event_judge_decisions"),
])
def test_malformed_batch_response_fails_closed_as_technical(approved_state, transform, code):
    state, batch, link = case(approved_state)
    fake = FakeResponses(transform=transform)
    accepted, feedback = judge(fake).review_event(state, batch, [link])
    assert not accepted and feedback[0]["reasons"] == ["semantic_judge_error:" + code]
    assert feedback[0]["failure_class"] == "technical_verification_failure"


def test_invalid_one_of_multiple_decisions_does_not_partially_accept_batch(approved_state):
    state, batch, link = case(approved_state)
    fake = FakeResponses(transform=lambda r: {"decisions": [r["decisions"][0],
                                      {**r["decisions"][1], "supported": "true"}]})
    accepted, feedback = judge(fake).review_event(state, batch, [link, {**link, "relation": "weakens"}])
    assert not accepted and len(feedback) == 2
    assert all(f["failure_class"] == "technical_verification_failure" for f in feedback)


def test_request_charging_covers_schema_instructions_and_each_transport_attempt(approved_state):
    state, batch, link = case(approved_state)
    fake = FakeResponses(overrides={"replacement_is_explicit": True}, incomplete=1)
    charges, observations = [], []

    class Charge:
        def __call__(self, payload):
            charges.append(deepcopy(payload))

        def record_response(self, response):
            observations.append(response)

    accepted, feedback = judge(fake).review_event(state, batch, [link], charge=Charge())
    assert len(accepted) == 1 and not feedback
    assert len(charges) == len(fake.calls) == len(observations) == 2
    for charged, request in zip(charges, fake.calls):
        assert charged == request
        assert charged["instructions"] and charged["text"]["format"]["schema"]
        assert json.loads(charged["input"])["same_event_context"]


def test_input_budget_exhaustion_propagates_before_paid_request(approved_state):
    state, batch, link = case(approved_state)
    fake = FakeResponses()

    def charge(_):
        raise BudgetExhausted("cumulative_input_token_limit")

    with pytest.raises(BudgetExhausted):
        judge(fake).review_event(state, batch, [link], charge=charge)
    assert not fake.calls


def test_provider_error_is_technical_not_semantic_rejection(approved_state):
    state, batch, link = case(approved_state)

    class BrokenResponses:
        def create(self, **_):
            raise ConnectionError("fixture outage")

    accepted, feedback = judge(BrokenResponses()).review_event(state, batch, [link])
    assert not accepted and feedback[0]["reasons"] == ["semantic_judge_error:ConnectionError"]
    assert feedback[0]["failure_class"] == "technical_verification_failure"


def test_secret_bearing_exact_quote_is_not_sent(approved_state):
    state, batch, link = case(approved_state, content="Password: fixture-secret-value",
                              source_type="issue_comment", relation="supports")
    fake = FakeResponses()
    accepted, feedback = judge(fake).review_event(state, batch, [link])
    assert not accepted and not fake.calls
    assert "unquotable_sensitive_source_span" in feedback[0]["reasons"]


def test_state_keywords_and_sibling_context_are_redacted_without_quote_fabrication(approved_state):
    state, batch, link = case(approved_state, content="Status publishes budgets.\nPassword: fixture-secret-value",
                              source_type="issue_comment", relation="supports", quote="Status publishes budgets.")
    state["requirements"][0]["keywords"] = ["secret: another-fixture-secret"]
    fake = FakeResponses()
    accepted, feedback = judge(fake).review_event(state, batch, [link])
    assert len(accepted) == 1 and not feedback
    sent = fake.calls[0]["input"]
    assert "fixture-secret-value" not in sent and "another-fixture-secret" not in sent
    assert accepted[0]["quote"] == "Status publishes budgets."


def test_full_state_text_is_not_silently_truncated(approved_state):
    state, batch, link = case(approved_state, content="Status publishes budgets.",
                              source_type="issue_comment", relation="supports")
    state["requirements"][0]["text"] = "A " * 2500 + "A material final clause."
    fake = FakeResponses()
    accepted, feedback = judge(fake).review_event(state, batch, [link])
    assert len(accepted) == 1 and not feedback
    assert "A material final clause." in fake.calls[0]["input"]


def test_incomplete_diff_comparison_fails_before_provider(approved_state):
    state, batch, link = case(approved_state, content=PATCH.replace("@@ -1 +1 @@", "@@ -1,8 +1,8 @@"))
    fake = FakeResponses()
    accepted, feedback = judge(fake).review_event(state, batch, [link])
    assert not accepted and not fake.calls
    assert "semantic_judge_error:incomplete_canonical_event_context" in feedback[0]["reasons"]
    assert feedback[0]["failure_class"] == "technical_verification_failure"


def test_corrupt_sibling_never_becomes_model_authority(approved_state):
    state, batch, link = case(approved_state)
    sibling = deepcopy(batch[0])
    sibling.update(artifact_id="synthetic-sibling", content="Tampered source bytes.")
    batch.append(sibling)
    fake = FakeResponses()
    accepted, feedback = judge(fake).review_event(state, batch, [link])
    assert not accepted and not fake.calls
    assert feedback[0]["reasons"] == ["semantic_judge_error:invalid_canonical_event_context"]


def test_empty_and_malformed_proposals_are_safe(approved_state):
    state, batch, _ = case(approved_state)
    fake = FakeResponses()
    assert judge(fake).review_event(state, batch, []) == ([], [])
    accepted, feedback = judge(fake).review_event(state, batch, [None])
    assert not accepted and feedback[0]["reasons"] == ["malformed_evidence_link"]
    accepted, feedback = judge(fake).review_event(state, batch, {})
    assert not accepted and feedback[0]["reasons"] == ["proposed_links_not_a_list"]
    assert not fake.calls

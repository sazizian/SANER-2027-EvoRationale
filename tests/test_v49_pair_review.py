"""Synthetic protocol/provenance checks; fake votes do not measure hosted F1."""
from copy import deepcopy
import json
from types import SimpleNamespace

import pytest

from evorationale.delta_context import build_delta_catalog
from evorationale.evidence_trace_verification import EvidenceTraceSemanticJudge, EVIDENCE_TRACE_INSTRUCTIONS
from evorationale.model import artifact_key, element_by_id, normalize_artifact
from evorationale.pair_review_verification import PairReviewSemanticJudge
from test_v46_evidence_trace_verification import case, effect, response, Replies, support_fields, CONTRACT


SUPPORT_PATCH = "@@ -1,0 +1 @@\n+Approved orders persist through CentralQueue.\n"


def pair_response(state, catalog, focus=None, effects=None, uncertain=None):
    focus = focus or list(catalog["artifacts"])
    effects = effects or {}
    uncertain = uncertain or set()
    result = response(state, catalog, effects)
    result["reviews"] = [r for r in result["reviews"] if r["artifact_handle"] in focus]
    for row in result["reviews"]:
        pairs = []
        for target in element_by_id(state):
            relations = sorted({PairReviewSemanticJudge.change_relations[e["change_kind"]]
                                for e in row["links"] if e["element_id"] == target
                                and PairReviewSemanticJudge.change_relations[e["change_kind"]] is not None})
            pairs.append({"element_id": target, "outcome": "relation_found" if relations else
                          "insufficient_evidence" if target in uncertain else "no_relation",
                          "reason": "Exact source predicate and authority independently assessed.",
                          "relations": relations})
        row["pair_outcomes"] = pairs
        if not row["links"] and uncertain:
            row["status"] = "insufficient_evidence"
    return result


def decision(candidate_id="C0001", verdict="confirm"):
    return {"candidate_id": candidate_id, "verdict": verdict,
            "reason": "The proposed qualified relation is independently assessed.",
            "predicate_reason": "The exact source predicate concerns the fixed target.",
            "contribution_reason": "The selected local lines add substantive evidence.",
            "authority_reason": "The source statement establishes the stated authority."}


class Scripted:
    def __init__(self, replies):
        self.replies = list(replies)
        self.calls = []

    def create(self, **request):
        self.calls.append(deepcopy(request))
        reply = self.replies.pop(0)
        if isinstance(reply, Exception):
            raise reply
        return SimpleNamespace(status="completed", output_text=json.dumps(reply))


def run(state, batch, replies, cls=PairReviewSemanticJudge):
    fake = Scripted(replies)
    judge = cls("fixture", client=SimpleNamespace(responses=fake))
    accepted, feedback = judge.review_event(state, batch, [])
    return accepted, feedback, judge, fake


def positive_case(approved_state, transform=None):
    state, batch = case(approved_state, SUPPORT_PATCH)
    catalog = build_delta_catalog(state, batch)
    item = effect(state, catalog, **support_fields())
    reply = pair_response(state, catalog, effects={"A0001": [item]})
    if transform:
        transform(reply)
    return state, batch, catalog, reply


def test_negative_grid_is_explicit_and_does_not_call_critic(approved_state):
    state, batch = case(approved_state, SUPPORT_PATCH)
    catalog = build_delta_catalog(state, batch)
    accepted, feedback, judge, fake = run(state, batch, [pair_response(state, catalog)])
    assert not accepted and not feedback and len(fake.calls) == 1
    row = judge.last_reviews[0]
    assert row["pair_outcomes_complete"] is True and row["pair_review_missing_element_ids"] == []
    assert row["pair_outcome_count"] == len(element_by_id(state))
    assert {p["element_id"] for p in row["explicit_pair_outcomes"]} == set(element_by_id(state))
    assert all(p["outcome"] == "no_relation" for p in row["explicit_pair_outcomes"])
    assert row["pair_outcomes_epistemic_status"] == "MODEL_ASSESSED"


@pytest.mark.parametrize("change,code", [
    (lambda r: r["reviews"][0]["pair_outcomes"].pop(), "incomplete_artifact_target_pairs"),
    (lambda r: r["reviews"][0]["pair_outcomes"].__setitem__(1, deepcopy(r["reviews"][0]["pair_outcomes"][0])),
     "invalid_or_duplicate_artifact_target_pair"),
    (lambda r: r["reviews"][0]["pair_outcomes"][0].update(element_id="UNSEEN_TARGET"),
     "invalid_or_duplicate_artifact_target_pair"),
    (lambda r: r["reviews"][0]["pair_outcomes"][0].update(reason=" "),
     "invalid_or_duplicate_artifact_target_pair"),
    (lambda r: r["reviews"][0]["pair_outcomes"][0].update(reason="x" * 401),
     "invalid_or_duplicate_artifact_target_pair"),
])
def test_missing_duplicate_unknown_and_unexplained_pairs_fail_closed(approved_state, change, code):
    state, batch = case(approved_state, SUPPORT_PATCH)
    catalog = build_delta_catalog(state, batch)
    reply = pair_response(state, catalog)
    change(reply)
    accepted, feedback, judge, fake = run(state, batch, [reply])
    assert not accepted and not judge.last_reviews and len(fake.calls) == 1
    assert feedback[0]["failure_class"] == "technical_verification_failure"
    assert feedback[0]["reasons"] == ["semantic_judge_error:" + code]


@pytest.mark.parametrize("relations,outcome", [([], "no_relation"), (["weakens"], "relation_found"),
                                                (["supports", "supports"], "relation_found")])
def test_pair_relations_must_match_emitted_target_links(approved_state, relations, outcome):
    state, batch, _, reply = positive_case(approved_state)
    row = next(p for p in reply["reviews"][0]["pair_outcomes"] if p["element_id"] == "TRACE_TARGET")
    row.update(relations=relations, outcome=outcome)
    accepted, feedback, judge, fake = run(state, batch, [reply])
    assert not accepted and not judge.last_reviews and len(fake.calls) == 1
    assert feedback[0]["failure_class"] == "technical_verification_failure"


def test_uncertain_pair_remains_uncertain_without_a_positive_hypothesis(approved_state):
    state, batch = case(approved_state, SUPPORT_PATCH)
    catalog = build_delta_catalog(state, batch)
    accepted, feedback, judge, fake = run(state, batch, [pair_response(state, catalog, uncertain={"TRACE_TARGET"})])
    assert not accepted and not feedback and len(fake.calls) == 1
    assert judge.last_reviews[0]["status"] == "insufficient_evidence"
    assert next(p for p in judge.last_reviews[0]["explicit_pair_outcomes"]
                if p["element_id"] == "TRACE_TARGET")["outcome"] == "insufficient_evidence"


@pytest.mark.parametrize("verdict,accepted_count,reason", [("confirm", 1, None),
    ("reject", 0, "MODEL_ASSESSED:candidate_review_rejected"),
    ("insufficient_evidence", 0, "MODEL_ASSESSED:candidate_review_insufficient_evidence")])
def test_independent_candidate_verdict_is_preserved_and_routed(approved_state, verdict, accepted_count, reason):
    state, batch, _, reply = positive_case(approved_state)
    accepted, feedback, judge, fake = run(state, batch, [reply, {"decisions": [decision(verdict=verdict)]}])
    assert len(accepted) == accepted_count and len(fake.calls) == 2
    assert fake.calls[0]["text"]["format"]["name"] == judge.request_name
    assert fake.calls[1]["text"]["format"]["name"] == judge.candidate_request_name
    metadata = judge.last_reviews[0]["candidate_review_decisions"][0]
    assert metadata["verdict"] == verdict
    assessed = accepted[0]["semantic_assessment"] if accepted else feedback[0]["semantic_assessment"]
    assert assessed["pair_review_candidate_id"] == "C0001"
    assert assessed["pair_review_confirmation"]["verdict"] == verdict
    assert assessed["candidate_check_epistemic_status"] == "MODEL_ASSESSED"
    if reason:
        assert reason in feedback[0]["reasons"]
    else:
        assert not feedback


def test_confirmation_cannot_rescue_failed_shared_entailment_guard(approved_state):
    state, batch, _, reply = positive_case(approved_state)
    reply["reviews"][0]["links"][0]["current_claim_entailed"] = False
    accepted, feedback, _, _ = run(state, batch, [reply, {"decisions": [decision()]}])
    assert not accepted and "MODEL_ASSESSED:current_fixed_claim_not_entailed" in feedback[0]["reasons"]


def test_duplicate_critic_candidate_is_rejected_even_when_count_matches():
    judge = PairReviewSemanticJudge("fixture", client=object())
    with pytest.raises(ValueError, match="invalid_or_duplicate_candidate_review"):
        judge._validate_candidate_response({"decisions": [decision(), decision()]},
                                           [{"candidate_id": "C0001"}, {"candidate_id": "C0002"}])


def test_candidate_size_limit_fails_closed_without_truncating(approved_state, monkeypatch):
    import evorationale.pair_review_verification as module
    monkeypatch.setattr(module, "MAX_CANDIDATES", 0)
    state, batch, _, reply = positive_case(approved_state)
    accepted, feedback, judge, fake = run(state, batch, [reply])
    assert not accepted and not judge.last_reviews and len(fake.calls) == 1
    assert feedback[0]["reasons"] == ["semantic_judge_error:pair_candidate_review_size_limit"]


@pytest.mark.parametrize("critic", [{"decisions": []}, {"decisions": [decision("UNKNOWN")]},
    {"decisions": [dict(decision(), authority_reason="")]}, RuntimeError("fixture transport failure")])
def test_missing_invalid_or_failed_critic_leaves_whole_event_unreviewed(approved_state, critic):
    state, batch, _, reply = positive_case(approved_state)
    accepted, feedback, judge, fake = run(state, batch, [reply, critic])
    assert not accepted and not judge.last_reviews and len(fake.calls) == 2
    assert feedback[0]["failure_class"] == "technical_verification_failure"
    assert judge.last_pair_review_trace[0]["status"] == "VALIDATED"
    assert judge.last_pair_review_trace[-1]["phase"] == "candidate_check"
    assert judge.last_pair_review_trace[-1]["status"] == "REQUESTED"


def multi_artifact_case(approved_state, count=4):
    state, batch = case(approved_state)
    first = batch[0]
    for number in range(2, count + 1):
        content = CONTRACT if number == count else f"@@ -{number},0 +{number} @@\n+Unrelated current documentary addition {number}.\n"
        batch.append(normalize_artifact({**first, "artifact_id": f"synthetic-captured-{number}",
            "version_id": f"captured-{number}", "content_sha256": "", "content": content}))
    keys = [artifact_key(a) for a in batch]
    for artifact in batch:
        artifact.update(source_commit_sha="a" * 40, source_file="docs/orders.md", _event_batch_complete=True,
                        _event_group_artifact_keys=keys)
    return state, batch


def test_chunked_focus_preserves_external_contract_and_all_original_source(approved_state):
    state, batch = multi_artifact_case(approved_state)
    catalog = build_delta_catalog(state, batch)
    item = effect(state, catalog, context_line_handles=[h for h, l in catalog["lines"].items()
                                                       if l["artifact_handle"] == "A0004" and l["role"] == "added"])
    replies = [pair_response(state, catalog, ["A0001", "A0002", "A0003"], {"A0001": [item]}),
               pair_response(state, catalog, ["A0004"]), {"decisions": [decision()]}]
    accepted, feedback, judge, fake = run(state, batch, replies)
    assert len(accepted) == 1 and not feedback and len(fake.calls) == 3
    assert len(judge.last_reviews) == 4
    for request, focus in zip(fake.calls[:2], [["A0001", "A0002", "A0003"], ["A0004"]]):
        payload = json.loads(request["input"])
        assert payload["review_artifact_handles"] == focus
        assert len(payload["event_context"]["canonical_artifacts"]) == 4
        assert payload["event_context"]["complete"] is True
        assert request["text"]["format"]["schema"]["properties"]["reviews"]["items"]["properties"]["artifact_handle"]["enum"] == focus
    assert accepted[0]["semantic_assessment"]["exact_context_source_lines"] == [CONTRACT.splitlines()[2]]


def test_later_chunk_failure_never_publishes_false_complete_event_coverage(approved_state):
    state, batch = multi_artifact_case(approved_state)
    catalog = build_delta_catalog(state, batch)
    first = pair_response(state, catalog, ["A0001", "A0002", "A0003"])
    final = pair_response(state, catalog, ["A0004"])
    final["reviews"][0]["pair_outcomes"].pop()
    accepted, feedback, judge, fake = run(state, batch, [first, final])
    assert not accepted and not judge.last_reviews and len(fake.calls) == 2
    assert len(feedback) == 4 and all(f["failure_class"] == "technical_verification_failure" for f in feedback)
    assert judge.last_pair_review_trace[0]["status"] == "VALIDATED"


def test_critic_never_receives_primary_explanations_or_protected_source(approved_state):
    patch = SUPPORT_PATCH.replace("+Approved", "+password=UNSHARED_SOURCE_VALUE\n+Approved")
    state, batch = case(approved_state, patch.replace("+1 @@", "+1,2 @@"))
    catalog = build_delta_catalog(state, batch)
    item = effect(state, catalog, **support_fields(reason="PRIMARY_SECRET_REASON", local_contribution="PRIMARY_SECRET_CONTRIBUTION",
                                                 before_claim="PRIMARY_SECRET_BEFORE", after_claim="PRIMARY_SECRET_AFTER",
                                                 qualification="PRIMARY_SECRET_QUALIFICATION"))
    accepted, feedback, _, fake = run(state, batch, [pair_response(state, catalog, effects={"A0001": [item]}),
                                                   {"decisions": [decision()]}])
    assert len(accepted) == 1 and not feedback
    payload = json.loads(fake.calls[1]["input"])
    hypothesis = payload["candidate_hypotheses"][0]
    assert not {"confidence", "reason", "local_contribution", "before_claim", "after_claim", "qualification"} & set(hypothesis)
    assert "PRIMARY_SECRET" not in fake.calls[1]["input"]
    assert "UNSHARED_SOURCE_VALUE" not in fake.calls[0]["input"] + fake.calls[1]["input"]
    assert "[CREDENTIAL_REDACTED]" in fake.calls[1]["input"]


def test_existing_v46_request_protocol_is_preserved_by_base_hook(approved_state):
    state, batch = case(approved_state, SUPPORT_PATCH)
    catalog = build_delta_catalog(state, batch)
    fake = Replies(response(state, catalog))
    judge = EvidenceTraceSemanticJudge("fixture", client=SimpleNamespace(responses=fake))
    accepted, feedback = judge.review_event(state, batch, [])
    assert not accepted and not feedback and len(fake.calls) == 1
    expected = {"model": "fixture", "reasoning": {"effort": "medium"}, "max_output_tokens": 4096,
                "instructions": EVIDENCE_TRACE_INSTRUCTIONS,
                "input": json.dumps(catalog["payload"], ensure_ascii=False, allow_nan=False),
                "text": {"format": {"type": "json_schema", "name": "independent_fixed_s0_evidence_trace_review",
                                    "strict": True, "schema": judge._response_schema(catalog, list(element_by_id(state)))}}}
    assert fake.calls[0] == expected
    assert "pair_outcomes" not in fake.calls[0]["text"]["format"]["schema"]["properties"]["reviews"]["items"]["properties"]


def test_new_outbound_schemas_use_basic_strict_compatible_shapes(approved_state):
    state, batch, catalog, _ = positive_case(approved_state)
    judge = PairReviewSemanticJudge("fixture", client=object())
    schemas = [judge._response_schema(catalog, list(element_by_id(state))),
               judge._candidate_schema([{"candidate_id": "C0001"}])]

    def inspect(node):
        if isinstance(node, dict):
            assert not {"maxLength", "minLength", "minItems", "maxItems", "uniqueItems"} & set(node)
            if node.get("type") == "object":
                assert node["additionalProperties"] is False
                assert set(node["required"]) == set(node["properties"])
            for value in node.values():
                inspect(value)
        elif isinstance(node, list):
            for value in node:
                inspect(value)

    for schema in schemas:
        inspect(schema)

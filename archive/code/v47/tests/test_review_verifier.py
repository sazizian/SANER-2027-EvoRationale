"""Independent verifier regressions with fake providers and synthetic sources."""
from copy import deepcopy
import json
from types import SimpleNamespace

import pytest

from evorationale.event_verification import EventSemanticJudge
from evorationale.linking import candidate_link
from evorationale.model import artifact_key, element_by_id, normalize_artifact
from evorationale.structured_json import StructuredModelResponseError, request_json_object


class Replies:
    def __init__(self, texts, statuses=None):
        self.texts = texts
        self.statuses = statuses
        self.calls = []

    def create(self, **kwargs):
        self.calls.append(deepcopy(kwargs))
        i = min(len(self.calls) - 1, len(self.texts) - 1)
        result = SimpleNamespace(output_text=self.texts[i])
        if self.statuses is not None:
            result.status = self.statuses[i]
        return result


def review_case(approved_state, *, diff=False):
    state = deepcopy(approved_state)
    state["implementation_scope"].append({
        "id": "REVIEW_TARGET", "source": "fixture://target",
        "text": "Status publishes applied budgets.",
    })
    artifact = normalize_artifact({
        "artifact_id": "review-source", "repository": state["repository"],
        "source_type": "git_commit_diff_hunk" if diff else "issue_comment",
        "source_location": "fixture://review-source", "title": "Adopted status redesign",
        "timestamp": "2024-02-01T00:00:00Z",
        "content": ("@@ -1 +1 @@\n-Status is empty.\n+Status publishes applied budgets.\n"
                    if diff else "Status publishes applied budgets."),
    })
    link = candidate_link(artifact, element_by_id(state)["REVIEW_TARGET"], "supports",
                          artifact["content"].strip(), 0.8)
    decision = {"proposal_id": "P0001", "supported": True, "reason": "Adopted source support.",
                "whole_element_supported": True, "scope_match": True,
                "replacement_is_explicit": False, "material_change": True,
                "surviving_clause_masks_replacement": False,
                "affected_subclaim": "Status publishes applied budgets.",
                "claim_scope": "whole_element", "source_role": "adopted_design"}
    return state, artifact, link, decision


@pytest.mark.parametrize("diff", [False, True])
@pytest.mark.parametrize("quote_kind", ["title", "title_body_boundary"])
def test_event_quote_must_be_contiguous_source_body(approved_state, diff, quote_kind):
    state, artifact, link, decision = review_case(approved_state, diff=diff)
    link["quote"] = (artifact["title"] if quote_kind == "title"
                     else artifact["title"] + "\n" + artifact["content"].splitlines()[0])
    fake = Replies([json.dumps({"decisions": [decision]})], ["completed"])
    accepted, feedback = EventSemanticJudge("fixture", client=SimpleNamespace(responses=fake)).review_event(
        state, [artifact], [link])
    assert not accepted and not fake.calls
    assert feedback[0]["reasons"] == ["quote_not_in_exact_artifact_version"]
    assert "semantic_assessment" not in feedback[0]


def test_exact_body_quote_still_reaches_independent_judge(approved_state):
    state, artifact, link, decision = review_case(approved_state)
    fake = Replies([json.dumps({"decisions": [decision]})], ["completed"])
    accepted, feedback = EventSemanticJudge("fixture", client=SimpleNamespace(responses=fake)).review_event(
        state, [artifact], [link])
    assert len(accepted) == 1 and not feedback and len(fake.calls) == 1
    assert accepted[0]["quote"] == artifact["content"]


def test_version_specific_source_handles_disambiguate_identical_ids_and_hashes(approved_state):
    state, artifact, _, decision = review_case(approved_state, diff=True)
    first = normalize_artifact({**artifact, "version_id": "capture-one"})
    second = normalize_artifact({**artifact, "version_id": "capture-two"})
    batch = [first, second]
    assert first["artifact_id"] == second["artifact_id"]
    assert first["content_sha256"] == second["content_sha256"]
    assert artifact_key(first) != artifact_key(second)
    for item in batch:
        item.update(source_commit_sha="a" * 40, source_file="docs/status.md",
                    _event_batch_complete=True,
                    _event_group_artifact_keys=[artifact_key(source) for source in batch])
    # Proposals intentionally reverse source order; mapping must use canonical
    # version identity, not proposal order, artifact_id, hash or quoted bytes.
    target = element_by_id(state)["REVIEW_TARGET"]
    links = [candidate_link(source, target, "supports", source["content"].strip(), 0.8)
             for source in reversed(batch)]
    reply = {"decisions": [decision, {**decision, "proposal_id": "P0002"}]}
    fake = Replies([json.dumps(reply)], ["completed"])
    accepted, feedback = EventSemanticJudge("fixture", client=SimpleNamespace(responses=fake)).review_event(
        state, batch, links)
    assert len(accepted) == 2 and not feedback
    sent = json.loads(fake.calls[0]["input"])
    sources = sent["same_event_context"]["canonical_artifacts"]
    assert [source["artifact_handle"] for source in sources] == ["A0001", "A0002"]
    proposals = sent["proposals"]
    assert [proposal["artifact_handle"] for proposal in proposals] == ["A0002", "A0001"]
    assert [proposal["artifact_key"] for proposal in proposals] == [artifact_key(second), artifact_key(first)]
    assert [link["semantic_assessment"]["canonical_artifact_key"] for link in accepted] == [
        artifact_key(second), artifact_key(first)]
    assert [link["semantic_assessment"]["canonical_artifact_handle"] for link in accepted] == ["A0002", "A0001"]


@pytest.mark.parametrize("content,quote", [
    ("Password:\nfixture-private-value\nStatus publishes applied budgets.", "fixture-private-value"),
    ("Password:\nfixture-private-value\nStatus publishes applied budgets.", "private-value"),
    # A repeated string has no occurrence selector; one safe occurrence cannot
    # license a second occurrence that is part of a credential or URL.
    ("fixture-private-value is a placeholder.\nPassword: fixture-private-value", "fixture-private-value"),
    ("Docs: https://fixture.invalid/private-part", "private-part"),
])
def test_sensitive_original_source_overlap_never_reaches_standalone_judge(approved_state, content, quote):
    state, artifact, link, decision = review_case(approved_state)
    artifact = normalize_artifact({**artifact, "content": content, "content_sha256": ""})
    link = candidate_link(artifact, element_by_id(state)["REVIEW_TARGET"], "supports", quote, 0.8)
    fake = Replies([json.dumps({"decisions": [decision]})], ["completed"])
    accepted, feedback = EventSemanticJudge("fixture", client=SimpleNamespace(responses=fake)).review_event(
        state, [artifact], [link])
    assert not accepted and not fake.calls
    assert feedback[0]["reasons"] == ["unquotable_sensitive_source_span"]
    assert "semantic_assessment" not in feedback[0]


def test_safe_quote_next_to_multiline_credential_retains_exact_body_citation(approved_state):
    state, artifact, _, decision = review_case(approved_state)
    artifact = normalize_artifact({**artifact, "content_sha256": "",
                                  "content": "Password:\nfixture-private-value\nStatus publishes applied budgets."})
    quote = "Status publishes applied budgets."
    link = candidate_link(artifact, element_by_id(state)["REVIEW_TARGET"], "supports", quote, 0.8)
    fake = Replies([json.dumps({"decisions": [decision]})], ["completed"])
    accepted, feedback = EventSemanticJudge("fixture", client=SimpleNamespace(responses=fake)).review_event(
        state, [artifact], [link])
    assert len(accepted) == 1 and not feedback
    assert accepted[0]["quote"] == quote
    assert "fixture-private-value" not in fake.calls[0]["input"]


def test_event_judge_respects_explicit_output_ceiling_including_retry(approved_state):
    state, artifact, link, decision = review_case(approved_state)
    fake = Replies(["", json.dumps({"decisions": [decision]})], ["incomplete", "completed"])

    class Charge:
        budget = SimpleNamespace(max_output_tokens=700)

        def __init__(self):
            self.requests = []

        def __call__(self, request):
            self.requests.append(deepcopy(request))

    charge = Charge()
    accepted, feedback = EventSemanticJudge("fixture", client=SimpleNamespace(responses=fake)).review_event(
        state, [artifact], [link], charge=charge)
    assert len(accepted) == 1 and not feedback
    assert len(fake.calls) == 2 and fake.calls == charge.requests
    assert [request["max_output_tokens"] for request in fake.calls] == [700, 700]


@pytest.mark.parametrize("duplicate_kind", ["vote", "top_level"])
def test_duplicate_json_keys_never_choose_a_semantic_vote(approved_state, duplicate_kind):
    state, artifact, link, decision = review_case(approved_state)
    if duplicate_kind == "vote":
        text = json.dumps({"decisions": [decision]}).replace(
            '"supported": true', '"supported": false, "supported": true')
    else:
        text = '{"decisions": [], "decisions": ' + json.dumps([decision]) + '}'
    fake = Replies([text, text], ["completed", "completed"])
    accepted, feedback = EventSemanticJudge("fixture", client=SimpleNamespace(responses=fake)).review_event(
        state, [artifact], [link])
    assert not accepted and len(fake.calls) == 2
    assert feedback[0]["reasons"] == ["semantic_judge_error:duplicate_json_key"]
    assert feedback[0]["failure_class"] == "technical_verification_failure"
    assert "semantic_assessment" not in feedback[0]


SCHEMA = {"type": "object", "properties": {"ok": {"type": "boolean"}},
          "required": ["ok"], "additionalProperties": False}


def json_request(fake, **overrides):
    args = {"client": SimpleNamespace(responses=fake), "model": "fixture", "name": "fixture",
            "schema": SCHEMA, "instructions": "JSON only", "payload": {"fixture": True},
            "initial_output_tokens": 600, "output_token_ceiling": 1200, "attempts": 2}
    args.update(overrides)
    return request_json_object(**args)


@pytest.mark.parametrize("number", ["NaN", "Infinity", "-Infinity", "1e10000"])
def test_nonfinite_model_json_is_a_technical_parse_failure(number):
    fake = Replies(['{"ok": true, "number": ' + number + '}'], ["completed"])
    with pytest.raises(StructuredModelResponseError, match="nonfinite_json_number"):
        json_request(fake)
    assert len(fake.calls) == 2


@pytest.mark.parametrize("status", ["queued", "in_progress", "unexpected"])
def test_nonterminal_response_text_is_not_a_final_verdict(status):
    fake = Replies(['{"ok": true}'], [status])
    with pytest.raises(StructuredModelResponseError, match="response_" + status):
        json_request(fake)
    assert len(fake.calls) == 2


def test_duplicate_response_retries_with_charged_larger_budget_then_recovers():
    fake = Replies(['{"ok": false, "ok": true}', '{"ok": false}'], ["completed", "completed"])
    charges = []
    assert json_request(fake, before_request=lambda request: charges.append(deepcopy(request))) == {"ok": False}
    assert charges == fake.calls
    assert [request["max_output_tokens"] for request in fake.calls] == [600, 1200]


def test_legacy_adapter_without_status_still_accepts_valid_json():
    fake = Replies(['{"ok": true}'])
    assert json_request(fake) == {"ok": True}
    assert len(fake.calls) == 1


@pytest.mark.parametrize("field,value", [
    ("attempts", True), ("attempts", 1.5), ("attempts", 3),
    ("initial_output_tokens", False), ("initial_output_tokens", 0.5),
    ("output_token_ceiling", True), ("output_token_ceiling", -1),
])
def test_invalid_retry_or_token_configuration_never_calls_provider(field, value):
    fake = Replies(['{"ok": true}'], ["completed"])
    with pytest.raises(ValueError):
        json_request(fake, **{field: value})
    assert not fake.calls


def test_nonfinite_outbound_payload_never_calls_provider():
    fake = Replies(['{"ok": true}'], ["completed"])
    with pytest.raises(ValueError):
        json_request(fake, payload={"value": float("nan")})
    assert not fake.calls

"""Generic source/coverage integration checks; controlled replies, no API or Gold."""
from copy import deepcopy
import json
from types import SimpleNamespace

import pytest

from evorationale.budget import Budget, BudgetExhausted
from evorationale.event_agent import EventReviewAgent, RequestBudgetTracker
from evorationale.event_context import select_event_batches
from evorationale.event_linking import EventLinker
from evorationale.linking import candidate_link
from evorationale.memory import DecisionMemory
from evorationale.model import element_by_id, normalize_artifact
from evorationale.structured_json import StructuredModelResponseError, request_json_object


def source(state, name="edit", commit="a" * 40):
    return normalize_artifact({"artifact_id": name, "repository": state["repository"],
        "source_type": "git_commit_diff_hunk", "source_location": "fixture://source-event",
        "source_commit_sha": commit, "source_file": "design.md", "title": "Source change",
        "timestamp": "2024-02-01T00:00:00Z",
        "content": "@@ -1 +1 @@\n-Old operation.\n+Fresh material observation.\n"})


class Replies:
    def __init__(self, transform=None):
        self.calls = []
        self.transform = transform

    def create(self, **kwargs):
        self.calls.append(kwargs)
        payload = json.loads(kwargs["input"])
        ids = [e["id"] for e in payload["decision_state"]["elements"]]
        rows = [{"artifact_handle": a["artifact_handle"], "considered_element_ids": ids,
                 "status": "no_material_relation", "reason": "No material relation established.",
                 "links": []} for a in payload["artifacts"]]
        output = {"reviews": rows}
        if self.transform:
            self.transform(output, payload)
        return SimpleNamespace(status="completed", output_text=json.dumps(output))


def linker(fake):
    return EventLinker("fixture-linker", client=SimpleNamespace(responses=fake))


def test_every_artifact_and_every_element_is_visible_without_target_filter(approved_state):
    batch = select_event_batches(approved_state, [source(approved_state, "one"), source(approved_state, "two")], 2)[0]
    fake = Replies()
    l = linker(fake)
    assert l.propose_event(approved_state, batch) == []
    p = json.loads(fake.calls[0]["input"])
    assert len(p["artifacts"]) == len(l.last_reviews) == 2
    assert len(p["decision_state"]["elements"]) == len(element_by_id(approved_state))
    assert all(r["considered_element_ids"] == list(element_by_id(approved_state)) for r in l.last_reviews)
    assert all(a["passages"] for a in p["artifacts"])


def test_same_artifact_id_versions_have_unambiguous_source_handles(approved_state):
    first = source(approved_state, "shared")
    raw = deepcopy(first)
    raw["content"] = raw["content"].replace("Fresh material observation", "Distinct source observation")
    raw.pop("content_sha256")
    raw["version_id"] = "second-version"
    second = normalize_artifact(raw)
    batch = select_event_batches(approved_state, [first, second], 2)[0]
    fake = Replies()
    linker(fake).propose_event(approved_state, batch)
    payload = json.loads(fake.calls[0]["input"])
    entries = payload["event_context"]["canonical_artifacts"]
    assert len(entries) == 2
    assert {e["artifact_id"] for e in entries} == {"shared"}
    by_handle = {e["artifact_handle"]: e for e in entries}
    assert len(by_handle) == 2
    for index, view in enumerate(payload["artifacts"]):
        assert by_handle[view["artifact_handle"]]["content_sha256"] == batch[index]["content_sha256"]


@pytest.mark.parametrize("mutation", ["missing", "duplicate", "unknown", "missing_element", "empty_reason", "extra"])
def test_incomplete_reviews_fail_closed(approved_state, mutation):
    batch = select_event_batches(approved_state, [source(approved_state, "one"), source(approved_state, "two")], 2)[0]
    def corrupt(o, p):
        if mutation == "missing": o["reviews"].pop()
        elif mutation == "duplicate": o["reviews"][1] = deepcopy(o["reviews"][0])
        elif mutation == "unknown": o["reviews"][0]["artifact_handle"] = "A9999"
        elif mutation == "missing_element": o["reviews"][0]["considered_element_ids"] = []
        elif mutation == "empty_reason": o["reviews"][0]["reason"] = " "
        else: o["reviews"][0]["extra"] = "untrusted"
    with pytest.raises(StructuredModelResponseError):
        linker(Replies(corrupt)).propose_event(approved_state, batch)


def test_multiple_material_elements_can_be_proposed_from_one_hunk(approved_state):
    batch = select_event_batches(approved_state, [source(approved_state)], 1)[0]
    ids = list(element_by_id(approved_state))[:2]
    def add(o, p):
        row = o["reviews"][0]
        row["status"] = "relation_found"
        row["links"] = [{"passage_handle": p["artifacts"][0]["passages"][0]["passage_handle"],
                         "element_id": e, "relation": "supports", "confidence": .8} for e in ids]
    proposals = linker(Replies(add)).propose_event(approved_state, batch)
    assert {x["decision_element_id"] for x in proposals} == set(ids)
    assert all(x["quote"] in batch[0]["content"] for x in proposals)


@pytest.mark.parametrize("bad", ["cross_artifact", "bool_confidence", "element_list", "relation_list", "duplicate"])
def test_invalid_proposals_do_not_bypass_exact_handles(approved_state, bad):
    batch = select_event_batches(approved_state, [source(approved_state, "one"), source(approved_state, "two")], 2)[0]
    def corrupt(o, p):
        row = o["reviews"][0]
        row["status"] = "relation_found"
        link = {"passage_handle": p["artifacts"][0]["passages"][0]["passage_handle"],
                "element_id": p["decision_state"]["elements"][0]["id"],
                "relation": "supports", "confidence": .8}
        if bad == "cross_artifact": link["passage_handle"] = p["artifacts"][1]["passages"][0]["passage_handle"]
        elif bad == "bool_confidence": link["confidence"] = True
        elif bad == "element_list": link["element_id"] = []
        elif bad == "relation_list": link["relation"] = []
        row["links"] = [link, deepcopy(link)] if bad == "duplicate" else [link]
    with pytest.raises(StructuredModelResponseError):
        linker(Replies(corrupt)).propose_event(approved_state, batch)


def test_long_material_state_text_is_not_silently_truncated(approved_state):
    s = deepcopy(approved_state)
    s["requirements"][0]["text"] = "Relevant statement. " * 260 + "MATERIAL_FINAL_CLAUSE"
    s["requirements"][0]["keywords"] = ["password=synthetic-private"]
    fake = Replies()
    linker(fake).propose_event(s, select_event_batches(s, [source(s)], 1)[0])
    assert "MATERIAL_FINAL_CLAUSE" in fake.calls[0]["input"]
    assert "synthetic-private" not in fake.calls[0]["input"]


class ControlledLinker:
    def __init__(self, target, fail=False):
        self.target, self.fail, self.calls = target, fail, []
        self.last_reviews = []

    def propose_event(self, state, batch, charge=None):
        self.calls.append(batch)
        if self.fail:
            raise StructuredModelResponseError("incomplete_artifact_reviews")
        from evorationale.model import artifact_key
        self.last_reviews = [{"artifact_key": artifact_key(a), "artifact_id": a["artifact_id"],
            "considered_element_ids": list(element_by_id(state)), "status": "relation_found",
            "reason": "Controlled fixture.", "candidate_links": 1} for a in batch]
        return [candidate_link(a, element_by_id(state)[self.target], "supports",
                               "+Fresh material observation.", .8) for a in batch]


class ControlledJudge:
    def __init__(self, whole=False): self.whole = whole
    def review_event(self, state, batch, proposals, charge=None):
        return [{**p, "verifier_status": "PASS", "semantic_check": "MODEL_ASSESSED:fixture",
                 "semantic_assessment": {"whole_element_supported": self.whole,
                                         "claim_scope": "whole_element" if self.whole else "material_subclaim"}}
                for p in proposals], []


def test_full_target_resolution_never_suppresses_remaining_source_events(approved_state):
    target = approved_state["central_element_ids"][0]
    fake = ControlledLinker(target)
    run = EventReviewAgent(linker=fake, judge=ControlledJudge(True),
                          budget=Budget(max_rounds=2, max_artifact_reads=2)).run(
                              approved_state, [source(approved_state, "one"), source(approved_state, "two", "b"*40)])
    assert len(fake.calls) == 2 and len(run.report["verified_evidence"]) == 2
    assert run.report["investigation_coverage"]["model_reported_reviewed_artifact_versions"] == 2


def test_partial_support_never_marks_whole_target_resolved(approved_state):
    target = approved_state["central_element_ids"][0]
    run = EventReviewAgent(linker=ControlledLinker(target), judge=ControlledJudge()).run(
        approved_state, [source(approved_state)])
    need = next(n for n in run.memory.needs if n["element_id"] == target)
    assert need["status"] == "PARTIAL_EVIDENCE"
    assert run.report["verification"]["status"] == "UNRESOLVED"


def test_omitted_model_reviews_remain_technical_unreviewed_coverage(approved_state):
    target = approved_state["central_element_ids"][0]
    run = EventReviewAgent(linker=ControlledLinker(target, fail=True), judge=ControlledJudge()).run(
        approved_state, [source(approved_state)])
    assert run.memory.technical_verification_failures and not run.memory.rejected_interpretations
    assert run.report["investigation_coverage"]["not_semantically_reviewed_artifact_ids"] == ["edit"]
    assert not run.report["verified_evidence"]


def test_round_bound_preserves_explicit_unreviewed_artifacts(approved_state):
    target = approved_state["central_element_ids"][0]
    run = EventReviewAgent(linker=ControlledLinker(target), judge=ControlledJudge(),
        budget=Budget(max_rounds=1, max_artifact_reads=2)).run(
            approved_state, [source(approved_state, "one"), source(approved_state, "two", "b"*40)])
    assert run.report["stopping_reason"] == "event_round_limit"
    assert len(run.report["investigation_coverage"]["not_semantically_reviewed_artifact_ids"]) == 1


def test_insufficient_source_review_cannot_be_reported_as_complete(approved_state):
    state = deepcopy(approved_state)
    target = state["central_element_ids"][0]
    state["central_element_ids"] = [target]
    state["original_evidence"] = [{"id": "accepted-evidence", "source": "fixture://accepted",
                                   "text": "Synthetic accepted rationale source."}]
    class UncertainSource(ControlledLinker):
        def propose_event(self, state, batch, charge=None):
            proposals = super().propose_event(state, batch, charge)
            if batch[0]["artifact_id"] == "uncertain":
                self.last_reviews[0]["status"] = "insufficient_evidence"
                return []
            return proposals
    run = EventReviewAgent(linker=UncertainSource(target), judge=ControlledJudge(True),
        budget=Budget(max_rounds=2, max_artifact_reads=2)).run(
            state, [source(state, "supported"), source(state, "uncertain", "b"*40)])
    assert run.report["investigation_coverage"]["unresolved_artifact_review_ids"] == ["uncertain"]
    assert run.report["verification"]["status"] == "UNRESOLVED"
    assert run.report["recommended_outcome"] == "REVALIDATE"
    assert run.report["outcome_probabilities"]["REVALIDATE"] == max(run.report["outcome_probabilities"].values())
    from evorationale.verification import ReportValidator
    assert ReportValidator().validate(state, run.memory.verified_links, run.report)["status"] == "PASS"


def test_budget_gap_outcome_and_probability_vector_remain_consistent(approved_state):
    state = deepcopy(approved_state)
    target = state["central_element_ids"][0]
    state["central_element_ids"] = [target]
    state["original_evidence"] = [{"id": "accepted-evidence", "source": "fixture://accepted",
                                   "text": "Synthetic accepted rationale source."}]
    run = EventReviewAgent(linker=ControlledLinker(target), judge=ControlledJudge(True),
        budget=Budget(max_rounds=1, max_artifact_reads=2)).run(
            state, [source(state, "one"), source(state, "two", "b"*40)])
    from evorationale.verification import ReportValidator
    assert ReportValidator().validate(state, run.memory.verified_links, run.report)["status"] == "PASS"
    assert run.report["recommended_outcome"] == "REVALIDATE"


def test_actual_envelope_is_reserved_before_provider_call(approved_state):
    fake = Replies()
    run = EventReviewAgent(linker=linker(fake), judge=ControlledJudge(),
                          budget=Budget(max_input_tokens=1)).run(approved_state, [source(approved_state)])
    assert fake.calls == []
    assert run.report["stopping_reason"] == "cumulative_input_token_limit"


def test_retry_is_separately_reserved_and_stops_before_second_call(approved_state):
    request = {"model": "fixture", "reasoning": {"effort": "medium"},
               "text": {"format": {"type": "json_schema", "name": "fixture", "strict": True, "schema": {}}},
               "max_output_tokens": 900, "instructions": "fixture", "input": "{}"}
    estimate = Budget.estimate_tokens(request)
    memory = DecisionMemory("fixture", approved_state)
    charge = RequestBudgetTracker(Budget(max_input_tokens=estimate), memory)
    calls = []
    def incomplete(**kwargs):
        calls.append(kwargs)
        return SimpleNamespace(status="incomplete", output_text="", usage={"input_tokens": 23, "output_tokens": 4})
    with pytest.raises(BudgetExhausted):
        request_json_object(client=SimpleNamespace(responses=SimpleNamespace(create=incomplete)),
            model="fixture", name="fixture", schema={}, instructions="fixture", payload={},
            before_request=charge, after_response=charge.record_response)
    assert len(calls) == 1 and len(charge.requests) == 1
    assert charge.summary()["provider_reported_input_tokens"] == 23
    assert memory.token_count == estimate

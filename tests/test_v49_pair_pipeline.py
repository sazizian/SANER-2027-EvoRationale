"""Opt-in pair-review integration, transaction limits and honest coverage.

Fake providers verify dispatch, source handling and request boundaries. These
checks do not measure classifier accuracy or establish semantic truth from a
complete matrix of model-reported artifact-target outcomes.
"""
from copy import deepcopy
import json
from types import SimpleNamespace

import pytest

from evorationale import cli
from evorationale.budget import Budget, BudgetExhausted
from evorationale.delta_context import build_delta_catalog
from evorationale.delta_linking import NoNomination
from evorationale.event_agent import EventReviewAgent, RequestBudgetTracker
from evorationale.event_context import select_event_batches
from evorationale.memory import DecisionMemory
from evorationale.model import artifact_key, element_by_id
from test_v46_evidence_pipeline import DOCUMENTATION, case, configured_args, reply, support


PROFILE = "event-pair-reviewed"


def test_pair_cli_selects_no_nomination_and_independent_pair_judge(monkeypatch, tmp_path):
    from evorationale import delta_linking, pair_review_verification
    seen = []
    monkeypatch.setenv("OPENAI_API_KEY", "synthetic-unused-key")
    monkeypatch.setattr(delta_linking, "DeltaLinker",
                        lambda *args, **kw: pytest.fail("Unexpected hosted nomination"))
    monkeypatch.setattr(pair_review_verification, "PairReviewSemanticJudge",
                        lambda model: seen.append(model) or object())
    agent = cli.build_agent(configured_args(tmp_path, investigation_profile=PROFILE,
                                           max_provider_requests=9, max_output_tokens=700))
    assert seen == ["opaque-independent-classifier"]
    assert agent.profile == PROFILE and isinstance(agent.linker, NoNomination)
    assert agent.max_provider_requests == 9
    assert agent.budget.max_output_tokens == 700


def test_pair_cli_defaults_to_bounded_provider_requests(monkeypatch, tmp_path):
    from evorationale import pair_review_verification
    monkeypatch.setenv("OPENAI_API_KEY", "synthetic-unused-key")
    monkeypatch.setattr(pair_review_verification, "PairReviewSemanticJudge", lambda model: object())
    agent = cli.build_agent(configured_args(tmp_path, investigation_profile=PROFILE,
                                           max_provider_requests=None))
    assert agent.max_provider_requests == 36


@pytest.mark.parametrize("profile", ["event-evidence-repair", "targeted"])
def test_provider_ceiling_is_not_silently_claimed_for_other_profiles(tmp_path, profile):
    with pytest.raises(RuntimeError, match="max-provider-requests requires"):
        cli.build_agent(configured_args(tmp_path, investigation_profile=profile,
                                       max_provider_requests=2))


def test_request_limit_stops_before_tokens_are_reserved_or_provider_called(approved_state):
    memory = DecisionMemory("synthetic-pair-budget", approved_state)
    tracker = RequestBudgetTracker(Budget(max_input_tokens=100000, max_output_tokens=700),
                                   memory, max_provider_requests=1)
    provider_calls = []
    request = {"model": "synthetic-reviewer", "input": "synthetic source", "max_output_tokens": 700}
    tracker(request)
    provider_calls.append(deepcopy(request))
    tracker.record_response(SimpleNamespace(usage={"input_tokens": 5, "output_tokens": 3}))
    charged_tokens = memory.token_count
    with pytest.raises(BudgetExhausted, match="provider_request_limit"):
        tracker(request)
        provider_calls.append(deepcopy(request))
    assert len(provider_calls) == len(tracker.requests) == 1
    assert memory.token_count == charged_tokens
    summary = tracker.summary()
    assert summary["max_provider_requests"] == 1
    assert summary["provider_requests_reserved"] == summary["provider_responses_received"] == 1


def pair_reply(state, catalog, effects=None):
    response = reply(state, catalog, effects)
    for row in response["reviews"]:
        final_relations = {}
        for item in row["links"]:
            relation = "supports" if item["change_kind"] == "documented_support" else "supersedes"
            final_relations.setdefault(item["element_id"], set()).add(relation)
        row["pair_outcomes"] = [
            {"element_id": eid,
             "outcome": "relation_found" if eid in final_relations else "no_relation",
             "reason": "Synthetic pair outcome for mechanical coverage testing only.",
             "relations": sorted(final_relations.get(eid, set()))}
            for eid in element_by_id(state)]
    return response


class PairProvider:
    def __init__(self, first_reply, *, fail_with_retry=False):
        self.first_reply = first_reply
        self.fail_with_retry = fail_with_retry
        self.calls = []

    def create(self, **request):
        self.calls.append(deepcopy(request))
        if self.fail_with_retry:
            return SimpleNamespace(status="incomplete", output_text="")
        if "decisions" in request["text"]["format"]["schema"]["properties"]:
            response = {"decisions": [{"candidate_id": "C0001", "verdict": "confirm",
                "reason": "Controlled independent confirmation for source-only integration.",
                "predicate_reason": "The fixture statement directly names the persistence predicate.",
                "contribution_reason": "The exact added line supplies the current adopted contract.",
                "authority_reason": "The fixture labels the local design as adopted, not deployed."}]}
        else:
            response = self.first_reply
        return SimpleNamespace(status="completed", output_text=json.dumps(response),
                               usage={"input_tokens": 151, "output_tokens": 37, "total_tokens": 188})


def _paired_run(state, batch, provider, *, limit=36):
    from evorationale.pair_review_verification import PairReviewSemanticJudge
    judge = PairReviewSemanticJudge("synthetic-pair-reviewer",
                                   client=SimpleNamespace(responses=provider))
    return EventReviewAgent(linker=NoNomination(), judge=judge, profile=PROFILE,
        max_provider_requests=limit,
        budget=Budget(max_rounds=1, max_artifact_reads=1,
                      max_input_tokens=1000000, max_output_tokens=16384)).run(state, batch)


def test_pair_pipeline_keeps_partial_support_after_independent_confirmation(approved_state):
    state, batch = case(approved_state, DOCUMENTATION)
    state["central_element_ids"] = ["DELTA_TARGET"]
    state["gold_labels"] = {"DELTA_TARGET": "SYNTHETIC_REFERENCE_MUST_NOT_REACH_MODEL"}
    state["evaluation_metadata"] = "SYNTHETIC_REFERENCE_MUST_NOT_REACH_MODEL"
    catalog = build_delta_catalog(state, batch)
    provider = PairProvider(pair_reply(state, catalog, {"A0001": [support(state, catalog)]}))
    run = _paired_run(state, batch, provider)
    assert len(provider.calls) == 2 and len(run.memory.verified_links) == 1
    assert all("SYNTHETIC_REFERENCE_MUST_NOT_REACH_MODEL" not in request["input"]
               for request in provider.calls)
    link = run.memory.verified_links[0]
    assert link["quote"] in batch[0]["content"] and link["relation"] == "supports"
    assert link["semantic_assessment"]["whole_element_supported"] is False
    assert link["semantic_assessment"]["deployed_behavior_verified"] is False
    assert link["semantic_assessment"]["pair_review_confirmation"]["verdict"] == "confirm"
    need = next(n for n in run.memory.needs if n["element_id"] == "DELTA_TARGET")
    assert need["status"] == "PARTIAL_EVIDENCE"
    assert run.report["nomination_mode"] == "none"
    assert run.report["verification"]["status"] == "UNRESOLVED"
    coverage = run.report["investigation_coverage"]["pair_review_coverage"]
    assert coverage["expected_selected_pairs"] == coverage["recorded_pairs"] == len(element_by_id(state))
    assert coverage["complete_artifact_reviews"] == 1 and coverage["incomplete_artifact_ids"] == []
    assert coverage["epistemic_status"] == "MODEL_ASSESSED"
    assert "semantic correctness" in coverage["note"]
    assert run.report["budget_usage"]["provider_requests_reserved"] == 2


@pytest.mark.parametrize("fail_with_retry", [False, True], ids=["critic", "classifier-retry"])
def test_pair_pipeline_request_limit_preserves_unconfirmed_evidence(approved_state, fail_with_retry):
    state, batch = case(approved_state, DOCUMENTATION)
    catalog = build_delta_catalog(state, batch)
    provider = PairProvider(pair_reply(state, catalog, {"A0001": [support(state, catalog)]}),
                            fail_with_retry=fail_with_retry)
    run = _paired_run(state, batch, provider, limit=1)
    assert len(provider.calls) == 1
    assert not run.memory.verified_links
    assert run.report["budget_usage"]["provider_requests_reserved"] == 1
    assert run.report["verification"]["status"] == "UNRESOLVED"
    assert run.report["stopping_reason"] == "provider_request_limit"


class CoverageJudge:
    def __init__(self, state, batch, *, missing=False):
        ids = list(element_by_id(state))
        selected = ids[:-1] if missing else ids
        self.last_reviews = [{"artifact_id": batch[0]["artifact_id"],
            "artifact_key": artifact_key(batch[0]), "considered_element_ids": ids,
            "status": "no_material_relation", "context_complete": True,
            "citation_coverage_complete": True,
            "explicit_pair_outcomes": [{"element_id": eid, "outcome": "no_relation",
                "reason": "Controlled structural record, not validated semantic truth.", "relations": []}
                for eid in selected],
            "pair_outcomes_complete": not missing,
            "pair_review_missing_element_ids": ids[-1:] if missing else []}]

    def review_event(self, state, batch, proposals, *, charge=None):
        return [], []


@pytest.mark.parametrize("missing", [False, True], ids=["complete", "missing-pair"])
def test_pair_review_coverage_is_structural_and_retains_missing_pairs(approved_state, missing):
    state, batch = case(approved_state, DOCUMENTATION)
    run = EventReviewAgent(linker=NoNomination(),
        judge=CoverageJudge(state, batch, missing=missing), profile=PROFILE,
        budget=Budget(max_rounds=1, max_artifact_reads=1, max_input_tokens=100000,
                      max_output_tokens=16384)).run(state, batch)
    coverage = run.report["investigation_coverage"]["pair_review_coverage"]
    assert coverage["expected_selected_pairs"] == len(element_by_id(state))
    assert coverage["recorded_pairs"] == (0 if missing else len(element_by_id(state)))
    assert coverage["complete_artifact_reviews"] == int(not missing)
    assert coverage["incomplete_artifact_ids"] == ([batch[0]["artifact_id"]] if missing else [])
    assert coverage["epistemic_status"] == "MODEL_ASSESSED"
    assert "structural" in coverage["note"].lower() and "semantic correctness" in coverage["note"]
    assert not run.memory.verified_links
    assert run.report["verification"]["status"] == "UNRESOLVED"


def test_pair_report_counts_selected_artifacts_not_reached_before_round_limit(approved_state):
    state, history = case(approved_state, DOCUMENTATION)
    history[0].update(source_commit_sha="a" * 40, source_file="synthetic-orders.md")
    second = deepcopy(history[0])
    second.update(artifact_id="synthetic-second-event", source_commit_sha="b" * 40)
    history.append(second)
    selected = select_event_batches(state, history, 2)
    assert len(selected) == 2
    run = EventReviewAgent(linker=NoNomination(),
        judge=CoverageJudge(state, selected[0]), profile=PROFILE,
        budget=Budget(max_rounds=1, max_artifact_reads=2, max_input_tokens=100000,
                      max_output_tokens=16384)).run(state, history)
    coverage = run.report["investigation_coverage"]["pair_review_coverage"]
    assert coverage["expected_selected_pairs"] == 2 * len(element_by_id(state))
    assert coverage["expected_reviewed_pairs"] == coverage["recorded_pairs"] == len(element_by_id(state))
    assert coverage["incomplete_artifact_ids"] == [selected[1][0]["artifact_id"]]
    assert run.report["stopping_reason"] == "event_round_limit"
    assert run.report["verification"]["status"] == "UNRESOLVED"


@pytest.mark.parametrize("change", [
    lambda row: row["explicit_pair_outcomes"][0].update(outcome="INVALID_OUTCOME"),
    lambda row: row["explicit_pair_outcomes"][0].update(outcome="relation_found", relations=[]),
    lambda row: row["explicit_pair_outcomes"][0].update(relations=["supports"]),
    lambda row: row.update(artifact_key="synthetic-unknown-source-version"),
], ids=["invalid-outcome", "positive-without-relation", "negative-with-relation", "unknown-source"])
def test_malformed_pair_metadata_cannot_certify_complete_artifact_grid(approved_state, change):
    state, batch = case(approved_state, DOCUMENTATION)
    judge = CoverageJudge(state, batch)
    change(judge.last_reviews[0])
    run = EventReviewAgent(linker=NoNomination(), judge=judge, profile=PROFILE,
        budget=Budget(max_rounds=1, max_artifact_reads=1, max_input_tokens=100000,
                      max_output_tokens=16384)).run(state, batch)
    coverage = run.report["investigation_coverage"]["pair_review_coverage"]
    assert coverage["recorded_pairs"] == coverage["complete_artifact_reviews"] == 0
    assert coverage["incomplete_artifact_ids"] == [batch[0]["artifact_id"]]
    assert run.report["verification"]["investigation_complete"] is False

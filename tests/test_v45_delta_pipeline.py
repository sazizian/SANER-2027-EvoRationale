"""Pipeline checks with controlled semantic classifications; no hosted calls.

These exercise recovery, independent coverage, and honest uncertainty, not
the linguistic accuracy of a model's architectural judgment.
"""
from types import SimpleNamespace

import pytest

from evorationale import cli
from evorationale.budget import Budget
from evorationale.event_agent import EventReviewAgent
from evorationale.linking import candidate_link
from evorationale.model import artifact_key, element_by_id
from evorationale.structured_json import StructuredModelResponseError
from test_v44_event_pipeline import source


class EmptyNominator:
    def propose_event(self, state, batch, charge=None):
        self.last_reviews = [{"artifact_key": artifact_key(a), "artifact_id": a["artifact_id"],
                              "considered_element_ids": list(element_by_id(state)),
                              "status": "no_material_relation", "reason": "No nominated element.",
                              "candidate_links": 0, "context_complete": True,
                              "citation_coverage_complete": True} for a in batch]
        return []


class IndependentClassifier:
    def __init__(self, target, technical=False):
        self.target, self.technical, self.calls = target, technical, []
        self.last_reviews = []

    def review_event(self, state, batch, nominees, charge=None):
        self.calls.append((batch, nominees))
        if self.technical:
            self.last_reviews = []
            return [], [{"element_id": None, "artifact_keys": [artifact_key(a) for a in batch],
                         "reasons": ["semantic_judge_error:fixture_contract_failure"]}]
        self.last_reviews = [{"artifact_key": artifact_key(a), "artifact_id": a["artifact_id"],
                              "considered_element_ids": list(element_by_id(state)),
                              "status": "relation_found", "reason": "Controlled independent review.",
                              "candidate_links": 1, "context_complete": True,
                              "citation_coverage_complete": True} for a in batch]
        return [{**candidate_link(a, element_by_id(state)[self.target], "supersedes",
                                  "+Fresh material observation.", .8),
                 "verifier_status": "PASS", "semantic_check": "MODEL_ASSESSED:controlled replacement",
                 "semantic_assessment": {"claim_scope": "material_subclaim",
                                         "whole_element_supported": False,
                                         "proposal_origin": "independent_recovery"}} for a in batch], []


def test_independent_classification_recovers_links_after_empty_nominations(approved_state):
    target = approved_state["central_element_ids"][0]
    judge = IndependentClassifier(target)
    run = EventReviewAgent(linker=EmptyNominator(), judge=judge, profile="event-delta",
                          budget=Budget(max_rounds=2, max_artifact_reads=2)).run(
        approved_state, [source(approved_state, "one"), source(approved_state, "two", "b" * 40)])
    assert len(judge.calls) == 2 and all(nominees == [] for _, nominees in judge.calls)
    assert len(run.memory.verified_links) == 2
    assert run.report["investigation_profile"] == "event-delta"
    assert run.report["investigation_coverage"]["model_reported_reviewed_artifact_versions"] == 2
    assert len(run.report["investigation_coverage"]["nomination_review_records"]) == 2
    assert sum(t["recovered_links_added"] for t in run.memory.trace) == 2
    assert all(t["nomination_only"] for t in run.memory.trace)
    need = next(n for n in run.memory.needs if n["element_id"] == target)
    assert need["status"] == "ADVERSE_EVIDENCE"
    # The fixture does not answer the other required needs or supply the
    # original rationale, so a recovered relation cannot imply a complete run.
    assert run.report["verification"]["status"] == "UNRESOLVED"


def test_failed_independent_review_does_not_inherit_nomination_coverage(approved_state):
    target = approved_state["central_element_ids"][0]
    run = EventReviewAgent(linker=EmptyNominator(), judge=IndependentClassifier(target, technical=True),
                          profile="event-delta").run(approved_state, [source(approved_state)])
    coverage = run.report["investigation_coverage"]
    assert coverage["model_reported_reviewed_artifact_versions"] == 0
    assert coverage["not_semantically_reviewed_artifact_ids"] == ["edit"]
    assert coverage["nomination_review_records"]
    assert run.memory.technical_verification_failures
    assert not run.memory.rejected_interpretations
    assert run.report["recommended_outcome"] == "REVALIDATE"


def test_unknown_event_profile_is_rejected():
    with pytest.raises(ValueError, match="Unknown event review profile"):
        EventReviewAgent(linker=None, judge=None, profile="invented")


def test_delta_profile_cli_dispatch_preserves_model_ids_and_budget(monkeypatch, tmp_path):
    from evorationale import delta_linking, delta_verification
    seen = []
    monkeypatch.setenv("OPENAI_API_KEY", "synthetic-unused-key")
    monkeypatch.setattr(delta_linking, "DeltaLinker", lambda model: seen.append(("nominator", model)) or object())
    monkeypatch.setattr(delta_verification, "DeltaSemanticJudge", lambda model: seen.append(("judge", model)) or object())
    args = SimpleNamespace(investigation_profile="event-delta", max_output_tokens=700,
                           delta_nomination="model",
                           max_rounds=6, max_queries=12, max_reads=36, max_input_tokens=100000,
                           mode="api", backend="local", allow_repository_text_to_api=True,
                           model="opaque-strong-proposer", judge_model="opaque-independent-judge",
                           memory="file", memory_dir=tmp_path, alloy_jar="")
    agent = cli.build_agent(args)
    assert seen == [("nominator", "opaque-strong-proposer"), ("judge", "opaque-independent-judge")]
    assert agent.profile == "event-delta" and agent.budget.max_output_tokens == 700


def test_default_delta_profile_skips_unused_provider_nomination(monkeypatch, tmp_path):
    from evorationale import delta_linking, delta_verification
    from evorationale.delta_linking import NoNomination
    monkeypatch.setenv("OPENAI_API_KEY", "synthetic-unused-key")
    monkeypatch.setattr(delta_linking, "DeltaLinker", lambda *args, **kwargs: pytest.fail("Nomination model constructed"))
    monkeypatch.setattr(delta_verification, "DeltaSemanticJudge", lambda model: object())
    args = SimpleNamespace(investigation_profile="event-delta", max_output_tokens=None,
                           max_rounds=6, max_queries=12, max_reads=36, max_input_tokens=100000,
                           mode="api", backend="local", allow_repository_text_to_api=True,
                           model="parent-linker", judge_model="parent-linker", memory="file",
                           memory_dir=tmp_path, alloy_jar="")
    agent = cli.build_agent(args)
    assert isinstance(agent.linker, NoNomination)
    assert agent.linker.propose_event({}, []) == [] and agent.linker.last_reviews == []


def test_optional_nomination_contract_failure_does_not_suppress_classifier(approved_state):
    class BrokenNominator:
        nomination_mode = "model"
        last_proposal_rejections = []
        def propose_event(self, *args, **kwargs):
            raise StructuredModelResponseError("incomplete_delta_artifact_reviews")
    target = approved_state["central_element_ids"][0]
    judge = IndependentClassifier(target)
    run = EventReviewAgent(linker=BrokenNominator(), judge=judge, profile="event-delta").run(
        approved_state, [source(approved_state)])
    assert len(judge.calls) == 1 and judge.calls[0][1] == []
    assert len(run.memory.verified_links) == 1
    assert run.report["investigation_coverage"]["model_reported_reviewed_artifact_versions"] == 1
    assert run.report["nomination_mode"] == "model"
    assert run.memory.technical_verification_failures and not run.memory.rejected_interpretations
    assert run.report["verification"]["status"] == "UNRESOLVED"
    assert run.memory.trace[0]["nomination_failures"]


def test_model_nomination_is_rejected_outside_delta_profile():
    with pytest.raises(RuntimeError, match="requires the event-delta profile"):
        cli.build_agent(SimpleNamespace(investigation_profile="event-complete", delta_nomination="model"))

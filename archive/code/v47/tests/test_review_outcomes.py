"""Outcome consistency on verified changes outside the central rationale."""
from copy import deepcopy

import pytest

from evorationale.analysis import ActionPlanner
from evorationale.linking import candidate_link
from evorationale.model import element_by_id
from evorationale.verification import ReportValidator


@pytest.mark.parametrize("relation", ["weakens", "contradicts", "supersedes"])
def test_noncentral_adverse_change_revises_scope_and_validates(approved_state, history, relation):
    state = deepcopy(approved_state)
    elements = element_by_id(state)
    target = next(e for e in elements if e not in state["central_element_ids"])
    source = next(a for a in history if a["artifact_id"] == "inc-017")
    # Input represents the downstream planner's already verified evidence;
    # this fixture does not assert a semantic source relation.
    evidence = [candidate_link(source, elements[target], relation, source["content"], .8)]
    report = ActionPlanner().compose(state, evidence, [])
    assert report["recommended_outcome"] == "REVISE"
    assert report["outcome_probabilities"]["REVISE"] == max(report["outcome_probabilities"].values())
    assert ReportValidator().validate(state, evidence, report)["status"] == "PASS"


def test_noncentral_adverse_with_unknown_central_need_keeps_revalidation(approved_state, history):
    state = deepcopy(approved_state)
    elements = element_by_id(state)
    target = next(e for e in elements if e not in state["central_element_ids"])
    source = next(a for a in history if a["artifact_id"] == "inc-017")
    evidence = [candidate_link(source, elements[target], "weakens", source["content"], .8)]
    report = ActionPlanner().compose(state, evidence, [{"question": "Resolve the original central claim."}])
    assert report["recommended_outcome"] == "REVALIDATE"
    assert ReportValidator().validate(state, evidence, report)["status"] == "PASS"

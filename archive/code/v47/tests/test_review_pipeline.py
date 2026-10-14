"""Pipeline regressions from review; synthetic transports and sources, no API."""
from copy import deepcopy
import json
from types import SimpleNamespace

import pytest

from evorationale.event_agent import EventReviewAgent
from evorationale.event_context import quotable_event_passages, redact_event_source, select_event_batches
from evorationale.event_linking import EventLinker
from evorationale.linking import candidate_link
from evorationale.model import artifact_key, element_by_id, normalize_artifact
from evorationale.structured_json import StructuredModelResponseError
from evorationale.verification import ReportValidator


def source(state, name="change", content=None):
    return normalize_artifact({
        "artifact_id": name, "repository": state["repository"],
        "source_type": "git_commit_diff_hunk", "source_location": "fixture://source",
        "source_commit_sha": "a" * 40, "source_file": "design.md",
        "title": "Design change", "timestamp": "2024-02-01T00:00:00Z",
        "content": content or "@@ -1 +1 @@\n-Previous mechanism.\n+Replacement mechanism.\n",
    })


class Replies:
    def __init__(self, corrupt=None):
        self.requests = []
        self.corrupt = corrupt

    def create(self, **request):
        self.requests.append(request)
        payload = json.loads(request["input"])
        ids = [e["id"] for e in payload["decision_state"]["elements"]]
        result = {"reviews": [{
            "artifact_handle": a["artifact_handle"], "considered_element_ids": ids,
            "status": "no_material_relation", "reason": "Synthetic no-effect response.", "links": [],
        } for a in payload["artifacts"]]}
        if self.corrupt:
            self.corrupt(result, payload)
        return SimpleNamespace(status="completed", output_text=json.dumps(result))


class UnusedJudge:
    def review_event(self, state, batch, proposals, charge=None):
        assert not proposals
        return [], []


def test_safe_changed_lines_survive_sensitive_neighboring_context(approved_state):
    patch = ("@@ -1,2 +1,2 @@\n-Previous mechanism.\n+Replacement mechanism.\n"
             " Contact engineer@example.com\n")
    artifact = source(approved_state, content=patch)
    quotes, omitted = quotable_event_passages(artifact)
    assert omitted == 1
    assert quotes == ["-Previous mechanism.\n+Replacement mechanism."]
    assert all(q in patch for q in quotes)
    transport = Replies()
    linker = EventLinker("fixture", client=SimpleNamespace(responses=transport))
    linker.propose_event(approved_state, select_event_batches(approved_state, [artifact], 1)[0])
    payload = json.loads(transport.requests[0]["input"])
    assert "engineer@example.com" not in transport.requests[0]["input"]
    catalog = payload["artifacts"][0]
    assert catalog["citation_coverage_complete"]
    assert len(catalog["passages"]) == 1
    assert catalog["passages"][0]["source_line_start"] == 2
    assert catalog["passages"][0]["source_line_end"] == 3
    assert linker.last_reviews[0]["citation_coverage_complete"]


def test_sensitive_changes_do_not_gain_context_only_citation_or_complete_verdict(approved_state):
    patch = ("@@ -1,2 +1,2 @@\n-Contact old@example.com\n+Contact new@example.com\n"
             " Unchanged safe statement.\n")
    artifact = source(approved_state, content=patch)
    quotes, omitted = quotable_event_passages(artifact)
    assert omitted == 1 and not quotes
    transport = Replies()
    run = EventReviewAgent(
        linker=EventLinker("fixture", client=SimpleNamespace(responses=transport)),
        judge=UnusedJudge(),
    ).run(approved_state, [artifact])
    coverage = run.report["investigation_coverage"]
    assert coverage["artifact_review_records"][0]["citation_coverage_complete"] is False
    assert coverage["unresolved_artifact_review_ids"] == [artifact["artifact_id"]]
    assert not run.report["verification"]["investigation_complete"]


def test_cross_line_credential_match_excludes_its_continuation(approved_state):
    patch = ("@@ -1,3 +1,3 @@\n-Previous mechanism.\n+Replacement mechanism.\n"
             " secret =\n next-value\n")
    quotes, omitted = quotable_event_passages(source(approved_state, content=patch))
    assert omitted == 1
    assert quotes == ["-Previous mechanism.\n+Replacement mechanism."]
    assert not any("next-value" in q or "secret" in q for q in quotes)


@pytest.mark.parametrize("newline", ["\n", "\r\n"])
def test_multiline_redaction_preserves_later_exact_citation_line_ranges(approved_state, newline):
    patch = newline.join(["@@ -1,3 +1,3 @@", " secret =", " next-value",
                          "-Previous mechanism.", "+Replacement mechanism.", ""])
    artifact = source(approved_state, content=patch)
    transport = Replies()
    linker = EventLinker("fixture", client=SimpleNamespace(responses=transport))
    linker.propose_event(approved_state, select_event_batches(approved_state, [artifact], 1)[0])
    payload = json.loads(transport.requests[0]["input"])
    entry = payload["event_context"]["canonical_artifacts"][0]
    catalog = payload["artifacts"][0]["passages"]
    assert "next-value" not in entry["numbered_source"]
    assert len(entry["numbered_source"].splitlines()) == len(patch.splitlines())
    assert "4: -Previous mechanism." in entry["numbered_source"]
    assert "5: +Replacement mechanism." in entry["numbered_source"]
    assert any(p["source_line_start"] == 4 and p["source_line_end"] == 5 for p in catalog)
    assert redact_event_source(patch).count(newline) == patch.count(newline)


def test_malformed_second_row_does_not_publish_partial_review_and_keeps_contract_audit(approved_state):
    batch = select_event_batches(approved_state,
                                 [source(approved_state, "one"), source(approved_state, "two")], 2)[0]

    def corrupt(result, payload):
        result["reviews"][1]["considered_element_ids"] = []

    linker = EventLinker("fixture", client=SimpleNamespace(responses=Replies(corrupt)))
    with pytest.raises(StructuredModelResponseError, match="invalid_artifact_review_coverage"):
        linker.propose_event(approved_state, batch)
    assert linker.last_reviews == []
    assert linker.last_proposal_rejections[0]["artifact_key"] == artifact_key(batch[1])
    assert linker.last_proposal_rejections[0]["stage"] == "linker_contract"


def test_linker_contract_failure_reaches_technical_checkpoint_feedback(approved_state):
    def corrupt(result, payload):
        result["extra"] = "Do not retain malformed model output."

    run = EventReviewAgent(
        linker=EventLinker("fixture", client=SimpleNamespace(responses=Replies(corrupt))),
        judge=UnusedJudge(),
    ).run(approved_state, [source(approved_state)])
    failures = [f for f in run.memory.verifier_feedback if f.get("stage") == "linker_contract"]
    assert failures[0]["reasons"] == ["semantic_judge_error:invalid_event_linker_response_fields"]
    assert failures[0] in run.memory.technical_verification_failures
    assert not run.memory.rejected_interpretations
    assert run.report["investigation_coverage"]["model_reported_reviewed_artifact_versions"] == 0
    assert "Do not retain malformed model output" not in json.dumps(run.memory.asdict())


class EvidenceLinker:
    def __init__(self, claims):
        self.claims = claims
        self.last_reviews = []

    def propose_event(self, state, batch, charge=None):
        self.last_reviews = [{
            "artifact_key": artifact_key(a), "artifact_id": a["artifact_id"],
            "considered_element_ids": list(element_by_id(state)), "status": "relation_found",
            "context_complete": True, "citation_coverage_complete": True,
        } for a in batch]
        return [candidate_link(batch[0], element_by_id(state)[target], relation,
                               "+Replacement mechanism.", .8)
                for target, relation in self.claims]


class EvidenceJudge:
    def review_event(self, state, batch, proposals, charge=None):
        return [{**p, "verifier_status": "PASS", "semantic_check": "MODEL_ASSESSED:fixture",
                 "semantic_assessment": {
                     "whole_element_supported": p["relation"] == "supports",
                     "claim_scope": "whole_element" if p["relation"] == "supports" else "material_subclaim",
                 }} for p in proposals], []


@pytest.mark.parametrize("claims, expected", [
    ([("A1", "weakens"), ("E1", "supports")], "REVISE"),
    ([("A1", "contradicts"), ("E1", "supersedes")], "REOPEN"),
    ([("A1", "contradicts"), ("A1", "supports"), ("E1", "supports")], "REVALIDATE"),
    ([("A1", "weakens")], "REVALIDATE"),
])
def test_answered_adverse_needs_allow_revision_but_conflicts_and_gaps_require_revalidation(
        approved_state, claims, expected):
    state = deepcopy(approved_state)
    run = EventReviewAgent(linker=EvidenceLinker(claims), judge=EvidenceJudge()).run(
        state, [source(state)])
    assert run.report["recommended_outcome"] == expected
    assert run.report["outcome_probabilities"][expected] == max(run.report["outcome_probabilities"].values())
    assert ReportValidator().validate(state, run.memory.verified_links, run.report)["status"] == "PASS"
    need = next(n for n in run.memory.needs if n["element_id"] == "A1")
    assert need["status"] == ("CONFLICTING_EVIDENCE" if len(claims) == 3 else "ADVERSE_EVIDENCE")
    assert not any(n["element_id"] == "A1" for n in run.memory.needs
                   if n["required"] and n["status"] in {"OPEN", "PARTIAL_EVIDENCE"})
    assert run.report["verification"]["investigation_complete"] is (expected != "REVALIDATE")

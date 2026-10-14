"""Generic synthetic regressions; no KEP identifiers or human gold labels.

Model replies are controlled to test the runtime contract, not model accuracy.
"""
from copy import deepcopy
import json
from types import SimpleNamespace

import pytest

from evorationale.diff_context import canonical_diff_context, quote_line_roles, removed_only_quote
from evorationale.linking import OpenAILinker, candidate_link
from evorationale.model import element_by_id, normalize_artifact
from evorationale.verification import EvidenceVerifier, OpenAISemanticJudge


PATCH = ("@@ -1 +1 @@\n"
         "-ServiceStatus reports reserved and applied resource budgets.\n"
         "+ServiceStatus reports applied resource budgets.\n")
NEW_QUOTE = "+ServiceStatus reports applied resource budgets."


class Replies:
    def __init__(self, reply):
        self.reply = reply
        self.calls = []

    def create(self, **kwargs):
        self.calls.append(kwargs)
        return SimpleNamespace(status="completed", output_text=json.dumps(self.reply))


def assessment(**overrides):
    return {"supported": True, "reason": "A source-backed assessment.",
            "whole_element_supported": True, "scope_match": True,
            "replacement_is_explicit": True, "affected_subclaim": "Public reporting of reserved budgets.",
            **overrides}


def case(state, content=PATCH, field="implementation_scope"):
    state = deepcopy(state)
    state[field].append({"id": "SYNTHETIC_TARGET", "source": "fixture://state",
                         "text": "Publish reserved and applied resource budgets in ServiceStatus."})
    element = element_by_id(state)["SYNTHETIC_TARGET"]
    artifact = normalize_artifact({
        "artifact_id": "synthetic-change", "repository": state["repository"],
        "source_type": "git_commit_diff_hunk", "source_location": "fixture://change",
        "title": "Synthetic resource status edit", "timestamp": "2024-02-01T00:00:00Z",
        "content": content,
    })
    return state, element, artifact


def test_before_after_preserve_unchanged_text_and_qualifiers(approved_state):
    patch = ("@@ -1,3 +1,4 @@\n"
             "-ServiceStatus reports reserved and applied resource budgets.\n"
             "+ServiceStatus reports applied resource budgets.\n"
             " Settings declare desired budgets.\n"
             "+The node checkpoints reserved budgets locally in the preview phase.\n"
             " Changes require authorization.\n")
    _, _, artifact = case(approved_state, patch)
    context = canonical_diff_context(artifact)
    assert context["complete"]
    old, new = context["hunks"][0]["before_text"], context["hunks"][0]["after_text"]
    assert "reserved and applied" in old and "reserved and applied" not in new
    assert "preview phase" in new and "preview phase" not in old
    assert "Changes require authorization." in old and "Changes require authorization." in new
    assert context["canonical_content_sha256"] == artifact["content_sha256"]


def test_markdown_bullets_are_not_misread_as_unified_diff(approved_state):
    _, _, artifact = case(approved_state, "- Resources remain reserved.\n+ Resources are applied.")
    assert canonical_diff_context(artifact) is None
    assert not removed_only_quote(artifact, "- Resources remain reserved.")


def test_multiple_hunks_keep_separate_comparisons(approved_state):
    patch = PATCH + "@@ -20 +20 @@\n-Logging is verbose.\n+Logging is compact.\n"
    _, _, artifact = case(approved_state, patch)
    context = canonical_diff_context(artifact)
    assert context["complete"] and len(context["hunks"]) == 2
    assert "Logging" not in context["hunks"][0]["after_text"]


def test_truncated_hunk_is_not_claimed_complete(approved_state):
    _, _, artifact = case(approved_state, PATCH.replace("@@ -1 +1 @@", "@@ -1,10 +1,10 @@"))
    context = canonical_diff_context(artifact)
    assert not context["complete"] and not context["hunks"]
    assert context["incomplete_reason"] == "diff_hunk_line_counts_mismatch"


def test_bounded_context_is_explicitly_incomplete(approved_state):
    _, _, artifact = case(approved_state)
    context = canonical_diff_context(artifact, max_chars=20)
    assert not context["complete"] and not context["hunks"]


def test_context_redacts_credentials_and_urls(approved_state):
    patch = "@@ -1 +1 @@\n-password: fixture-secret-value\n+Docs are at https://fixture.invalid/private\n"
    _, _, artifact = case(approved_state, patch)
    context = canonical_diff_context(artifact)
    serialized = json.dumps(context)
    assert context["complete"] and context["redacted"]
    assert "fixture-secret-value" not in serialized and "https://fixture.invalid" not in serialized


def test_ambiguous_identical_quote_is_not_assumed_deleted(approved_state):
    patch = "@@ -1 +1 @@\n-Resources remain reserved.\n+Resources remain reserved.\n"
    _, _, artifact = case(approved_state, patch)
    assert quote_line_roles(artifact, "Resources remain reserved.") == ["added", "removed"]
    assert not removed_only_quote(artifact, "Resources remain reserved.")


def test_deleted_only_support_is_rejected_without_model_call(approved_state):
    state, element, artifact = case(approved_state)
    quote = "-ServiceStatus reports reserved and applied resource budgets."
    fake = Replies(assessment())
    judge = OpenAISemanticJudge("mock", client=SimpleNamespace(responses=fake))
    link = candidate_link(artifact, element, "supports", quote, 0.9)
    accepted, rejected = EvidenceVerifier(judge).verify(state, [artifact], [link])
    assert not accepted and not fake.calls
    assert "removed_text_is_not_current_support" in rejected[0]["reasons"]
    assert rejected[0]["quote"] == quote and rejected[0]["relation"] == "supports"


def test_partial_support_cannot_pass_on_a_positive_model_vote(approved_state):
    state, element, artifact = case(approved_state)
    fake = Replies(assessment(whole_element_supported=False,
                              reason="Applied budgets remain; reserved reporting was removed."))
    judge = OpenAISemanticJudge("mock", client=SimpleNamespace(responses=fake))
    link = candidate_link(artifact, element, "supports", NEW_QUOTE, 0.9)
    accepted, rejected = EvidenceVerifier(judge).verify(state, [artifact], [link])
    assert not accepted and "partial_element_support" in rejected[0]["reasons"][0]
    payload = json.loads(fake.calls[0]["input"])
    assert payload["state_element"]["element_type"] == "implementation_scope"
    assert "reserved and applied" in payload["diff_context"]["hunks"][0]["before_text"]
    assert "reserved and applied" not in payload["diff_context"]["hunks"][0]["after_text"]
    assert rejected[0]["semantic_assessment"]["whole_element_supported"] is False


def test_requirement_scope_mismatch_is_rejected(approved_state):
    state, element, artifact = case(approved_state, field="requirements")
    fake = Replies(assessment(scope_match=False, reason="An API representation changed; the requirement did not."))
    judge = OpenAISemanticJudge("mock", client=SimpleNamespace(responses=fake))
    link = candidate_link(artifact, element, "weakens", artifact["content"].strip(), 0.9)
    accepted, rejected = EvidenceVerifier(judge).verify(state, [artifact], [link])
    assert not accepted and "target_scope_mismatch" in rejected[0]["reasons"][0]
    assert json.loads(fake.calls[0]["input"])["state_element"]["element_type"] == "requirements"


def test_superseding_relation_requires_explicit_replacement(approved_state):
    state, element, artifact = case(approved_state)
    fake = Replies(assessment(replacement_is_explicit=False))
    judge = OpenAISemanticJudge("mock", client=SimpleNamespace(responses=fake))
    link = candidate_link(artifact, element, "supersedes", artifact["content"].strip(), 0.9)
    accepted, rejected = EvidenceVerifier(judge).verify(state, [artifact], [link])
    assert not accepted and "replacement_not_established" in rejected[0]["reasons"][0]


def test_qualified_partial_replacement_records_scope_and_complete_reason(approved_state):
    state, element, artifact = case(approved_state)
    reason = "The public reserved-budget report is replaced, while applied-budget reporting remains. " * 5
    fake = Replies(assessment(whole_element_supported=False, reason=reason))
    judge = OpenAISemanticJudge("mock", client=SimpleNamespace(responses=fake))
    link = candidate_link(artifact, element, "supersedes", artifact["content"].strip(), 0.9)
    accepted, rejected = EvidenceVerifier(judge).verify(state, [artifact], [link])
    assert accepted and not rejected
    assert accepted[0]["semantic_check"] == "MODEL_ASSESSED:" + reason
    assert accepted[0]["semantic_assessment"]["affected_subclaim"]
    assert accepted[0]["semantic_assessment"]["canonical_content_sha256"] == artifact["content_sha256"]


@pytest.mark.parametrize("overrides", [
    {"supported": "true"}, {"whole_element_supported": "true"},
    {"scope_match": 1}, {"replacement_is_explicit": "true"},
    {"reason": None}, {"affected_subclaim": []},
])
def test_invalid_judge_contract_is_a_technical_failure(approved_state, overrides):
    state, element, artifact = case(approved_state)
    fake = Replies(assessment(**overrides))
    judge = OpenAISemanticJudge("mock", client=SimpleNamespace(responses=fake))
    link = candidate_link(artifact, element, "supports", NEW_QUOTE, 0.9)
    accepted, rejected = EvidenceVerifier(judge).verify(state, [artifact], [link])
    assert not accepted and "semantic_judge_error:invalid_diff_judge_fields" in rejected[0]["reasons"]


def test_incomplete_diff_fails_before_paid_judgment(approved_state):
    state, element, artifact = case(approved_state, PATCH.replace("@@ -1 +1 @@", "@@ -1,10 +1,10 @@"))
    fake = Replies(assessment())
    judge = OpenAISemanticJudge("mock", client=SimpleNamespace(responses=fake))
    link = candidate_link(artifact, element, "supports", NEW_QUOTE, 0.9)
    accepted, rejected = EvidenceVerifier(judge).verify(state, [artifact], [link])
    assert not accepted and not fake.calls
    assert "diff_hunk_line_counts_mismatch" in rejected[0]["reasons"]


def test_linker_sends_new_local_state_even_if_quote_ranking_omits_it(approved_state):
    patch = ("@@ -1,2 +1,3 @@\n"
             "-ServiceStatus reports reserved and applied resource budgets.\n"
             "+ServiceStatus reports applied resource budgets.\n"
             "+The node checkpoints reserved resource budgets locally.\n"
             " Configuration controls desired resource budgets.\n")
    state, element, artifact = case(approved_state, patch)
    fake = Replies({"links": []})
    linker = OpenAILinker("mock", client=SimpleNamespace(responses=fake))
    assert linker.propose(state, [artifact], {"id": "q", "element_id": element["id"], "query": "resource budgets"}) == []
    payload = json.loads(fake.calls[0]["input"])
    sent = payload["artifacts"][0]
    assert "checkpoints" in sent["diff_context"]["hunks"][0]["after_text"]
    assert sent["diff_context"]["complete"]
    assert {"added", "removed"} <= set(sent["passages"][0]["line_roles"])
    assert all(p["text"] in artifact["content"] and len(p["text"]) <= 650 for p in sent["passages"])

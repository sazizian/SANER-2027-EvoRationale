"""Synthetic source-selection regressions; no benchmark IDs or gold labels."""
from copy import deepcopy
import hashlib
import json

import pytest

from evorationale.event_context import (
    event_context_view, exact_event_passages, select_event_batches,
)
from evorationale.model import artifact_key, normalize_artifact, validate_state


PATCH = "@@ -1 +1 @@\n-Status publishes reserved budgets.\n+Status publishes applied budgets.\n"
COMMIT = "a" * 40


@pytest.fixture
def synthetic_state():
    return validate_state({
        "episode_id": "synthetic-episode", "decision_id": "synthetic-decision",
        "decision": "Keep resource status auditable", "repository": "fixture/project",
        "accepted_at": "2024-01-01T00:00:00Z", "cutoff_at": "2025-01-01T00:00:00Z",
        "human_approved": True, "central_element_ids": ["PRIMARY"],
        "goals": [{"id": "PRIMARY", "text": "Preserve latency targets.",
                   "source": "fixture://state"}],
        "implementation_scope": [{"id": "SECONDARY", "text": "Publish resource budgets in Status.",
                                  "source": "fixture://state"}],
    })


def source(artifact_id="edit-a", **overrides):
    return normalize_artifact({
        "artifact_id": artifact_id, "repository": "fixture/project",
        "source_type": "git_commit_diff_hunk", "source_location": "fixture://change",
        "title": "Status resource budget change", "timestamp": "2024-02-01T00:00:00Z",
        "content": PATCH, "source_commit_sha": COMMIT, "source_file": "design.md",
        **overrides,
    })


def test_explicit_identity_groups_siblings_and_marks_complete(synthetic_state):
    a, b = source("first"), source("second")
    batches = select_event_batches(synthetic_state, [b, a], 10)
    assert len(batches) == 1
    view = event_context_view(batches[0])
    assert view["complete"] and view["event_group_complete"]
    assert view["artifact_ids"] == ["first", "second"]
    assert view["identity"]["source_commit_sha"] == COMMIT
    entry = view["canonical_artifacts"][0]
    assert entry["raw_diff"] == PATCH
    assert entry["hunks"][0]["before_text_sha256"] == hashlib.sha256(
        b"Status publishes reserved budgets.\n").hexdigest()
    assert entry["hunks"][0]["after_text_sha256"] == hashlib.sha256(
        b"Status publishes applied budgets.\n").hexdigest()


@pytest.mark.parametrize("override", [
    {"source_commit_sha": "b" * 40}, {"source_file": "other.md"},
    {"first_auditable_at": "2024-02-02T00:00:00Z"},
])
def test_commit_file_and_capture_are_isolated(synthetic_state, override):
    batches = select_event_batches(synthetic_state, [source("a"), source("b", **override)], 10)
    assert len(batches) == 2
    assert all(len(batch) == 1 for batch in batches)
    with pytest.raises(ValueError, match="cross_identity"):
        event_context_view([source("a"), source("b", **override)])


def test_repository_and_temporal_guards_are_applied(synthetic_state):
    other_repo = source("other", repository="fixture/other")
    old = source("old", timestamp="2024-01-01T00:00:00Z")
    future = source("future", timestamp="2025-02-01T00:00:00Z")
    good = source("good")
    batches = select_event_batches(synthetic_state, [other_repo, old, future, good], 10)
    assert [a["artifact_id"] for batch in batches for a in batch] == ["good"]
    with pytest.raises(ValueError, match="cross_identity"):
        event_context_view([good, other_repo])


@pytest.mark.parametrize("commit", ["", "abc123", None])
def test_unpinned_sources_never_group_from_hunk_prefix_or_title(synthetic_state, commit):
    a = source("common-H01", source_commit_sha=commit)
    b = source("common-H02", source_commit_sha=commit)
    batches = select_event_batches(synthetic_state, [a, b], 10)
    assert len(batches) == 2
    assert all(event_context_view(batch)["complete"] for batch in batches)
    with pytest.raises(ValueError, match="cross_identity"):
        event_context_view([a, b])


def test_missing_file_is_not_an_event_group(synthetic_state):
    batches = select_event_batches(synthetic_state,
                                   [source("a", source_file=""), source("b", source_file="")], 10)
    assert len(batches) == 2


def test_canonical_digest_tampering_fails_before_context(synthetic_state):
    bad = source()
    bad["content"] += "+invented statement\n"
    with pytest.raises(ValueError, match="digest_mismatch"):
        select_event_batches(synthetic_state, [bad], 10)
    with pytest.raises(ValueError, match="digest_mismatch"):
        event_context_view([bad])
    with pytest.raises(ValueError, match="digest_mismatch"):
        exact_event_passages(bad)


def test_selection_is_deterministic_and_uses_all_elements(synthetic_state):
    irrelevant = source("a", title="Noise", content="@@ -1 +1 @@\n-Noise one.\n+Noise two.\n",
                        source_commit_sha="b" * 40)
    relevant = source("z", source_commit_sha="c" * 40)
    one = select_event_batches(synthetic_state, [irrelevant, relevant], 1)
    two = select_event_batches(synthetic_state, [relevant, irrelevant], 1)
    assert one == two and one[0][0]["artifact_id"] == "z"
    assert synthetic_state["central_element_ids"] == ["PRIMARY"]


def test_complete_diffs_precede_prose_then_malformed_diffs(synthetic_state):
    prose = source("a", source_type="issue_comment", content="Resource budgets in Status.",
                   source_commit_sha="b" * 40)
    malformed = source("b", content=PATCH.replace("@@ -1 +1 @@", "@@ -1,9 +1,9 @@"),
                       source_commit_sha="c" * 40)
    complete = source("z")
    batches = select_event_batches(synthetic_state, [prose, malformed, complete], 10)
    assert [batch[0]["artifact_id"] for batch in batches] == ["z", "a", "b"]
    bad_view = event_context_view(batches[2])
    assert not bad_view["complete"]
    assert bad_view["canonical_artifacts"][0]["diff_incomplete_reason"] == "diff_hunk_line_counts_mismatch"
    with pytest.raises(ValueError, match="incomplete_diff"):
        exact_event_passages(malformed)


def test_read_limit_does_not_claim_full_group_context(synthetic_state):
    history = [source("a"), source("b"), source("c")]
    batches = select_event_batches(synthetic_state, history, 2)
    keys = [artifact_key(a) for batch in batches for a in batch]
    assert len(keys) == len(set(keys)) == 2
    view = event_context_view(batches[0])
    assert not view["event_group_complete"] and not view["complete"]
    assert all(entry["diff_complete"] for entry in view["canonical_artifacts"])
    assert len(batches[0][0]["_event_group_artifact_keys"]) == 3


def test_source_byte_and_hunk_limits_split_without_truncation(synthetic_state):
    history = [source("a"), source("b"), source("c")]
    bound = len(PATCH.encode("utf-8"))
    batches = select_event_batches(synthetic_state, history, 10, max_chars=bound, max_hunks=2)
    assert len(batches) == 3
    for batch in batches:
        assert sum(len(a["content"].encode("utf-8")) for a in batch) <= bound
        assert batch[0]["content"] == PATCH
        assert not event_context_view(batch)["event_group_complete"]


def test_hunk_bound_counts_actual_hunks_not_artifacts(synthetic_state):
    multi = source(content=PATCH + "@@ -10 +10 @@\n-Old fact.\n+New fact.\n")
    assert select_event_batches(synthetic_state, [multi], 10, max_hunks=1) == []
    assert len(select_event_batches(synthetic_state, [multi], 10, max_hunks=2)) == 1


def test_utf8_bytes_and_oversized_sources_are_never_truncated(synthetic_state):
    unicode_patch = "@@ -1 +1 @@\n-" + "é" * 30 + "\n+" + "é" * 30 + "\n"
    artifact = source(content=unicode_patch)
    assert len(unicode_patch.encode("utf-8")) > len(unicode_patch)
    assert select_event_batches(synthetic_state, [artifact], 10, max_chars=len(unicode_patch)) == []
    batches = select_event_batches(synthetic_state, [artifact], 10,
                                   max_chars=len(unicode_patch.encode("utf-8")))
    assert batches[0][0]["content"] == unicode_patch


def test_zero_and_invalid_budgets(synthetic_state):
    assert select_event_batches(synthetic_state, [source()], 0) == []
    assert select_event_batches(synthetic_state, [source()], 10, max_chars=0) == []
    with pytest.raises(ValueError, match="nonnegative"):
        select_event_batches(synthetic_state, [source()], -1)
    with pytest.raises(ValueError, match="nonnegative"):
        select_event_batches(synthetic_state, [source()], True)


def test_duplicate_keys_dedup_selection_and_reject_conflicts(synthetic_state):
    artifact = source()
    batches = select_event_batches(synthetic_state, [artifact, deepcopy(artifact)], 10)
    assert len(batches[0]) == 1
    conflicting = deepcopy(artifact)
    conflicting["source_file"] = "other.md"
    with pytest.raises(ValueError, match="conflicting_artifact"):
        select_event_batches(synthetic_state, [artifact, conflicting], 10)
    with pytest.raises(ValueError, match="duplicate_artifact"):
        event_context_view([artifact, artifact])


def test_direct_pinned_batch_cannot_attest_capture_completeness():
    view = event_context_view([source()])
    assert not view["event_group_complete"]
    assert view["canonical_artifacts"][0]["diff_complete"]


def test_outbound_redaction_preserves_local_exact_quotes_and_hashes(synthetic_state):
    patch = ("@@ -1 +1 @@\n-Contact old@example.com; secret=old-value\n"
             "+Contact new@example.com; secret=new-value\n")
    artifact = source(content=patch)
    passages = exact_event_passages(artifact)
    assert passages and all(p in patch for p in passages)
    assert any("new@example.com" in p for p in passages)
    view = event_context_view(select_event_batches(synthetic_state, [artifact], 10)[0])
    encoded = json.dumps(view)
    assert view["redacted"]
    assert "new@example.com" not in encoded and "secret=new-value" not in encoded
    assert "[EMAIL_REDACTED]" in encoded and "[CREDENTIAL_REDACTED]" in encoded
    assert view["canonical_artifacts"][0]["content_sha256"] == artifact["content_sha256"]
    assert artifact["content"] == patch


def test_every_changed_line_is_covered_without_top_five_limit():
    changed = [f"+Distinct new architectural statement number {i}." for i in range(40)]
    patch = "@@ -0,0 +1,40 @@\n" + "\n".join(changed) + "\n"
    artifact = source(content=patch)
    passages = exact_event_passages(artifact, max_chars=150)
    assert len(passages) > 5
    assert all(p in patch and len(p) <= 150 for p in passages)
    assert all(any(line in p for p in passages) for line in changed)


def test_passages_preserve_crlf_and_do_not_cross_hunk_headers():
    patch = "@@ -1 +1 @@\r\n-Old one.\r\n+New one.\r\n@@ -9 +9 @@\r\n-Old two.\r\n+New two.\r\n"
    passages = exact_event_passages(source(content=patch))
    assert len(passages) == 2 and all(p in patch for p in passages)
    assert all("@@" not in p for p in passages)
    assert any("\r\n" in p for p in passages)


def test_huge_changed_line_fails_clearly_instead_of_disappearing():
    artifact = source(content="@@ -0,0 +1 @@\n+" + "x" * 651 + "\n")
    with pytest.raises(ValueError, match="changed_line_exceeds_bound"):
        exact_event_passages(artifact)


def test_large_event_payload_avoids_repeated_entire_before_after(synthetic_state):
    long_fact = "Old budget statement " + "x" * 4300
    new_fact = "New budget statement " + "x" * 4300
    patch = f"@@ -1 +1 @@\n-{long_fact}\n+{new_fact}\n"
    history = [source("a", content=patch), source("b", content=patch)]
    view = event_context_view(select_event_batches(synthetic_state, history, 10)[0])
    assert view["complete"]
    assert view["canonical_artifacts"][0]["hunks"][0]["before_text_sha256"] == hashlib.sha256(
        (long_fact + "\n").encode()).hexdigest()
    second = view["canonical_artifacts"][1]
    assert "before_text" not in second["hunks"][0]
    assert "before_text_sha256" in second["hunks"][0]
    assert second["raw_diff"] == patch and second["before_after_derivation"]

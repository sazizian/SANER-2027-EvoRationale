"""Source catalog and nomination regressions; synthetic adapters, no provider."""
from copy import deepcopy
import json
from types import SimpleNamespace

import pytest

from evorationale.budget import Budget
from evorationale.delta_context import build_delta_catalog
from evorationale.delta_linking import DeltaLinker, NoNomination
from evorationale.event_agent import RequestBudgetTracker
from evorationale.event_context import select_event_batches
from evorationale.memory import DecisionMemory
from evorationale.model import artifact_key, element_by_id, normalize_artifact
from evorationale.structured_json import StructuredModelResponseError


def source(state, name="delta", content=None, source_type="git_commit_diff_hunk", **extra):
    return normalize_artifact({
        "artifact_id": name, "repository": state["repository"], "source_type": source_type,
        "source_location": "fixture://source", "source_commit_sha": "a" * 40,
        "source_file": "design.md", "title": "Synthetic design delta",
        "timestamp": "2024-02-01T00:00:00Z",
        "content": content or "@@ -1 +1 @@\n-Old mechanism.\n+New mechanism.\n", **extra,
    })


def batch(state, *artifacts):
    return select_event_batches(state, list(artifacts), len(artifacts))[0]


def reconstruct_payload_references(catalog):
    entries = {a["artifact_handle"]: a for a in catalog["payload"]["event_context"]["canonical_artifacts"]}
    for artifact in catalog["payload"]["artifacts"]:
        handle = artifact["artifact_handle"]
        numbered = entries[handle]["numbered_source"]
        source_lines = [line.split(": ", 1)[1] for line in numbered.splitlines(keepends=True)]
        for role, indices in artifact["line_roles"].items():
            for index in indices:
                line = catalog["lines"][f"{handle}:L{index:04d}"]
                assert line["role"] == role
                assert source_lines[index - 1].rstrip("\r\n\v\f\x1c\x1d\x1e\x85\u2028\u2029") == line["text"]
        for suffix, (first, last, start_column, end_column) in artifact["passages"].items():
            selected = source_lines[first - 1:last]
            quote = (selected[0][start_column:end_column] if first == last else
                     selected[0][start_column:] + "".join(selected[1:-1]) + selected[-1][:end_column])
            assert quote == catalog["passages"][f"{handle}:{suffix}"]["quote"]


class Replies:
    def __init__(self, corrupt=None, nominated=False):
        self.requests = []
        self.corrupt, self.nominated = corrupt, nominated

    def create(self, **request):
        self.requests.append(request)
        payload = json.loads(request["input"])
        ids = [element["id"] for element in payload["fixed_s0"]["elements"]]
        result = {"considered_element_ids": ids, "reviews": [
            {"artifact_handle": artifact["artifact_handle"],
             "status": "relation_found" if self.nominated else "no_material_relation",
             "reason": "Synthetic nomination review.",
             "element_ids": ids[:1] if self.nominated else []}
            for artifact in payload["artifacts"]
        ]}
        if self.corrupt:
            self.corrupt(result, payload)
        return SimpleNamespace(status="completed", output_text=json.dumps(result),
                               usage=SimpleNamespace(input_tokens=7, output_tokens=3, total_tokens=10))


def test_catalog_roles_and_passages_are_bound_to_exact_original_source(approved_state):
    artifact = source(approved_state)
    catalog = build_delta_catalog(approved_state, batch(approved_state, artifact))
    assert catalog["artifacts"]["A0001"]["content_sha256"] == artifact["content_sha256"]
    assert catalog["citation_coverage"] == {"A0001": True}
    assert {line["role"] for line in catalog["lines"].values()} == {"removed", "added"}
    for line in catalog["lines"].values():
        assert artifact["content"][line["start"]:line["end"]] == line["text"]
    for passage in catalog["passages"].values():
        assert artifact["content"][passage["start"]:passage["end"]] == passage["quote"]
    outbound = json.dumps(catalog["payload"])
    assert outbound.count("Old mechanism.") == 1
    assert outbound.count("New mechanism.") == 1
    assert "A0001:L0001" not in catalog["lines"]  # Header is not an evidence line.
    reconstruct_payload_references(catalog)


@pytest.mark.parametrize("newline", ["\n", "\r\n", "\u2028"])
def test_catalog_multiline_secret_is_screened_without_shifting_safe_handles(approved_state, newline):
    patch = newline.join(["@@ -1,3 +1,3 @@", " secret =", " continuation-value",
                          "-Old mechanism.", "+New mechanism.", ""])
    artifact = source(approved_state, content=patch)
    catalog = build_delta_catalog(approved_state, batch(approved_state, artifact))
    outbound = json.dumps(catalog["payload"])
    assert "continuation-value" not in outbound
    assert "A0001:L0002" not in catalog["lines"]
    assert "A0001:L0003" not in catalog["lines"]
    assert catalog["lines"]["A0001:L0004"]["role"] == "removed"
    assert catalog["lines"]["A0001:L0005"]["role"] == "added"
    for passage in catalog["passages"].values():
        assert "continuation-value" not in passage["quote"]
    assert catalog["citation_coverage"]["A0001"]
    reconstruct_payload_references(catalog)


def test_catalog_sensitive_changed_lines_leave_incomplete_citation_coverage(approved_state):
    patch = "@@ -1,2 +1,2 @@\n-Contact old@example.com\n+Contact new@example.com\n Safe context.\n"
    catalog = build_delta_catalog(approved_state, batch(approved_state, source(approved_state, content=patch)))
    assert not catalog["citation_coverage"]["A0001"]
    assert not catalog["passages"]
    assert list(catalog["lines"]) == ["A0001:L0004"]
    assert catalog["lines"]["A0001:L0004"]["role"] == "unchanged"
    assert "@example.com" not in json.dumps(catalog["payload"])
    reconstruct_payload_references(catalog)


def test_catalog_ambiguous_repeated_secret_continuation_has_no_safe_line_handle(approved_state):
    patch = ("@@ -1,4 +1,4 @@\n-Old mechanism.\n+New mechanism.\n"
             " secret =\n continuation-value\n continuation-value\n")
    artifact = source(approved_state, content=patch)
    catalog = build_delta_catalog(approved_state, batch(approved_state, artifact))
    assert "A0001:L0005" not in catalog["lines"]
    assert "A0001:L0006" not in catalog["lines"]
    assert not any("continuation-value" in passage["quote"] for passage in catalog["passages"].values())


def test_catalog_does_not_lexically_filter_distant_changed_lines(approved_state):
    patch = ("@@ -1,17 +1,17 @@\n-Early old mechanism.\n+Early new mechanism.\n"
             + "".join(f" Neutral context {i}.\n" for i in range(15))
             + "-Distant previous policy.\n+Distant replacement policy.\n")
    artifact = source(approved_state, content=patch)
    catalog = build_delta_catalog(approved_state, batch(approved_state, artifact))
    changed = [line for line in catalog["lines"].values() if line["role"] in {"removed", "added"}]
    assert len(changed) == 4 and catalog["citation_coverage"]["A0001"]
    assert all(any(line["start"] >= p["start"] and line["end"] <= p["end"]
                   for p in catalog["passages"].values()) for line in changed)
    reconstruct_payload_references(catalog)


@pytest.mark.parametrize("newline", ["\n", "\r\n", "\u2028"])
def test_repeated_diff_windows_keep_distinct_original_passage_positions(approved_state, newline):
    patch = newline.join(["@@ -1 +1 @@", "-Same old mechanism.", "+Same new mechanism.",
                          "@@ -7 +7 @@", "-Same old mechanism.", "+Same new mechanism.", ""])
    artifact = source(approved_state, content=patch)
    catalog = build_delta_catalog(approved_state, batch(approved_state, artifact))
    assert catalog["citation_coverage"]["A0001"]
    passages = list(catalog["passages"].values())
    assert len(passages) == 2
    assert passages[0]["quote"] == passages[1]["quote"]
    assert passages[0]["start"] != passages[1]["start"]
    rows = catalog["payload"]["artifacts"][0]["passages"]
    assert rows["P0001"][:2] == [2, 3]
    assert rows["P0002"][:2] == [5, 6]
    reconstruct_payload_references(catalog)


def test_repeated_prose_spans_after_redaction_keep_original_position(approved_state):
    text = "Contact user@example.com. Safe repeated premise.\nSafe repeated premise."
    artifact = source(approved_state, content=text, source_type="issue_comment")
    catalog = build_delta_catalog(approved_state, batch(approved_state, artifact))
    repeated = [p for p in catalog["passages"].values() if p["quote"] == "Safe repeated premise."]
    assert len(repeated) == 2 and repeated[0]["start"] != repeated[1]["start"]
    reconstruct_payload_references(catalog)


def test_catalog_prose_uses_statement_roles_and_narrow_exact_spans(approved_state):
    text = "Current mechanism uses one store. A new design explicitly adds a second store."
    artifact = source(approved_state, content=text, source_type="issue_comment")
    catalog = build_delta_catalog(approved_state, batch(approved_state, artifact))
    assert all(line["role"] == "statement" for line in catalog["lines"].values())
    assert catalog["passages"]
    for passage in catalog["passages"].values():
        assert text[passage["start"]:passage["end"]] == passage["quote"]
    entry = catalog["payload"]["event_context"]["canonical_artifacts"][0]
    screened = "".join(line.split(": ", 1)[1] for line in entry["numbered_source"].splitlines(keepends=True))
    for suffix, (_first, _last, start_column, end_column) in catalog["payload"]["artifacts"][0]["passages"].items():
        assert screened[start_column:end_column] == catalog["passages"][f"A0001:{suffix}"]["quote"]


def test_catalog_same_artifact_id_and_hash_versions_keep_distinct_handles(approved_state):
    one = source(approved_state, first_auditable_at="2024-02-01T01:00:00Z")
    two = source(approved_state, first_auditable_at="2024-02-01T02:00:00Z")
    # Direct batch is intentionally incomplete because capture identities differ.
    with pytest.raises(ValueError, match="cross_identity"):
        build_delta_catalog(approved_state, [one, two])
    two = source(approved_state, version_id="second-version",
                 first_auditable_at=one["first_auditable_at"])
    selected = batch(approved_state, one, two)
    catalog = build_delta_catalog(approved_state, selected)
    assert len(catalog["artifacts"]) == 2
    assert len({artifact_key(a) for a in catalog["artifacts"].values()}) == 2
    assert catalog["context"]["complete"]
    reconstruct_payload_references(catalog)


def test_catalog_rejects_tampered_source_before_model(approved_state):
    artifact = source(approved_state)
    artifact["content"] += "Injected later text."
    with pytest.raises(ValueError, match="canonical_digest_mismatch"):
        build_delta_catalog(approved_state, [artifact])


def test_nomination_returns_ids_without_relation_quote_or_confidence(approved_state):
    transport = Replies(nominated=True)
    linker = DeltaLinker("fixture", client=SimpleNamespace(responses=transport))
    selected = batch(approved_state, source(approved_state))
    nominations = linker.propose_event(approved_state, selected)
    assert nominations == [{"artifact_key": artifact_key(selected[0]),
                            "artifact_id": selected[0]["artifact_id"],
                            "decision_element_id": next(iter(element_by_id(approved_state)))}]
    assert set(nominations[0]) == {"artifact_key", "artifact_id", "decision_element_id"}
    assert linker.last_reviews[0]["considered_element_ids"] == list(element_by_id(approved_state))
    assert linker.last_reviews[0]["candidate_links"] == 1
    schema = transport.requests[0]["text"]["format"]["schema"]
    assert "confidence" not in json.dumps(schema)
    assert '"relation"' not in json.dumps(schema)
    payload = json.loads(transport.requests[0]["input"])
    assert set(payload) == {"fixed_s0", "event_context", "artifacts"}
    assert all(set(row) == {"artifact_handle", "citation_coverage_complete"} for row in payload["artifacts"])


def test_empty_nominations_still_publish_full_review_coverage(approved_state):
    linker = DeltaLinker("fixture", client=SimpleNamespace(responses=Replies()))
    assert linker.propose_event(approved_state, batch(approved_state, source(approved_state))) == []
    assert linker.last_reviews[0]["status"] == "no_material_relation"
    assert len(linker.last_reviews[0]["considered_element_ids"]) == len(element_by_id(approved_state))


@pytest.mark.parametrize("corrupt,code", [
    (lambda r, p: r.update(considered_element_ids=[]), "element_coverage"),
    (lambda r, p: r["considered_element_ids"].append(r["considered_element_ids"][0]), "element_coverage"),
    (lambda r, p: r["reviews"].pop(), "incomplete_delta"),
    (lambda r, p: r["reviews"][1].update(artifact_handle=r["reviews"][0]["artifact_handle"]), "review_fields"),
    (lambda r, p: r["reviews"][1].update(element_ids=["invented"]), "review_fields"),
    (lambda r, p: r["reviews"][1].update(element_ids=[r["considered_element_ids"][0]]), "review_status"),
    (lambda r, p: r["reviews"][1].update(status={}), "review_fields"),
    (lambda r, p: r["reviews"][1].update(relation="supports"), "review_fields"),
])
def test_malformed_nomination_is_atomic_and_technical(approved_state, corrupt, code):
    linker = DeltaLinker("fixture", client=SimpleNamespace(responses=Replies(corrupt)))
    selected = batch(approved_state, source(approved_state, "one"), source(approved_state, "two"))
    with pytest.raises(StructuredModelResponseError, match=code):
        linker.propose_event(approved_state, selected)
    assert linker.last_reviews == []
    assert linker.last_proposal_rejections
    assert linker.last_proposal_rejections[0]["failure_class"] == "technical_verification_failure"
    assert "Synthetic nomination review" not in json.dumps(linker.last_proposal_rejections)


def test_nomination_honors_configured_output_ceiling_and_usage_callback(approved_state):
    transport = Replies()
    memory = DecisionMemory(run_id="fixture", initial_state=deepcopy(approved_state), needs=[])
    tracker = RequestBudgetTracker(Budget(max_output_tokens=777), memory)
    linker = DeltaLinker("fixture", client=SimpleNamespace(responses=transport))
    linker.propose_event(approved_state, batch(approved_state, source(approved_state)), charge=tracker)
    assert transport.requests[0]["max_output_tokens"] == 777
    assert tracker.summary()["provider_reported_input_tokens"] == 7
    assert tracker.summary()["provider_reported_output_tokens"] == 3


def test_no_nomination_spends_no_provider_work_and_asserts_no_review(approved_state, monkeypatch):
    def forbidden(*args, **kwargs):
        raise AssertionError("No-nomination stage must perform no request, catalog build, or budget charge.")

    monkeypatch.setattr("evorationale.delta_linking.request_json_object", forbidden)
    monkeypatch.setattr("evorationale.delta_linking.build_delta_catalog", forbidden)
    linker = NoNomination()
    assert linker.nomination_mode == "none"
    assert DeltaLinker.nomination_mode == "model"
    assert linker.propose_event(approved_state, [source(approved_state)], charge=forbidden) == []
    assert linker.last_reviews == []
    assert linker.last_proposal_rejections == []


def test_no_nomination_leaves_bad_source_validation_to_independent_judge(approved_state):
    artifact = source(approved_state)
    artifact["content"] += "Tampered source."
    linker = NoNomination()
    assert linker.propose_event(approved_state, [artifact]) == []
    assert linker.last_reviews == []
    with pytest.raises(ValueError, match="canonical_digest_mismatch"):
        build_delta_catalog(approved_state, [artifact])


def test_no_nomination_has_independent_resettable_audit_lists(approved_state):
    one, two = NoNomination(), NoNomination()
    one.last_reviews.append({"stale": True})
    one.last_proposal_rejections.append({"stale": True})
    assert two.last_reviews == [] and two.last_proposal_rejections == []
    assert one.propose_event(approved_state, []) == []
    assert one.last_reviews == [] and one.last_proposal_rejections == []

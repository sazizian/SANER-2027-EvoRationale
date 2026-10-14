"""Source-proof regressions independent of any research reference labels."""
from copy import deepcopy

import pytest

from evorationale.analysis import composite_coverage
from evorationale.delta_context import build_delta_catalog
from evorationale.evidence_change import (
    substantive_changed_proof, substantive_current_added_proof, substantive_current_added_proofs,
)
from test_v45_delta_verification import case


@pytest.mark.parametrize("old,new,expected", [
    ("Retries are bounded,", "Retries are bounded.", False),
    ("The field is `VisibleCount`.", "The field is VisibleCount.", False),
    ("Retry at least once.", "Retry atleast once.", False),
    ("attempts < 3", "attempts > 3", True),
    ("Status.OldCount", "Status.CurrentCount", True),
    ("value = 1.0", "value = 1.1", True),
    ('label = "ready now"', 'label = "readynow"', True),
    ("value = 3,", "value = 3", True),
    ("value = 3.", "value = 3", True),
])
def test_formatting_screen_preserves_identifiers_values_and_operators(approved_state, old, new, expected):
    state, batch = case(approved_state, "@@ -1 +1 @@\n-" + old + "\n+" + new + "\n")
    catalog = build_delta_catalog(state, batch)
    before = [x for x in catalog["lines"].values() if x["role"] == "removed"]
    after = [x for x in catalog["lines"].values() if x["role"] == "added"]
    assert substantive_changed_proof(batch[0], before, after) is expected
    assert substantive_current_added_proof(batch[0], after[0]) is expected
    if not expected:
        # Omitting the old handles cannot manufacture a substantive source change.
        assert substantive_changed_proof(batch[0], [], after) is False


def test_unrelated_edit_cannot_rescue_local_formatting_proof(approved_state):
    patch = "@@ -1,2 +1,2 @@\n-Retries are bounded,\n+Retries are bounded.\n-Other value = 1\n+Other value = 2\n"
    state, batch = case(approved_state, patch)
    catalog = build_delta_catalog(state, batch)
    before = [x for x in catalog["lines"].values() if x["role"] == "removed"][:1]
    after = [x for x in catalog["lines"].values() if x["role"] == "added"][:1]
    assert not substantive_changed_proof(batch[0], before, after)
    assert not substantive_current_added_proof(batch[0], after[0])


def test_current_statement_without_diff_has_no_invented_before(approved_state):
    state, batch = case(approved_state, "New documentation exposes the applied count.", source_type="issue_comment")
    lines = list(build_delta_catalog(state, batch)["lines"].values())
    assert substantive_changed_proof(batch[0], [], lines)
    assert substantive_current_added_proof(batch[0], lines[0])


def test_unrelated_revision_cannot_make_reflowed_assertion_fresh_support(approved_state):
    patch = "@@ -1,2 +1,3 @@\n-Approved orders remain durable after failover.\n+Approved orders remain durable\n+after failover.\n-Revision 5\n+Revision 6\n"
    state, batch = case(approved_state, patch)
    lines = list(build_delta_catalog(state, batch)["lines"].values())
    added = [line for line in lines if line["role"] == "added"]
    assert substantive_changed_proof(batch[0], [], added[:2])
    assert not substantive_current_added_proof(batch[0], added[0])
    assert not substantive_current_added_proofs(batch[0], added[:1])
    assert not substantive_current_added_proofs(batch[0], added[:2])
    assert substantive_current_added_proofs(batch[0], added[2:])


def test_grouped_diff_reflow_is_not_fresh_even_with_only_first_fragment(approved_state):
    patch = "@@ -1,2 +1,3 @@\n-Approved orders persist through CentralQueue by the writer.\n-Revision 5\n+Approved orders persist through CentralQueue\n+by the writer.\n+Revision 6\n"
    state, batch = case(approved_state, patch)
    added = [line for line in build_delta_catalog(state, batch)["lines"].values() if line["role"] == "added"]
    assert not substantive_current_added_proof(batch[0], added[0])
    assert not substantive_current_added_proofs(batch[0], added[:1])
    assert substantive_current_added_proof(batch[0], added[2])


def test_repetitive_current_assertion_preserves_real_difference_without_character_alignment(approved_state):
    old, new = "Payload = " + "a" * 300, "Payload = " + "a" * 299 + "b"
    patch = "@@ -1,20 +1,20 @@\n" + ("-" + old + "\n") * 20 + ("+" + old + "\n") * 19 + "+" + new + "\n"
    state, batch = case(approved_state, patch)
    added = [line for line in build_delta_catalog(state, batch)["lines"].values() if line["role"] == "added"]
    assert not substantive_current_added_proof(batch[0], added[0])
    assert substantive_current_added_proof(batch[0], added[-1])


@pytest.mark.parametrize("old,new", [("value = 3,", "value = 3"), ("value = 3.", "value = 3")])
def test_compound_screen_does_not_drop_meaningful_trailing_tokens(approved_state, old, new):
    state, batch = case(approved_state, "@@ -1 +1 @@\n-" + old + "\n+" + new + "\n")
    added = [line for line in build_delta_catalog(state, batch)["lines"].values() if line["role"] == "added"]
    assert substantive_current_added_proofs(batch[0], added)


def test_partial_support_of_every_atomic_member_is_not_whole_composite_support():
    state = {"composite_groups": [{"original_id": "C", "member_ids": ["C1", "C2"]}]}
    links = [{"decision_element_id": m, "relation": "supports", "semantic_assessment": {
        "claim_scope": "material_subclaim", "whole_element_supported": False}} for m in ["C1", "C2"]]
    row = composite_coverage(state, links)[0]
    assert row["supporting_member_ids"] == ["C1", "C2"]
    assert row["partial_member_ids"] == ["C1", "C2"]
    assert not row["all_members_supported"]
    whole = deepcopy(links)
    for link in whole:
        link["semantic_assessment"] = {"claim_scope": "whole_element", "whole_element_supported": True}
    assert composite_coverage(state, whole)[0]["all_members_supported"]
    assert not composite_coverage(state, whole + [{"decision_element_id": "C1", "relation": "weakens"}])[0]["all_members_supported"]


def test_missing_or_conflicting_scope_does_not_certify_structured_whole_support():
    state = {"composite_groups": [{"original_id": "C", "member_ids": ["C1"]}]}
    for assessment in [{"claim_scope": "whole_element"}, {"whole_element_supported": True},
                       {"claim_scope": "material_subclaim", "whole_element_supported": True}]:
        links = [{"decision_element_id": "C1", "relation": "supports", "semantic_assessment": assessment}]
        assert not composite_coverage(state, links)[0]["all_members_supported"]

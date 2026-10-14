"""Portable synthetic cache/typed-checker contracts; no semantic accuracy claim."""
from copy import deepcopy
import json
from types import SimpleNamespace
import unittest

from evorationale.delta_context import build_delta_catalog
from evorationale.event_context import select_event_batches
from evorationale.model import element_by_id, normalize_artifact, validate_state
from evorationale.pair_review_verification import PairReviewSemanticJudge
from scope_checker import ALIGNMENT_FIELDS, CachedEventReviews, ScopedReplayJudge, EXPERIMENT_KIND


def old_decision(verdict="confirm"):
    return {"candidate_id": "C0001", "verdict": verdict,
        "reason": "The exact qualified hypothesis is assessed.",
        "predicate_reason": "The source addresses the proposed predicate.",
        "contribution_reason": "The added local statement provides new evidence.",
        "authority_reason": "The authority matches the proposed route."}


def scope_decision(verdict="confirm", **changes):
    return {**old_decision(verdict), **{field: True for field in ALIGNMENT_FIELDS}, **changes}


class Replies:
    def __init__(self, replies):
        self.replies = list(replies)
        self.calls = []

    def create(self, **request):
        self.calls.append(deepcopy(request))
        item = self.replies.pop(0)
        if isinstance(item, Exception):
            raise item
        return SimpleNamespace(status="completed", output_text=json.dumps(item))


def synthetic_cache_fixture(effect_changes=None, proposal=False, no_positive=False):
    """Return portable (state, history, checkpoint), independent of project Gold."""
    target = ("Allow the requesting actor to choose fallback when adjustment cannot complete." if proposal else
              "Publish admitted and applied worker allocations through WorkerStatus.")
    state = validate_state({"episode_id": "synthetic-scope-episode", "decision_id": "synthetic-scope-decision",
        "decision": "Choose documented worker resource adjustment behavior", "repository": "synthetic/workers",
        "accepted_at": "2024-01-01T00:00:00Z", "cutoff_at": "2025-01-01T00:00:00Z", "human_approved": True,
        "central_element_ids": ["T_REPORT"],
        "implementation_scope": [{"id": "T_REPORT", "text": target, "source": "fixture://worker-contract"}],
        "requirements": [{"id": "T_OTHER", "text": "Explain each worker-resource adjustment failure with an Event.",
                          "source": "fixture://worker-contract"}]})
    statement = ("The proposed fallback leaves retry or recreation to the requesting actor, preserving its choice." if proposal else
                 "The controller publishes admitted and applied allocations through WorkerStatus.")
    artifact = normalize_artifact({"artifact_id": "synthetic-publisher", "repository": state["repository"],
        "title": "Synthetic current contract", "source_location": "fixture://current-worker-contract",
        "source_type": "git_commit_diff_hunk", "timestamp": "2024-02-01T00:00:00Z",
        "content": "@@ -1,0 +1 @@\n+" + statement + "\n"})
    history = [artifact]
    batch = select_event_batches(state, history, 36)[0]
    catalog = build_delta_catalog(state, batch)
    effect = {"passage_handle": next(iter(catalog["passages"])), "element_id": "T_REPORT", "s0_claim_quote": target,
        "before_line_handles": [], "after_line_handles": list(catalog["lines"]), "context_line_handles": [],
        "before_claim": "The captured earlier source has no corresponding local contribution.",
        "after_claim": statement, "change_kind": "direct_rationale" if proposal else "documented_support",
        "source_role": "proposal_or_alternative" if proposal else "adopted_design",
        "claim_scope": "material_subclaim", "whole_element_supported": False, "scope_match": True,
        "material_target_delta": False, "replacement_is_explicit": False, "surviving_clause_masks_replacement": False,
        "confidence": .7, "evidence_basis": "direct_rationale_argument" if proposal else "adopted_design_statement",
        "qualification": "Qualified partial source evidence, not whole fulfillment or deployment.",
        "reason": "PRIMARY_PERSUASIVE_REASON", "effect_basis": "direct_rationale_argument" if proposal else "current_design_statement",
        "local_contribution": "PRIMARY_PERSUASIVE_CONTRIBUTION", "current_claim_entailed": True,
        "context_establishes_replacement": False, **(effect_changes or {})}
    first = {"considered_element_ids": list(element_by_id(state)), "reviews": [{
        "artifact_handle": "A0001", "status": "no_material_relation" if no_positive else "relation_found",
        "reason": "Every target pair explicitly considered.", "support_reason": "Current evidence considered.",
        "change_reason": "Architectural change considered.", "links": [] if no_positive else [effect],
        "pair_outcomes": [{"element_id": key, "outcome": "relation_found" if key == "T_REPORT" and not no_positive else "no_relation",
            "reason": "Exact predicate reviewed.", "relations": ["supports"] if key == "T_REPORT" and not no_positive else []}
            for key in element_by_id(state)]}]}
    fake = Replies([first] if no_positive else [first, {"decisions": [old_decision()]}])
    judge = PairReviewSemanticJudge("synthetic-no-api-model", client=SimpleNamespace(responses=fake))
    accepted, rejected = judge.review_event(state, batch, [])
    assert not any(x.get("failure_class") == "technical_verification_failure" for x in rejected)
    checkpoint = {"run_id": "synthetic-v49-parent", "initial_state": deepcopy(state), "verified_links": accepted,
        "rejected_interpretations": rejected,
        "report": {"investigation_profile": "event-pair-reviewed", "verified_evidence": deepcopy(accepted)},
        "trace": [{"round": 1, "profile": "event-pair-reviewed", "verification": "EVENT_REVIEW_COMPLETED",
            "retrieved_artifact_keys": catalog["context"]["artifact_keys"],
            "independent_artifact_reviews": deepcopy(judge.last_reviews),
            "pair_review_trace": deepcopy(judge.last_pair_review_trace)}]}
    return state, history, checkpoint


def checked_replay(fixture, vote):
    state, history, checkpoint = fixture
    cache = CachedEventReviews(state, history, checkpoint)
    fake = Replies([{ "decisions": [vote] }])
    judge = ScopedReplayJudge("synthetic-no-api-model", cache, client=SimpleNamespace(responses=fake))
    accepted, feedback = judge.review_event(state, cache.batches[0], [])
    return accepted, feedback, judge, fake


class ScopeCheckerTests(unittest.TestCase):
    def test_cache_reproduces_original_commit_without_provider(self):
        state, history, checkpoint = synthetic_cache_fixture()
        before = deepcopy((state, history, checkpoint))
        cache = CachedEventReviews(state, history, checkpoint)
        self.assertEqual(cache.original_links, checkpoint["verified_links"])
        self.assertEqual((cache.event_count, cache.candidate_event_count, cache.candidate_count), (1, 1, 1))
        self.assertEqual(before, (state, history, checkpoint))
        copied = cache.batches
        copied[0][0]["content"] = "caller mutation"
        self.assertNotEqual(copied, cache.batches)

    def test_complete_typed_confirmation_keeps_original_proof_and_cached_grid(self):
        accepted, feedback, judge, fake = checked_replay(synthetic_cache_fixture(), scope_decision())
        self.assertEqual(len(accepted), 1)
        self.assertFalse(feedback)
        self.assertEqual(len(fake.calls), 1)
        assessment = accepted[0]["semantic_assessment"]
        self.assertEqual(assessment["experiment_kind"], EXPERIMENT_KIND)
        self.assertEqual(assessment["primary_classification_origin"], "VALIDATED_CACHED_V49_OUTPUT")
        self.assertEqual(assessment["typed_alignment_epistemic_status"], "MODEL_ASSESSED")
        self.assertTrue(judge.last_reviews[0]["pair_outcomes_complete"])
        self.assertEqual(judge.last_pair_review_trace[0]["provider_calls"], 0)
        self.assertEqual(judge.last_pair_review_trace[1]["phase"], "scope_candidate_check")

    def test_each_false_alignment_flag_blocks_confirmation(self):
        for field in ALIGNMENT_FIELDS:
            with self.subTest(field=field):
                accepted, feedback, judge, fake = checked_replay(synthetic_cache_fixture(), scope_decision(**{field: False}))
                self.assertFalse(accepted)
                self.assertIn("MODEL_ASSESSED:scope_recheck_" + field + "_not_established", feedback[0]["reasons"])
                self.assertTrue(judge.last_reviews)
                self.assertFalse(judge.last_reviews[0]["confirmed_candidate_ids"])
                self.assertFalse(feedback[0]["semantic_assessment"]["scope_vote_passes_local_contract"])
                self.assertEqual(len(fake.calls), 1)

    def test_proposal_partial_route_is_preserved_without_promoting_authority(self):
        accepted, feedback, _, fake = checked_replay(synthetic_cache_fixture(proposal=True), scope_decision())
        self.assertEqual(len(accepted), 1)
        self.assertFalse(feedback)
        hypothesis = json.loads(fake.calls[0]["input"])["cached_candidate_hypotheses"][0]
        self.assertEqual(hypothesis["source_role"], "proposal_or_alternative")
        self.assertEqual(hypothesis["claim_scope"], "material_subclaim")
        self.assertFalse(hypothesis["whole_element_supported"])
        self.assertEqual(accepted[0]["evidence_scope"], "discussion")

    def test_typed_confirmation_cannot_rescue_existing_proof_guard(self):
        accepted, feedback, _, _ = checked_replay(synthetic_cache_fixture(effect_changes={"current_claim_entailed": False}), scope_decision())
        self.assertFalse(accepted)
        self.assertIn("MODEL_ASSESSED:current_fixed_claim_not_entailed", feedback[0]["reasons"])

    def test_whole_scope_false_certification_still_rejected(self):
        accepted, feedback, _, _ = checked_replay(synthetic_cache_fixture(effect_changes={"claim_scope": "whole_element"}), scope_decision())
        self.assertFalse(accepted)
        self.assertIn("MODEL_ASSESSED:whole_scope_without_whole_element_support", feedback[0]["reasons"])

    def test_reject_and_uncertain_preserve_auditable_decision(self):
        for verdict, reason in [("reject", "candidate_review_rejected"), ("insufficient_evidence", "candidate_review_insufficient_evidence")]:
            with self.subTest(verdict=verdict):
                accepted, feedback, judge, _ = checked_replay(synthetic_cache_fixture(), scope_decision(verdict))
                self.assertFalse(accepted)
                self.assertIn("MODEL_ASSESSED:" + reason, feedback[0]["reasons"])
                self.assertEqual(judge.last_reviews[0]["candidate_review_decisions"][0]["verdict"], verdict)

    def test_nonboolean_alignment_and_transport_failure_leave_event_unreviewed(self):
        for response in [{"decisions": [scope_decision(scope_aligned=1)]}, RuntimeError("synthetic transport failure")]:
            with self.subTest(response=repr(response)):
                state, history, checkpoint = synthetic_cache_fixture()
                cache = CachedEventReviews(state, history, checkpoint)
                fake = Replies([response])
                judge = ScopedReplayJudge("fixture", cache, client=SimpleNamespace(responses=fake))
                accepted, feedback = judge.review_event(state, cache.batches[0], [])
                self.assertFalse(accepted)
                self.assertFalse(judge.last_reviews)
                self.assertEqual(feedback[0]["failure_class"], "technical_verification_failure")

    def test_new_checker_never_receives_confidence_or_persuasive_explanations(self):
        changes = {"qualification": "Conditional source qualification; password=QUALIFICATION_PROTECTED_VALUE",
                   "before_claim": "Earlier scope; password=BEFORE_PROTECTED_VALUE",
                   "after_claim": "Current scope; password=AFTER_PROTECTED_VALUE"}
        _, _, _, fake = checked_replay(synthetic_cache_fixture(effect_changes=changes), scope_decision())
        raw = fake.calls[0]["input"]
        hypothesis = json.loads(raw)["cached_candidate_hypotheses"][0]
        self.assertFalse({"confidence", "reason", "local_contribution"} & set(hypothesis))
        self.assertNotIn("PRIMARY_PERSUASIVE", raw)
        self.assertNotIn("PROTECTED_VALUE", raw)
        self.assertIn("[CREDENTIAL_REDACTED]", raw)
        self.assertEqual(hypothesis["change_kind"], "documented_support")
        self.assertEqual(hypothesis["evidence_basis"], "adopted_design_statement")

    def test_no_positive_cached_event_never_calls_provider(self):
        state, history, checkpoint = synthetic_cache_fixture(no_positive=True)
        cache = CachedEventReviews(state, history, checkpoint)
        fake = Replies([])
        judge = ScopedReplayJudge("fixture", cache, client=SimpleNamespace(responses=fake))
        accepted, feedback = judge.review_event(state, cache.batches[0], [])
        self.assertFalse(accepted or feedback or fake.calls)
        self.assertEqual(cache.candidate_event_count, 0)
        self.assertTrue(judge.last_reviews[0]["pair_outcomes_complete"])

    def test_mismatched_cached_state_artifact_grid_or_candidate_ids_are_rejected(self):
        changes = [lambda cp: cp["initial_state"].update(decision="changed"),
            lambda cp: cp["trace"][0]["retrieved_artifact_keys"].__setitem__(0, "stale-source"),
            lambda cp: cp["trace"][0]["independent_artifact_reviews"][0]["explicit_pair_outcomes"].pop(),
            lambda cp: cp["trace"][0]["pair_review_trace"][-1]["primary_effects"][0].update(candidate_id="C0999")]
        for change in changes:
            with self.subTest(change=repr(change)):
                state, history, checkpoint = synthetic_cache_fixture()
                change(checkpoint)
                with self.assertRaises(ValueError):
                    CachedEventReviews(state, history, checkpoint)

    def test_modified_original_committed_link_is_rejected_without_api(self):
        state, history, checkpoint = synthetic_cache_fixture()
        checkpoint["verified_links"][0]["relation_confidence"] = .99
        checkpoint["report"]["verified_evidence"] = deepcopy(checkpoint["verified_links"])
        with self.assertRaisesRegex(ValueError, "do_not_reproduce_checkpoint"):
            CachedEventReviews(state, history, checkpoint)

    def test_changed_target_view_is_not_silently_reviewed_using_cache(self):
        state, history, checkpoint = synthetic_cache_fixture()
        cache = CachedEventReviews(state, history, checkpoint)
        changed = deepcopy(state)
        changed["requirements"][0]["text"] = "A different unrelated mandatory behavior."
        fake = Replies([])
        judge = ScopedReplayJudge("fixture", cache, client=SimpleNamespace(responses=fake))
        accepted, feedback = judge.review_event(changed, cache.batches[0], [])
        self.assertFalse(accepted or fake.calls)
        self.assertEqual(feedback[0]["failure_class"], "technical_verification_failure")

    def test_outbound_schema_is_basic_strict_with_typed_flags(self):
        state, history, checkpoint = synthetic_cache_fixture()
        judge = ScopedReplayJudge("fixture", CachedEventReviews(state, history, checkpoint), client=object())
        schema = judge._candidate_schema([{"candidate_id": "C0001"}])
        item = schema["properties"]["decisions"]["items"]
        self.assertEqual(set(item["properties"]), set(item["required"]))
        self.assertFalse(item["additionalProperties"])
        self.assertTrue(all(item["properties"][f] == {"type": "boolean"} for f in ALIGNMENT_FIELDS))
        self.assertNotIn("maxLength", json.dumps(schema))
        self.assertNotIn("maxItems", json.dumps(schema))


if __name__ == "__main__":
    unittest.main()

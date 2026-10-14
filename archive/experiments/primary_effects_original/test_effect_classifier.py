"""Synthetic primary/secondary/time/proof contracts; fake output is not F1."""
from copy import deepcopy
import json
from types import SimpleNamespace
import unittest

from evorationale.delta_context import build_delta_catalog
from evorationale.event_context import select_event_batches
from evorationale.model import normalize_artifact, validate_state
from evorationale.structured_json import StructuredModelResponseError
from effect_classifier import PrimaryEffectClassifier


class Replies:
    def __init__(self, responses):
        self.responses = list(responses)
        self.calls = []

    def create(self, **request):
        self.calls.append(deepcopy(request))
        reply = self.responses.pop(0)
        if isinstance(reply, Exception):
            raise reply
        return SimpleNamespace(status="completed", output_text=json.dumps(reply))


def case(patch=None, sibling=None, target_text=None):
    state = validate_state({"episode_id": "synthetic-primary-episode", "decision_id": "synthetic-primary-decision",
        "decision": "Choose worker adjustment contracts", "repository": "synthetic/contracts", "human_approved": True,
        "accepted_at": "2024-01-01T00:00:00Z", "cutoff_at": "2025-01-01T00:00:00Z", "central_element_ids": ["T1"],
        "implementation_scope": [{"id": "T1", "text": target_text or "Publish admitted and applied worker allocations through WorkerStatus.",
                                  "source": "fixture://baseline-contract"}],
        "requirements": [{"id": "T2", "text": "Distinguish admitted worker allocations from applied worker allocations.",
                          "source": "fixture://baseline-contract"}]})
    patch = patch or "@@ -1,0 +1 @@\n+The controller publishes admitted and applied allocations through WorkerStatus.\n"
    first = normalize_artifact({"artifact_id": "local-a", "repository": state["repository"], "title": "Current contract",
        "source_location": "fixture://current-contract", "source_type": "git_commit_diff_hunk",
        "timestamp": "2024-02-01T00:00:00Z", "content": patch})
    history = [first]
    if sibling:
        other = normalize_artifact({**first, "artifact_id": "local-b", "version_id": "other-contract",
                                    "content_sha256": "", "content": sibling})
        history.append(other)
        for artifact in history:
            artifact.update(source_commit_sha="a" * 40, source_file="docs/contract.md")
    batch = select_event_batches(state, history, 36)[0]
    return state, batch, build_delta_catalog(state, batch)


def effect(state, catalog, **changes):
    passage = next(h for h, p in catalog["passages"].items() if p["artifact_handle"] == "A0001")
    return {"element_id": "T1", "relation": "supports", "target_quote": state["implementation_scope"][0]["text"],
        "passage_handle": passage,
        "before_line_handles": [h for h, l in catalog["lines"].items() if l["artifact_handle"] == "A0001" and l["role"] in {"removed", "unchanged"}],
        "after_line_handles": [h for h, l in catalog["lines"].items() if l["artifact_handle"] == "A0001" and l["role"] in {"added", "unchanged"}],
        "context_line_handles": [], "before_claim": "No corresponding publishing operation is present locally.",
        "after_claim": "The controller publishes both qualified allocation values.", "qualification": "Source-defined partial contract evidence, not deployment validation.",
        "target_version": "fixed_s0", "evidence_route": "qualified_realization", "source_role": "adopted_design",
        "claim_scope": "material_subclaim", "whole_element_supported": False, "scope_match": True,
        "material_effect": False, "current_claim_entailed": True, "replacement_is_explicit": False,
        "baseline_change_asserted": False, "prior_contract_lineage": False, "fresh_contribution": True,
        "confidence": .7, **changes}


def reply(catalog, primary=None, secondary=None, disposition=None):
    primary, secondary = primary or [], secondary or []
    return {"considered_element_ids": ["T2", "T1"], "reviews": [{"artifact_handle": "A0001",
        "disposition": disposition or (primary[0]["relation"] if primary else "implementation_only"),
        "reason": "The principal changed local contract is assessed separately from retained evidence.",
        "primary_effects": primary, "secondary_effects": secondary}]}


def run(state, batch, catalog, response, baseline_context=None):
    provider = Replies([response])
    classifier = PrimaryEffectClassifier("synthetic-model", client=SimpleNamespace(responses=provider), baseline_context=baseline_context)
    rows = classifier.review_chunk(state, batch, ["A0001"])
    links = classifier.primary_links(state, batch, rows)
    return links, classifier, provider, rows


class EffectClassifierTests(unittest.TestCase):
    def test_primary_support_preserves_model_epistemic_scope_and_provenance(self):
        state, batch, catalog = case()
        links, classifier, provider, rows = run(state, batch, catalog, reply(catalog, [effect(state, catalog)]))
        self.assertEqual(len(links), 1)
        self.assertEqual(links[0]["decision_element_id"], "T1")
        self.assertFalse(links[0]["baseline_change_asserted"])
        self.assertEqual(links[0]["prediction_projection"], "PRIMARY_HUNK_EFFECT")
        self.assertEqual(links[0]["semantic_assessment"]["epistemic_status"], "MODEL_ASSESSED")
        self.assertFalse(links[0]["semantic_assessment"]["architectural_outcome_claimed"])
        self.assertEqual(len(provider.calls), 1)
        self.assertEqual(provider.calls[0]["text"]["format"]["name"], "primary_hunk_effect_review")
        self.assertEqual(classifier.last_rows, rows)

    def test_same_relation_secondary_for_another_target_is_kept_but_not_scored(self):
        state, batch, catalog = case()
        first = effect(state, catalog)
        secondary = effect(state, catalog, element_id="T2", target_quote=state["requirements"][0]["text"])
        links, _, _, rows = run(state, batch, catalog, reply(catalog, [first], [secondary]))
        self.assertEqual([l["decision_element_id"] for l in links], ["T1"])
        self.assertEqual(rows[0]["secondary_effects"], [secondary])

    def test_different_relation_secondary_does_not_replace_primary_by_priority(self):
        state, batch, catalog = case("@@ -1 +1,2 @@\n-Admitted allocations are published in WorkerStatus.\n+Admitted allocations are kept in LocalCheckpoint.\n+Applied allocations continue to be published in WorkerStatus.\n")
        primary = effect(state, catalog)
        secondary = effect(state, catalog, relation="supersedes", evidence_route="contract_delta", material_effect=True,
                           replacement_is_explicit=True, baseline_change_asserted=True)
        links, _, _, rows = run(state, batch, catalog, reply(catalog, [primary], [secondary]))
        self.assertEqual([l["relation"] for l in links], ["supports"])
        self.assertEqual(rows[0]["secondary_effects"][0]["relation"], "supersedes")

    def test_mixed_primary_types_or_duplicate_across_channels_are_rejected(self):
        for mixed in [True, False]:
            with self.subTest(mixed=mixed):
                state, batch, catalog = case()
                first = effect(state, catalog)
                second = effect(state, catalog, relation="weakens", evidence_route="documented_tradeoff") if mixed else deepcopy(first)
                response = reply(catalog, [first, second] if mixed else [first], [] if mixed else [second])
                provider = Replies([response])
                classifier = PrimaryEffectClassifier("fixture", client=SimpleNamespace(responses=provider))
                with self.assertRaises(StructuredModelResponseError):
                    classifier.review_chunk(state, batch, ["A0001"])

    def test_negative_primary_disposition_can_keep_secondary_evidence_without_links(self):
        state, batch, catalog = case()
        links, _, _, rows = run(state, batch, catalog, reply(catalog, secondary=[effect(state, catalog)], disposition="implementation_only"))
        self.assertFalse(links)
        self.assertTrue(rows[0]["secondary_effects"])

    def test_intermediate_contract_evolution_does_not_assert_baseline_change(self):
        state, batch, catalog = case("@@ -1 +1 @@\n-The adjustment policy must be append-only.\n+The adjustment policy may now be fully mutable.\n",
                                    target_text="Offer per-resource adjustment-policy choices to the requesting actor.")
        item = effect(state, catalog, relation="supersedes", target_version="prior_intermediate_contract",
                      evidence_route="contract_delta", material_effect=True, replacement_is_explicit=True,
                      prior_contract_lineage=True, baseline_change_asserted=False)
        links, classifier, _, _ = run(state, batch, catalog, reply(catalog, [item]))
        self.assertEqual(len(links), 1)
        self.assertEqual(links[0]["target_version"], "prior_intermediate_contract")
        self.assertFalse(links[0]["baseline_change_asserted"])
        self.assertFalse(classifier.last_feedback)

    def test_intermediate_lineage_and_baseline_scope_flags_fail_closed(self):
        for changes in [{"prior_contract_lineage": False}, {"baseline_change_asserted": True}]:
            with self.subTest(changes=changes):
                state, batch, catalog = case("@@ -1 +1 @@\n-Old contract restriction.\n+New contract restriction.\n")
                item = effect(state, catalog, **{"relation": "supersedes", "target_version": "prior_intermediate_contract",
                    "evidence_route": "contract_delta", "material_effect": True, "replacement_is_explicit": True,
                    "prior_contract_lineage": True, **changes})
                links, classifier, _, _ = run(state, batch, catalog, reply(catalog, [item]))
                self.assertFalse(links)
                self.assertIn("MODEL_ASSESSED:intermediate_contract_scope_not_preserved", classifier.last_feedback[0]["reasons"])

    def test_fixed_target_supersession_needs_baseline_change_assertion(self):
        state, batch, catalog = case("@@ -1 +1 @@\n-Old publishing contract.\n+New checkpoint contract.\n")
        item = effect(state, catalog, relation="supersedes", evidence_route="contract_delta", material_effect=True,
                      replacement_is_explicit=True, baseline_change_asserted=False)
        links, classifier, _, _ = run(state, batch, catalog, reply(catalog, [item]))
        self.assertFalse(links)
        self.assertIn("MODEL_ASSESSED:fixed_target_change_not_asserted", classifier.last_feedback[0]["reasons"])

    def test_support_scope_not_inherited_from_event_temporal_metadata(self):
        state, batch, catalog = case()
        batch[0]["temporal_basis"] = "INTERIM_2024"
        links, _, _, _ = run(state, batch, catalog, reply(catalog, [effect(state, catalog)]))
        self.assertEqual(links[0]["target_version"], "fixed_s0")

    def test_qualified_proposal_policy_sketch_can_support_without_adoption(self):
        state, batch, catalog = case("@@ -1,0 +1 @@\n+The proposed fallback leaves retry or recreation to the requesting actor.\n",
                                    target_text="Allow the requesting actor to choose fallback when adjustment cannot complete.")
        item = effect(state, catalog, source_role="proposal_or_alternative", evidence_route="qualified_realization")
        links, _, _, _ = run(state, batch, catalog, reply(catalog, [item]))
        self.assertEqual(len(links), 1)
        self.assertEqual(links[0]["evidence_scope"], "discussion")

    def test_proposal_cannot_claim_whole_adopted_support(self):
        state, batch, catalog = case()
        item = effect(state, catalog, source_role="proposal_or_alternative", claim_scope="whole_element", whole_element_supported=True)
        links, classifier, _, _ = run(state, batch, catalog, reply(catalog, [item]))
        self.assertFalse(links)
        self.assertIn("MODEL_ASSESSED:proposal_support_scope_not_preserved", classifier.last_feedback[0]["reasons"])

    def test_documented_cost_can_weaken_without_literal_baseline_change(self):
        state, batch, catalog = case("@@ -1,0 +1 @@\n+The chosen public allocation contract incurs extra API-evolution and reconciliation costs.\n")
        item = effect(state, catalog, relation="weakens", evidence_route="documented_tradeoff", material_effect=True,
                      current_claim_entailed=False, source_role="proposal_or_alternative", baseline_change_asserted=False)
        links, classifier, _, _ = run(state, batch, catalog, reply(catalog, [item]))
        self.assertEqual(len(links), 1)
        self.assertFalse(classifier.last_feedback)

    def test_current_support_needs_added_local_proof_not_historical_context(self):
        state, batch, catalog = case("@@ -1,2 +1,2 @@\n-Revision one.\n+Revision two.\n The controller publishes allocations through WorkerStatus.\n")
        item = effect(state, catalog, after_line_handles=[h for h, l in catalog["lines"].items() if l["role"] == "unchanged"])
        baseline = {"role": "BASELINE_CONTEXT_ONLY_NOT_FRESH_POST_S0_PROOF", "excerpts": [{"lines": [{"handle": "B:L0001", "text": "Historical publishing contract."}]}]}
        links, classifier, provider, _ = run(state, batch, catalog, reply(catalog, [item]), baseline)
        self.assertFalse(links)
        self.assertIn("primary_effect_has_no_substantive_added_local_proof", classifier.last_feedback[0]["reasons"])
        self.assertEqual(json.loads(provider.calls[0]["input"])["baseline_context"]["role"], baseline["role"])

    def test_baseline_handle_never_qualifies_as_after_proof(self):
        state, batch, catalog = case()
        response = reply(catalog, [effect(state, catalog, after_line_handles=["B:L0001"])])
        classifier = PrimaryEffectClassifier("fixture", client=SimpleNamespace(responses=Replies([response])))
        with self.assertRaisesRegex(ValueError, "invalid_primary_effect_line_handles"):
            classifier.review_chunk(state, batch, ["A0001"])

    def test_adopted_dependency_uses_full_event_contract_outside_focused_artifact(self):
        state, batch, catalog = case("@@ -1 +1 @@\n-The component reads the public allocation field.\n+The component reads the local checkpoint contract.\n",
                                    sibling="@@ -20,0 +20 @@\n+The adopted contract replaces public allocated status with local checkpoints.\n")
        item = effect(state, catalog, relation="supersedes", evidence_route="adopted_dependency", material_effect=True,
                      replacement_is_explicit=True, baseline_change_asserted=True,
                      context_line_handles=[h for h, l in catalog["lines"].items() if l["artifact_handle"] == "A0002"])
        links, classifier, provider, _ = run(state, batch, catalog, reply(catalog, [item]))
        self.assertEqual(len(links), 1)
        self.assertFalse(classifier.last_feedback)
        payload = json.loads(provider.calls[0]["input"])
        self.assertEqual(len(payload["event_context"]["canonical_artifacts"]), 2)
        self.assertEqual(payload["review_artifact_handles"], ["A0001"])

    def test_foreign_current_line_cannot_replace_local_added_proof(self):
        state, batch, catalog = case(sibling="@@ -20,0 +20 @@\n+External contract evidence.\n")
        item = effect(state, catalog, after_line_handles=[h for h, l in catalog["lines"].items() if l["artifact_handle"] == "A0002"])
        classifier = PrimaryEffectClassifier("fixture", client=SimpleNamespace(responses=Replies([reply(catalog, [item])])))
        with self.assertRaisesRegex(ValueError, "wrong_primary_effect_source_side_or_passage"):
            classifier.review_chunk(state, batch, ["A0001"])

    def test_separate_old_contract_and_current_citation_need_not_share_passage(self):
        patch = ("@@ -1 +0,0 @@\n-Old allocations are published in WorkerStatus.\n"
                 "@@ -100,0 +100 @@\n+New allocations are stored in LocalCheckpoint.\n")
        state, batch, catalog = case(patch)
        current_passage = next(h for h, p in catalog["passages"].items() if "New allocations" in p["quote"])
        old_line = next(h for h, l in catalog["lines"].items() if l["role"] == "removed")
        current_line = next(h for h, l in catalog["lines"].items() if l["role"] == "added")
        self.assertNotIn(catalog["lines"][old_line]["text"], catalog["passages"][current_passage]["quote"])
        item = effect(state, catalog, relation="supersedes", evidence_route="contract_delta", material_effect=True,
                      replacement_is_explicit=True, baseline_change_asserted=True, passage_handle=current_passage,
                      before_line_handles=[old_line], after_line_handles=[current_line])
        links, classifier, _, _ = run(state, batch, catalog, reply(catalog, [item]))
        self.assertEqual(len(links), 1)
        self.assertFalse(classifier.last_feedback)
        self.assertEqual(links[0]["quote"], "+New allocations are stored in LocalCheckpoint.")
        self.assertEqual(links[0]["semantic_assessment"]["exact_before_source_lines"],
                         ["-Old allocations are published in WorkerStatus."])
        self.assertNotIn("Old allocations", links[0]["quote"])

    def test_foreign_before_line_remains_forbidden(self):
        state, batch, catalog = case(sibling="@@ -20 +20 @@\n-External old contract.\n+External new contract.\n")
        foreign = next(h for h, l in catalog["lines"].items() if l["artifact_handle"] == "A0002" and l["role"] == "removed")
        item = effect(state, catalog, before_line_handles=[foreign])
        classifier = PrimaryEffectClassifier("fixture", client=SimpleNamespace(responses=Replies([reply(catalog, [item])])))
        with self.assertRaisesRegex(ValueError, "wrong_primary_effect_source_side_or_passage"):
            classifier.review_chunk(state, batch, ["A0001"])

    def test_after_line_elsewhere_in_same_artifact_still_cannot_escape_current_passage(self):
        patch = ("@@ -1,0 +1 @@\n+First current reporting assertion.\n"
                 "@@ -100,0 +100 @@\n+Second unrelated current reporting assertion.\n")
        state, batch, catalog = case(patch)
        first_passage = next(h for h, p in catalog["passages"].items() if "First current" in p["quote"])
        second_line = next(h for h, l in catalog["lines"].items() if "Second unrelated" in l["text"])
        item = effect(state, catalog, passage_handle=first_passage, after_line_handles=[second_line])
        classifier = PrimaryEffectClassifier("fixture", client=SimpleNamespace(responses=Replies([reply(catalog, [item])])))
        with self.assertRaisesRegex(ValueError, "wrong_primary_effect_source_side_or_passage"):
            classifier.review_chunk(state, batch, ["A0001"])

    def test_own_unchanged_current_qualifier_routes_to_context_with_original_handles(self):
        patch = ("@@ -1 +1 @@\n Feature-gated adjustment applies only to enabled workers.\n"
                 "@@ -100,0 +100 @@\n+The controller publishes admitted and applied allocations through WorkerStatus.\n")
        state, batch, catalog = case(patch)
        current_passage = next(h for h, p in catalog["passages"].items() if "controller publishes" in p["quote"])
        qualifier = next(h for h, l in catalog["lines"].items() if l["role"] == "unchanged")
        added = next(h for h, l in catalog["lines"].items() if l["role"] == "added")
        item = effect(state, catalog, passage_handle=current_passage,
                      before_line_handles=[qualifier], after_line_handles=[qualifier, added])
        response = reply(catalog, [item])
        original = deepcopy(response)
        links, classifier, _, rows = run(state, batch, catalog, response)
        self.assertEqual(response, original)
        self.assertEqual(len(links), 1)
        self.assertFalse(classifier.last_feedback)
        self.assertEqual(rows[0]["primary_effects"][0]["after_line_handles"], [added])
        self.assertEqual(rows[0]["primary_effects"][0]["context_line_handles"], [qualifier])
        self.assertEqual(links[0]["semantic_assessment"]["exact_context_source_lines"],
                         [" Feature-gated adjustment applies only to enabled workers."])
        self.assertEqual(len(classifier.last_proof_routing), 1)
        trace = classifier.last_proof_routing[0]
        self.assertEqual(trace["original_after_line_handles"], [qualifier, added])
        self.assertEqual(trace["normalized_after_line_handles"], [added])
        self.assertEqual(trace["normalized_context_line_handles"], [qualifier])
        self.assertEqual(trace["verification_scope"], "MECHANICAL_SOURCE_ROLE_ROUTING_ONLY")

    def test_unchanged_qualifier_routing_never_rescues_missing_local_added_proof(self):
        patch = ("@@ -1 +1 @@\n The reporting contract remains feature-gated.\n"
                 "@@ -100,0 +100 @@\n+Unrelated bookkeeping is newly documented.\n")
        state, batch, catalog = case(patch)
        current_passage = next(h for h, p in catalog["passages"].items() if "Unrelated bookkeeping" in p["quote"])
        qualifier = next(h for h, l in catalog["lines"].items() if l["role"] == "unchanged")
        item = effect(state, catalog, passage_handle=current_passage, after_line_handles=[qualifier])
        links, classifier, _, rows = run(state, batch, catalog, reply(catalog, [item]))
        self.assertFalse(links)
        self.assertEqual(rows[0]["primary_effects"][0]["after_line_handles"], [])
        self.assertIn("primary_effect_has_no_substantive_added_local_proof", classifier.last_feedback[0]["reasons"])
        self.assertTrue(classifier.last_proof_routing)

    def test_removed_after_handle_never_moves_into_current_context(self):
        state, batch, catalog = case("@@ -1 +1 @@\n-Old reporting rule.\n+New reporting rule.\n")
        removed = next(h for h, l in catalog["lines"].items() if l["role"] == "removed")
        item = effect(state, catalog, after_line_handles=[removed])
        classifier = PrimaryEffectClassifier("fixture", client=SimpleNamespace(responses=Replies([reply(catalog, [item])])))
        with self.assertRaisesRegex(ValueError, "wrong_primary_effect_source_side_or_passage"):
            classifier.review_chunk(state, batch, ["A0001"])
        self.assertFalse(classifier.last_proof_routing)

    def test_malformed_target_or_disposition_types_are_structured_errors(self):
        for field in ["considered_element_ids", "disposition"]:
            with self.subTest(field=field):
                state, batch, catalog = case()
                response = reply(catalog)
                if field == "considered_element_ids":
                    response[field] = [{"id": "T1"}, "T2"]
                else:
                    response["reviews"][0][field] = ["supports"]
                classifier = PrimaryEffectClassifier("fixture", client=SimpleNamespace(responses=Replies([response])))
                with self.assertRaises(StructuredModelResponseError):
                    classifier.review_chunk(state, batch, ["A0001"])

    def test_basic_strict_schema_no_unsupported_length_or_array_bounds(self):
        state, batch, catalog = case()
        classifier = PrimaryEffectClassifier("fixture", client=object())
        schema = classifier._response_schema(catalog, ["T1", "T2"], ["A0001"])
        def inspect(node):
            if isinstance(node, dict):
                self.assertFalse({"maxLength", "minLength", "minItems", "maxItems"} & set(node))
                if node.get("type") == "object":
                    self.assertFalse(node["additionalProperties"])
                    self.assertEqual(set(node["required"]), set(node["properties"]))
                for child in node.values():
                    inspect(child)
            elif isinstance(node, list):
                for child in node:
                    inspect(child)
        inspect(schema)


if __name__ == "__main__":
    unittest.main()

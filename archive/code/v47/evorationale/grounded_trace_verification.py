"""Exact-source predicate contributions, separated from downstream implementation use.

This is a model-assessed semantic policy, not a deterministic entailment engine.
It adds no provider phase, reference labels, target amendments or repository rules.
Historical event-delta and event-evidence policies retain their original behavior.
"""
from __future__ import annotations

from copy import deepcopy
from typing import Any

from .delta_verification import _contained, _nonblank_proof
from .diff_context import DIFF_SOURCE_TYPES
from .evidence_change import substantive_current_added_proofs
from .evidence_trace_verification import EvidenceTraceSemanticJudge, EVIDENCE_TRACE_INSTRUCTIONS
from .structured_json import StructuredModelResponseError


CONTRIBUTIONS = {
    "direct_predicate_evidence", "rebound_predicate_evidence", "explicit_boundary_argument",
    "direct_target_change", "direct_target_tradeoff", "dependent_target_change",
    "mere_dependency_use", "implementation_of_retained_rule", "unclear",
}
SUPPORT_CONTRIBUTIONS = {
    "direct_predicate_evidence", "rebound_predicate_evidence", "explicit_boundary_argument",
}
EXTRA_FIELDS = {"target_contribution", "predicate_line_handles"}

GROUNDED_TRACE_INSTRUCTIONS = EVIDENCE_TRACE_INSTRUCTIONS + (
    " Apply these narrower contribution tests before choosing a relation. target_contribution "
    "must identify what the SUBSTANTIVE LOCAL edit proves about the EXACT FIXED predicate, "
    "not what the entire surrounding design already implies. direct_predicate_evidence "
    "explicitly states or concretely tests that target's predicate, entities and qualifications. "
    "A list of existing field names does not establish their semantic roles. A downstream "
    "statistic using named states does not itself define or corroborate the state-transition "
    "model. Persistence/recovery of a classification does not itself establish a normative "
    "restriction on changing that classification during a different operation. Those edits "
    "are mere_dependency_use or implementation_of_retained_rule unless their own changed "
    "proof establishes the fixed predicate. They must not receive a relation. "
    "rebound_predicate_evidence is a substantive update to the grounding of an explicit "
    "target predicate, such as a changed operand in a source-defined comparison or check. "
    "The comparison can retain its logical purpose while newly binding a material operand; "
    "cite removed and added LOCAL proof. Do not confuse this with renaming, formatting, "
    "a bare changed identifier or a consumer that merely uses an existing dependency. "
    "explicit_boundary_argument is a new concrete explanation that an exact non-goal or "
    "constraint forbids a particular operation and describes its qualified fallback. Such "
    "an explanation can support the stated boundary even when it has a cost. A documented "
    "cost is weakens only if it directly reduces validity, feasibility or justification of "
    "the ACTUAL selected target; a cost of complying with an exclusion is not by itself "
    "evidence that the exclusion became less true. Use direct_target_tradeoff for such "
    "a genuine effect, and distinguish it from a proposed candidate's private pros/cons. "
    "A candidate's consistent field types do not themselves justify an adopted requirement "
    "to distinguish semantic roles. Shared topic, field labels, possible applicability or "
    "consideration of an alternative are insufficient. A qualified sketch may support a "
    "literal actor-owned decision or explicit exclusion it actually states, without adoption. "
    "For supports, predicate_line_handles are safe CURRENT after-side lines from the exact "
    "selected LOCAL passage that actually express or test the predicate; at least one must "
    "be substantively added/changed. Explain missing target parts in qualification and "
    "keep material_subclaim scope when they are absent. Never set current_claim_entailed "
    "true just because a new detail helps implement a broader target. "
    "direct_target_change affects a material fixed claim itself. dependent_target_change "
    "requires a material change to that SAME fixed claim, not merely a restart/maintenance "
    "consumer's implementation while the target reporting contract lives elsewhere. "
    "For an adopted mechanism_replacement, new proof can occur in context_line_handles "
    "if it is an ADDED current contract in the SAME exact artifact as the removed local "
    "claim. Explicitly affirm context_establishes_replacement and replacement_is_explicit. "
    "This is not permission to infer retirement from deletion or to borrow a sibling's "
    "proposal or metadata. Preserve all optional/legacy qualifications. predicate_line_handles "
    "may be empty for adverse relations; they are not a nomination or desired answer. "
    "All contribution classifications remain fallible MODEL_ASSESSED judgments."
)


class GroundedTraceSemanticJudge(EvidenceTraceSemanticJudge):
    instructions = GROUNDED_TRACE_INSTRUCTIONS
    query_id = "independent-grounded-trace"
    request_name = "independent_fixed_s0_grounded_trace_review"
    feedback_stage = "independent_grounded_trace_judge"

    def _initial_output_tokens(self, batch_size: int) -> int:
        # A complex pilot review needed a larger-output retry. This stays within
        # the existing request ceiling and
        # bounded retry policy; unused completion allowance is not reported use.
        return min(16384, max(6144, 2200 + batch_size * 1000))

    def _response_schema(self, catalog: dict[str, Any], target_ids: list[str]) -> dict[str, Any]:
        schema = super()._response_schema(catalog, target_ids)
        link = schema["properties"]["reviews"]["items"]["properties"]["links"]["items"]
        link["properties"]["target_contribution"] = {"type": "string", "enum": sorted(CONTRIBUTIONS)}
        link["properties"]["predicate_line_handles"] = {"type": "array", "items": {"type": "string"}}
        link["required"] += sorted(EXTRA_FIELDS)
        return schema

    def _validate_response(self, result: Any, catalog: dict[str, Any], elems: dict[str, Any]):
        if not isinstance(result, dict) or not isinstance(result.get("reviews"), list):
            raise StructuredModelResponseError("invalid_grounded_trace_review_object")
        filtered = deepcopy(result)
        for original, review in zip(result["reviews"], filtered["reviews"]):
            if not isinstance(original, dict) or not isinstance(original.get("links"), list):
                raise StructuredModelResponseError("invalid_grounded_trace_review")
            for original_effect, effect in zip(original["links"], review["links"]):
                if (not isinstance(original_effect, dict)
                        or not isinstance(original_effect.get("target_contribution"), str)
                        or original_effect["target_contribution"] not in CONTRIBUTIONS
                        or not isinstance(original_effect.get("predicate_line_handles"), list)):
                    raise StructuredModelResponseError("invalid_grounded_trace_contribution")
                handles = original_effect["predicate_line_handles"]
                if (any(not isinstance(h, str) or h not in catalog["lines"] for h in handles)
                        or len(handles) != len(set(handles))):
                    raise StructuredModelResponseError("invalid_grounded_trace_predicate_handles")
                own = original.get("artifact_handle")
                if any(catalog["lines"][h]["artifact_handle"] != own
                       or catalog["lines"][h]["role"] not in {"added", "unchanged", "statement"}
                       or h not in original_effect.get("after_line_handles", []) for h in handles):
                    raise StructuredModelResponseError("invalid_grounded_trace_predicate_ownership")
                for field in EXTRA_FIELDS:
                    del effect[field]
        super()._validate_response(filtered, catalog, elems)
        return result["reviews"]

    def _review_metadata(self, review: dict[str, Any]):
        return {**super()._review_metadata(review), "semantic_policy": "predicate-grounded",
                "assessment_origin": "MODEL_SELF_REPORTED_INDEPENDENT_GROUNDED_TRACE_REVIEW"}

    def _assessment_metadata(self, effect: dict[str, Any]):
        return {**super()._assessment_metadata(effect), "semantic_policy": "predicate-grounded",
                "contribution_epistemic_status": "MODEL_ASSESSED_NOT_ENTAILMENT_PROOF"}

    def _replacement_current_context(self, effect, relation, artifact, before, after, context_lines):
        own = effect["passage_handle"].split(":", 1)[0]
        return bool(
            relation == "supersedes" and effect["change_kind"] == "mechanism_replacement"
            and artifact["source_type"] in DIFF_SOURCE_TYPES
            and effect["target_contribution"] == "direct_target_change"
            and effect["source_role"] == "adopted_design"
            and effect["evidence_basis"] == "adopted_design_statement"
            and effect["scope_match"] and effect["material_target_delta"]
            and effect["replacement_is_explicit"] and effect["context_establishes_replacement"]
            and any(line["role"] == "removed" and _nonblank_proof(line) for line in before)
            and any(line["artifact_handle"] == own and line["role"] == "added"
                    and _nonblank_proof(line) for line in context_lines)
        )

    def _additional_effect_reasons(self, effect, relation, artifact, passage, before, after, context_lines):
        reasons = super()._additional_effect_reasons(
            effect, relation, artifact, passage, before, after, context_lines)
        contribution = effect["target_contribution"]
        expected = {
            "supports": SUPPORT_CONTRIBUTIONS,
            "supersedes": {"direct_target_change", "dependent_target_change"},
            "contradicts": {"direct_target_change"},
            "weakens": {"direct_target_tradeoff"},
        }
        if relation in expected and contribution not in expected[relation]:
            reasons.append("MODEL_ASSESSED:grounded_trace_has_no_direct_target_contribution")
        if effect["change_kind"] == "dependent_replacement" and contribution != "dependent_target_change":
            reasons.append("MODEL_ASSESSED:grounded_dependency_is_not_target_change")
        if relation == "supports":
            selected = set(effect["predicate_line_handles"])
            proof = [line for handle, line in zip(effect["after_line_handles"], after) if handle in selected]
            if (not proof or any(not _contained(line, passage) or not _nonblank_proof(line) for line in proof)
                    or not substantive_current_added_proofs(artifact, proof)):
                reasons.append("MODEL_ASSESSED:grounded_support_has_no_local_current_predicate_proof")
            if contribution == "rebound_predicate_evidence":
                if (artifact["source_type"] not in DIFF_SOURCE_TYPES
                        or effect["change_kind"] != "operational_witness"
                        or not any(line["role"] == "removed" and _nonblank_proof(line) for line in before)):
                    reasons.append("MODEL_ASSESSED:rebound_witness_has_no_old_predicate_proof")
            if contribution == "explicit_boundary_argument" and effect["change_kind"] != "direct_rationale":
                reasons.append("MODEL_ASSESSED:boundary_argument_is_not_direct_rationale")
        return reasons

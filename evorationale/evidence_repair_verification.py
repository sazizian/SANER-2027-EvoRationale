"""Narrow proof-routing repair using the measured v4.6 semantic policy.

The prompt and response schema are inherited verbatim from EvidenceTraceSemanticJudge.
This deliberately removes the v4.7 contribution restrictions from this profile.
No provider phase, target mutation, reference lookup or semantic answer is added.
"""
from .delta_verification import _nonblank_proof
from .diff_context import DIFF_SOURCE_TYPES
from .evidence_trace_verification import EvidenceTraceSemanticJudge


class EvidenceRepairSemanticJudge(EvidenceTraceSemanticJudge):
    query_id = "independent-evidence-repair"
    request_name = "independent_fixed_s0_evidence_repair_review"
    feedback_stage = "independent_evidence_repair_judge"

    def _initial_output_tokens(self, batch_size: int) -> int:
        # Preserve the larger bounded allowance that avoided a retry in v4.7.
        # It does not establish cheaper or faster hosted behavior generally.
        return min(16384, max(6144, 2200 + batch_size * 1000))

    def _replacement_current_context(self, effect, relation, artifact, before, after, context_lines):
        own = effect["passage_handle"].split(":", 1)[0]
        return bool(
            relation == "supersedes" and effect["change_kind"] == "mechanism_replacement"
            and artifact["source_type"] in DIFF_SOURCE_TYPES
            and effect["source_role"] == "adopted_design"
            and effect["evidence_basis"] == "adopted_design_statement"
            and effect["scope_match"] and effect["material_target_delta"]
            and effect["replacement_is_explicit"] and effect["context_establishes_replacement"]
            and any(line["role"] == "removed" and _nonblank_proof(line) for line in before)
            and any(line["artifact_handle"] == own and line["role"] == "added"
                    and _nonblank_proof(line) for line in context_lines)
        )

    def _review_metadata(self, review):
        return {**super()._review_metadata(review), "semantic_policy": "evidence-trace-repair",
                "semantic_prompt_source": "V46_EVIDENCE_TRACE_VERBATIM"}

    def _assessment_metadata(self, effect):
        return {**super()._assessment_metadata(effect), "semantic_policy": "evidence-trace-repair",
                "semantic_prompt_source": "V46_EVIDENCE_TRACE_VERBATIM"}

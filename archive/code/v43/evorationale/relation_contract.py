"""Shared relation semantics for the development proposer and hosted judge.

These are operational instructions, not benchmark labels or semantic proof.
No repository identifiers, example verdicts, or human reference data occur here.
"""

RELATION_CONTRACT = (
    "Interpret a relation against the FULL target element and its element_type. "
    "SUPPORTS requires evidence for every material part of that element; "
    "evidence for its core points or one surviving clause is insufficient. "
    "For a compound element, explicitly examine material parts that are omitted, "
    "removed, or replaced. Do not equate lexical overlap with entailment. "
    "WEAKENS requires evidence reducing the validity, feasibility, or justification "
    "of the target at its stated scope. A change in where or how an implementation "
    "exposes information does not by itself weaken a requirement to distinguish "
    "that information. Do not invent an exposure requirement absent from S0. "
    "CONTRADICTS requires an explicit incompatibility with a material target claim. "
    "SUPERSEDES requires a source-backed replacement or retirement of a material "
    "target claim or chosen mechanism. It may affect one material part of a compound "
    "element; specify the affected part without claiming the whole architecture "
    "or underlying goal was overturned. Mere omission in an isolated excerpt, "
    "a candidate alternative, or an unrelated edit is insufficient. Preserve "
    "phase, feature-gate, platform, and other qualifiers. Documentation establishes "
    "what a design document says, not proof of deployed implementation. "
    "Abstain if no relation is established at the target's actual scope."
)

DIFF_CONTRACT = (
    "A unified diff is a change record: '-' lines are the OLD text, '+' lines "
    "are the NEW text, and space-prefixed lines are unchanged context. "
    "Deleted text is not positive evidence for the current design. "
    "Read the source-derived before_text AND after_text, not only the selected "
    "quote. Check whether a material target part was changed elsewhere in the "
    "same hunk. These mechanically derived views are explanatory context, not "
    "verbatim citations; only supplied passage handles yield exact source quotes. "
    "The selected passage must contribute to the proposed relation. Do not use "
    "unrelated context to rescue it. Redaction placeholders cannot establish a "
    "material claim. An incomplete comparison cannot establish a relation. "
    "Do not infer adoption, release availability, or repository-wide absence "
    "from an edit alone. No human reference labels are provided."
)

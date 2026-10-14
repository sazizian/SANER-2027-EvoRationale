# v4.9 scope-contract audit (read only; no provider calls)

The second phase does not have a mechanically checkable definition of the exact qualified claim being confirmed. This is an interface blind spot, not a demonstrated explanation for the measured semantic false positives.

## Actual results

- 28 primary positive candidates received second-phase decisions: 26 confirms and 2 rejects.
- 25 survived the inherited source/semantic guards; all 11 reference false positives were confirmed.
- 22 accepted links use `material_subclaim`; 13 of those anchor the complete fixed element rather than identify a narrower affected clause.
- The actual FP checker explanations generally preserve the classifier's limitation. They do not demonstrate a disagreeing checker scope being committed as the primary claim.

## Code contract

`evorationale/pair_review_verification.py` constructs hypotheses from `element_id`, exact `s0_claim_quote`, `claim_scope`, proposed relation and primary-selected proof handles (lines 243–253). It deliberately withholds model-written qualification, before/after claims, reasons, contribution prose and semantic boolean conclusions.

The critic can return only candidate ID, verdict and four bounded prose reasons (lines 164–189). It cannot select an exact independently checked target clause, proof handles, qualification or authority classification. `_additional_effect_reasons` accepts a confirm after the inherited primary-source gates (lines 291–299), without comparing checker scope with the primary qualification. These deterministic gates certify schema, identity and provenance consistency, not the meaning of the free-text reasons.

## Concrete examples

| Accepted FP | Claim supplied to checker | Primary and checker interpretation | Implication |
|---|---|---|---|
| 964…H04 / I1 / supports | Entire compound desired/mutable-spec + allocated/applied-status element; `material_subclaim` | Primary: applied-resource reporting only. Critic independently names applied-status reporting and excludes unconditional allocation reporting. | The primary limitation was absent from the request; the critic happened to reconstruct it. No independently validated clause is stored. |
| 964…H05 / I1 / supports | Same full compound I1 element; `material_subclaim` | Both narrow support to actual/applied-status reporting, leaving allocated status and mutable spec unconfirmed. | This is under-specified hypothesis scope, not observed contradiction. Reference allows only supersedes on this hunk. |
| 964…H11 / R1 / supports | Entire three-way desired/allocated/actual distinction; `material_subclaim` | Both narrow support to desired-versus-actual comparison; neither claims the allocated distinction. | Correctly qualified prose can still yield a false exact triple. Scope validation alone cannot resolve the label granularity. |
| 689…H05 / I3 / supports | Entire resize-state modeling element; `material_subclaim` | Both narrow support to aggregate proposed/terminal progress accounting and exclude individual InProgress tracking. | The criticism is whether bookkeeping is fresh model evidence, not a missing qualifier in the final prose. |
| 964…H14 / I1 / supports | Allocated/applied-reporting clause; `material_subclaim` | Both restrict to discussion-level rationale for container allocation visibility, not an adopted obligation or applied-status claim. | Both models make the same semantic inference from an option's risk. Stronger structural citation cannot guarantee a different judgment. |

## Narrow generic correction

Make the hypothesis and verdict refer to the same specific qualified claim. Include a source-anchored alleged target clause and alleged qualification as explicitly untrusted candidate fields, continuing to withhold primary reasons and confidence. Require the critic to return an independently selected exact fixed-target clause, exact original-source proof handles, independent qualification and authority class, together with an explicit exact-claim verdict. Validate the returned quote, handle membership, source roles and captured-event identity mechanically. A confirm of a different/narrower claim must remain unresolved or become an explicitly separate claim, rather than certify the original one silently. The accepted report should carry the checked scope and preserve the primary interpretation separately.

This correction closes an auditable interface gap. It does not make semantic entailment deterministic, establish that any measured FP would disappear, or guarantee better F1. Whole-element quotes can be necessary to preserve qualifications, so do not reject them solely for length. Do not blanket-reject proposals, dependent replacements, partial scopes, or different relations on distinct clauses of a compound target. Additional output/token/retry behavior needs bounded testing.

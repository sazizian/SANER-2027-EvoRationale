# Actual v4.9 false-negative source audit

Five reference links are missing. Four desired candidates were never emitted; one (C1) was emitted and rejected by the independent critic. No desired candidate was rejected for a technical or exact-source failure.

## 04de3dac4669-F01-H01 / I2 / supersedes

Primary no_relation. The hunk changes policy editability from append-only to qualified mutability. I2 promises per-resource restart-policy choices, not policy mutability. Explicit review states S0 has no append-only restriction to supersede. No desired candidate reached the critic or source guard.

## 079aa5fb9ab1-F01-H02 / I2 / supersedes

Primary insufficient_evidence. The hunk changes mutable policy updates to append-only extension, but does not replace the restart-policy choices asserted by I2. The fixed target never asserted mutable entries or the removed entry-coverage rule. No desired candidate reached the critic or source guard.

## 079aa5fb9ab1-F01-H05 / C1 / supports

Primary emits supports for material_subclaim actor-owned fallback, qualified as a future sketch for illegal resizes. The critic rejects because controller-managed recreation is merely compatible with the full lifecycle exclusion and does not explicitly argue that exclusion. Both v46 and v48 accepted this triple. The only rejection reason is candidate_review_rejected; no technical or exact-source failure is involved. The critic receives full fixed C1 quote plus material_subclaim flag, proof handles and relation; primary qualification specifying the intended partial scope is intentionally withheld. This is an inspectable scope-interface risk and fallible semantic disagreement, not demonstrated proof that admission should override the critic.

## 68952e4476e4-F01-H01 / R2 / supports

Primary no_relation. Pod-level aggregate request state counters do not supply per-container/per-resource discrepancy explanations or required Events in R2. This explicit rationale agrees with v46/v48. No desired candidate reached the critic or source guard.

## 964260d9c2da-F01-H14 / I1 / weakens

Primary and critic confirm supports, never weakens. Their new reading treats Option 3's stated risk of hiding container-level allocation from outside consumers as a discussion-level argument in favor of allocation reporting. Earlier v46/v48 supported different hypothetical API sketches. A cost of dropping allocation visibility is not automatically a cost of chosen allocation reporting; expected weakens remains sensitive to source attribution and fixed-target scope. Do not force all alternative costs into weakens or change Gold/S0.

## True-positive changes

Versus both v46 and v48, 11 true positives survive and C1 is lost. Compared with v46, gains are QoS-boundary C2a, direct I1 replacement H04, and rebound R1 witness H13. Compared with v48, gains are C2a and recovered I1 replacements H03/H05.

## F1 feasibility

TP14/FP2/FN5 gives exactly 0.80, requiring nine FP removals without losing a TP. TP15/FP1/FN4 gives0.857143, requiring one TP recovery plus ten FP removals. These are arithmetic scenarios, not measured improvements. The fixed19-positive denominator remains unchanged.

## Recommendation

Keep v49 frozen; preserve all actual predictions. The main remaining F1 bottleneck is precision (11FP), while the explicit pair stage recovered omitted supersession/boundary links. Prioritize a generic, independently testable precision/scope defect identified by the FP audit; do not create another version solely to force these five reference triples. Any new hosted F1 claim needs a separately frozen experiment.

Before changing semantics, test whether independent candidate review consistently sees the intended partial target scope. It currently receives material_subclaim and a full compound S0 quote while withholding the explicit qualification. A future scope hypothesis could expose intended scope and retained qualifications as untrusted claims for independent checking, while still withholding confidence/reasons/contribution assertions. This requires generic compound-target counterexamples and full saved-effect replay; it is not grounds to auto-confirm rejected candidates.

No deterministic FN-side source guard defect is demonstrated. Passing a primary qualifier may introduce anchoring and can worsen precision. Generic transport tests prove information routing, not hosted semantic improvement.

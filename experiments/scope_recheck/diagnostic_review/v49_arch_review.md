# v4.9 architecture and checker audit

The explicit pair grid worked as an engineering change, but the independent checker did not improve reference accuracy in this completed run. Its three requests removed one otherwise accepted reference-positive relation and removed no otherwise accepted false-positive relation. The final all-scope F1 is 0.636364, slightly above v4.6's 0.631579 on this development fixture and far below the requested 0.80–0.85 range. The baseline scope regresses from v4.6's 0.689655 to 0.666667. These are descriptive comparisons, not statistical or generalization conclusions.

## Verified phase behavior

Run `8096127b` diagnostics record 12 primary classification requests and 3 candidate-check requests, with no retry or technical verification failure. All 540 selected artifact–target pairs are explicitly represented (30 selected hunks × 18 fixed targets), with no missing selected pair. Six selected metadata artifacts remain outside semantic review when the six-round limit is reached; pair completeness on selected hunks does not imply completeness of the complete captured input or repository history.

The candidate checks reviewed 28 hypotheses: 26 confirmations, 2 rejections and no insufficient-evidence verdict. The first source event had 18 confirmations, the second 5 confirmations, and the third 3 confirmations plus 2 rejections. The existing shared guards ultimately accepted 25 relations and rejected three proposed interpretations.

| Stored-output analysis | TP | FP | FN | All-scope F1 |
|---|---:|---:|---:|---:|
| Raw first-stage hypotheses, before source/semantic gates | 15 | 13 | 4 | 0.638298 |
| First stage with unchanged shared gates, critic bypassed in offline replay | 15 | 11 | 4 | 0.666667 |
| Actual completed two-stage run | 14 | 11 | 5 | 0.636364 |

The bypass row is a cached counterfactual. It reuses the original stored classifier effects and exact proof handles, validates them against the unchanged full canonical catalog, and runs the existing shared guards while suppressing only critic rejection. It is not a regenerated classifier response, a newly hosted run, or held-out accuracy. Runtime/scorer/reference files were not changed. Reference sets were reconstructed after the completed run from TP+FN exact-triple rows; no reference labels entered a model request.

The checker rejects `079aa5fb9ab1-F01-H05 / C1 / supports`, which the frozen reference treats as positive. Its other rejection is the same hunk's `C2a / weakens`, which would already fail the unchanged `no_material_target_delta` guard. Hence its marginal effect on otherwise accepted triples is one lost true positive and zero removed false positives. Baseline results remain TP12/FP10/FN2 under the cached bypass because the C1 relation is an interim-scope example.

The third shared rejection is `68952e4476e4-F01-H06 / I3 / supports`. The critic confirms it, but the primary effect declares `operational_caveat` while using `operational_witness`; inherited support-basis checks reject it. This demonstrates that confirmation does not override the shared guards. It also demonstrates that the critic's confirmation is broader than the primary acceptance contract.

## Resource consequence

| Phase | Requests | Estimated input | Provider input | Provider output |
|---|---:|---:|---:|---:|
| Explicit pair classification | 12 | 147,826 | 108,393 | 52,240 |
| Candidate checker | 3 | 35,204 | 29,283 | 5,595 |
| Completed total | 15 | 183,030 | 137,676 | 57,835 |

The checker adds these tokens while lowering exact-reference accuracy on the stored hypotheses. Removing it is therefore a useful measured ablation hypothesis, but cached replay alone does not establish that a future hosted run without it will produce identical primary responses. Neither phase demonstrated the requested F1. No dollar-price inference is made from opaque model identifiers or envelope estimates.

## Contract and scope ambiguity

The checker receives the proposed relation, exact target anchor, `claim_scope`, code-owned local/context proof handles, and the full screened source catalog. It deliberately does not receive primary confidence or persuasive reason/contribution prose. It also does not receive `change_kind`, `source_role`, `evidence_basis`, `whole_element_supported`, or the primary qualification. Consequently it cannot explicitly verify all authority/basis/scope commitments that the final accepted assessment retains.

This is visible in the rejected C1 example. The primary assessment specifies **partial discussion-level support for actor-owned fallback only**, expressly disclaiming the full lifecycle non-goal. Its target anchor quotes the compound full C1 element. The critic rejects because the source does not explicitly establish the complete lifecycle exclusion. The primary and critic are assessing ambiguously different scopes. The current `material_subclaim` label does not identify which material clause is proposed. This is a concrete hypothesis-contract ambiguity; it is not proof that the reference or either semantic judgment is universally correct.

Likewise, a critic confirmation can be for qualified design intent while the final primary assessment retains a stronger authority/evidence declaration. In this actual archive, accepted primary authority and checker authority generally agree; no accepted contradictory authority declaration was established. The caveat candidate above was blocked by inherited guards. Do not claim that missing fields themselves deterministically explain all 11 false positives.

Multiple support/supersession effects for different surviving and replaced parts of a compound target can be source-plausible yet disagree with a reference that assigns a primary hunk relation. Suppressing all support in the presence of adverse evidence would change the interpretation policy and may remove legitimate independent evidence. Any such policy must be predeclared and validated outside this tuned case, rather than selected because it removes these observed false positives.

## Evidence-backed next actions

1. Preserve the completed v4.9 code, diagnostic archive, frozen reference and scorer. Report the explicit coverage improvement and the measured precision/cost limitation honestly. Do not advertise a new accuracy version on this evidence alone.
2. Keep the stored-output checker ablation as an offline diagnosis. If evaluating checker omission later, make it an explicit experimental phase configuration and report changed compute, request count and uncertainty; do not rewrite the historical v4.9 score as if the bypass were its hosted result.
3. Before retaining a critic phase, make its hypothesis contract precise. Supply validated route enums/booleans and a screened qualification as **untrusted hypothesis data**, while continuing to withhold confidence and persuasive explanations. Prefer an exact source-owned affected target-clause span when partial scope is meaningful. Have the critic return its independently assessed authority/basis/scope, and route contradictions explicitly instead of silently accepting them under an unchanged primary label.
4. Test the routing mechanics with generic synthetic contrasts: proposal/partial versus adopted/whole; a compound goal supported only in one clause; reporting versus consuming a value; a dependent migration tied to an adopted replacement; and an operational caveat falsely presented as corroboration. Fake-response tests verify field preservation, coherence and rejection routing, not hosted semantic performance.
5. Evaluate any revised policy on independently held-out cases with predeclared outcomes and exact budgets. Pair coverage cannot guarantee recall, and a second model pass cannot guarantee precision. Current remaining false positives require semantic/error-construct analysis; increasing request count again without a discriminating hypothesis is not justified by this archive.

## Artifacts and review boundary

`diagnostic_review/v49_arch_review.json` contains exact sets, all 28 original candidate/decision records, phase resources and shared-guard bypass results. `diagnostic_review/v49_arch_audit.py` reproduces the cached replay using the unchanged v4.9 source gates. No provider/API request, source edit, scorer edit, label rewrite or secret access occurred in this audit.

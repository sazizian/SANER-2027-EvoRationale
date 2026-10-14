# Actual frozen-reference architecture review

The uploaded confirmed freeze removes an important uncertainty: the numerical scores are correct, but the formal task is a single declared hunk relation with target IDs for that relation, whereas recent runtime profiles emitted all qualified target effects. A narrowly isolated primary-effect prediction view is justified by the actual annotation convention. It should preserve secondary evidence separately and distinguish intermediate-contract evolution from fixed-S0 change. Its hosted F1 is still unmeasured.

## Independent integrity and rescoring

All seven frozen files match their manifest pins. The actual hunk CSV SHA256 is `8448a4efeca142d4410ea902b0e9f9e85958af52d745b8582a0757feb802f9ac`; the confirmed S0 SHA256 is `6557ea5d549fbc2bac280be4f46d948948dbb70673c0c1f53ff21c24c4fbde42`. The CSV has 30 hunks and 19 positive exact triples. Its positive-target distribution contains ten I1 triples, two I2, two R1, and one each for C1, C2a, G2, I3 and R2.

Using the unchanged v4.9 `_score_core.evaluate` against this actual CSV reproduces every stored count/rate and every exact error row for all four runs:

| Run | Baseline TP/FP/FN | Baseline F1 | All TP/FP/FN | All F1 |
|---|---|---:|---|---:|
| v4.6 | 10/5/4 | 0.689655 | 12/7/7 | 0.631579 |
| v4.8 | 10/7/4 | 0.645161 | 12/9/7 | 0.600000 |
| v4.9 | 12/10/2 | 0.666667 | 14/11/5 | 0.636364 |
| Cached scope recheck | 12/10/2 | 0.666667 | 13/11/6 | 0.604651 |

No scorer bug or arithmetic correction raises these results to 0.80–0.85. The inherited offline-baseline limitation wording is cosmetic and does not change the scores.

## Actual notes explain the projection difference

The event note for the September policy update explicitly describes the ID-listing convention: IDs list only targets to which the declared relation applies; other affected targets and their own relations are recorded in prose. The hunk CSV similarly has one relation field, with its related-target list.

The clearest example is the alternatives hunk ending H14 in the checkpoint-replacement event. Its formal label is WEAKENS/I1. The actual frozen note explicitly describes R1 as supportive rather than weakening, and consequently does not list R1 under WEAKENS. Thus `(that hunk, R1, supports)` is prose-acknowledged secondary evidence but is absent from the formal positive set. v4.6 and v4.8 emit it and the unchanged exact-triple scorer counts it as FP. This is not a reason to silently amend the reference: it establishes why all-effect runtime output and declared-relation reference output are different prediction views.

Other notes distinguish primary contract replacement from retained concepts: I1 is superseded while field-agnostic R1 remains inside the node; restart recovery is implementation-only with its reason retained; the completion predicate supports R1's surviving distinction. The appropriate projection cannot be a universal “adverse wins” rule. It needs a source-grounded choice of the principal local subject/contract effect, with independently useful secondary statements retained outside the scored view.

The notes also explicitly say the two I2 supersessions concern intermediate 2024 restrictions and leave the 2023 I2 choice contract unaffected. The current fixed-S0-only gate correctly refuses to invent those restrictions in the fixed target, but an all-hunk benchmark must also represent target-family evolution at intermediate-contract scope. A later event can simultaneously support a fixed goal through a concrete proposal; the model must not inherit one temporal target scope from the whole event or its date.

## Small isolated architecture correction supported by these facts

A new experimental primary-effect view can make the declared prediction unit match the formal row:

1. Select one primary relation type for each focused artifact and the fixed target-family IDs to which it applies. Preserve all secondary relations in a separate trace channel. Only primary source-screened links enter `verified_evidence` for the unchanged evaluator.
2. Record `target_version` and `baseline_change_asserted` explicitly. Fixed-target supersession must assert a baseline change; an intermediate-contract replacement needs local old/new proof and target-family lineage while preserving `baseline_change_asserted=false`. Weakening can concern a documented cost without a literal policy change.
3. Allow a qualified goal/delegation policy sketch to realize its exact predicate without demanding a stated causal argument. Preserve discussion authority and partial scope. Distinguish newly defined or rebound target predicates/contracts from incidental use of existing definitions; do not blanket-ban metrics, operands or consumers.
4. Keep mechanical provenance gates, source-owned handles and proof sides. Every positive needs substantive current local proof; historical baseline text cannot masquerade as fresh support or a current replacement contract.

These rules contain no case/hunk blacklist, no reference labels, no confidence threshold and no deterministic relation-type ranking. They change the operational semantic policy and prediction projection, so resulting comparisons remain descriptive development comparisons, not equal-task/equal-compute superiority claims. No automatic scope or flag proves that the model selected the right primary effect.

## Pinned baseline context is a separate missing input

The runtime sends condensed target text; its original-evidence list is empty. The publicly captured original README is available locally, and its Git blob hash exactly matches the confirmed pin `ce5124cf7975a7d4ce6a122b2cb4006b4bc0ea2d`. The original API section identifies the admitted-allocation field as `v1.ResourceList` and actual resources as `v1.ResourceRequirements`. This is the chosen-mechanism premise explicitly cited by the frozen H14 weakening explanation, but omitted from the condensed model input.

An optional, separately tagged baseline-context channel can ground those original definitions and reasons while preserving the exact S0 text. It must be bound to the pinned public commit/blob, screened, and prevented from entering current proof arrays. This adds source information and request tokens; disclose that changed input context. It may help the model interpret costs of the original field, but no F1 improvement follows from the hash check alone.

## Implementation and validation boundary

The independent module `primary_effect_kit/effect_classifier.py` now implements the isolated primary/secondary/time-scope view without editing v4.9, the scope kit, frozen S0, reference or scorer. Its basic strict schema and local gates are covered by 18 synthetic unit tests: primary-type coherence; same-kind secondary traces; proposal/whole-scope limits; intermediate versus fixed scope; cost without literal baseline change; local/current proof ownership; external adopted dependencies; baseline-proof exclusion; and malformed response handling. These fake-response tests validate routing and provenance, not a hosted classifier's semantic accuracy or the requested F1.

The most important remaining evaluation step is a predeclared blinded contrast set applying this projection consistently. Include mixed primary/secondary targets, retained versus rebound definitions, direct policies versus incidental consumers, and fixed versus intermediate evolution. Preserve the current pilot's frozen scores and explain the operational change before interpreting a new run. No 0.80–0.85 threshold is guaranteed.

`development_review/frozen_actual_arch_review.json` records the verified pins, independent rescoring, target distributions and exact prose/formal-label distinction. `development_review/frozen_actual_arch_rescore.py` reproduces the numeric audit. This review and local implementation made no provider call.

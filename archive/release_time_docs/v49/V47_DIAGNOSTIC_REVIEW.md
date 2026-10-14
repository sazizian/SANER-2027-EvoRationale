# Verified v4.7 regression diagnosis

Run a50dd556-729c-4840-a509-0fdd9222b81b. The supplied ten-member archive,
member hashes, score commit receipt, run/preparation/checkpoint identities and
frozen v4.7 core hash were verified. S0 and all 53 source bytes match v4.6.
Metrics also match independent TP/FP/FN counts from the error CSV.

| Version | Scope | TP | FP | FN | Precision | Recall | F1 |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| v4.6 | Baseline | 10 | 5 | 4 | 0.666667 | 0.714286 | 0.689655 |
| v4.7 | Baseline | 2 | 6 | 12 | 0.250000 | 0.142857 | 0.181818 |
| v4.6 | All | 12 | 7 | 7 | 0.631579 | 0.631579 | 0.631579 |
| v4.7 | All | 5 | 6 | 14 | 0.454545 | 0.263158 | 0.333333 |

All 30 diff versions were reviewed in the same six batches. There were eleven
accepted effects, one semantic rejection and zero technical failures. No missed
reference positive was emitted and then rejected by the final guard. The one
rejection concerns C2a on 079aa5fb9ab1-F01-H03, an implementation-only reference
hunk, not a reference positive. The scoring and completion guards did not cause
the accuracy regression.

v4.7 retained only two of twelve v4.6 all-scope true positives and none of its ten
baseline true positives. It gained three different true positives: the C2a
boundary argument, same-artifact I1 replacement and rebound R1 comparison.
Six previous false positives disappeared, but five new false positives were
introduced; R1 on 964260d9c2da-F01-H04 remains shared. Broad semantic restrictions
removed useful operational witnesses and same-event dependent migrations. In
several hunks the model substituted R1 support for I1 supersession, creating
both a false positive and a miss.

## Every all-scope error

| Verdict | Artifact | Fixed target | Relation | Source-level diagnosis |
| --- | --- | --- | --- | --- |
| FP | 964260d9c2da-F01-H04 | R1 | supports | The same-artifact routing repair recovers I1 supersession. Separate R1 support remains a reference false positive, as in v4.6. |
| FP | 964260d9c2da-F01-H05 | I1 | supports | The model replaces the earlier I1 dependency supersession with support for retained actual reporting and desired/actual distinctions. Both new support triples are false positives and the supersession is missed. |
| FP | 964260d9c2da-F01-H05 | R1 | supports | The model replaces the earlier I1 dependency supersession with support for retained actual reporting and desired/actual distinctions. Both new support triples are false positives and the supersession is missed. |
| FP | 964260d9c2da-F01-H06 | R1 | supports | The local admission migration is reclassified as a rebound R1 operational witness. The expected I1 dependent supersession is omitted. |
| FP | 964260d9c2da-F01-H08 | R1 | supports | The scheduler migration becomes R1 support while I1 dependency supersession is suppressed as a consumer-only change. |
| FP | 964260d9c2da-F01-H11 | R1 | supports | The quota migration becomes R1 support for a changed operand; the earlier I1 dependency supersession is omitted. |
| FN | 04de3dac4669-F01-H01 | I2 | supersedes | The required policy-mutability restriction is absent from fixed I2. This disclosed reference-contract mismatch persists; do not invent it. |
| FN | 079aa5fb9ab1-F01-H02 | I2 | supersedes | The append-only update rule is not part of the fixed restart-policy-choice claim. This persistent miss reflects fixed-target/reference tension. |
| FN | 68952e4476e4-F01-H01 | I3 | supports | The model now calls new completion comparisons and state instrumentation mere observation of existing concepts. It emits no effects, losing the two v4.6 operational witnesses. R2 granularity remains a separate persistent reference tension. |
| FN | 68952e4476e4-F01-H01 | R1 | supports | The model now calls new completion comparisons and state instrumentation mere observation of existing concepts. It emits no effects, losing the two v4.6 operational witnesses. R2 granularity remains a separate persistent reference tension. |
| FN | 68952e4476e4-F01-H01 | R2 | supports | The model now calls new completion comparisons and state instrumentation mere observation of existing concepts. It emits no effects, losing the two v4.6 operational witnesses. R2 granularity remains a separate persistent reference tension. |
| FN | 68952e4476e4-F01-H04 | I1 | supports | The model now treats added field-setting authority as a bare field list and suppresses the prior qualified I1 reporting support. Retained current context no longer helps it interpret the new statement. |
| FN | 964260d9c2da-F01-H03 | I1 | supersedes | The classifier refuses to use a sibling adopted current replacement contract for the changed local summary. Its local-scope interpretation is narrower than v4.6, even though the code did not reject an emitted effect. |
| FN | 964260d9c2da-F01-H05 | I1 | supersedes | The model replaces the earlier I1 dependency supersession with support for retained actual reporting and desired/actual distinctions. Both new support triples are false positives and the supersession is missed. |
| FN | 964260d9c2da-F01-H06 | I1 | supersedes | The local admission migration is reclassified as a rebound R1 operational witness. The expected I1 dependent supersession is omitted. |
| FN | 964260d9c2da-F01-H08 | I1 | supersedes | The scheduler migration becomes R1 support while I1 dependency supersession is suppressed as a consumer-only change. |
| FN | 964260d9c2da-F01-H09 | I1 | supersedes | The accounting rule is deemed downstream use. The earlier exact local migration plus sibling adopted contract is not emitted. |
| FN | 964260d9c2da-F01-H11 | I1 | supersedes | The quota migration becomes R1 support for a changed operand; the earlier I1 dependency supersession is omitted. |
| FN | 964260d9c2da-F01-H12 | I1 | supersedes | The scheduler requirement is deemed a consumer instruction. The earlier I1 dependency supersession is omitted. |
| FN | 964260d9c2da-F01-H14 | I1 | weakens | Conditional alternative costs are not tied directly enough to the chosen fixed target. Applicability remains ambiguous; do not force an adverse relation. |

The included development_review/v47_runtime_analysis.json stores the actual
review reasons and accepted old/new assessments for all twenty score errors.
Unchanged frozen labels and source IDs are used only for diagnosis/scoring;
they do not determine runtime predictions.

## Request behavior and interpretation limits

v4.7 used six requests and no retry: estimated input 61,175; provider-reported
input/output 42,755/17,515. v4.6 used seven requests, including one retry:
estimated input 62,911; provider-reported input/output 45,800/26,646. Wrapper
elapsed time was about 311.4 versus 440.5 seconds. These are descriptive single
development runs. They are not repeated latency or cost experiments, and model
snapshots are not verified. Fewer tokens/requests did not produce better
accuracy. Both runs stopped after six rounds with incomplete rationale/needs.
UNRESOLVED and AWAITING_HUMAN_REVIEW remain appropriate workflow states.

The 671 passing v4.7 tests validated source guards and software contracts,
not hosted interpretation quality. The changed instructions/schema are the
observed semantic regression mechanism; a single opaque-model run cannot
isolate all causal factors or show statistical significance.

## Minimal repair experiment

v4.6 remains the strongest measured development result. v4.8 restores its
semantic instructions and response schema verbatim for event-evidence-repair.
The only verifier change is the already reproduced same-artifact added-current
replacement-proof routing repair. The larger bounded output allowance remains;
no provider phase or extra semantic classification fields are added.

All 23 stored v4.6 effects were replayed without Gold or provider calls. All 19
accepted interpretations survive; the reproduced same-artifact rejection is
repaired; the other three rejections remain. This includes previous false
positives and does not prove that a fresh hosted run will reproduce these
interpretations. It is not new v4.8 F1. The interim I2 target mismatch,
observability granularity, dependent-reporting scope, freshness and alternative
cost applicability remain disclosed. S0, Gold, denominators and scorer are
unchanged. No held-out, generalization or optimal-performance claim is made.

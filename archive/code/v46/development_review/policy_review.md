# Independent v4.5 policy review

Run: `e98cc3a9-fe80-4db8-99d9-cc23a64c115f`. This review reads the uploaded report, checkpoint, exact captured source, fixed S0 and post-run scoring rows. It does not treat reference rows as model input or modify the frozen target/scorer.

## Where the 15 false negatives originated

The checkpoint records **four positive classified effects, four accepted effects, zero rejected interpretations, zero verifier feedback, zero technical verification failures**, six received provider responses and 30 reviewed diff artifacts. All 15 scored missing triples were omitted by the independent model as `no_material_relation`; none were subsequently removed by a mechanical verifier gate.

Consequently, relaxing citation/source-side validation would not recover any of these actual omissions. The conservative semantic policy is the relevant area to improve.

## Four accepted links

All four are I1 `supersedes`, affecting the allocated-reporting portion of the fixed target while preserving applied-resource reporting and conditional alpha allocation reporting:

| Exact source | Assessment |
|---|---|
| `964260d9c2da-F01-H03` | The central summary removes ordinary allocated resources from the described PodStatus reporting role. Exact same-event API lines establish checkpointing and the separately gated residual field. The qualification avoids claiming global deletion. |
| `964260d9c2da-F01-H04` | The API design changes ordinary allocation reporting to checkpointing, with a separately gated alpha allocation-status field. This is a direct mechanism replacement, not invalidation of the requirement to distinguish resource quantities. |
| `964260d9c2da-F01-H05` | The compatibility description replaces its public comparison source from allocated resources to actual configurations. Same-event design context establishes that this reflects the changed reporting contract. |
| `964260d9c2da-F01-H06` | The admission description removes the ordinary allocation-status write, leaving checkpointing; the residual gated path is explicitly qualified. |

These are defensible partial source-backed interpretations. Their existence does not resolve all central needs or prove deployed behavior.

## Conservative policy and evaluation tensions

Original v4.5 locations are in `evorationale/delta_verification.py`:

- Lines 49–56 require an architectural effect of the target-local change and permit same-event context only to explain that local effect. Lines 63–70 prohibit surviving invariants/existing state names as fresh evidence and require newly realising mechanisms. Lines 86–88 exclude pure implementation details. This encourages the model to exclude downstream migrations even when their changed source dependency concretely witnesses an explicit same-event architectural replacement.
- H08/H09/H11/H12 migrate consumer references away from the old status allocation field. The model calls them consumer implementation changes because fixed S0 does not prescribe the consumer formula. A principled evidence-trace policy may link such a migration to I1 if exact local old/new proof and an adopted same-event replacement contract establish the causal dependency. A generic accounting edit must not borrow a sibling's supersession.
- Instrumentation can be a newly introduced operational witness for an existing state model (I3), even though the architecture is unchanged. The v4.5 negative explanation equates lack of a newly introduced state model with lack of supporting evidence. R1's desired/allocated/actual completion comparison is also plausible current trace evidence. R2 remains a scope tension: Pod-level aggregate counters do not establish per-resource/container explanations or Pod Events; shared state labels alone must not certify that compound target.
- The newly added readiness description explicitly says Kubelet sets the two resource status fields. Current documentary support can be meaningful without being a newly invented mechanism or observed runtime validation.
- H13 changes a representation while retaining the three-way completion invariant. It remains no novel architecture drift; a separately declared evidence-trace policy can assess the changed current expression as preservation evidence, without conflating it with fresh behavioral validation.
- H14's costs may weaken the chosen reporting mechanism only when the source ties those costs to that actual mechanism. Candidate-specific costs alone are insufficient. Discussion need not adopt a replacement to provide a direct cost argument.
- The two INTERIM_2024 expected I2 supersessions rely on mutability rules absent from fixed S0. Their omission is correct under the fixed-target task. No new policy should invent those unseen restrictions to obtain a higher score.
- The future controller sketch may provide qualified rationale for actor-owned control/lifecycle and preserved QoS restrictions without proving adopted behavior. Its policy arguments and hypothetical implementation benefits must be separated.

## Latent gate issue, not a cause of this uploaded run

Original lines 360–361 reject identical `before_claim` and `after_claim` strings for every relation. New supporting evidence can corroborate an unchanged proposition. A separate evidence-trace policy should permit qualified partial support with the same proposition when it has substantively added current source evidence; adverse relations still require an actual material change. This gate was never triggered in the uploaded run because no such effect was emitted.

## Minimal principled improvement

Keep v4.5 novel-delta available. Add an opt-in evidence-trace policy using the same deterministic provenance, source-side, quotation, time, privacy, whole-scope, removed-only and fixed-S0 guards. Require explicit `effect_basis`, nonempty local contribution, current-claim entailment assessment and separate support/change reasons. Map documented current support, operational witnesses and dependent replacements in code. Preserve partial scope and mark all semantic judgments as model-assessed. Separate current evidence support from novel architectural change and deployed validation in the audit record.

Substantive local source guards should reject punctuation/backtick-only edits, unchanged assertions supported by unrelated edits, and unsupported cross-artifact replacement borrowing. They are structural checks, not semantic correctness or F1 tests.

Suggested synthetic regression boundaries: existing proposition with a new current statement/witness; no novel drift metadata; explicit consumer migration with current external adopted contract; absent/old-only/own/proposed contract rejection; incorrect target scope rejection; current support entailment and qualified partial scope; formatting-only and incidental unchanged support rejection; direct discussion support/cost arguments without adopted behavior; absent interim target restriction rejection; original v4.5 schema/behavior preservation.

The next hosted F1 remains unmeasured; fake structured-provider tests validate these boundaries only.

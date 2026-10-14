# Supplied v4.6 hosted-run diagnosis

Run `188132b4-7975-4ae9-8df4-0cbbc1cad9ad`. The supplied nine-member diagnostic archive, its
member hashes, completed-run receipt, preparation, report, checkpoint and score
identities were checked. Runtime S0 and all 53 captured sources remain identical
to the prior inputs. These are known development examples, not held-out data.

| Scope | TP | FP | FN | Precision | Recall | F1 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Baseline | 10 | 5 | 4 | 0.666667 | 0.714286 | 0.689655 |
| All | 12 | 7 | 7 | 0.631579 | 0.631579 | 0.631579 |

All 30 diff versions were reviewed in six batches [14,6,5,1,2,2]. Nineteen links
were accepted, four semantic interpretations rejected and zero technical
verification failures recorded. The run used seven provider requests: six
classifications and one bounded retry, with no nomination. Estimated input was
62,911 / 100,000; provider-reported input/output was 45,800 / 26,646. Elapsed
wrapper time was about 440.5 seconds, not a controlled latency benchmark.

The five-artifact review first reported 4,800 output tokens at a 4,800 allowance
and was retried with 9,600, producing 5,876. This is consistent with an incomplete
or output-limited first reply, but raw provider status/reason was not retained,
so truncation is not proved. v4.7 increases the initial allowance within the same
16,384 ceiling. It adds no provider phase and does not promise lower token use,
cost or latency. Real positive outputs can still need the bounded retry.

`UNRESOLVED` is not an API crash. Six rounds were exhausted, rationale coverage
was incomplete, many needs remained open/partial, and I1 had conflicting
evidence. Claims passing source checks do not make the architectural outcome
correct or remove human review. v4.6 retained three of four v4.5 true positives
and added nine; the fourth was blocked by the routing defect described below.

## Every all-scope score error

| Verdict | Artifact | Fixed target | Relation | Diagnosis |
| --- | --- | --- | --- | --- |
| FP | 079aa5fb9ab1-F01-H03 | C2a | supports | Downstream implementation, not direct exclusion evidence |
| FP | 079aa5fb9ab1-F01-H04 | C2a | supports | Downstream recovery, not direct exclusion evidence |
| FP | 68952e4476e4-F01-H04 | R1 | supports | Compound predicate overreach |
| FP | 68952e4476e4-F01-H05 | I3 | supports | Consumer of retained transition rule |
| FP | 964260d9c2da-F01-H04 | R1 | supports | Freshness and target-attribution ambiguity |
| FP | 964260d9c2da-F01-H07 | I1 | supersedes | Reporting contract versus downstream recovery scope |
| FP | 964260d9c2da-F01-H14 | R1 | supports | Alternative-specific benefit versus adopted rationale |
| FN | 04de3dac4669-F01-H01 | I2 | supersedes | Fixed-target/reference mismatch |
| FN | 079aa5fb9ab1-F01-H02 | I2 | supersedes | Fixed-target/reference mismatch |
| FN | 079aa5fb9ab1-F01-H05 | C2a | supports | Boundary argument confused with cost of compliance |
| FN | 68952e4476e4-F01-H01 | R2 | supports | Observability granularity/reference tension |
| FN | 964260d9c2da-F01-H04 | I1 | supersedes | Confirmed proof-routing defect |
| FN | 964260d9c2da-F01-H13 | R1 | supports | Substantively rebound predicate evidence |
| FN | 964260d9c2da-F01-H14 | I1 | weakens | Cost applicability and authority ambiguity |

## Source-level explanations

### FP: 079aa5fb9ab1-F01-H03 / C2a / supports

Downstream implementation, not direct exclusion evidence

Guaranteed-resource condition changed; the QoS prohibition itself is retained with emphasis. Implementing a condition does not establish the different normative prohibition.

### FP: 079aa5fb9ab1-F01-H04 / C2a / supports

Downstream recovery, not direct exclusion evidence

The local change stores original QoS in status for restart recovery. That recovery dependency does not directly establish the prohibition on changing Pod QoS during in-place resize.

### FP: 68952e4476e4-F01-H04 / R1 / supports

Compound predicate overreach

New field names and a retained status explanation were taken as fresh evidence for the desired/allocated/actual distinction. The same hunk has a true I1 support; that does not imply a separate R1 support.

### FP: 68952e4476e4-F01-H05 / I3 / supports

Consumer of retained transition rule

A new steady-state aggregate metric uses existing state names. Using the transition model is weaker than expressing or testing its target predicate. Reference scope is implementation-only.

### FP: 964260d9c2da-F01-H04 / R1 / supports

Freshness and target-attribution ambiguity

The source changes where actual-resource derivation obtains allocation data. This can appear to corroborate the distinction; the reference instead attributes this hunk to I1 supersession. Direct target-local predicate evidence must be explicit.

### FP: 964260d9c2da-F01-H07 / I1 / supersedes

Reporting contract versus downstream recovery scope

Restart recovery moves from status to a checkpoint under an explicit sibling contract. The reference treats this consumer migration as implementation-only. A dependency change must affect the exact fixed reporting claim itself.

### FP: 964260d9c2da-F01-H14 / R1 / supports

Alternative-specific benefit versus adopted rationale

A prospective alternative lists consistent types for desired/allocated/actual fields. A candidate-specific type benefit does not by itself justify the adopted semantic-role distinction.

### FN: 04de3dac4669-F01-H01 / I2 / supersedes

Fixed-target/reference mismatch

The label requires an interim mutability restriction absent from the fixed I2 restart-policy-choice claim. Runtime must not invent the missing restriction or silently alter S0.

### FN: 079aa5fb9ab1-F01-H02 / I2 / supersedes

Fixed-target/reference mismatch

The append-only/mutability requirement needed by the reference is absent from fixed I2. Correct fixed-target abstention is still scored as a miss under the unchanged reference.

### FN: 079aa5fb9ab1-F01-H05 / C2a / supports

Boundary argument confused with cost of compliance

The source states that Guaranteed-to-Burstable is illegal in-place and requires recreation. The model proposed weakens and the gate rejected no_material_target_delta. An explicit exclusion and its fallback can support the boundary even if compliance costs something.

### FN: 68952e4476e4-F01-H01 / R2 / supports

Observability granularity/reference tension

The new aggregate Pod state metric omits the fixed each-container-resource explanations and Events. Do not manufacture these missing qualifications to obtain a full observability relation.

### FN: 964260d9c2da-F01-H04 / I1 / supersedes

Confirmed proof-routing defect

The model emitted the correct qualified replacement. Removed allocated-status proof is local; the affirmative checkpoint/optional-alpha replacement is added current context in the same exact hunk. The old gate looked only at after_line_handles and rejected replacement_lacks_both_source_sides.

### FN: 964260d9c2da-F01-H13 / R1 / supports

Substantively rebound predicate evidence

The equality check changes its allocation operand from a status field to the allocated snapshot while retaining the comparison purpose. A substantive rebind can provide qualified current evidence; identifier-only renaming and ordinary dependency use still cannot.

### FN: 964260d9c2da-F01-H14 / I1 / weakens

Cost applicability and authority ambiguity

Alternative API costs, delay, churn and checkpoint risks are discussed. Applicability to the chosen fixed I1 rather than a hypothetical candidate remains ambiguous; no adverse relation should be forced.

## General fixes and retained ambiguities

v4.7 adds the opt-in `event-grounded` profile. It requires a model-assessed
direct contribution classification and safe exact local current predicate
handles for support. A qualified explicit boundary argument is separated from
the cost of compliance; a substantive predicate rebind is separated from mere
renaming and consumer use. These semantic checks remain fallible model
assessments, not a deterministic entailment proof.

The confirmed routing defect is fixed narrowly: an adopted explicit mechanism
replacement can obtain new-side proof from added current context in the same
exact artifact. Removed-only context, unrelated sibling proof, proposals,
unknown authority, scope mismatch and unsupported whole-element claims cannot
use this path. Historical profiles preserve their original behavior.

Fixed S0, frozen Gold, the exact-triple scorer and historical results are
unchanged. No case identifiers or expected relation table determine runtime
decisions. The two interim I2 restrictions, observability granularity, evidence
freshness, downstream reporting scope and alternative-cost applicability are
disclosed rather than repaired by changing reference answers. v4.7 hosted F1
must be measured after a real run; replaying selected old assessments only
tests source guards and cannot establish new prediction accuracy.

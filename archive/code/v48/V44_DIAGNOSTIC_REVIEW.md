# Supplied v4.4 run: diagnostic review

This document analyzes development run `472626dc-dd7c-48c5-8a94-3420bb8c4ef4`.
It does not replace the frozen reference or constitute a new performance result.
No hosted provider was called during this review.

The diagnostic archive SHA-256 is
`2e1a3c92870eaf4a8583184b2c368bdcde4d9f7f8bc864d0aeafd4ec747ec0e7`.
The report bytes match the supplied receipt. The local v4.4 Python core matches
the receipt's tested hash. The checkpoint report equals the uploaded report,
and its initial state equals the supplied runtime S0. The upload omitted the
preparation manifest and run manifest, so their declared receipt digests could
not be independently checked from these seven files alone.

## Actual performance

| Scope | TP | FP | FN | Precision | Recall | F1 |
|---|---:|---:|---:|---:|---:|---:|
| Baseline | 3 | 11 | 11 | 0.214286 | 0.214286 | 0.214286 |
| All | 6 | 15 | 13 | 0.285714 | 0.315789 | 0.300000 |

All 30 scored hunks were read and received self-reported consideration of all
18 fixed S0 elements. Thirty-five candidates reached judging; 21 were accepted
and 14 semantically rejected. The checkpoint records zero technical failures.
Ten requests produced ten responses, without an observed retry or truncation.
Input usage was 79,257 estimated tokens and 59,423 provider-reported tokens;
provider-reported output was 23,640 tokens. These are different accounting
measures, not interchangeable billing estimates.

The overall review stopped at six rounds. Twenty-three captured commit records
remained unreviewed, but **none of the 13 scored false negatives was unread**.
The empty original-rationale evidence and two citation gaps independently
justify an unresolved review. More reads alone cannot repair these errors.

## All 13 false negatives

| Exact pipeline stage | Count |
|---|---:|
| Expected relation never proposed; another relation proposed | 9 |
| Expected target never proposed; another target proposed | 2 |
| Exact expected proposal semantically rejected | 2 |
| Missing source review or technical failure | 0 |

Seven baseline mechanism replacements were labeled weakening. Two interim
policy changes were labeled support. The two target substitutions concerned
aggregate status telemetry and a retained three-way resource distinction.
The two exact rejections concerned a phase-qualified mechanism replacement
and engineering tradeoffs discussed in an alternatives section.

## All 15 false positives

The following diagnoses are source-grounded analysis, not adjudicated new labels.

| Hunk | Accepted target/relation | Diagnostic finding |
|---|---|---|
| 04de3dac4669-F01-H01 | I2/supports | Appending policy entries is absent from the fixed target; interim reference mismatch. |
| 079aa5fb9ab1-F01-H02 | I2/supports | New-resource policy coverage is absent from the fixed target; interim reference mismatch. |
| 079aa5fb9ab1-F01-H03 | C2a/supports | The QoS invariant was already true before the edit; an existential rephrasing also narrows a non-goal. |
| 079aa5fb9ab1-F01-H05 | G1/supports | A tentative workload-resize sketch was treated as positive goal evidence; discussion policy needs explicit scope. |
| 68952e4476e4-F01-H04 | R1/supports | A chosen reporting representation was mapped to a broader requirement; potentially an additional relation requiring adjudication. |
| 68952e4476e4-F01-H06 | I1/weakens | An outage caveat assumes a freshness guarantee absent from the target. |
| 68952e4476e4-F01-H06 | I3/supports | Operational waiting/tracking was promoted into support for a named state model. |
| 68952e4476e4-F01-H06 | R2/weakens | Accuracy during an outage was substituted for the actual explanation/Event requirement. |
| 964260d9c2da-F01-H03 | I1/weakens | A qualified ordinary-mechanism replacement was called reduced justification. |
| 964260d9c2da-F01-H04 | R1/supports | A preserved distinction was promoted into fresh support. |
| 964260d9c2da-F01-H05 | I1/weakens | Optional legacy retention was mistaken for absence of a scoped replacement. |
| 964260d9c2da-F01-H06 | I1/weakens | The ordinary status-reporting path changed; an optional legacy path still survives. |
| 964260d9c2da-F01-H06 | R1/supports | The whole three-way distinction already held before the change. |
| 964260d9c2da-F01-H08 | I3/supports | State names already existed; resource-accounting behavior changed. |
| 964260d9c2da-F01-H14 | R1/supports | Conceptual alternative-API support can coexist with adverse design tradeoffs; reference policy ambiguity. |

Twenty of 21 accepted links were partial claims. All six true positives were
partial too; the sole whole-element acceptance was false positive. Removing all
partial support would discard correct evidence and would not fix this problem.

## Generic repairs in v4.5

- Optional nomination identifies possible elements without choosing a relation. The
  source-complete classifier reviews every supplied artifact against every actual
  S0 element, including artifacts with no nominations. It can recover a missing
  target and choose a relation without seeing a proposed relation/confidence.
- Hosted nomination is disabled in the default profile. It was consuming
  roughly 42% of estimated input while only identifying the audit origin of
  targets; its output never enters the classifier. Removing those requests
  preserves the classifier's source/target access and creates retry headroom.
- Every emitted relation identifies a verbatim S0 proposition and exact
  source-owned local evidence lines. Before/after claims, target effect and
  qualifications become reviewable fields. Exact span checks validate
  attribution; entailment and complete qualifier preservation remain fallible
  model judgments.
- Relation selection separates replacement of a chosen mechanism from reduced
  feasibility or justification. Replacement of the ordinary/default path can
  be partial and qualified while an optional legacy path remains; it does not
  imply global deletion or deployment.
- A retained premise, operational detail or hypothetical benefit is separated
  from newly contributed rationale. A discussion can provide a direct argument
  or tradeoff without proving implementation adoption. Whole-element support
  still requires every material clause.
- The independent classifier uses the parent linker's configured model by
  default, replacing the parent's separately configured judge. This is an
  explicit development configuration change, with potentially different cost
  and latency. Semantic improvement must be measured; it is not presumed.

## Reference-policy tensions retained

Two INTERIM_2024 I2/supersedes labels concern mutability restrictions absent from
the original fixed I2. A fixed-state runtime must not manufacture those clauses.
Another reference accepts support from a preserved three-way distinction; this
conflicts with a strict fresh-change contribution policy. Aggregate telemetry
also differs from per-resource explanations and Events. Additional conceptual
discussion relations may be semantically plausible but absent from a reference
row's selected targets. These cases remain visible for separate human review.

No label row, runtime S0, prior report or scoring rule has been altered. The
reference examples informed this development version. Its new F1 and any
generalization claim require real hosted runs and independent evaluation.

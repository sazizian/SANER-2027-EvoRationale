# Actual v4.5 run: diagnosis and v4.6 development rationale

The supplied run e98cc3a9-fe80-4db8-99d9-cc23a64c115f completed successfully.
Its baseline exact-triple score is TP4 / FP0 / FN10, F1 0.444444.
Its all-scope score is TP4 / FP0 / FN15, F1 0.347826.
The v4.4 all-scope result was TP6 / FP15 / FN13, F1 0.300000.

All 30 captured diff hunks were read and independently assessed against all 18
actual S0 elements. Six hosted classifier requests completed. The classifier
emitted only four positive effects, all accepted. No emitted effect was rejected
by semantic gates, and no technical/schema failure or retry was recorded.
All 15 false negatives are model no-relation decisions on reviewed sources.
Estimated input was 49,053 of 100,000; provider-reported input/output were
36,491 / 8,520. Increasing read or input limits alone does not address these
omissions. Six investigation rounds were used; 23 commit-metadata records remain
unreviewed. Raw provider responses/finish statuses are absent from the bundle;
strict complete parsed coverage passed and no truncation failure surfaced.

The four correct v4.5 links are new I1 supersession links. None of the six correct
v4.4 links survived. Precision improved by eliminating incorrect links, while
support for new instrumentation, newly explicit documentation and qualified
policy sketches was lost. This is a semantic-contract regression, not uniform
improvement across evidence types.

The v4.5 prompt required a novel TARGET-LOCAL architectural change. The model
used that requirement to reject current documentary evidence for an existing
claim and to reject local consumer migrations as unrelated to an explicitly
changed same-event reporting contract. v4.6 adds an opt-in event-evidence policy
that separately asks what current evidence supports and what architecture changes.
It retains exact fixed-S0 propositions and source-owned citation identities.
Positive support is source-statement evidence, not deployed-behavior validation.
Dependent migration must have old/new local proof plus explicit same-event
contract replacement evidence. Prospective discussion is qualified and partial.
Unchanged incidental text, formatting-only edits, bare labels and unrelated
implementation details remain insufficient evidence.

Two INTERIM_2024 expected I2 supersession labels concern mutability restrictions
that fixed I2 does not assert. Neither the S0 nor those labels is edited or
invented. Aggregate Pod-level telemetry versus R2 per-container-resource
explanations/Events, retained invariants versus documentary clarification, and
costs of unchosen representations versus the actual chosen design also require
careful interpretation. These are disclosed reference-contract tensions, not
authorization to relabel inputs or force runtime predictions.

UNRESOLVED is also explained by unresolved central needs, two screened citation
coverage gaps, unreviewed metadata, absent original rationale evidence, and the
round cap. The code must not hide these gaps to produce a favorable outcome.
A zero unsupported-claim rate describes four accepted extractive claims; it
does not measure recall or certify whole-element coverage.

All nine diagnostic snapshot hashes, receipt/manifest/checkpoint identities,
53 source-specific hashes, and the v4.5 code identity were verified. Actual
runtime S0/input bytes and historical outcomes remain unchanged. The exact-triple
scorer stays byte-identical. The accompanying detailed reports trace each FN and
record runtime evidence. Development examples inform fixes; they are not held-out
performance evidence. No hosted v4.6 F1 is available at package construction.

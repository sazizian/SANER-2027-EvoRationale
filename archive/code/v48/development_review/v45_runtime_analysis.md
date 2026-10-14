# v4.5 actual-run runtime diagnosis

Run `e98cc3a9-fe80-4db8-99d9-cc23a64c115f`; profile `event-delta`, nomination `none`, independent classifier `gpt-6.1-sol`. Hosted execution lasted 159.97 seconds.

## Finding

The low recall is not a transport, JSON/schema, citation-verifier, or missing-hunk failure. All 30 captured diff hunks were read and independently reviewed against all 18 fixed-S0 elements. The classifier generated four relations (I1 supersedes from H03–H06 in event 964260d9c2da); all four passed. The other 26 hunks received model `no_material_relation` verdicts. All 15 exact-match false-negative link triples belong to already reviewed hunks with those no-relation verdicts. No generated effect was discarded by a downstream gate. Increasing token/read/round limits alone therefore cannot recover these existing false negatives.

## Runtime and budget

- Six event/file batches: 14, 6, 5, 1, 2, 2 hunks; six queries and rounds.
- Six provider requests and responses with usage, one successful classifier call per batch; zero nomination API calls.
- No recorded structured-output retry, technical verification failure, semantic gate rejection, verifier feedback, or repair attempt.
- Estimated request-envelope input 49,053 / 100,000; provider input 36,491 and output 8,520 (45,011 total). Estimates are not tokenizer/billing numbers.
- Per-request output ceilings 10,200; 5,400; 4,800; 4,096; 4,096; 4,096. Actual output 4,448; 1,131; 1,585; 558; 461; 337.
- No truncation failure surfaced; complete batch coverage passed the strict contract. The bundle stores parsed reviews and usage, not raw provider JSON/status/finish-reason, so direct finish-status audit is unavailable. The implementation accepts final completed responses and retries incomplete/invalid ones.
- v4.4 used 10 calls, 59,423 provider input and 23,640 output tokens. v4.5 reduced calls 40%, reported input 38.59%, and output 63.96%. This is a descriptive token comparison, not a dollar-cost or equal-model comparison.

## Coverage and unresolved outcome

The eligible source pool contains 53 records: 30 diff hunks and 23 commit metadata records. Selection prepared 36 records; the sixth-round cap stopped after all 30 diff hunks, before six selected metadata records. All 23 metadata records remain unreviewed. The stopping marker `event_round_limit` is real, but none of the scored false negatives is an unread source.

All 30 reviews report full context and all 18 element IDs. Two hunks (`68952e4476e4-F01-H05`, `079aa5fb9ab1-F01-H05`) have code-owned incomplete citation coverage because policy screening redacted material; the no-relation model verdict does not repair these gaps.

Only I1 has adverse evidence. Required elements G1, R1, A1, Q1, I2 remain unresolved. Original rationale `original_evidence` is empty. Unreviewed metadata, two citation gaps, unresolved central coverage, absent original rationale, and the forced round stop all independently explain `UNRESOLVED`/`REVALIDATE`. `AWAITING_HUMAN_REVIEW` is the intended model-assisted output state. The unsupported-claim rate 0 applies only to four accepted claims; it does not measure recall or whole-element support. All four accepted claims are qualified material subclaims.

The zero `proposal_count`, empty `reviewed_proposals`, and trace `nomination_only: true` describe the deliberately disabled nomination stage, not absence of independent review. Four effects are recorded as `independent_recovery`.

## Integrity

All nine snapshot file hashes match the diagnostic bundle manifest. Receipt hashes for preparation, run manifest, report, and checkpoint match. Models, profile, nomination mode, budgets, input hashes, run ID, and code identity are consistent. Checkpoint report and normalized initial S0 exactly equal the supplied report and runtime S0. All 53 source-specific artifact digests validate (diff hunks hash body; metadata uses the existing source-specific digest contract). Local v4.5 core Python hash exactly matches `e53412024165759b0dec7c6e45556f6857fca39674faf119acf1290f512f5afd`. Inputs equal the declared v4.4/original digests. Frozen reference content and older complete manifests are not in this bundle, so their identities are pins rather than a fresh full verification here.

## Next implementation direction

Review the semantic definition of a target-local change versus post-S0 evidence. The actual classifier frequently treats consumer changes, instrumentation, documentary operationalisation, and discussions as out of scope, even where the exact-reference policy marks relations. Keep mechanical source/quote checks, current fixed-S0 boundaries, and original/interim distinctions intact. A bounded second independent review can address ambiguous rejected semantic cases, with detailed provenance; do not copy reference labels or overwrite the fixed S0 to inflate recall. Preserve abstention for unsupported interim-target claims.

Structured per-FN trace and all request usage are in `runtime_analysis.json`.

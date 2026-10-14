# EvoRationale v4.3 validation report

- Runtime: Python 3.12.14 on Linux; pytest 9.1.1.
- Final full-suite result: **163 passed** (140 inherited, 23 additional).
- 20 generic diff/scope contract checks; 3 synthetic preparation/scoring integration checks.
- Source tree SHA-256: `b53989d04604b68d76eddd92412db89b0b33025637e42649abda27714ee53d94`.
- Parent v4.2 source remains unchanged at `ab892cc339348fc6db243ecbdb18cb6df3a4959d5636332d5f2cdb7945fbdd09`.
- Exact-triple `_score_core.py` is byte-identical to the parent package.
- All 30 canonical captured input hunks produced complete before/after views;
  there were no line-count or context-bound failures on these inputs.
- The no-API helper was exercised end to end against synthetic hashed receipts:
  tests, preparation, opaque model-ID reuse, input hash checks, and dry run.
  Source experiments/reference files were unchanged; no run or checkpoint was created.
- Additional tests confirm that altered old configurations and altered new input
  bytes stop preparation/dry run, and that simulated post-run scoring preserves
  the previous population and score files.
- The final version metadata and pinned source hash were updated before the final
  full test-suite run. The helper's behavior was checked separately before that
  metadata-only update.

## Limits

No hosted v4.3 experiment was run, and no real-model F1 improvement is claimed.
Test-controlled model replies establish code gating and input preservation, not
real-model semantic accuracy. Synthetic completed receipts are test fixtures,
not experimental evidence. These changes were informed by inspected development
labels and failure cases; a new held-out evaluation is necessary for generalization.
Windows execution of the provided commands remains to be confirmed on the user's
machine. Added context can increase token consumption in a later hosted run.

# Candidate Package Verification Report

- Existing baseline README SHA-256: MATCH (2023 fixed commit).
- Existing KEP YAML SHA-256: MATCH.
- Original S0 candidate statements: 12.
- Atomic candidate S0 statements: 18 (G3 -> 3 and C2 -> 5).
- Commit screening reference rows: 23.
- Selected event reference rows: 4.
- Hunk reference rows: 30, all checked against the original stored patch-hunk SHA-256.
- Evidence input records: 53, with no reference judgments provided in their content.
- Candidate positive reference relation triples: 19; 14 excluding interim-only changes.
- Workbook scan: no Excel formula error tokens detected.
- Retrospective development test of v4.1: `validate PASS (53)`; run completed `REVALIDATE / UNRESOLVED`, not a scientific accuracy claim.
- Reviewer signature status in supplied workbooks: NOT DOCUMENTED.
- Historical replay certification: NO.
- Outcome-level reference labels: UNAVAILABLE.

Run `python scripts/verify_candidate.py` after extracting.

# EvoRationale - KEP-1287 Consensus Candidate and Evaluation Preparation

**English-only research files.** The project's software in Cursor is not modified by this packet.

## What is in this packet?

- `benchmark_inputs/S0_ATOMIC_CANDIDATE_UNAPPROVED.json`: 18 atomic decision elements derived from 12 original KEP-1287 elements; **human_approved=false**.
- `benchmark_inputs/S0_RUNTIME_RETROSPECTIVE_UNAPPROVED.json`: alternate analysis cutoff for a *retrospective exploratory* run only. It is **not historical-replay certified** and remains unapproved.
- `benchmark_inputs/POST_S0_EVIDENCE_RETROSPECTIVE_53.jsonl`: 23 Git commit metadata records and 30 verbatim patch hunks. This file contains **no reviewer reference labels**.
- `reference_private/`: PI-reported consensus *candidate* reference tables (18 S0 statements; 23 screening records; 4 selected events; 30 patch hunks). Never pass this directory to the agent or retrieval index.
- `audit/`: the source workbooks received in the conversation, provenance notes, and readiness flags.
- `sources/`: immutable baseline markdown/YAML and the four captured diff JSON files for source inspection.
- `scripts/`: integrity checks, sign-off workflow, and optional candidate relation scoring.
- `docs/`: a data dictionary and evaluation protocol.

## Study boundary

Pinned baseline: `5950905de89aab2be202d28b823701276cbefea0`, 2023-10-26.
Event screening window end (exclusive): 2024-10-11T00:00:00Z.
Retrospective retrieval/capture timestamp: 2026-10-11T00:48:50Z.

Do **not** use today's GitHub file contents as though they were available at the baseline. The generated histories preserve each commit's recorded time separately from the time its immutable object was actually retrieved/audited. This is not a certified historical replay.

## Scientific status

The PI reported that two human reviewers personally inspected the consensus outcomes without AI judgment and agree that commit `d7b996f...` also relates to `I1`. The uploaded reconciliation source nevertheless contains `AI proposal`, `PENDING`, and one new-evidence item. This packet preserves both facts without rewriting the source workbooks. Independent signed approvals or archived correspondence are not in the supplied files. Accordingly, labels here are *candidates*, not publication-ready Gold.

The event relation labels are SUPPORTS, SUPERSEDES, etc., but `SUPERSEDES` relative only to an INTERIM_2024 design **must not** be counted as invalidating the 2023 S0. No definitive KEEP/REOPEN/REVISE outcome labels are supplied.

## Next actions

1. Inspect `reference_private/S0_ATOMIC_CANDIDATE.csv` and confirm the seven rewrites, especially the G3 and C2 splits and central-element scope.
2. Preserve reviewer A/B confirmations of **exact wording, mappings, and temporal interpretations** via `reference_private/REVIEWER_CONFIRMATION_TEMPLATE.csv`, including dated email/thread references or minutes.
3. Run `python scripts/verify_candidate.py` to confirm counts, hunk hashes and no leaked gold labels in inputs.
4. Only after independent confirmation is recorded, use `python scripts/freeze_reference.py --confirmations ... --output <new_directory>`.
5. Follow `docs/EVALUATION_PROTOCOL.md` before running or reporting any model comparisons. Do not report current data as generalizable SANER benchmark metrics.

All research files remain in English; reviewer identities can stay coded A and B publicly.

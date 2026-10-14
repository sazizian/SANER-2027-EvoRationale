# Evaluation Protocol - KEP-1287 (Pre-Registered Working Draft)

## Research questions

- RQ1: Can EvoRationale locate and attribute post-S0 change evidence to documented S0 elements?
- RQ2: Can it classify the relationship correctly (supports/weakens/contradicts/supersedes) without confusing code existence and design validity?
- RQ3: Can it distinguish changes to an intermediate 2024 design from changes to the pinned 2023 design rationale?

## Dataset partitions and non-leakage

- `benchmark_inputs` may be provided to the agent. It has original S0 candidate wording and 53 unlabeled evidence artifacts.
- `reference_private` must **never** be placed in retrieval indices, the model prompt, or agent memory before a run.
- Freeze the code commit, S0 hash, history hash, model/judge names, prompting, token budget, tool version, and random seeds *before* opening reference labels for scoring.
- This single Kubernetes case is a **pilot**. It cannot support repository-disjoint train/test claims, cross-project statistical inference, or claims of broad performance superiority.

## Three different tasks

1. **Screening**: 23 commits. A `NEEDS_DIFF` or `UNCERTAIN` label is an abstention/triage outcome; do not silently convert it into relevant or irrelevant.
2. **Event relationship**: Four selected events with reviewer-assigned relation, S0 ID set, and temporal basis. `INTERIM_2024` changes should not be counted as baseline-2023 drift.
3. **Hunk linking**: Thirty patch hunks. Exact-match triples `(hunk_id, atomic_element_id, relation)` are the primary candidate link-level evaluation. Exclude IMPLEMENTATION_ONLY and UNRELATED from positive reference relations, but retain them as explicit negatives in the evaluated hunk universe.

## Eligibility and coverage

The patch evidence comes from only four curated commits. The other 19 of the 23 timeline commits do not have full patches in this packet. Do not calculate hunk-level recall over unreviewed changes or treat the 30 hunks as an exhaustive repository history.

Because the capture of Git objects was retrospective in 2026, the default runner's first-auditable timestamp is the capture observation time, not an unverified 2024 public-push time. The input `S0_RUNTIME_RETROSPECTIVE_UNAPPROVED.json` extends the *tool* cutoff to the actual capture observation. This is a diagnostic, not a historical-replay result.

## Metrics (after confirmation)

- Hunk-level link/relation: micro precision, recall and F1 from positive exact-match triples, with explicit TP/FP/FN and hunk coverage. Do not inflate performance through repeated links from the same hunk.
- Hunk relevance/relationship classification: confusion matrix, per-label precision/recall/F1 and macro-F1 only if full categorical predictions are available for all 30 hunks.
- Commit screening: agreement with scorable reference labels plus abstention rate and coverage; exclude NEEDS_DIFF/UNCERTAIN from binary denominators and report exclusions.
- Report false-positive relation predictions on UNRELATED / IMPLEMENTATION_ONLY hunks.
- Separate event temporal basis: BASELINE_2023, INTERIM_2024, BOTH. Baseline-only metrics exclude interim-only relation changes and must not infer architectural decision outcome from a SUPERSEDES label.
- No outcome macro-F1 is available: gold decisions of KEEP/REVALIDATE/REVISE/REOPEN were not independently adjudicated.

## Leakage and calibration safeguards

Do not optimize prompts, link thresholds, query selection or S0 wording on these labels and later call the same episode held-out. Preserve pre/post protocol versions and treat iterative runs as development evidence. If formal performance evaluation is desired, collect more repository-disjoint episodes with annotation before looking at predictions.

## Reporting caveat

The PI states two human reviewers reached agreement. The source reconciliation file contains AI-generated proposal annotations and no signed reviewer approvals. Record signed acceptance of exact final 18 S0 elements and maps (or dates/links to correspondence) before reporting this as a gold-standard annotation process.

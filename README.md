# EvoRationale: Code and Development Evidence

EvoRationale investigates how later repository evidence affects the elements of an accepted software-design decision. This repository brings together the pinned v4.9 Python implementation, isolated experiments, historical sources, and preserved pilot records for use in Cursor and GitHub.

The central [data directory](data/README.md) organizes the available inputs, captured GitHub resources, Excel workbooks, scoring references, results, and validation records. Current instructions and guides are written in English.

**Evidence status:** The manuscript table supplied for this README reports public-case exact-triple F1 scores of **0.686, 0.718, and 0.722**. These values are arithmetically consistent with that table's TP, FP, and FN counts. The earlier README reports different FP counts for the same named configurations; see [Score provenance and reconciliation](#score-provenance-and-reconciliation). This documentation update does not establish which counts match the archived predictions and scorer.

**Fresh-run status:** The supplied snapshot lists the **Fresh Primary Effects Windows Fix** result as **pending**. The operator-reported Windows preflight passed 98 tests and 6 subtests in 54.19 seconds. Its local forecast planned 12 fresh classification requests and no independent critic. These checks and forecasts do not measure F1.

## Start Here

- [English quickstart](docs/QUICKSTART_EN.md)
- [Windows setup, verification, and manual GitHub publishing](docs/WINDOWS_GITHUB_GUIDE_EN.md)
- [Evidence files, run IDs, and provenance](docs/EVIDENCE_GUIDE.md)
- [Data folders, Excel resources, and file inventory](data/README.md)
- [How to use this evidence in the paper](docs/PAPER_EVIDENCE_GUIDE.md)
- [Primary Effects Windows Fix](experiments/primary_effects_windows_fix/README_START_HERE_EN.md)
- [Historical cached scope recheck](experiments/scope_recheck/README_START_HERE_EN.md)

## Repository Map

| Path | Content |
|---|---|
| `evorationale/` | Pinned v4.9 runtime; project version `4.9.0.dev0` |
| `tests/`, `development_tools/`, `examples/` | v4.9 tests, helpers, and original runnable examples |
| `experiments/primary_effects_windows_fix/` | Fresh primary-effect projection, pinned baseline context, and Windows checkpoint repair |
| `experiments/scope_recheck/` | Historical cached-v4.9 checker experiment |
| `tools/` | Export-integrity checks, result verification, and test/forecast orchestration |
| `data/README.md` | Guide to data and resource categories |
| `data/RESOURCE_INDEX.json`, `data/RESOURCE_INDEX.csv` | Resource catalog, source paths, purposes, and checksums |
| `data/inputs/kep1287/` | Canonical fixed runtime S0 and all 53 post-S0 history artifacts |
| `data/github/` | KEP 1287 and Azure source captures, diffs, metadata, and `GITHUB_SOURCES.csv` |
| `data/excel/` | Nine workbook files representing eight distinct byte identities, including supplied, review, and separate pilot resources |
| `data/reference_candidates/` | Earlier annotation candidates, source indexes, and audit resources |
| `data/resources/original_workspace/` | Uploaded workspace research, documentation, and example outputs |
| `data/examples/`, `data/baseline_context/` | Azure/Redis examples and the pinned public baseline README |
| `data/results/runs/` | Supplied run records for v4.4–v4.9 and the scope recheck |
| `data/results/index.json` | Evidence index, hashes, metrics, coverage, and limitations |
| `data/results/summary.json`, `data/results/summary.csv` | Existing comparison summaries; check their scoring provenance before citing |
| `data/results/validation/` | Local test, forecast, replay, and export checks; not new hosted accuracy results |
| `data/references/frozen_reference/` | Frozen scoring reference, separate from model input |
| `archive/original_v41_workspace/` | Historical workspace with English documentation and preservation mappings |
| `archive/code/`, `archive/release_packages/` | Historical source and code-release ZIP copies with English documentation and test fixtures |
| `data/packages/diagnostics/` | Supplied diagnostic ZIPs |
| `docs/` | Current guides and identified historical material |
| `figures/` | Development-metrics figure and regeneration code; reconcile with the chosen score source |

## What the Public Evaluation Measures

The public KEP 1287 development case evaluates evidence-to-rationale links. Under the exact-triple definition in the supplied manuscript table, a predicted link is correct only when its **artifact, target, and relation** match a reference triple. Each distinct triple is counted once.

The full evaluation covers **30 patch hunks** and **19 positive reference triples**. A patch hunk is a block of changes in a diff. Hunks are the inspected units, while triples are the scored links: the number of hunks is not the denominator for Precision or Recall.

This case was inspected during development. Its results are development evidence, not an independent held-out evaluation.

### TP, FP, and FN

| Term | Meaning |
|---|---|
| **TP — True Positive** | A distinct predicted link that matches a reference link |
| **FP — False Positive** | A distinct predicted link that does not match a reference link |
| **FN — False Negative** | A reference link that the system did not predict correctly |

An unmatched prediction is an error relative to the scoring reference. If it uses the wrong target or relation, it can produce an FP while the intended reference triple remains an FN.

### P — Precision

Precision asks: **Of the links the system predicted, what fraction matched the reference?**

```text
P = TP / (TP + FP)
```

Higher Precision means fewer unmatched predictions relative to the number of predicted links.

### R — Recall

Recall asks: **Of the links in the reference, what fraction did the system find?**

```text
R = TP / (TP + FN)
```

Higher Recall means fewer missed reference links.

### F1 — F1-Score

F1 combines Precision and Recall using their harmonic mean.

```text
F1 = 2 × P × R / (P + R)
F1 = 2 × TP / (2 × TP + FP + FN)
```

Scores range from 0 to 1, with higher scores indicating better performance under this evaluation. F1 is not the arithmetic average of P and R, is not classification Accuracy, and does not establish architectural correctness or deployment success. All rows reported below have nonzero denominators.

## Manuscript-Reported Public Development Results

The following values reproduce the supplied manuscript table. P, R, and F1 are recalculated directly from its counts and rounded to three decimal places.

| Configuration | TP | FP | FN | P | R | F1 |
|---|---:|---:|---:|---:|---:|---:|
| v4.6 evidence trace | 12 | 4 | 7 | 0.750 | 0.632 | 0.686 |
| v4.9 pair review | 14 | 6 | 5 | 0.700 | 0.737 | 0.718 |
| Cached scope recheck | 13 | 4 | 6 | 0.765 | 0.684 | 0.722 |


For each completed row, `TP + FN = 19`, matching the stated number of positive reference triples.

### Worked Calculations

| Configuration | Precision calculation | Recall calculation | F1 calculation |
|---|---|---|---|
| v4.6 evidence trace | 12 / (12 + 4) = 0.750 | 12 / (12 + 7) = 0.632 | 24 / (24 + 4 + 7) = 0.686 |
| v4.9 pair review | 14 / (14 + 6) = 0.700 | 14 / (14 + 5) = 0.737 | 28 / (28 + 6 + 5) = 0.718 |
| Cached scope recheck | 13 / (13 + 4) = 0.765 | 13 / (13 + 6) = 0.684 | 26 / (26 + 4 + 6) = 0.722 |

For example, v4.6 predicted 16 distinct links, of which 12 matched the reference. Its Precision is therefore 75%. It recovered 12 of the 19 reference links, giving Recall of approximately 63.2%. Their harmonic mean gives F1 of approximately 0.686.

The cached recheck has the highest F1 in this supplied table, while v4.9 pair review has the highest Recall. These are descriptive comparisons on one development case.

## Baseline F1, All F1, and Run Names

### Baseline F1 and All F1

These labels identify **evaluation subsets**, not different definitions of F1.

| Label | Evaluation scope | Positive reference triples |
|---|---|---:|
| **Baseline F1** | Original annotation subset covering 24 hunks | 14 |
| **All F1** | Full evaluation covering 30 hunks | 19 |

In this context, **Baseline F1 does not mean the score of a separate baseline model**. Both subsets use the same F1 formula with their own TP, FP, and FN counts.

The manuscript-reported table above uses the full 30-hunk, 19-positive scope. The FP counts in that table do not supply enough information to derive new Baseline scores.

### Cached-v4.9 Scope Recheck

This experiment reuses the stored primary predictions from v4.9 and checks their scope. It is not a completely independent fresh execution of the entire prediction pipeline. Reusing primary predictions does not imply that every subsequent checking step required no computation or model calls.

### Fresh Primary Effects Windows Fix

This is a separate experiment that introduces pinned public baseline excerpts, focuses on primary effects separately from secondary traces, and includes a Windows checkpoint repair. It changes inference inputs and the prediction view while retaining the numeric scoring formula described in the supplied documentation.

The result is **pending in the supplied snapshot**. A passing preflight, unit tests, or a forecast of planned requests cannot substitute for completed predictions and scored results.

## Score Provenance and Reconciliation

**The supplied manuscript table and earlier README disagree about FP counts.** Their TP and FN counts match for the three compared configurations, but their FP counts and resulting F1 scores do not.

| Configuration | Manuscript FP | Earlier README All FP | Manuscript F1 | Earlier README All F1 |
|---|---:|---:|---:|---:|
| v4.6 | 4 | 7 | 0.685714 | 0.631579 |
| v4.9 | 6 | 11 | 0.717949 | 0.636364 |
| Cached scope recheck | 4 | 11 | 0.722222 | 0.604651 |

Both sets of F1 values are mathematically consistent with their respective counts. Arithmetic alone cannot determine which set matches the intended evaluation. The difference cannot be explained as rounding.

Before treating one set as the definitive repository result:

1. Identify the exact prediction files, frozen reference, evaluator version, and evaluation subset for each run.
2. Check the artifact–target–relation matching rules, duplicate handling, and inclusion or exclusion rules.
3. Recompute TP, FP, and FN from those inputs and inspect the corresponding error rows.
4. Record the reason for any difference and update the manuscript, summaries, figures, and evidence guide from the same scoring output.

Do not change predictions, reference labels, or historical records merely to match a preferred table. This README update checks the supplied arithmetic; it does not rerun the scorer or establish the cause of the discrepancy.

### Earlier README Snapshot

The following values preserve what the earlier supplied README reported. They are retained for traceability and must not be presented as interchangeable with the manuscript-reported table above.

| Run | Baseline TP / FP / FN | Baseline F1 | All TP / FP / FN | All F1 |
|---|---:|---:|---:|---:|
| v4.4 | 3 / 11 / 11 | 0.214286 | 6 / 15 / 13 | 0.300000 |
| v4.5 | 4 / 0 / 10 | 0.444444 | 4 / 0 / 15 | 0.347826 |
| v4.6 | 10 / 5 / 4 | 0.689655 | 12 / 7 / 7 | 0.631579 |
| v4.7 | 2 / 6 / 12 | 0.181818 | 5 / 6 / 14 | 0.333333 |
| v4.8 | 10 / 7 / 4 | 0.645161 | 12 / 9 / 7 | 0.600000 |
| v4.9 | 12 / 10 / 2 | 0.666667 | 14 / 11 / 5 | 0.636364 |
| Cached-v4.9 scope recheck | 12 / 10 / 2 | 0.666667 | 13 / 11 / 6 | 0.604651 |

The earlier README states that these rows were reproduced with the unchanged v4.9 evaluator. That execution claim has not been independently reverified for this documentation update. It also identifies v4.4 as having a flat diagnostic layout and partial receipt-linked provenance, with missing original records described in the evidence guide.

## Local Verification

Python 3.11 or newer is required. Follow the [Windows guide](docs/WINDOWS_GITHUB_GUIDE_EN.md) to create the environment and define `$pyRepo` and `$repo`, then run:

```powershell
& $pyRepo "$repo\tools\verify_bundle.py"
& $pyRepo "$repo\tools\run_local_checks.py"
```

According to the supplied documentation:

- The first command checks the exported file manifest and recorded results without an API call.
- The second runs the active runtime tests, both isolated experiment test suites, and local forecasts.
- Top-level verification does not need an API key.
- Historical release logs remain separate from newly executed export checks.

Passing tests or mock forecasts is not a semantic accuracy result. Byte verification does not independently authenticate provider execution or reviewer identity.

The pending Primary Effects run should finish in its existing location. Do not replace that output or repeat paid inference just to populate the export. Its guide documents separate API commands, consent flags, budgets, and scoring.

## Scientific Boundaries

- The supplied export documentation states that fixed S0 and all 53 history inputs retain their original bytes. Reference labels and notes are used for post-run scoring, not passed to the model.
- The reference has been inspected during development, so this public case is not held out.
- The 30 planned hunk review records and 53 history artifacts refer to different units. Structural coverage does not establish complete semantic review of the history.
- Versions differ in policies, models or call patterns, and resource settings. These are descriptive development comparisons, not equal-compute experiments.
- Matching opaque model IDs do not establish immutable provider snapshots.
- Source, schema, and provenance checks do not prove model interpretations, architectural suitability, or deployment success. This reference has no architecture-outcome gold standard and does not certify historical replay.
- These public pilot logs do not establish the archived manuscript's broader industrial-study claims. Public and industrial results have different scopes and endpoints and should be reported separately. See the [paper guide](docs/PAPER_EVIDENCE_GUIDE.md) and [source audit](docs/audits/github_source_audit.md).

## Preservation and Attribution

Historical resources retain their release-time claims and provenance. The supplied documentation describes historical code-release ZIPs as English adaptations rather than byte-identical originals. `docs/ARCHIVE_LANGUAGE_ADAPTATIONS.json` records original and adapted archive hashes and member changes.

The supplied export states that production runtime code, fixed inputs, frozen scoring data, and recorded results preserve their original bytes. Use the manifest for the corresponding export snapshot; historical `SHA256SUMS.txt` files describe their dated releases rather than adapted copies. This README itself is a new documentation revision, so an earlier manifest may report it as changed.

An Excel workbook is a supplied resource, not automatically the frozen scoring reference. The scoring reference is identified under `data/references/frozen_reference/`. Other pilot workbooks are under `data/excel/source_pilot_workbooks/`; their repository cases are separate from the KEP 1287 scoring reference.

Keep the supplied `.gitattributes` setting (`* -text`) and set repository-local `core.autocrlf=false` before staging, as described in the Windows guide. Avoid normalizing pinned source or historical record bytes. Use new folders for new runs and preserve old metrics.

The top-level license applies to author-owned implementation material. Captured third-party source retains its applicable attribution and rights; the project's license does not relicense it. Consult `LICENSE`, `NOTICE.md`, and source URLs and hashes in the evidence records. Cite a fixed commit or release after the method and reconciled evidence are frozen.

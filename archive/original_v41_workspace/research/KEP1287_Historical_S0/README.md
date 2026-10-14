# EvoRationale research case: Kubernetes KEP-1287

**Status: historical source-capture and rationale-screening package (English-only).**

This research package is intentionally separate from EvoRationale application code and from the Azure PR-1803 pilot. It does **not** modify approved S0 files, GitHub datasets, previous experiments, installed Python environments, or API keys.

## What this package establishes

The historical Git commit `5950905de89aab2be202d28b823701276cbefea0` (October 26, 2023) contains a version of KEP-1287 that discusses the problem, goals, non-goals, API choices and alternatives. Its `kep.yaml` says `status: implementable` and `stage: alpha`. The exact README and YAML Git blob hashes are recorded in `PROVENANCE.json`.

**Important:** The commit date fixes a *historical observation snapshot*, not the actual date of the original architectural decision or its formal approval. Those dates still require research. The first bounded follow-up window ends October 11, 2024. The four shortlisted commits are candidate change events, not known rationale drift.

## Contents

- `S0_KEP1287_2023_DRAFT.json`: unapproved, source-linked S0 candidate compatible with the existing EvoRationale state schema.
- `S0_RATIONALE_CANDIDATES.csv`: paraphrased, source-anchored candidates for human screening.
- `POST_S0_COMMIT_CANDIDATES.csv`: four sourced and dated design-change candidates for follow-up.
- `PROVENANCE.json`: immutable refs, reported status/stage, known limitations.
- `scripts/capture_kep1287.py`: Python-standard-library capture of the **actual historical source bytes** and a bounded Git commit history. The script verifies blob hashes, verifies curated commit SHAs against the README history, saves changed-file patches, and generates a capture manifest.
- `tests/test_capture_kep1287.py`: small offline unit tests for safety-critical hash and timeline handling.
- `REVIEW_PROTOCOL.md`: annotation and validity rules.

No complete copy of the copyrighted upstream KEP is redistributed in this ZIP; the collector retrieves the primary-source bytes directly from GitHub into the researcher's own workspace.

## Where to place it

Inside your existing project root (which remains `EvoRationale_PaperAligned_v4` with the v4.1 patch installed), extract the ZIP into `research/`. The resulting folder must be:

```text
EvoRationale_PaperAligned_v4/
  research/
    KEP1287_Historical_S0/
      README.md
      PROVENANCE.json
      S0_KEP1287_2023_DRAFT.json
      S0_RATIONALE_CANDIDATES.csv
      POST_S0_COMMIT_CANDIDATES.csv
      scripts/capture_kep1287.py
      tests/test_capture_kep1287.py
```

## One capture command (PowerShell, from the EvoRationale project root)

```powershell
$env:PYTHONUTF8 = "1"
$py = Join-Path $env:LOCALAPPDATA "er4venv\Scripts\python.exe"
& $py .\research\KEP1287_Historical_S0\scripts\capture_kep1287.py --output .\research\KEP1287_Historical_S0\captured
```

The collector does not use the OpenAI API. It uses the public GitHub REST API and may be subject to GitHub rate limits. If your GitHub API quota is exhausted, you may set a `GITHUB_TOKEN` environment variable **locally**; do not upload or paste that token.

Expected output is JSON with `status: CAPTURED_REQUIRES_HUMAN_ADJUDICATION` and `baseline_verified: true`. The actual number of commits in the window is determined by GitHub. **Do not copy expected numbers from examples.**

The output directory contains:

- `baseline_README_2023.md` and `baseline_kep_2023.yaml`, fetched at the pinned 2023 commit;
- `all_readme_commits_in_window.csv`, covering the bounded path history;
- `selected_events_for_review.csv` and `selected_commit_diffs/*.json`, for a four-event human review;
- `capture_manifest.json`, with Git blob checksums, local SHA-256 checksums, and limitations.

If you rerun the capture, select a *different* `--output` directory; captures are not overwritten.

## Current research limitations

1. Initial approval date and relevant pre-decision discussions have not yet been independently reconstructed.
2. The rationale elements in the S0 file are researcher *paraphrase candidates*, not human-approved quotations or gold labels.
3. Evidence derived from immutable commits should be independently inspected for chronology and scope before any replay benchmark is certified.
4. Finding an implementation change does not itself prove that the architectural rationale remains valid or should be revised.
5. The previous Azure data and EvoRationale implementation remain untouched.

**Next research decision after capture:** review the CSV annotations, audit the four diffs, and select one precise rationale-changing episode. Only then prepare an approved S0 and a time-safe test dataset.

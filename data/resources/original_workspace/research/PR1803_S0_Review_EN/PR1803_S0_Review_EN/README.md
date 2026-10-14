# EvoRationale: PR #1803 S0 Rationale Review

## Purpose

This package is a research-review worksheet for identifying potential **pre-decision design-rationale evidence** in the Azure/Enterprise-Scale pull request #1803 and its review discussion. **It is not a code patch**, an approved S0, a gold-standard dataset, or evidence of successful architectural revalidation.

All file names, data fields, documentation, and prose in this package are in English.

## Where to store this package

Place the extracted `PR1803_S0_Review_EN` folder under the existing EvoRationale project directory:

```text
EvoRationale_PaperAligned_v4/
  research/
    PR1803_S0_Review_EN/
      README.md
      PR1803_rationale_candidates_review.csv
      provenance.json
      LANGUAGE_POLICY.md
```

On Windows, start in the project's root directory. If the downloaded ZIP is in Downloads, you can extract it using:

```powershell
New-Item -ItemType Directory -Force .\research | Out-Null
Expand-Archive -LiteralPath "$env:USERPROFILE\Downloads\EvoRationale_PR1803_S0_Review_ENGLISH.zip" -DestinationPath .\research -Force
```

You may instead use Windows File Explorer to extract the ZIP into `research`. The original code, approved decision states, GitHub snapshots, and experimental outputs do not need to be moved or modified.

## Contents

- `PR1803_rationale_candidates_review.csv`: 13 candidate source records, direct source links, concise English summaries, candidate categories, and relevance assessments. Open with Excel or a CSV-aware editor.
- `provenance.json`: Source and study limitations, original PR merge timestamp, and source-table lineage.
- `LANGUAGE_POLICY.md`: The English-only convention for saved research and code artifacts.

## How these candidates were assembled

The records come from the PR #1803 overview and selected review comments created on January 9, 2025, before the PR merged on January 10, 2025. The dataset preserves source IDs, reported comment-creation times, relevant file paths, and direct GitHub URLs. Summaries are paraphrases; full comment bodies are not reproduced.

The information was gathered from GitHub in October 2026. The exact comment-body versions available immediately before the 2025 merge have **not** been independently certified. Source creation timestamps and present-day source text should not be confused with proof of a historical snapshot.

## Preliminary observations

1. The PR overview describes optional AVNM deployment through ARM and portal templates. This grounds **implementation scope**.
2. Review comments raise specific concerns about Boolean schema simplicity, maintainability, reuse, configuration readability, scope of application, policy provenance, and code cleanup.
3. Those localized considerations do **not** by themselves establish the original requirement for AVNM, alternatives considered, or why AVNM was preferred.
4. The later GitHub evidence and diff excerpts captured in October 2026 are useful for an exploratory implementation-evidence pilot, but have not been certified for historical replay.

## Suggested human review

For each CSV record, open its `source_url` and inspect the full context. Determine whether the content (a) refers to the central architecture decision or a local implementation detail; (b) was available prior to decision acceptance; (c) documents a specific assumption, requirement, trade-off, or design constraint; and (d) is sufficiently explicit and independently supported to become a proposed S0 entry.

The `eligible_for_s0_without_further_review` field contains preliminary **NO** or **REVIEW** decisions, not approval to insert content into S0. Document your final adjudication separately and retain the original evidence.

## Research interpretation

Keep the Azure case labeled as an **exploratory implementation-evidence pilot** unless central architectural rationale is recovered and independently adjudicated. Do not infer a `KEEP` verdict merely because post-decision code demonstrates the AVNM feature. For the principal Design-Rationale Revalidation evaluation, prefer cases with documented pre-decision rationales, alternatives, and independently reviewable post-decision evidence.

This review-only package does not contain the EvoRationale Python source code. The source code remains in the main project directory.

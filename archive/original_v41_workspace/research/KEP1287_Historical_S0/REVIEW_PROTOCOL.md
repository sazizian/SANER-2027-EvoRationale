# KEP-1287: Independent rationale review protocol

## Scope

The research question is whether subsequent artifacts **support, weaken, contradict, or supersede** an accepted design rationale. A passing syntax test or a change in the implementation does not by itself settle this question.

## Source and temporal controls

- Start from the immutable October 26, 2023 KEP revision and verify the two Git blob SHA-1 identifiers.
- Document the **actual** KEP review/acceptance event separately from the chosen observation snapshot. Do not relabel the commit date as the approval date.
- Keep `committer_date`, `capture_time`, `source_url`, `commit_sha`, and the original historical body distinct.
- Check ancestry, amended history, publication timing, and the applicable development stage before certifying historical replay.
- Treat the 2024 commits as candidates, not as preassigned design drift.

## Human S0 review

Each candidate element must be checked against the historical README at the listed section and source URL. Choose an independent verdict: `ACCEPT`, `REWRITE`, `REJECT`, or `NEEDS_CONTEXT`. Record an exact supporting passage in the **private annotation notes** if permitted, but avoid relying solely on the keyword overlap. The alternative designs in the KEP lack a complete comparative rejection rationale; never invent one. Keep unsupported `original_evidence` empty.

## Post-S0 annotation

For each event: record the exact changed hunk, identify the S0 element affected, and choose one of `SUPPORTS`, `WEAKENS`, `CONTRADICTS`, `SUPERSEDES`, `IMPLEMENTATION_ONLY`, or `UNRELATED`. Set `UNKNOWN` whenever documentary support is insufficient. Have at least two independent reviewers adjudicate differences; keep the automated label blind to the reference adjudication.

## Minimum artifact required before running an EvoRationale benchmark

- Human-approved S0 whose temporal provenance is verified;
- bounded, version-specific historical evidence with clearly stated completeness limitations;
- independent gold labels and their adjudication notes;
- fixed retrieval and model budgets for every method compared;
- explicit `historical_replay_certified` flag reflecting documentary evidence, not just a programmatic pass.

This package does not contain such a completed benchmark yet.

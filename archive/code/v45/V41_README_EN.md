# EvoRationale v4.1: Step-by-step guide for the Azure pilot

This is an English translation of the historical v4.1 guide. Its version numbers, instructions, observations, and research caveats describe that release. Use the current repository quick start for current work.

**Version described: 4.1.0rc1, a research and experimental release.** This version was built from v4 and does not guarantee that all evidence, repository history, or architectural correctness has been evaluated.

## Why a new version?

The v4 execution checkpoint showed that G1 and I1b had been resolved, but I1a had been investigated once, I1c had never been investigated, and C1a/C1b remained open. The original 22 records also did not contain the exact string `deployAVNM`, although the actual GitHub diffs contained the parameter definition and deployment conditions. Increasing the API budget alone would not address these gaps.

## v4.1 changes

- `scripts/enrich_azure_pr_diffs.py` reads every PR **already selected in the original manifest**, examines `eslzArm.json`, `eslz-portal.json`, and AVNM-specific files, and stores small diff excerpts containing **added lines**.
- The original set of 22 records and the original S0 **remain unchanged**. The script creates a new output directory and refuses to overwrite an existing directory.
- For new records, `first_auditable_at` is the **actual retrieval time**, not the PR creation time in 2025. The data are **not certified for historical replay**.
- The code-specific gate accepts `I1a` only with an actual `deployAVNM` definition and `type: bool`; `I1b` only with a `Microsoft.Common.CheckBox` control; `I1c/C1a` only with an actual `deployAVNM` condition; and `C1b` only with an actual AVNM dependency. The check operates on added `+` diff lines and does not infer functionality from a filename alone.
- The new `investigation_coverage` report identifies required needs that remain open and those that have never been investigated.
- If S0 has no **central element** relating to assumptions, requirements, initial evidence, or quality attributes, `KEEP` is invalid even if code evidence exists for every implementation component. The result remains `REVALIDATE / UNRESOLVED`.

## Installing the patch on an existing v4 project

Place `EvoRationale_v41_PATCH_TESTED.zip` next to the v4 project's `pyproject.toml`. In a terminal in that directory:

```powershell
Expand-Archive -LiteralPath .\EvoRationale_v41_PATCH_TESTED.zip -DestinationPath .\_v41_update -Force
& $py .\_v41_update\apply_v41_patch.py --project .
& $py -m pip install -e ".[openai,test]"
& $py scripts\verify_release.py
```

If you opened a new terminal and `$py` no longer exists:

```powershell
$py = Join-Path $env:LOCALAPPDATA 'er4venv\Scripts\python.exe'
```

The installer backs up existing files before replacing them. **It does not modify S0, GitHub history, outputs, or your API key.**

## Step 1: Collect public GitHub diffs without the OpenAI API

From the original v4 directory containing `pyproject.toml`:

```powershell
& $py scripts\enrich_azure_pr_diffs.py `
  --decision examples\azure\pilot_snapshot\decision_state_ATOMIC_APPROVED.json `
  --history examples\azure\pilot_snapshot\history_LIVE.jsonl `
  --capture-manifest examples\azure\pilot_snapshot\github_capture_manifest.json `
  --output data\azure-avnm-diff-v41
```

A network connection is required, but an OpenAI key is unnecessary. GitHub rate limits its public API. If you encounter a rate limit, you can securely set `GITHUB_TOKEN` in your own terminal. **Never send a key in chat, source code, or output files.** This script does not modify the GitHub repository.

The output status should be `DRAFT_REQUIRES_HUMAN_REVIEW`. The number of new artifacts depends on the PRs and their current GitHub versions. If the output directory already exists, choose a new directory name for another execution.

## Step 2: Review S0 and approve the enriched version

Open `data\azure-avnm-diff-v41\decision_state_ENRICHED_DRAFT.json` and the manifest. Compare the new diff excerpts with the corresponding GitHub `/files` pages. If you confirm the content and time range:

```powershell
& $py -m evorationale approve-state `
  --draft data\azure-avnm-diff-v41\decision_state_ENRICHED_DRAFT.json `
  --central-ids G1 I1a I1b I1c `
  --output data\azure-avnm-diff-v41\decision_state_ENRICHED_APPROVED.json

& $py -m evorationale validate `
  --decision data\azure-avnm-diff-v41\decision_state_ENRICHED_APPROVED.json `
  --history data\azure-avnm-diff-v41\history_ENRICHED.jsonl
```

## Step 3: Run an offline experiment, then use the API if needed

```powershell
& $py -m evorationale run `
  --decision data\azure-avnm-diff-v41\decision_state_ENRICHED_APPROVED.json `
  --history data\azure-avnm-diff-v41\history_ENRICHED.jsonl `
  --output outputs\azure-v41-diff-offline `
  --mode offline --max-rounds 6 --max-queries 12 `
  --max-reads 36 --max-input-tokens 120000
```

**Before an API run**, review `report.json`, `investigation_coverage`, and `data_audit.json`. After your approval, you can run the API with `--mode api`, `--allow-repository-text-to-api`, your model selections, and a separate output directory. API usage incurs costs. The token count shown by the program is an *estimate*, not the final OpenAI invoice.

## Research validity boundaries at the time of this release

- The original set contained only 22 **sampled artifacts**, not the complete repository history.
- PR text and diffs are archived at the **current retrieval time**. Without independently versioned data, they cannot be attributed to a PR's historical merge time.
- Diff excerpts establish the presence of specific code; they do not, by themselves, prove that the architectural decision remains correct or desirable.
- At the time of this Azure pilot, adjudicated gold labels were unavailable. These pilot outputs must not be reported as the paper's F1/UCR results.
- The first line of each diff document, containing the PR number and file path, is **metadata added by the collector**. The remaining lines form a contiguous excerpt of the retrieved diff. Raw GitHub API responses are stored in `raw_api`.

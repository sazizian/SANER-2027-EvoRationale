# EvoRationale primary-effects experiment

This is a **new experimental prediction view**, not a demonstrated accuracy
improvement. No hosted F1 result is claimed. It addresses concrete task and
source-context differences identified after reading the exact reviewer-confirmed
reference. The fixed S0, all 53 original history artifacts, historical code,
reference labels and exact-triple scorer remain unchanged.

## Why this experiment exists

The actual v4.9 all-scope result is TP14/FP11/FN5, F1 0.636364. Its subsequent
cached scope recheck retained all eleven FPs and lost another TP, resulting in
TP13/FP11/FN6, F1 0.604651. Extra checker flags did not discriminate these errors.

The frozen annotation notes clarify several distinctions:

- The scored hunk row lists target IDs for its stated relation. Other supported
  source relations can remain in explanatory notes rather than scored columns.
- Qualified goal/delegation sketches can support a target without explicit
  argumentative justification or proof of adoption.
- A new state/observability definition differs from operational consumption of
  an existing definition. A substantive defining-predicate rebind can still
  support a surviving concept.
- Intermediate contracts can evolve within the same target family while the
  fixed baseline wording remains unaffected.
- Some weaknesses concern the actual pinned implementation type or API design,
  which is absent from the condensed S0 paraphrase.

These findings justify an explicit primary-effect projection and historical
context channel. They do not establish that every extra relation is wrong,
that a simple dominance rule is valid, or that this classifier will achieve
80–85% F1. No hunk IDs, repository-specific mappings or frozen reference labels
are encoded into the runtime classifier.

## What changes

For every focused hunk, a fresh model request selects one primary relation
type and its applicable fixed target IDs. Secondary effects are preserved in
the checkpoint trace and excluded from the scored primary projection.
There is no universal adverse-before-support ranking. Local source focus
determines primary selection, which remains model-assessed.

The model receives the original fixed targets, full screened captured event,
and excerpts of the original public README. The baseline file is verified
against the Git blob pin already recorded in fixed S0. Excerpts cover **all
target source ranges**, with a four-line margin, not ranges selected from
reference labels. In the supplied case, this covers 147 of 1,181 source lines.
The full file is retained for byte identity; only selected screened excerpts
are sent to the model. Relevant qualifications outside these excerpts may be
missing. Baseline `B` handles are interpretation context and can never be used
as fresh post-S0 proof.

Effects distinguish `fixed_s0` from `prior_intermediate_contract`. The latter
is evolution of a locally evidenced intermediate contract associated with the
target family, with `baseline_change_asserted=false`; it does not claim the
fixed S0 sentence was superseded. Scope is chosen from source evidence, never
inherited mechanically from an event's temporal label.

Primary link provenance and declared flag consistency are screened locally.
All relation selection, target association, temporal lineage, authority and
semantic flags remain model assessments. There is no independent semantic
critic in this experiment, no certified deployment, and no architectural
decision outcome. The original primary responses are not replayed or sent as
candidate hypotheses; these are fresh classifications.

## Resource and comparison bounds

| Setting | Value |
|---|---|
| Focused artifacts per request | At most 3 |
| Planned events / artifacts for supplied source | 6 / 30 |
| Normal fresh classification requests | 12 |
| Independent critic requests | 0 |
| Maximum provider requests including format retries | 24 |
| Estimated cumulative input ceiling | 400,000 |
| Initial / retry output allowance | 12,000 / 16,384 |
| Model ID | Copied from original v4.9 linker configuration |
| Source reads / query / round bounds | Copied from original v4.9 preparation |

The normal local forecast estimates about 269,500 input tokens for the supplied
case. Every retry is charged before a request; the token ceiling can stop a
retry sequence before the request-count ceiling. Neither bound guarantees
completion under repeated errors. SDK automatic retries are disabled.

All 53 history artifacts remain inputs. The same read/round selection plans
30 hunk records; it does not claim all 53 artifacts or the entire repository
history received semantic review. Review-row coverage is not correctness.

Added baseline context, changed semantic policy, primary projection and
removed critic change the comparison. This is **not identical inference input
or equal compute**. Opaque matching model IDs do not certify immutable model
snapshots. The reference has been examined during development, so this pilot
is not held out and cannot establish cross-project superiority.

## Step 1: local tests and forecast only

Save `EvoRationale_PrimaryEffects_Experimental_Tested_EN.zip` in Downloads.
Paste the block below into PowerShell. Do not include `PS ...>` or `>>` prompts.
No virtual-environment activation is needed. This step requires no API key,
makes no API request and creates no inference-output directory.

```powershell
$zipPrimary = Join-Path $env:USERPROFILE "Downloads\EvoRationale_PrimaryEffects_Experimental_Tested_EN.zip"
if (-not (Test-Path -LiteralPath $zipPrimary -PathType Leaf)) {
    $zipPrimary = (Read-Host "Paste the full path to the downloaded ZIP").Trim().Trim('"')
}
if (-not (Test-Path -LiteralPath $zipPrimary -PathType Leaf)) { throw "ZIP file not found." }

$nPrimary = 1
do {
    $basePrimary = Join-Path $env:LOCALAPPDATA ("ERprimaryTools{0:D2}" -f $nPrimary)
    $nPrimary++
} while (Test-Path -LiteralPath $basePrimary)
Expand-Archive -LiteralPath $zipPrimary -DestinationPath $basePrimary -ErrorAction Stop

$kitPrimary = Join-Path $basePrimary "EvoRationale_PrimaryEffects_Experimental_EN"
$py = Join-Path $env:LOCALAPPDATA "er4venv\Scripts\python.exe"
$dev49 = Join-Path $env:LOCALAPPDATA "ERv49Dev01\EvoRationale_v49_DEV_EN"
$ready49 = Get-Content -LiteralPath "$dev49\V49_READY.json" -Raw -Encoding UTF8 -ErrorAction Stop | ConvertFrom-Json
$v49Eval = $ready49.evaluation
$primaryEval = Join-Path $env:LOCALAPPDATA "ER1287PrimaryEffects01"

& $py "$kitPrimary\start_primary_effect_no_api.py" --code-root "$dev49" --evaluation "$v49Eval" --output "$primaryEval"
if ($LASTEXITCODE -ne 0) { throw "Local preparation failed. Send the complete error." }
```

Expected: all targeted tests pass, then `PRIMARY_EFFECT_DRY_RUN_NO_API_CALLED`,
`mock_primary_requests: 12`, `forecast_complete: true`, no technical failures
and `output_created: false`. Test duration varies by computer. Keep the window
open. If your actual v4.9 code folder uses a later number, use its actual path.
The parent v4.9 run must already be completed and scored.

## Step 2: optional fresh hosted experiment

This step may incur API costs. Run only after Step 1 succeeds. This performs
fresh primary inference, unlike the three-call cached scope recheck.

```powershell
if ([string]::IsNullOrWhiteSpace($env:OPENAI_API_KEY) -and
    -not (Test-Path -LiteralPath "$primaryEval\RUN_RECEIPT.json" -PathType Leaf)) {
    $securePrimary = Read-Host "Enter your OpenAI API key" -AsSecureString
    $pointerPrimary = [System.Runtime.InteropServices.Marshal]::SecureStringToBSTR($securePrimary)
    try {
        $env:OPENAI_API_KEY = [System.Runtime.InteropServices.Marshal]::PtrToStringBSTR($pointerPrimary)
    }
    finally {
        [System.Runtime.InteropServices.Marshal]::ZeroFreeBSTR($pointerPrimary)
        $securePrimary.Dispose()
    }
}

& $py "$kitPrimary\run_primary_effect.py" --code-root "$dev49" --evaluation "$v49Eval" --output "$primaryEval" --mode api --allow-repository-text-to-api
if ($LASTEXITCODE -ne 0) { throw "Experiment failed. Send the complete error before retrying." }
```

A completed run is verified and reused with no key or API request. Incomplete
or interrupted output is preserved and refused. Per-chunk progress is retained
in `working_checkpoints`; final checkpoints are separately attested. An
interrupted provider request may still have incurred costs before a completed
chunk exists. Do not erase progress or silently repeat paid inference.

## Step 3: unchanged scoring and diagnostics

This step never contacts a provider. It verifies the original reference and
parent run, then applies the unchanged original exact-triple evaluator to
primary predictions only. An incomplete technical run is not scored as a
comparable completed accuracy experiment.

```powershell
$diagPrimary = Join-Path $primaryEval ("EvoRationale_PrimaryEffects_Diagnostics_" + (Get-Date -Format "yyyyMMdd-HHmmss-fff") + ".zip")
& $py "$kitPrimary\score_primary_effect.py" --code-root "$dev49" --evaluation "$primaryEval" --frozen "$env:LOCALAPPDATA\ER1287Gold\KEP1287_Reviewer_Confirmed_Freeze" --output-bundle "$diagPrimary"
if ($LASTEXITCODE -ne 0) { throw "Scoring failed. Send the complete error." }

$mPrimary = Get-Content -LiteralPath "$primaryEval\score\metrics.json" -Raw -Encoding UTF8 -ErrorAction Stop | ConvertFrom-Json
@($mPrimary.results.baseline, $mPrimary.results.all) | Select-Object scope, tp, fp, fn, precision, recall, f1 | Format-Table -AutoSize
$mPrimary.comparison | ConvertTo-Json -Depth 5
$diagPrimary
explorer.exe /select,"$diagPrimary"
```

Upload that ZIP and the metrics to review the actual result. Repeated scoring
verifies/reuses existing committed scores. The diagnostic ZIP destination must
be new. Score output is staged and committed atomically; interrupted score
attempts are preserved for inspection.

The frozen `baseline` scoring subset excludes hunks carrying inherited
`INTERIM_2024` annotation provenance. It is not equivalent to filtering model
effects whose `target_version` is `fixed_s0`. Both reported scopes and the
original denominators are unchanged. No outcome F1 is available.

## Restarting PowerShell

Recreate `$py`, `$dev49`, `$v49Eval`, `$primaryEval` using the assignments in
Step 1. Set `$kitPrimary` to the already extracted tool directory, for example
`$env:LOCALAPPDATA\ERprimaryTools01\EvoRationale_PrimaryEffects_Experimental_EN`.
There is no need to extract again, activate `.venv`, or repeat completed paid
inference to display its scores.

## Validation and review boundaries

The kit pins the original v4.9 core and separately pins its original scorer,
preparation helper and diagnostic verifier. Toolkit code, baseline raw bytes,
original unlabeled inputs and completed output are hashed and checked. These
checks establish integrity, not signed identity or semantic truth.

Release checks: **75 tests and 6 subtests passed**. All 28 saved proof fixtures
passed the new source/schema screen under explicitly synthetic semantic flags;
all four invalid current-source probes were rejected. These compatibility
checks establish no new semantic accuracy or F1.

Tests use generic synthetic sources and fake transports. Local tests,
source-proof compatibility fixtures and request-envelope forecasts do not
measure hosted semantic F1. The historical 782-test v4.9 release is unchanged;
this kit runs targeted new tests. Read `validation/` for release evidence.

`development_review/` contains post-run annotation analysis. The runtime never
loads these files or the Gold reference. Only the scorer reads reference rows,
after completed real inference and all integrity checks. Do not pass these
review files into model prompts or retrieval indices.

Promote a complete pipeline only after a measured useful result and validation
on independent cases under a predeclared annotation contract. F1 above 80% is
a goal, not a result established by this package.

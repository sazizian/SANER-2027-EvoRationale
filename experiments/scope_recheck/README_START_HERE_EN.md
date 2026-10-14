# EvoRationale cached-primary scope recheck experiment

The actual v4.9 result is **F1 0.636364** on all links (TP14/FP11/FN5) and
**0.666667** on baseline links (TP12/FP10/FN2). It has not reached 80%.
This kit tests one inspectable checker-interface issue while preserving the
completed v4.9 primary predictions, code, source inputs, frozen reference and
exact-triple scorer. **No hosted accuracy result is claimed for this kit.**

## What the diagnostics established

The original primary phase explicitly reviewed all 540 selected hunk/target
pairs. Its checker confirmed 26 of 28 hypotheses. It removed no otherwise
accepted false positive and rejected one otherwise accepted true positive.
Offline replay of the stored primary responses with unchanged source guards
and no critic rejection yields TP15/FP11/FN4, F1 0.666667. This is a cached
counterfactual, not a new hosted result.

The original checker sees a full target quote and a partial-scope label but
does not receive the primary hypothesis's explicit before/after claims,
qualification or authority/basis commitments. It can assess a different scope
from the proposed claim. The new checker receives these as **untrusted
hypotheses**, with confidence and persuasive reasons withheld, and returns
five typed alignment assessments. Confirmation requires all five to be true;
the unchanged source guards still apply. Model-assessed flags are not semantic
proof, and supplying hypotheses can introduce anchoring.

No deterministic source-handle, provenance or pair-coverage defect explains
all 11 false positives. Several are scope or evidence-policy disagreements
with the frozen exact-triple reference. The kit cannot recover a relation
omitted by the cached primary phase or change its relation direction.

## Experiment bounds

| Item | Setting |
|---|---|
| Primary predictions | Completed v4.9 checkpoint, validated and unchanged |
| New primary API requests | 0 |
| Normal checker requests for this cache | 3 |
| Maximum checker requests, including format retry | 6 |
| Estimated input ceiling | 100,000 |
| Local forecast for the supplied cache | 45,651 estimated input tokens |
| Model ID | Copied from the completed v4.9 judge configuration |
| Initial/retry output ceiling | 12,000 / 16,384 tokens |
| Nomination | None |

These limits are checked before provider requests. The forecast uses a local
all-reject fixture to measure request envelopes; it measures no F1. It creates
no experiment directory and requires no API key. An API run may incur costs.
Immutable provider model snapshots are not verified by matching model IDs.

The new checker is a separate request using the same model alias. This does
not establish statistical independence or independence from the architecture's
related instructions. The reference has already been examined during
development; any result is a development comparison, not held-out accuracy.

## Step 1 — extract and run local checks only

Save `EvoRationale_ScopeRecheck_Experiment_Tested_EN.zip` in Downloads.
Paste only this block into PowerShell. Do not paste `PS ...>` or `>>` prompts.
Virtual-environment activation is unnecessary.

```powershell
$zipScope = Join-Path $env:USERPROFILE "Downloads\EvoRationale_ScopeRecheck_Experiment_Tested_EN.zip"
if (-not (Test-Path -LiteralPath $zipScope -PathType Leaf)) {
    $zipScope = (Read-Host "Paste the full path to the downloaded ZIP").Trim().Trim('"')
}
if (-not (Test-Path -LiteralPath $zipScope -PathType Leaf)) {
    throw "ZIP file not found."
}

$nScope = 1
do {
    $baseScope = Join-Path $env:LOCALAPPDATA ("ERscopeTools{0:D2}" -f $nScope)
    $nScope++
} while (Test-Path -LiteralPath $baseScope)
Expand-Archive -LiteralPath $zipScope -DestinationPath $baseScope -ErrorAction Stop

$kit = Join-Path $baseScope "EvoRationale_ScopeRecheck_Experiment_EN"
$py = Join-Path $env:LOCALAPPDATA "er4venv\Scripts\python.exe"
$dev49 = Join-Path $env:LOCALAPPDATA "ERv49Dev01\EvoRationale_v49_DEV_EN"
$ready49 = Get-Content -LiteralPath "$dev49\V49_READY.json" -Raw -Encoding UTF8 -ErrorAction Stop | ConvertFrom-Json
$v49Eval = $ready49.evaluation
$scopeEval = Join-Path $env:LOCALAPPDATA "ER1287ScopeReview01"

& $py "$kit\start_scope_recheck_no_api.py" --code-root "$dev49" --evaluation "$v49Eval" --output "$scopeEval"
if ($LASTEXITCODE -ne 0) { throw "Local preparation failed. Send the complete error." }
```

Expected: all kit tests pass, then `SCOPE_RECHECK_DRY_RUN_NO_API_CALLED`,
`mock_checker_requests: 3`, `new_primary_api_requests: 0`, no technical failures,
and `output_created: false`. Test runtime varies by computer. Keep this
PowerShell window open for the next step. If your v4.9 code folder is a later
number than `ERv49Dev01`, use its actual path. The original v4.9 run must already
be scored; the supplied completed run meets this condition.

Release validation: **37 tests and 13 subtests passed** locally, followed by
the real-cache forecast. The complete log is in `validation/local_preflight.log`.

## Step 2 — optional real checker experiment

Run this only after Step 1 succeeds. It calls the provider and may incur costs;
it preserves the historical v4.9 output. Do not send your API key in chat.

```powershell
if ([string]::IsNullOrWhiteSpace($env:OPENAI_API_KEY) -and
    -not (Test-Path -LiteralPath "$scopeEval\RUN_RECEIPT.json" -PathType Leaf)) {
    $secureScope = Read-Host "Enter your OpenAI API key" -AsSecureString
    $pointerScope = [System.Runtime.InteropServices.Marshal]::SecureStringToBSTR($secureScope)
    try {
        $env:OPENAI_API_KEY = [System.Runtime.InteropServices.Marshal]::PtrToStringBSTR($pointerScope)
    }
    finally {
        [System.Runtime.InteropServices.Marshal]::ZeroFreeBSTR($pointerScope)
        $secureScope.Dispose()
    }
}

& $py "$kit\run_scope_recheck.py" --code-root "$dev49" --evaluation "$v49Eval" --output "$scopeEval" --mode api --allow-repository-text-to-api
if ($LASTEXITCODE -ne 0) { throw "Checker experiment failed. Send the complete error before retrying." }
```

A completed experiment is verified and reused on a repeated invocation, with
no API call and no key required. A partial experiment is preserved and refused;
send its error and directory listing before choosing a new output folder.
Per-round progress is retained in `working_checkpoints`; final immutable
checkpoints are stored separately. An interrupted provider call may still
have incurred costs and may not yet be represented by a completed round.

## Step 3 — score, bundle and show the actual F1

This step never calls an API. It requires the original unchanged Gold freeze.

```powershell
$diagScope = Join-Path $scopeEval ("EvoRationale_ScopeRecheck_Diagnostics_" + (Get-Date -Format "yyyyMMdd-HHmmss-fff") + ".zip")
& $py "$kit\score_scope_recheck.py" --code-root "$dev49" --evaluation "$scopeEval" --frozen "$env:LOCALAPPDATA\ER1287Gold\KEP1287_Reviewer_Confirmed_Freeze" --output-bundle "$diagScope"
if ($LASTEXITCODE -ne 0) { throw "Scoring failed. Send the complete error." }

$mScope = Get-Content -LiteralPath "$scopeEval\score\metrics.json" -Raw -Encoding UTF8 -ErrorAction Stop | ConvertFrom-Json
@($mScope.results.baseline, $mScope.results.all) | Select-Object scope, tp, fp, fn, precision, recall, f1 | Format-Table -AutoSize
$mScope.comparison | ConvertTo-Json -Depth 5
$diagScope
explorer.exe /select,"$diagScope"
```

Send the diagnostic ZIP and printed metrics for review. Existing committed
scores are verified and reused; the ZIP destination must be new. Scoring writes
a complete staged score directory and commits it atomically. Interrupted score
attempts are preserved for inspection. No Gold rows enter checker inputs.

## Restarting PowerShell

Variables and process API keys disappear after a restart. Recreate `$py`,
`$dev49`, `$v49Eval`, `$scopeEval` using Step 1's assignments. Set `$kit` to the
already extracted tool directory, for example:

```powershell
$kit = Join-Path $env:LOCALAPPDATA "ERscopeTools01\EvoRationale_ScopeRecheck_Experiment_EN"
```

There is no need to extract again or activate `.venv`. A completed experiment
can proceed straight to Step 3; do not repeat paid execution to display scores.

## How to interpret performance

With the fixed 19 positive exact triples, TP14/FP2/FN5 gives exactly 0.80.
TP15/FP1/FN4 gives 0.857143. These are arithmetic scenarios, not measured or
promised improvements. The unchanged cached proposals include at most 15
reference-positive triples. Four omitted reference positives remain beyond
this checker-only experiment.

Report the original primary classification cost when comparing end-to-end
architectures: 12 requests, 147,826 estimated input, 108,393 provider input and
52,240 provider output tokens. Cached cost is not zero. The original checker
also consumed 3 requests, 35,204 estimated input, 29,283 provider input and
5,595 provider output tokens. Distinguish incremental recheck cost, cumulative
development cost and any hypothetical full-pipeline cost comparison.

Promote a revised full pipeline only after a measured useful result, predeclared
semantic policy and separate held-out validation. Increasing test counts or
using more requests does not itself establish semantic accuracy.

## Integrity and included files

The kit pins the original v4.9 core and separately pins the original scorer,
preparation metadata helper and diagnostic verifier before importing them.
It validates parent receipts, complete cached pair grids, proof handles,
candidate identities and byte-equivalent reconstruction of original commits.
It hashes copied unlabeled inputs, toolkit code and completed output. These
are integrity checks, not signed attestations of provider authenticity.

`diagnostic_review/` contains post-run FP/FN/architecture audits and their data.
They may contain reference labels and must never be passed to a runtime model.
The runner does not load those files. Tests use portable synthetic sources,
reference rows and fake transports. The actual diagnostic cache is used only
for local provenance/replay/forecast checks. None of these tests are new hosted
F1 measurements. The historical 782-test v4.9 source release is unchanged;
this kit runs its own targeted tests rather than rerunning that suite.

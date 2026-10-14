# EvoRationale v4.8: measured-policy repair experiment

v4.7 regressed to F1 0.181818 baseline / 0.333333 all. v4.6 remains the strongest
measured result: 0.689655 / 0.631579. This development experiment restores the
v4.6 semantic instructions and schema verbatim. It is not yet a measured
replacement for v4.6. See V47_DIAGNOSTIC_REVIEW.md for all twenty score errors.

## Changes

The opt-in event-evidence-repair profile uses v4.6 source-qualified evidence and
same-event dependent migration semantics. It repairs one narrow proof location:
an adopted explicit mechanism replacement may cite added current contract
context in the same exact artifact as the removed claim. Unknown authority,
proposals, missing old proof, unrelated foreign context and unsupported scope
cannot use this repair. Historical profiles preserve their original behavior.

The v4.7 target-contribution schema and broad consumer restrictions are absent
from this profile. The larger initial structured output allowance remains
within the existing 16,384 ceiling. One classifier phase and bounded retry are
used, with no nomination. Models and budgets are pinned to v4.6 and match the
supplied v4.7 run. Frozen S0/Gold, original inputs and exact scorer are unchanged.

A repeated completed run verifies its stored receipt, source, report and
checkpoint and displays its path without a new provider call or API key.
Incomplete attempts remain preserved and cannot be silently retried. A repeated
complete score is also verified and reused without rewriting output. The STARTED
attempt record is an immutable record of start; RUN_RECEIPT attests completion.

## 1. Local tests/preparation only

Download EvoRationale_v48_V46PolicyRepair_Tested_EN.zip. Run this full block in
PowerShell. If the file is not at the default Downloads path, the prompt accepts
its actual full path, including a browser-added filename suffix. No activation
script or execution-policy change is needed.

```powershell
$zip48 = Join-Path $env:USERPROFILE "Downloads\EvoRationale_v48_V46PolicyRepair_Tested_EN.zip"
if (-not (Test-Path -LiteralPath $zip48 -PathType Leaf)) {
    $zip48 = (Read-Host "Paste the full path to the downloaded v4.8 ZIP").Trim().Trim('"')
}
if (-not (Test-Path -LiteralPath $zip48 -PathType Leaf)) { throw "ZIP file not found." }
$n48 = 1
do {
    $base48 = Join-Path $env:LOCALAPPDATA ("ERv48Dev{0:D2}" -f $n48)
    $n48++
} while (Test-Path -LiteralPath $base48)
Expand-Archive -LiteralPath $zip48 -DestinationPath $base48 -ErrorAction Stop
$dev48 = Join-Path $base48 "EvoRationale_v48_DEV_EN"
$py = Join-Path $env:LOCALAPPDATA "er4venv\Scripts\python.exe"
& $py "$dev48\development_tools\start_v48_no_api.py"
if ($LASTEXITCODE -ne 0) { throw "Preparation failed. Send the complete error." }
```

Original API/offline, frozen reference and completed v4.3-v4.7 folders default
to the previously used LOCALAPPDATA locations. All pins, including the completed
v4.7 score receipt and checkpoint, are checked. Use corresponding path flags if
different. The helper allocates an unused ER1287Eval_v48DevNN and copies the
identical two unlabeled inputs. Gold is not copied to agent inputs. V48_READY.json
records actual paths. Expected status: V48_TESTS_AND_DRY_RUN_COMPLETED_NO_API_CALLED.

## 2. Hosted experiment after successful preparation

This sends approved public repository excerpts to OpenAI and may incur API costs.
Use the same session. If a key is already set it is reused; otherwise the local
prompt hides input. Do not paste keys into chat, source files or receipts.

```powershell
$ready48 = Get-Content "$dev48\V48_READY.json" -Raw -Encoding UTF8 -ErrorAction Stop | ConvertFrom-Json
$v48Eval = $ready48.evaluation
if ([string]::IsNullOrWhiteSpace($env:OPENAI_API_KEY) -and
    -not (Test-Path -LiteralPath "$v48Eval\RUN_RECEIPT.json" -PathType Leaf)) {
    $secure48 = Read-Host "Enter your OpenAI API key" -AsSecureString
    $pointer48 = [System.Runtime.InteropServices.Marshal]::SecureStringToBSTR($secure48)
    try { $env:OPENAI_API_KEY = [System.Runtime.InteropServices.Marshal]::PtrToStringBSTR($pointer48) }
    finally {
        [System.Runtime.InteropServices.Marshal]::ZeroFreeBSTR($pointer48)
        $secure48.Dispose()
    }
}
& $py "$dev48\development_tools\run_v48.py" `
    --evaluation "$v48Eval" --code-root "$dev48" `
    --i-approve-public-repository-excerpts-to-openai
if ($LASTEXITCODE -ne 0) { throw "Run failed. Preserve the evaluation and send the complete error." }
```

Completed evaluations can be reused safely by this helper. Interrupted attempts
are preserved. AWAITING_HUMAN_REVIEW is normal; incomplete rationale or central
needs can still produce REVALIDATE/UNRESOLVED. Existing credentials are excluded
from receipts. Secret entry above applies only to the current PowerShell process.

## 3. Exact scoring and diagnostics; no API

```powershell
& $py "$dev48\development_tools\score_v48.py" `
    --evaluation "$v48Eval" --code-root "$dev48" `
    --frozen "$env:LOCALAPPDATA\ER1287Gold\KEP1287_Reviewer_Confirmed_Freeze" `
    --original-api "$env:LOCALAPPDATA\ER1287Eval_API01" `
    --original-offline "$env:LOCALAPPDATA\ER1287Eval_Offline01" `
    --previous-v43 "$env:LOCALAPPDATA\ER1287Eval_v43Dev01" `
    --previous-v44 "$env:LOCALAPPDATA\ER1287Eval_v44Dev01" `
    --previous-v45 "$env:LOCALAPPDATA\ER1287Eval_v45Dev01" `
    --previous-v46 "$env:LOCALAPPDATA\ER1287Eval_v46Dev01" `
    --previous-v47 "$env:LOCALAPPDATA\ER1287Eval_v47Dev01"
if ($LASTEXITCODE -ne 0) { throw "Scoring failed. Send the complete error." }
$m48 = Get-Content "$v48Eval\score\metrics.json" -Raw -Encoding UTF8 -ErrorAction Stop | ConvertFrom-Json
@($m48.results.baseline, $m48.results.all) |
    Select-Object scope, tp, fp, fn, precision, recall, f1 |
    Format-Table -AutoSize
$diag48 = Join-Path $v48Eval `
    ("EvoRationale_v48_Diagnostics_" + (Get-Date -Format "yyyyMMdd-HHmmss-fff") + ".zip")
& $py "$dev48\development_tools\bundle_v48_diagnostics.py" `
    --evaluation "$v48Eval" --output "$diag48"
if ($LASTEXITCODE -ne 0) { throw "Diagnostic verification failed. Send the complete error." }
$diag48
explorer.exe /select,"$diag48"
```

The ZIP is inside the evaluation directory and is selected in Explorer. Send
the table and ZIP for source-level review. Complete scores are reused read-only;
partial/tampered scores are preserved and rejected. Do not delete old evaluations.

## After restarting the PC

Restore variables using the actual extracted DevNN folder (Dev01 shown):

```powershell
$py = Join-Path $env:LOCALAPPDATA "er4venv\Scripts\python.exe"
$dev48 = Join-Path $env:LOCALAPPDATA "ERv48Dev01\EvoRationale_v48_DEV_EN"
$ready48 = Get-Content "$dev48\V48_READY.json" -Raw -Encoding UTF8 -ErrorAction Stop | ConvertFrom-Json
$v48Eval = $ready48.evaluation
```

If a completed run receipt exists, go directly to step 3. The run helper can
also verify and reuse it without a key or new provider call. Never infer a failed
run solely from the retained STARTED attempt record.

## Validation and limits

V48_TEST_REPORT.md, V48_SOURCE_PREFLIGHT.json, V48_V46_EFFECT_REPLAY.json,
MANIFEST_V48_DEV.json and SHA256SUMS_V48.json document the release. Replaying all
23 stored v4.6 effects preserves all 19 accepted interpretations and repairs one
rejection; earlier false positives are included. This is source-guard regression
testing, not a fresh prediction or measured v4.8 F1. Native Windows execution
and hosted v4.8 accuracy are not established during construction. Model
assessments are not semantic proof. Reference-contract tensions remain disclosed.
Known examples informed development; no held-out or best-architecture claim is
made. Prior-version files are historical records, not current checksums.

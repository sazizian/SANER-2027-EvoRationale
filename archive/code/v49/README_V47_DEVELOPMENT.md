# EvoRationale v4.7: exact predicate contributions

Development release following the supplied v4.6 hosted run. The opt-in
`event-grounded` profile requires direct target contributions and exact local
current predicate proof. Existing `targeted`, `event-complete`, `event-delta`
and `event-evidence` behavior is preserved.

Actual v4.6 F1 was 0.689655 baseline and 0.631579 all-scope. Its verified
diagnostics reveal one proof-routing defect and several semantic scope errors;
see `V46_DIAGNOSTIC_REVIEW.md`. New policy accuracy has not been measured.

## What changes

Supporting a fixed claim requires fresh local lines expressing or testing its
predicate. Ordinary downstream use, retained-rule implementation and a list of
field names are insufficient. A substantive predicate operand rebind can
provide qualified evidence. An explicit exclusion boundary and fallback can
support a non-goal even when compliance has a cost; weakens requires a direct
tradeoff affecting the selected fixed target.

An adopted explicit mechanism replacement can now use added current contract
context in the same exact artifact as the removed claim. The previous gate
discarded that proof location. Proposals, removed-only context and unrelated
sibling contracts cannot use this direct-replacement path. Source identity,
safe exact quotation, temporal eligibility, scope, qualification and authority
checks remain. Contribution and entailment decisions are MODEL_ASSESSED.

Models and nominal budgets are copied from the completed v4.6 run. Nomination
remains none: one classifier request per selected event batch, before any
bounded retry. The initial structured output allowance increases within the
existing 16,384 ceiling. Schema/instructions and actual token use differ, so
this is neither equal-compute nor held-out/generalization evidence. Fixed S0,
frozen reference, exact scoring and old results remain unchanged.

Scoring writes a complete score directory only after computing both scopes.
A committed receipt hashes the metrics and error CSV. Re-running the scorer
verifies all inputs, run and score identities and reuses the existing complete
result without rewriting it. Partial output or an interrupted scoring claim is
preserved and reported. No paid run is needed simply to display existing scores.

## 1. Local tests and preparation; no API

Download `EvoRationale_v47_GroundedTrace_Tested_EN.zip` into your Windows
Downloads folder. Paste this complete block into PowerShell. Virtual-environment
activation is unnecessary because the Python executable is called directly.

```powershell
$zip47 = Join-Path $env:USERPROFILE "Downloads\EvoRationale_v47_GroundedTrace_Tested_EN.zip"
if (-not (Test-Path -LiteralPath $zip47 -PathType Leaf)) {
    throw "ZIP not found. Save the downloaded ZIP in Downloads with this exact filename."
}
$n47 = 1
do {
    $base47 = Join-Path $env:LOCALAPPDATA ("ERv47Dev{0:D2}" -f $n47)
    $n47++
} while (Test-Path -LiteralPath $base47)
Expand-Archive -LiteralPath $zip47 -DestinationPath $base47 -ErrorAction Stop
$dev47 = Join-Path $base47 "EvoRationale_v47_DEV_EN"
$py = Join-Path $env:LOCALAPPDATA "er4venv\Scripts\python.exe"
& $py "$dev47\development_tools\start_v47_no_api.py"
if ($LASTEXITCODE -ne 0) { throw "Preparation failed. Send the complete error." }
```

The helper runs the full suite, verifies the original API/offline evaluation,
frozen reference and completed v4.3/v4.4/v4.5/v4.6 folders, allocates the next
unused `ER1287Eval_v47DevNN`, and copies the exact two unlabeled inputs. Paths
default to the previously used LOCALAPPDATA locations; use corresponding path
flags if yours differ. No agent input contains Gold labels. An API command is
printed without execution. Actual paths are recorded in `V47_READY.json`.
Expected final status: `V47_TESTS_AND_DRY_RUN_COMPLETED_NO_API_CALLED`.

## 2. Hosted evaluation after successful preparation

Use the same PowerShell session:

```powershell
$ready47 = Get-Content "$dev47\V47_READY.json" -Raw -Encoding UTF8 -ErrorAction Stop | ConvertFrom-Json
$v47Eval = $ready47.evaluation
& $py "$dev47\development_tools\run_v47.py" `
    --evaluation "$v47Eval" --code-root "$dev47" `
    --i-approve-public-repository-excerpts-to-openai
if ($LASTEXITCODE -ne 0) {
    throw "Run failed. Preserve this evaluation and send the complete error before retrying."
}
```

This step sends approved public repository excerpts to OpenAI and may incur
API costs. The helper exclusively claims an attempt before provider work and
refuses to overwrite prior work. Environment credentials are excluded from
receipts. `AWAITING_HUMAN_REVIEW` is expected. `UNRESOLVED` can remain correct
when rationale or investigation coverage is incomplete.

## 3. Exact scoring, display, diagnostics; no API

```powershell
& $py "$dev47\development_tools\score_v47.py" `
    --evaluation "$v47Eval" --code-root "$dev47" `
    --frozen "$env:LOCALAPPDATA\ER1287Gold\KEP1287_Reviewer_Confirmed_Freeze" `
    --original-api "$env:LOCALAPPDATA\ER1287Eval_API01" `
    --original-offline "$env:LOCALAPPDATA\ER1287Eval_Offline01" `
    --previous-v43 "$env:LOCALAPPDATA\ER1287Eval_v43Dev01" `
    --previous-v44 "$env:LOCALAPPDATA\ER1287Eval_v44Dev01" `
    --previous-v45 "$env:LOCALAPPDATA\ER1287Eval_v45Dev01" `
    --previous-v46 "$env:LOCALAPPDATA\ER1287Eval_v46Dev01"
if ($LASTEXITCODE -ne 0) { throw "Scoring failed. Send the complete error." }
$m47 = Get-Content "$v47Eval\score\metrics.json" -Raw -Encoding UTF8 -ErrorAction Stop | ConvertFrom-Json
@($m47.results.baseline, $m47.results.all) |
    Select-Object scope, tp, fp, fn, precision, recall, f1 |
    Format-Table -AutoSize
$m47.comparison | ConvertTo-Json -Depth 5
$diag47 = Join-Path $v47Eval `
    ("EvoRationale_v47_Diagnostics_" + (Get-Date -Format "yyyyMMdd-HHmmss-fff") + ".zip")
& $py "$dev47\development_tools\bundle_v47_diagnostics.py" `
    --evaluation "$v47Eval" --output "$diag47"
if ($LASTEXITCODE -ne 0) { throw "Diagnostic verification failed. Send the complete error." }
$diag47
explorer.exe /select,"$diag47"
```

The diagnostics ZIP is inside the printed evaluation folder; the last command
selects that exact file in Explorer. Attach it for review. Re-running this
scoring block reuses a complete verified score and creates a new diagnostics
ZIP. It never repeats the hosted evaluation.

## After restarting your PC

PowerShell variables are lost after restart; the files remain. If extraction
used `ERv47Dev01`, restore variables with:

```powershell
$py = Join-Path $env:LOCALAPPDATA "er4venv\Scripts\python.exe"
$dev47 = Join-Path $env:LOCALAPPDATA "ERv47Dev01\EvoRationale_v47_DEV_EN"
$ready47 = Get-Content "$dev47\V47_READY.json" -Raw -Encoding UTF8 -ErrorAction Stop | ConvertFrom-Json
$v47Eval = $ready47.evaluation
```

Use the actual extracted DevNN folder if different. If the hosted run already
completed, go directly to step 3. Activation-script execution policy need not
change. Do not delete an existing evaluation or edit its scored outputs.

## Validation limits

See `V47_TEST_REPORT.md`, `V47_SOURCE_PREFLIGHT.json`, `MANIFEST_V47_DEV.json`
and `SHA256SUMS_V47.json`. Source-only audit uses complete negative local
transport fixtures, not model predictions. Controlled replay tests source
guards, not new F1. Native Windows execution and hosted v4.7 accuracy must be
confirmed in your environment. Earlier version documents and manifests are
historical records and do not verify the current source.

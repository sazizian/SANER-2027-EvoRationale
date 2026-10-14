# EvoRationale v4.5 development workflow

Start with the local preparation below. It runs tests and prepares a fresh
evaluation, without contacting a model provider. Earlier code and evaluations
remain available. The hosted run is a separate explicit command.

This version adds `event-delta`. Its default pipeline makes one complete source
classification request per captured event, using the actual fixed S0. The
classifier can choose missing targets and relations, and emits an exact S0
anchor plus before/after source evidence. Source attribution checks are
deterministic; architectural interpretation remains a fallible model assessment.

## 1. Download and prepare locally

Save `EvoRationale_v45_DeltaReview_Tested_EN.zip` in the existing project's
`research` folder. Open PowerShell in that project directory and paste:

```powershell
$zip45 = Join-Path (Get-Location).Path "research\EvoRationale_v45_DeltaReview_Tested_EN.zip"
$n45 = 1
do {
    $base45 = Join-Path $env:LOCALAPPDATA ("ERv45Dev{0:D2}" -f $n45)
    $n45++
} while (Test-Path -LiteralPath $base45)

Expand-Archive -LiteralPath $zip45 -DestinationPath $base45 -ErrorAction Stop
$dev45 = Join-Path $base45 "EvoRationale_v45_DEV_EN"
$py = Join-Path $env:LOCALAPPDATA "er4venv\Scripts\python.exe"

& $py "$dev45\development_tools\start_v45_no_api.py"
if ($LASTEXITCODE -ne 0) {
    throw "Preparation failed. Send the complete error before continuing."
}
```

The helper uses the existing original API/offline evaluations, frozen reference,
v4.3 evaluation and completed v4.4 evaluation. Their default names are
`ER1287Eval_API01`, `ER1287Eval_Offline01`,
`ER1287Gold\KEP1287_Reviewer_Confirmed_Freeze`, `ER1287Eval_v43Dev01` and
`ER1287Eval_v44Dev01`, under LOCALAPPDATA. Supply the corresponding path flags
if yours differ. Preparation verifies the source/receipt/reference pins.

It allocates the next unused `ER1287Eval_v45DevNN` directory, copies exactly the
same two unlabeled input files, prints the proposed command and writes
`V45_READY.json` in the code folder. That convenience pointer records the actual
allocated path; it is not a run receipt. No provider request or score occurs.

Expected final status: `V45_TESTS_AND_DRY_RUN_COMPLETED_NO_API_CALLED`.

## 2. Run the prepared hosted evaluation

After reviewing preparation output, use the same PowerShell session:

```powershell
$ready45 = Get-Content "$dev45\V45_READY.json" -Raw -Encoding UTF8 | ConvertFrom-Json
$v45Eval = $ready45.evaluation

& $py "$dev45\development_tools\run_v45.py" `
    --evaluation "$v45Eval" `
    --code-root "$dev45" `
    --i-approve-public-repository-excerpts-to-openai

if ($LASTEXITCODE -ne 0) {
    throw "Run failed. Preserve the evaluation and send the error before retrying."
}
```

This step transmits approved public repository excerpts and may incur provider
costs. Credentials are read from the existing environment and excluded from
receipts. The classifier uses the prior linker's configured opaque model ID;
the parent models and model change are recorded. Nominal limits remain
6 rounds, 12 queries, 36 reads and 100,000 estimated input tokens when those are
the parent's recorded settings. Hosted nomination is disabled by default:
its result does not enter classification, so it added cost without affecting
the accepted relation. An optional direct-CLI `--delta-nomination model` audit
mode retains it for analysis. Its empty or failed response cannot gate the
classifier when budget remains. Actual calls, input/output usage, model cost and
latency can differ from v4.4.

Each hosted attempt is reserved exclusively before provider work; a failed
attempt cannot silently restart in the same evaluation directory. Prepare a
fresh evaluation for another attempt after inspecting the failure.

## 3. Score the completed run

```powershell
& $py "$dev45\development_tools\score_v45.py" `
    --evaluation "$v45Eval" `
    --code-root "$dev45" `
    --frozen "$env:LOCALAPPDATA\ER1287Gold\KEP1287_Reviewer_Confirmed_Freeze" `
    --original-api "$env:LOCALAPPDATA\ER1287Eval_API01" `
    --original-offline "$env:LOCALAPPDATA\ER1287Eval_Offline01" `
    --previous-v43 "$env:LOCALAPPDATA\ER1287Eval_v43Dev01" `
    --previous-v44 "$env:LOCALAPPDATA\ER1287Eval_v44Dev01"

if ($LASTEXITCODE -ne 0) {
    throw "Scoring failed. Send the complete error."
}

$m45 = Get-Content "$v45Eval\score\metrics.json" -Raw -Encoding UTF8 | ConvertFrom-Json
@($m45.results.baseline, $m45.results.all) |
    Select-Object scope, tp, fp, fn, precision, recall, f1 |
    Format-Table -AutoSize
$m45.comparison | ConvertTo-Json -Depth 5
```

Scoring uses the unchanged exact-triple scorer and frozen labels only after the
completed-run and reference checks pass. Comparisons include v4.4, v4.3 and the
original API/offline results. They are descriptive development comparisons;
model choice, classification policy, call pattern and token accounting differ.

## 4. Share complete diagnostics

```powershell
$diag45 = Join-Path (Get-Location).Path `
    ("research\EvoRationale_v45_Diagnostics_" + (Get-Date -Format "yyyyMMdd-HHmmss-fff") + ".zip")

& $py "$dev45\development_tools\bundle_v45_diagnostics.py" `
    --evaluation "$v45Eval" --output "$diag45"
if ($LASTEXITCODE -ne 0) { throw "Diagnostic bundling failed. Send the error." }
$diag45
```

Attach that ZIP to the chat. It includes the preparation/run manifests, receipt,
exact inputs, report, checkpoint and available score files, with relative paths
and checked hashes. This step makes no provider call.

## Optional source-only preflight

`development_tools/audit_v45_no_api.py` checks source-owned handles and estimates
the request envelopes using explicit no-relation transport fixtures. It can
use `--evaluation PATH --output NEW_JSON_PATH`. Those fixtures do not test
linguistic accuracy or produce an experimental F1. Read `V45_TEST_REPORT.md` for
the package's actual local checks and limits. Its optional `--nomination-mode
model` sizes the additional hosted audit stage; the default is `none`.

## Research boundaries

The uploaded v4.4 report achieved all-scope F1 0.300000. No v4.5 hosted result
exists at packaging time. Tests verify control flow, provenance, budgets,
response contracts and source attribution; they do not prove semantic accuracy.
Known development examples informed this version. Two interim-state labels
refer to policies absent from fixed S0, and further scope/freshness ambiguities
are documented in `V44_DIAGNOSTIC_REVIEW.md`. The runtime must not invent claims
or read Gold rows to improve a score. Overall unresolved coverage can still
correctly produce REVALIDATE/UNRESOLVED even when useful relations are found.

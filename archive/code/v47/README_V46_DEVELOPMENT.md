# EvoRationale v4.6: source-qualified evidence traces

Development release, following the supplied v4.5 hosted run. This version adds
the opt-in `event-evidence` profile. The existing `targeted` default,
`event-complete` and v4.5 `event-delta` policies remain available.

The actual v4.5 all-scope result was TP4/FP0/FN15, F1 0.347826. All 15 missed
reference links were reviewed but the model emitted no effect; no technical or
downstream verifier rejection caused the misses. v4.5 lost all six v4.4 true
positives and recovered four different links. See `V45_DIAGNOSTIC_REVIEW.md` and
`development_review/` for the exact-source diagnosis.

## What changes

The classifier now separately explains current supporting evidence and
architectural change. Substantively added documentation or operational
witnesses can trace-support an existing fixed-S0 claim without inventing new
architecture. A local dependent migration can evidence an explicitly documented
same-event contract replacement, with exact old/new local lines and current
external contract lines. Prospective policy arguments remain qualified and
partial. Formatting-only/reflow edits and incidental retained text are screened.

Exact source identity, quotations, temporal eligibility, source-side roles,
target scope and privacy screening remain enforced. Semantic entailment,
authority and causal interpretation are model assessments, not deterministic
proof. Every accepted assessment records its policy, support versus change,
qualification and source contribution. Documentation does not establish deployed
behavior. Partial support cannot resolve a whole central need or whole composite.

The v4.5 model IDs and nominal budgets are reused. Nomination remains disabled;
one classifier request per selected event batch precedes any bounded retry.
The request schema/instructions change, so token use can change. This is a
descriptive development comparison, not held-out or equal-compute evidence.
Frozen Gold, fixed S0, historical results and the exact-triple scorer are preserved.
Interim restrictions absent from fixed S0 are never fabricated to fit labels.

## 1. Local tests and preparation, no API

Place `EvoRationale_v46_EvidenceTrace_Tested_EN.zip` in the existing project's
`research` folder. Open PowerShell in that project and run:

```powershell
$zip46 = Join-Path (Get-Location).Path "research\EvoRationale_v46_EvidenceTrace_Tested_EN.zip"
$n46 = 1
do {
    $base46 = Join-Path $env:LOCALAPPDATA ("ERv46Dev{0:D2}" -f $n46)
    $n46++
} while (Test-Path -LiteralPath $base46)

Expand-Archive -LiteralPath $zip46 -DestinationPath $base46 -ErrorAction Stop
$dev46 = Join-Path $base46 "EvoRationale_v46_DEV_EN"
$py = Join-Path $env:LOCALAPPDATA "er4venv\Scripts\python.exe"

& $py "$dev46\development_tools\start_v46_no_api.py"
if ($LASTEXITCODE -ne 0) { throw "Preparation failed. Send the complete error." }
```

This helper expects the original API/offline evaluation, frozen reference and
completed v4.3/v4.4/v4.5 development folders already used in this session under
LOCALAPPDATA. Use its corresponding path flags if yours differ. It verifies all
provenance pins, including the completed v4.5 checkpoint, allocates the next
unused `ER1287Eval_v46DevNN`, copies the identical two unlabeled inputs and
prints the API command without running it. The actual path is recorded in
`V46_READY.json`; this is a convenience pointer, not a completed run receipt.
Expected final status: `V46_TESTS_AND_DRY_RUN_COMPLETED_NO_API_CALLED`.

## 2. Hosted evaluation

After successful preparation, use the same PowerShell session:

```powershell
$ready46 = Get-Content "$dev46\V46_READY.json" -Raw -Encoding UTF8 | ConvertFrom-Json
$v46Eval = $ready46.evaluation

& $py "$dev46\development_tools\run_v46.py" `
    --evaluation "$v46Eval" `
    --code-root "$dev46" `
    --i-approve-public-repository-excerpts-to-openai

if ($LASTEXITCODE -ne 0) {
    throw "Run failed. Preserve the evaluation and send the error before retrying."
}
```

This step sends approved public repository excerpts to OpenAI and can incur
API costs. Existing credentials are read from the environment and excluded
from receipts. The attempt is claimed exclusively before provider work. A failed
or interrupted attempt cannot silently overwrite itself; inspect it before
preparing a fresh evaluation. `AWAITING_HUMAN_REVIEW` is the intended workflow
state. `UNRESOLVED` can remain correct when rationale or coverage is incomplete.

## 3. Exact frozen scoring and complete diagnostics

```powershell
& $py "$dev46\development_tools\score_v46.py" `
    --evaluation "$v46Eval" --code-root "$dev46" `
    --frozen "$env:LOCALAPPDATA\ER1287Gold\KEP1287_Reviewer_Confirmed_Freeze" `
    --original-api "$env:LOCALAPPDATA\ER1287Eval_API01" `
    --original-offline "$env:LOCALAPPDATA\ER1287Eval_Offline01" `
    --previous-v43 "$env:LOCALAPPDATA\ER1287Eval_v43Dev01" `
    --previous-v44 "$env:LOCALAPPDATA\ER1287Eval_v44Dev01" `
    --previous-v45 "$env:LOCALAPPDATA\ER1287Eval_v45Dev01"
if ($LASTEXITCODE -ne 0) { throw "Scoring failed. Send the complete error." }

$m46 = Get-Content "$v46Eval\score\metrics.json" -Raw -Encoding UTF8 | ConvertFrom-Json
@($m46.results.baseline, $m46.results.all) |
    Select-Object scope, tp, fp, fn, precision, recall, f1 |
    Format-Table -AutoSize
$m46.comparison | ConvertTo-Json -Depth 5

$diag46 = Join-Path (Get-Location).Path `
    ("research\EvoRationale_v46_Diagnostics_" + (Get-Date -Format "yyyyMMdd-HHmmss-fff") + ".zip")
& $py "$dev46\development_tools\bundle_v46_diagnostics.py" `
    --evaluation "$v46Eval" --output "$diag46"
if ($LASTEXITCODE -ne 0) { throw "Diagnostic bundling failed. Send the error." }
$diag46
```

Attach the resulting ZIP for review. Scoring and bundling make no API calls.
The scorer is byte-identical to v4.5 and comparisons include all prior pinned
versions. Gold labels enter only post-run scoring. Two interim-target reference
relations and further scope/authority ambiguities remain disclosed independently;
no label or denominator is silently changed.

## Validation and limits

See `V46_TEST_REPORT.md`, `V46_SOURCE_PREFLIGHT.json`, `MANIFEST_V46_DEV.json` and
`SHA256SUMS_V46.json` for the delivered source and completed validation. A local
source-only audit can run with `development_tools/audit_v46_no_api.py --evaluation
PATH --output NEW_JSON_PATH`; its complete negative responses are transport
fixtures, never semantic predictions or performance results.

Files named for previous versions describe those versions and their historical
validation; their manifests/checksums do not verify the current v4.6 tree. No
hosted v4.6 accuracy is established during construction. Synthetic regression
tests validate guard behavior, not the accuracy of model interpretations.

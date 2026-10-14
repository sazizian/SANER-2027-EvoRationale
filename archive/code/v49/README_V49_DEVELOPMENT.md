# EvoRationale v4.9 — experimental pair review

**Goal: improve exact-triple F1 while retaining fixed S0, frozen reference labels and the unchanged scorer. Hosted v4.9 accuracy is unmeasured.** v4.6 remains the strongest recorded development baseline (all F1 0.631579). Local tests and controlled replay do not establish 80–85% F1.

## Architecture

The opt-in `event-pair-reviewed` profile classifies every focused artifact against every fixed target with an explicit outcome and reason. Requests focus on at most three artifacts while retaining the original full captured same-event context and citation maps. With this pilot's 18 targets, each full focus chunk has 54 explicit pair records.

A separate candidate checker re-derives each proposed relation from the screened original source and fixed target. It receives code-owned candidate IDs, selected proof handles and the proposed target/relation/scope. Primary confidence, generated claims, qualification and explanation prose are withheld. A candidate requires checker confirmation and the inherited exact-source gates; confirmation cannot override those gates. Checker rejection and uncertainty remain auditable model assessments.

Missing/duplicate pairs or incomplete checks fail the entire event closed. Completed focus-chunk traces are retained, but incomplete events contribute no accepted effects or complete review records. Explicit pair records establish structural coverage, not semantic correctness. The checker examines proposed positives; it cannot recover an omitted primary relation by itself.

The v4.6 evidence-trace semantics and v4.8 narrow routing repair remain available. New generic instructions distinguish consuming a value from publishing it, using state names from defining progress behavior, a conditional sketch from an explicit chosen-target argument, and preserving a boundary from its costs. Source-backed dependent replacement, qualified alternative rationale and partial evidence remain permitted. All historical profiles remain available.

## Compute and experimental limits

| Limit | v4.6/v4.8 | v4.9 experiment |
|---|---:|---:|
| Estimated cumulative input tokens | 100,000 | 400,000 |
| Event queries | 12 | 12 |
| Unique source reads | 36 | 36 |
| Event rounds | 6 | 6 |
| Provider requests including both phases/retries | No separate cap | 36 |
| Maximum output per request | 16,384 | 16,384 |

Nomination stays `none`; both model IDs are copied from completed v4.6 and checked against v4.8. They are opaque IDs, not verified immutable snapshots. This architecture and increased token budget make an **unequal-compute development comparison**. Model calls can cost more and take longer.

For the current first six events `[14,6,5,1,2,2]`, classification needs 12 first-attempt requests. Candidate checking adds at most one request per event, for at most 18 first-attempt requests. Both phases permit at most two format/transport attempts, bounded by 36 provider requests and the cumulative input ceiling. Domain validation failures remain technical failures; missing judgments are never filled as no relation. Candidate sets over 64 fail closed. The input estimate is a UTF-8 request-envelope estimator, not billing/tokenizer accounting.

The source-only negative fixture measures approximately 147,826 estimated input tokens. Controlled replay of all 23 stored v4.6 interpretations through explicit pairs plus mock confirmation measures approximately 181,785 tokens and 15 requests. It preserves all 19 prior accepted interpretations and admits the one known routing repair; prior false positives are intentionally preserved by this fake confirmation, so this is not an accuracy result.

A dense synthetic capacity scenario with 64 hypotheses and maximal proof lists in each event estimates approximately 623,680 combined input tokens, above the configured 400,000. The runtime stops before exceeding its input/request ceilings. The limit is intentional; it does not guarantee that every dense event or retry can complete. Output completeness, hosted usage, latency and F1 must be measured in the actual run.

## Step 1 — local preparation only

Save `EvoRationale_v49_PairReview_Experimental_Tested_EN.zip` to Downloads. Paste this block into PowerShell. No environment activation or API key is needed. Do not paste `PS ...>` or `>>` prompt characters.

```powershell
$zip49 = Join-Path $env:USERPROFILE "Downloads\EvoRationale_v49_PairReview_Experimental_Tested_EN.zip"
if (-not (Test-Path -LiteralPath $zip49 -PathType Leaf)) {
    $zip49 = (Read-Host "Paste the full path to the downloaded v4.9 ZIP").Trim().Trim('"')
}
if (-not (Test-Path -LiteralPath $zip49 -PathType Leaf)) { throw "ZIP file not found." }

$n49 = 1
do {
    $base49 = Join-Path $env:LOCALAPPDATA ("ERv49Dev{0:D2}" -f $n49)
    $n49++
} while (Test-Path -LiteralPath $base49)

Expand-Archive -LiteralPath $zip49 -DestinationPath $base49 -ErrorAction Stop
$dev49 = Join-Path $base49 "EvoRationale_v49_DEV_EN"
$py = Join-Path $env:LOCALAPPDATA "er4venv\Scripts\python.exe"
& $py "$dev49\development_tools\start_v49_no_api.py"
if ($LASTEXITCODE -ne 0) { throw "Preparation failed. Send the complete error." }
```

The helper runs the complete local test suite, verifies the v4.1/43/44/45/46/47/48 ancestry, creates an unused `ER1287Eval_v49DevNN` directory, and dry-runs the hosted command. It copies exactly the two original unlabeled inputs. Existing releases, evaluations, scores, S0 and reference labels are preserved. `V49_READY.json` records the actual code/evaluation paths.

If previous runs are stored in different folders, use the corresponding explicit `--previous-v48`, `--previous-v46` and other helper path flags. A missing or changed historical record is an error to inspect, not an instruction to delete old results.

## Step 2 — one optional hosted pilot

After successful preparation, this block uses the actual READY pointer. It may incur provider charges under the new limits. Use the same PowerShell session so `$dev49` points to the extracted folder. After restarting, set `$dev49` to the exact folder shown by preparation, for example `Join-Path $env:LOCALAPPDATA "ERv49Dev01\EvoRationale_v49_DEV_EN"`.

```powershell
$py = Join-Path $env:LOCALAPPDATA "er4venv\Scripts\python.exe"
$ready49 = Get-Content -LiteralPath "$dev49\V49_READY.json" -Raw -Encoding UTF8 -ErrorAction Stop | ConvertFrom-Json
$v49Eval = $ready49.evaluation

if ([string]::IsNullOrWhiteSpace($env:OPENAI_API_KEY) -and
    -not (Test-Path -LiteralPath "$v49Eval\RUN_RECEIPT.json" -PathType Leaf)) {
    $secure49 = Read-Host "Enter your OpenAI API key" -AsSecureString
    $pointer49 = [System.Runtime.InteropServices.Marshal]::SecureStringToBSTR($secure49)
    try { $env:OPENAI_API_KEY = [System.Runtime.InteropServices.Marshal]::PtrToStringBSTR($pointer49) }
    finally {
        [System.Runtime.InteropServices.Marshal]::ZeroFreeBSTR($pointer49)
        $secure49.Dispose()
    }
}

& $py "$dev49\development_tools\run_v49.py" --evaluation "$v49Eval" --code-root "$dev49" --i-approve-public-repository-excerpts-to-openai
if ($LASTEXITCODE -ne 0) { throw "Run failed. Send the complete error before retrying." }
```

A completed attested run is verified and reused without another API call or key. An interrupted/incomplete attempt is preserved and refused; inspect its records before preparing another evaluation. Never send the API key in chat.

## Step 3 — score and bundle locally

```powershell
& $py "$dev49\development_tools\score_v49.py" `
    --evaluation "$v49Eval" --code-root "$dev49" `
    --frozen "$env:LOCALAPPDATA\ER1287Gold\KEP1287_Reviewer_Confirmed_Freeze" `
    --original-api "$env:LOCALAPPDATA\ER1287Eval_API01" `
    --original-offline "$env:LOCALAPPDATA\ER1287Eval_Offline01" `
    --previous-v43 "$env:LOCALAPPDATA\ER1287Eval_v43Dev01" `
    --previous-v44 "$env:LOCALAPPDATA\ER1287Eval_v44Dev01" `
    --previous-v45 "$env:LOCALAPPDATA\ER1287Eval_v45Dev01" `
    --previous-v46 "$env:LOCALAPPDATA\ER1287Eval_v46Dev01" `
    --previous-v47 "$env:LOCALAPPDATA\ER1287Eval_v47Dev01" `
    --previous-v48 "$env:LOCALAPPDATA\ER1287Eval_v48Dev01"
if ($LASTEXITCODE -ne 0) { throw "Scoring failed. Send the complete error." }

$m49 = Get-Content -LiteralPath "$v49Eval\score\metrics.json" -Raw -Encoding UTF8 -ErrorAction Stop | ConvertFrom-Json
@($m49.results.baseline, $m49.results.all) | Select-Object scope, tp, fp, fn, precision, recall, f1 | Format-Table -AutoSize

$diag49 = Join-Path $v49Eval ("EvoRationale_v49_Diagnostics_" + (Get-Date -Format "yyyyMMdd-HHmmss-fff") + ".zip")
& $py "$dev49\development_tools\bundle_v49_diagnostics.py" --evaluation "$v49Eval" --output "$diag49"
if ($LASTEXITCODE -ne 0) { throw "Diagnostic verification failed. Send the complete error." }
$diag49
explorer.exe /select,"$diag49"
```

Scoring reads frozen labels only after the attested completed run. Complete committed scores are verified and reused; partial or changed scores fail closed. The diagnostic ZIP is created inside the actual evaluation folder and selected in Explorer.

## Source-only architecture audit

This optional command reads unlabeled inputs and uses fake transports. It does not make predictions or produce F1:

```powershell
$audit49 = Join-Path $v49Eval ("pair_preflight_" + (Get-Date -Format "yyyyMMdd-HHmmss-fff") + ".json")
& $py "$dev49\development_tools\audit_v49_no_api.py" --evaluation "$v49Eval" --output "$audit49"
if ($LASTEXITCODE -ne 0) { throw "Offline audit failed. Send the complete error." }
```

## Evaluation target and promotion

The declared pilot target is **all-scope exact-triple F1 ≥0.80**; ≥0.85 is a stretch target. All 19 frozen reference triples remain in the denominator, including disputed scope cases. For example, TP14/FP2/FN5 yields 0.80; TP15/FP1/FN4 yields 0.857143; TP16/FP2/FN3 yields 0.864865. These examples are feasibility calculations, not predictions.

Keep every result, report baseline scope separately, and compare resource usage as well as F1. A passing pilot does not establish performance on the paper's broader dataset or held-out projects. Freeze a candidate before independent held-out validation; do not tune the frozen test labels or select only favorable repetitions. The current development fixture and previously inspected reference are not held-out data. Additional validation can expose losses from the checker as well as gains from explicit pair coverage.

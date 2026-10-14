# EvoRationale v4.4: complete captured-event review

This is an isolated development successor to v4.3. It addresses failures observed
on previously inspected KEP1287 development examples. The original S0, historical
runs, frozen reference, and exact-triple scorer retain their identities. No new
hosted v4.4 accuracy measurement has been made during package construction.

## Why v4.3 missed links

The supplied v4.3 trace read all 30 labeled hunks. Of the 18 missed exact triples
in the all scope, only one correct triple was proposed and rejected; the other
17 correct triples never reached the verifier. Reading a source did not mean
reviewing every rationale relation in that source. Query-specific passage
selection, lexical gates, and stopping work on an element after one accepted
link limited proposal coverage.

The H03 implementation supersession also needed the related H04 source context.
Conversely, the accepted C2a link came from a hunk that retained an existing QoS
invariant while changing emphasis and terminology. A surviving sentence alone
did not establish a new supporting change.

## What changes

- The opt-in `event-complete` profile reviews every selected artifact against
  every actual S0 element. Python requires one explicit review row per artifact
  and the complete element-ID set. These rows are model-reported coverage, not
  proof that the model recognized every relation.
- Complete captured unified diffs are prioritized. Sibling hunks are grouped
  only by pinned repository, full commit SHA, file, and capture identity.
  Captured context completeness does not assert that an entire external commit
  was captured. Split or incomplete contexts remain explicitly unresolved.
- Source text is transmitted once with mechanical line numbers. Exact citation
  handles cover every changed line without query-specific top-five filtering.
  Python resolves original quote bytes and keeps canonical version hashes.
  Prose uses exact text spans when a sentence starts midway through a line.
- An independent judge reviews the same complete captured event. It must assess
  the target hunk's material change, source role, affected claim, and relation.
  Unchanged invariants, bold formatting, terminology changes, and sibling
  relations automatically copied to other hunks cannot establish fresh links.
- Partial support for a material S0 claim is represented explicitly. It does
  not certify the entire compound element or resolve a central evidence need.
  A retained clause cannot mask replacement of another material clause in the
  same event. Proposed alternatives cannot establish adopted implementation.
- Existing repository, time, digest, element-type, confidence, and exact-quote
  checks remain. Secret-bearing citation windows are omitted rather than
  relabeled as verbatim redacted quotes. Source is treated as untrusted data.
- Actual request envelopes, including instructions and schemas, are estimated
  before each provider call and each of at most two JSON-output attempts. Hidden
  SDK retries are disabled in this profile. Provider-reported usage is recorded
  separately. Event requests enforce a 16,384-token output ceiling by default;
  a smaller explicit `--max-output-tokens` applies to original calls and retries.
  The output limit is per request, not a total billing cap. The UTF-8 estimator is not the provider tokenizer or a billing cap.
- Reports distinguish source reads, model-reported reviews, uncertain reviews,
  technical failures, partial support, whole support, and unreviewed sources.
  A bounded incomplete investigation remains `REVALIDATE` / `UNRESOLVED`.

The legacy `targeted` profile remains the CLI default. The v4.4 development
wrappers explicitly select `event-complete`, which currently requires hosted
API mode and the local immutable history backend. No new runtime dependency is
introduced. The local heuristic mode is not being presented as an improved
semantic accuracy baseline.

## First step on Windows: local tests and dry run

Save `EvoRationale_v44_EventCoverage_Reviewed_EN.zip` in the existing
project's `research` folder. Run from that project directory:

```powershell
$zip44 = Join-Path (Get-Location).Path "research\EvoRationale_v44_EventCoverage_Reviewed_EN.zip"
if (-not (Test-Path -LiteralPath $zip44)) { throw "Save the v4.4 ZIP in research first." }
$n44 = 1
do {
    $dev44Base = Join-Path $env:LOCALAPPDATA ("ERv44Dev{0:D2}" -f $n44)
    $n44++
} while (Test-Path -LiteralPath $dev44Base)
Expand-Archive -LiteralPath $zip44 -DestinationPath $dev44Base -ErrorAction Stop
$dev44 = Join-Path $dev44Base "EvoRationale_v44_DEV_EN"
$py = Join-Path $env:LOCALAPPDATA "er4venv\Scripts\python.exe"
& $py "$dev44\development_tools\start_v44_no_api.py"
if ($LASTEXITCODE -ne 0) { throw "v4.4 preparation stopped; inspect the error above." }
```

This runs the entire suite, chooses an unused evaluation folder, checks the
completed source receipts and hashes, copies only the exact original unlabeled
runtime inputs, and prints a dry-run command. It makes no provider request and
installs no package. Required default sources under `LOCALAPPDATA` are:

- `ER1287Eval_API01`
- `ER1287Eval_Offline01`
- `ER1287Gold\KEP1287_Reviewer_Confirmed_Freeze`
- `ER1287Eval_v43Dev01`, including its completed score

Supply `--original-api`, `--original-offline`, `--frozen`, or `--previous-v43`
if those folders differ. `--previous-v42` is optional. Keep the final printed
`evaluation` path. Expected status:

```text
V44_TESTS_AND_DRY_RUN_COMPLETED_NO_API_CALLED
```

An additional local source/budget preflight is available after preparation:

```powershell
$v44Eval = "COPY THE NEW evaluation PATH FROM THE HELPER OUTPUT"
& $py "$dev44\development_tools\audit_v44_no_api.py" --evaluation "$v44Eval"
if ($LASTEXITCODE -ne 0) { throw "Source preflight failed; inspect the error above." }
```

That audit uses synthetic model replies to inspect source coverage and request
size. Its scenario is not semantic predictions, a new run, or an F1 result.

## Hosted development run and unchanged scoring

The following command contacts the configured provider and may incur costs.
It reuses model IDs and nominal budgets from the completed v4.3 receipt. New
batching, request accounting, and partial-support scope mean this is not a claim
of an equal-compute experiment. A retry or more proposed links may consume the
remaining token estimate before all selected batches finish.

```powershell
& $py "$dev44\development_tools\run_v44.py" `
  --evaluation "$v44Eval" --code-root "$dev44" `
  --i-approve-public-repository-excerpts-to-openai
if ($LASTEXITCODE -ne 0) { throw "Run failed. Inspect the error before retrying." }

$freeze = Join-Path $env:LOCALAPPDATA "ER1287Gold\KEP1287_Reviewer_Confirmed_Freeze"
$oldAPI = Join-Path $env:LOCALAPPDATA "ER1287Eval_API01"
$oldOffline = Join-Path $env:LOCALAPPDATA "ER1287Eval_Offline01"
$v43Eval = Join-Path $env:LOCALAPPDATA "ER1287Eval_v43Dev01"
& $py "$dev44\development_tools\score_v44.py" `
  --evaluation "$v44Eval" --code-root "$dev44" `
  --frozen "$freeze" --original-api "$oldAPI" `
  --original-offline "$oldOffline" --previous-v43 "$v43Eval"
if ($LASTEXITCODE -ne 0) { throw "Scoring failed. Inspect the error above." }
$m = Get-Content "$v44Eval\score\metrics.json" -Raw -Encoding UTF8 | ConvertFrom-Json
@($m.results.baseline, $m.results.all) |
  Select-Object scope, tp, fp, fn, precision, recall, f1 | Format-Table -AutoSize
```

The wrappers refuse overwriting completed or partial experiments. Do not retry
a failed hosted run blindly in the same evaluation folder. Frozen labels are
used only after the hosted run by the unchanged scorer; they are not added to
agent inputs. Existing approval fields are never manufactured or changed.

## Additional fixes from the final review

- Source-exact safe citation ranges survive unrelated redacted neighboring text;
  a redacted changed line keeps citation coverage explicitly unresolved.
- Model review records become visible only after the entire batch contract passes.
  Invalid responses retain source-qualified technical feedback in checkpoints.
- Title text and title/body boundary joins cannot substitute for body citations.
  Judge source handles distinguish canonical versions even with identical hashes.
- Duplicate JSON keys, nonfinite numbers and nonterminal response text cannot
  become a semantic vote. Retry attempts remain bounded and separately charged.
- Accepted adverse central evidence answers a need without claiming positive
  support. Fully reviewed evidence can recommend REVISE or REOPEN; gaps and
  conflicting evidence remain REVALIDATE. Noncentral adverse scope cannot KEEP.
- Relative launch paths resolve before subprocess working-directory changes.
  Run attempts are claimed exclusively before provider calls, preventing
  simultaneous duplicate launches. Direct CLI reports are never overwritten.

## Validation and remaining limits

See `V44_TEST_REPORT.md` and `MANIFEST_V44_DEV.json`. Synthetic tests verify
contracts, orchestration, provenance, and failure behavior. Source-only replay
checks bounded selection and request construction. Neither establishes semantic
accuracy, improved F1, Windows execution, or generalization.

Two inspected all-scope I2/supersedes labels concern interim mutability policies
that the fixed original S0 I2 does not assert. They require a separate reference
policy review. This package does not invent those claims or modify that reference
to obtain a better score. Partial-support policy also changed from v4.3 and must
be locked before a new study. Independent histories and human adjudication are
still needed to evaluate performance. Historical v4.1/v4.2/v4.3 reports and
manifests included in this archive describe their original versions.

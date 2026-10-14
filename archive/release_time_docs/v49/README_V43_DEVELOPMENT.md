# EvoRationale v4.3: diff context and target scope

Development prototype based on the unchanged v4.2 package. This is not an
independent held-out evaluation or a certified historical replay. No new hosted
F1 result has been obtained for this version.

## What changes

- The hosted proposer receives a code-derived before/after comparison of each
  captured unified-diff hunk, alongside the original exact passage handles.
- Passage ranking favors windows showing additions and removals. The complete
  bounded hunk comparison remains available even when the five selected passages
  omit a relevant new clause.
- Linker and Judge share explicit relation definitions. Positive support must
  substantiate all material parts of the target. A surviving clause alone does
  not substantiate a compound element. A representation/API change does not by
  itself weaken an underlying requirement.
- For diff evidence, the Judge explicitly assesses full-element support, target
  scope, replacement/retirement, and the affected subclaim. Python rejects positive
  support with a negative full-element assessment, a scope mismatch, an
  unsupported replacement claim, and malformed response fields.
- A material part of a compound element can be superseded when replacement is
  source-backed and qualified. That does not imply the entire architecture or
  underlying goal was overturned. This is an operational definition requiring
  independent review before any new held-out study.
- Removed-only quotations cannot establish current positive support. Diff header
  counts are checked; incomplete or oversized comparisons fail closed. Context
  is bounded to a 6,000-character canonical diff, and sensitive strings are
  redacted in the derived views. Derived views are explanatory context, not exact
  citations. Original quote/version/hash/repository/time checks remain in force.
- Accepted and rejected diff judgments retain their structured assessment and
  complete explanation. Rejections also retain the proposed quote and relation.

These changes contain no repository-specific verdict rules or benchmark labels.
The frozen S0, human reference, and exact-triple scoring function are unchanged.
The offline heuristic proposer is otherwise unchanged, though the verifier now
also rejects removed-only positive evidence. Keep the original v4.1/v4.2 results
as the historical baselines.

## First step on Windows: tests and dry run only

Save `EvoRationale_v43_DiffScope_Development_EN.zip` in the existing project's
`research` directory. Extract it to a NEW local directory. Do not overwrite an
existing project or experiment.

```powershell
$zip43 = Join-Path (Get-Location).Path "research\EvoRationale_v43_DiffScope_Development_EN.zip"
if (-not (Test-Path -LiteralPath $zip43)) { throw "Save the v4.3 ZIP in research first." }
$n43 = 1
do {
    $dev43Base = Join-Path $env:LOCALAPPDATA ("ERv43Dev{0:D2}" -f $n43)
    $n43++
} while (Test-Path -LiteralPath $dev43Base)
Expand-Archive -LiteralPath $zip43 -DestinationPath $dev43Base -ErrorAction Stop
$dev43 = Join-Path $dev43Base "EvoRationale_v43_DEV_EN"
$py = Join-Path $env:LOCALAPPDATA "er4venv\Scripts\python.exe"
& $py "$dev43\development_tools\start_v43_no_api.py"
if ($LASTEXITCODE -ne 0) { throw "v4.3 preparation stopped; inspect the error above." }
```

The no-API helper runs the full test suite, chooses an unused evaluation directory,
copies the original EXACT unlabeled v4.1 inputs, verifies existing receipts and
hashes, reuses the opaque model IDs from the completed v4.2 experiment, and only
prints a dry-run command. It does not contact a provider, install packages, or
change previous experiments. If the source directories differ, supply:

```powershell
& $py "$dev43\development_tools\start_v43_no_api.py" `
  --original-api "$oldAPI" --original-offline "$oldOffline" `
  --frozen "$freeze" --previous-v42 "$gpt6Eval"
```

Default read-only sources are under `LOCALAPPDATA`: `ER1287Eval_API01`,
`ER1287Eval_Offline01`, `ER1287Gold\KEP1287_Reviewer_Confirmed_Freeze`, and
`ER1287Eval_v42_GPT6_01`. If a required source is missing, the helper stops and
names the argument to supply. Keep the printed `evaluation` path for later work.

Expected final status:

```text
V43_TESTS_AND_DRY_RUN_COMPLETED_NO_API_CALLED
```

## Later optional hosted development run

After inspecting the dry run, use the NEW evaluation path printed by the helper.
This is the only step below that contacts a provider and may incur charges. The
comparison adds context to model requests; the configured token budget is not
a dollar spending cap. Model identifiers are copied from the prior receipt;
immutable model snapshots and current account access are not established here.

```powershell
$v43Eval = "COPY THE NEW evaluation PATH FROM THE HELPER OUTPUT"
& $py "$dev43\development_tools\run_v43.py" `
  --evaluation "$v43Eval" --code-root "$dev43" `
  --i-approve-public-repository-excerpts-to-openai
```

Do not blindly retry a failed hosted run in the same directory. The tool refuses
overwriting runs and checkpoints. It does not change authoritative S0.

Only after a completed, hashed run exists:

```powershell
& $py "$dev43\development_tools\score_v43.py" `
  --evaluation "$v43Eval" --code-root "$dev43" `
  --frozen "$freeze" --original-api "$oldAPI" `
  --original-offline "$oldOffline" --previous-v42 "$gpt6Eval"
```

The scorer retains the same exact-triple rule and frozen population, and adds an
optional descriptive v4.2 comparison. All results remain development observations.
Both the known reference labels and these failure cases informed development.
Fresh independent histories, a locked relation definition, and human review are
needed to evaluate generalization.

## Validation and practical limits

See `V43_TEST_REPORT.md` and `MANIFEST_V43_DEV.json`. Automated tests use synthetic
model replies; they establish code behavior and source integrity, not the ability
of a real model to recognize partial support or architectural replacement.
Windows execution must still be confirmed on the user's machine. A source-backed
model vote remains fallible and requires substantive human review.

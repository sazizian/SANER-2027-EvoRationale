# EvoRationale v4.2 — Research Development Prototype

**This is a development-only prototype.** It is neither the released v4.1 baseline nor a certified historical replay, and its evaluation is not held out. Do not replace the original v4.1 project or the reviewer-confirmed KEP-1287 frozen reference.

## Changes from v4.1

1. **Exact passage handles.** The LLM selects a short, source-backed `passage_handle`. Python resolves that handle to a verbatim substring of the retrieved canonical artifact. The independent verifier still checks artifact version, content hashes, timestamps, exact quote, and semantic relation. The model cannot create a valid citation merely by writing arbitrary prose.
2. **Wrapped passage extraction.** The extractor additionally offers short windows of adjacent lines (including Git patch prefixes), preserving the *exact* original bytes. It does not splice unrelated Markdown bullet items.
3. **Factual design assertions — hosted judge only.** For positive claims, a narrow descriptive-assertion screen is available when there are at least three overlapping terms. Document-format acronyms such as `KEP` are not mandatory subject tokens in this mode. The deterministic offline baseline retains the original v4.1 screening and single-line passage selection to prevent spurious `KEEP` outcomes. The independent LLM judge remains fail-closed.
4. **Structured rejection telemetry.** Invalid passage handles, model IDs, and confidence values are rejected before they become evidence links; a diagnostic is recorded rather than silently repaired.

All 135 inherited tests and 5 new safety-focused tests must pass before external model use. A no-API Kubernetes smoke run retained `REVALIDATE / UNRESOLVED` after these changes. The v4.1 code tree originally used for this package hashes to `83655ad7b7a65fc298073384975394f38fbf32b44f91cf443a73993a6b4fd27c` and is distinct from this v4.2-development tree.

## Windows / Cursor PowerShell workflow

From the **original v4.1** Cursor project folder, download `EvoRationale_v42_DEV_EN.zip` to `research`. Then:

```powershell
$env:PYTHONUTF8 = "1"
$py = Join-Path $env:LOCALAPPDATA "er4venv\Scripts\python.exe"
$devBase = Join-Path $env:LOCALAPPDATA "ERv42Dev01"
$dev = Join-Path $devBase "EvoRationale_v42_DEV_EN"
$devEval = Join-Path $env:LOCALAPPDATA "ER1287Eval_v42Dev01"
$freeze = Join-Path $env:LOCALAPPDATA "ER1287Gold\KEP1287_Reviewer_Confirmed_Freeze"
$oldOffline = Join-Path $env:LOCALAPPDATA "ER1287Eval_Offline01"
$oldAPI = Join-Path $env:LOCALAPPDATA "ER1287Eval_API01"
if ((Test-Path $devBase) -or (Test-Path $devEval)) { throw "Development destination exists; choose unused names." }
Expand-Archive -LiteralPath ".\research\EvoRationale_v42_DEV_EN.zip" -DestinationPath $devBase
Push-Location $dev
& $py -m pytest -q
& $py -c "import evorationale; print(evorationale.__file__)"
& $py "$dev\development_tools\prepare_v42.py" `
  --original-api "$oldAPI" --original-offline "$oldOffline" `
  --frozen "$freeze" --code-root "$dev" --output "$devEval"
& $py "$dev\development_tools\run_v42.py" `
  --evaluation "$devEval" --code-root "$dev" --dry-run
Pop-Location
```

**Stop here first.** These preparation and dry-run commands use **no OpenAI API** and create no hosted-model charges. Confirm the output before making a new model call. The original API receipt, frozen S0, and 53 unlabeled artifacts must hash-match.

### Optional later: hosted v4.2 development run

This step may incur API charges, requires organizational authorization for sending excerpts, and requires an explicit consent flag. Do not run until the preparation and dry-run checks have succeeded.

```powershell
Push-Location $dev
& $py "$dev\development_tools\run_v42.py" `
  --evaluation "$devEval" --code-root "$dev" `
  --i-approve-public-repository-excerpts-to-openai
Pop-Location
```

Only after that completes, compare to the unchanged frozen reference:

```powershell
& $py "$dev\development_tools\score_v42.py" `
  --evaluation "$devEval" --frozen "$freeze" --code-root "$dev" `
  --original-api "$oldAPI" --original-offline "$oldOffline"
```

No Gold labels are copied into agent inputs. Gold labels are read **only after** a completed and hashed run receipt is present. The same exact-triple scoring rule is reused across v4.1 and v4.2; changes in score are development observations only.

## Research safeguards

- Do not weaken exact evidence citation, canonical version, source hash, access policy, or temporal provenance checks.
- Do not automatically accept model outputs; independently assess the relation on exact source text.
- Do not confuse a descriptive statement with proof of the original rationale or a correct architectural decision.
- The existing human labels were inspected during debugging. To claim generalization, gather new, independently reviewed, held-out GitHub histories *after* finalizing the method.
- The 2024 timeline is retrospective; the original capture did not certify 2024 availability of all evidence.
- Source text sent to the provider is minimized and screened, but the protection is best-effort and is not a confidentiality guarantee.

**Development code tree hash:** `ab892cc339348fc6db243ecbdb18cb6df3a4959d5636332d5f2cdb7945fbdd09`

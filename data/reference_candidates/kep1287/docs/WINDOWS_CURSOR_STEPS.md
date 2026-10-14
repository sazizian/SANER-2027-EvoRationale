# Windows / Cursor Quick Start

Keep the EvoRationale v4.1 code project unchanged.

1. Place `KEP1287_Gold_Candidate_EN.zip` in the project `research` folder (archive copy).
2. From that EvoRationale v4.1 project terminal, extract to a SHORT, EMPTY directory:

```powershell
$dest = Join-Path $env:LOCALAPPDATA "ER1287Gold"
Test-Path $dest
# If False:
Expand-Archive -LiteralPath ".\research\KEP1287_Gold_Candidate_EN.zip" -DestinationPath $dest
```

3. Verify the package:

```powershell
$env:PYTHONUTF8 = "1"
$py = Join-Path $env:LOCALAPPDATA "er4venv\Scripts\python.exe"
& $py "$dest\KEP1287_Gold_Candidate_EN\scripts\verify_candidate.py"
```

Expected: `PASS_CANDIDATE_NOT_FROZEN_GOLD`.

4. Open `KEP1287_Candidate_Reference_Review.xlsx` and examine `Readiness Checks` and `S0 Atomic`.
5. Archive confirmation records from Reviewer A and B; enter them in the `reference_private/REVIEWER_CONFIRMATION_TEMPLATE.csv` without altering original independent submissions.
6. Once both reviewers' exact decisions are documented, freeze in a new separate folder:

```powershell
& $py "$dest\KEP1287_Gold_Candidate_EN\scripts\freeze_reference.py" `
  --confirmations "$dest\KEP1287_Gold_Candidate_EN\reference_private\REVIEWER_CONFIRMATION_TEMPLATE.csv" `
  --output "$dest\KEP1287_Reviewer_Confirmed_Freeze"
```

7. Only then approve the frozen S0 inside a *separate study execution environment*. Do not pass the reference-private files to the agent.
8. The CLI source archive and the 2024 change window must never be called a certified historical replay. Read `docs/EVALUATION_PROTOCOL.md`.

This is a working research dataset, not yet a released/peer-reviewed gold benchmark.

# Windows setup and manual GitHub publishing

Use a new folder for this export. Preserve the existing
`EvoRationale_PaperAligned_v4_FULL_TESTED` workspace and the paid Primary Effects
run currently in progress. The following local steps do not publish anything
and do not contact a model provider.

## 1. Extract the repository

Download `EvoRationale_GitHub_Reviewed_EN.zip` and save it in Downloads. Paste the
following into PowerShell without the `PS ...>` or `>>` prompt characters:

```powershell
$zipRepo = Join-Path $env:USERPROFILE "Downloads\EvoRationale_GitHub_Reviewed_EN.zip"
if (-not (Test-Path -LiteralPath $zipRepo -PathType Leaf)) {
    $zipRepo = (Read-Host "Paste the full path to the downloaded repository ZIP").Trim().Trim('"')
}
if (-not (Test-Path -LiteralPath $zipRepo -PathType Leaf)) { throw "ZIP file not found." }

$parentRepo = Join-Path $env:USERPROFILE ("Documents\EvoRationale_GitHub_" + (Get-Date -Format "yyyyMMdd-HHmmss-fff"))
if (Test-Path -LiteralPath $parentRepo) { throw "Destination already exists; use a new folder." }
Expand-Archive -LiteralPath $zipRepo -DestinationPath $parentRepo -ErrorAction Stop
$repo = Join-Path $parentRepo "EvoRationale_GitHub"
if (-not (Test-Path -LiteralPath "$repo\pyproject.toml" -PathType Leaf)) { throw "Repository root not found." }
Set-Location -LiteralPath $repo
$repo
```

In Cursor, choose **File → Open Folder** and open the displayed `$repo` path.
The repository root contains `README.md`, `pyproject.toml` and `evorationale`.
Open `data\README.md` for the central resource guide and
`data\RESOURCE_INDEX.csv` for the file inventory. The `data\excel` folders hold
available original workbooks; `data\github` holds captured GitHub resources.
These are included in the repository and should remain in the commit.
The historical code-release ZIPs are English adaptations identified in
`docs\ARCHIVE_LANGUAGE_ADAPTATIONS.json`. Use the current export verifier;
historical checksum files are dated source records, not checksums of these
adapted archive copies. Diagnostic/reference ZIPs and measured evidence remain
unchanged.

## 2. Use Python directly and check integrity

The user's existing environment can run the standard-library-only verifier:

```powershell
$pyRepo = Join-Path $env:LOCALAPPDATA "er4venv\Scripts\python.exe"
if (-not (Test-Path -LiteralPath $pyRepo -PathType Leaf)) {
    throw "Existing Python not found. Use the new-environment option below."
}
& $pyRepo "$repo\tools\verify_bundle.py"
if ($LASTEXITCODE -ne 0) { throw "Export verification failed; send the complete output." }
```

For a new environment, Python 3.11+ and the Windows Python launcher are required:

```powershell
$envRootRepo = Join-Path $env:LOCALAPPDATA "EvoRationaleGitHubVenv"
if (-not (Test-Path -LiteralPath "$envRootRepo\Scripts\python.exe" -PathType Leaf)) {
    py -3 -m venv "$envRootRepo"
    if ($LASTEXITCODE -ne 0) { throw "Environment creation failed." }
}
$pyRepo = Join-Path $envRootRepo "Scripts\python.exe"
& $pyRepo "$repo\tools\verify_bundle.py"
if ($LASTEXITCODE -ne 0) { throw "Export verification failed; send the complete output." }
```

No `Activate.ps1` execution is needed. Calling the environment's `python.exe`
directly avoids the PowerShell activation-policy problem encountered earlier.

## 3. Run local tests and forecasts

From the extracted repository root:

```powershell
Set-Location -LiteralPath $repo
& $pyRepo -m pip install -e '.[test,openai]'
if ($LASTEXITCODE -ne 0) { throw "Dependency installation failed." }
& $pyRepo "$repo\tools\run_local_checks.py"
if ($LASTEXITCODE -ne 0) { throw "Local checks failed; send the complete output." }
```

Installation can download packages. Installing the OpenAI SDK does not call a
model provider. The local checker runs the active v4.9 tests, experiment tests,
tool tests and forecasts, without an API key or paid inference. Windows and
Linux may report different native-test skip counts.

To forecast the fresh experiment separately, use the exported v4.9 source and
completed parent run, with a new output path:

```powershell
$kitRepo = Join-Path $repo "experiments\primary_effects_windows_fix"
$parentRunRepo = Join-Path $repo "data\results\runs\v49"
$forecastOutputRepo = Join-Path $env:LOCALAPPDATA ("ERPrimaryForecast_" + (Get-Date -Format "yyyyMMdd-HHmmss-fff"))
& $pyRepo "$kitRepo\start_primary_effect_no_api.py" --code-root "$repo" --evaluation "$parentRunRepo" --output "$forecastOutputRepo"
if ($LASTEXITCODE -ne 0) { throw "Primary-effects forecast failed." }
```

Expected status: `PRIMARY_EFFECT_DRY_RUN_NO_API_CALLED`. A complete forecast is
not measured F1 and creates no inference-output directory. The standalone
historical guides retain their original `LOCALAPPDATA` examples; the commands
above use the portable export paths explicitly.

## 4. Create a local Git commit

Install Git for Windows if `git --version` is unavailable. The supplied
`.gitattributes` contains `* -text`; preserve it so Git does not convert line
endings in hash-pinned source and records.

```powershell
Set-Location -LiteralPath $repo
git --version
if ($LASTEXITCODE -ne 0) { throw "Install Git for Windows before continuing." }
if (Test-Path -LiteralPath ".git") { throw "Use the newly extracted export folder." }
git init -b main
if ($LASTEXITCODE -ne 0) { throw "Git initialization failed." }
git config --local core.autocrlf false
if ($LASTEXITCODE -ne 0) { throw "Git configuration failed." }
git add -- .
if ($LASTEXITCODE -ne 0) { throw "Git staging failed." }
git status --short
git diff --cached --stat
```

Inspect the staged file list. Keep environment directories, populated `.env`
files and API keys out of the commit. The curated `data/results/runs` evidence is
intended to be included. Then create the local commit:

```powershell
git commit -m "Add EvoRationale code and development evidence"
if ($LASTEXITCODE -ne 0) { throw "Commit failed; inspect the Git message." }
git log -1 --format="%H"
```

If Git requests an author identity, set the desired name and email with
`git config --local user.name` and `git config --local user.email`, then retry
the commit. This step creates a local commit only.

## 5. Publish manually to an empty GitHub repository

On GitHub, create an empty repository with your chosen name and visibility.
Do not initialize it with a README, license or gitignore because these already
exist locally. Copy its HTTPS URL. Git/GitHub handles authentication; do not put
a token in the URL or commit one.

The following is the separate publishing step:

```powershell
$remoteRepo = (Read-Host "Paste the empty GitHub repository HTTPS URL").Trim()
if ($remoteRepo -notmatch '^https://github\.com/[^/]+/[^/]+(?:\.git)?/?$') {
    throw "Expected an empty repository URL on github.com."
}
git remote add origin "$remoteRepo"
if ($LASTEXITCODE -ne 0) { throw "Remote setup failed." }
git remote -v
git push -u origin main
if ($LASTEXITCODE -ne 0) { throw "Push failed; inspect the Git message." }
```

This workflow does not force-push or overwrite an existing remote. If the remote
is already populated, preserve its history and use a branch/merge workflow
instead of these empty-repository steps.

GitHub browser uploads allow up to 25 MiB per file; command-line uploads allow
up to 100 MiB per file. Larger individual files require an appropriate
large-file/release workflow. Use the export's size report to determine whether
that applies.

## 6. Record the pending result after it finishes

Keep the original paid run where it completed. Import its verified diagnostic
ZIP into a new `data/results/runs/<new-run-name>/` folder, preserving the exact bytes.
Record its run ID, toolkit/source/input/reference identities and ZIP hash in a
new evidence-index entry. Update the comparison table only after local
verification. Do not overwrite another run's metrics or edit its receipt.

If a completed Primary Effects result is moved, the existing scorer supports
`--source-evaluation` to locate its unchanged original v4.9 parent. This is a
path override, not permission to change its source records.

The export manifest describes this snapshot. New evidence or documentation
requires a new manifest/release; do not edit the existing manifest merely to
hide an integrity failure. Publish the final reviewed snapshot under a fixed
commit or tag and cite that identity in the paper.

## Official workflow references

- [GitHub: adding locally hosted code](https://docs.github.com/en/migrations/importing-source-code/using-the-command-line-to-import-source-code/adding-locally-hosted-code-to-github)
- [GitHub: adding files and size limits](https://docs.github.com/en/repositories/working-with-files/managing-files/adding-a-file-to-a-repository?platform=windows)
- [Git: attributes and byte-preserving `-text`](https://git-scm.com/docs/gitattributes)

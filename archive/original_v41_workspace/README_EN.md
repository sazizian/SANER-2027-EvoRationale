# EvoRationale v4: Short English guide

This is an English translation of the historical v4 guide. Its instructions, observations, and research caveats describe that release. Use the current repository quick start for current work.

This is a **complete project**. Extract it into a **new, separate directory** and keep the previous v2/v3 installation intact. Offline and mocked API tests were run before delivery. However, this package is not a verified reproduction of the private experiments described in the SANER 2027 paper.

## Suggested location for Windows and Cursor

Use a new directory:

`...\SANER 2027\CODE\EvoRationale_PaperAligned_v4`

In Cursor, select **File > Open Folder** and open this directory rather than the directory containing earlier ZIP archives.

## 1. Install and run tests without OpenAI costs

In a terminal inside the v4 directory:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -e ".[test]"
.\.venv\Scripts\python.exe scripts\verify_release.py
```

All tests should pass, and the output should include `OFFLINE_RELEASE_SMOKE_TEST: PASS`. The test count is recorded in `docs/V4_TEST_REPORT.md`.

## 2. Run the Azure pilot from a fixed snapshot

This package includes a **public GitHub sample from an earlier run**. Your original v3 files remain unchanged. Before approval, compare `examples\azure\pilot_snapshot\decision_state_ATOMIC_DRAFT.json` with PR #1803.

```powershell
.\.venv\Scripts\python.exe -m evorationale approve-state --draft examples\azure\pilot_snapshot\decision_state_ATOMIC_DRAFT.json --central-ids G1 I1a I1b I1c --output examples\azure\pilot_snapshot\decision_state_ATOMIC_APPROVED.json

.\.venv\Scripts\python.exe -m evorationale validate --decision examples\azure\pilot_snapshot\decision_state_ATOMIC_APPROVED.json --history examples\azure\pilot_snapshot\history_LIVE.jsonl

.\.venv\Scripts\python.exe -m evorationale run --decision examples\azure\pilot_snapshot\decision_state_ATOMIC_APPROVED.json --history examples\azure\pilot_snapshot\history_LIVE.jsonl --output outputs\azure-v4-offline --mode offline --max-rounds 3 --max-queries 9 --max-reads 16 --max-input-tokens 32000
```

Open the following outputs:

```powershell
notepad outputs\azure-v4-offline\report.json
notepad outputs\azure-v4-offline\trace.json
notepad outputs\azure-v4-offline\data_audit.json
```

In the package's build test, `I1b` obtained checkbox evidence from PR #1880. PR #2083 was not accepted as confirming evidence because the available snapshot contained no direct AVNM evidence for it. **REVALIDATE / UNRESOLVED** can still be the correct result because the snapshot is limited and some components lack direct evidence.

## 3. Optional OpenAI experiment after offline review

Install the model dependency first:

```powershell
.\.venv\Scripts\python.exe -m pip install -e ".[openai,test]"
```

**Do not put an API key in the conversation, ZIP archive, or GitHub.** Enter it only in your own terminal:

```powershell
$secure = Read-Host "OpenAI API Key" -AsSecureString
$env:OPENAI_API_KEY = ([System.Net.NetworkCredential]::new("", $secure)).Password
Remove-Variable secure
```

An API run may incur costs. Use **models available to your API account**:

```powershell
.\.venv\Scripts\python.exe -m evorationale run --decision examples\azure\pilot_snapshot\decision_state_ATOMIC_APPROVED.json --history examples\azure\pilot_snapshot\history_LIVE.jsonl --output outputs\azure-v4-api --mode api --allow-repository-text-to-api --model YOUR_AVAILABLE_MODEL --judge-model YOUR_AVAILABLE_JUDGE_MODEL --max-rounds 3 --max-queries 9 --max-reads 16 --max-input-tokens 32000
```

## Research caveats at the time of this release

These data came from the current GitHub snapshot. Historical versions of edited PR text cannot be established without an archive. `PASS` means that structure and extracted evidence satisfy the program's validation rules; it does not establish the final correctness of an architectural decision. The offline UCR value is also not an independent human evaluation.

For a scientific study, historical-version validity, dataset completeness, human reference labels, fixed models and settings, and baselines still require separate verification.

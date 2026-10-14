# English quickstart

This repository contains the available EvoRationale code, data, resources and
development evidence. Keep the existing workspace and Primary Effects run in
their current locations. Extract this export into a new folder.

## Follow these steps

1. Download `EvoRationale_GitHub_Reviewed_EN.zip`.
2. Follow step 1 of the [Windows guide](WINDOWS_GITHUB_GUIDE_EN.md) to extract it.
   In Cursor, choose **File → Open Folder** and select the displayed repository
   path. Its top-level folder is `EvoRationale_GitHub`.
3. Follow steps 2 and 3 of that guide to verify the files and run local checks.
   Call `python.exe` directly; `Activate.ps1` is unnecessary. Verification and
   local forecasts do not need an API key or make a model-provider call.
4. Open [`data/README.md`](../data/README.md) to locate the inputs, GitHub
   captures, Excel workbooks, reference files and genuine result records.
5. After the checks pass, follow steps 4 and 5 of the Windows guide to commit
   locally and push to a new empty GitHub repository. The package does not
   publish automatically.
6. Use the [paper guide](PAPER_EVIDENCE_GUIDE.md) to connect each reported
   result to its exact run and evaluation scope.

## Where to look

| Path | Purpose |
|---|---|
| `README.md` | Current status, measured comparison and repository map |
| `evorationale/` | Pinned active v4.9 runtime code |
| `experiments/primary_effects_windows_fix/` | Fresh experiment and Windows checkpoint repair |
| `data/inputs/kep1287/` | Fixed runtime S0 and 53-artifact history |
| `data/github/kep1287_capture_2023_2024/` | GitHub source captures, diffs and metadata |
| `data/excel/` | Available original supplied and review workbooks |
| `data/results/runs/` | Reports, checkpoints, scores and error tables from completed supplied runs |
| `data/results/summary.csv` | Readable comparison derived from those raw runs |
| `data/references/frozen_reference/` | Unchanged post-run scoring reference |
| `data/RESOURCE_INDEX.csv` | File-level resource index; open it in Excel or a text editor |
| `archive/` | Historical code and code-release copies with English documentation and fixtures |

The Excel workbooks are research resources. They do not replace the confirmed
frozen reference and are not model inputs. Use the resource index to identify
their original locations and checksums. The captured GitHub resources are
snapshots, not a complete clone or a claim to contain every upstream file.
`data/excel/source_pilot_workbooks/` contains resources for separate pilot cases;
these workbooks are not KEP 1287 Gold or additional scored runs.
There are nine workbook files representing eight distinct byte identities;
`data/excel/WORKBOOK_INDEX.csv` identifies the source and role of each.

The historical code-release ZIPs in this English export are adapted copies.
`docs/ARCHIVE_LANGUAGE_ADAPTATIONS.json` records original and adapted identities.
Production runtime code, research data, Gold reference and measured results are
unchanged. Original diagnostic/reference ZIPs retain their exact bytes.

## Current result status

The supplied Windows preflight passed **98 tests and 6 subtests**. It forecast
12 fresh classification requests and no independent critic. Tests and forecasts
do not measure F1. The fresh Primary Effects hosted result is still pending in
this repository snapshot.

Among the existing completed runs, the largest `all` F1 is **0.636364**, from
v4.9. The largest `baseline` F1 is **0.689655**, from v4.6. These are results
from one inspected development case. No F1 above 80% is established by this
package.

When the fresh run finishes, preserve its diagnostic ZIP and add it as a new
verified record. Keep older results unchanged. Follow the evidence guide when
using scores in the paper; archived manuscript text and local test counts do
not establish new experimental measurements.

Preserve `.gitattributes` and use repository-local `core.autocrlf=false` before
staging so Git retains the exact bytes of pinned code and evidence.

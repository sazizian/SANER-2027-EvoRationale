# Data and resource guide

This is the central location for the data and research resources available in
this repository snapshot. It includes the supplied inputs, captured public
GitHub material, available Excel workbooks, annotation resources, frozen scoring
reference, genuine completed results and technical validation logs.

Start with [`RESOURCE_INDEX.csv`](RESOURCE_INDEX.csv) for a file-level listing
you can open in Excel. [`RESOURCE_INDEX.json`](RESOURCE_INDEX.json) provides the
machine-readable catalog. The catalogs record source paths, resource roles and
SHA-256 identities. They distinguish preserved resources from derived files.

## Folder map

| Folder | What it contains | How to use it |
|---|---|---|
| [`inputs/kep1287/`](inputs/kep1287/) | Canonical runtime S0 and the complete 53-artifact post-S0 history copied from the completed v4.9 input snapshot | Fixed inputs for reproducing the documented case; keep their bytes unchanged |
| [`github/kep1287_capture_2023_2024/`](github/kep1287_capture_2023_2024/) | Public GitHub source captures, diff text, metadata and recorded source identities | Inspect the actual captured repository evidence and its provenance |
| [`github/azure_avnm_diff_v41/`](github/azure_avnm_diff_v41/) and [`github/GITHUB_SOURCES.csv`](github/GITHUB_SOURCES.csv) | Available Azure capture resources and a cross-resource GitHub source index | Trace the separate Azure example and recorded upstream URLs |
| [`excel/supplied_workbooks/`](excel/supplied_workbooks/) | Available supplied Excel resources | Read the original workbook contents; identify their source and checksum in the resource index |
| [`excel/review_workbooks/`](excel/review_workbooks/) | Available consensus, reconciliation and review workbooks | Inspect annotation and review resources without changing the frozen reference |
| [`excel/source_pilot_workbooks/`](excel/source_pilot_workbooks/) | Available source-pilot Excel resources supplied with prior project material | Inspect these separate cases; do not use them as KEP 1287 Gold or measured run records |
| [`reference_candidates/`](reference_candidates/) | Candidate annotation tables, review notes, audit documents and source indexes | Understand how research resources were prepared; candidate records are not automatically Gold labels |
| [`references/frozen_reference/`](references/frozen_reference/) | Original confirmed frozen reference and confirmation records | Post-run scoring only; exclude labels and notes from model input |
| [`baseline_context/`](baseline_context/) | Pinned public baseline README used by the fresh Primary Effects experiment | Interpret the fixed decision with the documented additional context; this is not fresh post-S0 proof |
| [`examples/azure/`](examples/azure/) and [`examples/redis/`](examples/redis/) | Available example input and output resources | Inspect separate examples; do not confuse Azure PR 1803 output with the KEP 1287 evaluation |
| [`resources/original_workspace/`](resources/original_workspace/) | Available uploaded workspace research, documentation and output resources | Trace resources to the original workspace without duplicating the active runtime code |
| [`results/runs/`](results/runs/) | Exact supplied report, checkpoint, input, receipt, score and error files for completed runs | Use these files as the primary evidence for measured results |
| [`results/validation/`](results/validation/) | Test logs, forecasts, replay checks and export verification records | Assess technical validation; these logs do not measure hosted semantic accuracy |
| [`packages/diagnostics/`](packages/diagnostics/) | Original supplied diagnostic ZIPs | Retain the exact source packages and compare member hashes |
| [`packages/reference/`](packages/reference/) | Original supplied frozen-reference ZIP | Preserve the original reference package identity |

The nine Excel files represent eight distinct byte identities. The
[`excel/WORKBOOK_INDEX.csv`](excel/WORKBOOK_INDEX.csv) and
[`excel/WORKBOOK_INDEX.json`](excel/WORKBOOK_INDEX.json) identify each workbook,
its source, role and checksum. Duplicate workbook bytes are reported explicitly;
they do not create an additional independent dataset. Available workbooks retain
their original bytes.

Repository guides and documentation inside the historical code-release ZIP
copies are in English. Those code archives are adapted copies, with original
and adapted hashes recorded in
[`docs/ARCHIVE_LANGUAGE_ADAPTATIONS.json`](../docs/ARCHIVE_LANGUAGE_ADAPTATIONS.json).
Production runtime code and research evidence are not translated or silently
rewritten. The diagnostic and frozen-reference ZIPs under `data/packages/`
retain their exact original bytes. Historical code-package checksum files are
dated attestations, not checksums of the newly adapted English archives; the
current export manifest identifies this snapshot.

## Keep the roles separate

The fixed runtime S0 and history are inference inputs. The scoring reference
contains labels and is read only after a completed run. Excel review workbooks,
candidate annotations and manuscript resources are available for research
inspection; they must not be injected into the model to improve the measured
score.
The source-pilot workbooks describe separate repository cases. Their inclusion
is resource preservation and does not create additional measured KEP 1287 runs.

The frozen reference evaluates 30 hunks and 19 positive exact triples in `all`,
and 24 hunks and 14 positives in `baseline`. It has no architecture-outcome Gold
and does not certify a historical replay. This case and its annotations were
inspected during development, so it is not independent held-out data.

The GitHub material here is captured public evidence for the documented case,
with source URLs and version identities where supplied. It is not a full clone
of Kubernetes or Azure. The top-level project code is the implementation to
publish to your GitHub repository; `data/github/` holds its research resources.

## Results you can use

[`results/summary.csv`](results/summary.csv) and
[`results/summary.json`](results/summary.json) contain the verified comparison.
[`results/index.json`](results/index.json) links each run to its exact records,
usage, original ZIP and provenance limitations. For report and metric links,
read the [evidence guide](../docs/EVIDENCE_GUIDE.md).

The fresh Primary Effects Windows Fix hosted result is **pending**. Its Windows
preflight and local forecast are technical checks. The catalog and summaries do
not invent a run ID, score, billing amount or timing to fill that gap.

The uploaded resources available to this snapshot are included and indexed.
An index cannot establish that an unprovided workbook, external database,
private study dataset or future result exists here. Missing original KEP 1287
v4.1 API/offline and v4.3 run records remain identified as missing; inherited
comparison numbers and separate Azure outputs are not substitutes.

## Verify before publishing or writing the paper

From the repository root, run the standard-library-only check:

```powershell
& $pyRepo "$repo\tools\verify_bundle.py"
if ($LASTEXITCODE -ne 0) { throw "Repository verification failed." }
```

This verifies the export snapshot and recorded results without a provider call.
Use the [Windows guide](../docs/WINDOWS_GITHUB_GUIDE_EN.md) to set `$repo` and
`$pyRepo`, run local tests and publish manually. Use the
[paper guide](../docs/PAPER_EVIDENCE_GUIDE.md) to report defensible results.

Keep raw evidence unchanged. Add genuinely new resources or results under new
paths, record their identities and roles, and issue a new verified snapshot.
Do not overwrite a historical score or edit its receipt.

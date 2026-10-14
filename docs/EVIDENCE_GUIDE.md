# Evidence files and run provenance

[`data/README.md`](../data/README.md) explains the central data folders.
[`data/RESOURCE_INDEX.csv`](../data/RESOURCE_INDEX.csv) lists the available
GitHub captures, input snapshots, Excel workbooks and other research resources
with their source paths and identities. This broader resource catalog is
separate from the measured-run catalog below.

`data/results/index.json` is the detailed catalog for this export. It records exact
source/export paths, original diagnostic ZIP identities, member hashes,
reference population, request usage and limitations. The raw run files are
preserved rather than rewritten into a uniform layout.

[summary.json](../data/results/summary.json) and [summary.csv](../data/results/summary.csv)
provide the derived comparison: fourteen measured scope rows and an explicitly
pending Primary Effects entry. The raw files remain the evidence of each run.

## Completed supplied development runs

| Run | Exact run ID | Raw metrics | Raw report |
|---|---|---|---|
| v4.4 | `472626dc-dd7c-48c5-8a94-3420bb8c4ef4` | [metrics](../data/results/runs/v44/metrics.json) | [report](../data/results/runs/v44/report.json) |
| v4.5 | `e98cc3a9-fe80-4db8-99d9-cc23a64c115f` | [metrics](../data/results/runs/v45/score/metrics.json) | [report](../data/results/runs/v45/run/report.json) |
| v4.6 | `188132b4-7975-4ae9-8df4-0cbbc1cad9ad` | [metrics](../data/results/runs/v46/score/metrics.json) | [report](../data/results/runs/v46/run/report.json) |
| v4.7 | `a50dd556-729c-4840-a509-0fdd9222b81b` | [metrics](../data/results/runs/v47/score/metrics.json) | [report](../data/results/runs/v47/run/report.json) |
| v4.8 | `201e1b3a-2e27-431c-ba03-0c9a822af43f` | [metrics](../data/results/runs/v48/score/metrics.json) | [report](../data/results/runs/v48/run/report.json) |
| v4.9 | `8096127b-4cbd-4e77-a9c4-a9c2c5dc0c03` | [metrics](../data/results/runs/v49/score/metrics.json) | [report](../data/results/runs/v49/run/report.json) |
| Cached scope recheck | `fbb1c892-88e4-4e49-80cb-0a433eaaa87a` | [metrics](../data/results/runs/scope_recheck/score/metrics.json) | [report](../data/results/runs/scope_recheck/run/report.json) |

Each run folder also contains its original `RUN_RECEIPT.json`, checkpoint,
inputs and `link_errors.csv` in the layout captured by its diagnostic package.
Run receipts link bytes and identities; they do not independently authenticate
provider execution. The raw diagnostic ZIPs are in
`data/packages/diagnostics/`.

v4.4 was supplied as a flat ZIP. Its original `DEV_PREP_MANIFEST.json`,
`run/manifest.json`, `score/SCORE_RECEIPT.json` and diagnostic-bundle manifest
were not included. Its available report/checkpoint/receipt and score are
preserved, and its exact metrics/errors can be recomputed. Do not describe
this as the same complete provenance package as later versions.

## Recompute the existing metrics locally

From the repository root, using Python 3.11+:

```powershell
& $pyRepo "$repo\tools\verify_results.py"
if ($LASTEXITCODE -ne 0) { throw "Result verification failed." }
```

This is a read-only local verification operation, not new inference. It uses the
unchanged v4.9 evaluator and the original frozen reference. The seven runs
produce fourteen scope rows. The new Primary Effects hosted result remains
pending. Raw metrics and reference labels must not be edited to improve scores.

The optional `--write-summary` flag regenerates `data/results/summary.json` and
`data/results/summary.csv` deterministically after verification. Routine inspection
does not need that flag. Changed evidence requires a new export manifest/release.

The current v4.9 runtime source tree hash is
`a0e1b1c0156e48d6a4bdae27a02fdfd9e0bedfbdd05bac79c2db812468937b22`.
The exact-triple scorer `_score_core.py` hash is
`18553a3a195a490102348e199233ef4ae752efaf8b80e351e52ff354c6d88895`.
These pins identify source bytes, not experimental accuracy.

## Fixed inputs and scoring reference

| Item | Identity / population |
|---|---|
| Runtime S0 | SHA-256 `a852f931aa41c2f67b1522651665feb67fad9d92116413553405fb3d9c3ba784` |
| History | SHA-256 `30f89a8dae945eb588898134b23c1a5276f94dd257ef0ae3f71b9befd670a058`; 53 artifacts |
| Frozen manifest | SHA-256 `2cfce69a76edea3b950394bd570d07a6cc3a1736481d1603ce4efd21344ee53c` |
| Frozen S0 | SHA-256 `6557ea5d549fbc2bac280be4f46d948948dbb70673c0c1f53ff21c24c4fbde42` |
| Atomic targets | 18 |
| Baseline scoring subset | 24 hunks; 14 positive exact triples |
| All scoring population | 30 hunks; 19 positive exact triples |

Runtime S0 and reviewer-confirmed frozen S0 are different files with distinct
hashes. The scorer reads the latter reference after the completed inference;
it is not copied into model inputs. The baseline scoring subset excludes the
inherited `INTERIM_2024` annotation category; that does not mechanically decide
the runtime target-version interpretation.

The frozen reference is in `data/references/frozen_reference/`. Its existing
confirmation files are declarations, not independent identity authentication.
The inspected reference and case have been used during development. Neither
their folder names nor their integrity checks make them held out.

Canonical copies of the unchanged inference inputs are under
`data/inputs/kep1287/`. Exact input copies also remain within individual run
snapshots because their original receipts identify those bytes and paths.
Available workbooks under `data/excel/` are review resources; they do not replace
the frozen reference or become model inputs. Earlier candidates and audit
documents are identified separately under `data/reference_candidates/`.
The workbooks in `data/excel/source_pilot_workbooks/` are supplied resources for
separate pilot cases; they are not KEP 1287 Gold or new scored KEP 1287 runs.

## Pending Primary Effects Windows Fix evidence

The toolkit identity is
`e9c479cb8386f9afe0b86c94b3648c365d3f5ebb5daaf6f1c13520ec36972cb1`.
Saved Linux checks report 97 passing tests, 6 passing subtests and one native
Windows skip. The user supplied a Windows console result with 98 passing tests,
6 passing subtests and 54.19 seconds. Its forecast reported:

| Field | Value |
|---|---:|
| Mock fresh primary requests | 12 |
| Independent critic requests | 0 |
| Estimated cumulative input | 269,494 |
| Estimated input ceiling | 400,000 |
| Provider-request cap including format retries | 24 |
| Planned events / hunk reviews | 6 / 30 |
| Selected artifacts / all history artifacts | 36 / 53 |
| Selected baseline source lines | 147 |
| Hosted accuracy available | false |

The estimator is a request-envelope estimate, not provider billing. All-negative
local fixtures forecast capacity; they do not generate measured accuracy.
The planned row coverage is complete, but the forecast explicitly does not
claim all 53 history artifacts received semantic review.

The experiment adds pinned public baseline context, selects primary effects
and removes the independent semantic critic. Fixed S0/history/reference and
the numeric scorer remain unchanged. Its changed inputs, projection and compute
make the comparison descriptive. No new hosted run, run ID or F1 is fabricated
to fill the pending entry.

## How to read the other logs

- `data/results/validation/historical/` contains original test, source forecast,
  mock/replay and release records. Their dates and stated boundaries matter.
- `experiments/*/validation/` records each isolated toolkit's technical checks.
  Synthetic proof compatibility is not provider judgment or measured F1.
- New export checks belong in a separate export-validation record. Keep these
  separate from historical run receipts and experimental scores.
- `docs/audits/` records source inventory, stale metadata, exclusion and
  claim-boundary findings. It is analysis, not a new runtime log.

The uploaded original workspace was v4.1 after an earlier patch, despite some
v4.0 release labels. Its historical code is under
`archive/original_v41_workspace/`, with research/documentation/output resources
also organized under `data/resources/original_workspace/`. Readable documentation
and test fixtures have English copies where required. Historical code-release
ZIPs in this export are also English adaptations; they are not original ZIP byte
snapshots. `docs/ARCHIVE_LANGUAGE_ADAPTATIONS.json` records original/adapted
archive hashes and changed members. Production runtime code, inference inputs,
Gold data, diagnostic ZIPs and measured results keep their original bytes. Its
historical `SHA256SUMS.txt` predates that patch and must not be used as the
current export integrity certificate. The new export manifest identifies the
current packaged files.

## Preserve and extend the evidence

Keep raw JSON/CSV, receipts, source inputs, diagnostic ZIPs and frozen-reference
ZIPs byte-for-byte. English adaptations of historical code-release packages have
separate identities recorded in `docs/ARCHIVE_LANGUAGE_ADAPTATIONS.json`. Do not
normalize line endings. Original absolute Windows paths remain historical
metadata; portable commands pass export paths explicitly.

When the new hosted result arrives, import a verified diagnostic snapshot into
a new run directory, create a new evidence-index entry and regenerate derived
summaries. Keep old results and references. A new publication snapshot needs a
new manifest/release identity. The original export's manifest should continue
to describe its original snapshot.

## Archived Git control files

Inactive `.gitignore` and `.gitattributes` files under `archive/` are preserved
byte-for-byte as `GITIGNORE.original` and `GITATTRIBUTES.original`. This prevents
old ignore rules from silently excluding archived Azure logs from the GitHub
commit. `ARCHIVED_GIT_CONTROLS.json` records every path mapping and checksum.
Historical code-release ZIPs have adapted English copies and separately recorded
original/adapted identities. Runtime source bytes, raw run files and frozen
references are unchanged.

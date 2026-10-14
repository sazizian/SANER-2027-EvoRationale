# EvoRationale results catalog for the GitHub export

This catalog distinguishes committed hosted development observations, inherited comparison values, and local synthetic checks. It was built without making provider requests. Historical files were read without alteration.

## Observed KEP1287 development scores

All scores below were independently reproduced with the unchanged v4.9 exact-triple scorer and the supplied frozen reference. Every corresponding TP/FP/FN CSV row also reproduced. These are development results from one repeatedly inspected repository case.

| Run | Baseline TP / FP / FN | Baseline P / R / F1 | All TP / FP / FN | All P / R / F1 | Evidence |
|---|---:|---:|---:|---:|---|
| v4.4 | 3 / 11 / 11 | 0.214286 / 0.214286 / 0.214286 | 6 / 15 / 13 | 0.285714 / 0.315789 / 0.300000 | partial provenance |
| v4.5 | 4 / 0 / 10 | 1.000000 / 0.285714 / 0.444444 | 4 / 0 / 15 | 1.000000 / 0.210526 / 0.347826 | all declared bundle members hashed |
| v4.6 | 10 / 5 / 4 | 0.666667 / 0.714286 / 0.689655 | 12 / 7 / 7 | 0.631579 / 0.631579 / 0.631579 | all declared bundle members hashed |
| v4.7 | 2 / 6 / 12 | 0.250000 / 0.142857 / 0.181818 | 5 / 6 / 14 | 0.454545 / 0.263158 / 0.333333 | all declared bundle members hashed |
| v4.8 | 10 / 7 / 4 | 0.588235 / 0.714286 / 0.645161 | 12 / 9 / 7 | 0.571429 / 0.631579 / 0.600000 | all declared bundle members hashed |
| v4.9 | 12 / 10 / 2 | 0.545455 / 0.857143 / 0.666667 | 14 / 11 / 5 | 0.560000 / 0.736842 / 0.636364 | all declared bundle members hashed |
| cached scope recheck | 12 / 10 / 2 | 0.545455 / 0.857143 / 0.666667 | 13 / 11 / 6 | 0.541667 / 0.684211 / 0.604651 | all declared bundle members hashed |

The all population contains 30 hunks and 19 positive exact triples. The baseline annotation subset contains 24 hunks and 14 positive exact triples; it excludes inherited INTERIM_2024 annotations. This annotation subset does not decide a model prediction’s target version. Each available report records 53 eligible history artifacts, 36 selected versions and 30 model-reported reviewed versions. Review-row coverage does not certify semantic correctness.

## Models, budgets and costs

| Run | Profile | Models | Input ceiling | Request ceiling | Recorded requests | Provider input / output tokens |
|---|---|---|---:|---:|---:|---:|
| v4.4 | event-complete | linker=gpt-6.1-sol; judge=gpt-6-luna | 100000 | not separately set | 10 | 59423 / 23640 |
| v4.5 | event-delta | linker=gpt-6.1-sol; judge=gpt-6.1-sol | 100000 | not separately set | 6 | 36491 / 8520 |
| v4.6 | event-evidence | linker=gpt-6.1-sol; judge=gpt-6.1-sol | 100000 | not separately set | 7 | 45800 / 26646 |
| v4.7 | event-grounded | linker=gpt-6.1-sol; judge=gpt-6.1-sol | 100000 | not separately set | 6 | 42755 / 17515 |
| v4.8 | event-evidence-repair | linker=gpt-6.1-sol; judge=gpt-6.1-sol | 100000 | not separately set | 6 | 38759 / 21026 |
| v4.9 | event-pair-reviewed | linker=gpt-6.1-sol; judge=gpt-6.1-sol | 400000 | 36 | 15 | 137676 / 57835 |
| cached scope recheck | cached-primary-scope-recheck | gpt-6.1-sol | 100000 | 6 | 3 | 35281 / 6628 |

v4.9 has 12 classification requests and 3 independent candidate-check requests. The scope recheck makes 3 additional checker requests over cached v4.9 primary outputs; these counts do not include or erase the original primary compute. Token counts are recorded usage, not monetary charges. Profiles, models and accounting changed across versions, so these comparisons are descriptive rather than equal-compute experiments.

## Source identities and raw export members

### v4.4

- Run UUID: `472626dc-dd7c-48c5-8a94-3420bb8c4ef4`
- Uploaded ZIP: `upload/EvoRationale_v44_Diagnostics_20261011-130744-846.zip`
- ZIP SHA-256: `2e1a3c92870eaf4a8583184b2c368bdcde4d9f7f8bc864d0aeafd4ec747ec0e7`
- Metrics: `diagnostics/v44_472626dc/metrics.json`
- Report: `diagnostics/v44_472626dc/report.json`
- Checkpoint: `diagnostics/v44_472626dc/472626dc-dd7c-48c5-8a94-3420bb8c4ef4.json`
- Source directory: `diagnostics/v44_472626dc`
- Missing original provenance files: `DEV_PREP_MANIFEST.json`, `run/manifest.json`, `score/SCORE_RECEIPT.json`, `DIAGNOSTIC_BUNDLE_MANIFEST.json`. Its uploaded flat ZIP has seven members; report/receipt identities match, but provenance completeness differs from later versions.
- Export the exact `original_diagnostic_members` list in the JSON catalog. Do not present nearby development analyses or case fixtures as raw hosted output.

### v4.5

- Run UUID: `e98cc3a9-fe80-4db8-99d9-cc23a64c115f`
- Uploaded ZIP: `upload/EvoRationale_v45_Diagnostics_20261011-140009-585.zip`
- ZIP SHA-256: `dc4f08eff1db1c634766adf73477aa21ac47aafd60e0da20dbc01fa68a86d119`
- Metrics: `diagnostics/v45_e98cc3a9/score/metrics.json`
- Report: `diagnostics/v45_e98cc3a9/run/report.json`
- Checkpoint: `diagnostics/v45_e98cc3a9/checkpoints/e98cc3a9-fe80-4db8-99d9-cc23a64c115f.json`
- Source directory: `diagnostics/v45_e98cc3a9`
- Use `DIAGNOSTIC_BUNDLE_MANIFEST.json` as member authority; every declared member hash passes.
- Export the exact `original_diagnostic_members` list in the JSON catalog. Do not present nearby development analyses or case fixtures as raw hosted output.

### v4.6

- Run UUID: `188132b4-7975-4ae9-8df4-0cbbc1cad9ad`
- Uploaded ZIP: `upload/EvoRationale_v46_Diagnostics_20261011-155343-966.zip`
- ZIP SHA-256: `19e9c83a51460a94b7f843657aed1fc7f64cde40d320ea52a798ca7020fe4a79`
- Metrics: `diagnostics/v46_188132b4/score/metrics.json`
- Report: `diagnostics/v46_188132b4/run/report.json`
- Checkpoint: `diagnostics/v46_188132b4/checkpoints/188132b4-7975-4ae9-8df4-0cbbc1cad9ad.json`
- Source directory: `diagnostics/v46_188132b4`
- Use `DIAGNOSTIC_BUNDLE_MANIFEST.json` as member authority; every declared member hash passes.
- Export the exact `original_diagnostic_members` list in the JSON catalog. Do not present nearby development analyses or case fixtures as raw hosted output.

### v4.7

- Run UUID: `a50dd556-729c-4840-a509-0fdd9222b81b`
- Uploaded ZIP: `upload/EvoRationale_v47_Diagnostics_20261011-172809-314.zip`
- ZIP SHA-256: `2d1f02171b38b73fbb68aac87d98c25cef6deb453c5e27016ed710899def82a9`
- Metrics: `diagnostics/v47_a50dd556/score/metrics.json`
- Report: `diagnostics/v47_a50dd556/run/report.json`
- Checkpoint: `diagnostics/v47_a50dd556/checkpoints/a50dd556-729c-4840-a509-0fdd9222b81b.json`
- Source directory: `diagnostics/v47_a50dd556`
- Use `DIAGNOSTIC_BUNDLE_MANIFEST.json` as member authority; every declared member hash passes.
- Export the exact `original_diagnostic_members` list in the JSON catalog. Do not present nearby development analyses or case fixtures as raw hosted output.

### v4.8

- Run UUID: `201e1b3a-2e27-431c-ba03-0c9a822af43f`
- Uploaded ZIP: `upload/EvoRationale_v48_Diagnostics_20261011-181147-645.zip`
- ZIP SHA-256: `0190fd86c2f64bbbf8aa0398d8bbfc021512165bcce55d81a0d915eafcdf92b7`
- Metrics: `diagnostics/v48_201e1b3a/score/metrics.json`
- Report: `diagnostics/v48_201e1b3a/run/report.json`
- Checkpoint: `diagnostics/v48_201e1b3a/checkpoints/201e1b3a-2e27-431c-ba03-0c9a822af43f.json`
- Source directory: `diagnostics/v48_201e1b3a`
- Use `DIAGNOSTIC_BUNDLE_MANIFEST.json` as member authority; every declared member hash passes.
- Export the exact `original_diagnostic_members` list in the JSON catalog. Do not present nearby development analyses or case fixtures as raw hosted output.

### v4.9

- Run UUID: `8096127b-4cbd-4e77-a9c4-a9c2c5dc0c03`
- Uploaded ZIP: `upload/EvoRationale_v49_Diagnostics_20261011-194323-093.zip`
- ZIP SHA-256: `4c5a4a2ae98bac1cc1fe1df735008fe0a49ccfd648430274aa1edf7942f1003a`
- Metrics: `diagnostics/v49_8096127b/score/metrics.json`
- Report: `diagnostics/v49_8096127b/run/report.json`
- Checkpoint: `diagnostics/v49_8096127b/checkpoints/8096127b-4cbd-4e77-a9c4-a9c2c5dc0c03.json`
- Source directory: `diagnostics/v49_8096127b`
- Use `DIAGNOSTIC_BUNDLE_MANIFEST.json` as member authority; every declared member hash passes.
- Export the exact `original_diagnostic_members` list in the JSON catalog. Do not present nearby development analyses or case fixtures as raw hosted output.

### cached scope recheck

- Run UUID: `fbb1c892-88e4-4e49-80cb-0a433eaaa87a`
- Uploaded ZIP: `upload/EvoRationale_ScopeRecheck_Diagnostics_20261011-205639-194.zip`
- ZIP SHA-256: `e2d03e807cc7f67a6daceb2a7215cd5157450b916b22dc7acf6eb5fce2b6b934`
- Metrics: `diagnostics/scope_fbb1c892/score/metrics.json`
- Report: `diagnostics/scope_fbb1c892/run/report.json`
- Checkpoint: `diagnostics/scope_fbb1c892/checkpoints/fbb1c892-88e4-4e49-80cb-0a433eaaa87a.json`
- Source directory: `diagnostics/scope_fbb1c892`
- Use `DIAGNOSTIC_BUNDLE_MANIFEST.json` as member authority; every declared member hash passes.
- Export the exact `original_diagnostic_members` list in the JSON catalog. Do not present nearby development analyses or case fixtures as raw hosted output.

## Historical values with missing raw runs

| Legacy comparator | Baseline F1 | All F1 | Status |
|---|---:|---:|---|
| offline v4.1 | 0.062500 | 0.142857 | quoted by later score files; original raw metrics/checkpoints unavailable |
| API v4.1 | 0.000000 | 0.000000 | quoted by later score files; original raw metrics/checkpoints unavailable |
| API v4.3 | 0.133333 | 0.095238 | quoted by later score files; original raw metrics/checkpoints unavailable |

v4.3’s UUID `a4ed806a-93fc-4869-bd09-a8e3445a86c5` and hashes survive in later preparation manifests, but its raw run has not been supplied. Do not infer TP/FP/FN or new measurements from these F1-only comparison fields. The Azure examples in the user’s project are a different `GitHub-PR-1803` episode and are not missing KEP1287 v4.1 runs.

## Current PrimaryEffects WindowsFix: no hosted accuracy yet

- Toolkit SHA-256: `e9c479cb8386f9afe0b86c94b3648c365d3f5ebb5daaf6f1c13520ec36972cb1`.
- Saved Linux local log: `primary_effect_windows_kit/validation/local_preflight.log`: 97 passed, 1 native-Windows test skipped, 6 subtests passed in 2.67 seconds.
- User’s pasted Windows console: 98 passed, 6 subtests passed in 54.19 seconds. This is a user-console observation, not a hashed uploaded hosted diagnostic bundle.
- Dry-run forecast: 12 mock classification requests, zero independent critic requests, input estimate 269494 within ceiling 400000; request cap 24; 147 pinned baseline-context lines.
- All-negative mock responses and synthetic flags in 28 source-proof compatibility fixtures do not measure precision, recall or F1.
- A completed PrimaryEffects API run/report/receipt/score has not been received. Record new F1 as null/pending. No result above 80% is established.

## Local validation records

The version `V43_TEST_REPORT.md` through `V49_TEST_REPORT.md` documents under `er_v49_build/EvoRationale_v49_DEV_EN` record local construction checks. The saved log `development_review/v49_local_tests_and_preparation.log` has 782 passed in 104.95 seconds using explicit synthetic ancestry fixtures. Scope local validation has 37 tests and 13 subtests; the primary experiment had 75 tests and 6 subtests before the Windows checkpoint repair. These records do not establish real-model accuracy. User console timings are separate observations and should not overwrite the saved Linux logs.

## Publication limits

- Single curated KEP1287 repository case repeatedly inspected for development; no held-out performance established.
- Different semantic profiles, inference context, judge models and request budgets prevent equal-compute causal claims.
- Opaque model IDs are reused; immutable provider snapshots are unverified.
- The strongest observed all-scope result is v4.9 0.636364; strongest baseline-subset result is v4.6 0.689655. No result above 0.80 is established.
- All-hosted report outcomes are recommendations with unresolved human review, without outcome Gold; link F1 is not architecture-outcome accuracy.
- Provider token fields are recorded usage, not monetary billing. Scope experiment adds 3 checker requests on reused v4.9 primary predictions; primary compute was not free.
- Reported historical test reports are local construction validation and synthetic workflow checks, not hosted accuracy.
- GitHub export can preserve provenance but does not independently authenticate reviewer declarations or external service responses.

Freeze and scorer identities:

- Frozen reference root: `diagnostics/frozen_reference_211411/KEP1287_Reviewer_Confirmed_Freeze`.
- Frozen manifest SHA-256: `2cfce69a76edea3b950394bd570d07a6cc3a1736481d1603ce4efd21344ee53c`.
- Unchanged scorer source: `er_v49_build/EvoRationale_v49_DEV_EN/development_tools/_score_core.py`.
- Unchanged scorer SHA-256: `18553a3a195a490102348e199233ef4ae752efaf8b80e351e52ff354c6d88895`.
- Reference labels and notes belong only in post-run scoring, never in runtime model inputs.

For self-contained post-run rescoring, export all seven original files under the frozen reference root. The four reference CSVs and frozen S0 hashes match FREEZE_MANIFEST.json; all seven file paths and SHA-256 identities are listed under required_frozen_reference_export_members in the JSON catalog. Keep this directory separate from inference inputs.

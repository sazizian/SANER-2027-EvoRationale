# Data and English-language resource audit

Read-only audit of the assembled export and supplied research resources. No API calls were made. Existing workbooks were inspected without editing or recalculation. This inventory was generated during the parent task; the final package verification must rescan the completed export.

## Original Excel resources

Seven standalone workbook paths and fourteen workbook ZIP members resolve to eight unique original payloads. All inspected worksheet names and text cells contain no Arabic or Persian characters. There are no Excel formulas or external workbook links in the eight unique workbooks. Embedded GitHub source URLs are already present in the KEP1287 workbooks.

| Original workbook | Source role | SHA-256 |
| --- | --- | --- |
| KEP1287_A_B_Consensus_Reconciliation_B01-Result.xlsx | KEP1287_REVIEW_OR_CANDIDATE_RESOURCE_SCORING_ONLY | `a459bd54ddcd8caa9cfd0c92686b5199a88dff85efb8b4fbd38595016be154dc` |
| KEP1287_Consensus_PI_Attested_20261010.xlsx | KEP1287_REVIEW_OR_CANDIDATE_RESOURCE_SCORING_ONLY | `93190e194efc35e651efc1a1ff4fc2c107d9a117c1dff8eda56ab7ba367d188e` |
| KEP1287_Reviewer_Consensus_Workbook.xlsx | KEP1287_REVIEW_OR_CANDIDATE_RESOURCE_SCORING_ONLY | `745fd742379d1c7fba5017455f03cfef3de31d19a7a11c3e56e1e0120f474bed` |
| KEP1287_Candidate_Reference_Review.xlsx | KEP1287_REVIEW_OR_CANDIDATE_RESOURCE_SCORING_ONLY | `5eec09955c4d438b3797cb39070fe04b5a20ca6bcd1d55a293d21c88e28b8944` |
| Reviewer_A_Consensus_Workbook_AS_RECEIVED.xlsx | KEP1287_REVIEW_OR_CANDIDATE_RESOURCE_SCORING_ONLY | `b0043dcba0b9e1b48098cf5be584af4a4bacdc3b255c9ca756c7ea4f4ec35c28` |
| Reviewer_B_Consensus_Workbook_AS_RECEIVED.xlsx | KEP1287_REVIEW_OR_CANDIDATE_RESOURCE_SCORING_ONLY | `a52a053dac3dbaa935c47050be6d320a5a09f28c119f70c758a3b3f2c8168d62` |
| reviewer_1_source_pilot_as_received.xlsx | OTHER_UPLOADED_SOURCE_PILOT_RESOURCE_NOT_KEP1287_GOLD | `9f866f06e3bb6431eb6ba990cd8c9772b2c641fe523b89d95c7caeeb199023eb` |
| reviewer_2_source_pilot_as_received.xlsx | OTHER_UPLOADED_SOURCE_PILOT_RESOURCE_NOT_KEP1287_GOLD | `6df89efbea38ff98ea0d20ec083cb1a1d4ba0a3e8993ac32c2800858e1bdd930` |

The two `reviewer_*_source_pilot_as_received.xlsx` files came from the user-supplied RationalePath resource ZIP already inside the project archive. They are supplemental uploaded resources, not KEP1287 frozen Gold labels or EvoRationale accuracy measurements.

Exact byte-preserving extracted copies and an alias manifest are in `tmp/data_resource_extracted_excel/`.

## English-only source findings

| File | Classification | Lines containing Arabic or Persian characters |
| --- | --- | --- |
| `archive/code/v42/V41_README_FA.md` | historical_document | 1, 3, 5, 7, 9, 11, 12, 13, 14, 15, 16, 18, 20, 29, 35, 37, 39, 49, 51, 53, 55, 68, 79, 81, 83, 84, 85, 86, 87 |
| `archive/code/v42/docs/V4_CHANGELOG_FA.md` | historical_document | 1, 3, 4, 5, 6, 7, 8, 10 |
| `archive/code/v43/V41_README_FA.md` | historical_document | 1, 3, 5, 7, 9, 11, 12, 13, 14, 15, 16, 18, 20, 29, 35, 37, 39, 49, 51, 53, 55, 68, 79, 81, 83, 84, 85, 86, 87 |
| `archive/code/v43/docs/V4_CHANGELOG_FA.md` | historical_document | 1, 3, 4, 5, 6, 7, 8, 10 |
| `archive/code/v44/V41_README_FA.md` | historical_document | 1, 3, 5, 7, 9, 11, 12, 13, 14, 15, 16, 18, 20, 29, 35, 37, 39, 49, 51, 53, 55, 68, 79, 81, 83, 84, 85, 86, 87 |
| `archive/code/v44/docs/V4_CHANGELOG_FA.md` | historical_document | 1, 3, 4, 5, 6, 7, 8, 10 |
| `archive/code/v44/tests/test_review_launchers.py` | test_path_fixture | 37, 42, 47 |
| `archive/code/v45/V41_README_FA.md` | historical_document | 1, 3, 5, 7, 9, 11, 12, 13, 14, 15, 16, 18, 20, 29, 35, 37, 39, 49, 51, 53, 55, 68, 79, 81, 83, 84, 85, 86, 87 |
| `archive/code/v45/docs/V4_CHANGELOG_FA.md` | historical_document | 1, 3, 4, 5, 6, 7, 8, 10 |
| `archive/code/v45/tests/test_review_launchers.py` | test_path_fixture | 37, 42, 47 |
| `archive/code/v45/tests/test_v45_development_tools.py` | test_path_fixture | 222, 227, 230 |
| `archive/code/v46/V41_README_FA.md` | historical_document | 1, 3, 5, 7, 9, 11, 12, 13, 14, 15, 16, 18, 20, 29, 35, 37, 39, 49, 51, 53, 55, 68, 79, 81, 83, 84, 85, 86, 87 |
| `archive/code/v46/docs/V4_CHANGELOG_FA.md` | historical_document | 1, 3, 4, 5, 6, 7, 8, 10 |
| `archive/code/v46/tests/test_review_launchers.py` | test_path_fixture | 37, 42, 47 |
| `archive/code/v46/tests/test_v45_development_tools.py` | test_path_fixture | 222, 227, 230 |
| `archive/code/v47/V41_README_FA.md` | historical_document | 1, 3, 5, 7, 9, 11, 12, 13, 14, 15, 16, 18, 20, 29, 35, 37, 39, 49, 51, 53, 55, 68, 79, 81, 83, 84, 85, 86, 87 |
| `archive/code/v47/docs/V4_CHANGELOG_FA.md` | historical_document | 1, 3, 4, 5, 6, 7, 8, 10 |
| `archive/code/v47/tests/test_review_launchers.py` | test_path_fixture | 37, 42, 47 |
| `archive/code/v47/tests/test_v45_development_tools.py` | test_path_fixture | 222, 227, 230 |
| `archive/code/v48/V41_README_FA.md` | historical_document | 1, 3, 5, 7, 9, 11, 12, 13, 14, 15, 16, 18, 20, 29, 35, 37, 39, 49, 51, 53, 55, 68, 79, 81, 83, 84, 85, 86, 87 |
| `archive/code/v48/docs/V4_CHANGELOG_FA.md` | historical_document | 1, 3, 4, 5, 6, 7, 8, 10 |
| `archive/code/v48/tests/test_review_launchers.py` | test_path_fixture | 37, 42, 47 |
| `archive/code/v48/tests/test_v45_development_tools.py` | test_path_fixture | 222, 227, 230 |
| `archive/code/v49/V41_README_FA.md` | historical_document | 1, 3, 5, 7, 9, 11, 12, 13, 14, 15, 16, 18, 20, 29, 35, 37, 39, 49, 51, 53, 55, 68, 79, 81, 83, 84, 85, 86, 87 |
| `archive/code/v49/docs/V4_CHANGELOG_FA.md` | historical_document | 1, 3, 4, 5, 6, 7, 8, 10 |
| `archive/code/v49/tests/test_review_launchers.py` | test_path_fixture | 37, 42, 47 |
| `archive/code/v49/tests/test_v45_development_tools.py` | test_path_fixture | 222, 227, 230 |
| `archive/original_v41_workspace/README_FA.md` | historical_document | 1, 3, 5, 7, 11, 13, 15, 23, 25, 27, 37, 45, 47, 49, 55, 63, 69, 71, 73 |
| `archive/original_v41_workspace/V41_README_FA.md` | historical_document | 1, 3, 5, 7, 9, 11, 12, 13, 14, 15, 16, 18, 20, 29, 35, 37, 39, 49, 51, 53, 55, 68, 79, 81, 83, 84, 85, 86, 87 |
| `archive/original_v41_workspace/_v41_update/V41_README_FA.md` | historical_document | 1, 3, 5, 7, 9, 11, 12, 13, 14, 15, 16, 18, 20, 29, 35, 37, 39, 49, 51, 53, 55, 68, 79, 81, 83, 84, 85, 86, 87 |
| `archive/original_v41_workspace/backup_before_v41_20261010T190857Z/V41_README_FA.md` | historical_document | 1, 3, 5, 7, 9, 11, 12, 13, 14, 15, 16, 18, 20, 29, 35, 37, 39, 49, 51, 53, 55, 68, 79, 81, 83, 84, 85, 86, 87 |
| `archive/original_v41_workspace/backup_before_v41_20261010T191139Z/V41_README_FA.md` | historical_document | 1, 3, 5, 7, 9, 11, 12, 13, 14, 15, 16, 18, 20, 29, 35, 37, 39, 49, 51, 53, 55, 68, 79, 81, 83, 84, 85, 86, 87 |
| `archive/original_v41_workspace/docs/V4_CHANGELOG_FA.md` | historical_document | 1, 3, 4, 5, 6, 7, 8, 10 |
| `archive/release_time_docs/v49/V41_README_FA.md` | historical_document | 1, 3, 5, 7, 9, 11, 12, 13, 14, 15, 16, 18, 20, 29, 35, 37, 39, 49, 51, 53, 55, 68, 79, 81, 83, 84, 85, 86, 87 |
| `docs/V4_CHANGELOG_FA.md` | document_or_source | 1, 3, 4, 5, 6, 7, 8, 10 |
| `tests/test_review_launchers.py` | test_path_fixture | 37, 42, 47 |
| `tests/test_v45_development_tools.py` | test_path_fixture | 222, 227, 230 |

Only two active Python files contain such literal characters. They are test paths, not code comments, prompts, or interface messages. Replacing the literal characters with `\uXXXX` escapes preserves the same runtime path strings and the meaning of these tests. The copied historical versions contain the same fixtures. Translating archived documentation changes hashes and should be recorded explicitly.

## GitHub and raw-source data

The Azure AVNM raw capture consists of nine files: an enriched history JSONL, draft and approved S0 JSON files, a capture manifest, and five GitHub API page JSON files. Its exact source hashes are in this audit JSON. Azure PR1803 data is a separate pilot; these records do not establish the v41 KEP1287 reference comparison.

The KEP1287 capture contains a historical baseline README, commit-screening and selected-event CSVs, capture manifest, and selected-commit JSON. Four selected commit JSON files were extracted on Linux with a literal backslash in the filename; normalize their destination paths carefully while preserving file contents and recording source aliases.

The historical/candidate review package contains the full candidate reference spreadsheet, atomic S0 and relations CSVs, benchmark input snapshot, patches, source manifests and AS_RECEIVED reviewer workbooks. Candidate and reviewer resources must remain separate from agent input material.

## PDF text checks

- `docs/EvoRationale_SANER2027_V4_reference.pdf`: PDF text extraction returned 0; Arabic/Persian characters found: False.
- `figures/development_pilot_metrics.pdf`: PDF text extraction returned 0; Arabic/Persian characters found: False.

## Recommendations

- Keep all eight unique original workbooks byte-identical in data/excel, with all supplied alias paths in a manifest. No merged or recalculated workbook is required.
- Translate human-facing Persian guides to English. Preserve archived source identity separately by keeping original payload hashes and recording transformations rather than silently treating translated source as the historical raw source.
- Replace literal Persian characters in Python Unicode-path fixtures with ASCII Unicode escapes, preserving the exact runtime string and Unicode path coverage.
- Centralize historical KEP1287 captured baseline, selected GitHub commit JSON, screening CSVs and source manifests under data/github/kep1287, preserving raw source bytes.
- Centralize Azure AVNM draft/approved decisions, enriched history, capture manifest and five raw GitHub API JSON pages under data/github/azure_avnm. Keep this pilot separate from KEP1287 scorer denominators.
- Keep frozen labels and reviewer/candidate workbooks in a clearly marked scoring/reference resource area. Inference inputs must remain the unlabeled runtime S0 and 53-artifact history.
- Latest primary-effects hosted metrics are still pending. No 80 or 85 percent F1 result is available in the supplied records.

## Missing measured evidence

The latest primary-effects hosted report/metrics have not yet been supplied. Original raw KEP1287 v41 API/offline and v43 hosted run outputs remain unavailable; later comparison fields are inherited values and should not be represented as independently rescored raw baselines. Existing Azure outputs do not fill that gap.

## Supplemental uploaded source-pilot ZIP

The supplied project includes a nine-member `RationalePath_ABC_Evidence_Checkpoint.zip`. Five English noncode text resources were extracted exactly into `tmp/data_source_pilot_resources/`: two evidence summary JSON files, the original manifest JSON, a rejection taxonomy CSV, and a LaTeX result insertion fragment. Two original workbooks are already preserved in the eight-workbook extraction. The other-study builder code and Persian guide remain within the original uploaded archive.

Every eight original-manifest member hashes matches its supplied bytes. These original summaries describe a different ABC study and source-only human pilot. They are supplied resource claims, not newly verified EvoRationale F1 results. Full raw execution logs, parent runner sources, raw upstream source packets and comparative ABC human judgments are absent from that ZIP. Do not use these as KEP1287 exact-triple Gold or combine their counts with the current pilot.

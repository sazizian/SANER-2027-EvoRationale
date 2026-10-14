# GitHub source audit — uploaded EvoRationale project

Audit date: 2026-10-12 UTC. Source: `upload/EvoRationale_PaperAligned_v4.zip`.
This is a read-only inventory and claim audit. No source file or historical run was modified, and no GitHub publication was performed.

## Confirmed source identities

- Uploaded archive SHA-256: `92590eb21cfdaab33deefb06941ee9c3f9dd60d213311064b9858aa00c3851e5`.
- The active uploaded `evorationale` tree is **v4.1**, despite the root folder saying v4, README saying 4.0.0rc1, and `__init__.__version__` still saying 2.0.0-rc1. Its pyproject declares 4.1.0rc1.
- The unchanged scorer's `code_tree_hash` gives the uploaded active tree exactly `83655ad7b7a65fc298073384975394f38fbf32b44f91cf443a73993a6b4fd27c`, matching the pinned v4.1 development source.
- The embedded v4.9 release archive is byte-identical to the previously tested delivered v4.9 archive. Its Python core hash is `a0e1b1c0156e48d6a4bdae27a02fdfd9e0bedfbdd05bac79c2db812468937b22`.
- Embedded releases v4.2–v4.9 match their expected core source hashes; full inventory is in `github_nested_source_inventory.json`.
- `research/EvoRationale_PaperAligned_v4_FULL_TESTED.zip` is actually a **byte-identical duplicate of v4.2 Development Pilot**, containing `EvoRationale_v42_DEV_EN`. Do not advertise it as a separate v4 release. Preserve the original filename only as historical provenance and index this alias explicitly.

## Files to exclude from active source

The uploaded ZIP contains 7,283 files. Its `.venv` alone contains 7,035 files and 231,916,461 uncompressed bytes. After excluding installed environments, caches, bytecode and egg-info, 177 original project files remain, totaling 10,791,027 uncompressed bytes; this count includes genuine historical ZIPs and results.

Exclude `.venv`, `__pycache__`, `.pytest_cache`, generated egg-info and Git internals. They are machine-specific installation state. Keep patch backup directories and `_v41_update` as historical archive entries, outside the active package; do not delete them from the user's working folder. Keep genuine source, tests, input captures, raw reports, checkpoints, scoring records and historical released ZIPs.

`research/RationalePath_ABC_Evidence_Checkpoint.zip` belongs to another project. Put it in an explicitly identified historical/unrelated area or list it as an excluded unrelated attachment; do not present it as EvoRationale experiment evidence.

## Credentials and archive integrity

The recursive pattern scan traversed 39 ZIP/Office containers and 1,807 non-environment project text files. All scanned archive CRC checks passed, and no unsafe path was found. Ten credential-shaped hits are the same synthetic GitHub-token test literal in `test_redaction_removes_credentials_and_urls`, repeated in the root and embedded releases. No non-test credential-shaped candidate was found. No matched token bytes are stored in this audit.

This is a bounded pattern scan, not a guarantee that every possible secret has been recognized. Installed `.venv` files were deliberately excluded from the scan and export. The supplied `.env.example` has empty key fields; no populated `.env` is included among project files.

## Concrete metadata problems

1. Root `.gitignore` does **not** ignore `.venv`. The GitHub export needs a proper ignore list for environments, caches and generated working outputs, without ignoring committed result snapshots.
2. Root `SHA256SUMS.txt` predates the applied v4.1 patch. 62 recorded files match, but five do not: `evorationale/agent.py`, `evorationale/linking.py`, `evorationale/verification.py`, `pyproject.toml` and `tests/test_atomic_memory_v3.py`. Preserve this list as historical metadata, and generate a new export manifest rather than describing the old file as a current integrity certificate.
3. Root `LICENSE` is a truncated MIT text, ending at the short warranty sentence and omitting the usual liability wording. A new top-level license for author-owned new material can contain a complete MIT text; retain historical files byte-for-byte with their provenance.
4. Version labels differ across README, pyproject and package constant. A new export index should distinguish the v4.1 historical root, v4.9 pinned source and the separate Primary Effects Windows Fix experiment. Do not modify pinned core files merely to make the labels uniform.
5. Root README refers to `docs/TEST_REPORT.md`, which is absent; the actual available files include `docs/V4_TEST_REPORT.md`, `docs/V41_TEST_REPORT.md` and `docs/TEST_REPORT_v2_reference.md`. Correct the new top-level documentation rather than altering old release documentation.

## Paper claims versus measured evidence

The archived manuscript `docs/EvoRationale_SANER2027_V4_reference.pdf` and `docs/Paper_LaTeX_as_provided.tex` assert a proprietary 1,500-episode study, including 1,200 held-out episodes from 40 repositories, seven baselines, drift macro-F1 0.82, outcome macro-F1 0.79, evidence F1 0.84, link F1 0.78, human-adjudicated UCR, confidence intervals and significance tests.

The project does **not** include the original private per-episode/per-run observations, all independent labels, genuine baseline adapters, complete immutable snapshots or original industrial prototype needed to support/reproduce these claims. Root README, `docs/PAPER_TRACEABILITY.md`, `docs/REMAINING_VALIDATION.md` and `evorationale/experiments.py` explicitly acknowledge this. `ExperimentalRegistry.run` raises `UnavailableStudyImplementation` for unregistered authentic baseline adapters; the named baseline list is not evidence of executed baselines.

The actual documented evidence in this workspace is a **curated public development pilot**. Its exact-triple hunk-link scores are not the manuscript's held-out outcome/drift macro-F1, independent operational UCR or repository-level significance results. Unit-test counts establish technical checks, not semantic F1. The most recent user-confirmed Windows run passed 98 tests and 6 subtests; its forecast was local/all-negative, with `hosted_accuracy_available=false`. No new Primary Effects hosted F1 was available when this audit was written.

Keep the original paper clearly marked **archived manuscript / claims not reproduced by this package**. Write new paper results from the authenticated pilot logs and independent future evaluation, or provide the missing original study evidence. Do not replace the manuscript's tables with made-up values or relabel this inspected/tuned pilot as held-out.

The frozen reviewer labels must remain separate from model input. PI attestation and reviewer confirmation files are recorded declarations; package integrity does not authenticate human identity or establish independent annotation quality. Existing audit recommendations and development tuning do not overwrite the reference freeze.

## Third-party attribution

Captured Kubernetes KEP-1287 README/diff text comes from `kubernetes/enhancements`, with pinned source URLs and hashes. The default-branch upstream license page inspected during this audit identifies **Apache-2.0**: `https://github.com/kubernetes/enhancements/blob/master/LICENSE`. The archived baseline commit's license copy was not independently fetched successfully during this audit; retain pinned content provenance and record this distinction.

Captured Azure AVNM data/raw diffs come from `Azure/Enterprise-Scale`: `https://github.com/Azure/Enterprise-Scale`. The supplied project does not include a dedicated upstream Azure license/copyright notice. Fetching the guessed upstream `LICENSE` path did not establish its license; do **not** assume it is MIT because the Python project declares MIT, or substitute a neighboring Azure repository's license.

Add `THIRD_PARTY_NOTICES.md` with source repository, exact source commits/URLs where recorded, captured-file hashes, preserved copyright/license notices, and the scope of copied or adapted excerpts. The author's top-level MIT notice does not relicense upstream captures, quoted GitHub discussions, manuscript figures or other independently owned material. Preserve those source attributions and identify unverified rights metadata transparently.

## Recommended root layout and Git handling

Use a clean documentation root with an explicit source map:

- `code/v49/EvoRationale_v49_DEV_EN/`: unmodified pinned v4.9 tree, including development helpers, tests and examples.
- `experiments/primary_effects_windows/`: current separate experimental toolkit; no measured hosted accuracy claim until the new completed run arrives.
- `history/source_v41/`: unchanged uploaded active v4.1 source, examples, scripts and original documentation.
- `history/releases/`: exact historical release ZIPs, their hashes and a version/alias index.
- `results/raw/`: immutable supplied reports, manifests, receipts, checkpoints and exact scorer outputs; no invented new logs.
- `results/summary/`: regenerated readable development comparison and scope explanations, with hashes pointing to immutable raw records.
- `data/runtime/` and `data/reference/`: distinct unlabeled runtime inputs versus frozen scoring labels and annotation records.
- `docs/`: reproducibility, measured-evidence boundaries, historical paper index and GitHub upload instructions.
- `provenance/`: imported archive identities, fresh file manifest, exclusions and source audit.

All core Python files inspected in v4.1 and v4.9 have LF bytes already. Use explicit Git rules to avoid Windows `autocrlf` rewriting hash-pinned records. The safest immutable paths use `-text`; newly authored code/docs can use `text eol=lf`. For example, protect `code/**`, `history/**`, `results/raw/**` and `data/**` from automatic conversion, set new root `.py/.md/.ps1/.json` files to LF, and treat `.zip/.pdf/.xlsx` as binary. Keep historical CSV/JSON line endings and raw ZIP bytes exactly as supplied. Verify pinned source hashes after a fresh Git checkout.

Historical launchers often default to the user's `LOCALAPPDATA` source directories and require the completed comparison chain. Being present in the export does not make every historical launcher portable without those inputs. Provide new top-level offline integrity/re-score helpers with explicit paths; do not silently rewrite historical scripts or report receipts.

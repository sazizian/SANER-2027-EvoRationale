# Current development release: EvoRationale v4.6

Use [README_V46_DEVELOPMENT.md](README_V46_DEVELOPMENT.md) for this package.
The opt-in event-evidence profile separates current documentary support from architectural change.
See V45_DIAGNOSTIC_REVIEW.md for the actual run diagnosis and V46_TEST_REPORT.md for validation.
Previous version documents and checksum manifests below are historical records.

---

> For this v4.5 development package, start with `README_V45_DEVELOPMENT.md`.

This v4.5 development archive adds the opt-in `event-delta` profile, with independent target/relation classification and source-owned before/after evidence. See [README_V45_DEVELOPMENT.md](README_V45_DEVELOPMENT.md) for its Windows workflow and [V44_DIAGNOSTIC_REVIEW.md](V44_DIAGNOSTIC_REVIEW.md) for the supplied run diagnosis. Reports and instructions named for earlier versions describe those historical versions.

> The rest of this file is inherited project documentation.

# v4.1 research update

See `V41_README_EN.md` and `docs/V41_TEST_REPORT.md` for the GitHub diff capture extension, required human approval, and stronger rationale-sufficiency guard. This package is not historical-replay-certified.

# EvoRationale — paper-aligned reference implementation (4.0.0rc1)

This is a **version-4 reference refactor** derived from the tested v2 + API-fix + Atomic-Memory-v3 packages,
based on the architecture and algorithm in the uploaded SANER 2027 V4 manuscript.
It is a **functional, tested reference implementation**, **not** a verified
reproduction of the paper's private 1,500-episode industrial study.

## Important scientific boundaries

- **Offline mode is conservative and extractive**, NOT a general semantic
  architecture-reasoning model. It uses explicit text cues and produces
  *heuristic, uncalibrated* recommendations. It is useful for test-driving the
  orchestration and verifying failure handling, not for validating effectiveness.
- **API mode has adaptive LLM query planning, evidence linking, and outcome
  planning**, with a separate model-assisted semantic evidence check. That
  check is a model assessment, not a mathematical proof of relevance/entailment.
- Only **source statements with verbatim quotes** can become verified material
  report claims; arbitrary natural-language material assertions are rejected.
- The original study's source data, frozen private configurations, seven actual
  baseline executions, statistical run logs, and proprietary Java/Spring/Spoon
  implementation were **not supplied**. They cannot be reconstructed by
  inferring numbers from the manuscript. The external fork adaptations in the
  manuscript are intentionally **not simulated or labeled as reproduced**.
- **Live model, BGE-M3, MongoDB, Elasticsearch, Kafka, Jira and Alloy service
  integrations were NOT exercised against real servers during this refactor**.
  Offline and mocked-contract tests are documented in `docs/TEST_REPORT.md`.
- No report changes architectural authority; human review is mandatory.

## Run immediately (Python 3.11+)

```bash
python -m pip install -e .
python -m pytest -q                 # optional: install pytest if unavailable
python -m evorationale demo --output outputs/redis
cat outputs/redis/report.json
```

The Redis example has a human-approved decision, predecision noise that is
excluded, then three explicitly worded postdecision documents. The offline
reference should recommend `REOPEN`, with status `AWAITING_HUMAN_REVIEW` and
`verification.status = PASS`. Its PASS means *extractive statements and
machine-enforced provenance checks passed*, **not** that the architecture
recommendation is experimentally validated or correct in a real organization.

## Run on an approved repository snapshot

```bash
python -m evorationale validate \
  --decision examples/redis/decision_state.json \
  --history examples/redis/history.jsonl

python -m evorationale run \
  --decision examples/redis/decision_state.json \
  --history examples/redis/history.jsonl \
  --output outputs/my-run \
  --mode offline
```

Expected input objects:

- `decision_state.json`: accepted `S0`, including `repository`,
  `human_approved: true`, `accepted_at`, `cutoff_at`, documented decision
  elements (IDs/text/source), and explicit `central_element_ids`.
- `history.jsonl`: one **exact artifact version** per line including
  `artifact_id`, `repository`, `source_type`, `timestamp`, `source_location`,
  `title`, `content`. Prefer explicit `version_id`, `first_auditable_at`,
  and a verified `content_sha256` from an immutable capture manifest.
- `timestamp` is event/version metadata. **Eligibility uses the first
  independently auditable availability timestamp**, which must be strictly
  after `accepted_at` and no later than `cutoff_at`. Current edited GitHub
  bodies cannot be backdated to `created_at`.

Each run writes `report.json`, `trace.json`, `manifest.json`, **`data_audit.json`**, and a full
working-memory checkpoint. The input is not modified.

## Import GitHub data

If you upload an already captured GitHub REST API export:

```bash
python -m evorationale import-github-export \
  --repo OWNER/REPO --json github_export.json \
  --captured-at 2026-10-10T00:00:00Z \
  --output history.jsonl
```

For a **fresh** GitHub snapshot with an authorized token:

```bash
export GITHUB_TOKEN="<your token>"    # Never place tokens in ZIPs
python -m evorationale ingest-github --repo OWNER/REPO --output history.jsonl
```

`ingest-github` captures current issue/PR/comment/commit/release representations
but does **not** reconstruct historical edits. For a 2025 replay, provide
properly versioned historical archives instead. Benchmarks/incidents/tests
must be imported as authenticated artifacts when absent from GitHub API.

## Advanced model-assisted run (requires authorization and live services)

Never send confidential GitHub/Jira content to a hosted API without permission.
This tool requires an additional explicit flag before making such requests.

```bash
export OPENAI_API_KEY="..."
export OPENAI_MODEL="<a model your account can access>"
export OPENAI_JUDGE_MODEL="<an independent verifier model>"
python -m evorationale run --decision s0.json --history history.jsonl \
  --output outputs/model-run --mode api --allow-repository-text-to-api
```

This enables LLM-generated query reformulation, evidence links, and action
proposals, while keeping deterministic repository/time/identity controls.
Model output is constrained through strict JSON schemas and independently
validated before memory is updated. It is not valid to equate model semantic
judgment with ground truth. API calls are opt-in and will incur charges.
The corpus and prompts must be checked for sensitive material; redaction is
best effort and **cannot guarantee removal of all confidential information**.

For optional production components, install appropriate extras:

```bash
pip install -e '.[openai,storage,embeddings,api,research,test]'
# Add --backend elasticsearch --embedding-revision <PINNED_BGE_M3_REVISION>
# Add --memory mongo
# Add --alloy-jar /path/to/org.alloytools.alloy.dist.jar
```

Alloy is **not** a generic claim validator. Supply an operator-reviewed
`formal_constraints[]` model/command for every applicable constraint. SAT/UNSAT
output is treated as bounded evidence only. If the solver returns an
unrecognized record, the result is `UNKNOWN`, never `PASS` just because Java
exited with code 0.

## Human approval and governance

`evorationale.human_review.record_human_review(...)` records explicit reviewer
actions `ACCEPT`, `REVISE`, `REJECT`, `REQUEST_EVIDENCE`. It does not write to
the authoritative S0. A separate human-controlled workflow must approve and
publish an updated S0 before the next run.

## Paper mapping and limitations

See `docs/PAPER_TRACEABILITY.md`, `docs/V4_TEST_REPORT.md`, and
`docs/REMAINING_VALIDATION.md` for what is implemented, tested, and not
independently verifiable at this stage.

**Never copy the old `paper_results/` values into a new results report.** The
original uploaded V3 structured result files disagreed with the V4 manuscript;
this clean project intentionally excludes those inconsistent aggregates. No
synthetic results are presented as industrial evidence.

The original supplied V4 LaTeX source is copied to
`docs/Paper_LaTeX_as_provided.tex` for reference; the required bibliography file
was not among the source attachments, so its TeX build is not certified.

For one-command **offline** verification after extracting this ZIP, install
`pytest` and run `python scripts/verify_release.py`. It compiles the Python
sources, runs the tests, and checks the Redis outcome and human-review status.

## What is new in version 4

- Passage-level evidence retrieval within each artifact: an atomic decision element
  can be linked from an *exact short quote*, without an artificial `top 2`
  decision-element cap per artifact.
- Offline evidence requires directly matching technical identifiers, subject,
  and a locally asserted relation. A generic portal PR is no longer treated
  as evidence for AVNM. File-modification metadata is not treated as proof
  that a particular parameter was introduced.
- The optional independent semantic judge is preceded by deterministic
  specificity checks and a 650-character quote limit; a model cannot waive
  those constraints simply by returning `supported=true`.
- `data_audit.json` separates a structurally valid captured snapshot from a
  historically auditable/complete study benchmark. A current edited body does
  **not** become historical evidence solely because a PR was created earlier.
- Supplied real GitHub pilot fixture is located in
  `examples/azure/pilot_snapshot/`. It is NOT held-out gold study data.

**Known unresolved work:** evidence-based decision quality remains unproven;
real OpenAI API requests and production GitHub, ES/Mongo/Alloy integrations
have not been re-tested with v4. Original confidential experiments, human
adjudicated ground truth, full historical GitHub event/version capture and
all baseline/ablation implementations remain unavailable. See
`docs/REMAINING_VALIDATION.md`.

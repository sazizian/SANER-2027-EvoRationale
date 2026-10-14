# EvoRationale

**A Stateful Agent for Evidence-Grounded Architectural Decision Revalidation**

EvoRationale is a research framework for examining whether an accepted software architecture decision remains justified as a repository evolves. It connects later evidence to the assumptions, constraints, and rationale of a fixed initial decision state, maintains investigation context, and produces recommendations with supporting evidence for human review.

This repository provides the Python implementation, runnable examples, public development resources, experiment workflows, and supporting documentation. It accompanies the EvoRationale research project prepared for SANER 2027.

## Overview

Architectural decisions can remain implemented after their original justification changes. EvoRationale supports the investigation of these changes through:

- **Decision-centered analysis:** begin with an explicit, accepted initial decision state.
- **Temporal evidence retrieval:** investigate versioned repository artifacts in relation to that state.
- **Evidence-to-rationale linking:** associate source evidence with particular elements of the decision.
- **Persistent investigation memory:** retain checkpoints and context across the investigation.
- **Verification and bounded execution:** check evidence support and operate within configured investigation budgets.
- **Human review:** preserve unresolved questions and expose the basis for each recommendation.

The public resources in this repository support development, inspection, and experimentation. Evaluation protocols, run provenance, and the relationship between the public artifact and the paper are documented in the [evidence guide](docs/EVIDENCE_GUIDE.md) and [paper evidence guide](docs/PAPER_EVIDENCE_GUIDE.md).

## Quick Start

### Requirements

- **Python 3.11 or newer**
- **Git**, if cloning the repository
- **pip** and the Python **venv** module
- Internet access to download the repository and install packages

The bundled offline example requires no model-provider API key, database service, or Alloy installation. Hosted-model execution and optional integrations are configured separately.

### 1. Obtain the Code

```bash
git -c core.autocrlf=false clone https://github.com/sazizian/SANER-2027-EvoRationale.git
cd SANER-2027-EvoRationale
git config --local core.autocrlf false
```

Alternatively, use **Code → Download ZIP** on GitHub and extract the archive.

In Cursor, select **File → Open Folder** and open the repository root: the folder containing `README.md`, `pyproject.toml`, and `evorationale/`. Run the following commands from that folder.

### 2. Create an Environment and Install

**Windows PowerShell**

```powershell
py -3 -m venv .venv
.\.venv\Scripts\python.exe --version
.\.venv\Scripts\python.exe -m pip install -e .
```

Confirm that the displayed Python version is at least 3.11. Calling the environment's Python executable directly avoids the need to activate it through `Activate.ps1`.

**Linux or macOS**

```bash
python3 -m venv .venv
.venv/bin/python --version
.venv/bin/python -m pip install -e .
```

### 3. Run the Offline Example

The bundled Redis example demonstrates the investigation workflow using deterministic local components.

**Windows PowerShell**

```powershell
.\.venv\Scripts\python.exe -m evorationale demo --output outputs/redis-demo
```

**Linux or macOS**

```bash
.venv/bin/python -m evorationale demo --output outputs/redis-demo
```

This example is intended for understanding the software and inspecting its outputs. Hosted-model experiments use the separate workflows described below.

Use a new output directory for each run. The CLI refuses to overwrite an output directory that already contains experiment files.

### 4. Inspect the Outputs

The example writes its files to `outputs/redis-demo/`.

| Output | Purpose |
|---|---|
| `report.json` | Recommendation, supporting rationale, verification information, and unresolved questions |
| `trace.json` | Investigation trace for inspecting the execution |
| `manifest.json` | Run identity, execution settings, and hashes of key inputs and outputs |
| `data_audit.json` | Input provenance checks and historical-availability information |
| `checkpoints/` | Persisted investigation state |

The report is intended to support a human decision. Review the cited evidence and unresolved questions before acting on a recommendation.

## Run with Your Own Inputs

The main CLI accepts two input files:

| Input | Format | Purpose |
|---|---|---|
| Initial decision state | JSON | Accepted decision and its rationale elements |
| Repository history | JSON Lines | Versioned evidence artifacts to investigate |

Use the [Redis example](examples/redis/) to understand the input structure. The [schemas](schemas/) directory documents the decision state, artifact version, and report formats.

The commands below use Windows PowerShell. On Linux or macOS, replace `.\.venv\Scripts\python.exe` with `.venv/bin/python`.

### Validate the Inputs

```powershell
.\.venv\Scripts\python.exe -m evorationale validate --decision examples/redis/decision_state.json --history examples/redis/history.jsonl
```

Replace the example paths with your own input files. Validation checks the required structure; it does not establish that the decision or its evidence is substantively correct.

### Run an Offline Investigation

```powershell
.\.venv\Scripts\python.exe -m evorationale run --decision examples/redis/decision_state.json --history examples/redis/history.jsonl --output outputs/custom-offline --mode offline --backend local --memory file --memory-dir outputs/custom-offline/checkpoints
```

Keep scoring references and post-run annotations separate from runtime inputs.

### Explore the CLI

```powershell
.\.venv\Scripts\python.exe -m evorationale --help
.\.venv\Scripts\python.exe -m evorationale run --help
```

Additional commands support drafting an initial state, recording human approval, capturing GitHub snapshots, and importing existing GitHub exports. A current GitHub snapshot does not automatically reconstruct a repository's historical contents.

## Hosted Models and Optional Integrations

For model-assisted investigation, install the provider integration:

```powershell
.\.venv\Scripts\python.exe -m pip install -e ".[openai]"
```

Configure these environment variables in the process that launches EvoRationale:

| Variable | Purpose |
|---|---|
| `OPENAI_API_KEY` | Provider authentication |
| `OPENAI_MODEL` | Investigation model identifier |
| `OPENAI_JUDGE_MODEL` | Separately configured verification model identifier |

The [.env.example](.env.example) file lists configuration names. The CLI reads process environment variables; merely creating a `.env` file does not load them automatically. Keep populated credentials out of version control.

Hosted execution uses `--mode api` and requires the explicit `--allow-repository-text-to-api` flag. It sends selected repository text to the configured provider and may incur charges. Select model identifiers available to your account, review the input scope, and configure execution budgets before starting.

For example, after configuring the environment variables:

```powershell
.\.venv\Scripts\python.exe -m evorationale run --decision examples/redis/decision_state.json --history examples/redis/history.jsonl --output outputs/custom-api --mode api --allow-repository-text-to-api --backend local --memory file --memory-dir outputs/custom-api/checkpoints
```

This runs the default investigation profile on the example inputs. Use the dedicated experiment guides for the public development configurations and their preparation, caching, and scoring requirements.

Other optional dependency groups are declared in [pyproject.toml](pyproject.toml):

| Extra | Purpose |
|---|---|
| `test` | Test dependencies |
| `embeddings` | Sentence-transformer embeddings |
| `storage` | MongoDB and Elasticsearch integrations |
| `api` | Web API dependencies |
| `research` | Numerical and statistical utilities |

Install an extra with `python -m pip install -e ".[extra-name]"`, using the Python executable from your environment. Database backends require their corresponding services. The optional Alloy integration requires a separately supplied Alloy JAR and its Java runtime; see `run --help` for the `--alloy-jar` option.

## Repository Structure

| Folder | Purpose |
|---|---|
| [evorationale/](evorationale/) | Main Python package: investigation agents, retrieval, linking, memory, verification, and CLI |
| [examples/](examples/) | Runnable examples and sample decision/history inputs |
| [schemas/](schemas/) | JSON schemas for decision states, artifact versions, and reports |
| [tests/](tests/) | Tests for the active implementation |
| [experiments/](experiments/) | Isolated experiment workflows and their documentation |
| [data/](data/) | Public inputs, captured sources, research resources, reference material, and recorded runs |
| [development_tools/](development_tools/) | Version-specific preparation, execution, scoring, and diagnostic utilities |
| [development_review/](development_review/) | Development analyses and post-run review material |
| [tools/](tools/) | Export verification, resource checks, local-check orchestration, and plotting utilities |
| [scripts/](scripts/) | Source-ingestion, enrichment, state-preparation, and release utilities |
| [docs/](docs/) | Setup guides, evidence documentation, traceability records, and historical material |
| [figures/](figures/) | Generated research figures |
| [archive/](archive/) | Historical workspaces, code, and release packages |
| [.github/](.github/) | GitHub automation workflows |
| [LICENSES/](LICENSES/) | Third-party license material |

Important top-level files include [pyproject.toml](pyproject.toml) for packaging and dependencies, [CITATION.cff](CITATION.cff) for software citation metadata, [ARTIFACT_MANIFEST.json](ARTIFACT_MANIFEST.json) for the frozen export inventory, and [NOTICE.md](NOTICE.md) for attribution.

### Data Organization

Start with [data/README.md](data/README.md). The [resource index](data/RESOURCE_INDEX.csv) provides file-level paths, roles, and checksums.

| Folder | Purpose |
|---|---|
| [data/inputs/](data/inputs/) | Runtime inputs, including the KEP 1287 initial decision state and versioned history |
| [data/github/](data/github/) | Captured GitHub source material, diffs, and metadata |
| [data/excel/](data/excel/) | Supplied workbooks and related research resources |
| [data/examples/](data/examples/) | Additional example data |
| [data/baseline_context/](data/baseline_context/) | Pinned public context used by specific experiments |
| [data/references/](data/references/) | Scoring references, kept separate from inference inputs |
| [data/reference_candidates/](data/reference_candidates/) | Earlier annotation candidates and audit material |
| [data/resources/](data/resources/) | Preserved research, documentation, and workspace resources |
| [data/results/](data/results/) | Recorded run artifacts, evidence indexes, and validation records |
| [data/packages/](data/packages/) | Preserved diagnostic packages |

Workbooks and annotation candidates have different roles from the frozen scoring reference. Consult the resource index before using a file as an input or evaluation reference.

### Experiment Organization

| Experiment | Purpose | Guide |
|---|---|---|
| `experiments/primary_effects_windows_fix/` | Primary-effect investigation with pinned context and Windows checkpoint handling | [Start here](experiments/primary_effects_windows_fix/README_START_HERE_EN.md) |
| `experiments/scope_recheck/` | Scope checking using preserved primary predictions | [Start here](experiments/scope_recheck/README_START_HERE_EN.md) |

The experiment guides describe their input dependencies, local preparation, optional provider calls, and scoring procedures. Some historical examples use paths from the original workspace; the [Windows guide](docs/WINDOWS_GITHUB_GUIDE_EN.md) gives export-relative preparation commands.

## Tests and Export Verification

Install the dependencies used by the documented local checks:

```powershell
.\.venv\Scripts\python.exe -m pip install -e ".[test,openai]"
```

Run the core implementation tests:

```powershell
.\.venv\Scripts\python.exe -m pytest tests -q
```

For the matching, unmodified export snapshot, the repository also provides:

```powershell
.\.venv\Scripts\python.exe tools/verify_bundle.py
.\.venv\Scripts\python.exe tools/run_local_checks.py
```

The bundle verifier checks the frozen file manifest and recorded resources. The local-check runner begins with that verification, then runs scoped tests and experiment forecasts without hosted inference.

**Snapshot compatibility:** `ARTIFACT_MANIFEST.json` describes a particular export. Later edits to manifested files, including this README, can produce an integrity mismatch. Use the corresponding export snapshot for byte verification; ordinary demo execution and the core test command above do not depend on that manifest matching. Preserve historical manifests and recorded run files when preparing a revised release.

## Documentation and Research Use

| Document | Use |
|---|---|
| [English quickstart](docs/QUICKSTART_EN.md) | Original export orientation |
| [Windows guide](docs/WINDOWS_GITHUB_GUIDE_EN.md) | Detailed environment setup, portable experiment preparation, and GitHub publishing |
| [Evidence guide](docs/EVIDENCE_GUIDE.md) | Run identities, provenance, evaluation scope, and supporting records |
| [Paper evidence guide](docs/PAPER_EVIDENCE_GUIDE.md) | Relationship between the available artifact and the paper |
| [Data guide](data/README.md) | Resource organization and input/reference roles |
| [Archive adaptation record](docs/ARCHIVE_LANGUAGE_ADAPTATIONS.json) | Provenance of adapted historical release packages |

Use a fixed commit or tagged release when reporting experiments. Record input identities, execution configuration, model settings where applicable, and the output directory for each run. Store new runs in new locations so the associated evidence remains traceable.

## Citation

If you use EvoRationale in research, cite the associated paper and identify the exact software commit or release used. Software citation metadata is provided in [CITATION.cff](CITATION.cff).


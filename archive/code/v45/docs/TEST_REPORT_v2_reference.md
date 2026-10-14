# EvoRationale v2.0.0rc1 — independent release verification

**Status: PASS for the implemented offline reference paths; live research/production paths NOT VERIFIED.**

## Commands executed (Python 3.11+, 2026-10-10)

```console
$ python -m pytest -q tests
89 passed in 0.73s
$ python -m compileall -q evorationale tests scripts
# Successful exit, no syntax errors
$ python scripts/verify_release.py
89 passed in 0.73s
{
  "status": "AWAITING_HUMAN_REVIEW",
  "outcome": "REOPEN",
  "verification": "PASS"
}
OFFLINE_RELEASE_SMOKE_TEST: PASS
```

The machine-readable pytest results are in `test-results.xml`. Tests are **not** evidence that industrial accuracy/F1/UCR numbers in the SANER manuscript are reproduced.

## Verified by actual offline execution

- Accurate-version document identity; cross-repository, timestamp, tampered-hash and provenance refusal
- Human-approved initial state; no agent approval of updated architecture
- Bounded, stateful retrieval/link/verify/report cycle with checkpoint persistence and unresolved-case behavior
- Negative tests for fabricated or empty material claims, wrong relations, citations and manipulated report content
- Four report outcomes exercised (`KEEP`, `REVALIDATE`, `REVISE`, `REOPEN`)
- Full Okapi BM25 term-frequency ranking, RRF fusion, version-consolidated retrieval
- Both whitespace approximation and fast-tokenizer-offset-based chunking (mock tokenizer)
- GitHub export snapshot dating (no backdating of edited issue/PR text); HMAC webhook validation
- Mocked contracts for OpenAI, Elasticsearch, Alloy, Mongo/File abstractions and a complete multi-call model path
- Repository-mean F1 and basic statistical utilities; correct Pratt zero-difference signed ranks
- End-to-end Redis sample emits a `REOPEN` recommendation and waits for a human

## Not verified and therefore not claimed

- A deployed Java/Spring/Spoon/Jira/Kafka stack or live GitHub capture with production permissions
- A real Elasticsearch cluster, MongoDB instance or BGE-M3 model pinned revision
- Real OpenAI Responses API output with the paper's exact named model, exact token accounting or independent judge quality
- Actual Alloy 6.2 command-line output using meaningful real-world architectural constraints
- Entire authentic seven-baseline and five-ablation experiments and 157,860 held-out runs
- The manuscript's proprietary 50 repositories, 1,500 labeled decisions, adjudicator records, and statistical source observations
- Real-world trust, time saving, architecture decision quality, model calibration or benchmark F1/UCR
- The source LaTeX is provided as uploaded; no `references.bib` was supplied, so a full reproducible LaTeX build is not asserted

## Security and correctness note

Exact-source quote verification demonstrates *provenance and faithful extraction*.
It is not a proof that a quoted statement is true, that a repository is genuine, or that a proposed relation has semantic correctness. The offline classifier is deliberately conservative. API mode adds a separately invoked semantic judge but must be audited with independent human ground truth.

Historical snapshot eligibility assumes authentic, authorized repository capture manifests; user-supplied timestamps alone cannot provide cryptographic evidence of what existed at a past time.

The reference package is not a drop-in substitute for the confidential experimental code claimed by the paper. Keep these scopes distinct in research reporting.

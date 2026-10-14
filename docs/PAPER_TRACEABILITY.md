# Traceability to submitted EvoRationale SANER V4 manuscript

This document distinguishes algorithmic/reference coverage from replicating
private empirical results. Page and section references are to the supplied
V4 PDF (2026-10-10).

| Paper requirement | Code | Executed checks | Status / boundary |
|---|---|---|---|
| II-B: S0 typed goals/requirements/assumptions/evidence/quality/constraints/scope | `model.py`, `state_builder.py` | State validity, missing fields, human approval | Working; auto-state construction unvalidated (paper also excludes it) |
| II-B: (t0,tc] version cutoff, exact repository | `model.py`, `retrieval.py`, `verification.py` | Date/repo attacks, version switching, current GitHub edit | Working, assuming honest captured/audited source snapshots |
| IV-A: single bounded agent | `agent.py`, `budget.py` | Full Redis, exhausted resources, checkpoint tests | Working; controlled outer loop, ≤3 rounds, ≤12 logical queries, ≤24 unique artifact reads |
| IV-B: decision-centered memory | `memory.py` | Persistent JSON store; in-memory checkpoints | Working; Mongo adapter mocked by interface, live service untested |
| IV-C: temporal retrieval | `retrieval.py`, `segmentation.py`, `planning.py` | BM25/RRF, mock ES, long segmentation | Working offline; BGE/ES service integration requires environment |
| IV-C: semantic evidence links and four relations | `linking.py`, `verification.py` | 12+ forged/tampered links, negative relation, fixed quotes | Offline only explicit relations; API mode supports model proposal + independent model assessment; still fallible |
| IV-D: six drift categories and four outcomes | `analysis.py` | Redis REOPEN, under-evidenced REVALIDATE | Rule decisions uncalibrated; learned P4 and historic metrics not reproduced |
| IV-D: output verification and unsupported claims | `verification.py` | False material claim, manipulated citation, zero claims, tampered rationale, illegal outcomes | Exact extractive support; NOT general semantic proof of arbitrary claims |
| IV-D: optional Alloy | `formal.py` | Fake solver results and unknown/failed evidence | Real Alloy 6.2 JAR unavailable here; no dummy constraint models |
| IV: human authority | `human_review.py`, `model.py` | Human approval/review tests | Working; no autonomous state change |
| V-E: capped artifact chunks ≤1024 tokens, 128 overlap | `segmentation.py` | Long-text segmentation and overlap tests | Default offline word approximation; production study must pin BGE tokenizer |
| V-E: 50 BM25/50 dense BGE-M3, RRF 60 | `retrieval.py` | Local RRF, ES mock, BGE adapter interface | Algorithm present; pinned BGE model and real ES not tested |
| V-E: gpt-5.6-terra API configuration | `planning.py`, `linking.py`, `analysis.py`, `verification.py` | Mock model schemas | User supplies accessible model; model and full 64k API budget not verified against live API |
| V-E: GitHub/Jira webhooks and Kafka, Mongo, Spoon/Java | `streaming.py`, `github.py`, `memory.py` | GitHub HMAC and export tests | Partial integration; no Jira adapter, Kafka broker, Java/Spoon parser or production-scale runtime validation |
| V-D: seven baselines, five ablations, private fork fidelity | `experiments.py` | Missing adapters explicitly raise | NOT REPRODUCED: require original forks and frozen configs |
| V-F: evidence/link scores, macro-F1, repo/bootstrap, Holm, Wilcoxon | `evaluation.py` | Deterministic metric/stats tests | Implemented from supplied observations; no access to original study observations |
| VI: 1,200 held-out episodes, 157,860 total executions | Not supplied in package | Not run | NOT VERIFIABLE without source data, logs, annotations and settings |

Design note: three bounded *outer* cycles correspond to the paper's
retrieve/link/verify passes. The `max_queries=12` setting is an upper bound,
not a statement that the current planner will use exactly twelve queries.

The local evaluator's 0 unsupported claims for extractive output is **not**
the independently adjudicated industrial UCR reported in Table V. The latter
needs material-claim annotations against real eligible evidence.

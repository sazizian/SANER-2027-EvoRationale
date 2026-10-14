# EvoRationale v4 test and release assessment

**Release candidate:** 4.0.0rc1  
**Test date:** 2026-10-10  
**Scope:** complete self-contained reference implementation; offline source and mocked API contracts.

## Tests actually run

- Python source compilation: PASS
- `python -m pytest -q tests`: **127 passed**
- `python scripts/verify_release.py`: PASS (compilation, 127 tests, Redis smoke execution)
- Redis demo: `REOPEN`, verification `PASS`, human review `PENDING`.
- Azure public snapshot (22 captured artifact versions) via offline reference agent: `REVALIDATE`, verification `UNRESOLVED`; supported `I1b` from PR #1880. Some other implementation elements remain uncovered.
- Reference provenance data audit: 22/22 records explicitly *not* safe for reconstructing the exact body at arbitrary 2025 cutoffs; current snapshot integrity is separate.
- Unapproved atomic S0 run: rejected with `ValidationError`, as intended.

## New independent adversarial regressions

The 12 initial v4 tests plus integration additions exercise:

1. PR #1880's directly described `AVNM` checkbox must link to atomic element `I1b`, without a `top-2` truncation.
2. An unrelated generic portal PR (#2083) must not be considered direct AVNM evidence.
3. A commit saying only `modified eslzArm.json` must not prove that `deployAVNM` was defined.
4. Quotes must be **exact contiguous substrings of a canonical version** and no longer than 650 characters.
5. Separate markdown bullets cannot be concatenated into a misleading statement.
6. Multiple atomic elements can receive independent valid evidence from one version.
7. Incorrect artifact key, content, quote and version fail closed.
8. Unrelated instruction text embedded in an artifact cannot be used as evidence or model instructions.
9. The hosted semantic judge's mocked response cannot override a failed element-specific relevance check.
10. The model linker's prompt uses relevant source passages rather than only initial PR boilerplate.
11. A simulated forged quote from a model is rejected by the verifier regardless of claimed confidence.
12. Claims of `historical_replay_safe=true` require the appropriate audited record, not the event timestamp of a mutable current PR body.

## What this does NOT establish

These tests do **not** verify the correctness of every possible source interpretation. The offline `ExplicitCueJudge` is a conservative keyword/quote checker and can have both false positives and false negatives. The optional LLM semantic judge is probabilistic and requires **human adjudication** for quantitative claims. Neither the production OpenAI Responses endpoint nor real Elasticsearch, MongoDB, Alloy, Kafka, live GitHub webhooks, private Jira sources, or the proprietary Java/Spring analysis stack were exercised as part of this v4 release. Model-generated queries inside this package run over a frozen local snapshot; the 22-record Azure pilot is not full GitHub-history discovery.

**The private 1,500-episode dataset, original 157,860 executions, baseline forks, and SANER results have not been reproduced.** The manuscript's measured F1, CI, UCR, run time and costs should not be attributed to this reference package.

## Next validation before academic submission

1. Independently audit GitHub event times and immutable code/version availability; reconstruct actual historical states where possible.
2. Independently annotate reference evidence and outcomes without access to EvoRationale predictions.
3. Re-run API mode against authorized live endpoint with permitted models, record tokens/costs and verify semantic judge outputs.
4. Audit a large held-out set of unrelated repositories for false positives/negatives and case-specific drift labels.
5. Obtain and execute paper-relevant baseline forks and all ablations with identical budget and inputs.
6. Reconcile paper tables and statistics against original frozen authorized run records.

# EvoRationale v4.5 validation report

Validated on Linux with Python 3.12 and isolated local test dependencies.
No hosted provider call was made during construction or validation. Native
Windows execution and v4.5 hosted F1 are not established by these checks.

## Executed checks

- **501 tests passed in 17.09 seconds** during the actual
  `start_v45_no_api.py` helper's full pytest invocation. This retains the
  previous 363 tests and adds 138 generic synthetic/integration regressions.
- The actual helper prepared a fresh evaluation using simulated, hashed
  original/v4.3/v4.4 transport fixtures and printed its no-API command.
  Source fixture bytes stayed unchanged; no run, checkpoint, hosted attempt,
  or score was created. Its READY pointer recorded the actual allocated paths.
  Simulated receipts/scores are transport fixtures, not experimental results.
- The ZIP was extracted independently, and its actual start helper passed the same 501 tests, preparation and dry-run with unchanged fixture sources.
- Python compilation passed. The offline Redis CLI demo produced REOPEN with
  structural verification PASS. Hosted semantic accuracy was not measured.
- Core source matches the preparation pin. The prior v4.4/v4.3 trees are
  unchanged. The exact-triple scorer is byte-identical to the delivered parent.

New checks cover independent recovery after empty or failed optional nomination,
exact S0 anchors, source-side proof handles, meaningful local changed evidence,
qualified replacement with surviving preview/legacy paths, explicit retirement,
unchanged premises, source-role/claim-scope consistency, discussion rationale
versus hypothetical behavior, complete atomic responses, malformed/duplicate
JSON, bounded retries/input/output, canonical versions and source redaction,
repeated identical quote occurrences, LF/CRLF/Unicode boundaries, model/profile
dispatch, receipt/checkpoint normalization, duplicate attempt prevention,
source preservation, no-label inputs, exclusive complete diagnostic ZIPs,
and source-only sizing. Controlled replies test these boundaries; they cannot
prove that a real model interprets language correctly.

## Structural replay of the actual uploaded inputs

`V45_SOURCE_PREFLIGHT.json` checks the supplied approved runtime S0 and 53
unlabeled captured artifacts without reading Gold. Original bytes and approval
are unchanged. First-six batch sizes are [14, 6, 5, 1, 2, 2], covering all 30
captured diff versions. Remaining commit records are explicitly outside the
bounded review; complete captured event context is not full repository history.

All 68 passage handles and 677 line handles/roles were checked against exact
canonical versions and physical positions. The 410 safely quotable changed
lines are covered; two of 412 changed lines are policy-screened and keep their
source reviews incomplete. URL/email screening need not mean credentials exist.

The default no-nomination scenario constructs six actual classifier envelopes
with complete schema/instructions and explicit negative fake responses:
**49,053 estimated input tokens**, within
100,000 for this no-retry scenario. The optional hosted-nomination sizing scenario
uses twelve envelopes and **83,996** estimated
input tokens. Classifier request hashes match across modes; nomination affects
audit origin only and is disabled by default to avoid unused provider work.

These figures are UTF-8 envelope estimates, not provider tokenization, billing,
latency or experimental semantic performance. Real positive-link output sizes,
reasoning and retries can differ; successful hosted completion is not guaranteed.

## Actual diagnosis and measurement limits

The supplied v4.4 hosted result is baseline TP3/FP11/FN11, F1=0.214286, and
all-scope TP6/FP15/FN13, F1=0.300000. All 13 false negatives had been reviewed;
nine expected relations and two targets were never proposed, and two exact
proposals were rejected. No technical failure caused those misses. The new
profile directly addresses target/effect interpretation and preserves source
attribution, uncertainty and exact frozen scoring.

**No v4.5 hosted F1 exists at packaging time.** Exact quotation and mechanical
proof checks do not establish semantic truth. Known reference examples informed
development; these checks are not held-out evidence or a guarantee of optimal
performance. A different configured classifier and call/policy
architecture require a descriptive comparison, not an equal-compute claim.

Two interim-state labels concern restrictions absent from fixed original S0;
freshness, operational scope and alternative-discussion annotation ambiguities
also remain documented in `V44_DIAGNOSTIC_REVIEW.md`. No reference row, original
state, historical report or scorer was changed. Empty original-rationale
evidence and unreviewed/citation-limited sources can still correctly produce
REVALIDATE/UNRESOLVED. External storage/API services were not exercised live.

## Integrity and Windows use

Core Python tree SHA-256: `e53412024165759b0dec7c6e45556f6857fca39674faf119acf1290f512f5afd`

Parent v4.4 core: `9c7fc66afd6d315c5f02a7b4d88a10ca91c7ad43360fadba9d01cd3e71f91e3e`

Use `README_V45_DEVELOPMENT.md` for the Windows workflow. Files named for earlier
versions describe their original versions. `MANIFEST_V45_DEV.json` and
`SHA256SUMS_V45.json` describe this package.

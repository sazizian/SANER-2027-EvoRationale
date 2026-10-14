# v4.9 local validation report

Status: TESTED_EXPERIMENTAL_PROFILE_NO_HOSTED_V49_ACCURACY_MEASURED.

The actual `start_v49_no_api.py` helper completed all **782 tests in 104.95 seconds**, preparation, hash checks, and hosted-command dry-run using explicitly synthetic ancestry fixtures. No provider call was made. All historical 712 tests and 70 new tests passed after runtime edits were frozen. A convenience READY pointer to a synthetic run is removed before packaging.

New tests comprise 25 pair/schema/source/checker tests, 15 CLI/pipeline/coverage/request-budget tests, 23 preparation/run/score/bundle workflow tests and 7 source-only audit tests. They cover missing/duplicate pair and candidate IDs, response consistency, current/foreign source proof, preserved same-event context across focused chunks, untrusted data/privacy, withheld primary model explanations, separate confirmation and unchanged source gates, interruption/retry/provider ceilings, malformed coverage metadata, uncertainty reporting, ancestry hashes, incomplete/completed-run handling and score commits. Fake providers test structural behavior, not real model judgments.

An early concurrent development test attempt encountered a source-hash mismatch while the core was being edited; no such mismatch remained in the frozen complete helper run. A scratch integration harness naming error was corrected before the final helper run. Neither affected a shipped runtime result.

Core SHA256: `a0e1b1c0156e48d6a4bdae27a02fdfd9e0bedfbdd05bac79c2db812468937b22`. Runtime version: `4.9.0.dev0`. Changed runtime files: evorationale/cli.py, evorationale/event_agent.py, evorationale/pair_review_verification.py, evorationale/__init__.py, evorationale/delta_verification.py.

The v4.6 evidence-trace implementation, v4.8 narrow routing implementation, relation contract and exact-triple scoring core remain byte-identical. Historical code roots and completed diagnostics were preserved. S0 and all 53 original source artifacts remain pinned; Gold labels are excluded from model inputs.

## Source/compute validation

Source-only audit covers all 30 selected diff artifacts against 18 targets: 540 explicit pair rows in 12 focused primary requests. It checks 677 original line positions and 412 changed positions: 410 safely quotable and two deliberately screened/protected. The captured source text is unchanged. The first six events have [14,6,5,1,2,2] artifacts; all source context remains complete across focus chunks.

Negative fixture primary estimate: 147,826 input tokens. Controlled replay of 23 stored fallible v4.6 effects with mock confirmation: 15 total requests and 181,785 input tokens, inside the 400,000/36 ceilings. It preserves all 19 prior accepted effects, including earlier false positives, and admits the one existing narrow routing repair; three old interpretations remain rejected. No Gold reference was read for this replay and no fresh semantic prediction was made.

A deliberately dense, maximal-proof 64-hypothesis-per-event checker capacity forecast estimates 475,854 checker tokens and 623,680 combined input tokens; that exceeds the 400,000 runtime ceiling. The audit reports this explicitly. It is not a normal usage prediction or a completeness guarantee. Actual request reservation fails before exceeding input/provider caps. Retrying can also consume the remaining budget. First-attempt count bound for this source selection is 12 primary plus at most six checker requests; at most two attempts per phase is 36 reserved provider calls.

All estimates include request schemas/instructions and are UTF-8 budget estimates, not billed token counts. Actual hosted tokens, time, cost, parsing completeness and F1 remain unmeasured.

## Evaluation

All-scope exact-triple F1 >=0.80 is the declared pilot target; >=0.85 is the stretch target. The unchanged reference has 19 positives. TP14/FP2/FN5 yields .80; TP15/FP1/FN4 yields .857143. This is arithmetic, not a forecast. Scope disagreements remain in the original denominator. Report all results, including failures, and separately report baseline scope/resource usage. Matching model IDs are opaque; provider snapshots are unverified. Increased input ceilings and two semantic phases make this an unequal-compute development comparison. Independent held-out validation is required for claims about broader accuracy.

## API schema compatibility

New outbound schemas use basic objects/arrays/types/enums with all fields required and additionalProperties=false. Exact pair/candidate cardinality and 400-character reason bounds are checked locally. New optional maxLength/minItems/maxItems constraints were excluded from outbound schemas to keep the copied opaque-model protocol conservative. Current official schema guidance was checked: https://developers.openai.com/api/docs/guides/structured-outputs . No provider schema acceptance is claimed without a hosted run.

See README_V49_DEVELOPMENT.md for Windows preparation, optional hosted pilot, scoring, bundling, restart handling and existing-result reuse. A test pass does not establish requested F1, semantic correctness, deployed behavior or architecture-outcome accuracy.

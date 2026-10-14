# EvoRationale v4.1 — verification report

Local technical validation (Python 3.13; offline only):

- Full regression suite: **135 passed**.
- Added tests: deterministic PR file selection from manifest; extraction of contiguous code hunks and provenance; refusal to overwrite; inability to treat mere filename changes as evidence; explicit typed boolean parameter and checkbox/condition recognition; retained incomplete initial-rationale warning; behavior with mocked S0 and mocked LLM/reviewer; ability to reach KEEP *only* when central predecision rationale elements exist and are supported by a test fake judge.
- GitHub HTTP network **not used** in these tests; read-only file API response was mocked.
- Actual OpenAI API **not executed** by this version of the test suite.
- Source code of the previous v4 pilot, original 22 snapshots, existing original PR sampling, and examples remain available for comparison.

Research caveat: `PATCH_SYNTAX_SCREEN_REQUIRES_HUMAN_AUDIT` means grounded implementation code changes only. It is not independent entailment of design rationale. S0 with no central predecision rationale must yield `REVALIDATE / UNRESOLVED` even if every code element is matched.

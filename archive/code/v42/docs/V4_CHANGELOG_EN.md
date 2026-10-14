# Changes in v4 compared with v3

This is an English translation of the historical v4 change log. Statements about tests and research limitations describe that release; they do not establish the performance of later versions.

1. **Linker:** Removed the artificial restriction of choosing only two elements per artifact. Uses a short sentence or paragraph quoted exactly from the artifact instead of the full PR text.
2. **Evidence specificity:** Requires direct evidence for technical identifiers and files named in an S0 element. A generic PR with no AVNM content, or a commit that merely records a file change, is insufficient evidence that an AVNM capability exists.
3. **Verifier:** Independently checks whether the short passage is relevant to the target element, in addition to validating identifiers, hashes, repository identity, time range, and exact quotations. In API mode, this check also runs before the judge model.
4. **Negative controls:** Added tests for PRs #1880, #1896, and #2083 and GitHub commits; irrelevant-text injection; fabricated quotations; version tampering; and semantic-judge failures.
5. **Data audit:** Automatically creates `data_audit.json` and records its hash in the manifest. Explicitly warns about incomplete snapshots and the inability to certify a historical replay of edited PR text.
6. **Package:** Combines the v2 base code, API fixes, v3 atomic memory, and GitHub snapshot importer in a new project, without requiring manual file replacement.

**Remaining limitation at the time of this release:** These tests did not validate real architectural decisions or the F1/UCR results claimed in the SANER paper. LLM and network behavior were not rerun with real credentials and services for v4; those tests used mocks.

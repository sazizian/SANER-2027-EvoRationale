# Validation required before claiming production readiness or paper reproduction

## Blockers to making the manuscript's empirical claims reproducible

1. Obtain the **frozen execution code and configurations** actually used for
   the proprietary 40 held-out repositories, not just a reconstructed public
   reference architecture.
2. Obtain an authorized privacy-preserving export of original per-run
   predictions, annotator references, evidence links, judge decisions and
   run-level costs; recalculate every V4 table/CI/p-value using the paper's
   repository-level aggregation. Resolve the old V3/V4 JSON discrepancy.
3. Provide pinned authentic baseline forks for Kantara, LinkAnchor and
   ExpeRepair; complete controlled baseline and ablation runners without
   giving any model gold labels, while keeping model/settings/budgets frozen.
4. Audit S0 source provenance and decision-acceptance timestamps; audit each
   artifact *version* first-auditable time. GitHub snapshots alone cannot
   reconstruct historic edited issue bodies.
5. Evaluate actual LLM semantic-judge precision and false acceptance of
   unsupported architectural claims with independent human adjudication.
6. Test exact model API parameters (configured model, response schema,
   tokenization, retry logic, response usage accounting) with credentials.
7. Test BGE-M3 tokenizer segment boundaries and pinned embeddings against
   Elasticsearch BM25+dense search; test real Mongo persistence.
8. Test actual Alloy 6.2 CLI JSON result format with pre-authored, meaningful
   architectural constraint specifications and adversarial SAT/UNSAT cases.
9. Implement and test the deployment-only Java/Spoon parser, Jira path,
   authenticated live streaming and Kafka idempotency if claiming support.
10. Run security review, sensitive-data authorization, and a human/practitioner
    usefulness study before advertising operational improvement.

## Fails-closed rather than pretending to implement unavailable artifacts

The reference package does not supply invented Kantara/LinkAnchor/ExpeRepair
forks, synthetic industry-scale run logs, or automatically approved decisions.
The paper's measured F1, UCR, CI and cost figures are **not reproduced** here.

Do **not** submit this package as an exact replica of the experimental method
without completing these items or narrowing the relevant manuscript claims.

## v4-specific note

The v4 release improves the public reference evidence linker, but the exact
historical evidence in the paper's original dataset is still inaccessible here.
On the public Azure Snapshot the conservative link validation rejects some
partial facts; `REVALIDATE/UNRESOLVED` is not a bug by itself. The release
includes explicit `data_audit.json` warnings, and tests may not be marketed
as establishing the industrial F1 scores in the manuscript.

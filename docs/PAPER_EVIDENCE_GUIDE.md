# Paper evidence and claim boundaries

This repository supports a documented public development pilot and the supplied
reference implementation. Use actual run records for every result. The pending
Primary Effects Windows Fix run has no hosted accuracy row in this export.

## What each evidence class establishes

| Evidence | Defensible statement | Statement it does not establish |
|---|---|---|
| Tests, mock transports and local forecasts | Tested source/provenance controls, failure handling and planned request coverage | Semantic F1, deployment success or cross-project performance |
| Supplied completed API run, receipt and hashes | Internally consistent preserved run files with recorded predictions/usage | Independent authentication of provider execution or human annotation identity |
| Recomputed exact-triple scores | TP/FP/FN and metrics for the unchanged reference/evaluation population | Architecture-outcome accuracy or a certified historical replay |
| Inspected single-case development comparison | Descriptive differences between these versions on this case | Held-out superiority, equal compute or generalization |
| Historical manuscript | Preserved text of earlier claims | Experimental evidence for those claims |
| Supplied Excel and candidate annotation resources | The available workbook contents and recorded annotation history | Automatically frozen Gold, independently authenticated reviewers or measured F1 |

All available research resources are indexed under `data/RESOURCE_INDEX.json`
and `data/RESOURCE_INDEX.csv`. The [data guide](../data/README.md) separates
fixed inference inputs, GitHub captures, Excel resources, candidate annotations,
the frozen scoring reference, completed results and technical validation.
Identify the exact file and version used in the paper; an Excel workbook and
the confirmed frozen reference may represent different preparation stages.
The historical code-release archives supplied here have English documentation
and test-fixture adaptations. `docs/ARCHIVE_LANGUAGE_ADAPTATIONS.json` records
the original/adapted identities and member changes. Describe these adaptations
when identifying the artifact; do not cite their old package checksum files as
checksums of the new export. Production runtime code, fixed inputs, Gold
reference and measured results retain their original bytes.

## Describe the task exactly

The scored prediction is an exact triple `(hunk, atomic S0 target, relation)`.
The `all` evaluation has 30 hunks and 19 positive triples across 18 fixed atomic
targets. The original `baseline` subset has 24 hunks and 14 positive triples.
It follows annotation provenance, not a rule that determines runtime temporal
scope. Keep all denominators and report both scopes.

For Primary Effects, the model selects one primary relation type per focused
hunk and applicable primary target IDs. Secondary effects remain in the trace
and are excluded from the scored primary projection. The numeric evaluator is
unchanged, but the prediction view has changed. Explain this distinction rather
than presenting it as an equal-task/equal-input ablation by default.

Fixed S0 and 53 history artifacts retain their original bytes. The fresh
experiment also provides source-pinned public baseline excerpts: 147 selected
lines out of 1,181, derived from all target source ranges with margins. These
are additional inference inputs. Baseline text is interpretation context, not
fresh post-S0 proof. The model distinguishes fixed-S0 change from evolution of
a locally evidenced intermediate contract associated with a target family.

Coverage separates 53 history artifacts, 36 selected artifacts and 30 planned
hunk review records. Complete validated rows do not prove complete semantic
review of every history artifact or correct relations.

## Report the comparisons faithfully

For each measured version, report TP/FP/FN, precision, recall and F1 with its run
ID and exact score path. Include model IDs, policy, input context, request count,
estimated/provider-reported token usage and recorded timing when available.
Never reconstruct missing costs or timings by guessing.

v4.4 used a different judge model. Later versions changed semantic policy,
request phases and accounting. v4.9 increased the estimated input ceiling from
100,000 to 400,000 and capped provider requests at 36. Its cached scope recheck
reuses primary predictions and adds three checker requests; those three calls
do not include the original v4.9 primary cost. Primary Effects uses fresh
classification, added baseline context, no independent critic, a 400,000 input
ceiling and a 24-request cap. Matching opaque model IDs do not prove immutable
provider snapshots or equal compute.

All existing pilot results are development results. The reference notes were
read while diagnosing errors. Keep reference labels out of model input and do
not describe this inspected case as independent held-out data.

An evidence-backed provisional Results paragraph is:

> In the inspected single-repository development case, v4.9 produced 14 true
> positives, 11 false positives and 5 false negatives, yielding all-scope
> exact-triple F1 of 0.636364. A cached-primary scope recheck yielded 0.604651.
> These are descriptive comparisons of differing inference procedures and
> resource use. The fresh Primary Effects experiment was pending at the time
> of this repository snapshot.

Update the final sentence only after importing and verifying the completed
new run. The 98 passing Windows tests and forecast estimates are technical
validation, not an 80–85% F1 result.

## Archived manuscript claims require separate evidence

The preserved `EvoRationale_SANER2027_V4_reference.pdf` and supplied LaTeX
assert a private 1,500-episode study, including 1,200 held-out episodes from 40
repositories, seven baselines, drift macro-F1 0.82, outcome macro-F1 0.79,
evidence F1 0.84, link F1 0.78, operational UCR, intervals and significance
tests. The [source audit](audits/github_source_audit.md) found that this package
does not contain the original private observations, complete labels, genuine
executed baseline adapters, immutable snapshots and original industrial
prototype needed to reproduce those claims.

The public hunk-link pilot is a different unit of analysis and cannot fill in
those missing measurements. Registered baseline names are not baseline runs.
Unit-test totals are not empirical sample sizes. The current reference provides
no architecture-outcome Gold, independently measured operational UCR or
certified historical replay.

To retain broader manuscript claims, supply and verify their authentic data,
labels, implementations and execution records. Otherwise revise the paper's
scope, methods and results to match the actual evidence. Do not invent baseline
or statistical results, reinterpret this tuned case as held out, or label model
confidence/provenance `PASS` as proven semantic correctness.

## Cite a stable artifact

After the final implementation and evidence are frozen, cite the GitHub URL
with a fixed commit SHA or release tag and the exported archive identity. A
mutable branch URL alone is insufficient to identify the evaluated version.

Associate every table row with:

1. Run ID and source/toolkit identity.
2. Fixed-S0/history hashes and any extra context identity.
3. Reference manifest/hash and scope definition.
4. Exact report, checkpoint, raw metrics and error-table paths.
5. Genuine request usage, budgets and recorded start/finish fields.

The [evidence guide](EVIDENCE_GUIDE.md) and `data/results/index.json` provide these
links. Preserve raw files and write newly derived tables separately. Human
confirmation and PI-attestation files are recorded declarations; hash integrity
does not authenticate their authors or establish independent annotation quality.

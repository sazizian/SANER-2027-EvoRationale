# Independent review of the v4.6 development change

Reviewer role: read-only review of source and observed v4.5 execution. This review does not generate model relations from the frozen reference and does not estimate a hosted v4.6 F1.

## Observed failure boundary

The supplied v4.5 checkpoint has no verifier feedback and no technical verification failures. All four emitted links were accepted; the other scored cases were semantic abstentions. Thirty source hunks were independently reviewed. The remaining 23 captured versions are commit records, and the six-round limit kept the investigation globally unresolved. Thus loosening a citation parser, increasing retry counts, or changing the scorer would not address the observed missed relations.

## Architecture assessment before implementation completion

Separating current-source support from a novel architectural change is an appropriate general correction: a post-S0 artifact can explicitly document or operationally witness a retained obligation without changing the obligation. This requires a distinct recorded assessment kind. Current documentation must remain a source statement, never evidence that deployed software satisfied the obligation. Partial statements must not resolve an entire central need.

Dependent migration can establish an effect on a chosen representation when an exact target-local old-to-new change is tied to an explicit same-event replacement contract. A shared event alone cannot propagate the replacement to each sibling hunk. Both the local change and the contract must be cited and their substantive dependency assessed. Merely consuming a field, a title, a gate name, and release bookkeeping are insufficient.

## Accuracy risks and required checks

1. **Quantifiers and compound requirements.** An exact S0 substring is not proof of semantic scope. A weak existential fragment of a normative requirement must not erase obligations such as each container/resource or accompanying Events. Aggregate counters and names of states must not automatically become support for a granular explanatory interface. The full target must be shown and qualifications preserved; the semantic assessment remains fallible.
2. **Unseen intermediate targets.** Fixed S0's per-resource restart-policy choice does not encode append-only versus mutable restrictions from later intermediate revisions. Those restrictions cannot be invented to manufacture supersession. Preserve abstention when the fixed claim is not affected, even if the supplied reference contains an intermediate target relation.
3. **Current assertions versus topic overlap.** Permitting substantive unchanged current lines must not revive support from arbitrary background, lists of names, state co-occurrence, a future enhancement, or a related consumer formula. Accepted current support needs a direct qualified source assertion or a concrete witness of the target proposition.
4. **Proposals and adopted behavior.** An alternative can supply an explicit argument for a qualified goal, or a tradeoff against an existing design, but cannot prove an adopted mechanism or actual runtime success. Direct rationale must retain the discussion scope and partial qualification.
5. **Coverage versus correctness.** Artifact/S0 coverage, exact handles, valid JSON, and a passed synthetic regression are structural checks. None demonstrate that a hosted classifier will recover more true links. No claim of improved v4.6 accuracy is justified before the next hosted run.
6. **Support accounting.** The action planner currently derives drift types from adverse relations, so retained support does not itself become drift. The new profile must retain this distinction in metadata and report descriptions. Existing partial-support safeguards must continue to prevent whole-need resolution.

## Final implementation review

Reviewed `evidence_trace_verification.py`, its narrow extension hooks in `delta_verification.py`, CLI/profile dispatch, the source-change helper and the composite coverage correction. The new classifier retains canonical batch validation, same-event construction, exact S0 substring anchoring, source-owned quotations/line roles, sensitive-span screening, final digest/time/body checks and independent classification without nomination gating. The v4.5 default schema and gate behavior remain separate from the new policy.

The new schema records separate support and change reasons for every artifact and source-basis explanations for effects. Support can avoid the novel-target-delta gate while still requiring affirmative exact-current-claim entailment, qualified scope and an added local source proof. Dependent replacements require both old/new local sides, an explicit replacement assessment and current proof from another captured artifact of the same event. Authority and causal attribution remain model-assessed; a current external proposal must not be promoted to an adopted replacement contract merely because it shares the event.

Accepted evidence traces carry `assessment_kind`, `architectural_change` and `deployed_behavior_verified=false`. The event agent continues to leave partial positive central evidence unresolved. The corrected composite diagnostic now separates partial versus fully supported atomic members and cannot claim full composite coverage from explicit partial links.

The mechanical source-change helper conservatively rejects whitespace, code-span delimiters and terminal prose comma/period-only changes. Its revised normalization preserves spaces in quoted literals, operators, numeric endpoints and tuple punctuation. It is a proof screen rather than a relation classifier; indentation or unquoted whitespace distinctions can still cause conservative false abstention.

**Concrete issue found and corrected:** a same-hunk reflow of an existing target assertion plus an unrelated substantive edit initially evaded the exact-old-line check when the response omitted old proof handles. Reproduction: remove `Approved orders are persisted through CentralQueue by the order writer.`, add the same sentence split over two lines, and independently edit `Revision 5` to `Revision 6`. Both complete two-line proofs and a proof citing only the first fragment could initially be accepted. The final implementation uses cached source-owned canonical old/new alignment independently of selected model handles, and requires complete earlier assertion spans to match before classifying an added line as retained/reflowed. Independent reruns of all four variants (interleaved/grouped diff layouts, one/two selected fragments) rejected the false support with `evidence_trace_support_has_no_added_local_proof`.

The test-helper issue is corrected: automatic context population now distinguishes an absent key from an explicitly empty context list, so a negative external-contract fixture remains negative. The review-origin label now names the independent evidence-trace policy. External replacement instructions explicitly require combined adopted authority, and an added regression checks that proposal context cannot establish adopted supersession.

The exact-triple scorer and the shared relation-contract source remain byte-identical to v4.5. No blocker remains in the reviewed schema/provenance/semantic-policy integration. Full-suite and packaged-entrypoint validation are owned by the release integrator; this review does not duplicate or substitute for that validation.

## Performance correction and remaining interpretation limits

A measured quadratic behavior in the intermediate `SequenceMatcher(..., autojunk=False)` implementation was corrected before release. The final helper searches for deduplicated complete earlier normalized assertions in current text, merges retained intervals, caches at most 64 source alignments and caps cumulative matches at 200,000. If the work bound is reached, fresh support conservatively abstains.

Independent final repeated-character benchmark timings were approximately 0.0001, 0.0006, 0.0020 and 0.0028 seconds for lengths 1,000, 3,000, 6,000 and 24,000. An additional valid source/citation case with 100 distinct earlier repeated-character assertions and six safe 500-character added lines reached the matching-work bound; all six fresh-support proofs correctly abstained. The complete bound exercise, including citation catalog construction, took approximately 0.469 seconds. All four reflow bypass variants remained rejected after this replacement.

This mechanical screen is conservative rather than a semantic equivalence proof. Normalization of unquoted whitespace and combining complete retained source assertions can reject unusual substantive edits; bounded-work abstention is also intentionally conservative. Source scope, entity/predicate meaning and qualifications must still be assessed independently.

No structural verification, source benchmark, preserved four-link replay, or synthetic fake response demonstrates hosted v4.6 accuracy. Source entailment, normative scope, adopted authority and dependency remain fallible model assessments. The fixed-S0/intermediate-reference disagreements remain unresolved and must not be removed by changing the scorer, S0 or frozen reference.

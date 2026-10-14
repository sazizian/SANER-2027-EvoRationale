# v4.9 false-positive and checker audit

The pair grid and second phase are structurally complete on executed batches. All eleven reference false positives were independently confirmed under a broad partial-evidence/dependent-replacement policy. No source provenance, handle-ownership, technical parsing or deterministic source-guard defect was demonstrated. Some checker predicate explanations overextend the fixed predicate; others are plausible source-evidence relations omitted by the frozen reference. A structured independently checked scope/proof contract closes an audit blind spot but has not been shown to remove these FPs or raise F1.

Both phases use the same opaque model ID and related instructions. Separate requests do not establish statistical independence or semantic proof. The checker cannot recover omitted primary relations.

Measured development result: TP14 / FP11 / FN5; F1 0.636364. All 11 false positives were checker-confirmed. Of 28 checked primary candidates, 26 were confirmed and 2 rejected; 25 passed the shared final guards.

| Artifact | Target/relation | New versus v4.6 | New versus v4.8 | Main issue |
|---|---|---|---|---|
| 079aa5fb9ab1-F01-H03 | C2a / supports | False | False | Boundary-preserving validation detail versus rationale/non-goal relation |
| 68952e4476e4-F01-H05 | I3 / supports | False | True | Metric/SLO consumption versus progress-model predicate |
| 964260d9c2da-F01-H04 | I1 / supports | True | True | Surviving applied-reporting evidence alongside allocated-reporting supersession |
| 964260d9c2da-F01-H04 | R1 / supports | False | False | Representation replacement as fresh evidence of an unchanged distinction |
| 964260d9c2da-F01-H05 | I1 / supports | True | True | Partial current actual-status assignment amid a replaced allocation dependency |
| 964260d9c2da-F01-H05 | R1 / supports | True | True | Two-way comparison treated as partial evidence of a three-way requirement |
| 964260d9c2da-F01-H06 | R1 / supports | True | False | Changed admission representation corroborating an existing sequence |
| 964260d9c2da-F01-H07 | I1 / supersedes | False | False | Recovery consumer migration boundary |
| 964260d9c2da-F01-H11 | R1 / supports | True | True | Quota consumer rebound as partial desired/actual distinction evidence |
| 964260d9c2da-F01-H13 | I1 / supersedes | True | True | Instrumentation operand migration versus reporting-contract supersession |
| 964260d9c2da-F01-H14 | I1 / supports | True | False | Risk of hiding container allocation as rationale for an unstated reporting scope |

## 079aa5fb9ab1-F01-H03 / C2a / supports

The current proof is the genuinely added CPU-and-memory completeness constraint, not v4.8's renamed class/shape definitions. Both phases treat Guaranteed-class preservation as partial support of the class-change non-goal. The reference treats the hunk as implementation-only. This is a stable evidence-policy boundary from v4.6, not a malformed quote or missing qualifier.

Checker predicate: For running Guaranteed Pods, resize validation must preserve their original QoS class. Requiring equal requests and limits for both CPU and memory directly constrains transitions that would lower that class.

Checker contribution: A0003:L0031 adds the substantive requirement that Guaranteed Pods retain both CPU and memory settings, beyond the earlier requests-equal-limits condition.

Checker authority: The pinned KEP diff supplies a current design constraint, not implementation or deployment validation. Assessment is limited to the captured event.

Audit concern: A constraint that preserves one existing class is accepted as evidence of a normative non-goal. The checker provides the semantic inference but cannot mechanically establish the normative relation.

Repair risk: A prohibition on all validation/enforcement witnesses would remove the true boundary support at the later conditional recreation example. Require an independently stated link from the local operation to the exact boundary; do not use a case-specific exclusion.

## 68952e4476e4-F01-H05 / I3 / supports

The exact addition is an aggregate steady-state terminal-versus-proposed counter equality. It consumes counters defined elsewhere; it does not itself define a progress state meaning, transition, or per-operation state producer. The checker reframes the fixed progress-model claim as an operator obligation to assess aggregate progress. v4.6 accepted this FP; v4.8 rejected its candidate because current_claim_entailed was false; v4.9 sets that flag true and the checker agrees.

Checker predicate: For I3's material subclaim, operators should assess aggregate resize progress by comparing completed, infeasible and canceled counts against proposed counts in steady state. Individual InProgress tracking is not asserted.

Checker contribution: Generic SLO examples are replaced by resize-specific progress accounting. The adopted A0001 contract defines the consumed transition counters, making this a substantive dependent contribution.

Checker authority: The pinned KEP adopts this progress-accounting SLO alongside the same-event metric contract. It establishes design intent, not measured SLO compliance.

Audit concern: The predicate_reason adds the actor/operators and activity/assessment predicate absent from fixed I3. It explicitly preserves only aggregate accounting but still confirms support for modeling progress. This is a concrete semantic overextension, not a source-identity defect.

Repair risk: A blanket ban on instrumentation or partial progress evidence would remove the true newly defined transition-counter contract. A generic checker should independently classify whether the fresh local assertion defines/produces target progress behavior or merely consumes its measurements; the distinction remains model-assessed.

## 964260d9c2da-F01-H04 / I1 / supports

The current fallback sources actual-resource values from the latest admitted allocation snapshot. Both phases limit support to applied reporting, while the same artifact also has accepted I1 supersession for allocated reporting. The candidate anchors all of compound I1 and uses material_subclaim. The reference includes the supersession and omits this surviving-branch support.

Checker predicate: I1's applied-resource reporting clause is supported: PodStatus.Resources shows actual resources, obtained from runtime reports for specified CPU/memory values and otherwise copied from the latest allocation snapshot.

Checker contribution: The changed fallback explicitly connects actual-resource reporting to the latest allocated snapshot instead of the removed AllocatedResources status field.

Checker authority: The pinned API Changes section states the current reporting contract and identifies runtime-reported resource values; this is design authority, not runtime verification.

Audit concern: The checker is asked to confirm a qualified scope without receiving the primary qualification, and returns no independently selectable target clause or source handles. Its prose reconstructs the applied-only limitation, so there is no observed disagreement between phases.

Repair risk: Rejecting all support whenever an adverse relation exists for the same element would suppress legitimate independent support for distinct material clauses. A checked clause contract can identify overlap and avoid labeling the replaced clause supportive without discarding a distinct surviving clause.

## 964260d9c2da-F01-H04 / R1 / supports

The added checkpoint allocation contract distinguishes admitted resources from desired spec values and actual container status. v4.6, v4.8 and v4.9 all emit this R1 support while I1 representation changes. The full three-way distinction is supported as source-design meaning; the frozen reference excludes the additional relation.

Checker predicate: R1 distinguishes PodSpec desired resources, kubelet-admitted requests/limits cached on the node, and actual container resources in PodStatus. Allocation need not be generally published to remain distinct.

Checker contribution: The added checkpoint contract substantively relocates allocation while retaining separate desired and actual representations, supporting the complete three-way distinction.

Checker authority: The pinned current API design establishes field meanings and local allocation handling. Confirmation concerns that design, not implementation correctness.

Audit concern: The checker agrees that a changed allocation representation substantively corroborates the existing requirement. A scope/handle guard cannot decide whether this relation belongs in an exhaustive architectural-rationale reference.

Repair risk: Suppressing secondary targets on a primary replacement conflicts with the evidence-trace instruction to preserve independent exact-element evidence and may erase valid future multi-target effects.

## 964260d9c2da-F01-H05 / I1 / supports

The compatibility warning changes the tracked representation from true allocations/AllocatedResources to actual configurations/Resources. Both phases treat the explicit current actual tracking statement as partial applied-reporting support, while a separate accepted I1 supersession addresses the replaced allocation dependency. The full compound I1 anchor is broader than the checked prose claim.

Checker predicate: For I1's applied-reporting subclaim, actual Pod/container configurations are tracked in PodStatus.ContainerStatuses[i].Resources, distinct from desired PodSpec values. It does not restore unconditional allocation reporting.

Checker contribution: The new wording directly identifies the actual-status representation and explains why reading desired PodSpec resources can mislead applications.

Checker authority: The pinned Risks and Mitigations section explicitly adopts actual configurations tracked in PodStatus.Resources and requires documentation of that meaning.

Audit concern: The checker confirms an applied-only reporting clause under a whole compound anchor; its free-text predicate_reason narrows scope but code does not bind that independently derived scope to the committed affected_subclaim. No actual qualifier disagreement is present.

Repair risk: A rule requiring every target part for support would remove true partial source evidence elsewhere, including mutable desired-field and actor-control evidence. Separating checked clauses is safer than rejecting all partial support.

## 964260d9c2da-F01-H05 / R1 / supports

Current compatibility text explicitly contrasts desired spec values with actual configurations. It does not establish the node-allocated representation. Both phases acknowledge that missing part and still emit qualified support for R1; the reference excludes it. The source is substantive, so this is semantic breadth/exhaustiveness rather than lexical formatting leakage.

Checker predicate: R1's desired-versus-actual subclaim is supported: applications reading desired PodSpec resources may not observe actual configurations tracked in PodStatus.Resources.

Checker contribution: The changed warning explicitly contrasts desired specification values with actual configurations, rather than merely mentioning either representation.

Checker authority: The pinned compatibility rationale is authoritative design discussion about the changed API meanings, not evidence of deployed client behavior.

Audit concern: The hypothesis contains whole R1 plus material_subclaim; the independently covered desired-versus-actual part is represented only in prose. Exact source and target-anchor checks certify identity, not this selected scope.

Repair risk: Rejecting all partial three-way evidence would also reject the true completion equality, whose primary uses material_subclaim despite comparing all three roles. Scope flags are model choices and cannot be treated as reference truth.

## 964260d9c2da-F01-H06 / R1 / supports

Desired requests, allocated updates and later actual-status updates are distinct in both before/current procedures. The local change removes ordinary allocated-status writes and preserves checkpointing. Both phases treat the revised acceptance operation as fresh full R1 evidence. v4.8 also emitted this FP, while v4.6 omitted it.

Checker predicate: For R1, kubelet tests desired Spec requests against node allocation, updates admitted allocation on acceptance, then actuates containers and updates Status.Resources after successful updates.

Checker contribution: The changed acceptance operation updates allocation without the removed status-field dependency, while the surrounding sequence independently identifies desired requests and actual resource reporting.

Checker authority: The pinned kubelet resize design specifies admission, allocation, CRI actuation, and actual-status updates; it does not validate implementation.

Audit concern: The checker describes the operation accurately but counts a new representation binding as fresh evidence for a surviving abstract sequence. Whether that meets the reference rationale criterion is not resolved by the current policy.

Repair risk: A blanket invariance prohibition would reject legitimate newly supplied evidence for existing requirements; a blanket change-in-all-parts requirement would also be invalid.

## 964260d9c2da-F01-H07 / I1 / supersedes

Recovery replaces an explicit read of Status.AllocatedResources with checkpoint restoration and cites the same-event adopted allocation contract. This satisfies the documented dependent-replacement route and preserves the optional alpha status qualification. v4.6/v4.8/v4.9 all accept; the reference calls this exact recovery hunk implementation-only.

Checker predicate: I1's allocated-status mechanism is superseded for kubelet restart recovery: existing Pods are re-admitted from checkpointed allocation before pending resizes. Applied reporting and gated alpha allocation reporting remain.

Checker contribution: Re-admission replaces reading Status.AllocatedResources with restoring the local checkpoint, directly depending on the new allocation contract.

Checker authority: The pinned restart-tolerance design and same-event API contract jointly establish the adopted dependency replacement, not workload-restart behavior.

Audit concern: The checker infers a superseded reporting-backed mechanism from a migrated read consumer. That inference is permitted by policy and structurally resembles accepted migration TPs. No safe deterministic guard separates it using provenance or handles alone.

Repair risk: A consumer migration ban removes five current TPs. A restart/recovery or hunk-specific blacklist would fit this label rather than establish a general rule.

## 964260d9c2da-F01-H11 / R1 / supports

The changed maximum switches its second operand from allocated status to actual status. Before text already compared desired/actual limits; current request comparison supplies a distinct rebound use. Both phases explicitly provide only desired-versus-actual evidence, not node allocation. The reference accepts I1 supersession and excludes R1 support.

Checker predicate: R1's desired-versus-actual distinction is supported: enabled quota accounting uses the maximum of PodSpec requests and PodStatus.Resources to account for pending resizes.

Checker contribution: The new maximum calculation directly compares desired requests against actual status instead of allocated status, substantively corroborating their different meanings.

Checker authority: The pinned quota design and API field meanings establish a normative calculation for the feature-enabled path, not observed controller execution.

Audit concern: The checker equates a representation-consuming calculation with partial corroboration of the distinction predicate. It preserves the limitation in prose but cannot return independently bound covered target parts.

Repair risk: Rejecting every operation consuming distinct representations would remove the true completion comparison. A predicate-role analysis needs to distinguish what the operation establishes and preserve the exact target scope.

## 964260d9c2da-F01-H13 / I1 / supersedes

The local completion equality changes status.Allocated to generic allocated resources and cites the checkpoint contract. Both phases infer that this consumer no longer depends on status-exposed allocation, producing I1 supersession. The same hunk has a correct R1 support link. Earlier v4.6/v4.8 omitted this I1 relation, and the reference includes only R1 support.

Checker predicate: For I1's allocated-status mechanism, resize completion no longer requires allocation represented in status: desired, locally allocated, and actual status values must agree. Gated alpha allocation reporting remains available.

Checker contribution: The completion predicate drops its status.Allocated dependency and instead compares against allocated resources, matching the newly adopted local checkpoint contract.

Checker authority: The pinned instrumentation definition and API allocation contract specify current design semantics; confirmation does not validate emitted metrics.

Audit concern: An equality predicate using allocation no longer names its reporting path, but its role is still measurement. The checker treats the generic operand replacement as evidence of reporting-backed mechanism replacement under the existing dependent-migration policy. Its source proof is exact; the disputed bridge to the reporting obligation is semantic.

Repair risk: A metrics-specific exclusion or broad downstream-consumer ban would be case fitting. A general output/publication versus input/measurement role contract would improve accountability but must retain independently adopted migration evidence where the chosen contract actually changes.

## 964260d9c2da-F01-H14 / I1 / supports

Unlike v4.8's type-consistency sketch, v4.9 selects the explicit risk that outsiders may need container-level allocations. Both phases infer discussion-level support of the allocated-reporting clause and preserve conditional, nonadopted authority. Fixed I1 states PodStatus reporting but does not itself assert a container-level external-consumer visibility requirement. The source risk belongs to conditional Option 3; the reference expects I1 weakens and omits this support.

Checker predicate: For I1's allocated-reporting subclaim, the premise is that outsiders need only Pod-level allocation. The stated risk challenges that premise because outsiders may need container-level allocation exposed through the status API.

Checker contribution: Option 3 explicitly identifies the risk of dropping container-level allocation visibility, directly addressing the allocation-reporting boundary rather than offering generic API consistency benefits.

Checker authority: The pinned Alternatives section supplies conditional discussion-level rationale only. It is not an adopted requirement to retain unconditional container allocation reporting.

Audit concern: The checker adds the inference that outsiders need allocation exposed through the status API. The source con states a risk about missing knowledge, not an unconditional adopted external-status obligation. The primary is explicitly partial and proposed, so current authority guards permit it.

Repair risk: A proposal ban loses two current TPs. A direct-rationale checker should require an explicit premise/conclusion tie to the chosen fixed predicate, distinguish visibility goals from a specific status channel, and record missing assumptions independently.

## Narrow generic review-contract correction

Make the second-phase checked predicate, scope, source contribution and source authority explicit and mechanically attributable. This is a review-contract correction, not a proven precision improvement.

- Pass an explicitly untrusted alleged qualification/covered clause in addition to the full fixed target, or require the checker to rederive it without access to primary rationales.
- Require checker outputs to identify independently covered fixed-target span(s), exact local/context source handles, authority/qualification, contribution role and an exact-scope verdict.
- Validate canonical target anchoring, source ownership, before/current roles, same-event contract authority and agreement of proposed versus checked scope before committing an effect. If the checker establishes a different predicate, preserve it only as unresolved diagnostic evidence.
- Distinguish a reporting/output predicate from consuming existing values, and a progress-model predicate from aggregate operator assessment. Permit explicit adopted dependent replacement as its own route.
- Keep proposal rationale when the source explicitly argues the chosen goal/boundary, but do not infer a new external visibility/status obligation from candidate-specific risk without an explicit tie.

A consistent structured scope contract would make assumptions inspectable; the stored checker explanations already repeat most primary limitations, so these results do not prove that the omission of primary qualification caused the false positives.

| Broad rejected class | FP removed | TP lost |
|---|---:|---:|
| operational_witness | 4 | 2 |
| documented_support | 4 | 2 |
| dependent_replacement | 2 | 5 |
| partial_support | 7 | 5 |
| proposal_or_alternative_support | 1 | 2 |

The runtime, historical reports, fixed S0, frozen labels and exact-triple scorer were not changed. No provider was called. Complete exact source and assessment data are retained in v49_fp_audit.json.

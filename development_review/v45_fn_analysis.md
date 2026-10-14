# v4.5 false-negative diagnosis

## Factual stage attribution

Every one of the 15 scored false negatives was read and independently reviewed against all 18 actual fixed-S0 elements. Every FN artifact received `no_material_relation` and zero candidates. There are no semantic rejections or technical failures in this checkpoint. All 15 are classifier omissions/abstentions, rather than emitted predictions subsequently rejected by code.

The run made six successful classification requests, used 49,053 estimated input tokens (36,491 provider-reported input; 8,520 output), and read all 30 scored diff hunks. Raising reads or the input ceiling does not directly fix these omissions.

## Important regression

v4.4 had six exact true positives. v4.5 retained **none** of them and instead recovered four different I1 supersession triples (H03/H04/H05/H06 in event 964260d9c2da). The old six positives comprise future-policy sketches (C1/C2a/G2), new instrumentation (I3/R1), and new default-behavior documentation (I1). Better overall F1 results from removing 15 false positives while exchanging positive evidence categories; it does not establish uniform semantic improvement.

## Per-reference trace

| Hunk | Fixed target / expected relation | Source-based analyst category | Actual pipeline stage |
|---|---|---|---|
| 04de3dac4669-F01-H01 | I2 / supersedes | interim_policy_absent_from_fixed_S0 | Model abstained; 0 candidates |
| 079aa5fb9ab1-F01-H02 | I2 / supersedes | interim_policy_absent_from_fixed_S0 | Model abstained; 0 candidates |
| 079aa5fb9ab1-F01-H05 | C1 / supports | proposal_evidence_vs_adopted_fulfillment | Model abstained; 0 candidates |
| 079aa5fb9ab1-F01-H05 | C2a / supports | proposal_evidence_vs_adopted_fulfillment | Model abstained; 0 candidates |
| 079aa5fb9ab1-F01-H05 | G2 / supports | proposal_evidence_vs_adopted_fulfillment | Model abstained; 0 candidates |
| 68952e4476e4-F01-H01 | I3 / supports | new_documentary_operationalisation_treated_as_old_invariant | Model abstained; 0 candidates |
| 68952e4476e4-F01-H01 | R1 / supports | new_documentary_operationalisation_treated_as_old_invariant | Model abstained; 0 candidates |
| 68952e4476e4-F01-H01 | R2 / supports | aggregate_observability_vs_per_resource_reference | Model abstained; 0 candidates |
| 68952e4476e4-F01-H04 | I1 / supports | new_documentation_treated_as_old_mechanism | Model abstained; 0 candidates |
| 964260d9c2da-F01-H08 | I1 / supersedes | related_consumer_migration_denied_architectural_contract | Model abstained; 0 candidates |
| 964260d9c2da-F01-H09 | I1 / supersedes | related_consumer_migration_denied_architectural_contract | Model abstained; 0 candidates |
| 964260d9c2da-F01-H11 | I1 / supersedes | related_consumer_migration_denied_architectural_contract | Model abstained; 0 candidates |
| 964260d9c2da-F01-H12 | I1 / supersedes | related_consumer_migration_denied_architectural_contract | Model abstained; 0 candidates |
| 964260d9c2da-F01-H13 | R1 / supports | retained_invariant_reference_freshness_tension | Model abstained; 0 candidates |
| 964260d9c2da-F01-H14 | I1 / weakens | tradeoff_applicability_to_fixed_chosen_mechanism | Model abstained; 0 candidates |

### 1. 04de3dac4669-F01-H01 / I2 / supersedes

**Fixed S0:** Offer per-resource restart-policy choices to control how container resizes are attempted.

**Model reason:** A0001:P0001 changes ResizePolicy from append-only (A0001:L0005–L0006) to mutable, while retaining append as the strictly necessary capability and qualifying full mutability as subject to reevaluation (A0001:L0007–L0009). I2 requires per-resource restart-policy choices but does not prescribe whether those choices are append-only or mutable; this change therefore does not replace or materially alter the fixed target claim. I1 concerns mutable desired resource values and allocated/applied resource reporting, not mutation of ResizePolicy. The retained restart behavior is unchanged context, not fresh evidence. No material effect on any other fixed-S0 element is established by this local change.

**Source-based interpretation:** The diff reverses append-only ResizePolicy to mutable, with only append strictly required and possible future reevaluation. Fixed I2 specifies per-resource restart-policy choices, without mutability/append-only guarantees. The reference temporal_basis is INTERIM_2024. Its supersession requires an intermediate target absent from runtime S0.

**Generalizable action:** Do not invent a mutability clause or auto-label a policy difference supersedes. Maintain abstention against this fixed target; reconcile the evaluation contract separately using authorized reference review.

### 2. 079aa5fb9ab1-F01-H02 / I2 / supersedes

**Fixed S0:** Offer per-resource restart-policy choices to control how container resizes are attempted.

**Model reason:** The change replaces mutable ResizePolicy entries with append-only entries, permitting additions for newly present resources. I2 requires per-resource restart-policy choices, but does not require subsequent modification of existing choices or an entry for every resource. The changed mutability rule therefore does not replace or retire a fixed-S0 claim. The passage also does not change the mutability of desired resource fields asserted by I1.

**Source-based interpretation:** The diff changes mutable-with-entry-for-every-resource to append-only. Neither mutability nor comprehensive-entry constraint occurs in fixed I2. INTERIM_2024 reference supersession therefore evaluates a richer intermediate decision.

**Generalizable action:** As above: keep exact S0 anchoring; represent historical target versions explicitly only if supplied and independently approved.

### 3. 079aa5fb9ab1-F01-H05 / C1 / supports

**Fixed S0:** Explicit non-goal: controlling the full lifecycle of a Pod whose in-place resize failed; this is left to the actors that initiated the resize.

**Model reason:** The additions are future-enhancement design sketches, not adopted controller-resize or explicit-QoS mechanisms. The controller policy discussion does not newly operationalise G2 or I2, and it provides no explicit rationale for their exact qualified obligations. The mixed-QoS replica example documents a prospective workload-resize complication, but its suggested mitigation preserves recreation when changing QoS class; it neither supersedes C2a nor establishes a reduction in the feasibility of the qualified fixed-S0 in-place-resize goal. Removing a future-work item about updating limits does not retire G1's existing CPU/memory request-and-limit goal. No material effect on the remaining fixed elements is established.

**Source-based interpretation:** The new workload-controller sketch assigns InPlace/Recreate policy and has the initiating controller recreate illegal resizes, including a QoS-class change. This is a future proposal consistent with actor-owned lifecycle handling. It is not adopted behavior, but can be qualified documentary evidence illustrating C1 rather than empirical fulfillment.

**Generalizable action:** Permit qualified direct policy/design rationale from a prospective sketch when it explicitly allocates the very responsibility named by the fixed target. Preserve prospective source authority and do not resolve whole-element or deployed-behavior coverage.

### 4. 079aa5fb9ab1-F01-H05 / C2a / supports

**Fixed S0:** Changing a Pod's QoS class without a restart is a non-goal.

**Model reason:** The additions are future-enhancement design sketches, not adopted controller-resize or explicit-QoS mechanisms. The controller policy discussion does not newly operationalise G2 or I2, and it provides no explicit rationale for their exact qualified obligations. The mixed-QoS replica example documents a prospective workload-resize complication, but its suggested mitigation preserves recreation when changing QoS class; it neither supersedes C2a nor establishes a reduction in the feasibility of the qualified fixed-S0 in-place-resize goal. Removing a future-work item about updating limits does not retire G1's existing CPU/memory request-and-limit goal. No material effect on the remaining fixed elements is established.

**Source-based interpretation:** The sketch explicitly states guaranteed/burstable changes cause recreation and changing explicit QoSClass triggers recreation of replicas. This directly exemplifies the fixed QoS no-restart non-goal, under a proposed mechanism. Classifier denies evidence because no controller mechanism is adopted.

**Generalizable action:** Distinguish evidence of a normative policy/constraint from observed success of an implementation. Explicit recurrence of the exact non-goal in new proposal text can be scoped documentary support without asserting implementation or empirical validation.

### 5. 079aa5fb9ab1-F01-H05 / G2 / supports

**Fixed S0:** Allow actors (e.g., users, VPA, StatefulSet, JobController) to decide how to proceed when an in-place resource resize is not possible.

**Model reason:** The additions are future-enhancement design sketches, not adopted controller-resize or explicit-QoS mechanisms. The controller policy discussion does not newly operationalise G2 or I2, and it provides no explicit rationale for their exact qualified obligations. The mixed-QoS replica example documents a prospective workload-resize complication, but its suggested mitigation preserves recreation when changing QoS class; it neither supersedes C2a nor establishes a reduction in the feasibility of the qualified fixed-S0 in-place-resize goal. Removing a future-work item about updating limits does not retire G1's existing CPU/memory request-and-limit goal. No material effect on the remaining fixed elements is established.

**Source-based interpretation:** The new controller ResizePolicy offers InPlace/Recreate choices and controllers recreate illegal in-place resizes. This illustrates actor fallback choice, but is a future design sketch with open questions, not implementation of every actor/condition in G2.

**Generalizable action:** Assess scoped rationale or policy alignment independently of adopted fulfillment. Keep the actor and failed/illegal-resize condition; do not claim every actor has this interface.

### 6. 68952e4476e4-F01-H01 / I3 / supports

**Fixed S0:** Model resize operation progress through states such as proposed, in progress, deferred and infeasible.

**Model reason:** The added instrumentation counts Pod-level resize requests and transitions of an existing resize-status model. It provides aggregate monitoring, not a newly adopted model of resize progress (I3), per-container explanations and Events (R2), or a new distinction between desired, allocated, and applied resources (R1). The completion equality references those existing resource representations without changing or independently validating them. No material change to the other fixed elements is established.

**Source-based interpretation:** New instrumentation explicitly models state labels proposed/infeasible/deferred/completed/canceled, omits InProgress, and counts transitions. The state model already existed, but its new observability mechanism can corroborate a material qualified progress-model subclaim. Classifier treats new telemetry as irrelevant because it is not a newly adopted state model.

**Generalizable action:** Allow a new explicit operational observation/control mechanism to corroborate an existing qualified architectural claim. Do not require reinvention of the underlying state model. Record omitted InProgress, Pod-level granularity, and documentary authority.

### 7. 68952e4476e4-F01-H01 / R1 / supports

**Fixed S0:** Distinguish the desired resources declared in the Pod spec from the resources allocated to the Pod on the node and from the actual resources applied to its containers.

**Model reason:** The added instrumentation counts Pod-level resize requests and transitions of an existing resize-status model. It provides aggregate monitoring, not a newly adopted model of resize progress (I3), per-container explanations and Events (R2), or a new distinction between desired, allocated, and applied resources (R1). The completion equality references those existing resource representations without changing or independently validating them. No material change to the other fixed elements is established.

**Source-based interpretation:** The entirely added completion metric equates spec.Resources, status.Allocated, and status.Resources. The three-way architecture predates it, but this introduces a new completion criterion using all three representations. Classifier rejects it because it does not change or independently validate those representations.

**Generalizable action:** Evaluate new source-owned operational use of exact distinctions as scoped support, while keeping documentary versus empirical evidence separate. An unchanged neighboring equality alone still cannot become a positive link.

### 8. 68952e4476e4-F01-H01 / R2 / supports

**Fixed S0:** Expose, for each resized container resource, why the desired and actual resources differ: whether a proposed resize has not yet been accepted or rejected by the kubelet, has been accepted and is being actuated, is deferred, or has been rejected as infeasible; supplemented by Pod Events at key steps.

**Model reason:** The added instrumentation counts Pod-level resize requests and transitions of an existing resize-status model. It provides aggregate monitoring, not a newly adopted model of resize progress (I3), per-container explanations and Events (R2), or a new distinction between desired, allocated, and applied resources (R1). The completion equality references those existing resource representations without changing or independently validating them. No material change to the other fixed elements is established.

**Source-based interpretation:** Telemetry counts Pod-level state transitions, omits InProgress, and does not expose per-container-resource differences or add Pod Events. Reference supports may intend partial progress observability, but the fixed sentence binds exposure to each resized resource and Events. Aggregate evidence cannot establish that full normative clause.

**Generalizable action:** Keep scope mismatch explicit. Any proposed partial link must anchor a meaningful qualified S0 proposition; do not remove per-resource qualifiers to fit aggregate telemetry. This requires reference-policy adjudication if partial evidence is intended.

### 9. 68952e4476e4-F01-H04 / I1 / supports

**Fixed S0:** Represent desired resources through mutable PodSpec fields and report allocated/applied resources through PodStatus.

**Model reason:** The hunk clarifies default-behavior documentation by naming status fields the kubelet sets, formats the feature-gate name, removes an unused enablement template, and advises against disabling the feature on a running node. The status-field statement describes the existing reporting representation rather than establishing a newly introduced mechanism or validation of I1 or R1; applied-resource reporting already appears in unchanged text. The node-level feature-disable caveat does not change the restart requirements for resizing a running Pod, and Q1 does not guarantee disruption-free feature rollback. No material effect on another fixed element is established.

**Source-based interpretation:** The changed default-behavior answer removes No and newly names AllocatedResources and Resources as Kubelet-populated status fields. This directly documents the reporting mechanism in fixed I1, although it is a clarification of existing behavior rather than an invented API. Classifier rejects on that basis.

**Generalizable action:** Permit introduced explicit documentary corroboration of an existing exact target when before/after text materially adds the assertion. Keep the evidence as a source statement, not observed runtime verification. Apply target-local contribution rather than architectural novelty.

### 10. 964260d9c2da-F01-H08 / I1 / supersedes

**Fixed S0:** Represent desired resources through mutable PodSpec fields and report allocated/applied resources through PodStatus.

**Model reason:** The hunk changes scheduler accounting inputs and how InProgress is treated. It does not itself change which quantities are reported, retire the desired/allocated/actual distinction, or newly introduce the progress-state model. These consumer-side changes do not establish a material effect on an exact fixed-S0 clause.

**Source-based interpretation:** Scheduler accounting switches from AllocatedResources to Resources and revises handling of InProgress; same-event H04 establishes ordinary allocated status becoming gated alpha, with local checkpointing. Classifier views consuming-field changes as unrelated to I1 reporting. The reference uses these migration manifestations as I1 supersession evidence.

**Generalizable action:** Review whether a changed consumer explicitly depends on the replaced representation in the same event, rather than blanket implementation_only. Require local old/new binding and contextual default/gated qualification; never propagate event effects onto an unrelated hunk. Exact hunk-level supersession attribution remains a semantic policy choice.

### 11. 964260d9c2da-F01-H09 / I1 / supersedes

**Fixed S0:** Represent desired resources through mutable PodSpec fields and report allocated/applied resources through PodStatus.

**Model reason:** The accounting rule switches consumers from AllocatedResources to Resources while retaining the same anti-race rationale. Fixed S0 does not prescribe that accounting input. Existing Resources reporting is not newly operationalised, and the unchanged CPU-manager caveat supplies no fresh effect.

**Source-based interpretation:** The all-components accounting rule changes its required input from AllocatedResources to Resources, retaining anti-race rationale. Same-event H04 explains the reporting migration. The classifier says fixed I1 does not prescribe the accounting input.

**Generalizable action:** As above: qualify a local dependency migration as documentary evidence of a same-event mechanism replacement, provided the source binds that dependency to the reporting contract. No field-name-based auto-upgrade.

### 12. 964260d9c2da-F01-H11 / I1 / supersedes

**Fixed S0:** Represent desired resources through mutable PodSpec fields and report allocated/applied resources through PodStatus.

**Model reason:** The changes revise quota accounting, status-update triggers, and a component checklist. Fixed S0 does not choose these accounting formulas or require initialization of AllocatedResources on Create. The hunk does not independently establish a replacement of the reporting contract; the surviving validation and resize-policy entries are invariants, not fresh evidence.

**Source-based interpretation:** Quota accounting/status-update triggers drop allocatedResources; the API checklist deletes initialization of AllocatedResources on Create. This is a local withdrawal of an API population responsibility plus related consumer migration. Classifier calls it an accounting/formula change and says I1 does not specify initialization.

**Generalizable action:** Allow explicit withdrawal of a producer/population responsibility to evidence scoped reporting-mechanism replacement with same-event binding. Deleted checklist proof requires current replacement context and may not imply global disappearance.

### 13. 964260d9c2da-F01-H12 / I1 / supersedes

**Fixed S0:** Represent desired resources through mutable PodSpec fields and report allocated/applied resources through PodStatus.

**Model reason:** The scheduler checklist changes its accounting input to actual Status.Resources. That is a consumer implementation change, not a local change to I1's reporting mechanism or R1's required distinctions. The unchanged Linux/Windows CRI statement is not new support for G3a.

**Source-based interpretation:** Scheduler checklist changes compute resource allocations using AllocatedResources to actual Status.Resources. Same-event H04 establishes reporting change. Classifier treats it as consumer-only and denies I1 effect.

**Generalizable action:** As H08/H09, with strict local dependent-mechanism contribution and phase qualification. Avoid labeling every scheduler change an I1 architecture change.

### 14. 964260d9c2da-F01-H13 / R1 / supports

**Fixed S0:** Distinguish the desired resources declared in the Pod spec from the resources allocated to the Pod on the node and from the actual resources applied to its containers.

**Model reason:** The completed-state expression replaces a status-field reference with the conceptual allocated quantity. Successful completion still equates desired, allocated, and actual resources. This preserves the completion invariant rather than introducing a new state model or independently changing public reporting.

**Source-based interpretation:** Completion equality changes status.Allocated to conceptual allocated resources. Desired/allocated/actual quantities survive identically; only reporting representation changes. Classifier rejects fresh support for a surviving invariant, while reference credits R1 support.

**Generalizable action:** A semantic-link contract may allow an explicit new restatement/clarification as documentary support; a drift-only contract reasonably abstains. Choose and document evidence semantics before runtime changes. Do not turn all unchanged context into new evidence.

### 15. 964260d9c2da-F01-H14 / I1 / weakens

**Fixed S0:** Represent desired resources through mutable PodSpec fields and report allocated/applied resources through PodStatus.

**Model reason:** The addition discusses conditional alternatives for an allocated-status API. No alternative is adopted here. Its benefits and costs concern particular candidate fields, type choices, migration paths, and container-versus-Pod granularity; they do not establish retirement or incompatibility with a fixed-S0 requirement. Nor do they directly reduce the justification of S0's broad PodStatus reporting choice: several costs arise specifically from proposed representations that S0 does not choose. Prospective DRA support does not supersede the CPU/memory-only scope.

**Source-based interpretation:** Added alternatives document beta delay, type inconsistency, API noise, code churn, long-term checkpointing and risk of hiding container-level allocation. These can affect the rationale for reporting allocated resources, but several costs concern candidate representations that broad I1 does not commit to. Classifier explicitly reasons that no cost reduces the exact broad chosen target.

**Generalizable action:** Reconsider a documented tradeoff without requiring adoption, but require explicit cost-to-current-target applicability. Separate critique of an existing chosen contract from drawbacks of a hypothetical representation; do not automatically weaken I1 because a cons list exists.

## Architectural findings and boundaries

1. The current contract asks for novel target-local architectural effects, while evidence linking can also need new documentary corroboration or policy/rationale alignment for an existing architecture. In `DELTA_REVIEW_INSTRUCTIONS`, `new_operationalisation` requires a mechanism newly realizing the target and invariant/implementation-only effects map to no relation. The model applies those instructions broadly: old architecture with new telemetry or newly explicit documentation is omitted. This is a semantic-contract issue, not a deterministic rejection bug.

2. Positive evidence and adverse drift should have separate semantic questions. First assess whether added/changed current text provides direct qualified evidence for an actual S0 claim; separately assess whether an actual chosen mechanism is replaced, a claim retired, or justification weakened. Keep exact source ownership, before/after roles, proposition qualifiers and prospective authority. Supporting documentation must not certify deployed behavior or automatically close a whole-element investigation need.

3. Same-event consumer migrations can corroborate an explicit representation replacement when their changed input is demonstrably dependent on that representation. Source-owned local contribution still matters. A blanket exclusion of consumer implementations loses linked migration evidence; blanket propagation of event-wide conclusions creates spurious links. H11 is strongest because it also deletes API initialization, not just a consumer formula.

4. Not all missing reference triples are safe recovery targets. Both interim I2 supersession labels require policy constraints absent from fixed S0. Aggregate R2 telemetry does not satisfy per-container-resource explanation or Pod Events. H13 freshness depends on whether clarification is evidentiary support. H14 tradeoffs must be shown to apply to the chosen current design rather than a hypothetical candidate. Keep the frozen scorer unchanged and report these contract tensions independently.

5. Generic regression cases should contrast newly explicit status documentation versus formatting-only context; instrumentation realizing existing distinctions versus a metric that merely mentions unrelated state names; future policy explicitly restating an exact non-goal versus prospective goal fulfillment; same-event producer/consumer migration versus unrelated implementation; a chosen-contract tradeoff versus drawbacks of an unchosen alternative; fixed versus historical target claims.

6. An optional budgeted source-only reconsideration pass should examine semantic contradictions or underexplained abstentions, not use the frozen FN list. There is ~50k estimated input headroom in this run, but six investigation rounds are already used. A second pass must be accounted as a real provider request and cannot be described as free, guaranteed, or an equal-compute comparison.

## Integrity

This is a read-only diagnostic join using the uploaded completed run, exact source hunks, fixed S0, prior completed v4.4 trace and existing code instructions. The diagnosis does not change human labels, scoring, source inputs, runtime code, or hosted outcomes. Per-case interpretations above are analyst judgments, not adjudicated reference corrections.

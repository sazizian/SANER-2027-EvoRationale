# Actual confirmed-reference review of the eleven retained false positives

Offline and read-only. The confirmed S0, all four reference CSVs, confirmation file, and all nine unique FP source patches match their manifest/reference SHA256 values. Fixed target text matches the confirmed S0 in every case. No provider call, released-code edit, reference change, scorer change, or runtime case filter was made.

The typed scope checker retained all eleven v4.9 false positives and marked all 55 alignment flags true. The actual human notes now explain the failure more clearly: part is an overly broad local-contribution policy; part is a difference between qualified source entailment and the reference's selected architectural effect. Neither more boolean flags nor a global dominant-relation rule resolves that difference.

## What the confirmed notes establish

- Operational use is distinct from a model-defining contribution. H05 monitoring uses the resize metric; H01 defines the states. A changed validation detail is not fresh evidence for an already unchanged non-goal. Internal restart recovery is classified as implementation, despite a real dependency migration.
- Genuine consumer accounting migration remains architectural evidence. Scheduler/quota rules are supersession positives even when their rationale is kept. Non-binding controller sketches are support positives.
- The notes do not establish one relation or one target per hunk. The same event assigns I1 supersession to H04/H05/H06/H11 and R1 support to H13. H14 explicitly acknowledges R1 support while its single CSV row is WEAKENS I1.
- Seven of the eleven extras occur on five hunks that already carry a correctly scored effect. Several extra qualified support propositions are literally defensible; they are not fabricated source facts. Their exclusion needs a contribution/output projection policy.

## All eleven scored false positives

### 1. 079aa5fb9ab1-F01-H03 → C2a supports

Reference: **IMPLEMENTATION_ONLY → C2a**. Fixed target: “Changing a Pod's QoS class without a restart is a non-goal.”

Human note: “RESOLVED: B01 adopts Reviewer A's label; A's C2 is renamed C2a;C2b under the agreed split. The hunk's own changes are terminology and emphasis ('QOS Class' vs 'QOS Shape'; bold 'cannot be changed'), a validation detail (Guaranteed pods must set both CPU and memory), and 'resizeable' -> 'restartable' for sidecars. The QoS invariant was already in the pre-image, and the substantive edit to the 2023 non-goals was made by d774b5c, so this hunk adds no rationale evidence.”

Exact source span(s):

> -A pod's QOS class cannot be changed once the pod is started, independent of any resizes.

> +A pod's QOS class **cannot be changed** once the pod is started, independent of any resizes.

> -* Guaranteed pods: must maintain `requests == limits`

> +* Guaranteed pods: must maintain `requests == limits`, and must be set for both CPU & memory

> +* "QOS Class" - The QOS class that was computed based on the original resource requests & limits

> +* "QOS Shape" - The QOS class that _would_ be computed based on the current resource requests &

>  * `.status.qosClass` always reports the original QOS class

Current critic: “A0003:L0031 newly requires both CPU and memory to be set, beyond the retained requests-equal-limits condition. This is substantive, unlike the surrounding terminology changes.”

The new Guaranteed configuration validation detail is real, but the source explicitly separates the original QOS Class from the current-resource QOS Shape. The CPU/memory rule constrains the shape; the stored class is already fixed independently in the pre-image and current text. The added rule does not introduce or newly reject a class-changing transition. The critic promotes shape preservation to fresh support for the class-change prohibition, and the human note expressly excludes this refinement from rationale evidence.

Assessment: **TARGET_OBJECT_AND_FRESH_CONTRIBUTION_CONFUSION; NOT_A_FABRICATED_SOURCE_FACT**.

Generic repair: Keep stored classification and recomputed resource shape as distinct objects. Require a substantive change that directly establishes, rejects, or argues for the exact prohibited transition; a shape-validation detail does not newly enforce an already immutable class.

Risk: Do not require an explanatory why argument for every support: actual reference accepts direct boundary-instantiating sketches and state definitions.

### 2. 68952e4476e4-F01-H05 → I3 supports

Reference: **IMPLEMENTATION_ONLY → R2;I3**. Fixed target: “Model resize operation progress through states such as proposed, in progress, deferred and infeasible.”

Human note: “RESOLVED: B01 adopts Reviewer A's label and IDs. The PRR rollout/monitoring/dependency answers (rollback metrics, test plan, SLIs/SLOs built on the resize-request metric) describe operations. They use the resize-state model but say nothing about why R2 was required. The metric definition itself (H01) is the hunk that operationalises I3/R2.”

Exact source span(s):

> +  - Using `kubelet_container_resize_requests_total`, `completed + infeasible + canceled` request count

> +  should approach `proposed` request count in steady state.

Current critic: “Generic SLO examples are replaced by resize-specific proposed-versus-terminal accounting. The same event introduces the counter and outcome definitions, making this more than consumption of preexisting status values.”

The added SLO uses existing same-event counter states. It does not locally define state meaning, transition, or production. The human note explicitly assigns model operationalisation to H01 and classifies H05 as operational use. The critic imports H01 freshness into H05 and rephrases the target as state-based progress accounting.

Assessment: **REFERENCE_SUPPORTED_LOCAL_CONTRIBUTION_ERROR; NO_DETERMINISTIC_PARSE_FAILURE**.

Generic repair: Separate defining or newly binding a target state predicate from monitoring or aggregating the model. Context can explain the metric but must not relocate another artifact's model-defining contribution.

Risk: A metric definition that explicitly binds target states or three-way completion can legitimately support I3/R1; no global metric ban.

### 3. 964260d9c2da-F01-H04 → I1 supports

Reference: **SUPERSEDES → I1**. Fixed target: “Represent desired resources through mutable PodSpec fields and report allocated/applied resources through PodStatus.”

Human note: “Open point: the R1 convention. Same relation. Core decision: the kubelet checkpoints the allocated state, and the AllocatedResources field stays alpha behind a separate gate as a 'candidate for future removal'. This supersedes I1's 'allocated via PodStatus' for beta. R1 is retained inside the node ('cached and checkpointed locally').”

Exact source span(s):

> -PodStatus is extended to show the resources allocated for and applied to the Pod and its Containers.

> +PodStatus is extended to show the resources applied to the Pod and its Containers.

> +The actual resources are reported by the container runtime in some cases, and for all other

> +resources are copied from the latest snapshot of allocated resources.

Current critic: “The reporting fallback changes from the public AllocatedResources field to the latest allocated-resource snapshot, giving a fresh source-defined reporting mechanism.”

The applied-reporting branch is literally preserved and its fallback representation changes. The same artifact replaces ordinary allocated-status reporting. The human reference chooses I1 supersession, whereas the broad runtime policy explicitly permits a qualified independently affected material subclaim. This is a compound-target projection disagreement, not evidence that the reporting proposition is false.

Assessment: **PRINCIPAL_CHANGE_VS_QUALIFIED_PARTIAL_SUPPORT_GAP**.

Generic repair: Record clause effects separately, then explicitly distinguish a surviving contextual branch from a new target contribution. Any target-level projection that suppresses an extra support must be a documented case-neutral policy, not a claim of failed source entailment.

Risk: A universal SUPERSEDES-over-SUPPORTS rule fails H13 and independent local contributions.

### 4. 964260d9c2da-F01-H04 → R1 supports

Reference: **SUPERSEDES → I1**. Fixed target: “Distinguish the desired resources declared in the Pod spec from the resources allocated to the Pod on the node and from the actual resources applied to its containers.”

Human note: “Open point: the R1 convention. Same relation. Core decision: the kubelet checkpoints the allocated state, and the AllocatedResources field stays alpha behind a separate gate as a 'candidate for future removal'. This supersedes I1's 'allocated via PodStatus' for beta. R1 is retained inside the node ('cached and checkpointed locally').”

Exact source span(s):

> +When the Kubelet admits a pod initially or admits a resize, all resource requirements from the spec

> +are cached and checkpointed locally. When a container is (re)started, these are the requests and

> +limits used.

Current critic: “New local allocation caching/checkpointing makes the allocated representation independent of ordinary public status, alongside explicit desired and actual representations.”

The source and human note both preserve desired/allocated/actual distinctions. The new allocation storage is a fresh implementation of the retained distinction. Human notes annotate the principal I1 storage/reporting replacement, but do not explicitly deny a qualified R1 entailment. H13 is annotated SUPPORTS precisely because the same R1 concept survives.

Assessment: **SOURCE_ENTAILMENT_DEFENSIBLE; CONTRIBUTION_PROJECTION_UNDERDETERMINED**.

Generic repair: Require the classifier to distinguish a target-predicate definition from a representation change preserving the predicate, and retain the latter in contextual evidence unless an independent target contribution is shown.

Risk: Blanket retained-predicate rejection contradicts the reference R1 support on H13.

### 5. 964260d9c2da-F01-H05 → I1 supports

Reference: **SUPERSEDES → I1**. Fixed target: “Represent desired resources through mutable PodSpec fields and report allocated/applied resources through PodStatus.”

Human note: “Agreed. Edits the 2023 Risks text (L352-365); consequence of H04.”

Exact source span(s):

> -   tracked in Pod.Status.ContainerStatuses[i].AllocatedResources, applications

> +   tracked in Pod.Status.ContainerStatuses[i].Resources, applications

Current critic: “The compatibility statement substantively changes its tracked object from true allocations in AllocatedResources to actual configurations in Resources.”

The new risk text directly asserts actual-status tracking, so qualified applied-reporting entailment is defensible. Human notes classify the hunk as a consequence of the I1 allocation-reporting replacement. A standalone semantic alignment checker following broad current-evidence policy will confirm this extra relation.

Assessment: **POLICY_COMPATIBLE_PARTIAL_ENTAILMENT; REFERENCE_PROJECTION_GAP**.

Generic repair: Separate changed contract effect from a surviving reporting branch; aggregate compound-target relations with a documented contribution policy.

Risk: Rejecting all current reporting assertions would lose legitimate source-defined support.

### 6. 964260d9c2da-F01-H05 → R1 supports

Reference: **SUPERSEDES → I1**. Fixed target: “Distinguish the desired resources declared in the Pod spec from the resources allocated to the Pod on the node and from the actual resources applied to its containers.”

Human note: “Agreed. Edits the 2023 Risks text (L352-365); consequence of H04.”

Exact source span(s):

> +   representative of desired state, and Pod's actual resource configurations are

> +   tracked in Pod.Status.ContainerStatuses[i].Resources, applications

> +   configurations will see values that may not represent actual configurations. As a

Current critic: “The warning newly contrasts desired spec values with actual configurations, replacing its previous desired-versus-allocation contrast.”

The current warning literally compares desired spec and actual status, but does not establish the complete three-way distinction. The hypothesis is qualified accordingly. Human note only records the I1 consequence. No false whole-element certification or fabricated third state occurred; disagreement concerns whether the revised warning is an independent R1 contribution.

Assessment: **QUALIFIED_PARTIAL_ENTAILMENT_DEFENSIBLE; CONTRIBUTION_BOUNDARY_GAP**.

Generic repair: Identify the changed local contract and keep incidental surviving distinctions separate unless the distinction itself receives a new predicate definition or argument.

Risk: New comparisons can be material support under existing PREDICATE instructions; narrowing this is a changed semantic policy.

### 7. 964260d9c2da-F01-H06 → R1 supports

Reference: **SUPERSEDES → I1**. Fixed target: “Distinguish the desired resources declared in the Pod spec from the resources allocated to the Pod on the node and from the actual resources applied to its containers.”

Human note: “Agreed. The kubelet no longer writes the AllocatedResources status field; consequence of H04.”

Exact source span(s):

> -requests & limits to its internal allocated resources checkpoint, and write the

> -admitted requests to the `AllocatedResources` field in the container status.

> +requests & limits to its internal allocated resources checkpoint.

> -  Status...AllocatedResources field and setting Status.Resize to

> +  the allocated resourcesa, and sets Status.Resize to

Current critic: “The revised sequence removes the allocation-status dependency while retaining separate allocation acceptance and subsequent actual-status update steps.”

The new contribution removes allocation-status publication. Desired fit, allocation acceptance, and later actual-status update exist before and after. The checker explicitly confirms that all three remain distinguishable; it does not show a newly introduced three-way sequencing invariant.

Assessment: **REFERENCE_SUPPORTED_TARGET_FRESHNESS_OVERREACH**.

Generic repair: Compare normalized before/current target predicate independent of changed field names. A revised storage reference must not alone establish a new abstract distinction relation.

Risk: Fresh definition of a preserved concept can still legitimately support it; mere absence of architectural drift is not sufficient to reject support.

### 8. 964260d9c2da-F01-H07 → I1 supersedes

Reference: **IMPLEMENTATION_ONLY → I1**. Fixed target: “Represent desired resources through mutable PodSpec fields and report allocated/applied resources through PodStatus.”

Human note: “Agreed. Restart tolerance now reads the checkpoint; the 2023 reason is kept verbatim.”

Exact source span(s):

> -Pods are admitted at their current Status...AllocatedResources

> +Pods are re-admitted based on their current allocated resources (restored from

> + checkpoint). Pending resizes are handled after all existing Pods have been

> +added. This ensures that resizes don't affect previously admitted existing Pods.

Current critic: “Re-admission changes from Status.AllocatedResources to allocation restored from checkpoint, concretely migrating an existing consumer dependency.”

There is a real local old-status to checkpoint dependency change, and adopted H04 contract context. The inherited runtime dependent_replacement policy permits this. Human note nevertheless classes recovery migration as IMPLEMENTATION_ONLY, keeping its reason verbatim. Thus it is not a missing-proof bug; it is over-broad dependency contribution relative to the reference.

Assessment: **GENERIC_DEPENDENCY_POLICY_MISMATCH; NOT_FALSE_SOURCE_MIGRATION**.

Generic repair: For target publication/reporting replacement, require a local public contract producer or explicitly specified cross-boundary accounting dependency. Owner-internal recovery of an unchanged allocation quantity should stay an implementation consequence unless it independently changes a target obligation.

Risk: Scheduler/quota changes remain valid supersession TPs even with unchanged rationale. No blanket consumer, recovery-word, or unchanged-reason filter.

### 9. 964260d9c2da-F01-H11 → R1 supports

Reference: **SUPERSEDES → I1**. Fixed target: “Distinguish the desired resources declared in the Pod spec from the resources allocated to the Pod on the node and from the actual resources applied to its containers.”

Human note: “Agreed. Quota uses status resources; removes 2023 L655.”

Exact source span(s):

> -`.spec.container[*].resources.requests` and `.status.containerStatuses[*].allocatedResources` to

> +`.spec.container[*].resources.requests` and `.status.containerStatuses[*].resources` to

> -pod updates where either `.status...allocatedResources` or `.status...resources` changed.

> +pod updates where `.status...resources` changed.

Current critic: “The request comparison newly uses actual status rather than allocated status. This is substantive evidence beyond the pre-existing desired/actual limits comparison.”

The local public consumer read/update-trigger migration substantiates the correct I1 supersession. The new desired/actual maximum literally instantiates a partial R1 comparison, which existing PREDICATE instructions explicitly allow. Human note prioritizes the dependency change without separately labelling that comparison.

Assessment: **POLICY_COMPATIBLE_PARTIAL_ENTAILMENT; PRINCIPAL_CHANGE_PROJECTION_GAP**.

Generic repair: Preserve the consumer contract replacement, while deciding explicitly whether the target distinction is newly contributed or only contextual to the migrated rule.

Risk: Global downstream-consumer rejection would discard multiple correct I1 supersession triples.

### 10. 964260d9c2da-F01-H13 → I1 supersedes

Reference: **SUPPORTS → R1**. Fixed target: “Represent desired resources through mutable PodSpec fields and report allocated/applied resources through PodStatus.”

Human note: “Agreed. 'Completed' still means spec == allocated == actual, so R1's concept survives.”

Exact source span(s):

> -  - `completed` - Resize operation completed successfully (`spec.Resources == status.Allocated == status.Resources`)

> +  - `completed` - Resize operation completed successfully (`spec.Resources == allocated resources == status.Resources`)

Current critic: “The completion operand changes from public status.Allocated to allocated resources. Same-event context establishes local allocation storage, making this more than an isolated rename.”

The local metric changes an abstract completion operand name, while preserving the exact desired/allocated/actual equality. No local allocation read, reporting write, checkpoint retrieval, or external consumer contract is specified. The checker imports H04 storage context to infer a reporting-dependency replacement. Human note intentionally assigns R1 support to the preserved completion predicate.

Assessment: **STRONGEST_UNSUPPORTED_TARGET_LOCAL_BRIDGE; POLICY_ALLOWS_OVERPROPAGATION**.

Generic repair: An external replacement contract can explain a local changed operation, but cannot supply the local reporting operation or cross-boundary dependency itself. Require the exact local operation to be source-defined; keep direct metric predicate evidence for R1.

Risk: Do not blanket-reject contextual migration or treat all operand changes as inconsequential: source-explicit consumer contracts can still migrate.

### 11. 964260d9c2da-F01-H14 → I1 supports

Reference: **WEAKENS → I1**. Fixed target: “Represent desired resources through mutable PodSpec fields and report allocated/applied resources through PodStatus.”

Human note: “Open point: the R1 convention. Same relation. The alternatives show that the 2023 field (v1.ResourceList, requests only; L204-205) cannot carry allocated limits, and they record API-evolution costs, which weakens I1's field as specified. All three options keep a distinct allocated state (Option 1 names desired, allocated and actual), so for R1 this hunk is supportive rather than weakening, and R1 is not linked to WEAKENS.”

Exact source span(s):

> +If we need allocated resources & limits in the pod status API, the following options have been

> +We can't change the type of the existing field, so instead we

> +`ContainerStatus.AllocatedResourceLimits` alongside `AllocatedResources` (requests).

> +- Extra risk in assuming nothing outside the node ever needs to know container-level allocated resources.

Current critic: “The newly added con directly identifies the risk of assuming external consumers never need container-level allocation information.”

The selected option-3 con is a genuine conditional argument for retaining external container-level allocation visibility. Human reference instead weakens I1's specific existing request-only field because it cannot carry limits and incurs API-evolution costs. The fixed I1 paraphrase does not explicitly state the existing field type or request-only limitation, so exact chosen-mechanism binding must come from source context, not from a stronger invented target. The note also expressly acknowledges R1 supportive evidence absent from the row's WEAKENS ID list.

Assessment: **OPPOSITE_ARGUMENT_SELECTION_PLUS_CHOSEN_MECHANISM_GRANULARITY_GAP**.

Generic repair: Extract premises/conclusions separately for the chosen baseline mechanism and each conditional alternative. Compare field-specific costs with the selected contract and keep alternative visibility arguments distinct from the hunk's principal changed mechanism effect.

Risk: The risk sentence remains a defensible qualified support argument. A proposal ban would remove actual G2/C1/C2a supporting sketches; suppressing it is task projection, not deterministic entailment repair.

## Why a blanket dominant relation would be wrong

The EVENT row says, “This is one decision spread over many hunks, so count it once.” That concerns event accounting. Its separate convention says, “the IDs column lists only the elements the stated relation applies to, and other affected elements are recorded here with their own relation.” The H14 note goes further: “for R1 this hunk is supportive rather than weakening, and R1 is not linked to WEAKENS.” A single-relation CSV projection can omit an acknowledged secondary relation; it is not a general proof that the secondary proposition is invalid.

H04 notes “R1 is retained inside the node”, while H13 notes “Completed still means spec == allocated == actual, so R1's concept survives” and labels R1 SUPPORTS. Thus a filter that rejects all retained predicates would reject an actual true positive. A supersession-first rule would likewise retain H13's false I1 supersession while discarding its correct R1 support.

## Existing policy tension

- `er_v49_build/EvoRationale_v49_DEV_EN/evorationale/evidence_trace_verification.py::EVIDENCE_TRACE_INSTRUCTIONS`: “lack of novel design drift does not imply lack of current source evidence.” Support is deliberately broader than architectural drift.
- `er_v49_build/EvoRationale_v49_DEV_EN/evorationale/evidence_trace_verification.py::EVIDENCE_TRACE_INSTRUCTIONS`: “Reusing an existing concept within a new operational witness can corroborate it; merely mentioning its name cannot.” Operational witness breadth permits the QoS refinement and SLO interpretations; the actual reference draws a narrower contribution boundary.
- `er_v49_build/EvoRationale_v49_DEV_EN/evorationale/evidence_trace_verification.py::EVIDENCE_TRACE_INSTRUCTIONS`: “dependent_replacement is a target-local migration of a consumer's dependency that evidences an explicitly documented same-event architectural replacement” H07 is policy-compatible and H13 is a weaker local bridge; neither is a raw parsing/source-hash failure.
- `er_v49_build/EvoRationale_v49_DEV_EN/evorationale/evidence_trace_verification.py::EVIDENCE_TRACE_INSTRUCTIONS`: “Do not let a primary effect suppress independent evidence for other exact elements.” A universal dominant-relation filter conflicts with current policy.
- `er_v49_build/EvoRationale_v49_DEV_EN/evorationale/pair_review_verification.py::PREDICATE_INSTRUCTIONS`: “A new comparison among representations can corroborate a distinction predicate; consuming a status value alone does not establish a publish/write/report obligation.” The R1 partial-comparison extras are expected under current policy; local consumption is insufficient for reporting support but genuine changed dependency remains eligible.
- `er_v49_build/EvoRationale_v49_DEV_EN/evorationale/evidence_trace_verification.py::EVIDENCE_TRACE_INSTRUCTIONS`: “direct_rationale is an explicit argument, policy or concrete design sketch corroborating an exact stated goal or non-goal” Actual non-binding controller sketch support agrees with this broader wording.
- `er_v49_build/EvoRationale_v49_DEV_EN/evorationale/pair_review_verification.py::PREDICATE_INSTRUCTIONS`: “a candidate sketch or generic type-consistency benefit alone does not argue for the chosen target.” Stricter argument wording contributed to rejecting G2 support even though actual reference accepts the sketch; scope kit appends this existing v49 instruction.

Actual workload H05 notes call the controller strategy a “Non-binding sketch” and label G2/C1 support. The latest scope checker removes G2 because it “does not explicitly argue for that actor-discretion goal.” This supports a concrete policy inconsistency: literal actor-owned strategy can instantiate the goal at proposal scope without a separate why argument. The strict wording was already in v4.9; the scope recheck applied it differently. Restore an internally consistent contract rather than broadly banning proposals.

## Concrete repair that follows from source roles

Add one source-first contribution analysis before relation projection. It must identify the exact changed local operation or predicate, normalized before/current meaning, its role, exact target clause, and which dependency/argument is supplied locally. Separate contract definitions, specified cross-boundary contract consumers, owner-internal recovery, monitoring use, chosen-mechanism arguments, and conditional-alternative arguments. This is more informative than five ungrounded true/false confirmations.

Context may explain a changed local operation but must not manufacture that operation or relocate another hunk's contribution. Preserve public scheduler/quota dependency migration; treat internal recovery and bare metric operand rewriting as implementation consequences absent a separate target obligation. Preserve actual state definitions, three-way completion predicates and actor-owned conditional sketches. Compare the selected baseline field's costs separately from one option's argument for keeping visibility.

Keep literal contextual support in diagnostics. If the product should emit only contribution-qualified architectural effects for hunk scoring, document that projection explicitly and allow multiple relations when genuinely independent local contributions exist. Do not make target IDs, hunk IDs, relation priority or observed Gold outcomes part of runtime selection. The official S0/reference/scorer remain frozen.

Synthetic contrasts should separately test stored class versus computed profile, defining state semantics versus consuming counters, internal checkpoint recovery versus explicit external accounting contract migration, and chosen-field cost versus an unchosen alternative’s visibility argument. Tests can verify proof fields and routing; they cannot assert that a real model will interpret those semantics correctly.

Contrasting synthetic fixtures and held-out source episodes are required to validate a new policy. This audit demonstrates no new F1 result, and does not establish that 80–85% F1 is reachable. The latest actual result remains 13 TP / 11 FP / 6 FN, all-scope F1 0.604651; its parent remains 14 / 11 / 5, F1 0.636364.

Independent five-hunk contract review: `tmp/frozen_scope_contract_review.md` and `.json`. Complete machine-readable evidence: `development_review/frozen_actual_fp_review.json`.

# Frozen annotation review of actual false negatives

The confirmed annotations reveal two separate issues: a stricter support criterion in the checker, and temporal/implementation detail missing from the fixed runtime target. No runtime or historical artifact was changed.

## 079aa5fb9ab1-F01-H05 / G2 / supports

The frozen note expressly accepts a non-binding controller sketch as support: controllers attempt resizing and recreate replicas when illegal. It does not require an explicit because-style argument. A proposed policy choice and fallback instantiate a limited actor-choice goal; adoption and full actor-wide fulfillment remain unproved. The new scope critic imposed a narrower argument-only route, explaining the lost TP.

Frozen hunk note: Open point: C2a. Same relation. Non-binding sketch: workload controllers attempt an in-place resize and recreate replicas when it is not legal (G2, C1; 2023 Future Enhancement L691-692). The explicit-QOSClass sketch keeps QoS class changes tied to recreation ('can be changed, triggering a recreation of all replicas'), which matches C2a. The removal of 'Allow resource limits to be updated (VPA feature)' (L694) is UNKNOWN and is not linked.

## 079aa5fb9ab1-F01-H05 / C1 / supports

The same frozen note expressly maps controller-owned illegal-resize recreation to C1. It permits qualified evidence of the initiating actor's fallback responsibility, without proof of every lifecycle operation or adopted controller behavior. The source does not literally restate the full non-goal, but the reference accepts the concrete delegation sketch as partial support. A semantic policy requiring an explicit argument for the entire exclusion is stricter than this criterion.

Frozen hunk note: Open point: C2a. Same relation. Non-binding sketch: workload controllers attempt an in-place resize and recreate replicas when it is not legal (G2, C1; 2023 Future Enhancement L691-692). The explicit-QOSClass sketch keeps QoS class changes tied to recreation ('can be changed, triggering a recreation of all replicas'), which matches C2a. The removal of 'Allow resource limits to be updated (VPA feature)' (L694) is UNKNOWN and is not linked.

## 079aa5fb9ab1-F01-H02 / I2 / supersedes

The note explicitly says the mutable-entry rule was introduced by d774b5c, changed to append-only here, and 2023 I2 is silent on mutability. This supersedes an interim2024 contract mapped to I2, not the immutable2023 I2 proposition. Event annotations give this same interpretation and warn against automatically treating interim changes as baseline drift. A fixed2023 predicate checker's abstention is semantically consistent with its stated task.

Frozen hunk note: Agreed. Interim only: 'mutable, but must have an entry for every resizable resource type' (introduced by d774b5c) -> 'append-only'. 2023 I2 is silent on mutability.

## 04de3dac4669-F01-H01 / I2 / supersedes

The note explicitly calls this an interim append-only-to-mutable reversal and says 2023 I2 is unaffected. The event note records the2024 sequence: silent2023 -> mutable September7 -> append-only September17 -> provisionally mutable October10. A versioned claim target is required to report honest interim supersession while preserving the2023 baseline.

Frozen hunk note: Agreed. Interim reversal append-only -> mutable; 2023 I2 unaffected.

## 68952e4476e4-F01-H01 / R2 / supports

The note justifies R2 because metric states mirror Status.Resize. It accepts state-model operational correspondence as qualified supporting implementation. It does not assert that an aggregate Pod-level metric exposes each container/resource discrepancy or generates required Events. The event note explicitly says operationalisation is not evidence that the original reasons were correct. This is a broader partial-support criterion than full compound-R2 entailment.

Frozen hunk note: Open point: R1. Same relation. Metric states mirror Status.Resize (I3, R2). The 'completed' condition spec.Resources == status.Allocated == status.Resources uses the three-state distinction (R1). Both reviewers linked the same definition, as later edited, to R1 in 964260d9c2da-F01-H13, so R1 is proposed here for consistency.

## 964260d9c2da-F01-H14 / I1 / weakens

The note specifically weakens the2023 allocated-status field as specified: requests-only v1.ResourceList cannot carry allocated limits and options record API-evolution costs. This differs from the checker-selected Option3 consumer-visibility risk, which can instead favor allocation reporting. A qualified weakening argument must bind costs to the actual baseline field implementation, while leaving the abstract three-state R1 distinction intact. S0 I1 abstracts away the type and requests-only detail; original_evidence is empty. Current H04 states alphaAllocatedResources included onlyrequests, but its removed2024 type is ResourceRequirements, so cross-version details must be distinguished.

Frozen hunk note: Open point: the R1 convention. Same relation. The alternatives show that the 2023 field (v1.ResourceList, requests only; L204-205) cannot carry allocated limits, and they record API-evolution costs, which weakens I1's field as specified. All three options keep a distinct allocated state (Option 1 names desired, allocated and actual), so for R1 this hunk is supportive rather than weakening, and R1 is not linked to WEAKENS.

## Generic repair implications

Separate evidence routes for qualified realization, explicit rationale, observed validation, and fulfillment.: For a goal or delegation boundary, permit a concrete proposed operation/policy that instantiates its exact limited predicate to provide discussion-level partial support. An explicit because-argument is optional for this route. Keep source_role=proposal_or_alternative and no runtime/adoption certification.

Post-run development repair, not held-out proof or an assured F1 increase.

Represent target versions and temporal relation scope explicitly.: Keep fixed S0 immutable. Independently ground S(t_prior)/S(t_after) from source-owned old/current contracts and classify interim supersession against that version; expose baseline_relation separately from interim_relation. Current d774 input is commit-title-only, so fetch/capture pinned missing intermediate content in a separately versioned future dataset if full timeline reconstruction is needed.

Do not silently reinterpret interim supersession as superseding the2023 fixed clause just to match the existing all-scope score.

Bind implementation costs to pinned baseline mechanisms.: Attach independently captured baseline source/context to a claim's mechanism mapping rather than reviewer notes. Distinguish selected-field type/limits, conceptual requirement and later replacements. A cost can weaken a selected mechanism while preserving its requirement, but candidate-specific costs do not automatically transfer.

Changing or expanding source context creates a distinct experiment; preserve original53 inputs and frozen scoring results.

These annotations support a generic qualified-realization/partial-operational-support policy and a versioned temporal-target architecture. They do not justify hardcoded case filters, relaxing full reporting/Events obligations, adding private reviewer notes to hosted prompts, or altering frozen Gold/S0/scorer. Establish and freeze a coherent target relation contract before another paid experiment; use generic counterexamples and later untouched episodes for validation.

# Independent Source-Based Audit — Kubernetes KEP-1287 Reviewer Labels

**Scope:** October 26, 2023 pinned S0; 18 atomic S0 statements; 23 screened commits; 4 curated events; 30 patch hunks. Additional public GitHub diffs inspected: d774b5c, a093b5b, be6445f, 9c2404d, 5388d74. This is an independent textual-methodological audit, **not** a replacement for the two human reviewers or a revised gold standard.

## Executive assessment

- **The 18 final S0 element texts are traceable to the immutable 2023 README.** All pinned line anchors were checked against the captured source.
- **The core 2024 beta-scope revision of I1 is well supported.** Commit `964260d9c2da` removes allocated resource reporting from the beta public PodStatus contract in favor of Kubelet checkpointing, while preserving some underlying three-state rationale.
- **Two SUPERSEDES events target an interim 2024 design, not the 2023 S0.** Both `079aa5fb` and `04de3dac` are valid temporal events but must not be interpreted as invalidating baseline I2.
- **The gold/reference annotations are not beyond question.** Six of the 30 curated hunks merit a targeted mapping/relation review; two other hunks carry crucial interim-only scope qualifications. These are review flags, not proven incorrect labels.
- **Coverage, not just label validity, is a material concern.** `d774b5c` changes original InitContainer non-goal C2b, while `a093b5b` revises the CRI section. Neither commit has hunk-level labels in the 30-hunk pilot.
- **This dataset cannot establish architecture-outcome accuracy or repository-wide recall.** It is a curated, retrospectively captured single-project development pilot. Keep frozen v1 unmodified; create a distinct review/versioned extension if labels or samples change.

## Reproducibility and source integrity

- Source README Git blob SHA-1: `ce5124cf7975a7d4ce6a122b2cb4006b4bc0ea2d`; independently recomputed and matched.
- Source README SHA-256: `f42855e662d154268b3fca59ef816128f8b7e5359e56466a174a375a930b26fa`; independently recomputed and matched.
- All 30 hunk IDs and their recorded SHA-256 hashes match between the private reference file and the source hunk index. This establishes consistency of identifiers and index hashes, not semantic correctness.
- The 2023 commit is an immutable reproducible revision, not a independently verified approval event; historical replay is not certified.

## Prioritized questions for human adjudication

| ID | Priority | Issue | Review action | Source |
|---|---|---|---|---|
| A01 | HIGH | Unrepresented 2023-to-2024 scope change (`d774b5cf414b`) | Obtain a separate annotation for the full d774b5c diff against pinned 2023 S0; decide baseline supersession vs exception/clarification. | [GitHub](https://github.com/kubernetes/enhancements/commit/d774b5cf414b6a13fd53064d157f2b535f25e430) |
| A02 | HIGH | Major CRI revision outside curated hunk sample (`a093b5b260a5`) | Review full a093b5b diff; distinguish goal fulfilled, API redesign, and superseded design. | [GitHub](https://github.com/kubernetes/enhancements/commit/a093b5b260a5016a5c6feb4407728fa1d1ee7dfd) |
| A03 | HIGH | Inconsistent C2b mapping across frozen tables (`079aa5fb9ab1-F01-H03`) | Ask reviewers to confirm whether H03 should additionally map to C2b (possibly as a non-positive context link). | [GitHub](https://github.com/kubernetes/enhancements/commit/079aa5fb9ab1a66f09f1d0c841025f7451474265) |
| A04 | HIGH | Temporal target changes exact-match interpretation (`079aa5fb9ab1;04de3dac4669`) | Retain interim relations as a distinct temporal task; do not interpret all-30 F1 as 2023-baseline drift detection. | [GitHub](https://github.com/kubernetes/enhancements/commit/04de3dac4669f4b2f792c17488c680ce4b144679) |
| A05 | MEDIUM | Inconsistent implementation vs supersession boundary (`964260d9c2da-F01-H07`) | Decide rubric based on whether a downstream operational consequence is a separate supersession link. | [GitHub](https://github.com/kubernetes/enhancements/commit/964260d9c2da8f75423771fffd9989077d4d92aa) |
| A06 | MEDIUM | SUPPORTS may conflate documentation with evidence (`68952e4476e4-F01-H01;964260d9c2da-F01-H13`) | Define SUPPORTS as consistent textual evidence vs operational empirical corroboration; keep interpretation narrow. | [GitHub](https://github.com/kubernetes/enhancements/commit/68952e4476e47eb71321a2c7f92844e602d38d22) |
| A07 | MEDIUM | Speculative design sketch counted as SUPPORTS (`079aa5fb9ab1-F01-H05`) | Consider a context-only or proposed alternative label; if SUPPORTS retained, explicitly qualify as proposal consistency. | [GitHub](https://github.com/kubernetes/enhancements/commit/079aa5fb9ab1a66f09f1d0c841025f7451474265) |
| A08 | MEDIUM | Unsettled interpretation of WEAKENS on alternatives (`964260d9c2da-F01-H14`) | Ask reviewers for a precise WEAKENS rule distinguishing technical limitation from undecided option analysis. | [GitHub](https://github.com/kubernetes/enhancements/commit/964260d9c2da8f75423771fffd9989077d4d92aa) |
| A09 | HIGH | Non-independent evidence concentration (`964260d9c2da`) | Report event/commit-cluster sensitivity alongside hunk-level micro-F1; do not treat 30 hunks as 30 independent cases. | [GitHub](https://github.com/kubernetes/enhancements/commit/964260d9c2da8f75423771fffd9989077d4d92aa) |
| A10 | HIGH | Only four of 23 timeline commits have curated full patches (`23-commit timeline`) | Keep present dataset frozen as v1 development pilot; curate and adjudicate additional commits as a separate v2, then use independent cases for confirmatory metrics. | [GitHub](https://github.com/kubernetes/enhancements/tree/5950905de89aab2be202d28b823701276cbefea0/keps/sig-node/1287-in-place-update-pod-resources) |

## Hunk-by-hunk provisional evidence audit

Status **PLAUSIBLE** means no obvious contradiction was found against the available source diff under the current permissive relation rubric; it is not a correctness certification. **RECHECK** means a substantive mapping or classification ambiguity exists. **INTERIM_ONLY** means the original relation can be valid for 2024 but does not constitute direct 2023 drift.

| Hunk | Reviewer relation | S0 IDs | Audit status | Reason / qualification |
|---|---|---|---|---|
| `68952e4476e4-F01-H01` | SUPPORTS | `R2;I3;R1` | RECHECK | R1 is inferred from a new metric equality; R2/I3 mapping is stronger. Ask if this operational metric independently supports the three-state distinction. |
| `68952e4476e4-F01-H02` | UNRELATED | `—` | PLAUSIBLE | No clear textual contradiction; interpretation remains conditional on the stated relation and temporal rubric. |
| `68952e4476e4-F01-H03` | UNRELATED | `—` | PLAUSIBLE | No clear textual contradiction; interpretation remains conditional on the stated relation and temporal rubric. |
| `68952e4476e4-F01-H04` | SUPPORTS | `I1` | PLAUSIBLE | No clear textual contradiction; interpretation remains conditional on the stated relation and temporal rubric. |
| `68952e4476e4-F01-H05` | IMPLEMENTATION_ONLY | `R2;I3` | PLAUSIBLE | No clear textual contradiction; interpretation remains conditional on the stated relation and temporal rubric. |
| `68952e4476e4-F01-H06` | IMPLEMENTATION_ONLY | `I1` | PLAUSIBLE | No clear textual contradiction; interpretation remains conditional on the stated relation and temporal rubric. |
| `68952e4476e4-F02-H01` | UNRELATED | `—` | PLAUSIBLE | No clear textual contradiction; interpretation remains conditional on the stated relation and temporal rubric. |
| `68952e4476e4-F02-H02` | UNRELATED | `—` | PLAUSIBLE | No clear textual contradiction; interpretation remains conditional on the stated relation and temporal rubric. |
| `079aa5fb9ab1-F01-H01` | UNRELATED | `—` | PLAUSIBLE | No clear textual contradiction; interpretation remains conditional on the stated relation and temporal rubric. |
| `079aa5fb9ab1-F01-H02` | SUPERSEDES | `I2` | INTERIM_ONLY | Correct supersession of 2024 interim ResizePolicy mutability; do not count as a supersession of 2023 I2. |
| `079aa5fb9ab1-F01-H03` | IMPLEMENTATION_ONLY | `C2a` | RECHECK | Hunk changes sidecar wording (restartable InitContainers) but maps only to C2a. Event note also explicitly links C2b to H03; confirm C2b mapping and relation granularity. |
| `079aa5fb9ab1-F01-H04` | IMPLEMENTATION_ONLY | `C2a` | PLAUSIBLE | No clear textual contradiction; interpretation remains conditional on the stated relation and temporal rubric. |
| `079aa5fb9ab1-F01-H05` | SUPPORTS | `G2;C1;C2a` | RECHECK | Added design sketch is expressly future/illustrative. SUPPORTS G2/C1/C2a is plausible as consistency, but does not establish implemented or approved behavior. |
| `964260d9c2da-F01-H01` | UNRELATED | `—` | PLAUSIBLE | No clear textual contradiction; interpretation remains conditional on the stated relation and temporal rubric. |
| `964260d9c2da-F01-H02` | UNRELATED | `—` | PLAUSIBLE | No clear textual contradiction; interpretation remains conditional on the stated relation and temporal rubric. |
| `964260d9c2da-F01-H03` | SUPERSEDES | `I1` | PLAUSIBLE | No clear textual contradiction; interpretation remains conditional on the stated relation and temporal rubric. |
| `964260d9c2da-F01-H04` | SUPERSEDES | `I1` | PLAUSIBLE | No clear textual contradiction; interpretation remains conditional on the stated relation and temporal rubric. |
| `964260d9c2da-F01-H05` | SUPERSEDES | `I1` | PLAUSIBLE | No clear textual contradiction; interpretation remains conditional on the stated relation and temporal rubric. |
| `964260d9c2da-F01-H06` | SUPERSEDES | `I1` | PLAUSIBLE | No clear textual contradiction; interpretation remains conditional on the stated relation and temporal rubric. |
| `964260d9c2da-F01-H07` | IMPLEMENTATION_ONLY | `I1` | RECHECK | Changes restart-tolerance source from public status.AllocatedResources to node checkpoint. Compare with H04/H06/H08 SUPERSEDES I1; current IMPLEMENTATION_ONLY may be rubric-dependent. |
| `964260d9c2da-F01-H08` | SUPERSEDES | `I1` | PLAUSIBLE | No clear textual contradiction; interpretation remains conditional on the stated relation and temporal rubric. |
| `964260d9c2da-F01-H09` | SUPERSEDES | `I1` | PLAUSIBLE | No clear textual contradiction; interpretation remains conditional on the stated relation and temporal rubric. |
| `964260d9c2da-F01-H10` | IMPLEMENTATION_ONLY | `I1` | PLAUSIBLE | No clear textual contradiction; interpretation remains conditional on the stated relation and temporal rubric. |
| `964260d9c2da-F01-H11` | SUPERSEDES | `I1` | PLAUSIBLE | No clear textual contradiction; interpretation remains conditional on the stated relation and temporal rubric. |
| `964260d9c2da-F01-H12` | SUPERSEDES | `I1` | PLAUSIBLE | No clear textual contradiction; interpretation remains conditional on the stated relation and temporal rubric. |
| `964260d9c2da-F01-H13` | SUPPORTS | `R1` | RECHECK | Nearly a terminology substitution for a metric completion predicate. SUPPORTS R1 is weak evidence of rationale validity; a purely consequential/editorial label is plausible. |
| `964260d9c2da-F01-H14` | WEAKENS | `I1` | RECHECK | Documents alternatives/trade-offs and limits of old field. Does this constitute WEAKENS I1, or evidence of reconsideration without a new decision? Clarify taxonomy. |
| `964260d9c2da-F02-H01` | UNRELATED | `—` | PLAUSIBLE | No clear textual contradiction; interpretation remains conditional on the stated relation and temporal rubric. |
| `964260d9c2da-F02-H02` | IMPLEMENTATION_ONLY | `I1` | PLAUSIBLE | No clear textual contradiction; interpretation remains conditional on the stated relation and temporal rubric. |
| `04de3dac4669-F01-H01` | SUPERSEDES | `I2` | INTERIM_ONLY | Correct reversal of 2024 interim append-only rule; original 2023 I2 was silent on mutability. |

## New commits inspected outside curated four

| Commit | Existing screening | Independent source-based finding |
|---|---|---|
| [`d774b5cf414b`](https://github.com/kubernetes/enhancements/commit/d774b5cf414b6a13fd53064d157f2b535f25e430) | POTENTIALLY_RELEVANT | Original non-goal shifts from InitContainers generally to non-restartable InitContainers; sidecars become resizable. Baseline C2b change candidate. |
| [`a093b5b260a5`](https://github.com/kubernetes/enhancements/commit/a093b5b260a5016a5c6feb4407728fa1d1ee7dfd) | NEEDS_DIFF | CRI section rewrites old API plans into already-implemented status, and introduces UpdatePodSandboxResources. Assess G3a/G3b/G3c vs new scope separately. |
| [`be6445f8b7a2`](https://github.com/kubernetes/enhancements/commit/be6445f8b7a20792aeb9da1f10f8bdb2c79e8194) | NEEDS_DIFF | Moves mutable QoS shape proposal out of beta into future enhancements. Consistent with pinned C2a non-goal; temporally important but not automatic 2023 contradiction. |
| [`5388d74bfe6b`](https://github.com/kubernetes/enhancements/commit/5388d74bfe6bd321ddb0584d2d993c2f82a8795d) | NEEDS_DIFF | Clarifies static CPU/memory policy out-of-scope for beta; broadly consistent with pinned C2e non-goal. |
| [`9c2404dcfe49`](https://github.com/kubernetes/enhancements/commit/9c2404dcfe491c7ce9917124a34a4ae5fd346969) | NOT_RELEVANT | Clarifies disabling feature gate during pending resizes. Existing NOT_RELEVANT is reasonable under narrowly construed S0 rationale, though useful operational context. |

## Reviewer questions (copy/paste)

1. Relative to the fixed 2023 S0, should commit d774b5c be considered a scope supersession of C2b, and at what exact hunk/decision unit?
2. For a093b5b, do G3a/G3b represent achieved goals, altered mechanisms, or superseded design commitments? Which relation vocabulary captures the distinction?
3. Should hunk 079aa5fb-F01-H03 include C2b, as its event note says, even if that link remains non-positive/implementation-only?
4. Do hunk 964260d-F01-H07 and H13 use the same operational-consequence and evidence-strength rules as adjacent hunks?
5. Is a discussion of technical alternatives sufficient to label 964260d-F01-H14 WEAKENS, and can a future design sketch count as SUPPORTS?
6. How will interim-2024 supersessions be handled separately from 2023 baseline drift for claims and metrics?

## Evaluation guidance

- **Do not overwrite the reviewer-confirmed freeze.** It should remain the v1 audit reference and current API-development pilot comparator.
- Introduce a new, clearly versioned v2 annotation candidate only after both reviewers resolve flagged questions and new events/diffs. Preserve the prior judgments and recorded justifications.
- Since the v1 data has already been used for system diagnostics and inspected here, subsequent tuning on it is development, not held-out evaluation; arrange independent episodes/repositories for confirmatory claims.
- Report hunk exact-triple F1 alongside event/commit-level sensitivity; 10 of 14 baseline positive triples come from one commit, so raw hunk counts should not be treated as independent evidence.
- Do not use a relation SUPERSEDES by itself as evidence that original design *rationale* was invalid. Some changes reflect beta scoping, completed goals, or intermediates.

## Source and method limitations

- Pinned source: [KEP-1287 README at Git commit 5950905d](https://github.com/kubernetes/enhancements/blob/5950905de89aab2be202d28b823701276cbefea0/keps/sig-node/1287-in-place-update-pod-resources/README.md).
- Four curated original event diffs were examined from the user-provided captured dataset. Five additional commit diffs were fetched from the public GitHub commit records during this audit.
- No empirical Kubernetes runtime, test, PR discussion, or developer intent was independently validated. This report cannot guarantee the scientific truth of disputed relationships.
- The PI reports two human reviewers signed off; the audit does not independently authenticate reviewer identity, and it does not modify their historical records.

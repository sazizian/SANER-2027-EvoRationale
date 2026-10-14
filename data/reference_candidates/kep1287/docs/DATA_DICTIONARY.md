# Data Dictionary

- `element_id`: stable atomic S0 identifier.
- `original_id`: corresponding 2023 12-element draft identifier; `G3` and `C2` are decomposed into member IDs.
- `is_central`: whether the element belongs to the unchanged original six-element required coverage list.
- `screening_label`: human-proposed screening label. `NEEDS_DIFF`/`UNCERTAIN` remain review states.
- `relation_candidate`: reviewer-proposed label. An event-level relation is not automatically baseline rationale drift.
- `temporal_basis`: BASELINE_2023, INTERIM_2024, or BOTH; source of truth for temporal scope.
- `historical_replay_safe`: false for all generated retrospective tool records; Git object immutability alone does not prove real-time auditable availability.
- `first_auditable_at`: when the record was retrieved/audited (2026), kept distinct from source commit timestamp (2024).
- `human_approved`: remains false in delivered S0 files pending documented sign-off.
- `PI_REPORTED_DUAL_HUMAN_REVIEW`: a factual assertion reported by PI, not a cryptographically authenticated reviewer signature.

Commit SHA and hunk SHA-256 are from source capture. A `POTENTIALLY_RELEVANT` commit is not a verified design drift event.

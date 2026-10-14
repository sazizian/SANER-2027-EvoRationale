# How to record final human consensus

The PI reported that both reviewers are human and personally reviewed the consensus judgments. The uploaded spreadsheets still contain historical AI-draft and PENDING annotations.

This file does **not** request re-review from scratch. Ask each reviewer to confirm the exact frozen wording and mapping represented by the candidate reference tables, with a dated confirmation email/message or meeting minutes.

Complete `reference_private/REVIEWER_CONFIRMATION_TEMPLATE.csv` (do not edit original reviewer submissions). Enter `YES` in all five decision-confirmation columns only for items each reviewer genuinely verified. Record a UTC date, a confirmation method such as `email` or `meeting minutes`, and an audit reference linking to that confirmation. Preserve the original records separately.

If one reviewer disputes any candidate item, revise the candidate tables under a new version and obtain confirmation for that new exact version. Never overwrite the original baseline or independent reviews.

Once both confirmations are documented, run `scripts/freeze_reference.py` to generate a separately hashed, explicitly reviewed reference bundle. That script records evidence of declarations; it cannot independently verify human identity or the accuracy of the judgment.

Do not use the resulting freeze artifact as evidence of outcome-level ground truth or historical replay certification.

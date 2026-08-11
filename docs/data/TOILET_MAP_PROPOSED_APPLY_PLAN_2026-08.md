# Toilet Map Proposed Apply Plan - Review 1

> PLAN ONLY. This file describes a future apply policy; it does not implement or invoke one.

- Source checksum: `f6824fdc7cd29df8c1f45ba749c1b28d319fb34803c55459bbe748ef65937624`
- Executable mutation path: `False`
- Counts: `{'would_require_manual_review': 77, 'would_enrich_existing': 48, 'would_create_new': 29, 'would_mark_source_missing': 17, 'would_ignore_out_of_scope': 457, 'would_quarantine': 1}`

## Proposed policy

- **exact_source_id:** Retain source identity as authoritative; do not fuzzy-override it.
- **unknown_to_known_scalar:** Recommend AUTO_ENRICH only for exact-linked scalar fields when Relief is unknown and no stronger provenance exists.
- **conflicts:** KEEP_CURRENT_AND_RECORD_CONFLICT; manual review before any update.
- **coordinates:** Manual review; small movements may be provenance-aware updates, large/extreme movements remain suspicious.
- **names:** Manual review; cosmetic changes are not identity changes, but materially different names are not auto-overwritten.
- **opening_hours:** Day-level manual review; missing source days are unknown, not closed/deleted.
- **new_facilities:** CREATE_NEW only after confirmed identity, in-scope geography, valid identity/name/coordinates, and explicit approval.
- **source_id_churn:** Manual crosswalk review; do not alter facility_sources automatically.
- **absent_upstream:** Manual review/export confirmation; do not delete, unpublish, or mark not-current automatically.
- **inactive_removed:** Future explicit inactive/removed signals may be quarantined or marked source-not-current only under an approved policy; none occur in this snapshot.
- **out_of_scope:** IGNORE_OUT_OF_SCOPE for valid external geography only after a separate product-scope decision.
- **invalid_malformed:** QUARANTINE or manual review; preserve independent valid fields and never invent missing values.
- **quality_warnings:** Warnings are field-specific; authoritative linked records can remain reviewable while warning fields are withheld.

## Provisional precedence

- Order: `['staff_verified_or_community_confirmed', 'existing_relief_value_with_provenance', 'newer_toilet_map_value', 'unverified_toilet_map_value']`
- Required provenance: `['facility_id', 'canonical source name', 'source_record_id', 'source_updated_at', 'field name', 'old value', 'new value', 'decision basis', 'reviewer or approved policy version', 'recorded-at timestamp']`
- Observation: The captured schema does not show a community/staff verification marker, so Toilet Map must not be assumed to outrank future verified evidence.

The JSON artifact contains every proposed entry, including current/proposed values, evidence, confidence, and provenance that a future approved apply would record. Nothing here is applied.

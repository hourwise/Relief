# Toilet Map Apply 2A existing-facility execution evidence

> Production execution committed successfully and passed the bounded postcheck.

- Project: `bgwxrxkmyaihplaloely`
- Preparation commit: `008498bd94cfac1867228d71351184f06d23efda`
- Frozen manifest SHA-256: `38D2CE874955075D0EDE9F431A7D37EC142120D3AD8DFD7577679C9AE19F977`
- Execution time: `2026-08-19T21:12:06.323737Z`
- Outcome: `COMMITTED / POSTCHECK PASSED`

## Applied scope

Exactly 22 `APPLY_SOURCE` operations were applied to 10 existing facilities:

| Field | Operations |
|---|---:|
| `is_gender_neutral` | 9 |
| `requires_radar_key` | 7 |
| `has_baby_changing` | 5 |
| `is_free` | 1 |

All operations were boolean enrichments with exact Toilet Map source identity. Field-level provenance was recorded with the frozen manifest SHA, source checksum, source record ID, and `EXACT_SOURCE_ID` basis.

## Postcheck

The production postcheck confirmed:

- 22 of 22 target facilities matched;
- 22 of 22 applied values matched the frozen manifest;
- 22 of 22 source record IDs and provenance entries matched;
- 22 of 22 policy, manifest, approved-commit, and source-checksum markers matched;
- production totals remained 15,584 facilities, 15,584 facility-source links, 5 import runs, and 0 staging rows.

## Explicit exclusions

No `KEEP_CANONICAL`, `PROTECTED`, or deferred operation was executed. There were no new-facility inserts, deletes, unpublishes, opening-hours, coordinate, name, source-link, import-run, staging, stale, quarantine, or source-omission mutations.

The frozen execution manifest remains unchanged and is still the authoritative record of the 22-operation authorization boundary.

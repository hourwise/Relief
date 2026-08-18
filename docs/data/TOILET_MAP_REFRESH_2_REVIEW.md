# Toilet Map Refresh 2 Review

> **REVIEW ONLY — PROPOSED / NOT AUTHORIZED FOR PRODUCTION EXECUTION**

- Source checksum: `5600358ce06ca5dfdc0060968b26e8c9e05a1cb5c9dbe0455cdf3951f480ad7f`
- Generating commit: `3093583`
- Canonical mutations: `0`

## Operation classes

| Class | Count |
|---|---:|
| `SAFE_CANDIDATE` | 22 |
| `REVIEW_REQUIRED` | 2,830 |
| `PROTECTED` | 0 |
| `QUARANTINED` | 485 |
| `STALE_CANDIDATE` | 20 |

## Review rules

- Explicit source booleans preserve `true`, `false`, and `null`; missing source values do not become false.
- Source/canonical conflicts, omissions, names, coordinates, opening hours, inferred matches and new facilities require human review.
- Stronger community/staff/governed provenance is protected and is never auto-overwritten.
- Missing source records are stale candidates; no deletion or unpublish operation is proposed.

Known bad-name records reviewed: `9`; fresh non-empty bad-name candidates: `24`.
Duplicate/collision candidates: `3`.

The complete deterministic operation set, including before/after values, source evidence, provenance and review flags, is in `TOILET_MAP_APPLY_2_MANIFEST.json`.

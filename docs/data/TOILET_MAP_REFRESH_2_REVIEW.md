# Toilet Map Refresh 2 Review

> **REVIEW ONLY — PROPOSED / NOT AUTHORIZED FOR PRODUCTION EXECUTION**

- Source checksum: `5600358ce06ca5dfdc0060968b26e8c9e05a1cb5c9dbe0455cdf3951f480ad7f`
- Generating commit: `7e090e2`
- Canonical mutations: `0`

## Operation classes

| Class | Count |
|---|---:|
| `SAFE_CANDIDATE` | 22 |
| `REVIEW_REQUIRED` | 152 |
| `REVIEW_DEFERRED` | 2,678 |
| `PROTECTED` | 0 |
| `QUARANTINED` | 485 |
| `STALE_CANDIDATE` | 20 |

## Review rules

- Explicit source booleans preserve `true`, `false`, and `null`; missing source values do not become false.
- Source/canonical conflicts, names, coordinates, opening hours, inferred matches and new facilities remain human-review candidates.
- Source omissions are `REVIEW_DEFERRED`: preserve the canonical value and exclude the omission clear from Apply 2; no safe promotion is claimed.
- Stronger community/staff/governed provenance is protected and is never auto-overwritten.
- Missing source records are stale candidates; no deletion or unpublish operation is proposed.

## Review decomposition

| Reason code | Operations | Apply 2 candidate | Human review | Deterministic resolution |
|---|---:|---:|---:|---|
| `NEW_FACILITY` | 42 | yes | yes | RETAIN_FOR_EXPLICIT_CREATION_APPROVAL |
| `SAFE_BOOLEAN_ENRICHMENT` | 22 | yes | no | PROMOTE_TO_SAFE_CANDIDATE |
| `SOURCE_CANONICAL_CONFLICT` | 100 | yes | yes | RETAIN_FOR_HUMAN_REVIEW |
| `SOURCE_OMISSION` | 2,678 | no | no | EXCLUDE_FROM_APPLY_2_PRESERVE_CANONICAL |
| `SOURCE_VALIDATION` | 485 | no | yes | QUARANTINE_NO_APPLY |
| `STALE_SOURCE_RECORD` | 20 | no | yes | RETAIN_CANONICAL_NO_DELETE |
| `UNSUPPORTED_ENRICHMENT` | 10 | yes | yes | RETAIN_FOR_HUMAN_REVIEW |

Known bad-name records reviewed: `9`; fresh non-empty bad-name candidates: `24`.
Duplicate/collision candidates: `3`.

The complete deterministic operation set, including before/after values, source evidence, provenance and review flags, is in `TOILET_MAP_APPLY_2_MANIFEST.json`.

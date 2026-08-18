# Toilet Map Refresh 2 Reconciliation

> **TOILET MAP REFRESH 2 — RECONCILED / APPLY NOT AUTHORIZED**
> Read-only source refresh, local reconciliation and Apply 2 preparation. No production mutation was authorized or performed.

## Source and baseline

- Official source: [Toilet Map UK](https://www.toiletmap.org.uk/dataset)
- Source-declared version/update: `2026-08-18T01:00:00+00:00`
- Retrieval: `2026-08-18T21:18:35.8681807Z`
- SHA-256: `5600358ce06ca5dfdc0060968b26e8c9e05a1cb5c9dbe0455cdf3951f480ad7f`
- Bytes: `7,874,878`
- Licence: `CC BY 4.0`
- Attribution: Contains data from the Toilet Map © 2025 – CC BY 4.0 (Creative Commons Attribution 4.0 International)
- Accepted baseline: `accepted_source_linked_baseline` with `15,584` source-linked records.

## Reconciliation statistics

| Measure | Count |
|---|---:|
| Source rows received | 16,092 |
| Valid rows | 15,607 |
| Invalid rows | 485 |
| Duplicate source IDs | 0 |
| Unchanged source records | 15,495 |
| Changed source records | 69 |
| New source records | 43 |
| Missing/stale candidates | 20 |
| Exact canonical matches | 15,564 |
| New facility candidates | 42 |
| Proposed canonical field changes | 132 |
| Protected/provenance-conflict operations | 0 |
| Duplicate/collision candidates | 3 |
| Quarantined rows | 485 |
| Bad-name rows | 33 |
| Missing source-name rows | 2,679 |
| Bad-coordinate rows | 485 |
| Review-required operations | 152 |
| Review-deferred operations | 2,678 |
| Apply 2 candidate operations | 174 |
| Manual-review count | 657 |

## Proposed operation classes

| Class | Count |
|---|---:|
| `SAFE_CANDIDATE` | 22 |
| `REVIEW_REQUIRED` | 152 |
| `REVIEW_DEFERRED` | 2,678 |
| `PROTECTED` | 0 |
| `QUARANTINED` | 485 |
| `STALE_CANDIDATE` | 20 |

## Safety findings

- `canonical_mutations = 0` and `production_mutations = 0`.
- Source omissions, including true-to-null and known-hours-to-missing transitions, are `REVIEW_DEFERRED` evidence only; they do not clear canonical values and are excluded from the Apply 2 candidate set.
- Missing source records are `STALE_CANDIDATE`; no delete or unpublish operation is proposed.
- Known unusable-name records reviewed: `9`; newly found bad-name rows: `24`.
- Duplicate/collision candidates: `3`.
- Apply 1A manifest, plan, audit evidence, roles and sealing evidence were read-only inputs and remain immutable.

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

## Production read-only postcheck boundary

- Accepted entering-state counts: `{'facilities': 15584, 'facility_sources': 15584, 'import_runs': 5, 'staging_rows': 0}`.
- Observed facilities: `15,584`.
- Observed facility_sources: `15,584`.
- import_runs visibility: `{'status': 'READ', 'count': 0}`.
- staging visibility: `{'status': 'READ', 'count': 0}`.

Machine-readable reconciliation: `TOILET_MAP_REFRESH_2_RECONCILIATION.md`.
Machine-readable review: `TOILET_MAP_REFRESH_2_REVIEW.md`.

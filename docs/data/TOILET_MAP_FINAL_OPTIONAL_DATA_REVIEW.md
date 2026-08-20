# Relief final optional data review

**Date:** 2026-08-20  
**Repository branch:** `codex/toilet-map-apply-1a-production-deploy`  
**Review basis:** committed Refresh 2 / Apply 2B evidence and read-only production inspection

## Decision

**NO ADDITIONAL PRODUCTION DATA PACKAGE IDENTIFIED — NO APPLY EXECUTED**

This final pre-pause review did not find a separately frozen, exact operation
manifest for another bounded production application. The completed governed
lineage remains:

- national seed;
- Apply 1A;
- Refresh 2 reconciliation;
- Apply 2A — 22 existing-facility boolean enrichments; and
- Apply 2B — 36 new facilities.

No new package is being inferred from the presence of the general Refresh 2
review evidence. In particular, this review does not authorize a broad
source refresh, source-omission clearing, stale-record processing, name
rewriting, collision resolution, or another new-facility insertion batch.

## Read-only production checkpoint

The live project was inspected without mutation:

| Measure | Observed |
|---|---:|
| `public.facilities` | 15,620 |
| `public.facility_sources` | 15,620 |
| `public.import_runs` | 5 |
| `public.toilet_map_import_staging` | 0 |
| Published facilities | 15,620 |
| Current Toilet Map UK source links | 15,620 |
| Mutations in this review | 0 |

## Data-quality finding retained for future review

The Refresh 2 evidence identifies nine already-published records whose names
are two characters or fewer or contain no alphanumeric characters. For all
nine, the fresh Toilet Map name is the same unusable value as the canonical
name. The committed evidence marks each as `safe_deterministic_correction =
false` and `manual_review_required = true`.

The 24 newly observed bad-name source rows remain part of the Refresh 2
quarantine/review boundary. They are not silently converted into canonical
names or insertion candidates.

The safe decision is therefore to preserve the current canonical data and
defer any name correction until a separately approved, source-backed or
human-verified manifest exists.

## Boundary confirmation

This review did not perform:

- facility insert, update, delete, publish, or unpublish;
- `facility_sources`, provenance, import-run, or staging mutation;
- Apply 1A, Apply 2A, or Apply 2B execution;
- processing of source omissions, stale candidates, quarantined rows, or
  deferred new-facility records.

The authoritative source and package artifacts remain under `docs/data/`,
including `TOILET_MAP_REFRESH_2_RECONCILIATION.json`,
`TOILET_MAP_REFRESH_2_REVIEW.json`, and the Apply 2B execution evidence.

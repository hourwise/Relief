# Data Enrichment Foundation

This document records the read-only reconciliation foundation for external facility data. It is deliberately separate from product UI behavior and from the existing live importer.

## Current architecture audit

The existing Relief import schema is sufficient for a dry run and should be reused:

- `facilities` is the canonical facility table. It stores the current product-facing values and a JSONB `field_provenance` column.
- `facility_sources` stores source identity and lifecycle metadata: source name, source record ID, source URL/licence, source update time, first/last seen, current status, import run, and raw source data. Its source-name/source-record-ID uniqueness is the authoritative identity link.
- `import_runs` records existing import execution and row counters, checksum, status, and error information.
- `toilet_map_import_staging` is the existing unlogged staging table for the current Toilet Map import path.
- There is no separate `field_provenance` table in the current migration baseline; provenance is a field on `facilities`.

The existing `tools/facility-import/import_to_supabase.py` remains a live mutation path. It was not invoked here and is not called by the new dry-run command. The new foundation has no database client and no write method.

## Source adapter boundary

`tools/enrichment/pipeline.py` defines a `SourceAdapter` protocol and a source-neutral `NormalizedCandidate` record. A source adapter is responsible only for reading a source snapshot and mapping it into normalized semantics:

```text
source snapshot -> SourceAdapter -> NormalizedCandidate[] -> matcher/reconciler -> report
```

The first adapter is `ToiletMapAdapter` for the official Toilet Map UK CSV. It preserves source-native fields that do not have a safe Relief equivalent in `other_fields`; for example, Toilet Map `children` is not silently converted into Relief `is_family_friendly`, and `attended` is not converted into `has_staff_nearby`.

Known mappings are explicit:

| Normalized field | Relief field | Toilet Map source field |
|---|---|---|
| `name` | `name` | `name` |
| `town` | `town` | `areas` name |
| `latitude` / `longitude` | same | `latitude` / `longitude` |
| `opening_hours` | `open_hours` | `opening_times` |
| `is_free` | `is_free` | `no_payment` |
| `is_accessible` | `is_accessible` | `accessible` |
| `requires_radar_key` | `requires_radar_key` | `radar` |
| `has_baby_changing` | `has_baby_changing` | `baby_change` |
| `is_gender_neutral` | `is_gender_neutral` | `all_gender` |

Blank values remain unknown. The adapter does not invent names, booleans, opening hours, or family/staff semantics. Each candidate also carries the source record ID, source licence/update time, source status, a hash of the raw row, validation errors, and quality warnings.

## Matching and confidence

Matching is deliberately conservative and produces a decision rather than a mutation:

1. An existing `facility_sources` link for the same canonical source and source record ID is `EXACT_SOURCE_ID` and takes precedence over all inferred evidence.
2. Records without an exact link are considered only inside a 250 metre spatial search envelope.
3. `HIGH_CONFIDENCE_MATCH` requires a close normalized-name match within 60 metres, or a very close name match within 150 metres, with a matching or unknown town and no close competitor.
4. Plausible candidates with insufficient score margin are `AMBIGUOUS` and are never automatically selected.
5. Records without a conservative match are `LIKELY_NEW`.
6. Missing identity, unusable/out-of-envelope coordinates, duplicate source IDs without an authoritative link, or missing names are `INVALID_SOURCE_RECORD`.

The decision includes distance, name similarity, town comparison, reasons, and up to three alternatives so a reviewer can reproduce the recommendation. No fuzzy result can override an existing source identity link.

## Field-level reconciliation

For exact and high-confidence matches, each mapped field is classified independently as:

- `same`: values agree or the source did not provide a value and Relief is also unknown;
- `enrichment`: the source supplies a known value where Relief is unknown;
- `conflict`: both sides are known but disagree;
- `omission`: the source is unknown while Relief already has a value.

Partial opening-hours data compares only days explicitly expressed by the source. An absent day is not treated as a false value and does not clear a Relief value. A conflict report is evidence for review, not permission to overwrite the product value. Field provenance updates are intentionally deferred until a separate reconciliation decision is approved.

## Lifecycle and duplicate safety

The dry run reports active, removed, and unknown source statuses. A source record missing from the current snapshot is reported as `previously_linked_absent_upstream`; it is not deleted, unpublished, or marked stale. Removed/inactive records are reported as lifecycle evidence and are not mutated.

Duplicate risk is surfaced for duplicate source IDs and for multiple inferred source records pointing at one Relief facility. There is no automatic deduplication or source-precedence change.

## Read-only command and artifacts

Run from the repository root:

```text
npm run enrichment:toilet-map:dry-run -- \
  --report-json docs/data/TOILET_MAP_RECONCILIATION_YYYY-MM.json \
  --report-markdown docs/data/TOILET_MAP_RECONCILIATION_YYYY-MM.md
```

The command performs only HTTP `GET` requests for paged `facilities` and `facility_sources` snapshots, and local writes for ignored snapshots plus the requested reports. It contains no `POST`, `PATCH`, `DELETE`, migration, deployment, or live-import call. `--offline` reuses local snapshots for repeatable analysis.

The current source registry is `tools/enrichment/source_registry.json`. The official source page, download URL, retrieval timestamp, source-declared update time, licence, input byte count, checksum, record counts, lifecycle counts, match categories, field diffs, and review samples are recorded in the generated JSON and Markdown reports. Raw source data and REST snapshots remain ignored under `tools/facility-enrichment/cache/`; the raw dataset is not committed.

## Current review boundary

This phase covers the official Toilet Map UK source only. TfL, National Rail, council, specialist, and other sources are future adapters. No production inserts/updates/deletes, migrations, UI/filter changes, external contact, EAS build, Play setup, or data enrichment apply step is part of this foundation.

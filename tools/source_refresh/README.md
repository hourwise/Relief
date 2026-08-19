# Source refresh framework

This is a local, review-only preparation layer. It does not import data into
Supabase and does not call the Apply 1A path.

The existing `tools/facility-import/download_toilet_map.py` remains the
source-specific fetch boundary. After a candidate is downloaded and its
source identity/licence are checked, run:

```text
python -m tools.source_refresh.cli --source-id toilet_map_uk --input <candidate.csv> --previous <previous.csv>
```

The command writes a content-addressed raw snapshot and a JSON review report.
It reports new, missing/stale, changed, duplicate, and unchanged source
records, and always reports `canonical_mutations: 0`. Normalization and
deterministic facility matching remain in `tools/enrichment/pipeline.py` and
the existing read-only `dry_run.py`/`review.py` path. Any future bounded apply
must be a separately approved path; this command deliberately has no `--apply`
option.

Every registry entry carries publisher, source URL, licence identifier and
URL, required attribution, parser/normalizer version, and preparation status.
Per-snapshot/per-record evidence carries retrieval time, source version,
checksum, source record identifier, last-seen time, and current/stale status.

## Toilet Map Refresh 2

`refresh2.py` is the bounded current-source reconciliation path. It consumes a
locally preserved official CSV, reconstructs the accepted source-linked
baseline from read-only `facility_sources.raw_data`, and reads current
`facilities`/source links with HTTP GET only. It emits the versioned
`TOILET_MAP_REFRESH_2_*` evidence and `TOILET_MAP_APPLY_2_MANIFEST.json` under
`docs/data/`.

The manifest is always marked `PROPOSED / NOT AUTHORIZED FOR PRODUCTION
EXECUTION`. It has no `--apply` option, does not use the Apply 1A engine, and
reports `canonical_mutations: 0` and `production_mutations: 0`. Missing source
records become `STALE_CANDIDATE`; they are never deleted or unpublished by this
tool. Raw snapshots and live REST snapshots remain under the ignored facility
enrichment cache.

### Refresh 2 review decomposition

Source omissions are classified as `REVIEW_DEFERRED`: the current canonical
value is preserved, the omission clear is excluded from the Apply 2 candidate
set, and an unknown source value is never converted into false certainty.
Exact-source conflicts, new-facility creation, and material opening-hours
enrichment remain `REVIEW_REQUIRED`. Stronger Relief/community/staff/governed
provenance remains `PROTECTED`; malformed, duplicate, and stale records retain
their quarantine/lifecycle boundaries. Each operation records its review reason
code, deterministic resolution, Apply 2 candidate flag, and safety assessment.

### Refresh 2A existing-facility decision package

`apply2a.py` consumes the published Refresh 2 Apply 2 manifest and produces a
separate, read-only decision register for the 132 existing-facility candidate
operations. It does not contact Supabase and has no apply option. The bounded
policy promotes only exact-source explicit boolean enrichments where the
canonical value is unknown and unproven. Existing canonical conflicts are
kept or protected, and material opening-hours enrichments are deferred until
independent current verification is available. The resulting execution
candidate manifest is proposed only; it contains no authorization to mutate
canonical or production data.

The council and TfL entries are templates pending source-specific reuse
verification. The Changing Places Consortium master registry and OSM/ODbL data
are intentionally outside the canonical ingestion path.

### Refresh 2B new-facility review package

`apply2b.py` consumes the published Refresh 2 review evidence and assesses all
42 `NEW_FACILITY` candidates individually. It is read-only and has no apply
option. A candidate is included in the future-insert manifest only when the
frozen public source row has a usable name and coordinate, the production
exact-source preflight found no existing link, and no deterministic collision
evidence was found. Same-name nearby source rows and canonical-neighbour
collisions remain `DEFER_EXTERNAL_VERIFICATION`; placeholder identities are
`QUARANTINE`.

The generated artifacts are `TOILET_MAP_APPLY_2B_NEW_DECISIONS.json`,
`TOILET_MAP_APPLY_2B_NEW_DECISIONS.md`,
`TOILET_MAP_APPLY_2B_NEW_MANIFEST.json`, and
`TOILET_MAP_APPLY_2B_NEW_PLAN.md` under `docs/data/`. The package is marked
`TOILET MAP APPLY 2B — NEW FACILITY PACKAGE PREPARED / EXECUTION NOT
AUTHORIZED`, contains no facility IDs or production write command, and reports
zero canonical, production, source-link, provenance, staging, and import-run
mutations.

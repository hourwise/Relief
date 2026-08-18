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

The council and TfL entries are templates pending source-specific reuse
verification. The Changing Places Consortium master registry and OSM/ODbL data
are intentionally outside the canonical ingestion path.

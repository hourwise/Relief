# RELIEF Local Authority OGL Pilot 2 — Targeted Multi-Council Yield Expansion

**Date:** 2026-08-23
**Classification:** `PRODUCTION_READ_ONLY`
**Principal result:** `OGL_COMBINED_POOL_READY_FOR_REVIEW_AND_APPLY`

## Scope and result

Pilot 2 reused the Pilot 1 adapter and inspected four retained, directly licensed local-authority resources. Eleven additional council datasets were triaged and rejected quickly because a current machine-readable resource, normal retrieval, or the actual resource licence was not proven. No canonical production write was attempted.

The combined strict pool is **89** (80 new Pilot 2 candidates plus the nine carried-forward Pilot 1 candidates, less 0 cross-source duplicates). The bounded review pool is **7**.

## Starting and production state

- Repository: `hourwise/Relief`
- Branch: `codex/toilet-map-apply-1a-production-deploy`
- Starting local SHA and independently verified remote SHA: `513772892265e0d80619813b58e7944739d57a21`.
- Pilot 1 foundation commit: `8f239f15c79340f008a4cc265a3e523b58b6791f`
- Read-only production snapshot rows: `15620` facilities; expected accompanying counts are `15634` facility_sources, `14` observations, `0` toilet_units.
- Production project: `Relief` (`bgwxrxkmyaihplaloely`).
- Total production mutations: `0`.

The uncommitted `.easignore`, `app.json`, `docs/EAS_CONFIG_AUDIT.md`, N4/N5/N6 evidence, and sealed migration work were preserved outside the Pilot 1 and Pilot 2 staging sets.

## Source results

| Council/source | Raw rows | Unique physical toilets | Likely existing | Strict new | Review new | Enrichment | Licence | TLS |
|---|---:|---:|---:|---:|---:|---:|---|---|
| Adur District Council — Adur public toilets | 15 | 15 | 0 | 15 | 0 | 0 | Open Government Licence v3.0 | NORMAL_TLS_VERIFIED |
| Belfast City Council — Public toilets | 14 | 14 | 12 | 0 | 2 | 12 | Open Government Licence v3.0 | NORMAL_TLS_VERIFIED |
| Perth & Kinross Council — Public Toilets and Comfort Schemes (open data) | 42 | 41 | 0 | 41 | 0 | 0 | UK Open Government Licence v3.0; original content CC-BY-SA 4.0 | NORMAL_TLS_VERIFIED |
| Worthing Borough Council — Worthing public toilets | 58 | 27 | 0 | 24 | 3 | 0 | Open Government Licence v3.0 | NORMAL_TLS_VERIFIED |

Adur and Worthing exports use stable UPRNs and OSGB36 coordinates converted deterministically to WGS84. Worthing’s 58 raw rows reduced to 27 physical candidates after same-site internal deduplication. Perth’s GeoJSON uses British National Grid geometry and includes explicit public-toilet and comfort-scheme records; Belfast has stable derived IDs from name/address/coordinates and is retained for overlap, review, and enrichment analysis.

### Rejected datasets

| Council/source | Licence | Access/format | Decision |
|---|---|---|---|
| Northumberland County Council — Public Toilets Northumberland | Open Government Licence | Resource returned an HTML page rather than the advertised CSV during normal retrieval. | MACHINE_READABLE_RESOURCE_NOT_VERIFIED |
| Peterborough City Council — Peterborough City Council public toilets | Open Government Licence | Catalogue and resource checked; no current machine-readable payload retrieved. | RESOURCE_NOT_RETRIEVED |
| Manchester City Council — Public toilets in Manchester | Open Government Licence | Resource redirected to the open-data landing page, without a stable payload in this pass. | RESOURCE_NOT_FROZEN |
| Bournemouth Borough Council — Public toilets Bournemouth | Open Government Licence | Certificate validation failed against the resource host; no audit snapshot retained. | TLS_RETRIEVAL_NOT_PRODUCTION_VERIFIED |
| Colchester Borough Council — Public toilets CBC | Open Government Licence | Catalogue reviewed; no current resource URL was frozen for this bounded pass. | RESOURCE_NOT_FROZEN |
| Surrey Heath Borough Council — Surrey Heath Borough Council public conveniences | Open Government Licence | Catalogue states availability not released. | NOT_RELEASED |
| West Oxfordshire District Council — Public conveniences in West Oxfordshire | Open Government Licence | Advertised resource returned 404 during the bounded retrieval check. | RESOURCE_NOT_FOUND |
| Herefordshire Council — Community Toilets | Ordnance Survey Open Data licence | Documented service route did not return a stable payload in this pass. | SERVICE_ROUTE_NOT_VERIFIED |
| Salford City Council — SCC public toilets | Open Government Licence | Resource host connection failed during the bounded check. | RESOURCE_NOT_RETRIEVED |
| St Helens Council — Public toilets St Helens Council CSV | Open Government Licence | Current catalogue page has no released data link. | NOT_RELEASED |
| Newcastle City Council — Public toilet | LICENCE_NOT_PROVEN | Catalogue has no usable data link and reports no dataset licence. | LICENCE_NOT_PROVEN |

## Pilot 1 + Pilot 2 reconciliation

- `PILOT_1_STRICT: 9`
- `PILOT_1_REVIEW: 2`
- `PILOT_2_STRICT: 80`
- `PILOT_2_REVIEW: 5`
- `CROSS_SOURCE_DUPLICATES: 0`
- `COMBINED_CONSERVATIVE_NET_NEW: 89`
- `COMBINED_REVIEW_POOL: 7`

The nine Pilot 1 strict candidates and two near-overlap cases remain unchanged. The Pilot 2 candidate register contains the full carry-forward and additional strict/review pool with deterministic candidate IDs, source IDs, coordinates, nearest facility evidence, licensing, and TLS readiness.

## Projected facility count and target progress

- `CURRENT: 15620`
- `STRICT POST-APPLY POTENTIAL: 15709`
- `REVIEW-ASSISTED POTENTIAL: 15716`

| Target | Additional toilets required | Strict pool progress |
|---:|---:|---:|
| 16,000 | 380 | 89 |
| 17,000 | 1380 | 89 |
| 20,000 | 4380 | 89 |

Review candidates are not guaranteed additions. The recommended next action is one bounded human review followed by a separately authorized production apply, including normal-TLS re-fetch and frozen source hashes.

## Source ranking

| Rank | Council/source | Unique toilets | Likely existing | Strict net-new | Review net-new | Licence | Data quality | Yield rate |
|---:|---|---:|---:|---:|---:|---|---|---:|
| 1 | Perth & Kinross Council | 41 | 0 | 41 | 0 | UK Open Government Licence v3.0; original content CC-BY-SA 4.0 | ROWS_WITH_STABLE_ID=42; ROWS_WITH_VALID_COORDINATES=42; DUPLICATE_COORDINATE_CLUSTERS=1 | 100.0% |
| 2 | Worthing Borough Council | 27 | 0 | 24 | 3 | Open Government Licence v3.0 | ROWS_WITH_STABLE_ID=58; ROWS_WITH_VALID_COORDINATES=58; DUPLICATE_COORDINATE_CLUSTERS=40 | 88.9% |
| 3 | Adur District Council | 15 | 0 | 15 | 0 | Open Government Licence v3.0 | ROWS_WITH_STABLE_ID=15; ROWS_WITH_VALID_COORDINATES=15; DUPLICATE_COORDINATE_CLUSTERS=0 | 100.0% |
| 4 | Causeway Coast and Glens Borough Council / OpenDataNI | 52 | 46 | 5 | 1 | Open Government Licence v3.0 | verified Pilot 1 normalized records | 9.6% |
| 5 | City of York Council | 18 | 13 | 4 | 1 | Open Government Licence v3.0 | verified Pilot 1 normalized records | 22.2% |
| 6 | Belfast City Council | 14 | 12 | 0 | 2 | Open Government Licence v3.0 | ROWS_WITH_STABLE_ID=14; ROWS_WITH_VALID_COORDINATES=14; DUPLICATE_COORDINATE_CLUSTERS=0 | 0.0% |

## TLS and retrieval

The four Pilot 2 candidate-source resources were each retrieved with normal certificate validation and are marked `NORMAL_TLS_VERIFIED`. Pilot 1’s two official ArcGIS resources remain marked `TLS_RETRIEVAL_NOT_PRODUCTION_VERIFIED` because its evidence was captured through a disposable verification-disabled fallback after normal validation failed. No TLS bypass is present in the adapter’s normal path, and no TLS-caveated source is production-ingestion-ready.

## Schema and production safety

The current facilities/provenance schema remains sufficient for a later bounded apply: this batch only needs the existing facility identity, source provenance, and facility-source observation structures. No migration, trigger, index, RLS, RPC, source graph, import run, or promotion service was added.

- `TOTAL PRODUCTION MUTATIONS: 0`
- `TOTAL CANONICAL FACILITY INSERTS: 0`
- `TOTAL CANONICAL FACILITY UPDATES: 0`
- `TOTAL SCHEMA MUTATIONS: 0`
- `TOTAL AUTH MUTATIONS: 0`

## Files and tests

The intended Pilot 2 files are the existing adapter extension, its focused tests, the bounded audit runner, six compact evidence files under `docs/data/`, and no raw downloads.

- Pilot 1/Pilot 2 adapter tests: **10 passed**.
- Package-qualified relevant source-expansion regression modules (pipeline, TfL, N1–N5): **97 passed**.
- N6A/N6B/N6C baseline check: **18 run; one existing N6B fixture failure and one dependent N6C setup error** because the protected N6B proposed cohort contains 44 rather than the test’s expected 51 cases. No N6 files were changed.
- Deterministic replay: **all six evidence-file hashes matched** a clean temporary replay.
- JSON parsing, Python compilation, bounded secret scan, and source-internal/cross-source reconciliation: **passed**.
- `git diff --check`: **no new Pilot 2 whitespace errors**; the separately committed Pilot 1 Markdown report retains its intentional two-space hard-break warning.

**Next action:** `LOCAL AUTHORITY OGL BOUNDED REVIEW + PRODUCTION APPLY`.

The production apply remains separately unauthorized in this pilot.

# RELIEF TfL Existing-Parent Source-Observation Audit ? 2026-08-22

**Classification:** `RELIEF TFL EXISTING-PARENT SOURCE-OBSERVATION AUDIT — ADDITIVE SOURCE-OBSERVATION MODEL REQUIRED / PROMOTION NOT AUTHORIZED`

**PROPOSED / PRODUCTION PROMOTION NOT AUTHORIZED**

## Executive summary

This bounded audit uses only the committed, frozen TfL reconciliation evidence. It does not redownload or refresh the ZIP, conduct fresh web research, deploy schema, or promote TfL records. The previous ?28-row? count is reproducibly 28 operation entries?14 `SOURCE_LINK` plus 14 `ENRICHMENT` entries?over the same 14 immutable TfL source identities. The distinction is preserved rather than manufacturing 28 observations.

- Starting SHA: `f8bd1bcaeb137f8858d9023bd9983454f6912b17`
- Repository: `hourwise/Relief`
- Branch: `codex/toilet-map-apply-1a-production-deploy`
- Protected working-tree files remain untouched: `.easignore`, `app.json`, `docs/EAS_CONFIG_AUDIT.md`
- Production mutations: `0`

## Source integrity

- TfL ZIP URL: https://api.tfl.gov.uk/stationdata/tfl-stationdata-detailed.zip
- ZIP SHA-256: `19c50772febd1a3d7625f59e079b7590c5da4ed70424d6f552cfd7db1611e2ce`
- ZIP size: `186973` bytes
- Retrieval UTC: `2026-08-21T06:08:20.1476469Z`
- Frozen reconciliation SHA-256: `65cc9cc8c41b7b3a003524610b674c7f2eae96ff7fe5116f38f2d2856cb777cb`
- Frozen reconciliation path: `tools/source_expansion/cache/tfl-detailed-2026-08-21/tfl-reconciliation.json`
- Attribution retained: `Data provided by Transport for London`
- Frozen input was not refreshed, replaced, normalized, or redownloaded.

## Cohort reproduction

| Measure | Result |
|---|---:|
| Frozen operation entries | 28 |
| `SOURCE_LINK` entries | 14 |
| `ENRICHMENT` entries | 14 |
| Unique TfL source rows | 14 |
| Station groups | 14 |
| Existing canonical facility groups | 14 |
| Batch 1 contamination | 0 |
| New-parent contamination | 0 |

No source identity is dropped, duplicated, changed, gender-collapsed, ID-collapsed, or row-count-collapsed. The cohort accounting discrepancy is deterministic and is retained in the machine-readable package.

## Current model audit

- `facilities` represents the canonical discoverable parent/place. Its accessibility, baby-changing, gender-neutral, fee, opening and provenance fields are parent-level and cannot safely represent conflicting source-row attributes without semantic overwrite.
- `facility_sources` is strongly attached to a facility and has source identity uniqueness, but its existing public SELECT contract exposes `raw_data`; it is not an explicit source-observation object and is not a safe private structured provenance boundary.
- `toilet_units` represents an explicitly asserted physical child unit. Its zero-row meaning is ?unit detail unknown?, not ?exactly one unit?. It must not be overloaded for a TfL source row.
- `toilet_unit_sources` requires a toilet-unit foreign key and is private under the deployed security contract, so it cannot represent an unlinked observation without changing its meaning.
- Existing app/query contracts use canonical facilities for map/search/nearest/detail and published toilet units for child detail. No source-observation read path exists.

Current model classification: **`SOURCE_OBSERVATION_MODEL_REQUIRED`**. The current schema can retain opaque evidence, but it cannot preserve structured TfL observation attributes safely without either exposing privileged provenance or overwriting canonical parent values.

## Source-observation finding

A source observation is a distinct semantic object: ?TfL published these toilet-provision attributes for this already-known facility? without asserting a physical room/unit. The smallest safe additive design is a private `facility_source_observations` table with a strong foreign key to `facility_sources`, immutable observation identity, structured attributes, station-level coordinate precision, and an optional later human-adjudicated link to `toilet_units`. No polymorphic foreign key is proposed.

### Proposed additive model (design only)

- Table: `facility_source_observations` ? **DESIGN ONLY / NOT DEPLOYED**.
- Strong `facility_source_id` FK; unique `(facility_source_id, observation_key)`.
- `observed_attributes jsonb` preserves source-specific fields without rewriting canonical parent fields.
- `physical_unit_asserted=false` requires no `toilet_unit_id` and `unit_link_status=UNLINKED`.
- Optional `toilet_unit_id` FK is used only after independent human adjudication; the immutable observation and source identity remain.
- Station coordinates remain explicitly `STATION_LEVEL_ONLY` and are not copied into unit precision.
- RLS enabled; no anon/authenticated SELECT or write grant by default; governed importer/service role only. A later public projection, if needed, must be reviewed separately.

## Row classification

| TfL source identity | Station | Existing parent | Outcome | Physical unit asserted |
|---|---|---|---|---|
| `tfl:910GBARKRIV:toilet:1` | Barking Riverside | Barking Riverside Station, WITHIN BARRIER | `REQUIRES_ADDITIVE_SOURCE_OBSERVATION_MODEL` | `false` |
| `tfl:910GGODMAYS:toilet:1` | Goodmayes | Tesco Extra Romford Goodmayes | `REQUIRES_ADDITIVE_SOURCE_OBSERVATION_MODEL` | `false` |
| `tfl:910GHANWELL:toilet:1` | Hanwell | Hanwell Rail Station | `REQUIRES_ADDITIVE_SOURCE_OBSERVATION_MODEL` | `false` |
| `tfl:910GMANRPK:toilet:1` | Manor Park | Manor Park Library | `REQUIRES_ADDITIVE_SOURCE_OBSERVATION_MODEL` | `false` |
| `tfl:910GSVNKNGS:toilet:1` | Seven Kings | Seven Kings | `REQUIRES_ADDITIVE_SOURCE_OBSERVATION_MODEL` | `false` |
| `tfl:940GZZBPSUST:toilet:1` | Battersea Power Station | Battersea Power Station (Tube Station) | `REQUIRES_ADDITIVE_SOURCE_OBSERVATION_MODEL` | `false` |
| `tfl:940GZZLUFYC:toilet:3` | Finchley Central | Finchley Central Station | `REQUIRES_ADDITIVE_SOURCE_OBSERVATION_MODEL` | `false` |
| `tfl:940GZZLURSG:toilet:1` | Ruislip Gardens | Ruislip Gardens Underground Station | `REQUIRES_ADDITIVE_SOURCE_OBSERVATION_MODEL` | `false` |
| `tfl:HUBBAN:toilet:1` | Bank | The Bank of England Museum | `REQUIRES_ADDITIVE_SOURCE_OBSERVATION_MODEL` | `false` |
| `tfl:HUBELM:toilet:1` | Elmers End | Elmers End Station | `REQUIRES_ADDITIVE_SOURCE_OBSERVATION_MODEL` | `false` |
| `tfl:HUBMJT:toilet:1` | Mitcham Junction | Mitcham Junction Station | `REQUIRES_ADDITIVE_SOURCE_OBSERVATION_MODEL` | `false` |
| `tfl:HUBSRU:toilet:1` | South Ruislip | Sainsbury's South Ruislip | `REQUIRES_ADDITIVE_SOURCE_OBSERVATION_MODEL` | `false` |
| `tfl:HUBTCR:toilet:1` | Tottenham Court Road | Tottenham Court Road Underground Station | `REQUIRES_ADDITIVE_SOURCE_OBSERVATION_MODEL` | `false` |
| `tfl:HUBZWL:toilet:1` | Whitechapel | Idea Store Whitechapel | `REQUIRES_ADDITIVE_SOURCE_OBSERVATION_MODEL` | `false` |

All 14 rows are `REQUIRES_ADDITIVE_SOURCE_OBSERVATION_MODEL`. No row is a physical-unit approval, no source row is invalid, and no current parent canonical field is approved for enrichment.

### Proven versus not proven

Proven by the frozen source/reconciliation: TfL station identity; stable `(StationUniqueId, Id)` row identity; supplied type/accessibility/baby-changing/gateline/fee/management/location attributes; station-level coordinates; and a deterministic existing-parent candidate. Not proven: physical unit identity/count/topology, whether another row is the same room, entrance-level placement, or toilet-specific coordinates.

## Physical-unit safety

- Physical units created: `0`.
- Physical-unit mappings inferred: `0`.
- Toilet-specific coordinates inferred: `0`.
- No unit is inferred from gender, accessibility, baby changing, fee, opening, row order, source ID, location text, multiple rows, or station coordinates.

## Proposed future operations

The package is declarative only and contains no SQL, Supabase mutation client, RPC invocation, staging path, import-run path, or automatic apply logic.

| Operation | Count |
|---|---:|
| Facility inserts | 0 |
| TfL facility-source links | 14 |
| Source-observation inserts | 14 |
| Canonical facility enrichments | 0 |
| Toilet-unit inserts | 0 |
| Toilet-unit source links | 0 |

Each proposed observation operation identifies the TfL source identity, canonical facility, evidence paths, limitations, and `physical_unit_asserted=false`. Anything unresolved would produce zero operations; the current model gap means all 14 are deferred to a future governed transaction after the additive model exists.

## Security and production safety

- Existing production checkpoint was verified read-only: facilities `15,620`; facility_sources `15,620`; import_runs `5`; toilet_map_import_staging `0`; toilet_units `0`; toilet_unit_sources `0`.
- `toilet_units` RLS is enabled.
- `toilet_unit_sources` RLS is enabled and has no public/anon/authenticated SELECT policy in the observed posture.
- Production mutations: `0`.
- Staging rows created: `0`.
- Import runs created: `0`.
- Migrations applied to production: `0`.
- TfL records promoted: `0`.
- Apply RPC calls: `0`.

## Remaining blockers

1. The repository has no source-observation table/contract; adding it requires a separately reviewed additive migration and security review.
2. The frozen 14 parent matches include source-vs-canonical attribute differences; they must remain observations, not parent enrichments, until a governed policy decides how to expose them.
3. The 14 source identities are operation-overlap evidence, not 28 distinct physical units. Physical topology remains unresolved for every row.
4. Public UI/search behavior for source observations requires a future explicit product contract; this transaction does not modify UI.

## Validation

- `python -m py_compile tools/source_expansion/tfl_existing_parent_observation_audit.py tools/source_expansion/test_pipeline.py`: PASS.
- `PYTHONPATH=... python -m unittest tools.source_expansion.test_pipeline`: PASS, 24 tests.
- JSON parse and audit invariant validation: PASS.
- `npm.cmd --prefix D:\Users\fleur\Nicola App\relief-app run typecheck`: PASS.
- Direct `node tools/run-tests.mjs` with temporary output redirected to a D: workspace directory: PASS, all 23 test files.
- `git diff --check`: PASS.
- Bounded secret-pattern scan on intended files: PASS, no matches.
- Read-only production verification: PASS; expected counts unchanged and no mutation path invoked.
- No EAS, Gradle, Expo prebuild, Android, APK, migration, or deployment tooling was run.

## Files

- `tools/source_expansion/tfl_existing_parent_observation_audit.py`
- `tools/source_expansion/test_pipeline.py`
- `docs/data/RELIEF_TFL_EXISTING_PARENT_SOURCE_OBSERVATION_AUDIT_2026-08-22.json`
- `docs/data/RELIEF_TFL_EXISTING_PARENT_SOURCE_OBSERVATION_AUDIT_2026-08-22.md`

## Final state

`RELIEF TFL EXISTING-PARENT SOURCE-OBSERVATION AUDIT — ADDITIVE SOURCE-OBSERVATION MODEL REQUIRED / PROMOTION NOT AUTHORIZED`

TfL promotion to production was not authorized or executed by this transaction.

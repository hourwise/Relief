# RELIEF TfL Physical-Unit Semantics & Adjudication Batch 2

**Final classification:** RELIEF TFL PHYSICAL-UNIT SEMANTICS — SOURCE DOES NOT SUPPORT SAFE UNIT PROMOTION

## Starting state

- Repository: `hourwise/Relief`
- Branch: `codex/toilet-map-apply-1a-production-deploy`
- This report is generated from the published `da0111a9334d15812e2c2b39307184888789c5ab` checkpoint.
- Protected working-tree files were preserved untouched: `.easignore`, `app.json`, `docs/EAS_CONFIG_AUDIT.md`.

## Source integrity

- ZIP SHA-256: `19c50772febd1a3d7625f59e079b7590c5da4ed70424d6f552cfd7db1611e2ce`
- ZIP size: `186973` bytes
- Retrieval UTC: `2026-08-21T06:08:20.1476469Z`
- Reconciliation SHA-256: `65cc9cc8c41b7b3a003524610b674c7f2eae96ff7fe5116f38f2d2856cb777cb`
- Attribution: `Data provided by Transport for London`
- Frozen input was verified locally and was not refreshed, replaced, or redownloaded.

## Whole-source semantics

- Stations in frozen `Stations.csv`: **509**
- Toilet rows examined: **410**
- Stations represented by toilet rows: **179**
- Stations with multiple rows: **4**
- Rows-per-station distribution: `{"1": 32, "2": 68, "3": 76, "4": 2, "6": 1}`
- Representative 1/2/3/4+ row examples: `{"1": {"source_record_ids": ["tfl:910GACTONML:toilet:1"], "station_id": "910GACTONML"}, "2": {"source_record_ids": ["tfl:940GZZLUALP:toilet:1", "tfl:940GZZLUALP:toilet:2"], "station_id": "940GZZLUALP"}, "3": {"source_record_ids": ["tfl:910GBHILLPK:toilet:1", "tfl:910GBHILLPK:toilet:2", "tfl:910GBHILLPK:toilet:3"], "station_id": "910GBHILLPK"}, "4": {"source_record_ids": ["tfl:HUBSRA:toilet:1", "tfl:HUBSRA:toilet:2", "tfl:HUBSRA:toilet:3", "tfl:HUBSRA:toilet:4"], "station_id": "HUBSRA"}, "6": {"source_record_ids": ["tfl:HUBVIC:toilet:1", "tfl:HUBVIC:toilet:2", "tfl:HUBVIC:toilet:3", "tfl:HUBVIC:toilet:4", "tfl:HUBVIC:toilet:5", "tfl:HUBVIC:toilet:6"], "station_id": "HUBVIC"}}`
- Unique `(StationUniqueId, Id)` identities: **410**; duplicate identities: **0**.
- Frozen `FeedInfo.csv` identifies Transport for London and the feed date but does not define `Id` as a physical-room identifier.
- Exact material-attribute duplicate candidate groups: **0**; extra candidate rows: **0**.
- Repeated same-gender groups within stations: **6**.
- Potential duplicate-identity exposure in multi-row groups: **378 rows**; same-location multi-row groups: **115**.
- Gender distribution: `{"FEMALE": 147, "MALE": 147, "UNISEX": 116}`.
- Accessibility distribution: `{"FALSE": 291, "TRUE": 119}`; baby-changing distribution: `{"FALSE": 330, "TRUE": 80}`.
- Fee distribution: `{"FALSE": 397, "TRUE": 13}`.
- TfL row IDs are publisher source identity components, not proof of separate physical rooms. Row position is transient.
- The feed exposes station-level coordinates through `StationPoints.csv`; it has no toilet-specific coordinate field.
- Gender, accessibility, baby-changing, fee, opening/access, gateline, and management values are source attributes. None is independently sufficient to establish physical topology.

## Physical-unit interpretation

A TfL row is best treated as a **station toilet-provision observation**: it preserves what TfL publishes for a station/row identity and its attributes. The frozen feed does not document that `Id` is a room identifier, does not provide toilet-level coordinates, and does not distinguish whether multiple rows are separate rooms, a shared block, or overlapping attribute views. The classifier therefore fails closed.

Accessibility and baby-changing are not promoted to extra units. Male/Female/Unisex differences are not automatically collapsed or promoted. Different source IDs and row counts are not physical proof.

## Batch 2 adjudication

- `PHYSICAL_UNIT_PROMOTION_READY`: **0**
- `OBSERVATION_ONLY`: **14**
- `HUMAN_ADJUDICATION_REQUIRED`: **0**
- Confidence: `{"MEDIUM": 14}`
- Reason codes: `{"ROW_SEMANTICS_AMBIGUOUS": 14}`

No row is promotion-ready. Single-row station cases remain observation-only because the source does not establish a physical-room identity. Multi-row station cases require human topology adjudication.

## Row decisions

| Source identity | Station | Rows at station | Classification | Confidence | Reason |
|---|---|---:|---|---|---|
| `tfl:910GBARKRIV:toilet:1` | Barking Riverside | 1 | `OBSERVATION_ONLY` | `MEDIUM` | `ROW_SEMANTICS_AMBIGUOUS` |
| `tfl:910GGODMAYS:toilet:1` | Goodmayes | 1 | `OBSERVATION_ONLY` | `MEDIUM` | `ROW_SEMANTICS_AMBIGUOUS` |
| `tfl:910GHANWELL:toilet:1` | Hanwell | 1 | `OBSERVATION_ONLY` | `MEDIUM` | `ROW_SEMANTICS_AMBIGUOUS` |
| `tfl:910GMANRPK:toilet:1` | Manor Park | 1 | `OBSERVATION_ONLY` | `MEDIUM` | `ROW_SEMANTICS_AMBIGUOUS` |
| `tfl:910GSVNKNGS:toilet:1` | Seven Kings | 1 | `OBSERVATION_ONLY` | `MEDIUM` | `ROW_SEMANTICS_AMBIGUOUS` |
| `tfl:940GZZBPSUST:toilet:1` | Battersea Power Station | 1 | `OBSERVATION_ONLY` | `MEDIUM` | `ROW_SEMANTICS_AMBIGUOUS` |
| `tfl:940GZZLUFYC:toilet:3` | Finchley Central | 1 | `OBSERVATION_ONLY` | `MEDIUM` | `ROW_SEMANTICS_AMBIGUOUS` |
| `tfl:940GZZLURSG:toilet:1` | Ruislip Gardens | 1 | `OBSERVATION_ONLY` | `MEDIUM` | `ROW_SEMANTICS_AMBIGUOUS` |
| `tfl:HUBBAN:toilet:1` | Bank | 1 | `OBSERVATION_ONLY` | `MEDIUM` | `ROW_SEMANTICS_AMBIGUOUS` |
| `tfl:HUBELM:toilet:1` | Elmers End | 1 | `OBSERVATION_ONLY` | `MEDIUM` | `ROW_SEMANTICS_AMBIGUOUS` |
| `tfl:HUBMJT:toilet:1` | Mitcham Junction | 1 | `OBSERVATION_ONLY` | `MEDIUM` | `ROW_SEMANTICS_AMBIGUOUS` |
| `tfl:HUBSRU:toilet:1` | South Ruislip | 1 | `OBSERVATION_ONLY` | `MEDIUM` | `ROW_SEMANTICS_AMBIGUOUS` |
| `tfl:HUBTCR:toilet:1` | Tottenham Court Road | 1 | `OBSERVATION_ONLY` | `MEDIUM` | `ROW_SEMANTICS_AMBIGUOUS` |
| `tfl:HUBZWL:toilet:1` | Whitechapel | 1 | `OBSERVATION_ONLY` | `MEDIUM` | `ROW_SEMANTICS_AMBIGUOUS` |

## Schema readiness

`SCHEMA_READY`. The deployed additive model supports multiple units per facility, unlinked source observations, strong provenance relationships, station-level coordinate scope, deterministic observation identity, and future governed observation-to-unit linking. No schema change is required for this unresolved batch.

## Future promotion contract (proposal only)

A future promotion must require independent authoritative evidence of a distinct physical location, a verified parent, an explicit row-to-unit mapping, and conflict-free attributes. It must create a deterministic unit identity under the parent, preserve the original `facility_source_observations` row and provenance, keep station coordinates at station scope, and run atomically with idempotency and pre/post invariant checks. Conflicts fail closed. This batch emits no executable promotion path.

## Pilot recommendation

**NO PHYSICAL-UNIT PILOT RECOMMENDED.** The frozen source alone does not produce a high-confidence, independently distinguishable toilet unit for this batch.

## Production verification

Read-only production verification confirmed no changes:

| Table | Before | After | Delta |
|---|---:|---:|---:|
| `facilities` | 15620 | 15620 | 0 |
| `facility_sources` | 15634 | 15634 | 0 |
| `import_runs` | 5 | 5 | 0 |
| `toilet_map_import_staging` | 0 | 0 | 0 |
| `toilet_units` | 0 | 0 | 0 |
| `toilet_unit_sources` | 0 | 0 | 0 |
| `facility_source_observations` | 14 | 14 | 0 |

**TOTAL PRODUCTION MUTATIONS: 0**

Toilet units created: `0`; toilet-unit source links created: `0`; observations changed: `0`; canonical facilities changed: `0`.

## Security

RLS, grants, anonymous access, authenticated access, public API exposure, and service-role boundaries were verified unchanged. Raw source observations remain governed provenance and are not exposed publicly.

## Validation

- Frozen ZIP/reconciliation hash verification: passed.
- Deterministic Batch 2 classifier and JSON invariant validation: passed.
- Focused semantic tests: 7 passed; existing TfL/source-expansion tests: 29 passed; combined: 36 passed.
- Python compilation: passed.
- TypeScript typecheck: passed.
- Lightweight repository test runner: 24 test files passed.
- `git diff --check`: passed.
- Bounded secret-pattern scan: passed.
- Read-only production verification: passed; counts and all 14 observation physical states unchanged.
- Read-only provenance check recorded a pre-existing source-name encoding discrepancy: all 14 production TfL source links contain `U+FFFD` instead of the registry em dash. No repair was authorized or executed.
- No EAS, Expo prebuild, Gradle, Android, APK, or emulator tooling was run.

## Safety declaration

This batch is read-only with respect to production. It does not create units, link observations, modify canonical facilities, refresh TfL, or authorize promotion.

# RELIEF N5-R2 — Exact Frozen National NaPTAN Source Graph Ingestion

## STARTING STATE

- Repository: `hourwise/Relief`
- Branch: `codex/toilet-map-apply-1a-production-deploy`
- Starting local SHA: `f14f38651805070455150992b4cddb5529a53749`
- Starting remote SHA: `f14f38651805070455150992b4cddb5529a53749`
- Remote verification: `git fetch origin` succeeded and `git ls-remote origin refs/heads/codex/toilet-map-apply-1a-production-deploy` matched the required SHA.
- Migration chain preflight before and after ingestion: `Remote database is up to date.`
- Starting source-graph rows: all five N4A tables were empty.
- Starting Relief baseline: facilities 15,620; facility_sources 15,634; facility_source_observations 14; import_runs 5; toilet_map_import_staging 0; toilet_units 0; toilet_unit_sources 0.

Protected files remained untouched, unstaged, and uncommitted throughout: `.easignore`, `app.json`, and `docs/EAS_CONFIG_AUDIT.md`. Existing N4C/R1 evidence and tooling were preserved.

## SEALED N4A

- Migration: `supabase/migrations/20260822170000_naptan_transport_source_graph.sql`
- Required SHA-256: `087A389B8CEAC021B12708BC55C39022CB38D5459510EFFB6CF057CEF232C44E`
- Hash at start, before DML, after DML, before commit, and final: exact match.
- No migration, schema, policy, grant, trigger, function, or migration-ledger change was made by N5-R2.

## PRODUCTION PROJECT

- Project: `Relief`
- Supabase ref: `bgwxrxkmyaihplaloely`
- Health: `ACTIVE_HEALTHY`
- Region: `eu-central-1`
- Database runtime: PostgreSQL 17.6; PostGIS 3.3.7; pgcrypto 1.3.
- No production project ref other than the exact Relief ref was used.

## FROZEN SOURCE

- Publisher: UK Department for Transport.
- Product: National NaPTAN XML access-node / StopArea dataset.
- URL: `https://naptan.api.dft.gov.uk/v1/access-nodes?dataFormat=xml`
- Disposable cache: `C:\Temp\relief-n5\NaPTAN.xml`.
- Size: 578,991,782 bytes.
- SHA-256: `6FC7E40E2AF3B30E9FD117BDAC313B58F3385BFF26517FD78D5554DA12B4183A` — exact.
- Governed retrieval UTC: `2026-08-22T14:48:39.4826193Z`.
- Encoding: UTF-8 XML.
- Licence: Open Government Licence v3.0.
- Attribution: `Contains public sector information licensed under the Open Government Licence v3.0.`
- Raw XML was not committed, staged, copied into evidence, or uploaded.

## CORRECTED CONTRACT

The committed `N5-R1-2026-08-23` contract was parsed and enforced. The superseded `169,524` stored-membership expectation was not used.

| Measure | Required and reproduced |
|---|---:|
| Source snapshots | 1 |
| StopArea/place rows | 97,270 |
| StopPoint/node rows | 436,428 |
| Raw publisher membership elements | 169,530 |
| Unique membership keys | 169,527 |
| Stored membership rows | 169,527 |
| Duplicate extra occurrences | 3 |
| Raw/unique/stored parent edges | 3,519 / 3,519 / 3,519 |
| Unresolved membership edges / missing identities | 2,804 / 1,543 |
| Unresolved parent edges / missing identities | 92 / 41 |
| Normalized complexes | 93,751 |
| Total stored source-graph rows | 706,745 |

## PRE-INGESTION PLANNER

`tools/source_expansion/naptan_n5_r2.py` reused the committed N3 parser and N5-R1 independent keyed-count semantics. It verified the exact source hash, corrected counts, all three duplicate keys, zero hierarchy cycles, maximum depth 13, 701 multi-parent nodes, 73 shared-root multi-parent nodes, and 628 cross-complex/unresolved multi-parent nodes. The production preflight found zero rows in every source-graph table and zero source-identity conflicts.

The deterministic projection reproduced 91,757 single-area complexes, 559 parent-area complexes, 1,435 multimodal-parent complexes, and 93 unresolved area nodes. Mode distribution reproduced the N5-R1 contract: bus/coach 75,920; multimodal 1,541; no observed mode 13,591; metro/tram/underground 641; rail 1,519; ferry/port 470; air 65; taxi 4.

## SNAPSHOT INSERTION

- Deterministic key: `naptan:sha256:6fc7e40e2af3b30e9fd117bdac313b58f3385bff26517fd78d5554da12b4183a`.
- Inserted: 1 source snapshot row.
- Initial lifecycle state: `CAPTURED`; final lifecycle state: `INGESTED`.
- Conflicts before write: 0.
- No legacy `import_runs` row was created.

## PLACE INGESTION

- Planned: 97,270.
- Inserted: 97,270.
- Final count: 97,270.
- Conflicts: 0.
- Identities were `naptan-stop-area:<UPPER StopAreaCode>`.

## NODE INGESTION

- Planned: 436,428.
- Inserted: 436,428.
- Final count: 436,428.
- Conflicts: 0.
- Identities were `naptan-stop-point:<UPPER ATCOCode>`.
- Publisher coordinates were written only to source-node publisher fields; no canonical facility geometry was touched.

## MEMBERSHIP INGESTION

- Raw publisher elements represented: 169,530.
- Unique logical keys: 169,527.
- Stored rows: 169,527.
- Duplicate extra occurrences preserved: 3.
- The three duplicate keys each have `duplicate_occurrence_count = 2`; the other 169,524 rows have value 1.
- Unresolved logical edges: 2,804.
- Distinct missing StopArea identities: 1,543.
- No valid unique publisher relationship was discarded and no placeholder StopArea was fabricated.

## PARENT INGESTION

- Raw publisher elements: 3,519.
- Stored edges: 3,519.
- Unresolved edges: 92.
- Distinct missing parent identities: 41.
- Duplicate parent edges: 0.
- Multi-parent relationships were preserved; no preferred parent was selected.

## SOURCE-GRAPH COUNTS

| Production table | Final rows |
|---|---:|
| transport_source_snapshots | 1 |
| transport_source_places | 97,270 |
| transport_source_nodes | 436,428 |
| transport_source_memberships | 169,527 |
| transport_source_place_parents | 3,519 |
| **Total stored source-graph rows** | **706,745** |

## GRAPH VALIDATION

- Hierarchy maximum depth: 13.
- Hierarchy cycles: 0.
- Multi-parent nodes: 701 (667 two-parent, 34 three-parent).
- Shared-root multi-parent nodes: 73.
- Cross-complex/unresolved multi-parent nodes: 628.
- Normalized complexes: 93,751; single-area 91,757; parent-area 559; multimodal-parent 1,435; unresolved area nodes 93.
- Production recursive SQL reproduced depth 13 and zero cycle paths.
- Production geography verification: 84,415 valid StopArea geographies and 399,246 valid StopPoint geographies, all SRID 4326.

## SECOND-PASS IDEMPOTENCY

The identical frozen source was replanned and compared against every explicit production source fact and relationship key. The exact-row readback covered 1 snapshot, 97,270 places, 436,428 nodes, 169,527 memberships, and 3,519 parent edges.

- Proposed new snapshots: 0.
- Proposed new places: 0.
- Proposed new nodes: 0.
- Proposed new memberships: 0.
- Proposed new parent edges: 0.
- Conflicts: 0.
- Differing existing publisher rows: 0.
- Gratuitous updates: 0.
- Canonical changes: 0.
- Classification: `SECOND_PASS_ZERO_MUTATIONS`.

Two verifier-only corrections were required: offset pagination was replaced with indexed keyset pagination after a PostgREST statement timeout, and database `double precision` coordinate round-trips were compared at a 1e-12 tolerance. No production data or migration was changed by either correction.

## EXISTING RELIEF DATA

| Table | Before | After | Delta |
|---|---:|---:|---:|
| facilities | 15,620 | 15,620 | 0 |
| facility_sources | 15,634 | 15,634 | 0 |
| facility_source_observations | 14 | 14 | 0 |
| import_runs | 5 | 5 | 0 |
| toilet_map_import_staging | 0 | 0 | 0 |
| toilet_units | 0 | 0 | 0 |
| toilet_unit_sources | 0 | 0 | 0 |

## SECURITY

All five source tables retain RLS enabled, zero policies, zero direct `PUBLIC`/`anon`/`authenticated` privileges, and the N4A-established `service_role` grants. No policy, view, RPC, grant, or RLS change was made. Existing project-wide Supabase advisor findings were observed and not remediated because they are outside N5-R2 scope.

## MIGRATION CHAIN

The final command `supabase db push --dry-run --linked` returned `Remote database is up to date.` N5-R2 created no migration and made no migration-ledger mutation.

## PERFORMANCE

- Exact-source planner: 91.474 seconds, 7,726.18 stored rows/sec.
- Chunked production apply end-to-end: 795.819 seconds.
- Chunk POST time: 314.691 seconds, 2,245.34 inserted rows/sec.
- Batch size: 2,000.
- Chunks: 355.
- Retries: 0.
- Slowest chunk: 6.976 seconds.

## TFL REPRODUCTION

The optional TfL cohort reproduction was not run. N5-R2 did not read or mutate TfL observations and did not write any canonical match.

## PRODUCTION MUTATION ACCOUNTING

Authorized source-graph inserts:

- `SOURCE SNAPSHOT INSERTS: 1`
- `SOURCE PLACE INSERTS: 97,270`
- `SOURCE NODE INSERTS: 436,428`
- `SOURCE MEMBERSHIP INSERTS: 169,527`
- `SOURCE PLACE-PARENT INSERTS: 3,519`
- `TOTAL SOURCE-GRAPH INSERTS: 706,745`

Required zero categories:

- `CANONICAL FACILITY INSERTS: 0`
- `CANONICAL FACILITY UPDATES: 0`
- `FACILITY_SOURCE INSERTS: 0`
- `FACILITY_SOURCE_OBSERVATION MUTATIONS: 0`
- `IMPORT_RUN MUTATIONS: 0`
- `TOILET_UNIT MUTATIONS: 0`
- `TOILET_UNIT_SOURCE MUTATIONS: 0`
- `TFL OBSERVATION MUTATIONS: 0`
- `AUTH MUTATIONS: 0`
- `SCHEMA MUTATIONS: 0`
- `MIGRATION LEDGER MUTATIONS: 0`

## VALIDATION

- 50 Python unit tests passed after adding the N5-R2 guard tests.
- Python compilation passed.
- Exact frozen-source hash and size passed.
- Corrected N5-R1 plan passed.
- Production graph counts and semantic aggregates passed.
- Exact-row second-pass comparison passed.
- Hierarchy, duplicate, unresolved-reference, Unicode, geography, RLS, grants, index, trigger, and constraint checks passed.
- No EAS, Expo, Android, Gradle, national-source refresh, canonical reconciliation, or N6 execution occurred.

## FILES CREATED OR MODIFIED

- `tools/source_expansion/naptan_n5_r2.py`
- `tools/source_expansion/test_naptan_n5_r2.py`
- `docs/data/NAPTAN_N5_R2_PRE_INGESTION_PLAN_2026-08-23.json`
- `docs/data/NAPTAN_N5_R2_EXECUTION_EVIDENCE_2026-08-23.json`
- `docs/data/NAPTAN_N5_R2_CHUNK_EVIDENCE_2026-08-23.json`
- `docs/data/NAPTAN_N5_R2_SOURCE_VERIFICATION_2026-08-23.json`
- `docs/data/NAPTAN_N5_R2_SOURCE_GRAPH_COUNTS_2026-08-23.json`
- `docs/data/NAPTAN_N5_R2_MEMBERSHIP_VALIDATION_2026-08-23.json`
- `docs/data/NAPTAN_N5_R2_UNRESOLVED_REFERENCE_VALIDATION_2026-08-23.json`
- `docs/data/NAPTAN_N5_R2_HIERARCHY_VALIDATION_2026-08-23.json`
- `docs/data/NAPTAN_N5_R2_NORMALIZED_PROJECTION_2026-08-23.json`
- `docs/data/NAPTAN_N5_R2_IDEMPOTENCY_PLAN_2026-08-23.json`
- `docs/data/NAPTAN_N5_R2_IDEMPOTENCY_EVIDENCE_2026-08-23.json`
- `docs/data/NAPTAN_N5_R2_PRODUCTION_IMMUTABILITY_2026-08-23.json`
- `docs/data/NAPTAN_N5_R2_SECURITY_VERIFICATION_2026-08-23.json`
- `docs/data/NAPTAN_N5_R2_PERFORMANCE_2026-08-23.json`
- `docs/data/NAPTAN_N5_R2_N6_READINESS_2026-08-23.json`
- `docs/data/NAPTAN_N5_R2_PRODUCTION_INGESTION_REPORT_2026-08-23.md`

The raw XML was not committed. The sealed N4A migration, protected files, and prior evidence were not modified.

## GIT

- Commit A: `efc1179` — `feat(data): ingest governed national NaPTAN graph`.
- Commit B: the final evidence/report finalization commit containing this update.
- Commit A was pushed normally; no merge, rebase, reset, amend, cherry-pick, or force-push was used.
- The final local and remote branch SHAs are verified after Commit B.

## REQUIRED CLASSIFICATIONS

- `FROZEN_SOURCE_EXACTLY_VERIFIED`
- `CORRECTED_N5_R1_CONTRACT_REPRODUCED`
- `NATIONAL_SOURCE_GRAPH_INGESTED`
- `CORRECTED_MEMBERSHIP_SEMANTICS_REPRODUCED`
- `N3_GRAPH_INVARIANTS_REPRODUCED`
- `SECOND_PASS_ZERO_MUTATIONS`
- `CANONICAL_RELIEF_DATA_UNCHANGED`
- `SOURCE_GRAPH_SECURITY_UNCHANGED`
- `MIGRATION_CHAIN_SYNCHRONIZED`
- `N6_READ_ONLY_RECONCILIATION_PLANNING_READY_FOR_SEPARATE_AUTHORIZATION`

## FINAL CLASSIFICATION

`RELIEF NAPTAN N5-R2 — EXACT FROZEN NATIONAL SOURCE GRAPH INGESTED / 706,745 SOURCE ROWS STORED / CORRECTED MEMBERSHIP CONTRACT REPRODUCED / SECOND-PASS ZERO MUTATIONS / CANONICAL RELIEF DATA UNCHANGED / N6 READ-ONLY PLANNING READY FOR SEPARATE AUTHORIZATION`

N6 remains separately unauthorized. No canonical reconciliation was performed.

`TOTAL PRODUCTION SOURCE-GRAPH INSERTS: 706,745`

`TOTAL NON-SOURCE PRODUCTION MUTATIONS: 0`

`NO CANONICAL FACILITY CHANGES: 0`

`NO NAPTAN INGESTION ROWS OUTSIDE SOURCE GRAPH: 0`

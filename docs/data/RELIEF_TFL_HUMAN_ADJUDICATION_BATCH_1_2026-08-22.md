# Relief TfL Human Adjudication Batch 1 — 2026-08-22

**RELIEF TFL HUMAN ADJUDICATION BATCH 1 — NO-GO / INSUFFICIENT PHYSICAL-UNIT EVIDENCE**

**PROPOSAL-ONLY / PRODUCTION EXECUTION NOT AUTHORIZED**

This bounded transaction reproduces and adjudicates only the frozen 58-row cohort: 9 new-parent rows and 49 same-station multi-row physical-unit rows. It does not include the remaining 28 existing-parent rows without a determinable child-unit target.

## Executive summary

- Starting SHA: `16841f03e22bb925daec97d98bb2c0b2c572409a`
- TfL ZIP SHA-256: `19c50772febd1a3d7625f59e079b7590c5da4ed70424d6f552cfd7db1611e2ce`
- Reconciliation SHA-256: `65cc9cc8c41b7b3a003524610b674c7f2eae96ff7fe5116f38f2d2856cb777cb`
- Required attribution: `Data provided by Transport for London`
- Scope: 58 source rows; 9 parent candidates; 49 physical-unit ambiguity rows
- Production mutations: **0**
- External web evidence used for a decision: **No**

## Source integrity and evidence ledger

The ZIP and reconciliation JSON were consumed from their committed frozen paths. No feed refresh, replacement, normalization, or source-row identity change was performed.

| Evidence | Reference | What it establishes | Physical-unit proof |
|---|---|---|---|
| E1 | Official TfL ZIP and frozen local copy | Station identity, source toilet row, attributes, station-level coordinates | No |
| E2 | `tools/source_expansion/cache/tfl-detailed-2026-08-21/tfl-reconciliation.json` | Exact cohort membership and no existing candidate under frozen rules | No |
| E3 | Read-only production verification on 2026-08-22 | Existing counts, empty child tables, RLS/source exposure boundary | No |

Official station pages were not used to approve a decision: they establish station existence or a station-level facility listing, not a source-row-to-physical-room mapping. No low-confidence third-party evidence was used.

## New-parent adjudication

- Total rows: **9**
- `APPROVE_PARENT_CREATION`: **0**
- `REJECT_PARENT_CREATION`: **0**
- `STILL_UNRESOLVED`: **9**
- Proposed future parent creations: **0**

All 9 rows remain unresolved. The frozen source identifies the TfL station and toilet row, but does not establish the canonical parent address/town needed for a safe new facility record. Station-level coordinates are retained as station-level only.

| StationUniqueId | Station | TfL Id | Type | Location | Decision |
|---|---|---:|---|---|---|
| `910GACTONML` | Acton Main Line | `1` | UNISEX | Located in ticket hall | `STILL_UNRESOLVED` |
| `910GCHDWLHT` | Chadwell Heath | `1` | UNISEX | Located in ticket hall | `STILL_UNRESOLVED` |
| `910GDENMRKH` | Denmark Hill | `1` | UNISEX | Located behind ticket office | `STILL_UNRESOLVED` |
| `910GFRSTGT` | Forest Gate | `1` | UNISEX | Located in ticket hall | `STILL_UNRESOLVED` |
| `910GMRYLAND` | Maryland | `1` | UNISEX | Located in ticket hall | `STILL_UNRESOLVED` |
| `940GZZLUECM` | Ealing Common | `1` | MALE | Located on platform 2 | `STILL_UNRESOLVED` |
| `940GZZLUECM` | Ealing Common | `2` | FEMALE | Located on platform 1 | `STILL_UNRESOLVED` |
| `940GZZLUHWE` | Hounslow East | `1` | UNISEX | Located in ticket hall | `STILL_UNRESOLVED` |
| `940GZZLUWLA` | Wood Lane | `1` | UNISEX | Located in ticket hall | `STILL_UNRESOLVED` |

## Physical-unit adjudication

- Total rows: **49**
- Affected station groups: **22**
- `APPROVE_DISTINCT_UNIT`: **0**
- `APPROVE_SHARED_UNIT`: **0**
- `REJECT_AS_NON_UNIT`: **0**
- `STILL_UNRESOLVED`: **49**
- Proposed future toilet units: **0**

No row was collapsed or promoted. Gender, accessibility, baby-changing, gateline, consecutive IDs, row order, shared location text, and station coordinates do not prove physical topology.

## Station topology table

| StationUniqueId | Station | TfL rows | Source identities | Proposed units | State |
|---|---|---:|---|---:|---|
| `910GHAYESAH` | Hayes & Harlington | 3 | `1`, `2`, `3` | — | `STILL_UNRESOLVED` |
| `910GPENEW` | Penge West | 3 | `1`, `2`, `3` | — | `STILL_UNRESOLVED` |
| `910GWHHRTLA` | White Hart Lane | 3 | `1`, `2`, `3` | — | `STILL_UNRESOLVED` |
| `940GZZLUALP` | Alperton | 2 | `1`, `2` | — | `STILL_UNRESOLVED` |
| `940GZZLUBEC` | Becontree | 2 | `1`, `2` | — | `STILL_UNRESOLVED` |
| `940GZZLUBSC` | Barons Court | 2 | `1`, `2` | — | `STILL_UNRESOLVED` |
| `940GZZLUCWL` | Chigwell | 2 | `1`, `2` | — | `STILL_UNRESOLVED` |
| `940GZZLUDGE` | Dagenham East | 2 | `1`, `2` | — | `STILL_UNRESOLVED` |
| `940GZZLUDGY` | Dagenham Heathway | 3 | `1`, `2`, `3` | — | `STILL_UNRESOLVED` |
| `940GZZLUGGH` | Grange Hill | 2 | `1`, `2` | — | `STILL_UNRESOLVED` |
| `940GZZLUHCH` | Hornchurch | 2 | `1`, `2` | — | `STILL_UNRESOLVED` |
| `940GZZLUNEN` | North Ealing | 2 | `1`, `2` | — | `STILL_UNRESOLVED` |
| `940GZZLUNHT` | Northolt | 2 | `1`, `2` | — | `STILL_UNRESOLVED` |
| `940GZZLUPKR` | Park Royal | 2 | `1`, `2` | — | `STILL_UNRESOLVED` |
| `940GZZLUPVL` | Perivale | 2 | `1`, `2` | — | `STILL_UNRESOLVED` |
| `940GZZLURVY` | Roding Valley | 2 | `1`, `2` | — | `STILL_UNRESOLVED` |
| `940GZZLUSUH` | Sudbury Hill | 2 | `1`, `2` | — | `STILL_UNRESOLVED` |
| `940GZZLUSUT` | Sudbury Town | 2 | `1`, `2` | — | `STILL_UNRESOLVED` |
| `940GZZLUUPB` | Upminster Bridge | 2 | `1`, `2` | — | `STILL_UNRESOLVED` |
| `940GZZLUUPY` | Upney | 2 | `1`, `2` | — | `STILL_UNRESOLVED` |
| `940GZZLUWTA` | West Acton | 2 | `1`, `2` | — | `STILL_UNRESOLVED` |
| `HUBHX4` | Heathrow Terminal 4 | 3 | `1`, `2`, `3` | — | `STILL_UNRESOLVED` |

Every topology group has an empty source-row-to-unit mapping because no authoritative evidence proves a distinct or shared physical unit.

## Proposed future operations

| Operation | Count |
|---|---:|
| Facility inserts | 0 |
| Facility-source links | 0 |
| Toilet-unit inserts | 0 |
| Toilet-unit source links | 0 |

The JSON is declarative evidence only. It contains no executable SQL, Supabase client, promotion RPC, staging operation, import-run operation, or production apply mechanism.

## Remaining blockers

- All 9 new-parent rows: canonical parent address/town and safe parent identity remain unresolved.
- All 49 physical-unit rows across the station groups above: physical toilet topology remains unresolved.
- The source provides station-level coordinates only; no toilet-specific coordinate is available.
- The 28 existing-parent/no-unit-target rows remain explicitly out of scope.

## Validation and safety declaration

- Frozen source hashes unchanged.
- Source identity coverage: 58 of 58 exactly once.
- Station-level coordinate precision preserved for every row.
- Unresolved decisions generate zero proposed operations.
- Production counts remain 15,620 facilities, 15,620 facility_sources, 5 import_runs, 0 staging rows, 0 toilet_units, and 0 toilet_unit_sources.
- TfL promotion to production was not authorized or executed by this transaction.

## Final classification

**RELIEF TFL HUMAN ADJUDICATION BATCH 1 — NO-GO / INSUFFICIENT PHYSICAL-UNIT EVIDENCE**

TfL production promotion remains separately unauthorized regardless of this adjudication result.

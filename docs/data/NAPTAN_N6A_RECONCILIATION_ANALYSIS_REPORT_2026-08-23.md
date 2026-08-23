# RELIEF NAPTAN N6A — Read-Only Production Reconciliation Analysis

## STARTING STATE

- Repository: `hourwise/Relief`
- Branch: `codex/toilet-map-apply-1a-production-deploy`
- Starting local and remote SHA: `ff70e8255fd1806d9abab6f081d15a95c5c9dbd1`
- Remote verification: `git fetch origin` and independent `git ls-remote`
- Production project: `Relief` / `bgwxrxkmyaihplaloely`
- Project state: `ACTIVE_HEALTHY`, `eu-central-1`, PostgreSQL `17.6.1.127`
- Migration ledger head: `20260822170000`
- Migration dry run: `Remote database is up to date.`
- A later CLI-only recheck in the evidence shell lacked a `SUPABASE_ACCESS_TOKEN`; it made no request and no mutation. The initial required dry-run gate and final read-only migration-ledger/list-migrations check remained clean at `20260822170000`.
- Protected files were preserved as existing local changes and were not staged or modified.

N6A used only read-only production SQL/catalog/PostGIS queries. It created no production candidate table, view, RPC, index, policy, or provenance row.

## SEALED N4A

`supabase/migrations/20260822170000_naptan_transport_source_graph.sql` remained byte-for-byte unchanged. SHA-256 at start, before commit, and final state is:

`087A389B8CEAC021B12708BC55C39022CB38D5459510EFFB6CF057CEF232C44E`

## SOURCE GRAPH

The governed snapshot was verified as `naptan:sha256:6fc7e40e2af3b30e9fd117bdac313b58f3385bff26517fd78d5554da12b4183a`, publisher UK Department for Transport, 578,991,782 bytes, with the required OGL v3.0 attribution.

Production counts remained exactly: 1 snapshot, 97,270 places, 436,428 nodes, 169,527 memberships, and 3,519 parent edges; total 706,745. Unresolved membership edges were 2,804 across 1,543 missing identities; unresolved parent edges were 92 across 41 missing identities. The rebuilt hierarchy had maximum depth 13 and zero cycles.

## CANONICAL BASELINE AND EVIDENCE SURFACE

The canonical baseline was 15,620 facilities, 15,634 facility_sources, 14 facility_source_observations, 5 import_runs, and zero staging/toilet-unit rows. All 15,620 facilities had geography; 15,012 had town; no canonical address or postcode values were available for this analysis.

The only source namespaces present were the historical `Toilet Map UK` rows and 14 TfL detailed station rows. NaPTAN source names and source record IDs were both zero. Therefore no shared official identifier or existing NaPTAN provenance was invented: exact identifier matches are `0` and the correct state is `NO_SHARED_OFFICIAL_IDENTIFIER`.

## NORMALIZED COMPLEX PROJECTION

The projection was rebuilt from production source tables, not from raw XML and not from persisted derived rows. It reproduced 93,751 complexes: 91,757 single-area, 559 parent-area, and 1,435 multimodal parent complexes. Root publisher geometry was available for 81,435 complexes and unavailable for 12,316. Mode distribution reproduced the N5-R2 contract: bus/coach 75,920; multimodal 1,541; no observed mode 13,591; metro/tram/underground 641; rail 1,519; ferry/port 470; air 65; taxi 4.

Normalized complexes remain `DETERMINISTIC_PROJECTION`; none were persisted.

## CANDIDATE GENERATION CONTRACT

The primary unit is a normalized transport complex. Candidate generation uses exact normalized names or a source-token subset with at least two source tokens, then indexed PostGIS geography bands of 25m, 50m, 100m, 250m, 500m, 1km, and 5km. The full bounded candidate query uses a 500m band, retains publisher root coordinates as the primary geography source, and does not use a derived centroid as publisher evidence. Proximity alone is a hard veto.

The bounded name-and-geography query produced 695 candidate pairs across 654 complexes. Candidate counts were 0 for 93,097 complexes, 1 for 619, 2 for 31, 3 for 2, and 4 for 2. At 25m/50m/100m/250m/500m the candidate-pair counts were 80/205/383/600/695. The most important limitation is product scope, not database scale: source-to-facility candidates are sparse for high-value modes but ordinary bus/coach data must remain supporting-only.

## EVIDENCE MODEL AND CLASSIFICATIONS

Official identifier evidence has precedence, followed by existing governed provenance, exact normalized name, source-token compatibility, publisher geography, hierarchy resolution, and competing-candidate analysis. A facility collision or multiple plausible candidates remains ambiguous. Generic labels such as `Station`, `Central`, and `High Street` are not identity proof.

The analytical classification totals were:

| Classification | Complexes |
|---|---:|
| EXISTING_CANONICAL_MATCH | 0 |
| PROPOSED_CANONICAL_MATCH | 51 |
| AMBIGUOUS_CANONICAL_MATCH | 9 |
| PROPOSED_NEW_TRANSPORT_PLACE | 4,163 |
| SUPPORTING_SOURCE_ONLY | 75,933 |
| CONFLICT | 0 |
| NO_ACTION | 13,595 |

These are local analysis outcomes only. They were not written to production.

The 4,163 proposed-new rows are an explicit product-governance warning, not a creation queue: air 58, ferry/port 462, metro/tram/underground 640, multimodal 1,500, rail 1,503. Ordinary bus/coach complexes, 75,920, default to `SUPPORTING_SOURCE_ONLY` to prevent a raw NaPTAN mirror from becoming the Relief canonical model.

Collisions were retained: two source complexes had multiple facilities (Cockfosters Underground Station and Wapping Wharf), and 30 facilities had multiple source-complex candidates. Oakwood Underground Station was a representative facility collision between distinct Oakwood source complexes.

## TFL REPRODUCTION

The frozen 509-station TfL roster was re-evaluated against the production graph using the committed N2 candidate roster and production root-resolution/type/mode data. The result exactly reproduced N3: 47 `HIGH_CONFIDENCE_COMPLEX_MATCH`, 7 `HIGH_CONFIDENCE_SUBPLACE_MATCH`, 104 `MULTIMODAL_COMPLEX_MATCH`, 2 `AMBIGUOUS_COMPLEX`, and 349 `NO_MATCH`; exact official identifier matches remained 0. All 28 N2 ambiguities were resolved and no formerly high-confidence case was downgraded.

The 14 existing TfL observations were audited without writes. Five had a strict root name/geometry candidate (three exact-name and two token-subset); nine had no strict candidate. The audit does not create NaPTAN provenance and does not force the nine cases. Child-area/subplace evidence remains a separate review input.

## PERFORMANCE

The production probe used `idx_transport_source_places_snapshot_name` and `facilities_location_gix`. A representative `EXPLAIN ANALYZE` exact-name plus 500m probe used those indexes, with 33.339ms planning and 16.977ms execution, 903 shared-hit blocks, and zero shared reads. No index or schema change was made. Full projection/candidate/TfL query round trips were bounded and completed through the read-only Supabase SQL channel.

## N6B RECOMMENDATION

Canonical promotion is not ready. The next safe transaction is a separately authorized, human-adjudicated, high-value sample drawn from the 51 proposed existing links and 9 ambiguous/collision cases, after a product decision on transport canonical scope. The 4,163 proposed-new analytical rows must not become a mass creation batch. No N6 schema change is required by this analysis.

## SECURITY AND IMMUTABILITY

All five source tables remained RLS-enabled, with zero policies and direct grants only to `service_role`; no direct `PUBLIC`, `anon`, or `authenticated` grants were observed. Before/after counts remained equal for the source graph and all canonical baseline tables. No production data, schema, migration ledger, provenance, facility, observation, toilet, auth, or security mutation occurred.

## VALIDATION

- N3/N4A/N5-R1/N5-R2/N6A Python tests: 59 passed.
- Python compilation: passed.
- Production projection counts and graph invariants: passed.
- Frozen TfL reproduction: passed exactly.
- Candidate key/name normalization/read-only guard tests: passed.
- PostGIS geography/index probe: passed read-only.
- JSON evidence parsing, sealed migration hash, migration dry run, and final git checks: recorded with the final evidence.

## REQUIRED CLASSIFICATIONS

- `PRODUCTION_SOURCE_GRAPH_REPRODUCED`
- `TFL_RECONCILIATION_REPRODUCED`
- `CANONICAL_CANDIDATE_GENERATION_VALIDATED`
- `RECONCILIATION_EVIDENCE_MODEL_VALIDATED`
- `TRANSPORT_CANONICAL_SCOPE_REQUIRES_PRODUCT_DECISION`
- `PRODUCTION_RECONCILIATION_ANALYSIS_READ_ONLY`
- `N6B_CANONICAL_PROMOTION_NOT_READY`

`TOTAL PRODUCTION MUTATIONS: 0`

# RELIEF NAPTAN N3 — Transport Complex Normalisation & Canonical Reconciliation

Status: bounded read-only evidence/design batch. **Production ingestion is not authorized.**

## Starting state

- Repository: `hourwise/Relief`
- Branch: `codex/toilet-map-apply-1a-production-deploy`
- Starting local and remote SHA: `3b3f89e300a8a13cf9680a6954cf389921a17a60`
- Protected working-tree changes preserved untouched: `.easignore`, `app.json`, `docs/EAS_CONFIG_AUDIT.md`
- Production project: `bgwxrxkmyaihplaloely` / Relief

The exact checkpoint matched after fetching `origin`. No unexpected staged changes were present.

## Source replay and integrity

N2’s raw XML was intentionally removed from its disposable cache after N2 evidence generation. N3 therefore retrieved a separately manifested current snapshot from the same official DfT endpoint. The bytes match the frozen N2 hash exactly; N2 artifacts were not rewritten.

- Publisher: UK Department for Transport
- Product: national NaPTAN XML access-node and StopArea package
- URL: `https://naptan.api.dft.gov.uk/v1/access-nodes?dataFormat=xml`
- Documentation: [DfT national NaPTAN download](https://beta-naptan.dft.gov.uk/download/national), [official API catalogue](https://www.api.gov.uk/dft/national-public-transport-access-nodes-naptan-and-national-public-transport-gazetteer-nptg-api/), [schema guide](https://naptan.dft.gov.uk/naptan/schema/2.5/doc/NaPTANSchemaGuide-2.5-v0.67.pdf)
- N3 retrieval UTC: `2026-08-22T14:48:39.4826193Z`
- Size: `578,991,782` bytes
- SHA-256: `6FC7E40E2AF3B30E9FD117BDAC313B58F3385BFF26517FD78D5554DA12B4183A`
- Frozen N2 SHA-256: identical
- Format/encoding: UTF-8 XML; replacement characters rejected; raw bytes hashed before parsing
- Licence: Open Government Licence v3.0, with published terms recorded in the N3 manifest
- Attribution: `Contains public sector information licensed under the Open Government Licence v3.0.`
- Raw XML: retained only in disposable external cache, not committed

## National hierarchy profile

The replay reproduced N2’s source totals: 436,428 StopPoints, 97,270 StopAreas and 169,527 publisher-declared memberships. N3 normalised the 93,751 publisher root areas; it did not equate them with Relief facilities.

| Measure | Result |
|---|---:|
| Normalised source complexes | 93,751 |
| Single-area complexes | 91,757 |
| Parent-area complexes | 559 |
| Multimodal parent complexes | 1,435 |
| Root areas with no members | 13,928 |
| Areas unresolved because their parent chain cannot resolve | 93 |
| Maximum StopAreas in one normalized complex | 18 |
| Mean / median StopAreas per complex | 1.0365 / 1 |
| Mean / median StopPoints per complex | 1.7753 / 2 |
| Maximum StopPoints in one complex | 76 |

Complex mode counts were: bus/coach 75,920; multimodal 1,541; no observed mode 13,591; metro/tram/underground 641; rail 1,519; ferry/port 470; air 65; taxi 4. A multimodal complex preserves every observed mode; N3 does not select a lossy primary mode.

Geometry was classified as publisher StopArea/root coordinate 81,435 (1,884 parent-area and 79,551 single-area scopes), derived child-area centroid 1, derived member StopPoint centroid 23, and no usable geometry 12,292. Derived geometry is analysis-only and cannot overwrite publisher coordinates.

Status aggregation produced ACTIVE 79,653, MIXED 3,838, PENDING 6 and SOURCE_DELETED 10,254. Inactive/deleted members remain source evidence.

## Transport-complex definition and subplaces

The source-level complex is the unique resolved highest StopArea ancestor. A root with no children is `SINGLE_AREA_COMPLEX`; a one-mode root with child areas is `PARENT_AREA_COMPLEX`; a root whose descendants contain multiple structured modes is `MULTIMODAL_PARENT_COMPLEX`. A child StopArea remains a source subplace, and a StopPoint remains a source node. An entrance, platform, bay or ordinary bus node is never promoted to a canonical Relief facility merely because it has a row.

The deepest ancestor is not accepted as a user-facing station solely because it is deepest. N3 checks the publisher graph, area type, descendants, modes, status and geometry; unresolved or defective chains remain unresolved. The formal contract is in `NAPTAN_N3_NORMALISATION_CONTRACT_2026-08-22.md`.

## Multi-parent StopPoints

N3 reproduced 701 multi-parent StopPoints: 667 have two parents and 34 have three. There are 73 whose resolved parents share one root complex and 628 whose parents cross complexes or include unresolved references. N3 does not interpret the shared-root count as proof of physical interchange semantics. It records every publisher membership and refuses arbitrary parent selection.

The source types and modes vary; therefore a multi-parent node is represented as `MULTI_PARENT_NODE_COMPLEX` evidence, not duplicated into one node per parent and not collapsed to one parent. This is the safe rule for shared entrances, cross-modal nodes and any malformed relationships until publisher semantics or later adjudication resolve them.

## Deep hierarchy

Depth distribution (root = 1) was: 1: 93,843; 2: 3,178; 3: 180; 4: 38; 5: 9; 6: 7; 7: 5; 8: 4; 9: 2; 10: 1; 11: 1; 12: 1; 13: 1. The maximum chain is an Oxford example containing locality/grouping-style `GCLS`/`GPBS` areas and a rail `GRLS` area. Other representative chains include Bristol Temple Meads (depth 2), Bedford (depth 3), and Luton (depth 6).

These chains demonstrate that depth is a publisher hierarchy property, not a universal station-level identity rule. The top ancestor can be a meaningful transport parent, a grouping area, or unresolved from the available semantics. N4 must persist parent edges rather than flattening by depth.

## Referential defects

N3 recorded: missing member-parent references 1,543; missing area-parent references 41; duplicate membership elements 3; invalid identity 0; hierarchy cycles 0; unresolved references 1,581. Defects are isolated to affected nodes/subgraphs. No missing area, parent, or facility is fabricated. No resolved root complex was marked defect-affected merely because an unrelated missing member reference existed.

## TfL ↔ NaPTAN N3 reconciliation

N3 reused the frozen TfL evidence and the committed N2 candidate decisions. It did not refresh TfL. It mapped each frozen candidate StopArea to its resolved N3 root, preserving N2’s name/geometry evidence and avoiding a second incomplete join for stations without toilet rows.

| Classification | N2 | N3 |
|---|---:|---:|
| Exact official identity | 0 | 0 |
| High-confidence StopArea / complex result | 130 | 47 `HIGH_CONFIDENCE_COMPLEX_MATCH` |
| High-confidence subplace result | — | 7 |
| Multimodal complex result | — | 104 |
| Ambiguous | 30 | 2 |
| No match | 349 | 349 |

N3 resolved 28 of N2’s 30 ambiguous stations by collapsing multiple candidate StopAreas to one authoritative root complex. It resolved no additional N2 no-matches, downgraded no N2 high-confidence results, and found 20 candidate sets where several StopAreas represented one normalized complex. Examples include Brent Cross West, Bethnal Green, and rail/bus complexes such as Caledonian Road & Barnsbury, Coulsdon South, Cricklewood and City Thameslink. The result is a material consistency improvement in ambiguity handling, not authorization for a facility link or creation.

## Canonical Relief reconciliation

The future contract distinguishes `EXISTING_CANONICAL_MATCH`, `PROPOSED_CANONICAL_MATCH`, `AMBIGUOUS_CANONICAL_MATCH`, `PROPOSED_NEW_TRANSPORT_PLACE`, `SUPPORTING_SOURCE_ONLY`, `CONFLICT` and `NO_ACTION`. Strong evidence is an existing source link or authoritative cross-reference; name, mode, hierarchy and bounded geometry are secondary evidence; proximity alone is weak. A normalized NaPTAN complex is not a canonical Relief facility.

The N3 dry run reports node-level N2 estimates (48 likely existing, 824 ambiguous, 3,459 likely new candidates, 431,035 supporting/excluded). At normalized source-complex level it reports 93,751 source roots, 13,928 empty roots, 12,292 without geometry, 24 derived-only geometry and 73 multi-parent shared-root cases. The frozen N2 candidate estimates remain 380 likely existing, 1,717 ambiguous and 72,364 likely new at StopArea level; they are estimates only, not revised facility counts or operations. The complete machine-readable boundary is in `NAPTAN_N3_RELIEF_DRY_RUN_2026-08-22.json`.

## N4 schema contract

N3 recommends a small additive source-neutral model, not a migration in this batch:

- `transport_source_places` for root complexes and preserved child areas;
- `transport_source_nodes` for publisher StopPoints;
- `transport_source_memberships` for every node-to-place membership;
- `transport_source_place_parents` for nested parent edges.

Publisher identities remain unique and immutable within a source namespace. Source evidence is private/service-role-governed by default. A canonical facility link is not required in the first migration; if added later it must be a strong, auditable relation rather than a nullable polymorphic shortcut. N4 is `N4_SCHEMA_CONTRACT_READY_WITH_OPEN_QUESTIONS` because revision history, source registry ownership and any eventual public read surface still require owner decisions.

## RDG readiness

N3 gives a future RDG integration a stable NaPTAN root/subplace/node graph: a rail StopArea can match an RDG station while bus/metro child areas remain evidence. Direct RDG identity must come from RDG or an authoritative cross-reference; names, mode, geometry and hierarchy are secondary. One RDG station must not automatically become every constituent NaPTAN node, and a multimodal parent must not automatically be treated as the RDG station.

## Performance

The 578,991,782-byte XML was parsed with streaming `iterparse` in approximately 56.4 seconds in the N3 run, about 10.3 MB/s at the measured wall-clock rate. The parser retains compact identity, membership, parent, status and coordinate indexes and clears XML elements at StopPoint/StopArea boundaries. Root traversal uses adjacency maps and memoized resolution; it does not perform an O(N²) scan. Reconciliation uses frozen N2 candidates and root lookup rather than a national pairwise geometry join.

## Production safety and validation

N3 performed no production mutation, migration, RPC apply, ingestion, source-link creation, facility change, toilet change, RLS change or grant change. The required outcome is:

**TOTAL PRODUCTION MUTATIONS: 0**

Read-only production verification against `bgwxrxkmyaihplaloely` returned: facilities 15,620; facility_sources 15,634; import_runs 5; toilet_map_import_staging 0; toilet_units 0; toilet_unit_sources 0; facility_source_observations 14. These match the beginning of N3. `facility_source_observations`, `toilet_units` and `toilet_unit_sources` retained RLS enabled. The private source-observation and unit-source tables retained no public/anon/authenticated policies or table grants; the existing published-toilet-unit SELECT policy and public unit grants were unchanged. No public API exposure was added.

Validation actually run:

- `python -m unittest tools.source_expansion.test_naptan_n3`: 9 passed.
- `python -m unittest discover -s tools/source_expansion -t . -p 'test_*.py'`: 65 passed, 0 failed.
- explicit `python -m py_compile` over all `tools/source_expansion/*.py`: passed.
- `npm.cmd run typecheck`: passed.
- `npm.cmd test`: 24 test files passed, 0 failed.
- JSON parsing and N3 invariants: passed (source totals, 93,751 complexes, 509 TfL stations, zero mutation plan).
- national N3 replay: all five derived JSON SHA-256 values byte-stable on rerun.
- `git diff --check`: passed.
- bounded secret-pattern scan: passed.
- executable mutation-pattern scan: passed.

No EAS, Expo prebuild, Gradle, Android, APK, emulator or native build tooling was invoked. N1/N2 evidence was reused without modification. The raw N3 cache was removed after validation.

## Task-owned files

The bounded commit contains exactly 13 N3 files: the source manifest, complex/multi-parent/deep/TfL/dry-run JSON evidence, three Markdown contracts plus this report, the streaming parser, fixture and focused tests. No national raw XML or CSV was committed. The protected `.easignore`, `app.json` and `docs/EAS_CONFIG_AUDIT.md` changes remain unstaged and uncommitted.

## Decision gates

- Normalisation: `TRANSPORT_COMPLEX_NORMALISATION_PARTIAL` — root normalization is deterministic for the resolved graph, while 93 area nodes and referential defects remain explicitly unresolved.
- Multi-parent handling: `MULTI_PARENT_CONTRACT_PROVEN` — all publisher parents are retained and no arbitrary parent is selected.
- Deep hierarchy: `DEEP_HIERARCHY_PARTIALLY_RESOLVED` — structure is profiled, but depth alone does not establish user-facing transport-place semantics.
- TfL reconciliation: `N3_MATERIALLY_IMPROVES_TFL_RECONCILIATION` — 28 N2 ambiguities resolve through root collapse, with no high-confidence downgrades.
- Canonical contract: `CANONICAL_RECONCILIATION_CONTRACT_READY`
- N4 readiness: `N4_SCHEMA_CONTRACT_READY_WITH_OPEN_QUESTIONS`
- Production: `PRODUCTION INGESTION NOT AUTHORIZED`

## Final classification

**RELIEF NAPTAN N3 — TRANSPORT_COMPLEX_NORMALISATION_PARTIAL / N3_MATERIALLY_IMPROVES_TFL_RECONCILIATION / CANONICAL_RECONCILIATION_CONTRACT_READY / N4_SCHEMA_CONTRACT_READY_WITH_OPEN_QUESTIONS / PRODUCTION INGESTION NOT AUTHORIZED**

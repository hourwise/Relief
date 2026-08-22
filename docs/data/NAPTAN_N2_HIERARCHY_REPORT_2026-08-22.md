# Relief NaPTAN N2 — Official StopArea and Interchange Hierarchy Reconciliation

## Final classification

**RELIEF NAPTAN N2 — OFFICIAL_HIERARCHY_CAPTURED / TRANSPORT_COMPLEX_MODEL_PARTIAL / HIERARCHY_MATERIALLY_IMPROVES_RECONCILIATION / ADDITIVE_TRANSPORT_SCHEMA_RECOMMENDED / PRODUCTION INGESTION NOT AUTHORIZED**

## Starting and source basis

N2 starts from the frozen N1 checkpoint and reuses the frozen TfL evidence. The current official DfT XML package is `NaPTAN.xml`; it contains `StopPoints` and `StopAreas`. The OpenAPI description confirms the current access-node endpoint surface. Raw XML and OpenAPI bytes were held in disposable external storage and were not committed.

- XML bytes: 578,991,782
- XML SHA-256: `6FC7E40E2AF3B30E9FD117BDAC313B58F3385BFF26517FD78D5554DA12B4183A`
- XML retrieval UTC: 2026-08-22T13:57:21Z
- OpenAPI bytes: 3,617
- OpenAPI SHA-256: `9745D22B53160D60F8225432388672D011C274523B54AC6DAA0EB691256765CC`
- Licence: Open Government Licence v3.0
- Attribution: “Contains public sector information licensed under the Open Government Licence v3.0.”

## Hierarchy profile

- StopPoints: **436,428**
- StopAreas: **97,270**
- Membership rows: **169,527**
- StopPoints with one parent: **168,091**
- StopPoints with multiple parents: **701**
- StopPoints with zero parents: **267,636**
- StopAreas with multiple members: **70,598**
- Maximum members in one StopArea: **39**
- Duplicate StopPoint identities: **0**
- Duplicate StopArea identities: **0**
- Missing StopArea references: **1543**
- Duplicate memberships: **3**
- Parent-area relationship rows: **3519**
- Hierarchy cycles: **0**

The XML declares StopArea membership through StopPoint `StopAreaRef` values. Membership is publisher evidence; no spatial membership was inferred. The proposed StopArea identity namespace is `naptan-stop-area:<StopAreaCode>`.

## Interchange semantics

The official model distinguishes access nodes from grouped transport places. A StopArea can contain multiple StopPoints, including entrances, platforms, bays, on-street stops, and nodes from more than one mode. A StopArea therefore provides a safer transport-complex identity than choosing whichever constituent node is nearest to a Relief facility. Multiple nodes inside one StopArea must not become multiple canonical Relief facilities automatically.

Area modes and type distributions are in `NAPTAN_N2_HIERARCHY_PROFILE_2026-08-22.json`. Direct StopArea coordinates are retained as `STOP_AREA_LEVEL`; where absent, member-point centroids are labeled `DERIVED_FROM_MEMBER_STOPPOINTS` and are not production coordinates.

## TfL reconciliation comparison

N1 had 4 high-confidence name/geometry matches, 4 ambiguities, and 501 no-matches. N2 results:

{
  "AMBIGUOUS_TRANSPORT_COMPLEX": 30,
  "HIGH_CONFIDENCE_STOPAREA_MATCH": 118,
  "HIGH_CONFIDENCE_TRANSPORT_COMPLEX_MATCH": 12,
  "NO_MATCH": 349
}

N2 uses official StopArea names, membership, and area geometry before bounded geometry matching. It does not claim an exact cross-source identifier match where none is present. The result artifact contains all 509 station decisions and explicitly retains member counts and modes for each candidate.

Compared with N1, the hierarchy-assisted pass resolved **126** of the N1 no-match stations to high-confidence StopArea/transport-complex matches and resolved **3** of the 4 N1 ambiguities. **3** of the 4 N1 high-confidence name/geometry matches were contradicted or made ambiguous by the stronger hierarchy evidence. **105** high-confidence N2 matches contain multiple publisher-declared member nodes; these are transport-complex collapses, not multiple Relief facilities.

Representative hierarchy-assisted matches include Barking Riverside (`910GBARKRIV` → `naptan-stop-area:910GBARKRIV`), Caledonian Road & Barnsbury (`910GCLDNNRB`), Coulsdon South (`910GCOLSDNS`), Cricklewood (`910GCRKLWD`), and City Thameslink (`910GCTMSLNK`). Remaining ambiguity includes Brent Cross West (`910GBRENTX`) and other stations where multiple or conflicting hierarchy evidence remains.

## Relief dry run

The node-level and transport-complex-level estimates are intentionally separate:

{
  "ambiguous_existing_relief_transport_complex": 1717,
  "empty_stop_area": 13928,
  "likely_existing_relief_transport_complex": 380,
  "likely_new_transport_place_candidate": 72364,
  "unresolved_no_area_geometry": 8881
}

Raw node counts cannot be interpreted as potential Relief facility counts. The dry run is declarative only and contains zero facility, source-link, observation, or production operations.

## Schema readiness

**ADDITIVE_TRANSPORT_SCHEMA_RECOMMENDED.** The deployed source-observation model can preserve private NaPTAN evidence, but N2 now establishes a justified need for a source-neutral transport hierarchy model. A future additive design should separate:

- canonical Relief facility;
- source transport place/StopArea identity;
- source transport node/ATCO identity;
- publisher-declared membership;
- optional parent-area relationships;
- source geometry and coordinate scope;
- mode, type, status, revision, and provenance.

The model must not create a second uncontrolled canonical facility system and must not expose raw source provenance publicly by default. No migration is created or applied in N2.

## RDG readiness

NaPTAN StopArea identities and membership now provide a useful transport-complex scaffold for a future National Rail/RDG batch. RDG must still provide or validate its own station identifiers and any direct cross-reference. Names, geometry, mode, and StopArea membership remain secondary evidence only until the RDG source is available.

## Performance

- XML size: 578,991,782 bytes
- XML elements processed with streaming `iterparse`
- Parse time: 86.754937 seconds
- StopPoints/sec: 5030.58
- Raw XML elements cleared at record boundaries; compact identity, membership, area, and coordinate indexes retained.

## Production safety

This batch performed no production write, schema change, migration, RLS/grant change, API exposure change, source ingestion, facility mutation, or toilet operation.

**TOTAL PRODUCTION MUTATIONS: 0**

## Evidence artifacts

- `NAPTAN_N2_SOURCE_MANIFEST_2026-08-22.json`
- `NAPTAN_N2_HIERARCHY_PROFILE_2026-08-22.json`
- `NAPTAN_N2_TFL_RECONCILIATION_2026-08-22.json`
- `NAPTAN_N2_RELIEF_DRY_RUN_2026-08-22.json`

# Relief NaPTAN N1 — National Source Capture and Semantic Audit

## Classification

**RELIEF NAPTAN N1 — NATIONAL TRANSPORT IDENTITY FOUNDATION COMPLETE / PRODUCTION INGESTION NOT AUTHORIZED**

## Source and integrity

- Publisher: UK Department for Transport, official NaPTAN service.
- Product: current national `Stops.csv` access-node export.
- URL: https://naptan.api.dft.gov.uk/v1/access-nodes?dataFormat=csv
- Retrieval UTC: 2026-08-22T12:09:52Z
- Bytes: 101,824,634
- SHA-256: `FF981876B8442122E058634769F290F6E775F454D80D82B465491E2E5006D3C2`
- Encoding: UTF-8 CSV with optional BOM; decoding and U+FFFD corruption fail closed.
- Licence: Open Government Licence v3.0. Attribution retained: “Contains public sector information licensed under the Open Government Licence v3.0.”
- The raw national file was not committed; it was held in a disposable external cache and removed after artifact generation.

The official national download page and DfT API catalogue identify this as the current national machine-readable NaPTAN access-node product. The GOV.UK schema page records the OGL v3.0 publication terms. The retrieved response contained one file, `Stops.csv`; StopArea/StopsInArea/AreaHierarchy files were not present in this product and are not invented below.

## National profile

- Total rows: **435,366**
- Distinct publisher ATCO identities: **435,366**
- Duplicate publisher-identity rows: **0**
- Rows with complete WGS84 coordinates: **398,181**
- Rows without complete WGS84 coordinates: **37,185**
- Projected Easting/Northing pairs: **435,366**
- Administrative areas: **149**
- Stop areas/membership: **not available in retrieved `Stops.csv`**; locality codes are not treated as StopArea links.
- Parser performance: 16.638381 seconds; 26,166.37 rows/sec; streaming parse with no raw-row retention.

### Stop types

| Type | Count | Meaning / Relief classification |
|---|---:|---|
| `AIR` | 70 | airport entrance / `RELIEF_SUPPORTING_NODE` |
| `BCE` | 196 | bus/coach station entrance / `RELIEF_SUPPORTING_NODE` |
| `BCQ` | 165 | variable bus/coach bay or stand / `RELIEF_SUPPORTING_NODE` |
| `BCS` | 4,950 | bus/coach station bay or stand / `RELIEF_SUPPORTING_NODE` |
| `BCT` | 416,595 | on-street bus/coach/trolley stop / `RELIEF_SUPPORTING_NODE` |
| `BST` | 40 | bus/coach station access area / `RELIEF_TRANSPORT_PLACE_CANDIDATE` |
| `FBT` | 345 | ferry or port berth / `RELIEF_SUPPORTING_NODE` |
| `FER` | 505 | ferry or port interchange area / `RELIEF_TRANSPORT_PLACE_CANDIDATE` |
| `FTD` | 327 | ferry terminal or dock entrance / `RELIEF_SUPPORTING_NODE` |
| `GAT` | 84 | airport interchange area / `RELIEF_TRANSPORT_PLACE_CANDIDATE` |
| `MET` | 987 | tram/metro/underground interchange / `RELIEF_TRANSPORT_PLACE_CANDIDATE` |
| `PLT` | 1,633 | tram/metro/underground platform / `RELIEF_SUPPORTING_NODE` |
| `RLY` | 2,715 | railway interchange area / `RELIEF_TRANSPORT_PLACE_CANDIDATE` |
| `RPL` | 3 | rail platform / `RELIEF_SUPPORTING_NODE` |
| `RSE` | 4,308 | rail station entrance / `RELIEF_SUPPORTING_NODE` |
| `STR` | 71 | shared taxi rank / `NOT_RELIEF_PLACE_CANDIDATE` |
| `TMU` | 1,519 | tram/metro/underground entrance / `RELIEF_SUPPORTING_NODE` |
| `TXR` | 853 | taxi rank / `NOT_RELIEF_PLACE_CANDIDATE` |

The classification is transport-identity evidence only. It does not authorize creating Relief facilities, toilets, or source links.

## Identifier and geometry model

`ATCOCode` is treated as the publisher-defined stop-point identity and proposed future namespace `naptan:<ATCOCode>`. `NaptanCode`, plate, locality, and administrative codes remain secondary/source fields; none is substituted for ATCOCode. Row position is never an identity. Duplicate publisher identity is a hard reconciliation error, not a deduplication invitation.

Longitude/Latitude are preserved at **`TRANSPORT_STOP_LEVEL`**. Easting/Northing and GridType are retained as source geometry. No source geometry is interpreted as a Relief toilet coordinate. Shared coordinates are recorded as shared transport-node geometry, not evidence of duplicate facilities.

## Hierarchy

The retrieved national CSV does not contain StopArea, StopsInArea, or AreaHierarchy tables. Stop-area counts, orphan membership, multi-parent membership, and interchange topology are therefore **NOT_COMPUTABLE_FROM_THIS_PRODUCT**. N2 must capture the official hierarchy product/API before using hierarchy as a matching signal. No invented grouping is emitted.

## TfL ↔ NaPTAN proof of concept

The frozen TfL station/station-point files were used without refresh. The reconciliation output contains **509** station candidates and is deterministic. Counts:

{
  "AMBIGUOUS": 4,
  "HIGH_CONFIDENCE_NAME_GEO_MATCH": 4,
  "NO_MATCH": 501
}

There was no explicit TfL-to-NaPTAN identifier cross-reference in the frozen cohort. Exact identifier matches are therefore not manufactured. Name/geometry matches are evidence for future review only; multi-node results remain one transport-complex candidate, not multiple Relief facilities.

## Relief dry run

The read-only estimate uses the existing committed production-published facility snapshot. It is not an insertion plan. The machine-readable dry-run artifact reports candidate transport-place matches, ambiguity, supporting-only nodes, and a zero-mutation plan.

## Schema readiness

**SCHEMA_READY_WITH_MINOR_MODEL_GAP.** Existing `facility_sources` and private `facility_source_observations` can preserve future NaPTAN source identity and structured source evidence attached to a canonical facility without canonical overwrite or toilet-unit creation. The current schema does not provide a first-class transport-node/StopArea hierarchy object, so a later additive transport-source model is likely required before ingesting hierarchy as canonical data. No migration is created in N1.

## Future ingestion gates

1. Capture the official national node and hierarchy products with a manifest and immutable hashes.
2. Validate ATCO identity uniqueness, encoding, status, and geometry.
3. Classify source nodes into candidate place, supporting node, excluded, or unresolved.
4. Reconcile exact identity/group evidence before name/geometry matching.
5. Attach source evidence to existing facilities or quarantine; never apply `one row = one facility`.
6. Require explicit authorization for any new canonical transport place, source link, or schema migration.
7. Make repeat ingestion idempotent and fail closed on conflicts.

## RDG compatibility

The proposed identity/hierarchy separation can later accept National Rail/RDG evidence as another source without inventing a direct RDG↔NaPTAN key. RDG integration remains pending; direct cross-reference, hierarchy semantics, and identifier joins are unresolved and must be verified from the future official RDG source.

## Production safety

This batch performed no production write, migration, RPC, staging operation, import run, source-link insertion, facility mutation, or toilet operation. **TOTAL PRODUCTION MUTATIONS: 0.**

## Evidence files

- Source manifest: `NAPTAN_N1_SOURCE_MANIFEST_2026-08-22.json`
- Semantic profile: `NAPTAN_N1_SEMANTIC_PROFILE_2026-08-22.json`
- Stop-type classification: `NAPTAN_N1_STOP_TYPE_CLASSIFICATION_2026-08-22.json`
- TfL reconciliation: `NAPTAN_N1_TFL_RECONCILIATION_2026-08-22.json`
- Relief dry run: `NAPTAN_N1_RELIEF_DRY_RUN_2026-08-22.json`

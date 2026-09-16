# RELIEF Data Growth R4A — Causeway Source Drift Revalidation

**Classification:** `R4A_SOURCE_DRIFT_REVALIDATED`

R4A compared the exact R3 Causeway payload, the R4 drift payload, and a fresh official HTTPS payload. The source oscillated between two byte representations but preserved the same 52 normalized records and all five R3 apply candidates.

## Verified payloads

- R3 sealed payload: `6f320593a8bb8f9734af37724499401b0ee6065bbb35cc475736295ad434ab07` (33341 bytes).
- R4 observed payload: `50eabf55fa58be22bcd09d1f9d0d94a61b17278e7f3434ad832b4df9cb884279` (33341 bytes).
- R4A current payload: `6f320593a8bb8f9734af37724499401b0ee6065bbb35cc475736295ad434ab07` (33341 bytes), HTTP 200, `application/json; charset=utf-8`.
- R4A retrieval UTC: `2026-09-16T12:56:53.8791954Z`.
- All three payloads contain 52 GeoJSON features with stable source identities.

## Semantic result

The R3-to-R4 payload difference was limited to publisher/export metadata (`last_updated` precision and `raw_source_fingerprint`). Names, addresses, postcodes, coordinates, toilet types, accessibility, charge, opening-hours, status, operator, and direct-toilet evidence remained stable. The fresh R4A payload is byte-identical to the R3 sealed payload.

- Causeway R3 candidates examined: **5**.
- Candidate impact: `{"UNCHANGED": 5}`.
- Removed candidates: **0**.
- Ambiguous/review-required candidates: **0**.

## Replacement manifest

The immutable R3 manifest was not overwritten. A new R4 manifest was sealed with the current Causeway hash. It remains a non-authorizing input for a future apply transaction; the next apply must repeat all six source gates.

- Manifest: `docs/data/LOCAL_AUTHORITY_OGL_R4_PRODUCTION_APPLY_MANIFEST_2026-09-16.json`.
- Manifest SHA-256: `0db20d9c6ea254125e5550de94e2303c50f5a3d12a7d4954f34589e30b101685`.
- Automatic candidate count: **89**.
- Review candidates excluded: **7**.
- Production apply authorized: **false**.

## Safety

No production SQL or DML was executed. No facilities, provenance, import records, source rows, schema, or migration state changed.

`R4A_SOURCE_DRIFT_REVALIDATED`

`TOTAL PRODUCTION MUTATIONS: 0`

# RELIEF Data Growth R3 — OGL Pilot Revalidation and Apply Manifest

**Classification:** `PRODUCTION_READ_ONLY`

R3 revalidated the existing Local Authority OGL Pilot 1 + Pilot 2 pool against fresh official HTTPS payloads and a read-only production recheck. No canonical insertion was attempted.

## Result

- Strict pool revalidated: **89** (`CONSERVATIVE_NET_NEW`).
- Review pool preserved but excluded from the apply manifest: **7**.
- Current production nearest-facility identity agreed with the frozen reference for all 89 strict candidates.
- Current production 250 m duplicate guard matched **0** strict candidates.
- Existing selected OGL source provenance rows in production: **0**.
- Production mutations in R3: **0**.
- Apply-manifest content SHA-256: `c9564843ca2f18771fa9ae9c129de4e68feb67d81a4d36464b9d994cb3801e74`.

## Source revalidation

All six selected official resources were fetched into disposable C:\Temp storage over normal TLS. Five payloads are byte-identical to the Pilot 1/Pilot 2 evidence. The current Causeway payload has a new SHA-256 and metadata change, but all 52 stable source identities, names, addresses, postcodes, coordinates, and toilet type values remain unchanged; this is recorded as `PAYLOAD_CHANGED_IDENTITIES_STABLE`, not silently ignored.

## Production safety

- Production project: Relief (`bgwxrxkmyaihplaloely`).
- Production migration head: `20260822170000`.
- Canonical facilities remained at 15,620; facility_sources at 15,634; observations at 14; import_runs at 5; toilet units at 0.
- Source graph remained at 1 / 97,270 / 436,428 / 169,527 / 3,519 rows.
- No `INSERT`, `UPDATE`, `DELETE`, `MERGE`, `TRUNCATE`, DDL, migration, import, provenance, or canonical operation was run.

## Apply-manifest boundary

`LOCAL_AUTHORITY_OGL_R3_PRODUCTION_APPLY_MANIFEST_2026-09-16.json` is a sealed input for a later separately authorized apply transaction. It is not an authorization and contains no execution path. The seven review candidates are excluded; only the 89 strict candidates are listed.

## Required next transaction

A separate production-apply authorization must repeat the source/hash and conflict gates immediately before writing. R3 stops here.

`R3_SOURCE_REVALIDATED_READ_ONLY`

`R3_CANDIDATE_POOL_STABLE`

`R3_PRODUCTION_APPLY_MANIFEST_SEALED`

`R3_CANONICAL_INSERTION_NOT_AUTHORIZED`

`TOTAL PRODUCTION MUTATIONS: 0`

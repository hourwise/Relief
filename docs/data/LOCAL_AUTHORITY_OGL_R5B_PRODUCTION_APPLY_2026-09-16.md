# Relief R5B — Mid Ulster + Dover Production Apply

## Result

`R5B_PRODUCTION_APPLY_COMPLETE`

The exact committed R5B manifest was applied in one bounded transaction to the Relief production project `bgwxrxkmyaihplaloely`.

- Canonical facilities inserted: **23**
- Production facilities: **15,709 → 15,732**
- Facility-source links inserted: **23**
- Governed import/audit rows inserted: **1**
- Review candidates applied: **0**
- Canonical updates: **0**
- Canonical deletes: **0**
- Unrelated production mutations: **0**

## Integrity and authority

- Repository: `hourwise/Relief`
- Execution branch: `codex/toilet-map-apply-1a-production-deploy`
- R5B execution lineage began at the required checkpoint `d144f88ac0269301375fd0c9a506be7571ac5db1`.
- The publication branch included the two authorized generic governed-source audit-contract migrations before data DML.
- Manifest: `docs/data/LOCAL_AUTHORITY_OGL_R5B_PRODUCTION_APPLY_MANIFEST_2026-09-16.json`
- Manifest SHA-256: `76492D8641B40456C6C43401172D61DF7A92B545EEEE9961BFD9FB86EF0B1F9B`
- Manifest candidates: 23 (Mid Ulster 17, Dover 6, review 0)
- R5B manifest seal was unchanged and matched the manifest used by the transaction.
- Sealed N4A migration SHA-256 before/after: `087A389B8CEAC021B12708BC55C39022CB38D5459510EFFB6CF057CEF232C44E`

## Source revalidation and final collision gate

The two R5A-approved sources were byte-identical on revalidation:

| Source | SHA-256 | Bytes | Retained |
| --- | --- | ---: | ---: |
| Mid Ulster District Council public toilets | `927c30cf5d4a4d59bf74d9f21efc340d6848ec6ee77caf6a2852e19287002778` | 13,387 | 17 |
| Dover District Council public toilets | `b872ab5062390a20d6d08301b2327b0e9edd7909ed2267eec54cddcb190ddd68` | 10,106 | 6 |

Final manifest-driven live preflight:

- candidates: 23
- distinct candidate IDs: 23
- distinct source identities: 23
- exact existing source links: 0
- invalid coordinates: 0
- candidate pairs under 10 m: 0
- candidate pairs under 25 m: 0
- review candidates: 0

## Audit contract

The historical `apply_1a` and `apply_r4b` run kinds were not reused. The authorized generic `governed_source_apply` contract was added by the two narrow forward migrations already present in the publication branch:

- `20260916154510_governed_source_apply_audit_contract.sql`
- `20260916160238_fix_governed_source_apply_audit_pattern.sql`

The committed audit row records:

- run kind: `governed_source_apply`
- status: `completed`
- transaction outcome: `committed`
- manifest checksum: `76492d8641b40456c6c43401172d61df7a92b545eeee9961bfd9fb86ef0b1f9b`
- engine: `relief.local-authority-ogl-r5b.v1`
- project ref: `bgwxrxkmyaihplaloely`
- requested/ready/applied: `23 / 23 / 23`
- stale/failed: `0 / 0`
- audit timestamps: `2026-09-16 16:15:04.440783+00` for both database start and completion fields

## Production counts

| Table | Before | After | Delta |
| --- | ---: | ---: | ---: |
| `facilities` | 15,709 | 15,732 | +23 |
| `facility_sources` | 15,723 | 15,746 | +23 |
| `facility_source_observations` | 14 | 14 | 0 |
| `import_runs` | 6 | 7 | +1 |
| `toilet_units` | 0 | 0 | 0 |
| `toilet_unit_sources` | 0 | 0 | 0 |

Per-source provenance inserts: Mid Ulster 17; Dover 6; total 23.

NaPTAN source graph remained unchanged: snapshots 1, places 97,270, nodes 436,428, memberships 169,527, place-parent edges 3,519; total 706,745.

## Post-apply verification and replay

- 23/23 manifest candidates have exactly one intended facility-source link.
- 23/23 link to distinct facilities.
- 23/23 facility names and coordinates exactly match the sealed manifest.
- No duplicate provenance identities were found.
- No review candidate was included or inserted.
- Read-only replay result: `ALREADY_APPLIED`.
- Replay proposed facility inserts: 0; facility-source inserts: 0; import/audit inserts: 0.

Production identity remained Relief / `bgwxrxkmyaihplaloely` / `eu-central-1`, `ACTIVE_HEALTHY`; PostgreSQL `17.6.1.127`, PostGIS `3.3.7`, pgcrypto `1.3`. Source-table RLS remained enabled with zero policies and no direct PUBLIC, anon, or authenticated INSERT privilege. The migration ledger remained at the two R5B audit-contract migrations after N4A; no additional schema change was made during the data apply.

No credentials, raw source downloads, or proprietary source payloads were committed. Rail, NaPTAN expansion, commercial, heritage, and other unrelated work remained out of scope.

**TOTAL AUTHORIZED PRODUCTION INSERTS:** 47 persistent rows in the authorized tables: 23 facilities, 23 facility-source links, and 1 audit row; no other production mutation categories occurred. **UNRELATED PRODUCTION MUTATIONS: 0.**

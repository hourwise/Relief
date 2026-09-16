# Relief R4C — bounded local-authority production apply

Classification: `R4C_PRODUCTION_APPLY_COMPLETE`

## Starting state

- Repository: `hourwise/Relief`
- Branch: `codex/toilet-map-apply-1a-production-deploy`
- Starting commit: `a493998bd9f94443e4f2212521fe0a43b2b627a2`
- Audit-contract commit pushed before production mutation: `ee7fec587740eade90715254b0a1e795d15bee3c`
- Production project: `Relief` / `bgwxrxkmyaihplaloely` / `eu-central-1`
- Production status: `ACTIVE_HEALTHY`
- Protected original checkout was not used for commit, cleanup, or production execution.

## Sealed inputs

- R4 manifest: `docs/data/LOCAL_AUTHORITY_OGL_R4_PRODUCTION_APPLY_MANIFEST_2026-09-16.json`
- R4 manifest SHA-256: `0DB20D9C6EA254125E5550DE94E2303C50F5A3D12A7D4954F34589E30B101685`
- Automatic candidates: `89`
- Review candidates in apply manifest: `0`
- Review candidates excluded: `7`
- Sealed N4A migration SHA-256 before, during, and after: `087A389B8CEAC021B12708BC55C39022CB38D5459510EFFB6CF057CEF232C44E`

## Audit contract decision

The live `import_runs_apply_1a_committed_check` proved that `run_kind='apply_1a'` is a narrow historical 48-operation Apply 1A contract. It requires the original Apply 1A identity, 48 requested/ready/applied operations, zero stale/failed operations, and a completed committed outcome. Five historical rows confirmed that meaning. Reusing `apply_1a` for this 89-candidate source expansion would have been false.

The smallest truthful correction was one forward migration:

`supabase/migrations/20260916140000_r4b_audit_contract.sql`

Migration SHA-256: `911C7E1F3794A403200D1BB81CFD43885F9A84FD4E6D91C4EE85233EF98F3E92`.

It preserves the exact Apply 1A committed branch, adds only the exact `apply_r4b` 89-operation committed branch, extends the run-kind allowlist, and adds an R4B identity check bound to the sealed manifest, project ref, and apply engine. A disposable contract probe accepted a valid R4B committed row and rejected an arbitrary committed run kind. The live migration ledger recorded the pushed migration name under execution version `20260916134537`.

## Pre-apply production state

| Table | Before |
| --- | ---: |
| `facilities` | 15,620 |
| `facility_sources` | 15,634 |
| `facility_source_observations` | 14 |
| `import_runs` | 5 |
| `toilet_units` | 0 |
| `toilet_unit_sources` | 0 |
| NaPTAN source graph total | 706,745 |

Project runtime was PostgreSQL `17.6.1.127`, PostGIS `3.3.7`, and pgcrypto `1.3`.

The 89-candidate collision preflight remained clean: 89 candidates, 89 distinct source identities, zero existing exact source links, zero candidate conflicts, zero review candidates, and zero facilities within the governed 250 m overlap guard.

## Apply transaction

The first one-transaction attempt was rejected because `facilities.location` is a generated column. It rolled back completely; read-only counts immediately afterward remained at 15,620 / 15,634 / 14 / 5, with zero R4B audit rows.

The corrected retry omitted the generated column and committed one bounded transaction containing only the sealed 89-candidate manifest, its 89 provenance links, and one truthful `apply_r4b` audit row. The audit row recorded `source_name='Local Authority OGL R4B'`, the sealed manifest checksum in the manifest/checksum fields, `relief.local-authority-ogl-r4b.v1`, project ref `bgwxrxkmyaihplaloely`, 89 requested/ready/applied, zero stale/failed, status `completed`, and outcome `committed`.

Rows inserted by source group were: Adur 15, Causeway Coast and Glens 5, City of York 4, Perth & Kinross 41, and Worthing 24. Belfast was not represented in this 89-row manifest.

## Post-apply verification

| Table | Before | After | Delta |
| --- | ---: | ---: | ---: |
| `facilities` | 15,620 | 15,709 | +89 |
| `facility_sources` | 15,634 | 15,723 | +89 |
| `facility_source_observations` | 14 | 14 | 0 |
| `import_runs` | 5 | 6 | +1 |
| `toilet_units` | 0 | 0 | 0 |
| `toilet_unit_sources` | 0 | 0 | 0 |
| NaPTAN source graph total | 706,745 | 706,745 | 0 |

All `89 / 89` manifest candidates have exactly one intended canonical facility and one matching `facility_sources` row. There are zero missing links, zero name/coordinate mismatches, 89 distinct inserted facilities, and one matching committed R4B audit row. A read-only replay of the sealed manifest classified the set as `ALREADY_APPLIED` with zero proposed facilities, provenance links, or audit rows.

Post-apply security inspection found all five NaPTAN tables still RLS-enabled, with zero policies, no direct PUBLIC/anon/authenticated insert privileges, and service-role insert privilege only. PostGIS remained active. The N4A migration remained byte-for-byte unchanged.

## Production safety and accounting

- Canonical facility inserts: `89`
- Facility-source inserts: `89`
- Import/audit rows: `1`
- Canonical facility updates: `0`
- Canonical facility deletes: `0`
- Facility-source-observation mutations: `0`
- Toilet-unit mutations: `0`
- Toilet-unit-source mutations: `0`
- NaPTAN source-graph mutations: `0`
- Rail work, ingestion, review-candidate insertion, Auth changes, and unrelated-table mutations: `0`
- Authorized audit-contract schema mutations: `1`

No Rail R1 work, NaPTAN ingestion, review-candidate apply, source re-fetch, or unrelated production operation was performed.

## Evidence

- `docs/data/LOCAL_AUTHORITY_OGL_R4C_PRODUCTION_APPLY_RESULT_2026-09-16.json`
- `docs/data/LOCAL_AUTHORITY_OGL_R4C_PRODUCTION_POSTVERIFY_2026-09-16.json`

No credentials or raw source downloads are included.

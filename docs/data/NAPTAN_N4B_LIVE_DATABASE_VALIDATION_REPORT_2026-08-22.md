# Relief NaPTAN N4B — live database validation report

Status: LIVE_DATABASE_VALIDATION_PASSED

This is a bounded disposable PostgreSQL/PostGIS validation record. It is not a
production deployment and does not authorize N4C.

## STARTING STATE

- Repository: hourwise/Relief
- Branch: codex/toilet-map-apply-1a-production-deploy
- Starting local and remote SHA: 8627dbfd586df9069b2f73b0cc2d6543645fa950
- git fetch origin was blocked only by the known local .git/FETCH_HEAD permission error; git ls-remote verified the same remote SHA.
- Protected .easignore, app.json, and docs/EAS_CONFIG_AUDIT.md remained untouched, unstaged, and uncommitted.
- Sealed migration SHA-256: 087A389B8CEAC021B12708BC55C39022CB38D5459510EFFB6CF057CEF232C44E

## HISTORICAL APPLY 1A PREREQUISITE

The old blocker was the exact-zero qualifying committed Apply 1A
public.import_runs row count at the historical seal migration. The seal also
requires the exact 48-row private.relief_apply_1a_approved_operations registry.

The state was proven reproducible from committed Apply 1A migration, fixture,
seed, post-check fault, tests, manifest, plan, and sealing-evidence artifacts.
The CI-only bootstrap under tools/enrichment/n4b_historical_apply_1a_bootstrap.sql
reconstructed that state in a fresh database:

- canonical prefix ended at 20260812124351_apply_1a_facilities_update_rls.sql;
- bootstrap ran before 20260812190246_seal_apply_1a_execution_path.sql;
- exactly 48 registry rows and one qualifying import run were created;
- the existing rollback/commit historical Apply 1A behavior was exercised;
- canonical migration replay resumed with the seal and skipped no migration.

No production access or guessed data was used.

## HOSTED EXECUTION

Final run: https://github.com/hourwise/Relief/actions/runs/32590319699
Job: 97073021827
Artifact: https://github.com/hourwise/Relief/actions/runs/32590319699/artifacts/9480182011
Artifact digest: sha256:6bf987cec5f574480b58059f94c5997f7a8635b6664e4b0cba87eadba80e194a

The run used Ubuntu 24.04.4 LTS, Supabase CLI 2.75.0, PostgreSQL server
17.6, PostGIS 3.3.7, Node 22.22.2, and Python 3.12.14. The sealed N4A
migration executed unchanged and its SHA remained exact.

## LIVE ASSERTIONS

tools/source_expansion/naptan_n4b_live_validation.sql returned
N4B_LIVE_SQL_ASSERTIONS_PASSED. Live checks covered schema catalogs, columns,
generated geography, keys, foreign keys, same-snapshot and cross-snapshot
relationships, unique duplicate protection, invalid coordinates, indexes,
five update triggers and trigger behavior, RLS/policies/grants, PostGIS
geography, hierarchy fixtures, unresolved references, rollback, replay, and
idempotency.

Role checks in the disposable database were:

- anon: DENIED
- authenticated: DENIED
- service_role: READ_AND_ROLLBACK_WRITE

## OTHER VALIDATION

- N4A Python suite: 14 passed, 0 failed.
- Python compilation: passed.
- TypeScript tsc --noEmit: passed.
- JS/TS harness: 24 test files passed, 0 failed.
- Lint: 0 errors, 81 warnings; no application files were changed.

## SAFETY

No production credentials, production database connection, production SQL,
remote migration, ingestion, canonical facility mutation, source observation
mutation, toilet-unit mutation, source promotion, N3 refresh, national XML
download, production grant/RLS/policy change, or N4C operation was performed.

TOTAL PRODUCTION MUTATIONS: 0

## CLASSIFICATION

LIVE_DATABASE_VALIDATION_PASSED

N4B_VALIDATION_PASSED

N4C_AWAITING_SEPARATE_AUTHORIZATION

TOTAL PRODUCTION MUTATIONS: 0


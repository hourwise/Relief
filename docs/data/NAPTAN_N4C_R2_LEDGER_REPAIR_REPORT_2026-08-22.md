# Relief N4C-R2 — Supabase Migration Ledger Repair and N4A Isolation

## FINAL CLASSIFICATIONS

`ONLY_N4A_PENDING_PROVEN`

`N4C_PRODUCTION_SCHEMA_APPLY_READY_FOR_SEPARATE_AUTHORIZATION`

`MIGRATION LEDGER METADATA REPAIR: PERFORMED`

`TOTAL PRODUCTION SCHEMA MUTATIONS: 0`

`TOTAL PRODUCTION APPLICATION-DATA MUTATIONS: 0`

`TOTAL AUTH MUTATIONS: 0`

`TOTAL NAPTAN INGESTION ROWS: 0`

N4A was not applied. NaPTAN ingestion and N5 were not started.

## STARTING STATE

- Repository: `hourwise/Relief`
- Branch: `codex/toilet-map-apply-1a-production-deploy`
- Starting local SHA: `975a1f9539c5b2a14d63f0abbc28b2b11f16cfb4`
- Starting remote SHA: `975a1f9539c5b2a14d63f0abbc28b2b11f16cfb4`
- `git fetch origin`: passed
- `git ls-remote`: matched the required SHA
- No staged files at start
- Protected files remained untouched, unstaged, and uncommitted
- Previous N4C, N4C-R1, and N4C-R1A evidence was preserved

## SEALED N4A

- Path: `supabase/migrations/20260822170000_naptan_transport_source_graph.sql`
- Required SHA-256: `087A389B8CEAC021B12708BC55C39022CB38D5459510EFFB6CF057CEF232C44E`
- Starting SHA: exact match
- SHA immediately before repair: exact match
- SHA immediately before dry-run: exact match
- Final SHA: exact match
- Status: not applied and not marked applied

## PRODUCTION PROJECT

Read-only project identity confirmation:

- Project: `Relief`
- Ref: `bgwxrxkmyaihplaloely`
- Status: `ACTIVE_HEALTHY`
- Region: `eu-central-1`
- PostgreSQL: `17.6`
- PostGIS: `3.3.7`
- pgcrypto: `1.3`
- Supabase CLI: `2.75.0`

No credentials, passwords, service-role keys, access tokens, or connection strings were recorded.

## PRE-REPAIR MIGRATION STATE

Production ledger before repair contained 17 rows with head `20260822100920`.

Production-only aliases:

```text
20260814115817
20260816210130
20260817062603
20260821213435
20260822100920
```

Local equivalents:

```text
20260814113440
20260816205543
20260816220000
20260821211239
20260822092938
```

The canonical account migration `20260814135046` was already aligned. N4A `20260822170000` was present locally, absent from production, and its target tables were absent.

## REPAIR-PLAN VALIDATION

Validated artifact:

`docs/data/NAPTAN_N4C_R1A_FUTURE_LEDGER_REPAIR_PLAN_2026-08-22.json`

Validation passed:

- exactly 10 operations;
- all operations belong to the five approved high-confidence pairs;
- N4A excluded;
- account v2 excluded;
- no unknown versions;
- expected schema delta `0`;
- expected application-data delta `0`;
- source plan contained no executable commands.

The installed CLI supports the executed form:

```text
supabase migration repair [version] --status [applied|reverted] --linked --yes
```

## PRE-REPAIR DRY RUN

Command:

```text
supabase db push --dry-run --linked
```

Result was the expected known five-alias block:

```text
Remote migration versions not found in local migrations directory.

Make sure your local git repo is up-to-date. If the error persists, try repairing the migration history table:
supabase migration repair --status reverted 20260814115817 20260816210130 20260817062603 20260821213435 20260822100920
```

No dry-run migration was applied.

## PRODUCTION PRE-REPAIR BASELINE

Read-only counts:

| Table | Count |
|---|---:|
| `facilities` | 15,620 |
| `facility_sources` | 15,634 |
| `facility_source_observations` | 14 |
| `import_runs` | 5 |
| `toilet_map_import_staging` | 0 |
| `toilet_units` | 0 |
| `toilet_unit_sources` | 0 |

N4A transport tables were absent. PostgreSQL, PostGIS, RLS, policy, and account-function fingerprints matched the established N4C-R1A baseline.

## LEDGER REPAIR EXECUTION

All ten authorized operations succeeded with exit code `0`:

| Seq. | Version | Status | Equivalent | Result |
|---:|---|---|---|---|
| 1 | `20260814115817` | reverted | `20260814113440` | success |
| 2 | `20260814113440` | applied | `20260814115817` | success |
| 3 | `20260816210130` | reverted | `20260816205543` | success |
| 4 | `20260816205543` | applied | `20260816210130` | success |
| 5 | `20260817062603` | reverted | `20260816220000` | success |
| 6 | `20260816220000` | applied | `20260817062603` | success |
| 7 | `20260821213435` | reverted | `20260821211239` | success |
| 8 | `20260821211239` | applied | `20260821213435` | success |
| 9 | `20260822100920` | reverted | `20260822092938` | success |
| 10 | `20260822092938` | applied | `20260822100920` | success |

No historical migration SQL ran. No tables, functions, triggers, grants, policies, RLS rules, or application rows were intentionally executed or recreated.

## POST-REPAIR LEDGER

The post-repair ledger contains 17 rows with head `20260822092938`.

All local historical migrations through `20260822092938` now align with production. The only local-only migration is:

```text
20260822170000_naptan_transport_source_graph.sql
```

N4A remains absent from the production ledger.

## LEDGER DIFF

Only the ten authorized metadata transitions occurred: five production deployment timestamps were reverted and five proven local equivalents were marked applied. The account migration `20260814135046` and all earlier migrations were unchanged. The ledger row count remained 17.

## SCHEMA IMMUTABILITY

- Schema mutations: `0`
- N4A tables before: absent
- N4A tables after: absent
- PostgreSQL before/after: `17.6`
- PostGIS before/after: `3.3.7`
- pgcrypto before/after: `1.3`
- Historical migration SQL rerun: no
- N4A SQL executed: no

## APPLICATION-DATA IMMUTABILITY

Before and after counts were identical:

| Table | Before | After | Delta |
|---|---:|---:|---:|
| `facilities` | 15,620 | 15,620 | 0 |
| `facility_sources` | 15,634 | 15,634 | 0 |
| `facility_source_observations` | 14 | 14 | 0 |
| `import_runs` | 5 | 5 | 0 |
| `toilet_map_import_staging` | 0 | 0 | 0 |
| `toilet_units` | 0 | 0 | 0 |
| `toilet_unit_sources` | 0 | 0 | 0 |

No Auth operation, canonical-facility mutation, source-observation mutation, toilet-unit mutation, or NaPTAN insertion occurred.

## SECURITY IMMUTABILITY

Read-only before/after verification found:

- RLS remained enabled on the audited tables;
- audited policies were unchanged;
- account function definitions remained unchanged;
- account functions remained `SECURITY DEFINER` with empty `search_path`;
- `anon` remained denied execution of the account functions;
- `authenticated` retained execution;
- audited source-table service-role boundaries remained unchanged;
- no public API, Auth, role, grant, or policy mutation command was executed.

## POST-REPAIR REAL DRY RUN

Command:

```text
supabase db push --dry-run --linked
```

Exit code: `0`

Exact pending migration output:

```text
DRY RUN: migrations will *not* be pushed to the database.
Would push these migrations:
 • 20260822170000_naptan_transport_source_graph.sql
Finished supabase db push.
```

No other migration was proposed.

## N4A ISOLATION

`ONLY_N4A_PENDING_PROVEN`

The real supported Supabase dry-run proves that exactly the sealed N4A migration is pending.

## PRODUCTION MUTATION ACCOUNTING

Authorized operation:

`MIGRATION LEDGER METADATA REPAIR: PERFORMED`

Prohibited mutations:

- `TOTAL PRODUCTION SCHEMA MUTATIONS: 0`
- `TOTAL PRODUCTION APPLICATION-DATA MUTATIONS: 0`
- `TOTAL AUTH MUTATIONS: 0`
- `TOTAL NAPTAN INGESTION ROWS: 0`
- canonical facility mutations: `0`
- source-observation mutations: `0`
- toilet-unit mutations: `0`

The ledger metadata mutation is reported separately from schema and application-data mutation counts.

## VALIDATION

- Repair-plan JSON: passed.
- Alias scope guard: passed.
- Ten repair operations: passed, 10/10 exit code 0.
- Post-repair ledger inventory: passed.
- Local/remote alignment: passed except sealed N4A.
- Real post-repair dry-run: passed, exactly N4A pending.
- N4A hash: passed at all required checkpoints.
- Schema immutability: passed.
- Application-data immutability: passed.
- Security immutability: passed for audited RLS, policies, functions, and service-role boundaries.
- JSON invariant validator: passed.
- `git diff --check`: passed with only pre-existing protected-file line-ending warnings.
- Secret scan: no credential-bearing patterns found.
- No raw NaPTAN XML, database dump, or generated credential was created.

## FILES CREATED OR MODIFIED

New N4C-R2 evidence files:

- `docs/data/NAPTAN_N4C_R2_LEDGER_REPAIR_REPORT_2026-08-22.md`
- `docs/data/NAPTAN_N4C_R2_PRE_REPAIR_LEDGER_2026-08-22.json`
- `docs/data/NAPTAN_N4C_R2_REPAIR_COMMANDS_2026-08-22.json`
- `docs/data/NAPTAN_N4C_R2_EXECUTION_EVIDENCE_2026-08-22.json`
- `docs/data/NAPTAN_N4C_R2_POST_REPAIR_LEDGER_2026-08-22.json`
- `docs/data/NAPTAN_N4C_R2_LEDGER_DIFF_2026-08-22.json`
- `docs/data/NAPTAN_N4C_R2_PRODUCTION_IMMUTABILITY_2026-08-22.json`
- `docs/data/NAPTAN_N4C_R2_SECURITY_IMMUTABILITY_2026-08-22.json`
- `docs/data/NAPTAN_N4C_R2_DRY_RUN_EVIDENCE_2026-08-22.json`
- `docs/data/NAPTAN_N4C_R2_N4A_ISOLATION_2026-08-22.json`
- `docs/data/NAPTAN_N4C_R2_READINESS_2026-08-22.json`
- `tools/source_expansion/naptan_n4c_r2_validate.py`

No prior N4C, N4C-R1, or N4C-R1A evidence was rewritten.

## GIT RESULT

The N4C-R2 evidence was committed and pushed normally. Protected files were not staged.

- Commit A: `a0e0788d44ef30555502ca173cd6b0195d6dd5bf`
- Push: passed normally to `origin/codex/toilet-map-apply-1a-production-deploy`
- No amend, force-push, merge, rebase, reset, cherry-pick, or migration apply occurred.

## N4C READINESS

`N4C_PRODUCTION_SCHEMA_APPLY_READY_FOR_SEPARATE_AUTHORIZATION`

This is a readiness result only. It does not authorize N4C or N5.

## FINAL CLASSIFICATION

`RELIEF N4C-R2 — MIGRATION LEDGER REPAIRED / ONLY N4A PENDING PROVEN / N4C PRODUCTION SCHEMA APPLY READY FOR SEPARATE AUTHORIZATION / SCHEMA AND APPLICATION-DATA MUTATIONS 0`

N4A remains unapplied. NaPTAN source-graph ingestion and N5 remain unauthorized.

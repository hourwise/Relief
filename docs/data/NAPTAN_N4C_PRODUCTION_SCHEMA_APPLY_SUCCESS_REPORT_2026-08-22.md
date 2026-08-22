# Relief N4C — Sealed NaPTAN Transport Source Graph Production Schema Apply

## FINAL CLASSIFICATION

`RELIEF N4C — N4A SOURCE GRAPH SCHEMA DEPLOYED / SOURCE GRAPH EMPTY / SECURITY VERIFIED / MIGRATION CHAIN SYNCHRONIZED / N5 READY FOR SEPARATE AUTHORIZATION`

- `N4A_SCHEMA_DEPLOYED`
- `SOURCE_GRAPH_SECURITY_VERIFIED`
- `SOURCE_GRAPH_SCHEMA_EMPTY`
- `MIGRATION_CHAIN_SYNCHRONIZED`
- `N5_SOURCE_GRAPH_INGESTION_READY_FOR_SEPARATE_AUTHORIZATION`

`AUTHORIZED SCHEMA MIGRATION: 20260822170000`

`TOTAL NAPTAN INGESTION ROWS: 0`

`TOTAL CANONICAL FACILITY MUTATIONS: 0`

`TOTAL APPLICATION-DATA MUTATIONS: 0`

`TOTAL AUTH MUTATIONS: 0`

`TOTAL TOILET-UNIT MUTATIONS: 0`

No N5 work or NaPTAN ingestion was performed.

## STARTING STATE

- Repository: `hourwise/Relief`
- Branch: `codex/toilet-map-apply-1a-production-deploy`
- Starting local SHA: `16e29c6530cf8f763d9c7614c99db1c6b2a765ab`
- Starting remote SHA: `16e29c6530cf8f763d9c7614c99db1c6b2a765ab`
- `git fetch origin`: passed
- Independent remote check: `git ls-remote origin`, matched exactly
- Protected files remained untouched, unstaged, and uncommitted
- Earlier blocked N4C, N4C-R1, N4C-R1A, and N4C-R2 evidence was preserved

## SEALED MIGRATION

- Path: `supabase/migrations/20260822170000_naptan_transport_source_graph.sql`
- Expected SHA-256: `087A389B8CEAC021B12708BC55C39022CB38D5459510EFFB6CF057CEF232C44E`
- Batch-start SHA: exact match
- Pre-dry-run SHA: exact match
- Immediately-before-apply SHA: exact match
- Immediately-after-apply SHA: exact match
- Final pre-commit SHA: exact match
- Byte-for-byte unchanged: confirmed

## PRODUCTION PROJECT

- Project: `Relief`
- Ref: `bgwxrxkmyaihplaloely`
- Organization: `dlvnqpwxnsirmpvtlkaj`
- Status: `ACTIVE_HEALTHY`
- Region: `eu-central-1`
- PostgreSQL: `17.6`
- PostGIS: `3.3.7`
- pgcrypto: `1.3`
- Supabase CLI: `2.75.0`

No secret, password, service-role key, access token, or connection string was recorded.

## PRE-APPLY MIGRATION STATE

- Pre-apply production head: `20260822092938`
- N4A `20260822170000`: absent
- Account migration `20260814135046`: aligned
- Historical aliases: reconciled by N4C-R2
- Five target tables: absent

## PRE-APPLY COUNTS

| Table | Before |
|---|---:|
| `facilities` | 15,620 |
| `facility_sources` | 15,634 |
| `facility_source_observations` | 14 |
| `import_runs` | 5 |
| `toilet_map_import_staging` | 0 |
| `toilet_units` | 0 |
| `toilet_unit_sources` | 0 |

## PRE-APPLY DRY RUN

Command:

```text
supabase db push --dry-run --linked
```

Exit code: `0`.

Exactly one migration was proposed:

```text
20260822170000_naptan_transport_source_graph.sql
```

No `--include-all`, repair command, manual SQL, or additional migration was used.

## PRODUCTION APPLY

Command:

```text
supabase db push --linked
```

- Start UTC: `2026-08-22T21:32:56.8981314Z`
- End UTC: `2026-08-22T21:33:31.2017451Z`
- Exit code: `0`
- CLI result: `Applying migration 20260822170000_naptan_transport_source_graph.sql...`
- Additional migrations applied: none

## POST-APPLY LEDGER

- N4A version `20260822170000`: present exactly once
- Migration name: `naptan_transport_source_graph`
- Final production head: `20260822170000`
- Ledger order: canonical

## TABLES CREATED

All five expected tables exist:

1. `public.transport_source_snapshots`
2. `public.transport_source_places`
3. `public.transport_source_nodes`
4. `public.transport_source_memberships`
5. `public.transport_source_place_parents`

## LIVE SCHEMA VERIFICATION

Catalog verification matched the sealed migration:

| Table | Columns | Keyed constraints | Checks | Indexes | Triggers | RLS | Policies |
|---|---:|---:|---:|---:|---:|---|---:|
| `transport_source_snapshots` | 19 | 3 | 26 | 4 | 1 | enabled | 0 |
| `transport_source_places` | 18 | 4 | 19 | 6 | 1 | enabled | 0 |
| `transport_source_nodes` | 17 | 4 | 18 | 7 | 1 | enabled | 0 |
| `transport_source_memberships` | 12 | 5 | 17 | 5 | 1 | enabled | 0 |
| `transport_source_place_parents` | 12 | 5 | 17 | 5 | 1 | enabled | 0 |

Verified:

- primary keys and expected unique identity keys;
- snapshot foreign keys;
- composite same-snapshot foreign keys for memberships and parent edges;
- source identity, coordinate-range, lifecycle, JSON-object, resolution, and duplicate-count checks;
- partial GiST geography indexes and required B-tree indexes;
- one `BEFORE UPDATE` trigger per table invoking `update_updated_at()`;
- generated `public.geography(Point,4326)` publisher locations on places and nodes;
- no normalized-complex table was created.

## RLS / SECURITY

For all five source-graph tables:

- RLS: enabled;
- force RLS: false;
- policies: zero;
- direct `PUBLIC` privileges: none;
- direct `anon` privileges: none;
- direct `authenticated` privileges: none;
- `service_role`: governed table privileges from the migration;
- no public RPC, view, or source-graph API route was created by N4A.

Existing audited facilities/source/toilet RLS and policies remained unchanged. Existing account-deletion function fingerprints remained unchanged.

The read-only inventory also surfaced the pre-existing Supabase advisory that `public.spatial_ref_sys` has RLS disabled. This is an existing PostGIS system-table condition, not an N4A source-graph table and not changed by this deployment; no remediation was attempted within this bounded transaction.

## SOURCE GRAPH ROW COUNTS

| Table | After |
|---|---:|
| `transport_source_snapshots` | 0 |
| `transport_source_places` | 0 |
| `transport_source_nodes` | 0 |
| `transport_source_memberships` | 0 |
| `transport_source_place_parents` | 0 |

`NAPTAN SOURCE GRAPH ROWS: 0`

## APPLICATION-DATA IMMUTABILITY

| Table | Before | After | Delta |
|---|---:|---:|---:|
| `facilities` | 15,620 | 15,620 | 0 |
| `facility_sources` | 15,634 | 15,634 | 0 |
| `facility_source_observations` | 14 | 14 | 0 |
| `import_runs` | 5 | 5 | 0 |
| `toilet_map_import_staging` | 0 | 0 | 0 |
| `toilet_units` | 0 | 0 | 0 |
| `toilet_unit_sources` | 0 | 0 | 0 |

## AUTH / SECURITY IMMUTABILITY

No Auth API, user mutation, account-deletion invocation, role mutation, or application DML was performed. Existing account function definition fingerprints remained:

- `check_my_account_deletion_subscription_guard()`: `ba7d5db93a5f1225a5397e760ef50403`
- `delete_my_account_data()`: `0e1dc846cd3f16c773e3b76aec5f2bcb`

## POST-DEPLOY DRY RUN

Command:

```text
supabase db push --dry-run --linked
```

Exit code: `0`.

Result:

```text
Remote database is up to date.
```

`MIGRATION_CHAIN_SYNCHRONIZED`

## PRODUCTION MUTATION ACCOUNTING

- Authorized production schema mutation: application of N4A `20260822170000`
- Migration-history repair operations during N4C: `0`
- Total NaPTAN ingestion rows: `0`
- Total canonical facility mutations: `0`
- Total application-data mutations: `0`
- Total Auth mutations: `0`
- Total toilet-unit mutations: `0`
- Total TfL observation mutations: `0`

## VALIDATION

- sealed SHA checks: passed at all required checkpoints;
- project identity and health: passed;
- pre-apply ledger and dry-run gates: passed;
- migration execution: passed, exactly one migration;
- post-apply ledger: passed, N4A exactly once and head;
- five target tables: passed;
- columns, defaults, nullability, generated geography: passed;
- primary/unique/foreign/check constraints: passed;
- indexes including partial GiST indexes: passed;
- triggers: passed;
- RLS and zero-policy source-graph security: passed;
- grants: passed, service-role only;
- source-graph rows: passed, all zero;
- existing application counts: passed, all deltas zero;
- PostGIS and PostgreSQL runtime: passed;
- post-deploy dry-run: passed, no pending migrations;
- no N5, ingestion, canonical reconciliation, or toilet work: confirmed.

## FILES CREATED

New success evidence was created separately from earlier reports:

- `NAPTAN_N4C_PRODUCTION_SCHEMA_APPLY_SUCCESS_REPORT_2026-08-22.md`
- `NAPTAN_N4C_PRODUCTION_SCHEMA_APPLY_SUCCESS_EVIDENCE_2026-08-22.json`
- `NAPTAN_N4C_SUCCESS_PRE_APPLY_DRY_RUN_2026-08-22.json`
- `NAPTAN_N4C_SUCCESS_MIGRATION_EXECUTION_2026-08-22.json`
- `NAPTAN_N4C_SUCCESS_LEDGER_VERIFICATION_2026-08-22.json`
- `NAPTAN_N4C_SUCCESS_SCHEMA_INTROSPECTION_2026-08-22.json`
- `NAPTAN_N4C_SUCCESS_SECURITY_VERIFICATION_2026-08-22.json`
- `NAPTAN_N4C_SUCCESS_DATA_IMMUTABILITY_2026-08-22.json`
- `NAPTAN_N4C_SUCCESS_SOURCE_GRAPH_EMPTY_2026-08-22.json`
- `NAPTAN_N4C_SUCCESS_POST_DEPLOY_DRY_RUN_2026-08-22.json`
- `NAPTAN_N4C_SUCCESS_N5_READINESS_2026-08-22.json`

No raw NaPTAN XML, secrets, credentials, or source data was created or committed. The sealed migration was unchanged.

## GIT RESULT

The success evidence was committed and pushed normally after staged-diff, protected-file, secret-scan, and final-hash checks.

- Evidence commit: `6c334d1cb81b50cf427882a4761f0c7b4adb0806`
- Push: passed normally to `origin/codex/toilet-map-apply-1a-production-deploy`
- No amend, force-push, merge, rebase, reset, cherry-pick, or second migration apply occurred.
- Earlier evidence remains untouched.

## N5 READINESS

`N5_SOURCE_GRAPH_INGESTION_READY_FOR_SEPARATE_AUTHORIZATION`

This is a readiness classification only. It does not authorize N5 ingestion.

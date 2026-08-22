# Relief N4C-R1A — Account-Deletion Migration Variant Recovery

## FINAL CLASSIFICATIONS

`PRODUCTION_ACCOUNT_MIGRATION_EXACTLY_RECOVERED`

`LOCAL_V1_SUPERSEDED_BY_PRODUCTION_V2`

`REPOSITORY_MIGRATION_HISTORY_CANONICALISED`

`ONLY_N4A_PENDING_AFTER_LEDGER_REPAIR`

`N4C_R2_LEDGER_REPAIR_READY_FOR_SEPARATE_AUTHORIZATION`

`TOTAL PRODUCTION MUTATIONS: 0`

`TOTAL MIGRATION LEDGER MUTATIONS: 0`

`TOTAL NAPTAN INGESTION ROWS: 0`

No production schema, data, Auth, RLS, grant, policy, or migration-ledger change was performed. N4A was not applied and N5 was not started.

## STARTING STATE

- Repository: `hourwise/Relief`
- Branch: `codex/toilet-map-apply-1a-production-deploy`
- Local SHA: `f444d2b34ad9acd8d330786d776cc03832ed6f93`
- Remote SHA: `f444d2b34ad9acd8d330786d776cc03832ed6f93`
- `git fetch origin`: passed
- `git ls-remote`: matched the required remote SHA
- `git diff --check`: passed, with only the pre-existing LF/CRLF warnings on protected files
- No staged files before this batch

The protected files and prior blocked N4C evidence were preserved. The N4C-R1 forensic artifacts remain available and were not silently replaced.

## SEALED N4A

- Path: `supabase/migrations/20260822170000_naptan_transport_source_graph.sql`
- Required SHA-256: `087A389B8CEAC021B12708BC55C39022CB38D5459510EFFB6CF057CEF232C44E`
- Actual SHA-256: `087A389B8CEAC021B12708BC55C39022CB38D5459510EFFB6CF057CEF232C44E`
- Status: unchanged and not applied

## PREVIOUS EVIDENCE PRESERVATION

Original blocked N4C evidence remained unchanged:

- Report SHA-256: `C9E826C845F53A4D72EC96B03CF9C1F9049243ED2691B9CB32B737EE3C3E6740`
- Evidence JSON SHA-256: `6ABB7F432CA1A470EBDEB9CDF80AB92DA357E5943A84D8F2AE593EEE93C7CB54`

The earlier N4C-R1 artifacts remain unmodified. Their account-pair conclusion is superseded by this separately documented recovery result, not erased.

## PRODUCTION PROJECT

Read-only identity confirmation:

- Project: `Relief`
- Project ref: `bgwxrxkmyaihplaloely`
- Status: `ACTIVE_HEALTHY`
- Region: `eu-central-1`
- PostgreSQL: `17.6`
- PostGIS: `3.3.7`
- pgcrypto: `1.3`
- Supabase CLI: `2.75.0`

No credentials were printed, persisted, uploaded, or committed.

## PRODUCTION ACCOUNT MIGRATION RECOVERY

Production ledger row:

- Version: `20260814135046`
- Name: `account_deletion_cleanup_contract`
- Statement count: `1`
- Source: read-only `supabase_migrations.schema_migrations.statements`
- Statement bytes: `7025`
- Statement MD5: `86accd93b46b873626465a9025e7d33c`
- Statement SHA-256: `432d61cc4784f741d9c09c3a905cdd84a9d17244dfb5231fd87e3a8a4c32df0a`

The recovered statement was not executed. A deterministic byte comparison showed that the production statement is the local migration body with only the successful-cleanup literal changed from `20260814.1` to `20260814.2`, with the production ledger omitting the repository terminal newline.

The active repository file is:

`supabase/migrations/20260814135046_account_deletion_cleanup_contract.sql`

Its SQL body fingerprint, excluding the conventional terminal newline, matches the production statement exactly. The repository file SHA including its terminal newline is `5E432EEB7DC2DA9A1A3F2FE6072FCAC6E637E67216496C79BA355694370C5B23`.

## V1 ↔ V2 SEMANTIC DIFF

One material difference was found:

- Local successful eligible-account cleanup returns `contract_version = 20260814.1`.
- Production successful eligible-account cleanup returns `contract_version = 20260814.2`.

The following behavior is otherwise equivalent:

- subscription-history guard and fail-closed response;
- guard-before-cleanup ordering;
- reviewer, reporter, and creator anonymisation;
- owned-row deletion ordering;
- retention safeguard for subscription/payment history;
- `SECURITY DEFINER` and empty `search_path`;
- exception and transaction behavior;
- anonymous/public execute revocations and authenticated execute grants.

The difference is observable contract metadata. Replaying local v1 after production v2 would replace the production function definition with the stale success label, so the local v1 was not safe to leave executable.

## HISTORICAL LINEAGE

`LOCAL_V1_SUPERSEDED_BY_PRODUCTION_V2`

Confidence: HIGH.

Git history shows:

1. `319cafaf539b8caec1741f059d7ebc918861ee7a` created the original v1 contract.
2. `04fac791e1bd3a05ac6d91460bcae6bb51f11a6f` added the subscription guard and blocked v2 response, but retained the v1 success label.
3. Production contains one account migration row whose exact SQL uses v2 for the successful path.

No separate production follow-up row exists. No exact v2 migration file was found in reachable or inspected unreachable Git objects. The production ledger is therefore the authoritative source for the recovered v2 body.

## CURRENT INTENDED ACCOUNT-DELETION CONTRACT

The current intended contract is v2:

- production is authoritative and returns v2;
- the current Edge Function does not depend on the stale v1 label;
- current documentation describes the guarded deletion path as deployed;
- current tests validate the guard, cleanup ordering, identity derivation, and Auth sequencing rather than v1 metadata.

No application behavior was redesigned.

## REPOSITORY CANONICALISATION DECISION

Repository-only canonicalisation was safe and completed:

- removed executable local v1: `supabase/migrations/20260814124706_account_deletion_cleanup_contract.sql`;
- added exact production-version body: `supabase/migrations/20260814135046_account_deletion_cleanup_contract.sql`;
- preserved the old v1 bytes at `docs/data/NAPTAN_N4C_R1A_SUPERSEDED_ACCOUNT_MIGRATION_V1_2026-08-22.sql`;
- preserved v1 SHA-256: `854C2ECD3F1EB9A43809710CF7887375BD02DB7FA4A0A98A868303743D27627F`;
- updated only the directly relevant account-deletion test and documentation references.

The five settled timestamp aliases were not renamed in this batch. Their equivalence remains documented, and they are handled by a separate future ledger-repair plan.

## ACTIVE MIGRATION INVENTORY AFTER CANONICALISATION

The active directory contains 18 unique migration versions and 18 unique migration names. It contains no executable `20260814124706` account migration and contains the canonical production version `20260814135046`.

Remaining production-only versions are the five previously settled deployment aliases:

`20260814115817`, `20260816210130`, `20260817062603`, `20260821213435`, `20260822100920`

Remaining local-only versions are their five local counterparts plus sealed N4A:

`20260814113440`, `20260816205543`, `20260816220000`, `20260821211239`, `20260822092938`, `20260822170000`

## FIVE PREVIOUSLY RECONCILED PAIRS

No contradictory evidence emerged. The five classifications remain:

- badge awards: `EXACT_EQUIVALENT_LOCAL_MIGRATION`;
- community hardening: `SEMANTICALLY_EQUIVALENT_LOCAL_MIGRATION`;
- moderation contract: `EXACT_EQUIVALENT_LOCAL_MIGRATION`;
- toilet-unit model: `SEMANTICALLY_EQUIVALENT_LOCAL_MIGRATION`;
- facility source observations: `SEMANTICALLY_EQUIVALENT_LOCAL_MIGRATION`.

## DRY-RUN RESULT

Executed after canonicalisation:

```text
supabase db push --dry-run --linked
```

Result:

```text
Remote migration versions not found in local migrations directory.

Make sure your local git repo is up-to-date. If the error persists, try repairing the migration history table:
supabase migration repair --status reverted 20260814115817 20260816210130 20260817062603 20260821213435 20260822100920
```

The account migration is no longer listed as a mismatch. The dry-run is blocked only by the five previously proven timestamp aliases. No repair command was executed.

## N4A ISOLATION

`ONLY_N4A_PENDING_AFTER_LEDGER_REPAIR`

This is not a claim that N4A is currently the only dry-run pending migration. The real dry-run remains blocked by the five production/local ledger aliases. After their separately authorized metadata repair, the canonical repository model has no remaining account discrepancy and N4A is the only genuinely new migration.

## FUTURE LEDGER REPAIR PLAN

N4C-R2 remains separately required. The future plan contains ten commands, all with `execute: false`: revert each of the five production deployment timestamps and mark its proven local equivalent applied.

Expected effects:

- schema delta: `0`;
- application-data delta: `0`;
- migration-ledger mutations: metadata-only, performed only in N4C-R2;
- N4A apply: not part of N4C-R2.

No ledger repair was performed in N4C-R1A.

## PRODUCTION VERIFICATION

Read-only production counts remained the established baseline:

| Table | Count |
|---|---:|
| `facilities` | 15,620 |
| `facility_sources` | 15,634 |
| `facility_source_observations` | 14 |
| `import_runs` | 5 |
| `toilet_map_import_staging` | 0 |
| `toilet_units` | 0 |
| `toilet_unit_sources` | 0 |

N4A is absent from the production ledger and its transport tables remain absent. No production account deletion, function invocation, or test-user operation occurred.

`TOTAL PRODUCTION MUTATIONS: 0`

`TOTAL MIGRATION LEDGER MUTATIONS: 0`

`TOTAL NAPTAN INGESTION ROWS: 0`

## SECURITY

No production security state changed. Read-only catalog verification confirms the recovered account functions are:

- `SECURITY DEFINER`;
- configured with an empty `search_path`;
- not executable by `anon`;
- executable by `authenticated`.

No Auth, RLS, policy, grant, public API, or production function invocation was changed or performed.

## VALIDATION

- Focused N4C-R1A validator: passed.
- Python compilation: passed.
- Existing deterministic repository test harness: passed, 24 test files, 0 failures.
- Account-deletion test file: 18 assertions passed.
- TypeScript typecheck: passed with `tsc --noEmit`.
- Active migration inventory: 18 unique versions, no duplicate versions or names.
- Superseded v1 exact-byte preservation: passed.
- Sealed N4A hash: passed.
- JSON artifacts: parsed successfully.
- Bounded secret scan: no credential-bearing patterns found.
- Production mutation/repair execution: none.
- Expo, EAS, Gradle, Android, APK, emulator: not run.

## FILES CREATED OR MODIFIED

Active migration and directly relevant references:

- `supabase/migrations/20260814135046_account_deletion_cleanup_contract.sql` — added canonical production migration body.
- `supabase/migrations/20260814124706_account_deletion_cleanup_contract.sql` — removed from active migration directory after exact preservation.
- `__tests__/accountDeletion.test.ts` — updated active migration path.
- `docs/ACCOUNT_DELETION_CONTRACT.md` — updated active migration path.
- `docs/FEATURE_TEST_READINESS.md` — updated active migration path.
- `docs/FEATURE_MATRIX.md` — updated active migration path.

Historical evidence, reports, and validation:

- `docs/data/NAPTAN_N4C_R1A_SUPERSEDED_ACCOUNT_MIGRATION_V1_2026-08-22.sql`
- `docs/data/NAPTAN_N4C_R1A_ACCOUNT_PRODUCTION_MIGRATION_MANIFEST_2026-08-22.json`
- `docs/data/NAPTAN_N4C_R1A_ACCOUNT_V1_V2_DIFF_2026-08-22.json`
- `docs/data/NAPTAN_N4C_R1A_LINEAGE_EVIDENCE_2026-08-22.json`
- `docs/data/NAPTAN_N4C_R1A_CANONICALISATION_DECISION_2026-08-22.json`
- `docs/data/NAPTAN_N4C_R1A_CANONICAL_MIGRATION_INVENTORY_2026-08-22.json`
- `docs/data/NAPTAN_N4C_R1A_N4A_ISOLATION_2026-08-22.json`
- `docs/data/NAPTAN_N4C_R1A_FUTURE_LEDGER_REPAIR_PLAN_2026-08-22.json`
- `docs/data/NAPTAN_N4C_R1A_DRY_RUN_EVIDENCE_2026-08-22.json`
- `docs/data/NAPTAN_N4C_R1A_VALIDATION_RESULTS_2026-08-22.json`
- `tools/source_expansion/naptan_n4c_r1a_validate.py`
- this report

The earlier N4C-R1 evidence files remain preserved and were not rewritten.

## GIT RESULT

Canonicalisation and evidence were committed in `06aa511b34e44ee2be83367fa3038c83ac21f478` with message `fix(db): reconcile account deletion migration history` and pushed normally to the required branch. Protected files remained unstaged. No production push or ledger repair was performed.

The follow-up documentation commit records this final handoff; local and remote branch heads were verified equal after the push.

## FINAL CLASSIFICATION

`RELIEF N4C-R1A — PRODUCTION ACCOUNT MIGRATION EXACTLY RECOVERED / LOCAL V1 SUPERSEDED BY PRODUCTION V2 / REPOSITORY MIGRATION HISTORY CANONICALISED / ONLY N4A PENDING AFTER LEDGER REPAIR / N4C-R2 LEDGER REPAIR READY FOR SEPARATE AUTHORIZATION / PRODUCTION MUTATIONS 0`

N4A remains sealed and undeployed. N5 remains unauthorized.

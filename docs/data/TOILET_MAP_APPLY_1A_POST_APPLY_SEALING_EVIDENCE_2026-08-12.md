# Relief Apply 1A Post-Apply Sealing Evidence

**Evidence date:** 2026-08-12
**Project:** Relief (`bgwxrxkmyaihplaloely`)
**Branch:** `codex/toilet-map-apply-1a-production-deploy`
**Starting HEAD:** `7b7808d99c893fb5ceaf6efc7a2861331438ac27`

This record covers the authorized post-Apply sealing preparation only. The
sealing migration was not deployed to production. No fourth Apply invocation,
production migration push, role credential assignment, or live execution was
performed.

## Accepted production Apply state

The previously verified production Apply state remains:

- successful run: `390f7338-2099-4953-ae47-f9e49ff3691c`
- historical rolled-back run: `676893a6-c7ac-4727-af82-4d6bb91faf9a`
- Apply audit rows: 2 total, 1 committed, 1 rolled back
- committed approved-manifest rows: 1
- approved registry rows: 48
- distinct target facilities: 25
- successful run: `completed`, `committed`, `ready_count=48`,
  `applied_count=48`, `stale_count=0`, `failed_count=0`,
  `rows_updated=48`
- historical run: `failed`, `rolled_back`, `applied_count=0`,
  `rows_updated=0`
- approved target values present: 48
- approved provenance matches: 48
- operations remaining unapplied: 0
- unexpected target values: 0
- facility-source rows: 15,584
- full source canonical MD5:
  `a927d8e332ec85fd1584197b4c7960e6`
- relevant source canonical MD5:
  `2f87c72124063d0896d7817407b330b5`
- source links with exactly one current relevant link: 48
- bad source-link multiplicity: 0
- non-current relevant links: 0
- newer-than-approved relevant links: 0
- target publication-status differences: 0
- accepted post-Apply canonical snapshot:
  `8ffce135dc1be29fbe5a7b0c715ae5297d1bf3d4bfa03a44875610fdc6a8ee52`

The fresh production read-only SQL recheck returned the same counters and
digests. No unexplained production data difference was observed.

Frozen Apply identities were not changed:

| Identity | SHA/value |
| --- | --- |
| infrastructure migration | `c3b463dfba10e1112750fb85c89a7f6e1913170600e388140968fa2373de895c` |
| audit-RLS migration | `ec6606681b0dc671372fdc8f905efe970ffd3a8001c7019db5028d354a3a212d` |
| facilities-RLS migration | `7f04c9bf79c71c745695f0515aefc33800e818377cb1b72996ccd32fbce2dfc` |
| plan | `7400626bc99061af7ba82c29969fc8929d7394c59afcfe574e1880521bad2b45` |
| manifest | `1de1a71186b80ce043b48fc5f4d6c4bc6ed9d1c964b3ddf7ad3b96ddd073bfa0` |
| source | `f6824fdc7cd29df8c1f45ba749c1b28d319fb34803c55459bbe748ef65937624` |
| review commit | `4710b9ec7a9f5a83aa9e7225400b8a6046ce0e77` |
| Apply engine | `relief.apply-engine-1a.v1` |

`LIVE_EXECUTION_ENABLED=False`,
`APPLY_REUSABLE_LOGIN_PATH_ENABLED=False`, and
`OPERATOR_CREDENTIAL_ASSIGNED_BY_THIS_TASK=False` remain unchanged.

## Temporary production surface before sealing

The read-only production inspection immediately before sealing preparation
confirmed:

- `relief_apply_owner` and `relief_apply_operator` are both NOLOGIN,
  NOSUPERUSER, and NOBYPASSRLS.
- `private.apply_relief_toilet_map_1a(text,text,text,text,text)` exists exactly
  once, is owned by `relief_apply_owner`, is SECURITY DEFINER, and has an empty
  `search_path`.
- `relief_apply_operator` had private-schema USAGE and function EXECUTE.
- `relief_apply_owner` had SELECT on `public.import_runs`, table-level UPDATE
  false on `public.facilities`, and column-level UPDATE true only for the six
  Apply columns: `has_baby_changing`, `requires_radar_key`,
  `is_gender_neutral`, `is_accessible`, `is_free`, and `field_provenance`.
- `public.facilities` contained the published SELECT policy and the temporary
  `relief_apply_owner_apply_1a_facilities_update` policy.
- `public.import_runs` contained exactly the temporary Apply SELECT, INSERT,
  and UPDATE policies.
- owner Apply-specific import INSERT and UPDATE column privileges were
  present; owner read-only SELECT was present.
- application-facing function EXECUTE privileges were absent.

## New forward sealing migration

Created through the installed Supabase CLI:

```text
supabase migration new seal_apply_1a_execution_path
```

| Field | Value |
| --- | --- |
| filename | `20260812190246_seal_apply_1a_execution_path.sql` |
| SHA-256 | `83d7f74de98c10675a4d6e902b27d85bea2ec3b3238ceca31d2bd29d0cf53eb7` |
| production status | not deployed; dry-run only |

The three prior Apply migrations were not edited.

### Fail-closed preconditions

Before any revocation, the migration asserts:

1. The immutable approved-operation registry contains exactly 48 rows.
2. Exactly one approved-manifest Apply row is committed with the frozen
   source, plan, manifest, review, engine, project, requested-count, ready,
   applied, stale, failed, and rows-updated values.
3. Run `390f7338-2099-4953-ae47-f9e49ff3691c` exists with the approved
   completed/committed/48-applied/48-updated state.
4. Run `676893a6-c7ac-4727-af82-4d6bb91faf9a` exists with the approved
   failed/rolled-back/zero-applied/zero-updated state.
5. The Apply function exists exactly once, is owned by `relief_apply_owner`,
   remains SECURITY DEFINER, and has `search_path=''`.
6. Both Apply roles are NOLOGIN, NOSUPERUSER, and NOBYPASSRLS.
7. The temporary facilities UPDATE policy exists.
8. The temporary import_runs INSERT and UPDATE policies exist.
9. The frozen import_runs SELECT policy exists.
10. The operator has private-schema USAGE and Apply-function EXECUTE.
11. Before/after digests are captured for the two audit rows, registry,
    approved target values/provenance/publication state, and all
    `facility_sources` rows.

### Exact revocations and policy removals

The migration performs only these persistent changes:

- revoke Apply-function EXECUTE from `relief_apply_operator`;
- revoke private-schema USAGE from `relief_apply_operator`;
- drop `relief_apply_owner_apply_1a_facilities_update` from
  `public.facilities`;
- revoke owner UPDATE on exactly the six Apply facility columns listed above;
- drop `relief_apply_owner_apply_1a_insert` from `public.import_runs`;
- drop `relief_apply_owner_apply_1a_update` from `public.import_runs`;
- revoke owner INSERT on the approved Apply audit INSERT columns;
- revoke owner UPDATE on the approved Apply audit UPDATE columns.

The public facilities SELECT policy, frozen import_runs SELECT policy, owner
SELECT privileges, function, registry, roles, role memberships, and historical
audit rows are preserved. The migration does not write facility values,
provenance, facility_sources, publication status, registry contents, or audit
rows. Its only created object is a transaction-scoped temporary baseline table,
which is dropped automatically on commit.

### Postconditions

The migration asserts:

- operator NOLOGIN, private USAGE false, and Apply EXECUTE false;
- owner NOLOGIN, NOSUPERUSER, and NOBYPASSRLS;
- facilities Apply UPDATE policy absent;
- owner table-level facilities UPDATE false and all seven checked columns,
  including publication status, UPDATE false;
- import_runs Apply SELECT policy present and Apply INSERT/UPDATE policies
  absent;
- owner Apply-specific import INSERT and UPDATE privileges false;
- owner import_runs SELECT true;
- registry count remains 48;
- both exact audit rows remain present and unchanged;
- function count/owner/SECURITY DEFINER/empty search_path remain unchanged;
- application-facing EXECUTE is absent;
- audit, registry, approved facility/provenance/publication, and complete
  facility-source digests equal their pre-seal values.

## Disposable PostgreSQL regression

`tools/enrichment/test_apply_1a_sealing.py` builds the infrastructure,
audit-RLS, and facilities-RLS fixture, creates one rolled-back Apply followed
by one committed Apply, binds the disposable audit rows to the accepted
production evidence IDs, applies the seal, and removes the disposable
databases afterward.

The regression passed in an isolated temporary PostgreSQL 17 cluster:

- successful audit row preserved: true;
- historical failed audit row preserved: true;
- 48 target values unchanged by sealing: true;
- 48 provenance records unchanged by sealing: true;
- facility_sources unchanged: true;
- operator private-schema access: denied, SQLSTATE 42501;
- operator Apply invocation: denied at private-schema privilege boundary,
  SQLSTATE 42501;
- owner facility UPDATE: denied, SQLSTATE 42501;
- owner Apply audit INSERT: denied, SQLSTATE 42501;
- owner successful-row UPDATE: denied, SQLSTATE 42501;
- owner failed-row UPDATE: denied, SQLSTATE 42501;
- owner SELECT of both audit rows and the immutable registry: allowed;
- owner retry result: `ALREADY_APPLIED`, `applied_count=0`,
  `mutations_committed=false`, same successful run ID;
- missing committed-row fixture: SQLSTATE 42501, `permission denied for table
  import_runs`, no new audit row, no facility/provenance/source mutation.

The existing audit-RLS and facilities-RLS PostgreSQL regressions also passed
against the same isolated PostgreSQL 17 cluster.

## Generated database types

The only authorized generator was run:

```text
npm run gen:types
```

It exited 1 because `SUPABASE_DB_URL` is not available in the local/server
environment. No credential was created, echoed, persisted, or added to
`EXPO_PUBLIC_*`; `src/types/database.types.ts` was not regenerated or
hand-edited.

```text
GENERATED_TYPES_UPDATE_REQUIRED = True
GENERATED_TYPES_REFRESH_BLOCKED = True
```

The generator remains a required follow-up when the server-side connection
variable is securely available.

## Other verification

- JavaScript suite: 11 test files passed.
- TypeScript typecheck: passed.
- ESLint: passed with 0 errors and 90 existing warnings.
- Apply engine Python suite: 25 passed.
- live Apply boundary/interlock suite: 37 passed.
- enrichment pipeline suite: 15 passed.
- `git diff --check`: passed.
- Supabase security advisors: 22 existing lints; no Apply/sealing-related
  finding in the current undeployed production state. No unrelated security
  remediation was performed.

## Production migration history and dry-run

Linked project ref read from the checkout: `bgwxrxkmyaihplaloely`.

`supabase migration list` showed every existing migration aligned and exactly
one local-only pending migration:

```text
20260812190246 | [local only] | 2026-08-12 19:02:46
```

Complete required dry-run output:

```text
Finished supabase db push.
Initialising login role...
DRY RUN: migrations will *not* be pushed to the database.
Connecting to remote database...
Would push these migrations:
 • 20260812190246_seal_apply_1a_execution_path.sql
```

No `--include-roles` flag was used. The exact proposed production migration
set is one migration: `20260812190246_seal_apply_1a_execution_path.sql`.
The SQL proposes only the bounded role/policy/column privilege revocations
listed above; no role operation, seed, table, function drop, data mutation,
or unrelated schema change is proposed.

## Production mutation and counters

Production mutation count for this task is zero. No migration was deployed,
no Apply function was invoked, and no migration-history repair was performed.
The counters remain:

```text
PRODUCTION_MIGRATION_HISTORY_REPAIRS = 2
PRODUCTION_CUSTOM_ROLES_PROVISIONED = 2
PRODUCTION_MIGRATIONS_DEPLOYED = 3
PRODUCTION_APPLY_FUNCTION_PRESENT = 1
PRODUCTION_APPLY_DISPATCH_ATTEMPTS = 3
PRODUCTION_APPLY_COMMITTED_EXECUTIONS = 1
PRODUCTION_APPLY_ROLLED_BACK_EXECUTIONS = 1
PRODUCTION_APPLY_AUDIT_ROWS = 2
PRODUCTION_FACILITY_VALUE_MUTATIONS = 48
PRODUCTION_PROVENANCE_MUTATIONS = 48
PRODUCTION_FACILITY_SOURCE_MUTATIONS = 0
APPLY_REUSABLE_LOGIN_PATH_ENABLED = False
OPERATOR_CREDENTIAL_ASSIGNED_BY_THIS_TASK = False
LIVE_EXECUTION_ENABLED = False
```

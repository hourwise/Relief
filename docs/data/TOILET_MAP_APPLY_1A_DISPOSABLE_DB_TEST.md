# Relief Apply 1A disposable database execution evidence

Date: 2026-08-11
Branch: `codex/toilet-map-apply-1a-disposable-test`
Starting SHA: `90bf6a90137fe9a048589bba4a05590b496269d5`

This evidence is local/throwaway only. No migration was deployed to Relief
Supabase, no live Apply function was executed, and no production facility,
provenance, or `import_runs` data was mutated.

## Approved identities

| Identity | Approved value |
|---|---|
| Review commit | `4710b9ec7a9f5a83aa9e7225400b8a6046ce0e77` |
| Apply Engine checkpoint | `a323b515a961332d78f9ec878ee6fe84d579a64e` |
| Plan SHA-256 | `7400626bc99061af7ba82c29969fc8929d7394c59afcfe574e1880521bad2b45` |
| Manifest SHA-256 | `1de1a71186b80ce043b48fc5f4d6c4bc6ed9d1c964b3ddf7ad3b96ddd073bfa0` |
| Source SHA-256 | `F6824FDC7CD29DF8C1F45BA749C1B28D319FB34803C55459BBE748EF65937624` |
| Operations | 48 |
| Distribution | `has_baby_changing=16`, `requires_radar_key=14`, `is_gender_neutral=15`, `is_accessible=2`, `is_free=1` |

## Disposable target and fixture

The test used a fresh PostgreSQL `17.10` `x86_64-windows` cluster on
`127.0.0.1:55432`, initialized under the OS temporary directory. The hard
target check recorded:

```text
host=127.0.0.1
port=55432
database=relief_apply_1a_test
current_user=relief_local_admin
server=PostgreSQL 17.10 on x86_64-windows
```

The cluster used local trust authentication and throwaway roles only. No
password was committed or printed. `relief_apply_owner` was `NOLOGIN,
NOSUPERUSER, NOCREATEDB, NOCREATEROLE, NOINHERIT`; `relief_apply_operator` was
`NOLOGIN, NOSUPERUSER, NOCREATEDB, NOCREATEROLE, NOINHERIT`. `anon` and
`authenticated` were non-login, non-privileged roles.

The fixture created the minimum relevant current schema for `facilities`,
`facility_sources`, and `import_runs`, including the relevant checks, foreign
keys, unique source identity, and the existing `updated_at` trigger pattern.
The exact approved registry then supplied 25 distinct target facilities and 25
source links. One unrelated facility was added as a no-touch control. All 48
target fields started `NULL`; provenance covered absent keys, unrelated keys,
and compatible `Toilet Map UK` / `source_imported` entries.

Disposable-only SQL files are in `tools/enrichment/`:

- `disposable_apply_1a_fixture.sql`
- `disposable_apply_1a_seed.sql`
- `disposable_apply_1a_call.sql`
- `disposable_apply_1a_postcheck_fault.sql`
- `disposable_apply_1a_rollback.sql`

## Migration result and defect correction

`supabase/migrations/20260811164202_apply_1a_audit_and_transaction.sql`
applied successfully. The database contained 48 immutable registry rows with
the exact approved hashes and `16/14/15/2/1` distribution. The function
signature was exactly:

```text
private.apply_relief_toilet_map_1a(text, text, text, text, text) RETURNS jsonb
```

The actual `SECURITY DEFINER` function owner was `relief_apply_owner`.

The first real call exposed a genuine privilege defect: the original
`LOCK TABLE public.facilities, public.facility_sources IN SHARE MODE` could not
run under the bounded owner because PostgreSQL has no grantable `LOCK`
privilege. It failed with SQLSTATE `42501` before any facility update. The
correction is narrow: the migration now share-locks existing facility rows,
retains exact source-link validation and the full before/after source digest,
and upgrades target facility rows to `FOR UPDATE` for the allowlisted writes.
No operation, plan, manifest, checksum, field allowlist, provenance policy,
database precondition, or output value changed. The corrected artifact was
reapplied from a fresh disposable database and all relevant tests were rerun.

A second execution of the migration itself failed at the immutable registry
insert with exit code `3`, as expected for a once-only migration, and the
transaction rolled back. It did not duplicate registry rows, functions,
triggers, indexes, or facility/source data. This is safe in the repository’s
once-only migration runner; a partial deployment recovery must use the
documented rollback/recovery procedure rather than blindly rerun the file.

## Privilege proof

| Principal | Result |
|---|---|
| `PUBLIC` | No Apply execute grant; execution rejected |
| `anon` | Execution rejected |
| `authenticated` | Execution rejected |
| `relief_apply_operator` | Private schema usage and function execute only; direct facility/source/registry/import-run writes rejected |
| `relief_apply_owner` | Owns function; SELECT on registry/facilities/source links; bounded `import_runs` write; column-only facility update for the five fields plus `field_provenance` |

The owner was not superuser, did not have `BYPASSRLS`, `CREATEROLE`, or
`CREATEDB`, and did not have broad facility-table UPDATE. Operator UPDATE and
DELETE attempts against the approval registry were rejected. The function has
no caller-supplied operations parameter.

## Transaction evidence

The successful disposable transaction returned:

```text
COMMITTED
requested=48
ready=48
applied=48
stale=0
failed=0
mutations_committed=true
```

Postchecks found all 48 exact scalar values and all 48 exact target
provenance records. Facility count stayed 26; source-link count and source
digest stayed unchanged; publication status stayed unchanged; the unrelated
facility was not created, deleted, or altered; and unrelated provenance keys
survived. The existing `updated_at` trigger was allowed to update timestamps.

The exact second call returned `ALREADY_APPLIED` with `applied_count=0` and no
facility or provenance changes. There was one committed success for the
manifest.

The following failure tests were run in fresh databases and each returned
`ROLLED_BACK`, `applied=0`, with all target values still null and no Apply
provenance retained:

- stronger community/staff provenance;
- uninterpretable target provenance;
- missing exact source link;
- `is_current=false`;
- source link moved to the wrong facility;
- source timestamp newer than the approved registry timestamp.

A deliberate non-null operation-48 target proved full rollback: operations
1–47 did not leak through, the pre-existing stale value remained, and the safe
failure audit contained no credential or connection details. Restoring the
target to `NULL` allowed a clean `COMMITTED` 48-operation retry. A duplicate
source identity was rejected by the fixture’s unique constraint before Apply.

Two near-simultaneous exact calls serialized as one `COMMITTED` 48-operation
result and one `ALREADY_APPLIED` zero-operation result. A disposable
before-update fault trigger changed a publication status during the write;
the postcheck detected it and rolled back all facility/provenance changes.
After removing only that test trigger, the exact call committed 48 operations.

The documented schema rollback was run against a fresh database where Apply
had not been used. It removed the function, trigger, private registry, indexes,
private schema, and Apply-specific `import_runs` columns while preserving the
pre-existing historical import-run table/data. This was a schema rollback
test, not a claim that production enrichment data is reversibly undone by
rolling back a migration.

## Operator, simulation, and production read-only gates

`tools/enrichment/live_apply_1a.py` remains hard-locked with
`LIVE_EXECUTION_ENABLED = False`. No `--apply` is dry-run only; wrong
identities and missing environment are rejected; valid identities plus a
dummy localhost environment are rejected before any database client or
connection is constructed.

The offline in-memory simulation returned:

```text
requested=48
ready=48
stale=0
persistent_data_differences=0
before_snapshot=cd16178ed5310f6dc228e0be7b6b0171606936a2c3160bb0e584aa1d015f57d1
after_snapshot=cd16178ed5310f6dc228e0be7b6b0171606936a2c3160bb0e584aa1d015f57d1
```

After disposable testing, the only production access was the approved
GET-only preflight. It returned `48 READY / 0 STALE` on both reads, with both
snapshot hashes equal to:

```text
8d4d910af231a0a083316ee299678442b3e396a558d6a411d3109e92bfe764f1
```

The live project still had three historical `import_runs`, zero Apply-specific
`import_runs` columns, and no private Apply registry. The remote migration list
did not contain `20260811164202`.

```text
PRODUCTION_MIGRATIONS_DEPLOYED = 0
PRODUCTION_LIVE_APPLY_EXECUTIONS = 0
PRODUCTION_DATABASE_MUTATIONS = 0
```

## Quality gates

- Node `v22.22.2`
- npm `10.9.7`
- fresh `npm ci`: PASS; 816 packages added; npm reported 26 audit vulnerabilities
- `npm run verify`: PASS; TypeScript, Expo lint, and all 11 JavaScript test files
- `npx expo-doctor`: PASS; 21/21 checks
- Python enrichment / Apply Engine / live-boundary tests: PASS; 75 tests
- disposable PostgreSQL SQL harness: PASS
- `git diff --check`: PASS
- Android build: NOT RUN per task
- EAS: NOT RUN
- Play setup: NOT RUN

The remaining prerequisite before any production migration deployment is
separate production provisioning and review of `relief_apply_owner` and
`relief_apply_operator`, followed by an explicitly authorized deployment
decision. This task intentionally stops before that boundary.

NOT READY FOR APPLY 1A PRODUCTION MIGRATION DEPLOYMENT

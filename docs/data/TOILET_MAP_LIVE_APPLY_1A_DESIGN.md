# Toilet Map Apply 1A — live-apply design gate

**Status: DESIGN ONLY. No migration is deployed. No live Apply 1A execution has occurred.**

This document is the final pre-live engineering design for the exact approved
48-operation Apply 1A boundary. It does not widen the plan, regenerate the
manifest, or authorize the write.

## Frozen approval identities

| Identity | Approved value |
|---|---|
| Reconciliation review commit | `4710b9ec7a9f5a83aa9e7225400b8a6046ce0e77` |
| Apply Engine checkpoint | `a323b515a961332d78f9ec878ee6fe84d579a64e` |
| Plan SHA-256 | `7400626bc99061af7ba82c29969fc8929d7394c59afcfe574e1880521bad2b45` |
| Manifest SHA-256 | `1de1a71186b80ce043b48fc5f4d6c4bc6ed9d1c964b3ddf7ad3b96ddd073bfa0` |
| Toilet Map source SHA-256 | `F6824FDC7CD29DF8C1F45BA749C1B28D319FB34803C55459BBE748EF65937624` |
| Project ref | `bgwxrxkmyaihplaloely` |
| Apply Engine version | `relief.apply-engine-1a.v1` |

The committed plan was rehashed from its raw bytes. The committed manifest was
recomputed canonically and matched its recorded hash. It contains exactly 48
operations with field distribution:

```text
has_baby_changing  16
requires_radar_key 14
is_gender_neutral  15
is_accessible       2
is_free             1
```

The only target fields are null-to-boolean scalar updates. Names, coordinates,
opening hours, addresses, publication status, source links, facility creation,
deletion, absent-source records, and manual-review entries have no path.

## Live schema re-audit

Result: **`LIVE_SCHEMA_MATCHES_EXPECTED` for the Apply 1A-relevant schema.**

The current project was introspected read-only on 2026-08-11. The relevant
objects match the committed baseline plus the already-recorded
`20260806000100_repair_find_nearest_facilities.sql` change:

- `public.facilities` has the five approved nullable boolean columns and
  `field_provenance jsonb`; its primary key is `id` and the existing trigger
  only updates `updated_at`.
- `public.facility_sources` has `facility_id`, `source_name`,
  `source_record_id`, `source_updated_at`, `is_current`, and `import_run_id`.
  The unique key is `(source_name, source_record_id)`, with facility and
  current-source indexes.
- `public.import_runs` has the existing source/run lifecycle fields, row
  counts, timestamps, and `error_summary`, but no dedicated Apply 1A identity
  or transaction-outcome fields. The local migration adds those fields but
  has not been deployed.
- `auth.users.id` is the UUID primary key. The relevant public foreign keys
  remain intact; Apply 1A does not use user/person data.
- RLS is enabled on `facilities`, `facility_sources`, `import_runs`, and
  `auth.users`. The public policies expose read-only published facilities and
  their source links; there is no public write policy for the Apply boundary.
- `find_nearest_facilities` is `SECURITY INVOKER`, has `search_path = public`,
  and is the existing read-only discovery RPC. No live Apply or Enrichment RPC
  exists.
- Existing indexes and constraints relevant to exact facility/source matching
  are present.

The live introspection also reports the PostGIS-managed
`public.spatial_ref_sys` table with RLS disabled. That is an unrelated
extension object and does not affect the Apply 1A tables or transaction
preconditions; it is not changed by this task.

The current Supabase security advisor also reports existing, pre-task issues:
`public.import_runs` and the staging table have RLS enabled without policies,
and several existing public security-definer functions are callable by normal
roles. These are existing schema/application concerns, not an Apply 1A write
path. This task does not broaden scope by repairing them. The local migration
now prepares the Apply function in a private schema with explicit role-only
execute permission, but the migration has not been deployed and the function
has not been executed.

The existing importer source run referenced by all 48 source links is:

```text
run_id:         143e2b77-05b7-4415-aa29-0ea0f05190f4
source_name:    Toilet Map UK
source_file:    normalised.csv
status:         completed
rows_received:  15584
rows_valid:     15584
rows_inserted:  15480
rows_unchanged: 104
```

Its historical import checksum is recorded in the preflight evidence. It is
not substituted for the frozen Apply 1A source snapshot checksum above.

## Audit schema decision: A — extend `public.import_runs`

`public.import_runs` is the truthful parent because it already represents a
source-backed run with a UUID, source name/checksum, lifecycle timestamps,
row counts, status, and error summary. Creating a second apply-run framework
would split importer and enrichment audit history and make the run lineage
harder to explain.

The undelivered migration
`supabase/migrations/20260811164202_apply_1a_audit_and_transaction.sql` adds:

- `run_kind` (`import` or `apply_1a`);
- approved plan, manifest, review-commit, engine-version, and project-ref
  columns;
- requested, ready, applied, stale, and failed counts;
- `transaction_outcome` (`not_started`, `dry_run`, `committed`,
  `rolled_back`, `failed`, or `already_applied`);
- `rollback_summary`;
- guarded format, identity, count, and committed-outcome constraints; and
- a non-unique manifest lookup plus a committed-only unique key. This permits
  durable rolled-back attempt history and a safe retry while still preventing
  two committed rows for the same approved manifest.

The migration is additive and idempotently guarded. Existing importer rows
remain `run_kind = import` and retain their current status vocabulary. A
documented rollback is included as comments in the migration; it has not been
run.

## Future privileged write boundary

The future operator is local/admin-only and must use a server-side privileged
database connection. The mobile app and its anon/authenticated key must never
call the write boundary.

The migration now prepares the function in a non-exposed `private` schema,
using `SECURITY DEFINER SET search_path = ''` and fully qualified relations.
It accepts only the five approval gates; it does not accept an operations JSON
payload. The exact 48 operations are seeded into
`private.relief_apply_1a_approved_operations`, checked for the approved hashes
and field distribution, and protected by an immutable trigger. A caller-
supplied hash can therefore never authorize a substituted operation set.

The intended function contract is conceptually:

```text
private.apply_relief_toilet_map_1a(
  p_project_ref,
  p_plan_sha256,
  p_manifest_sha256,
  p_source_sha256,
  p_confirmation
) -> run evidence JSON
```

That function is prepared in this design-only migration but is not callable by
normal roles: execute is revoked from `PUBLIC`, `anon`, and `authenticated`.
The migration does not create either privileged role. If a deployment DBA has
provisioned them separately, it conditionally grants `relief_apply_operator`
only this function and gives `relief_apply_owner` only the registry read,
facility read/approved-column update, and audit insert/update rights before
transferring function ownership. With either role absent, no grant or transfer
occurs.

When implemented, permissions must be explicit:

```sql
revoke execute on function private.apply_relief_toilet_map_1a(...) from public;
revoke execute on function private.apply_relief_toilet_map_1a(...) from anon;
revoke execute on function private.apply_relief_toilet_map_1a(...) from authenticated;
grant execute on function private.apply_relief_toilet_map_1a(...) to relief_apply_operator;
```

The role names are deployment placeholders, not roles created in this task. No
service-role key, database password, token, or nonce is committed. The current
operator module refuses the live form because `LIVE_EXECUTION_ENABLED = False`
on this review branch, even when all arguments and the named environment
variable are present.

## Exact transaction semantics

The future function must run as one PostgreSQL transaction:

1. Take a transaction-scoped advisory lock keyed by the approved manifest.
2. Lock or create the `apply_1a` audit run and resolve idempotency state.
3. Validate project, plan, manifest, source, confirmation, and exact registry
   operation identities.
4. Lock and re-read all 48 facilities and exact source links.
5. Refuse the entire run if any facility is missing, a link is absent/not
   current, a source timestamp is newer, a target is non-null, or stronger or
   uninterpretable provenance exists.
6. Update only the five allowlisted scalar columns through a fixed `CASE`
   allowlist; never construct a column name from JSON or unchecked input.
7. Merge only the changed field’s provenance entry while preserving unrelated
   JSONB keys.
8. Assert exactly 48 affected scalar rows and 48 provenance changes.
9. Run the post-apply checks and complete the audit row as `status = completed`
   and `transaction_outcome = committed`.
10. Commit once. Any exception rolls back every facility/provenance change.

The audit row is inserted before the inner PL/pgSQL exception block. A failure
inside that block rolls back all facility/provenance work, then records a safe
`status = failed`, `transaction_outcome = rolled_back` row after the
subtransaction rollback. The rollback summary stores only a SQLSTATE and fixed
operator-safe text; it never stores a database URL or raw exception detail.

There is no permitted `47 committed + 1 failed` outcome. A retry of a
rolled-back attempt is allowed after a fresh preflight; a committed same-
manifest attempt returns `ALREADY_APPLIED` without repeating changes.

## Provenance contract

`public.facilities.field_provenance` is a JSONB object keyed by facility field.
For each changed field the future transaction replaces only that key and keeps
all unrelated keys. The new per-field object should include:

```text
source: Toilet Map UK
source_record_id
source_updated_at
source_snapshot_checksum
import_run_id
field
previous_value: null
new_value
basis: EXACT_SOURCE_ID
confidence: HIGH
policy/apply version
approved plan hash
approved manifest hash
approved review commit
recorded_at
```

The function must refuse to overwrite stronger or uninterpretable existing
provenance. The synthetic implementation and tests prove unrelated-key
preservation; the live function must repeat that check inside the database
transaction.

## Idempotency and concurrency

The committed-only unique manifest key on `import_runs` is the durable
duplicate guard. A transaction-scoped advisory lock serializes concurrent attempts for
the same manifest before the run row is inspected:

- committed same manifest → `ALREADY_APPLIED`, no-op;
- failed/rolled-back same manifest → a new attempt row is retryable after
  fresh preflight;
- in-progress duplicate → reject or wait behind the lock, never run twice;
- different manifest → reject as unapproved.

The local synthetic coordinator tests both serialization and the single
successful application effect. The local transaction model also proves that a
rolled-back manifest can be retried.

## Historical import-run checksum preflight

Before considering deployment, the live `public.import_runs` table was read
with a GET-only SQL query on 2026-08-11:

```text
total rows:                 3
null source_checksum rows:  0
valid 64-hex rows:          3
invalid/non-64 rows:        0
```

All three rows are completed `Toilet Map UK` importer runs with the historical
lowercase checksum
`24a3655f01f03596f3427c9b4af8c752bc0844eb8dbd66c066b04a82e1c2d40f`.
The new format constraint is therefore compatible with existing history. The
Apply identity uses canonical lowercase comparison with `lower(source_checksum)`
and does not replace or reinterpret those historical rows.

## Rollback and recovery

Transaction rollback is automatic: any precondition, affected-row, provenance,
or postcheck failure aborts the whole facility update set. The audit result
must never claim `committed` after that rollback.

A later corrective rollback is a separate, manual-review operation. It must
first prove all 48 fields still equal their Apply 1A values, that no stronger
source/community/staff evidence superseded them, and that each provenance key
still identifies Apply 1A. No reverse mutation that blindly writes `null` is
generated here.

## Live preflight result

The read-only evidence in
`docs/data/TOILET_MAP_LIVE_APPLY_1A_PREFLIGHT.json` and `.md` was captured from
the current project using GET-only reads and two immediate snapshots:

```text
requested operations:    48
READY:                   48
STALE/failures:           0
before snapshot SHA:     8d4d910af231a0a083316ee299678442b3e396a558d6a411d3109e92bfe764f1
after snapshot SHA:      8d4d910af231a0a083316ee299678442b3e396a558d6a411d3109e92bfe764f1
persistent differences:  0
database mutations:      0
```

The artifact contains all 48 target values, exact source links, target
provenance observations, and the existing importer run reference. It contains
no fake post-apply result and no live Apply audit row.

## Exact future operator command

This command is documented only. It was not run:

```text
python tools/enrichment/live_apply_1a.py --apply --project-ref bgwxrxkmyaihplaloely --plan-sha 7400626bc99061af7ba82c29969fc8929d7394c59afcfe574e1880521bad2b45 --manifest-sha 1de1a71186b80ce043b48fc5f4d6c4bc6ed9d1c964b3ddf7ad3b96ddd073bfa0 --source-sha F6824FDC7CD29DF8C1F45BA749C1B28D319FB34803C55459BBE748EF65937624 --confirm APPLY_RELIEF_TOILET_MAP_1A_48 --privileged-db-env RELIEF_APPLY_1A_DATABASE_URL
```

The privileged database URL is supplied only at execution time through the
named environment variable. There is no default that enables mutation, and
the current boundary branch refuses the live form because
`LIVE_EXECUTION_ENABLED = False`, even when the named environment variable is
present. The function and migration are prepared only for deployment review.

## Current gate result

This is **READY FOR APPLY 1A MIGRATION DEPLOYMENT REVIEW**, but **NOT READY FOR
LIVE APPLY 1A AUTHORIZATION**. The 48-operation preflight is ready and the
privileged transactional SQL boundary is implemented in the migration, but it
has not been deployed, no privileged role has been created, and the operator
hard lock remains in force. The required zero-mutation boundary remains
intact.

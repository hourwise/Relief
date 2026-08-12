# Relief Apply 1A Facilities UPDATE-RLS Corrective Evidence

Date: 2026-08-12

This is a new factual evidence record for the second production dispatch
attempt and the forward facilities-RLS correction. Earlier attempt records are
not rewritten. Production deployment and another Apply invocation remain
unauthorized by the governing approval.

## Production incident state

- Project: `Relief` / `bgwxrxkmyaihplaloely`
- Branch at investigation start: `codex/toilet-map-apply-1a-production-deploy`
- Starting HEAD: `f1ac18a770c866d40f8ea2c817d14fc949fdcf35`
- Second production dispatch run ID: `676893a6-c7ac-4727-af82-4d6bb91faf9a`
- Durable audit state: `status=failed`, `transaction_outcome=rolled_back`
- Durable result: `ready_count=0`, `stale_count=1`, `applied_count=0`, `failed_count=1`, `rows_updated=0`
- Rollback summary records `SQLSTATE=P0001` and no committed facility or provenance partial change.
- Production Apply history remains one audit row, zero committed approved-manifest rows, and one failed row.

The exact root cause is a missing `FOR UPDATE` RLS policy on
`public.facilities`, not missing column grants. Production has RLS enabled,
`FORCE ROW LEVEL SECURITY=false`, and table owner `postgres`. The only
facilities policy before this corrective migration was:

```text
Published facilities are viewable by everyone
command: SELECT
role: PUBLIC
USING: publication_status = 'published'
```

Under `relief_apply_owner`, production still has table-level SELECT=true and
table-level UPDATE=false. The exact intended column UPDATE privileges remain
true for `has_baby_changing`, `requires_radar_key`, `is_gender_neutral`,
`is_accessible`, `is_free`, and `field_provenance`; `publication_status` remains
false. The owner and operator remain NOLOGIN, NOSUPERUSER, and NOBYPASSRLS.
The owner could see 25 approved/published target rows by ordinary SELECT but
could lock 0 through `SELECT ... FOR UPDATE`, causing the function's explicit
facility precondition to raise P0001.

## Forward correction

New migration generated with the Supabase CLI:

```text
20260812124351_apply_1a_facilities_update_rls.sql
SHA-256: 7f04c9bf79c71c745695f0515aefc33800e818377cb1b72996ccd32fbce2dfc
```

The migration contains one policy and no role, grant, ownership, function, or
data changes:

```text
policy: relief_apply_owner_apply_1a_facilities_update
table: public.facilities
command: UPDATE
role: relief_apply_owner
```

The normalized PostgreSQL 17 USING and WITH CHECK expressions are identical:

```sql
((publication_status = 'published'::text) AND (EXISTS (
  SELECT 1
  FROM private.relief_apply_1a_approved_operations r
  WHERE r.facility_id = facilities.id
    AND r.project_ref = 'bgwxrxkmyaihplaloely'
    AND r.approved_plan_sha256 = '7400626bc99061af7ba82c29969fc8929d7394c59afcfe574e1880521bad2b45'
    AND r.approved_manifest_sha256 = '1de1a71186b80ce043b48fc5f4d6c4bc6ed9d1c964b3ddf7ad3b96ddd073bfa0'
    AND r.approved_review_commit = '4710b9ec7a9f5a83aa9e7225400b8a6046ce0e77'
    AND r.apply_engine_version = 'relief.apply-engine-1a.v1'
    AND r.source_checksum = 'f6824fdc7cd29df8c1f45ba749c1b28d319fb34803c55459bbe748ef65937624'
))))
```

The policy admits the immutable registry's 25 approved facilities and admits
0 non-approved facilities. It is not granted to PUBLIC, anon, authenticated,
service_role, authenticator, or relief_apply_operator. `supabase/roles.sql`
was not changed.

## Disposable PostgreSQL 17 evidence

The existing deployed-state fixture was extended only in the new test harness
to model the production facilities SELECT policy and to make the 25 approved
fixture targets published, matching the current production precondition. The
temporary PostgreSQL 17 cluster was local and was removed after each run.

- Old-state ordinary approved SELECT: 25
- Old-state approved `FOR UPDATE`: 0
- Old-state Apply: `ROLLED_BACK`, `ready_count=0`, `applied_count=0`, `failed_count=1`, `mutations_committed=false`, durable failed audit present
- Corrected policy count: 1 facilities UPDATE policy, owner role, UPDATE command
- Corrected approved rows admitted: 25
- Corrected non-approved rows admitted: 0
- Corrected approved `FOR UPDATE`: 25
- Corrected non-approved `FOR UPDATE`: 0
- Corrected initial `FOR SHARE` lockable rows: 25
- Corrected Apply: `COMMITTED`, 48 requested, 48 READY, 48 applied, 0 STALE, 0 failed, mutations committed=true
- Corrected committed audit rows: 1, `rows_updated=48`
- Repeated Apply: `ALREADY_APPLIED`, `applied_count=0`, same committed run ID, no second committed audit row
- Controlled fault: `ROLLED_BACK`, `applied_count=0`, `rows_updated=0`, durable failed audit, no facility/provenance snapshot change
- Concurrent Apply calls: exactly one COMMITTED and one ALREADY_APPLIED; one committed audit row
- Explicit target-row lock: Apply waited approximately 2.67 seconds for the target row lock, then committed; unrelated facilities were not required to lock
- Correct target values: 48
- Incorrect or NULL target values: 0
- Matching provenance rows: 48; mismatches: 0
- Facility-source rows changed: 0; publication-status differences: 0
- Non-approved published UPDATE affected rows: 0
- Application-facing UPDATE policies: 0
- Function EXECUTE boundary unchanged

The frozen disposable registry remained 48 operations, 25 distinct target
facilities, and the distribution `has_baby_changing=16`,
`requires_radar_key=14`, `is_gender_neutral=15`, `is_accessible=2`,
`is_free=1`, with zero identity mismatches.

## Production read-only recheck

The fresh GET-only Apply Engine preflight used the configured Relief REST
endpoint and wrote only temporary local output:

```text
requested operations: 48
READY: 48
STALE/PRECONDITION_FAILED: 0
snapshot mode: read-only Supabase REST GET
fresh before snapshot: 8d4d910af231a0a083316ee299678442b3e396a558d6a411d3109e92bfe764f1
fresh after snapshot:  8d4d910af231a0a083316ee299678442b3e396a558d6a411d3109e92bfe764f1
persistent differences: 0
```

The fresh snapshot matches the previous recorded snapshot exactly. Relevant
source and provenance snapshots were unchanged. Production source checks also
remain:

```text
public.facility_sources rows: 15584
FULL_SOURCE_CANONICAL_MD5: a927d8e332ec85fd1584197b4c7960e6
RELEVANT_SOURCE_CANONICAL_MD5: 2f87c72124063d0896d7817407b330b5
approved operations with exactly one relevant source link: 48
bad multiplicity: 0
non-current relevant links: 0
newer-than-approved relevant links: 0
```

`LIVE_EXECUTION_ENABLED=False` remains hard-locked in
`tools/enrichment/live_apply_1a.py`. No production migration was applied and
no production Apply retry or third dispatch was invoked. Live retry remains
unauthorized.

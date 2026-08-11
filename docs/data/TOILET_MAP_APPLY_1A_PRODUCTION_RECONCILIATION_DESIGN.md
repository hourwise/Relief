# Apply 1A production migration and role reconciliation design

**Status: RECONCILIATION CHECKPOINT. No production schema, data, role, grant,
or Apply mutation was performed at this checkpoint.**

This document records the bounded follow-up authorized after the accepted
Apply 1A reconciliation report. It is a local reconciliation design and
evidence record, not a deployment approval. The CLI was linked only to the
confirmed Relief project. No `supabase migration repair`, role DDL, grant
change, `supabase db push`, Apply RPC call, credential generation, or live
execution was performed while producing this checkpoint.

## 1. Starting state

| Item | Value |
|---|---|
| Branch | `codex/toilet-map-apply-1a-production-deploy` |
| Starting/observed HEAD | `d7b058fbe18af154dfec5ce5f661ba2bde28e5cf` |
| Supabase project | Relief / `bgwxrxkmyaihplaloely` |
| Current production conclusion | `NOT READY FOR APPLY 1A PRODUCTION DEPLOYMENT AUTHORIZATION` |
| Production relevant-data snapshot | `8d4d910af231a0a083316ee299678442b3e396a558d6a411d3109e92bfe764f1` |
| Accepted GET-only preflight | 48 requested, 48 READY, 0 STALE |
| `LIVE_EXECUTION_ENABLED` | `False` |
| Supabase CLI | `2.75.0` (not upgraded) |

The user-controlled Supabase CLI authentication was available through the
native credential store. `supabase link --project-ref
bgwxrxkmyaihplaloely` completed successfully, and the linked project ref was
verified as exactly `bgwxrxkmyaihplaloely`. The pre-repair CLI migration list
was captured before any history repair.

## 2. Reconstructed migration lineage

### Production migration rows

The current production migration table contains exactly these five rows:

| Production version/name | SQL recoverable in git | Historical path | Active-local status | Effects represented by baseline/current schema | Independent application evidence |
|---|---|---|---|---|---|
| `001` / `initial_schema` | Yes | `supabase/legacy_migrations/001_initial_schema.sql` | Moved out of active chain | Yes | Production migration row plus current schema; the row proves recorded application, not an external execution log |
| `20260624` / `community_features` | Yes | `supabase/legacy_migrations/20260624_community_features.sql` | Moved out of active chain | Yes | Production migration row plus current schema |
| `20260625` / `premium_features` | Yes | `supabase/legacy_migrations/20260625_premium_features.sql` | Moved out of active chain | Yes | Production migration row plus current schema |
| `20260701` / `monetisation` | Yes | `supabase/legacy_migrations/20260701_monetisation.sql` | Moved out of active chain | Yes | Production migration row plus current schema |
| `20260725` / `facility_trust_and_import` | Yes | `supabase/legacy_migrations/20260725_facility_trust_and_import.sql` | Moved out of active chain | Yes | Production migration row plus current schema |

The remote rows are the authoritative evidence that those five version
identities were recorded as applied. The exact historical SQL is still
recoverable from git, but the repository does not contain a separate deployment
log proving every statement in each file was executed. The live-schema baseline
and read-only production introspection independently establish the resulting
schema state.

### Legacy files without corresponding production rows

Two additional historical files remain in `supabase/legacy_migrations/`:

- `20260725_field_provenance.sql`: its effect is independently visible in the
  live `facilities.field_provenance jsonb` column and in the baseline, but there
  is no separate `20260725` production migration row for this file.
- `20260725_postgis_nearest_facility_rpc.sql`: its old function body references
  six columns that do not exist in the live schema. It is historical code
  archaeology, not a truthful description of the current production function.
  The current function is the narrow repaired definition represented by
  `20260806000100_repair_find_nearest_facilities.sql`.

The three `20260725_*.sql` filenames also cannot all be restored to the active
migration directory: they share one migration version while the production
history has only one `20260725` row. Moving them back would create a false
active chain and would collide with the squashed baseline. They remain in
`legacy_migrations/` unchanged.

### Why the divergence exists

Git history shows that the complete `supabase/` directory was previously
ignored. Commit `842f38c` began tracking it, added a schema-only dump from the
running database as the authoritative baseline, and moved the seven old
hand-written files to `legacy_migrations/` because replaying them no longer
reproduced the live database. Commit `1804cce` then added the function repair
after the baseline.

Consequently:

1. Production retains five older migration-history records.
2. The active local directory intentionally starts with a live-schema
   snapshot rather than the old replay chain.
3. The repair effect is already present in production, but its
   `20260806000100` version is absent from production migration history.
4. Apply 1A is a genuinely new local migration and is absent from production.

This is a history/lineage gap, not evidence that the legacy SQL should be
replayed.

## 3. Classification of the three active local migrations

### `20260806000000_live_schema_baseline.sql`

Classification: **declarative live-schema snapshot / fresh-disposable baseline,
not an executable forward migration for the existing Relief database**.

The file is explicitly documented as a `pg_dump --schema-only --schema=public`
export from the live database on 2026-08-06. It contains top-level schema
creation statements and the then-current broken function definition. It does
not represent a safe delta from the existing production schema; applying it to
the existing database would attempt to recreate objects that already exist and
could fail before later migrations run.

It must **never be executed against the existing production database merely
because it is in `supabase/migrations/`**. Its intended uses are schema
reference, fresh/disposable reconstruction, and a truthful baseline marker after
read-only equivalence has been proven. The future reconciliation should mark
its version `applied` in migration history only; it should not execute the SQL.

### `20260806000100_repair_find_nearest_facilities.sql`

Classification: **real forward function repair whose effect is already present
in production**.

The production function is read-only introspected as:

- signature `find_nearest_facilities(double precision, double precision,
  integer, integer)`;
- owner `postgres`;
- `SECURITY INVOKER` (`prosecdef = false`);
- `search_path = public`;
- narrow return set containing facility identity, display/location fields,
  verification/accessibility fields, score, and `distance_metres`;
- published-facility and PostGIS distance filtering with distance/name order.

That definition matches the repair migration's intended replacement. Git commit
`1804cce` also records that the repair was applied to the live project and
verified through the RPC/REST path. Therefore it is not genuinely pending as a
schema change, but its version is missing from the remote history table.

The migration is repeatable at the SQL-object level because it drops and
recreates the known function signature. That does not make re-running it an
appropriate history-repair technique: it is still a production function
replacement. It is not required before Apply 1A because the repaired definition
already exists. If a future exact definition comparison fails, stop and obtain a
separate owner decision; do not silently deploy the repair or broaden its
projection.

### `20260811164202_apply_1a_audit_and_transaction.sql`

Classification: **genuinely new, once-only Apply 1A infrastructure migration**.

It is the only active migration that should remain pending after truthful
history reconciliation. It depends on the current live schema represented by
the baseline, including `facilities`, `facility_sources`, and `import_runs`.
It also has bounded conditional role grants and ownership transfer for the two
named roles; it deliberately does not create roles.

The approved migration is unchanged. Its approved raw SHA-256 remains:
`5b893f371ee25adf16550370d312c2a227578e2af562bebe46e383a29a3c81d7`.

## 4. Read-only equivalence gates completed

The baseline gate used read-only production catalog queries for schemas,
extensions, relations, columns, defaults, generated expressions, constraints,
indexes, functions, triggers, RLS, policies, ownership, ACLs, and default
privileges. A CLI schema dump was also attempted with `--linked --schema
public`; the CLI could not use it because Docker was unavailable, so no dump or
DDL was executed. The catalog comparison covered the same material object
classes directly.

The application-owned production inventory matched the baseline exactly:

- 18 tables, including the unlogged `toilet_map_import_staging` table;
- 245 application-table columns, including the generated geography column;
- 66 constraints;
- 56 indexes including constraint-backed indexes, with all 35 explicit index
  definitions matching;
- 33 policies across 18 RLS-enabled tables;
- one `facilities_updated_at` trigger;
- six application-owned public functions and zero application sequences;
- matching schema/table/function ACLs and both `postgres` and
  `supabase_admin` public default-privilege sets.

The production application-column digest is
`eef780add990dbb1028b64023691e2ac707eaa4a501bf84127af1c265b3224a4`, and the
per-table digests matched the independently parsed baseline for all 18 tables.
PostGIS relations (`geography_columns`, `geometry_columns`, and
`spatial_ref_sys`) and hosted extensions are managed-platform objects and were
accounted for separately; they are not application drift.

Exactly one superseded object was allowed:

```text
public.find_nearest_facilities
  -> superseded by 20260806000100_repair_find_nearest_facilities.sql
  -> RPC_REPAIR_EQUIVALENCE=PASS
```

The production RPC identity is
`find_nearest_facilities(double precision, double precision, integer, integer)`;
it is PL/pgSQL, `STABLE`, `SECURITY INVOKER`, owned by `postgres`, configured
with `search_path=public`, and has the repaired published-only PostGIS query,
validation, return shape, and stable distance/name ordering. Its production
definition is materially equivalent to the repair migration. The obsolete
`20260725_postgis_nearest_facility_rpc.sql` remains historical only.

Therefore the completed gates are:

```text
BASELINE_EQUIVALENCE = PASS
RPC_REPAIR_EQUIVALENCE = PASS
```

## 5. Proposed migration-history reconciliation

The proposed reconciliation is metadata-only and must be separately
authorized. It does not execute historical SQL, modify the live function, or
touch facility, provenance, source-link, audit, role, or grant data.

### No historical-file replay

Do not move the legacy files back into the active directory. Do not rename the
baseline to make it resemble an old migration. Do not invent stubs whose names
claim that the two unrecorded `20260725` files were separately applied. The
legacy SQL remains available for audit and lineage review under its exact git
path.

### Proposed repairs

Each repair is a separate future command and requires a fresh read-only
precondition check plus an explicit owner gate:

```text
supabase migration repair --status applied 20260806000000
supabase migration repair --status applied 20260806000100
```

| Version | Proposed state | Why | Evidence required immediately before repair | Risk if incorrect |
|---|---|---|---|---|
| `20260806000000` | `applied` | The file is a schema-only snapshot of the already-live schema, not a forward production delta. Marking it applied prevents `db push` from trying to replay the baseline. | Full read-only schema comparison against the baseline, including tables, columns, constraints, indexes, functions, triggers, policies, grants, extensions, and schemas; current facility/source/provenance snapshot unchanged. | A false repair would tell the CLI to skip schema that is actually missing, causing later migration failure or an unrecorded schema gap. |
| `20260806000100` | `applied` | The repaired function definition is already present in production, and the Git change records live application/verification. Marking it applied records the existing effect without replacing the function again. | Exact signature/owner/security/search-path/return-shape/body/grant comparison to the approved repair, plus a read-only RPC smoke query. | A false repair would leave the old broken RPC while the CLI believes the repair exists. The repair must be deployed as a separately authorized forward change if equality cannot be proven. |

No repair is proposed for `001`, `20260624`, `20260625`, `20260701`, or
`20260725`: those versions already exist remotely. No repair is proposed for
the two extra legacy `20260725` files because there is no truthful distinct
remote version to mark and their effects are represented by the baseline/current
schema.

After the two proposed repairs, the exact local-only pending set should be:

```text
20260811164202_apply_1a_audit_and_transaction.sql
```

The expected remote migration table would contain the five historical rows plus
the two truthful applied markers. Any other row, local file, or pending SQL is a
stop condition.

## 6. Bounded production roles

### Recommended mechanism

The repository should contain `supabase/roles.sql`. It is now present as a
secret-free, idempotent definition of exactly the disposable-tested role
attributes. Supabase CLI's `db push --include-roles` is the supported mechanism
for including that file in a migration push, but it must be used only after its
dry-run has been inspected. The file can also be reviewed/executed verbatim by
an owner-controlled SQL Editor or secure Postgres session when a separate
role-only approval is required.

The local file creates or normalizes only:

```text
relief_apply_owner     NOLOGIN NOSUPERUSER NOCREATEDB NOCREATEROLE NOINHERIT
relief_apply_operator  LOGIN   NOSUPERUSER NOCREATEDB NOCREATEROLE NOINHERIT
```

It also grants `relief_apply_owner` to the hosted `postgres` deployment role so
the non-superuser migration executor can transfer ownership of the
`SECURITY DEFINER` Apply function to the NOLOGIN owner. This is a bounded
bootstrap membership, not an application-role grant; it does not grant
`relief_apply_operator` membership or any broad table/schema privilege. The
Apply migration itself remains the source of the exact object-level grants.

The current hosted `postgres` role is `NOSUPERUSER` but has `CREATEROLE` and
`CREATEDB`, while the Supabase-managed `supabase_admin` is the superuser. The
bounded custom-role definition does not request superuser, replication,
createdb, createrole, or bypass-RLS privileges. If the hosted CLI path refuses
the membership/role DDL, stop and use the supported owner-controlled SQL Editor
or admin session; do not add privileges to the Apply roles to work around it.

### Credential and invocation model

`LOGIN` is necessary for the selected architecture because a controlled
server-side Apply runner authenticates directly to Postgres as
`relief_apply_operator`. The operator role is not a mobile/API identity. The
mobile app, anon key, authenticated role, and `service_role` must not call the
function.

The roles file intentionally has no `PASSWORD` clause. A future owner-approved
credential step must set a randomly generated operator secret outside this
repository, store it only in the server-side deployment runner/secret manager,
redact it from CLI output and logs, and never expose it through any
`EXPO_PUBLIC_*` variable or mobile bundle. Rotation is a controlled password
replacement followed by runner-secret replacement and a connection check;
disablement is `NOLOGIN` plus removal of the runner secret. No credential was
generated or changed in this task.

Using an Edge Function with `service_role` would reduce password custody but
would not preserve the disposable-tested least-privilege boundary because
`service_role` is a broad bypass-RLS identity. Do not substitute it for the
dedicated operator role without a new security design and test.

## 7. Future production deployment sequence

The following is the proposed order. Every production mutation is gated
separately; no step below was executed here.

1. **Read-only readiness.** Authenticate the unchanged CLI version, link the
   checkout to `bgwxrxkmyaihplaloely`, verify the linked ref exactly, capture
   branch/HEAD/CLI version, run `supabase migration list`, and capture a fresh
   facility/source/provenance snapshot. Abort on any identity or data drift.
2. **Read-only lineage proof.** Compare the full production schema to the
   baseline, compare the live RPC definition to the repair migration, and
   confirm the five historical remote rows. Preview the expected history repair
   set; do not repair yet.
3. **Owner Gate A — migration history only.** Authorize only the two
   `status=applied` repairs listed above. Run them one at a time, capture the
   result, and immediately re-run migration listing and direct read-only
   history queries. No `db push` is allowed before this verification passes.
4. **Read-only post-repair check.** Confirm the remote/local comparison has no
   unexpected version, the baseline and repair are both recorded as applied,
   and the only local-only pending migration is `20260811164202`.
5. **Owner Gate B — role provisioning.** Review `supabase/roles.sql`, approve
   only its two bounded role definitions and the owner-to-`postgres` bootstrap
   membership, then provision them through the owner-controlled SQL path or a
   narrowly scoped CLI role operation. Do not use a normal `db push --include-roles`
   as a presumed role-only command while Apply 1A is still pending; the CLI can
   bundle pending migrations.
6. **Secure operator credential step.** Set the operator password through the
   approved secret-handling path, store it server-side only, and verify role
   attributes without printing password material. This is a separate approval
   from role DDL and was not performed here.
7. **Role verification.** Confirm both role attribute tuples exactly, confirm
   the owner membership needed for ownership transfer, and confirm there are no
   extra memberships or broad grants. Do not proceed if the roles differ from
   the disposable-tested design.
8. **Owner Gate C — Apply infrastructure deployment.** Run and inspect:

   ```text
   supabase db push --dry-run --include-roles
   ```

   The dry-run may show the idempotent role file plus the single approved Apply
   migration. It must not show the baseline, the RPC repair, any historical
   migration, an unexpected migration, or unrelated SQL. If it does, stop.
9. **Pre-deployment read-only gate.** Take a fresh production snapshot, confirm
   the prior snapshot is unchanged or explain every difference, rerun the
   GET-only Apply 1A preflight, and require exactly 48 READY / 0 STALE with the
   frozen plan, manifest, source, project, and engine identities.
10. **Owner Gate D — infrastructure migration.** Only after the dry-run and
    preflight are approved, run the approved `supabase db push --include-roles`
    command. This deploys schema/control metadata and roles only; it does not
    authorize the Apply function call.
11. **Post-migration verification.** Run the complete checklist in section 7,
    recapture facility/source/provenance snapshots, and confirm that no Apply
    audit transaction exists and no facility data changed.
12. **Owner Gate E — first live Apply.** Keep `LIVE_EXECUTION_ENABLED=False`
    until a new owner authorization explicitly approves the exact 48-operation
    transaction. The server-side operator runner must revalidate all frozen
    hashes and preflight results immediately before calling the function.

## 8. Post-migration / pre-Apply verification checklist

All checks are read-only and must pass together:

- migration history contains exactly the five historical versions,
  `20260806000000`, `20260806000100`, and the newly applied Apply migration;
  no unknown or reverted row exists;
- the migration file SHA, plan SHA, manifest SHA, source SHA, review commit,
  project ref, engine version, 48-operation count, and field distribution are
  unchanged;
- both roles exist with the exact approved attributes; operator password
  material is not selected or logged; owner membership is bounded;
- `private.apply_relief_toilet_map_1a(text,text,text,text,text)` exists exactly
  once, is `SECURITY DEFINER`, has the approved owner, and has a fixed empty
  `search_path`/fully-qualified implementation;
- execute is absent from `PUBLIC`, `anon`, and `authenticated`, and present
  only for `relief_apply_operator` as intended;
- private schema usage, approval-registry access, facility column updates, and
  `import_runs` audit rights match the migration's explicit grants; no broad
  table update/delete grant exists;
- the immutable registry contains exactly 48 rows, its operation identities,
  hashes, timestamps, and field distribution match the approved manifest, and
  its immutable trigger is present;
- `public.import_runs` has the Apply columns, constraints, lookup index, and
  committed-only unique manifest index, with zero Apply run rows;
- facility count, source-link count, source-link digest, publication values,
  and all relevant provenance values equal the fresh pre-deployment snapshot;
- the GET-only preflight is exactly 48 READY / 0 STALE;
- no Apply function invocation has occurred, no facility/provenance/source
  mutation occurred during deployment, and `LIVE_EXECUTION_ENABLED` remains
  `False`.

## 9. Failure and rollback analysis

| Stage | Failure mode | Atomicity / resulting state | Required response |
|---|---|---|---|
| History repair | Wrong version marked applied or unexpected remote row | Migration metadata changes are separate from schema/data transactions. A wrong marker can hide a needed migration. | Stop immediately, preserve CLI/direct-history output, and obtain a new owner-authorized corrective repair. Never compensate by replaying the baseline. |
| Role provisioning | Role exists with wrong attributes, membership, or partial DDL | Role DDL may persist independently of a later migration push. It does not alter facility data, but it changes authentication/ownership state. | Re-read attributes and memberships; use a narrowly reviewed forward normalization or owner-approved removal only after dependency review. Never grant superuser/bypass-RLS/broad memberships. |
| Operator credential | Password leaks, is logged, or cannot be tested | Credential state is independent of migration transaction. | Do not continue; rotate/revoke through the secret owner, scrub logs, and re-run the credential gate. No secret belongs in git. |
| RPC repair | Function body/signature differs or repair is unexpectedly pending | The repair is a function replacement, not a harmless history operation. A failed transactional migration should roll back its own SQL, but an already-present differing function needs investigation. | Prefer history repair only when exact equivalence is proven. Otherwise stop for a separately approved forward repair; do not broaden the RPC or replay the broken legacy definition. |
| Apply migration | DDL, grant, ownership, registry seed, or constraint step fails | The migration is wrapped in `BEGIN`/`COMMIT`; a failure should roll back its schema objects and seed rows. Role DDL performed separately may remain. | Capture CLI output, recheck migration history and schema, confirm no data mutation, keep roles bounded, and fix forward only after review. Do not blindly rerun a once-only migration. |
| Post-migration verification | Unexpected object, grant, audit row, snapshot change, or preflight STALE | The infrastructure migration may be committed while the Apply transaction remains uncalled. | Freeze all Apply activity, preserve before/after snapshots, and do not enable live execution. Forward correction is preferred to destructive rollback unless an owner approves rollback. |
| First live Apply | Stale row, stronger provenance, source mismatch, concurrency, or runtime error | The Apply function is designed as one transaction; facility/provenance writes must roll back together and record safe rollback evidence. | Treat any non-committed result as no deployment success; take a fresh preflight before retry. A schema rollback cannot undo already committed enrichment data, so data correction requires a separate reviewed procedure. |

Immediate stop conditions are any target/ref mismatch, unauthorised migration,
role drift, unexpected dry-run SQL, unexplained snapshot change, non-exact
48/0 preflight, failed identity/hash check, or any evidence of a live Apply
call.

## 10. Files changed and validation

The authorized local package contains:

- `supabase/roles.sql` — new, secret-free bounded role definition;
- `docs/data/TOILET_MAP_APPLY_1A_PRODUCTION_RECONCILIATION_DESIGN.md` — this
  reconciliation and deployment-gate design.

The approved Apply migration and all historical migration SQL are unchanged.
No production migration metadata was changed. No production role or grant was
changed.

Validation for this package must include:

- static review of `roles.sql` for the exact role attributes, no password
  clause, no superuser/bypass-RLS/create-role/create-db request, and no broad
  grants;
- the existing Apply 1A Python tests and manifest/plan integrity checks;
- `git diff --check`;
- final branch/HEAD/status capture.

At the reconciliation checkpoint, the package is limited to these two files and
is ready for the separately authorized checkpoint commit. The production
history repairs remain gated below and are not implied by this local commit.

## 11. Recommendation

The design and read-only equivalence gates are sufficiently specific for the
separately authorized history-repair step. Production is not yet ready for
infrastructure deployment authorization until both metadata repairs, the fresh
data/preflight gate, and the dry-run have completed exactly as specified. The
current checkpoint status is:

**READY FOR MIGRATION-HISTORY RECONCILIATION AUTHORIZATION**

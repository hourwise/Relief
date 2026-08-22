# NaPTAN N4A — migration readiness

Candidate migration: `supabase/migrations/20260822170000_naptan_transport_source_graph.sql`

Candidate migration SHA-256: `087A389B8CEAC021B12708BC55C39022CB38D5459510EFFB6CF057CEF232C44E`

## Scope

The migration is additive and creates only the five private source-graph tables. It has no inserts, updates, deletes, backfills, facility references, source-observation writes, toilet writes, import-run writes, or public API objects. It adds snapshot-scoped unique constraints, same-snapshot composite foreign keys, bounded coordinate checks, indexes, and existing `update_updated_at()` triggers.

## Security

RLS is enabled on every new table. Table privileges are revoked from `public`, `anon`, and `authenticated`; `service_role` receives the intended governed access. No permissive policies are created. This is the same fail-closed posture used for private provenance/source-observation data.

## Validation gate

Static migration validation checks all expected table definitions, the security boundary, and forbidden DML patterns. Focused fixture tests validate replay and projection behavior. No local database execution was available/required for this bounded batch, so the correct classification is `STATIC_MIGRATION_VALIDATED / LIVE_DATABASE_VALIDATION_REQUIRED`. The migration must not be deployed until a separate transaction performs live schema validation.

Generated production database types are intentionally not changed: the candidate migration is unapplied, and adding generated types now would falsely claim the production schema exists. The Python contract module supplies typed/deterministic repository tooling without exposing the model to the app.

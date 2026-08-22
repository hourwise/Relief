# RELIEF TfL Source-Observation Model — Local Implementation Report

**Classification:** `RELIEF TFL SOURCE-OBSERVATION MODEL — SCHEMA IMPLEMENTED AND LOCALLY VALIDATED / PRODUCTION DEPLOYMENT NOT AUTHORIZED`

## Starting state

- Repository: `hourwise/Relief`
- Branch: `codex/toilet-map-apply-1a-production-deploy`
- Starting local SHA: `610ca76a9f4d75ce3581cf1024ab96ab2eb40454`
- Starting remote SHA: `610ca76a9f4d75ce3581cf1024ab96ab2eb40454`
- Commit message: `docs(data): audit TfL facility-level toilet observations`
- Protected working-tree changes preserved and not staged: `.easignore`, `app.json`, `docs/EAS_CONFIG_AUDIT.md`

## Previous audit basis

The previous audit established 14 unique TfL source observations represented by 28 overlapping operation entries: 14 `SOURCE_LINK` entries and 14 `ENRICHMENT` entries. The frozen source proves facility-level/source-level attributes but does not prove physical toilet topology. The implementation therefore preserves source observations without creating physical units or overwriting canonical facilities.

Frozen evidence remains:

- ZIP SHA-256: `19c50772febd1a3d7625f59e079b7590c5da4ed70424d6f552cfd7db1611e2ce`
- ZIP size: `186,973` bytes
- Retrieval UTC: `2026-08-21T06:08:20.1476469Z`
- Reconciliation SHA-256: `65cc9cc8c41b7b3a003524610b674c7f2eae96ff7fe5116f38f2d2856cb777cb`
- Required attribution: `Data provided by Transport for London`
- The TfL feed was not refreshed or redownloaded.

## Schema implemented

Migration: `supabase/migrations/20260822092938_facility_source_observations.sql`

Table: `public.facility_source_observations`

- Primary key: repository-standard UUID with `gen_random_uuid()`.
- Provenance: required FK to `facility_sources.id`, `ON DELETE CASCADE`.
- Optional future unit link: nullable FK to `toilet_units.id`, `ON DELETE RESTRICT`; it cannot be populated by this migration or source ingestion.
- Deterministic identity: non-empty `observation_key`, unique within `facility_source_id`.
- Attributes: non-null `observed_attributes jsonb`, retaining source-specific fields without copying them into `facilities`.
- Coordinate semantics: `coordinate_scope` is constrained to `NONE`, `FACILITY_LEVEL`, `STATION_LEVEL`, or `TOILET_LEVEL`. TfL observations use `STATION_LEVEL`; no toilet coordinates are created.
- Physical semantics: `physical_unit_asserted` defaults to `false`; the normal state requires `toilet_unit_id IS NULL` and `unit_link_status = 'UNLINKED'`.
- Future linked state: `physical_unit_asserted = true` requires a non-null unit link and either `CONFIRMED_DISTINCT_UNIT` or `SAME_UNIT_MULTI_SOURCE`.
- Timestamps: `first_seen_at`, `last_seen_at`, `created_at`, and `updated_at` use repository `timestamptz` conventions.
- Indexes: provenance FK, current observations by provenance, and nullable future unit links. No map/search indexes were added.
- Trigger: shared `public.update_updated_at()` trigger only updates the observation row timestamp.

The migration is additive, contains no backfill, and contains no TfL inserts, staging writes, import-run creation, or canonical updates.

## Security

- RLS is enabled on `facility_source_observations`.
- No policies are created, so there is no public, `anon`, or `authenticated` read/write path.
- `public`, `anon`, and `authenticated` table privileges are explicitly revoked.
- `service_role` receives the existing governed server-side table privilege pattern.
- No existing grants or policies on `facilities`, `facility_sources`, `toilet_units`, or `toilet_unit_sources` are changed.
- No public application query or UI path was added.

This follows Supabase’s two-layer Data API model: grants determine reachability and RLS determines row access. Both are fail-closed for this provenance table. See the [Supabase Data API security guidance](https://supabase.com/docs/guides/api/securing-your-api).

## Semantic safety

- A source row is not a physical toilet unit.
- A unique TfL source ID is not treated as a unit identity.
- Observations do not modify facility name, address, town, coordinates, accessibility, baby-changing, opening, fee, or other canonical fields.
- Station-level coordinates remain station-level.
- No topology is inferred from gender, accessibility, baby changing, fee status, row order, source ID, shared location text, multiple rows, or station coordinates.
- The migration has no propagation trigger from observations to canonical facilities.

## 14-observation validation

The committed audit JSON was used as a deterministic fixture. All 14 unique TfL observations remain representable with their source identities and observed attributes.

- Observations representable: `14/14`
- Duplicate logical observations prevented: yes, by `(facility_source_id, observation_key)` uniqueness
- Physical units required: `0`
- Physical units created: `0`
- Physical-unit mappings inferred: `0`
- Canonical facility enrichments required: `0`
- Toilet-specific coordinates inferred: `0`

The fixture keeps all rows in `REQUIRES_ADDITIVE_SOURCE_OBSERVATION_MODEL` and retains `physical_unit_asserted = false`.

## Future adjudication path

1. A governed importer creates or resolves the appropriate `facility_sources` provenance row.
2. It inserts or updates one observation using the deterministic `(facility_source_id, observation_key)` key.
3. The observation remains unlinked while physical topology is unknown.
4. A separate human/governed process independently verifies a physical `toilet_units` row.
5. That process may set `toilet_unit_id`, `physical_unit_asserted`, and an allowed link status together.
6. The original source identity, observed JSONB attributes, timestamps, and provenance remain unchanged.

No adjudication workflow or importer is implemented in this transaction.

## Production safety

Production deployment is not authorized and was not attempted.

- Production migrations applied: `0`
- Production observations inserted: `0`
- Production facility mutations: `0`
- Production toilet units created: `0`
- Production promotion operations: `0`
- Production mutations total: `0`

Read-only verification remained unchanged at 15,620 facilities, 15,620 facility_sources, 5 import_runs, 0 staging rows, 0 toilet_units, and 0 toilet_unit_sources.

## Validation

The final transaction report records the exact command results. The bounded validation set includes:

- migration static semantic/security tests;
- 14-observation JSON fixture validation;
- Python compilation and focused source-expansion tests;
- TypeScript typecheck;
- existing JavaScript/TypeScript repository test runner;
- JSON parsing and invariant validation;
- `git diff --check`;
- bounded secret-pattern scan;
- read-only production count/RLS/grant verification.

No EAS, Gradle, Expo prebuild, Android, APK, or production deployment tooling was run.

## Files created / changed

- `supabase/migrations/20260822092938_facility_source_observations.sql`
- `src/types/database.types.ts`
- `src/types/facilitySourceObservations.ts`
- `__tests__/facilitySourceObservationSchema.test.ts`
- `docs/data/RELIEF_TFL_SOURCE_OBSERVATION_MODEL_IMPLEMENTATION_2026-08-22.md`

## Git result

- Starting SHA: `610ca76a9f4d75ce3581cf1024ab96ab2eb40454`
- Final SHA: recorded in the final transaction report after the bounded commit.
- Commit message: `feat(data): add facility source observations`
- Push: authorized only after validation; no force-push, amend, merge, or rebase.
- Protected files remain untouched and unstaged.

## Final classification

`RELIEF TFL SOURCE-OBSERVATION MODEL — SCHEMA IMPLEMENTED AND LOCALLY VALIDATED / PRODUCTION DEPLOYMENT NOT AUTHORIZED`

Production deployment and TfL observation ingestion remain separate future transactions and are unauthorized.

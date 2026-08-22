# Relief TfL source-observation model — production deployment verification

## Final classification

**RELIEF TFL SOURCE-OBSERVATION MODEL — PRODUCTION SCHEMA DEPLOYED AND VERIFIED / TFL INGESTION NOT AUTHORIZED**

This report covers one production schema deployment only. TfL source observations were not ingested and no TfL promotion path was executed.

## Starting state

- Repository: `hourwise/Relief`
- Branch: `codex/toilet-map-apply-1a-production-deploy`
- Local starting SHA: `321c18991cad191683619cdce4e1acfd222e986e`
- Remote starting SHA: `321c18991cad191683619cdce4e1acfd222e986e`
- Starting commit: `feat(data): add facility source observations`
- Protected working-tree changes preserved byte-for-byte and left unstaged:
  - `.easignore`
  - `app.json`
  - `docs/EAS_CONFIG_AUDIT.md`

The migration file was verified unchanged from `HEAD` before deployment.

## Production target

- Supabase project ref: `bgwxrxkmyaihplaloely`
- Project name: `Relief`
- Project status: `ACTIVE_HEALTHY`
- Region: `eu-central-1`
- Target identity was independently verified before deployment.

## Migration preflight

- Authorized migration file: `supabase/migrations/20260822092938_facility_source_observations.sql`
- Migration SHA-256: `f57e32cb44c68a247ffe1cba0df4241ea91259324acef592422826d7c26eae0d`
- Previous production migration head: `20260821213435 add_toilet_unit_model`
- Repository predecessor: `20260821211239_add_toilet_unit_model.sql`
- Repository/production timestamp differences for earlier migrations are the known documented deployment mappings; no unknown predecessor or migration-history divergence was found.
- Pending semantic migration before deployment: exactly the authorized source-observation migration.

The committed SQL was statically reviewed immediately before deployment. It contained only additive DDL, constraints, indexes, trigger creation, RLS enablement, and the intended role grants/revokes. It contained no DML, backfill, canonical facility mutation, toilet-unit creation, staging operation, import-run creation, promotion RPC, or TfL ingestion path.

## Pre-deploy production counts

| Object | Count/state |
| --- | ---: |
| `facilities` | 15,620 |
| `facility_sources` | 15,620 |
| `import_runs` | 5 |
| `toilet_map_import_staging` | 0 |
| `toilet_units` | 0 |
| `toilet_unit_sources` | 0 |
| `facility_source_observations` | absent |

## Deployment

The exact committed migration was applied through the established Supabase migration workflow. The deployment returned success and no data-row operation was included.

- Migration file applied: `20260822092938_facility_source_observations.sql`
- Application result: success
- Production ledger entry after deployment: `20260822100920 facility_source_observations`
- The ledger timestamp differs from the repository filename prefix because the deployment workflow assigned the applied migration timestamp; the applied SQL content was the exact committed file identified above.

## Production schema verification

`public.facility_source_observations` exists with the intended schema:

- UUID primary key `id`, default `gen_random_uuid()`.
- Required `facility_source_id` foreign key to `facility_sources.id`, `ON DELETE CASCADE`.
- Required non-empty `observation_key`.
- `observation_kind`, default `TOILET_PROVISION`.
- Structured `observed_attributes jsonb`, default `{}`.
- `coordinate_scope`, default `NONE`, constrained to `NONE`, `FACILITY_LEVEL`, `STATION_LEVEL`, or `TOILET_LEVEL`.
- `physical_unit_asserted`, `NOT NULL DEFAULT false`.
- Nullable `toilet_unit_id` foreign key to `toilet_units.id`, `ON DELETE RESTRICT`.
- `unit_link_status`, default `UNLINKED`, constrained to the governed link states.
- `source_schema_version`, nullable.
- `first_seen_at`, `last_seen_at`, `created_at`, and `updated_at` timestamp columns with the intended defaults.
- `is_current`, `NOT NULL DEFAULT true`.

Verified constraints include:

- primary key;
- required facility-source foreign key;
- optional toilet-unit foreign key with restrictive deletion;
- unique `(facility_source_id, observation_key)` identity;
- non-empty observation key and kind checks;
- coordinate-scope check;
- physical assertion/link-status consistency check;
- `TOILET_LEVEL` coordinates require an explicit linked physical unit and physical assertion.

Verified indexes include:

- unique observation identity index;
- primary key index;
- `(facility_source_id)` provenance index;
- `(facility_source_id, is_current)` current-observation index;
- partial `toilet_unit_id` index for linked observations.

The `set_facility_source_observations_updated_at` `BEFORE UPDATE` trigger is installed and invokes the existing `update_updated_at()` function.

## Security verification

- RLS: enabled.
- Policies: zero policies on the new table.
- `public`: no table privileges.
- `anon`: no table privileges.
- `authenticated`: no table privileges.
- `service_role`: intended privileged table access only; the database owner also appears in catalog privilege results as expected.

The new table is therefore fail-closed for public Data API roles at both the grant and policy layers. No public source-observation read path was added, and no existing table’s RLS or grants were changed.

## Post-deploy production counts

| Object | Pre-deploy | Post-deploy | Delta caused by this migration |
| --- | ---: | ---: | ---: |
| `facilities` | 15,620 | 15,620 | 0 |
| `facility_sources` | 15,620 | 15,620 | 0 |
| `import_runs` | 5 | 5 | 0 |
| `toilet_map_import_staging` | 0 | 0 | 0 |
| `toilet_units` | 0 | 0 | 0 |
| `toilet_unit_sources` | 0 | 0 | 0 |
| `facility_source_observations` | absent | 0 | schema only |

The production migration ledger records the new migration as applied. No observation rows exist.

## TfL safety declaration

This transaction did not ingest or promote TfL data:

- TfL source observations ingested: **0**
- Facility-source links created: **0**
- Canonical facility enrichments: **0**
- Toilet units created: **0**
- Toilet-unit source links created: **0**
- Import runs created: **0**
- Staging rows created: **0**
- Promotion/apply RPC calls: **0**
- Total production data mutations: **0**

The schema deployment did not manufacture physical-unit topology or toilet-specific coordinates.

## Validation

All checks completed without running prohibited native tooling:

- Migration SHA-256 and working-tree-versus-`HEAD` comparison: passed.
- Static migration DML/security scope scan: passed; no data mutation or public access path found.
- Production catalog verification of columns, defaults, constraints, foreign keys, indexes, trigger, RLS, policies, and grants: passed.
- Python compilation for the TfL audit tooling: passed.
- Focused Python test suite: **24 passed, 0 failed**.
- TypeScript typecheck (`npm.cmd run typecheck`): passed.
- Full lightweight repository runner: **24 test files passed**.
- Source-observation schema test within the repository runner: **23 assertions passed**.
- Temporary test output was redirected to a disposable repository-local D: workspace directory because of the known C: drive/Node temporary-path issue; the directory was removed after the run.
- No EAS, Gradle, Expo prebuild, Android, APK, or native build command was run.

## Files created / changed

This deployment-evidence transaction added exactly:

- `docs/data/RELIEF_TFL_SOURCE_OBSERVATION_MODEL_PRODUCTION_DEPLOYMENT_2026-08-22.md`

The migration, generated types, and tests were already committed in `321c18991cad191683619cdce4e1acfd222e986e` and were not modified by this deployment transaction.

## Git result

- Starting SHA: `321c18991cad191683619cdce4e1acfd222e986e`
- Deployment-evidence commit: recorded after final staged-diff review
- Protected files remain untouched, unstaged, and uncommitted.
- No amend, force-push, merge, or rebase was used.

## Final classification

**RELIEF TFL SOURCE-OBSERVATION MODEL — PRODUCTION SCHEMA DEPLOYED AND VERIFIED / TFL INGESTION NOT AUTHORIZED**

The next TfL observation-ingestion or promotion transaction remains separately unauthorized.

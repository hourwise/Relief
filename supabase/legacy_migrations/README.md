# Legacy migrations — historical only, NOT applied by the CLI

These seven SQL files are the original hand-written migrations. They were
never tracked in git (the whole `supabase/` directory was previously listed in
`.gitignore`), so GitHub had no record of the database at all.

They have been moved out of `supabase/migrations/` because they no longer
describe the live database accurately, and applying them in order would not
reproduce it. The clearest example is
`20260725_postgis_nearest_facility_rpc.sql`, which declares
`find_nearest_facilities()` over six columns that do not exist on
`facilities`:

- `is_water_refill_station`
- `is_shower_facility`
- `is_breastfeeding_room`
- `is_rest_area`
- `is_changing_place`
- `is_ev_charging`

That is the defect that made "Need One Now" fail at runtime with
PostgreSQL error `42703`.

## What replaced them

`supabase/migrations/20260806000000_live_schema_baseline.sql` — exported from
the running database with `pg_dump --schema-only --schema=public` on
2026-08-06. That file, not these, is the source of truth for the schema.

Keep these for provenance and code archaeology. Do not use them for
implementation decisions, and do not move them back into `migrations/`.

// Node typings are intentionally not part of the mobile app dependency graph.
// @ts-expect-error -- the test runner executes this under Node via tsx.
import { readFileSync } from 'node:fs';
import { assertEqual, assertTrue, section } from './helpers/harness';

const migration = readFileSync(
  new URL('../supabase/migrations/20260821211239_add_toilet_unit_model.sql', import.meta.url),
  'utf8',
);

section('additive toilet-unit migration boundary');

assertTrue(
  'creates the parent child table',
  migration.includes('create table public.toilet_units'),
);
assertTrue(
  'creates the unit source table',
  migration.includes('create table public.toilet_unit_sources'),
);
assertTrue(
  'unit source identity is strongly unique',
  migration.includes('unique (source_name, source_record_id)'),
);
assertTrue(
  'unit rows require a facility foreign key',
  migration.includes('references public.facilities(id) on delete cascade'),
);
assertTrue(
  'unit source rows require a unit foreign key',
  migration.includes('references public.toilet_units(id) on delete cascade'),
);
assertTrue(
  'both new tables enable RLS',
  migration.includes('alter table public.toilet_units enable row level security') &&
    migration.includes('alter table public.toilet_unit_sources enable row level security'),
);
assertTrue(
  'source rows are not exposed to public Data API roles',
  migration.includes('revoke all on table public.toilet_unit_sources from public, anon, authenticated') &&
    !migration.includes('Published toilet unit sources are viewable') &&
    migration.includes('grant select on table public.toilet_units to anon, authenticated'),
);
assertTrue(
  'child coordinates cannot be station-level coordinates',
  migration.includes("coordinate_precision = 'TOILET_LEVEL'::text") &&
    migration.includes("coordinate_precision = 'UNKNOWN'::text and latitude is null and longitude is null"),
);
assertTrue(
  'unresolved physical rows cannot be published as canonical units',
  migration.includes('toilet_units_published_identity_check') &&
    migration.includes("publication_status <> 'published'::text"),
);
assertEqual(
  'migration contains no TfL or staging insert path',
  /insert\s+into\s+public\.(toilet_units|toilet_unit_sources|toilet_map_import_staging)/i.test(migration),
  false,
);

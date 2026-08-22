// Node typings are intentionally not part of the mobile app dependency graph.
// @ts-expect-error -- the test runner executes this under Node via tsx.
import { readFileSync } from 'node:fs';
import { assertEqual, assertTrue, section } from './helpers/harness';

const migration = readFileSync(
  new URL('../supabase/migrations/20260822092938_facility_source_observations.sql', import.meta.url),
  'utf8',
);
const audit = JSON.parse(
  readFileSync(
    new URL('../docs/data/RELIEF_TFL_EXISTING_PARENT_SOURCE_OBSERVATION_AUDIT_2026-08-22.json', import.meta.url),
    'utf8',
  ),
) as {
  rows: Array<{
    source_identity: { source_record_id: string };
    source_facts: Record<string, unknown>;
    outcome: string;
    physical_unit_asserted: boolean;
    physical_unit_mapping_inferred: boolean;
  }>;
};

section('facility source observation migration boundary');

assertTrue(
  'creates the additive source observation table',
  migration.includes('create table public.facility_source_observations'),
);
assertTrue(
  'has a strong provenance foreign key',
  migration.includes('references public.facility_sources(id)') &&
    migration.includes('on delete cascade'),
);
assertTrue(
  'has a nullable future physical-unit foreign key',
  migration.includes('references public.toilet_units(id)') &&
    migration.includes('on delete restrict'),
);
assertTrue(
  'observation identity is deterministic within provenance',
  migration.includes('unique (facility_source_id, observation_key)'),
);
assertTrue(
  'observation keys cannot be blank',
  migration.includes('length(btrim(observation_key)) > 0'),
);
assertTrue(
  'observed attributes use structured JSONB',
  migration.includes('observed_attributes jsonb') &&
    migration.includes("observed_attributes jsonb default '{}'::jsonb not null"),
);
assertTrue(
  'station-level coordinates have an explicit scope',
  migration.includes('coordinate_scope text') &&
    migration.includes("'STATION_LEVEL'::text"),
);
assertTrue(
  'unlinked observations default to non-physical',
  migration.includes('physical_unit_asserted boolean default false not null') &&
    migration.includes("unit_link_status text default 'UNLINKED'::text not null"),
);
assertTrue(
  'physical semantics require an explicit governed unit relationship',
  migration.includes('physical_unit_asserted = false') &&
    migration.includes('toilet_unit_id is null') &&
    migration.includes('physical_unit_asserted = true') &&
    migration.includes('toilet_unit_id is not null'),
);
assertTrue(
  'toilet-level coordinate scope requires a physical relationship',
  migration.includes("coordinate_scope <> 'TOILET_LEVEL'::text") &&
    migration.includes('physical_unit_asserted = true'),
);
assertTrue(
  'RLS is enabled with no public observation policy',
  migration.includes('alter table public.facility_source_observations enable row level security') &&
    !migration.includes('create policy'),
);
assertTrue(
  'Data API roles are explicitly revoked',
  migration.includes(
    'revoke all on table public.facility_source_observations from public, anon, authenticated',
  ),
);
assertTrue(
  'canonical overwrite and apply paths are absent',
  !/update\s+public\.(facilities|facility_sources)/i.test(migration) &&
    !/insert\s+into\s+public\.(facilities|facility_sources|toilet_units|toilet_unit_sources|toilet_map_import_staging)/i.test(migration),
);

section('14 frozen TfL source observations');

assertEqual('all 14 unique observations remain representable', audit.rows.length, 14);
assertEqual(
  'source identities remain unique',
  new Set(audit.rows.map((row) => row.source_identity.source_record_id)).size,
  14,
);
assertTrue(
  'every observation retains source attributes',
  audit.rows.every((row) => Object.keys(row.source_facts).length > 0),
);
assertTrue(
  'no physical units are asserted or inferred',
  audit.rows.every(
    (row) => !row.physical_unit_asserted && !row.physical_unit_mapping_inferred,
  ),
);
assertTrue(
  'all rows remain observation-model candidates',
  audit.rows.every((row) => row.outcome === 'REQUIRES_ADDITIVE_SOURCE_OBSERVATION_MODEL'),
);
assertTrue(
  'station-level precision is retained',
  audit.rows.every(
    (row) =>
      row.source_facts.positional_precision ===
      'STATION_LEVEL_ONLY; TOILET_COORDINATES_NOT_PROVIDED',
  ),
);

section('idempotency and future adjudication contract');

assertTrue(
  'same source key repeats resolve through the unique constraint',
  migration.includes('facility_source_observations_identity_key') &&
    migration.includes('facility_source_id, observation_key'),
);
assertTrue(
  'different observation keys may coexist under one provenance row',
  migration.includes('unique (facility_source_id, observation_key)') &&
    !migration.includes('unique (facility_source_id)'),
);
assertTrue(
  'source identity remains separate from physical-unit identity',
  migration.includes('source-observation identity') &&
    migration.includes('physical_unit_asserted'),
);
assertTrue(
  'future linking preserves provenance through a retained observation row',
  migration.includes('source identity and observed evidence remain unchanged'),
);

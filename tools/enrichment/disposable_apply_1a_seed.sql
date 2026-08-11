-- Disposable-only seed that derives every identity from the deployed,
-- immutable approved registry. Run after the real Apply 1A migration.

BEGIN;

WITH target_facilities AS (
  SELECT facility_id,
         row_number() OVER (ORDER BY facility_id) AS fixture_number
  FROM (
    SELECT DISTINCT facility_id
    FROM private.relief_apply_1a_approved_operations
  ) AS distinct_facilities
)
INSERT INTO public.facilities (
  id, name, address, latitude, longitude, postcode, town, country,
  is_free, is_accessible, has_baby_changing, is_gender_neutral,
  requires_radar_key, publication_status, verification_status,
  field_provenance
)
SELECT
  facility_id,
  'Disposable Apply 1A fixture ' || fixture_number,
  fixture_number || ' Test Street',
  53.400000 + fixture_number / 100000.0,
  -2.990000 - fixture_number / 100000.0,
  'L1 1AA',
  'Liverpool',
  'GB',
  NULL,
  NULL,
  NULL,
  NULL,
  NULL,
  CASE WHEN fixture_number % 2 = 0 THEN 'published' ELSE 'hidden' END,
  'source_imported',
  CASE fixture_number % 3
    WHEN 1 THEN '{}'::jsonb
    WHEN 2 THEN jsonb_build_object(
      'unrelated_fixture_key',
      jsonb_build_object('source', 'fixture-only', 'value', fixture_number)
    )
    ELSE jsonb_build_object(
      'unrelated_fixture_key',
      jsonb_build_object('source', 'fixture-only', 'value', fixture_number),
      (
        SELECT field
        FROM private.relief_apply_1a_approved_operations AS compatible
        WHERE compatible.facility_id = target_facilities.facility_id
        ORDER BY compatible.operation_id
        LIMIT 1
      ),
      jsonb_build_object(
        'source', 'Toilet Map UK',
        'verification_status', 'source_imported',
        'note', 'compatible disposable fixture provenance'
      )
    )
  END
FROM target_facilities;

-- One non-target row proves the function does not create/delete or otherwise
-- alter unrelated facilities.
INSERT INTO public.facilities (
  id, name, address, latitude, longitude, postcode, town, country,
  is_free, publication_status, verification_status, field_provenance
)
VALUES (
  '00000000-0000-0000-0000-000000000002'::uuid,
  'Unrelated disposable fixture',
  '99 Control Street',
  53.4500,
  -2.9500,
  'L2 2BB',
  'Liverpool',
  'GB',
  true,
  'published',
  'source_imported',
  '{"unrelated_fixture_key":{"source":"fixture-only","value":"preserve"}}'::jsonb
)
ON CONFLICT (id) DO NOTHING;

INSERT INTO public.facility_sources (
  facility_id,
  import_run_id,
  source_name,
  source_record_id,
  source_url,
  source_licence,
  source_updated_at,
  first_seen_at,
  last_seen_at,
  is_current,
  raw_data
)
SELECT
  operation.facility_id,
  '00000000-0000-0000-0000-000000000001'::uuid,
  'Toilet Map UK',
  operation.source_record_id,
  'https://www.toiletmap.org.uk/fixture/' || operation.source_record_id,
  'Open Government Licence',
  operation.source_updated_at,
  '2026-08-11T00:00:00Z'::timestamptz,
  '2026-08-11T00:01:00Z'::timestamptz,
  true,
  jsonb_build_object('fixture', true, 'source_record_id', operation.source_record_id)
FROM (
  SELECT DISTINCT ON (facility_id, source_record_id)
    facility_id, source_record_id, source_updated_at
  FROM private.relief_apply_1a_approved_operations
  ORDER BY facility_id, source_record_id, operation_id
) AS operation;

COMMIT;

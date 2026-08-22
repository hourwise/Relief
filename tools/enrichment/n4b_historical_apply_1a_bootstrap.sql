\set ON_ERROR_STOP on

-- N4B.1 disposable-only reconstruction of the accepted historical Apply 1A
-- prerequisite. This is not a migration and must never be run against a
-- production database. It uses the immutable registry created by the
-- canonical Apply migration and the exact audit identities recorded in the
-- committed Apply 1A sealing evidence.

BEGIN;

DO $$
DECLARE
  registry_count bigint;
  distinct_project_refs bigint;
  distinct_plan_hashes bigint;
  distinct_manifest_hashes bigint;
  distinct_source_hashes bigint;
  distinct_review_commits bigint;
  distinct_engine_versions bigint;
BEGIN
  SELECT count(*), count(DISTINCT project_ref), count(DISTINCT approved_plan_sha256),
         count(DISTINCT approved_manifest_sha256), count(DISTINCT source_checksum),
         count(DISTINCT approved_review_commit), count(DISTINCT apply_engine_version)
  INTO registry_count, distinct_project_refs, distinct_plan_hashes,
       distinct_manifest_hashes, distinct_source_hashes, distinct_review_commits,
       distinct_engine_versions
  FROM private.relief_apply_1a_approved_operations;

  IF registry_count <> 48
     OR distinct_project_refs <> 1
     OR distinct_plan_hashes <> 1
     OR distinct_manifest_hashes <> 1
     OR distinct_source_hashes <> 1
     OR distinct_review_commits <> 1
     OR distinct_engine_versions <> 1
  THEN
    RAISE EXCEPTION 'N4B historical bootstrap refused: immutable Apply 1A registry identity is not exactly one 48-row approved set';
  END IF;

  IF EXISTS (
    SELECT 1
    FROM private.relief_apply_1a_approved_operations
    WHERE source_name <> 'Toilet Map UK'
       OR matching_basis <> 'EXACT_SOURCE_ID'
       OR confidence <> 'HIGH'
       OR expected_current_value IS NOT NULL
       OR source_checksum <> lower(source_checksum)
       OR approved_plan_sha256 <> lower(approved_plan_sha256)
       OR approved_manifest_sha256 <> lower(approved_manifest_sha256)
  ) THEN
    RAISE EXCEPTION 'N4B historical bootstrap refused: approved registry shape changed';
  END IF;
END;
$$;

-- This is the pre-existing source import run needed by the committed
-- disposable Apply 1A seed. It is not an Apply audit row and carries no
-- production data. The exact source identity is the committed source
-- checksum used by the registry and the Apply 1A evidence.
INSERT INTO public.import_runs (
  id, source_name, source_file_name, source_checksum, status,
  started_at, completed_at, rows_received, rows_valid, rows_inserted
)
VALUES (
  '00000000-0000-0000-0000-000000000001'::uuid,
  'Toilet Map UK',
  'TOILET_MAP_APPLY_1A_DISPOSABLE_SOURCE.json',
  (SELECT min(source_checksum) FROM private.relief_apply_1a_approved_operations),
  'completed',
  '2026-08-11T00:00:00Z'::timestamptz,
  '2026-08-11T00:01:00Z'::timestamptz,
  48, 48, 48
)
ON CONFLICT (id) DO NOTHING;

DO $$
BEGIN
  IF (SELECT count(*) FROM public.import_runs WHERE id = '00000000-0000-0000-0000-000000000001'::uuid) <> 1
     OR (SELECT count(*) FROM public.import_runs WHERE id = '00000000-0000-0000-0000-000000000001'::uuid
         AND source_name = 'Toilet Map UK'
         AND lower(source_checksum) = (SELECT min(source_checksum) FROM private.relief_apply_1a_approved_operations)
         AND status = 'completed'
         AND rows_received = 48
         AND rows_valid = 48
         AND rows_inserted = 48) <> 1
  THEN
    RAISE EXCEPTION 'N4B historical bootstrap refused: disposable source import prerequisite is not exact';
  END IF;
END;
$$;

COMMIT;

-- Reuse the committed disposable target/source fixture, then make all
-- synthetic target facilities satisfy the already-canonical published-row
-- policy used by the Apply function. No canonical facility is touched.
\ir disposable_apply_1a_seed.sql

BEGIN;
ALTER TABLE public.facilities ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS "Published facilities are viewable by everyone" ON public.facilities;
CREATE POLICY "Published facilities are viewable by everyone"
ON public.facilities
FOR SELECT
TO PUBLIC
USING (publication_status = 'published'::text);

UPDATE public.facilities AS f
SET publication_status = 'published'
WHERE EXISTS (
  SELECT 1
  FROM private.relief_apply_1a_approved_operations AS r
  WHERE r.facility_id = f.id
);

DO $$
BEGIN
  IF (SELECT count(*) FROM private.relief_apply_1a_approved_operations) <> 48
     OR (SELECT count(DISTINCT facility_id) FROM private.relief_apply_1a_approved_operations) <> 25
     OR (SELECT count(*) FROM public.facilities) <> 26
     OR (SELECT count(*) FROM public.facility_sources) <> 25
     OR (SELECT count(*) FROM public.facilities WHERE publication_status = 'published') <> 25
     OR (SELECT count(*) FROM private.relief_apply_1a_approved_operations AS r
         JOIN public.facilities AS f ON f.id = r.facility_id
         WHERE CASE r.field
           WHEN 'has_baby_changing' THEN f.has_baby_changing
           WHEN 'requires_radar_key' THEN f.requires_radar_key
           WHEN 'is_gender_neutral' THEN f.is_gender_neutral
           WHEN 'is_accessible' THEN f.is_accessible
           WHEN 'is_free' THEN f.is_free
         END IS NOT NULL) <> 0
  THEN
    RAISE EXCEPTION 'N4B historical bootstrap refused: synthetic Apply target fixture is not the committed 48-operation shape';
  END IF;
END;
$$;
COMMIT;

-- First reproduce the recorded rolled-back attempt using the committed
-- disposable fault harness. The function call derives every identity from
-- the immutable registry rather than embedding a production project ref.
\ir disposable_apply_1a_postcheck_fault.sql

BEGIN;
SET LOCAL ROLE relief_apply_owner;
DO $$
DECLARE
  result jsonb;
BEGIN
  SELECT private.apply_relief_toilet_map_1a(
    (SELECT min(project_ref) FROM private.relief_apply_1a_approved_operations),
    (SELECT min(approved_plan_sha256) FROM private.relief_apply_1a_approved_operations),
    (SELECT min(approved_manifest_sha256) FROM private.relief_apply_1a_approved_operations),
    (SELECT min(source_checksum) FROM private.relief_apply_1a_approved_operations),
    'APPLY_RELIEF_TOILET_MAP_1A_48'
  ) INTO result;
  IF result ->> 'status' <> 'ROLLED_BACK'
     OR (result ->> 'applied_count')::integer <> 0
     OR (result ->> 'mutations_committed')::boolean IS DISTINCT FROM false
  THEN
    RAISE EXCEPTION 'N4B historical bootstrap expected the recorded rolled-back Apply attempt, got %', result;
  END IF;
END;
$$;
COMMIT;

DROP TRIGGER disposable_apply_1a_postcheck_trip_trigger ON public.facilities;
DROP FUNCTION public.disposable_apply_1a_postcheck_trip();

BEGIN;
SET LOCAL ROLE relief_apply_owner;
DO $$
DECLARE
  result jsonb;
BEGIN
  SELECT private.apply_relief_toilet_map_1a(
    (SELECT min(project_ref) FROM private.relief_apply_1a_approved_operations),
    (SELECT min(approved_plan_sha256) FROM private.relief_apply_1a_approved_operations),
    (SELECT min(approved_manifest_sha256) FROM private.relief_apply_1a_approved_operations),
    (SELECT min(source_checksum) FROM private.relief_apply_1a_approved_operations),
    'APPLY_RELIEF_TOILET_MAP_1A_48'
  ) INTO result;
  IF result ->> 'status' <> 'COMMITTED'
     OR (result ->> 'requested_operation_count')::integer <> 48
     OR (result ->> 'ready_count')::integer <> 48
     OR (result ->> 'applied_count')::integer <> 48
     OR (result ->> 'stale_count')::integer <> 0
     OR (result ->> 'failed_count')::integer <> 0
     OR (result ->> 'mutations_committed')::boolean IS DISTINCT FROM true
  THEN
    RAISE EXCEPTION 'N4B historical bootstrap expected the recorded committed Apply attempt, got %', result;
  END IF;
END;
$$;
COMMIT;

-- The committed sealing evidence binds the accepted historical audit rows to
-- these exact UUIDs. The disposable generated IDs are replaced only inside
-- this runner-local database, as in the committed sealing regression.
UPDATE public.import_runs
SET id = '676893a6-c7ac-4727-af82-4d6bb91faf9a'::uuid
WHERE run_kind = 'apply_1a' AND transaction_outcome = 'rolled_back';

UPDATE public.import_runs
SET id = '390f7338-2099-4953-ae47-f9e49ff3691c'::uuid
WHERE run_kind = 'apply_1a' AND transaction_outcome = 'committed';

DO $$
DECLARE
  committed_rows bigint;
  rolled_back_rows bigint;
BEGIN
  SELECT count(*) INTO committed_rows
  FROM public.import_runs
  WHERE id = '390f7338-2099-4953-ae47-f9e49ff3691c'::uuid
    AND run_kind = 'apply_1a'
    AND source_name = 'Toilet Map UK'
    AND source_file_name = 'TOILET_MAP_APPLY_1A_MANIFEST.json'
    AND lower(source_checksum) = (SELECT min(source_checksum) FROM private.relief_apply_1a_approved_operations)
    AND lower(approved_plan_sha256) = (SELECT min(approved_plan_sha256) FROM private.relief_apply_1a_approved_operations)
    AND lower(approved_manifest_sha256) = (SELECT min(approved_manifest_sha256) FROM private.relief_apply_1a_approved_operations)
    AND approved_review_commit = (SELECT min(approved_review_commit) FROM private.relief_apply_1a_approved_operations)
    AND apply_engine_version = (SELECT min(apply_engine_version) FROM private.relief_apply_1a_approved_operations)
    AND project_ref = (SELECT min(project_ref) FROM private.relief_apply_1a_approved_operations)
    AND status = 'completed'
    AND transaction_outcome = 'committed'
    AND requested_operation_count = 48
    AND ready_count = 48
    AND applied_count = 48
    AND stale_count = 0
    AND failed_count = 0
    AND rows_updated = 48;

  SELECT count(*) INTO rolled_back_rows
  FROM public.import_runs
  WHERE id = '676893a6-c7ac-4727-af82-4d6bb91faf9a'::uuid
    AND run_kind = 'apply_1a'
    AND status = 'failed'
    AND transaction_outcome = 'rolled_back'
    AND applied_count = 0
    AND rows_updated = 0;

  IF (SELECT count(*) FROM public.import_runs WHERE run_kind = 'apply_1a') <> 2
     OR committed_rows <> 1
     OR rolled_back_rows <> 1
     OR (SELECT count(*) FROM public.import_runs
         WHERE run_kind = 'apply_1a'
           AND lower(approved_manifest_sha256) = (SELECT min(approved_manifest_sha256) FROM private.relief_apply_1a_approved_operations)
           AND transaction_outcome = 'committed') <> 1
  THEN
    RAISE EXCEPTION 'N4B historical bootstrap did not reproduce exactly one committed and one rolled-back Apply audit row';
  END IF;
END;
$$;

SELECT 'N4B_HISTORICAL_APPLY_1A_BOOTSTRAP_PASSED' AS result;

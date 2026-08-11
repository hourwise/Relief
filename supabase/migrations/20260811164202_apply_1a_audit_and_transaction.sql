-- Relief Apply 1A privileged audit-run and database-boundary preparation
--
-- DESIGN-ONLY MIGRATION: this file has not been deployed to Supabase.
-- It contains the future bounded function and its private control metadata,
-- but no deployment or live Apply execution has occurred in this task.
-- The only seed INSERT is into the private immutable approval registry; the
-- function is the only path that can write public Apply audit/facility data.
--
-- Decision A: extend public.import_runs. The existing importer already owns
-- source identity, lifecycle timestamps, row counts, and error summaries.
-- Apply 1A is an enrichment/import run with additional approval identity and
-- transaction outcome fields, so a second run framework would be misleading.

BEGIN;

ALTER TABLE public.import_runs
  ADD COLUMN IF NOT EXISTS run_kind text NOT NULL DEFAULT 'import',
  ADD COLUMN IF NOT EXISTS approved_plan_sha256 text,
  ADD COLUMN IF NOT EXISTS approved_manifest_sha256 text,
  ADD COLUMN IF NOT EXISTS approved_review_commit text,
  ADD COLUMN IF NOT EXISTS apply_engine_version text,
  ADD COLUMN IF NOT EXISTS project_ref text,
  ADD COLUMN IF NOT EXISTS requested_operation_count integer NOT NULL DEFAULT 0,
  ADD COLUMN IF NOT EXISTS ready_count integer NOT NULL DEFAULT 0,
  ADD COLUMN IF NOT EXISTS applied_count integer NOT NULL DEFAULT 0,
  ADD COLUMN IF NOT EXISTS stale_count integer NOT NULL DEFAULT 0,
  ADD COLUMN IF NOT EXISTS failed_count integer NOT NULL DEFAULT 0,
  ADD COLUMN IF NOT EXISTS transaction_outcome text NOT NULL DEFAULT 'not_started',
  ADD COLUMN IF NOT EXISTS rollback_summary text;

DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1
    FROM pg_constraint
    WHERE conname = 'import_runs_run_kind_check'
      AND conrelid = 'public.import_runs'::regclass
  ) THEN
    ALTER TABLE public.import_runs
      ADD CONSTRAINT import_runs_run_kind_check
      CHECK (run_kind IN ('import', 'apply_1a'));
  END IF;

  IF NOT EXISTS (
    SELECT 1
    FROM pg_constraint
    WHERE conname = 'import_runs_transaction_outcome_check'
      AND conrelid = 'public.import_runs'::regclass
  ) THEN
    ALTER TABLE public.import_runs
      ADD CONSTRAINT import_runs_transaction_outcome_check
      CHECK (transaction_outcome IN (
        'not_started',
        'dry_run',
        'committed',
        'rolled_back',
        'failed',
        'already_applied'
      ));
  END IF;

  IF NOT EXISTS (
    SELECT 1
    FROM pg_constraint
    WHERE conname = 'import_runs_approval_hash_format_check'
      AND conrelid = 'public.import_runs'::regclass
  ) THEN
    ALTER TABLE public.import_runs
      ADD CONSTRAINT import_runs_approval_hash_format_check
      CHECK (
        (approved_plan_sha256 IS NULL OR approved_plan_sha256 ~ '^[0-9A-Fa-f]{64}$')
        AND (approved_manifest_sha256 IS NULL OR approved_manifest_sha256 ~ '^[0-9A-Fa-f]{64}$')
        AND (source_checksum IS NULL OR source_checksum ~ '^[0-9A-Fa-f]{64}$')
      );
  END IF;

  IF NOT EXISTS (
    SELECT 1
    FROM pg_constraint
    WHERE conname = 'import_runs_apply_1a_identity_check'
      AND conrelid = 'public.import_runs'::regclass
  ) THEN
    ALTER TABLE public.import_runs
      ADD CONSTRAINT import_runs_apply_1a_identity_check
      CHECK (
        run_kind <> 'apply_1a'
        OR (
          source_name = 'Toilet Map UK'
          AND lower(source_checksum) = 'f6824fdc7cd29df8c1f45ba749c1b28d319fb34803c55459bbe748ef65937624'
          AND lower(approved_plan_sha256) = '7400626bc99061af7ba82c29969fc8929d7394c59afcfe574e1880521bad2b45'
          AND lower(approved_manifest_sha256) = '1de1a71186b80ce043b48fc5f4d6c4bc6ed9d1c964b3ddf7ad3b96ddd073bfa0'
          AND approved_review_commit = '4710b9ec7a9f5a83aa9e7225400b8a6046ce0e77'
          AND apply_engine_version = 'relief.apply-engine-1a.v1'
          AND project_ref = 'bgwxrxkmyaihplaloely'
          AND requested_operation_count = 48
        )
      );
  END IF;

  IF NOT EXISTS (
    SELECT 1
    FROM pg_constraint
    WHERE conname = 'import_runs_apply_1a_outcome_check'
      AND conrelid = 'public.import_runs'::regclass
  ) THEN
    ALTER TABLE public.import_runs
      ADD CONSTRAINT import_runs_apply_1a_outcome_check
      CHECK (
        run_kind <> 'apply_1a'
        OR (
          requested_operation_count >= 0
          AND ready_count >= 0
          AND applied_count >= 0
          AND stale_count >= 0
          AND failed_count >= 0
          AND applied_count <= requested_operation_count
          AND ready_count <= requested_operation_count
          AND stale_count <= requested_operation_count
          AND failed_count <= requested_operation_count
        )
      );
  END IF;

  IF NOT EXISTS (
    SELECT 1
    FROM pg_constraint
    WHERE conname = 'import_runs_apply_1a_committed_check'
      AND conrelid = 'public.import_runs'::regclass
  ) THEN
    ALTER TABLE public.import_runs
      ADD CONSTRAINT import_runs_apply_1a_committed_check
      CHECK (
        transaction_outcome <> 'committed'
        OR (
          run_kind = 'apply_1a'
          AND status = 'completed'
          AND completed_at IS NOT NULL
          AND requested_operation_count = 48
          AND ready_count = 48
          AND applied_count = 48
          AND stale_count = 0
          AND failed_count = 0
        )
      );
  END IF;
END;
$$;

DROP INDEX IF EXISTS public.import_runs_apply_1a_manifest_key;

CREATE INDEX IF NOT EXISTS import_runs_apply_1a_manifest_lookup
  ON public.import_runs (run_kind, approved_manifest_sha256)
  WHERE run_kind = 'apply_1a' AND approved_manifest_sha256 IS NOT NULL;

CREATE UNIQUE INDEX IF NOT EXISTS import_runs_apply_1a_committed_manifest_key
  ON public.import_runs (run_kind, approved_manifest_sha256)
  WHERE run_kind = 'apply_1a'
    AND approved_manifest_sha256 IS NOT NULL
    AND transaction_outcome = 'committed';

COMMENT ON COLUMN public.import_runs.run_kind IS
  'Run family: import for the existing importer, apply_1a for the approved enrichment boundary.';
COMMENT ON COLUMN public.import_runs.transaction_outcome IS
  'Apply transaction result. committed is the only successful live mutation outcome.';
COMMENT ON COLUMN public.import_runs.rollback_summary IS
  'Operator-safe summary of a rejected or rolled-back Apply 1A attempt; never stores secrets.';

-- The registry is control metadata, not enrichment data. It is deliberately
-- private and seeded from the already approved manifest, so the future
-- function never trusts a caller-supplied operations array/hash pairing.
CREATE SCHEMA IF NOT EXISTS private;

REVOKE USAGE ON SCHEMA private FROM PUBLIC, anon, authenticated;

CREATE TABLE IF NOT EXISTS private.relief_apply_1a_approved_operations (
  operation_id text PRIMARY KEY,
  facility_id uuid NOT NULL,
  source_record_id text NOT NULL,
  field text NOT NULL,
  expected_current_value boolean,
  proposed_value boolean NOT NULL,
  source_updated_at timestamptz NOT NULL,
  matching_basis text NOT NULL,
  confidence text NOT NULL,
  source_name text NOT NULL,
  source_checksum text NOT NULL,
  approved_plan_sha256 text NOT NULL,
  approved_manifest_sha256 text NOT NULL,
  approved_review_commit text NOT NULL,
  apply_engine_version text NOT NULL,
  project_ref text NOT NULL,
  CONSTRAINT relief_apply_1a_approved_operations_identity_key
    UNIQUE (facility_id, source_record_id, field),
  CONSTRAINT relief_apply_1a_approved_operations_shape_check
    CHECK (
      field IN (
        'has_baby_changing',
        'requires_radar_key',
        'is_gender_neutral',
        'is_accessible',
        'is_free'
      )
      AND expected_current_value IS NULL
      AND matching_basis = 'EXACT_SOURCE_ID'
      AND confidence = 'HIGH'
      AND source_name = 'Toilet Map UK'
      AND source_checksum = lower(source_checksum)
      AND source_checksum ~ '^[0-9a-f]{64}$'
      AND approved_plan_sha256 = lower(approved_plan_sha256)
      AND approved_plan_sha256 ~ '^[0-9a-f]{64}$'
      AND approved_manifest_sha256 = lower(approved_manifest_sha256)
      AND approved_manifest_sha256 ~ '^[0-9a-f]{64}$'
    )
);

INSERT INTO private.relief_apply_1a_approved_operations (
  operation_id,
  facility_id,
  source_record_id,
  field,
  expected_current_value,
  proposed_value,
  source_updated_at,
  matching_basis,
  confidence,
  source_name,
  source_checksum,
  approved_plan_sha256,
  approved_review_commit,
  apply_engine_version,
  project_ref,
  approved_manifest_sha256
)
VALUES
    ('A1A-c5dbe77c3c08ad19', '0263f629-ce2e-415d-9a04-8ca326a98224'::uuid, '6edfb3b672f93d881c971075', 'requires_radar_key', NULL, true, '2026-08-09T01:00:29.193Z'::timestamptz, 'EXACT_SOURCE_ID', 'HIGH', 'Toilet Map UK', 'f6824fdc7cd29df8c1f45ba749c1b28d319fb34803c55459bbe748ef65937624', '7400626bc99061af7ba82c29969fc8929d7394c59afcfe574e1880521bad2b45', '4710b9ec7a9f5a83aa9e7225400b8a6046ce0e77', 'relief.apply-engine-1a.v1', 'bgwxrxkmyaihplaloely', '1de1a71186b80ce043b48fc5f4d6c4bc6ed9d1c964b3ddf7ad3b96ddd073bfa0'),
    ('A1A-942a34c2f2f43842', '0dab87d1-fc22-4681-9bb9-261592d5c124'::uuid, 'a715e37cd85cefda2cf7488f', 'has_baby_changing', NULL, true, '2026-08-06T10:12:02.202Z'::timestamptz, 'EXACT_SOURCE_ID', 'HIGH', 'Toilet Map UK', 'f6824fdc7cd29df8c1f45ba749c1b28d319fb34803c55459bbe748ef65937624', '7400626bc99061af7ba82c29969fc8929d7394c59afcfe574e1880521bad2b45', '4710b9ec7a9f5a83aa9e7225400b8a6046ce0e77', 'relief.apply-engine-1a.v1', 'bgwxrxkmyaihplaloely', '1de1a71186b80ce043b48fc5f4d6c4bc6ed9d1c964b3ddf7ad3b96ddd073bfa0'),
    ('A1A-131cef5192c07f27', '0dab87d1-fc22-4681-9bb9-261592d5c124'::uuid, 'a715e37cd85cefda2cf7488f', 'requires_radar_key', NULL, true, '2026-08-06T10:12:02.202Z'::timestamptz, 'EXACT_SOURCE_ID', 'HIGH', 'Toilet Map UK', 'f6824fdc7cd29df8c1f45ba749c1b28d319fb34803c55459bbe748ef65937624', '7400626bc99061af7ba82c29969fc8929d7394c59afcfe574e1880521bad2b45', '4710b9ec7a9f5a83aa9e7225400b8a6046ce0e77', 'relief.apply-engine-1a.v1', 'bgwxrxkmyaihplaloely', '1de1a71186b80ce043b48fc5f4d6c4bc6ed9d1c964b3ddf7ad3b96ddd073bfa0'),
    ('A1A-a710244c4057201b', '0ee69f7f-940d-44da-b53d-aaea3885f262'::uuid, 'acb5bd8c054de53ee570635e', 'is_gender_neutral', NULL, false, '2026-08-08T16:17:24.903Z'::timestamptz, 'EXACT_SOURCE_ID', 'HIGH', 'Toilet Map UK', 'f6824fdc7cd29df8c1f45ba749c1b28d319fb34803c55459bbe748ef65937624', '7400626bc99061af7ba82c29969fc8929d7394c59afcfe574e1880521bad2b45', '4710b9ec7a9f5a83aa9e7225400b8a6046ce0e77', 'relief.apply-engine-1a.v1', 'bgwxrxkmyaihplaloely', '1de1a71186b80ce043b48fc5f4d6c4bc6ed9d1c964b3ddf7ad3b96ddd073bfa0'),
    ('A1A-fcd6a18b9db47cf2', '14be9cfa-9925-4690-aa9e-95f984971dcb'::uuid, 'ce574c14a011cf31129647bd', 'is_gender_neutral', NULL, false, '2026-07-30T10:04:53.066Z'::timestamptz, 'EXACT_SOURCE_ID', 'HIGH', 'Toilet Map UK', 'f6824fdc7cd29df8c1f45ba749c1b28d319fb34803c55459bbe748ef65937624', '7400626bc99061af7ba82c29969fc8929d7394c59afcfe574e1880521bad2b45', '4710b9ec7a9f5a83aa9e7225400b8a6046ce0e77', 'relief.apply-engine-1a.v1', 'bgwxrxkmyaihplaloely', '1de1a71186b80ce043b48fc5f4d6c4bc6ed9d1c964b3ddf7ad3b96ddd073bfa0'),
    ('A1A-6e56d5fa754ed9d4', '1952126a-2910-43e6-a3b9-0b3a6cca0030'::uuid, 'd07b48635f4c6704deb97183', 'has_baby_changing', NULL, true, '2026-08-06T10:33:28.386Z'::timestamptz, 'EXACT_SOURCE_ID', 'HIGH', 'Toilet Map UK', 'f6824fdc7cd29df8c1f45ba749c1b28d319fb34803c55459bbe748ef65937624', '7400626bc99061af7ba82c29969fc8929d7394c59afcfe574e1880521bad2b45', '4710b9ec7a9f5a83aa9e7225400b8a6046ce0e77', 'relief.apply-engine-1a.v1', 'bgwxrxkmyaihplaloely', '1de1a71186b80ce043b48fc5f4d6c4bc6ed9d1c964b3ddf7ad3b96ddd073bfa0'),
    ('A1A-6b0cd475fe2068df', '1952126a-2910-43e6-a3b9-0b3a6cca0030'::uuid, 'd07b48635f4c6704deb97183', 'requires_radar_key', NULL, false, '2026-08-06T10:33:28.386Z'::timestamptz, 'EXACT_SOURCE_ID', 'HIGH', 'Toilet Map UK', 'f6824fdc7cd29df8c1f45ba749c1b28d319fb34803c55459bbe748ef65937624', '7400626bc99061af7ba82c29969fc8929d7394c59afcfe574e1880521bad2b45', '4710b9ec7a9f5a83aa9e7225400b8a6046ce0e77', 'relief.apply-engine-1a.v1', 'bgwxrxkmyaihplaloely', '1de1a71186b80ce043b48fc5f4d6c4bc6ed9d1c964b3ddf7ad3b96ddd073bfa0'),
    ('A1A-85fa5a8044acc84a', '41bb7d76-9416-4e46-a065-7a51c9735d0e'::uuid, '85b55c1bf2609e112e0dfb0f', 'is_free', NULL, true, '2026-08-05T18:24:10.663Z'::timestamptz, 'EXACT_SOURCE_ID', 'HIGH', 'Toilet Map UK', 'f6824fdc7cd29df8c1f45ba749c1b28d319fb34803c55459bbe748ef65937624', '7400626bc99061af7ba82c29969fc8929d7394c59afcfe574e1880521bad2b45', '4710b9ec7a9f5a83aa9e7225400b8a6046ce0e77', 'relief.apply-engine-1a.v1', 'bgwxrxkmyaihplaloely', '1de1a71186b80ce043b48fc5f4d6c4bc6ed9d1c964b3ddf7ad3b96ddd073bfa0'),
    ('A1A-75321260fe546b96', '43d0fa52-7ee2-453a-9400-5fefa07dc4e8'::uuid, '3596d85e074dbcee6eb47e42', 'is_gender_neutral', NULL, false, '2026-07-28T13:15:58.635Z'::timestamptz, 'EXACT_SOURCE_ID', 'HIGH', 'Toilet Map UK', 'f6824fdc7cd29df8c1f45ba749c1b28d319fb34803c55459bbe748ef65937624', '7400626bc99061af7ba82c29969fc8929d7394c59afcfe574e1880521bad2b45', '4710b9ec7a9f5a83aa9e7225400b8a6046ce0e77', 'relief.apply-engine-1a.v1', 'bgwxrxkmyaihplaloely', '1de1a71186b80ce043b48fc5f4d6c4bc6ed9d1c964b3ddf7ad3b96ddd073bfa0'),
    ('A1A-03a30b1bd39c996f', '43d0fa52-7ee2-453a-9400-5fefa07dc4e8'::uuid, '3596d85e074dbcee6eb47e42', 'requires_radar_key', NULL, false, '2026-07-28T13:15:58.635Z'::timestamptz, 'EXACT_SOURCE_ID', 'HIGH', 'Toilet Map UK', 'f6824fdc7cd29df8c1f45ba749c1b28d319fb34803c55459bbe748ef65937624', '7400626bc99061af7ba82c29969fc8929d7394c59afcfe574e1880521bad2b45', '4710b9ec7a9f5a83aa9e7225400b8a6046ce0e77', 'relief.apply-engine-1a.v1', 'bgwxrxkmyaihplaloely', '1de1a71186b80ce043b48fc5f4d6c4bc6ed9d1c964b3ddf7ad3b96ddd073bfa0'),
    ('A1A-2c7ae5aec54deae4', '46fccd66-378c-47dc-91d6-16b33b36b2fe'::uuid, 'bd1a4cf729701d698457c96a', 'has_baby_changing', NULL, true, '2026-08-06T10:42:05.301Z'::timestamptz, 'EXACT_SOURCE_ID', 'HIGH', 'Toilet Map UK', 'f6824fdc7cd29df8c1f45ba749c1b28d319fb34803c55459bbe748ef65937624', '7400626bc99061af7ba82c29969fc8929d7394c59afcfe574e1880521bad2b45', '4710b9ec7a9f5a83aa9e7225400b8a6046ce0e77', 'relief.apply-engine-1a.v1', 'bgwxrxkmyaihplaloely', '1de1a71186b80ce043b48fc5f4d6c4bc6ed9d1c964b3ddf7ad3b96ddd073bfa0'),
    ('A1A-780d5f061b6f248e', '46fccd66-378c-47dc-91d6-16b33b36b2fe'::uuid, 'bd1a4cf729701d698457c96a', 'requires_radar_key', NULL, true, '2026-08-06T10:42:05.301Z'::timestamptz, 'EXACT_SOURCE_ID', 'HIGH', 'Toilet Map UK', 'f6824fdc7cd29df8c1f45ba749c1b28d319fb34803c55459bbe748ef65937624', '7400626bc99061af7ba82c29969fc8929d7394c59afcfe574e1880521bad2b45', '4710b9ec7a9f5a83aa9e7225400b8a6046ce0e77', 'relief.apply-engine-1a.v1', 'bgwxrxkmyaihplaloely', '1de1a71186b80ce043b48fc5f4d6c4bc6ed9d1c964b3ddf7ad3b96ddd073bfa0'),
    ('A1A-a90af4b597bb25fc', '4a6cff49-1286-47e2-8c0e-9678638e08b6'::uuid, '1e71d9a13cbb1d1f32455bff', 'is_gender_neutral', NULL, false, '2026-08-02T11:54:49.701Z'::timestamptz, 'EXACT_SOURCE_ID', 'HIGH', 'Toilet Map UK', 'f6824fdc7cd29df8c1f45ba749c1b28d319fb34803c55459bbe748ef65937624', '7400626bc99061af7ba82c29969fc8929d7394c59afcfe574e1880521bad2b45', '4710b9ec7a9f5a83aa9e7225400b8a6046ce0e77', 'relief.apply-engine-1a.v1', 'bgwxrxkmyaihplaloely', '1de1a71186b80ce043b48fc5f4d6c4bc6ed9d1c964b3ddf7ad3b96ddd073bfa0'),
    ('A1A-7e3ff5fb6865fb99', '4cddc62f-71e0-4106-a1aa-13080a6a2934'::uuid, '439082c9b8bdf249c7799223', 'is_gender_neutral', NULL, false, '2026-07-25T14:18:39.616Z'::timestamptz, 'EXACT_SOURCE_ID', 'HIGH', 'Toilet Map UK', 'f6824fdc7cd29df8c1f45ba749c1b28d319fb34803c55459bbe748ef65937624', '7400626bc99061af7ba82c29969fc8929d7394c59afcfe574e1880521bad2b45', '4710b9ec7a9f5a83aa9e7225400b8a6046ce0e77', 'relief.apply-engine-1a.v1', 'bgwxrxkmyaihplaloely', '1de1a71186b80ce043b48fc5f4d6c4bc6ed9d1c964b3ddf7ad3b96ddd073bfa0'),
    ('A1A-25bc3d6c2c00c96a', '4cddc62f-71e0-4106-a1aa-13080a6a2934'::uuid, '439082c9b8bdf249c7799223', 'requires_radar_key', NULL, true, '2026-07-25T14:18:39.616Z'::timestamptz, 'EXACT_SOURCE_ID', 'HIGH', 'Toilet Map UK', 'f6824fdc7cd29df8c1f45ba749c1b28d319fb34803c55459bbe748ef65937624', '7400626bc99061af7ba82c29969fc8929d7394c59afcfe574e1880521bad2b45', '4710b9ec7a9f5a83aa9e7225400b8a6046ce0e77', 'relief.apply-engine-1a.v1', 'bgwxrxkmyaihplaloely', '1de1a71186b80ce043b48fc5f4d6c4bc6ed9d1c964b3ddf7ad3b96ddd073bfa0'),
    ('A1A-37aa8efbc6d58174', '5742c567-92c6-47f3-b755-9c936886d905'::uuid, '1050bb89634e172910d88402', 'has_baby_changing', NULL, true, '2026-08-04T12:14:45.044Z'::timestamptz, 'EXACT_SOURCE_ID', 'HIGH', 'Toilet Map UK', 'f6824fdc7cd29df8c1f45ba749c1b28d319fb34803c55459bbe748ef65937624', '7400626bc99061af7ba82c29969fc8929d7394c59afcfe574e1880521bad2b45', '4710b9ec7a9f5a83aa9e7225400b8a6046ce0e77', 'relief.apply-engine-1a.v1', 'bgwxrxkmyaihplaloely', '1de1a71186b80ce043b48fc5f4d6c4bc6ed9d1c964b3ddf7ad3b96ddd073bfa0'),
    ('A1A-7c11865f296a4aee', '5742c567-92c6-47f3-b755-9c936886d905'::uuid, '1050bb89634e172910d88402', 'is_gender_neutral', NULL, true, '2026-08-04T12:14:45.044Z'::timestamptz, 'EXACT_SOURCE_ID', 'HIGH', 'Toilet Map UK', 'f6824fdc7cd29df8c1f45ba749c1b28d319fb34803c55459bbe748ef65937624', '7400626bc99061af7ba82c29969fc8929d7394c59afcfe574e1880521bad2b45', '4710b9ec7a9f5a83aa9e7225400b8a6046ce0e77', 'relief.apply-engine-1a.v1', 'bgwxrxkmyaihplaloely', '1de1a71186b80ce043b48fc5f4d6c4bc6ed9d1c964b3ddf7ad3b96ddd073bfa0'),
    ('A1A-9eae67b1ab6e9c68', '5742c567-92c6-47f3-b755-9c936886d905'::uuid, '1050bb89634e172910d88402', 'requires_radar_key', NULL, true, '2026-08-04T12:14:45.044Z'::timestamptz, 'EXACT_SOURCE_ID', 'HIGH', 'Toilet Map UK', 'f6824fdc7cd29df8c1f45ba749c1b28d319fb34803c55459bbe748ef65937624', '7400626bc99061af7ba82c29969fc8929d7394c59afcfe574e1880521bad2b45', '4710b9ec7a9f5a83aa9e7225400b8a6046ce0e77', 'relief.apply-engine-1a.v1', 'bgwxrxkmyaihplaloely', '1de1a71186b80ce043b48fc5f4d6c4bc6ed9d1c964b3ddf7ad3b96ddd073bfa0'),
    ('A1A-4718b4db01684dc5', '5d9e20fd-4e64-417e-9942-11472e59c715'::uuid, '717915db1407696a7aeca883', 'is_gender_neutral', NULL, false, '2026-08-03T02:13:35.389Z'::timestamptz, 'EXACT_SOURCE_ID', 'HIGH', 'Toilet Map UK', 'f6824fdc7cd29df8c1f45ba749c1b28d319fb34803c55459bbe748ef65937624', '7400626bc99061af7ba82c29969fc8929d7394c59afcfe574e1880521bad2b45', '4710b9ec7a9f5a83aa9e7225400b8a6046ce0e77', 'relief.apply-engine-1a.v1', 'bgwxrxkmyaihplaloely', '1de1a71186b80ce043b48fc5f4d6c4bc6ed9d1c964b3ddf7ad3b96ddd073bfa0'),
    ('A1A-1649d4a9bf6c901d', '5d9e20fd-4e64-417e-9942-11472e59c715'::uuid, '717915db1407696a7aeca883', 'requires_radar_key', NULL, true, '2026-08-03T02:13:35.389Z'::timestamptz, 'EXACT_SOURCE_ID', 'HIGH', 'Toilet Map UK', 'f6824fdc7cd29df8c1f45ba749c1b28d319fb34803c55459bbe748ef65937624', '7400626bc99061af7ba82c29969fc8929d7394c59afcfe574e1880521bad2b45', '4710b9ec7a9f5a83aa9e7225400b8a6046ce0e77', 'relief.apply-engine-1a.v1', 'bgwxrxkmyaihplaloely', '1de1a71186b80ce043b48fc5f4d6c4bc6ed9d1c964b3ddf7ad3b96ddd073bfa0'),
    ('A1A-a43bc3a0623396af', '6067c02c-993c-426c-b0ea-100b11b658df'::uuid, 'd6a814c2f04e92c2cc621951', 'has_baby_changing', NULL, false, '2026-08-03T02:11:28.423Z'::timestamptz, 'EXACT_SOURCE_ID', 'HIGH', 'Toilet Map UK', 'f6824fdc7cd29df8c1f45ba749c1b28d319fb34803c55459bbe748ef65937624', '7400626bc99061af7ba82c29969fc8929d7394c59afcfe574e1880521bad2b45', '4710b9ec7a9f5a83aa9e7225400b8a6046ce0e77', 'relief.apply-engine-1a.v1', 'bgwxrxkmyaihplaloely', '1de1a71186b80ce043b48fc5f4d6c4bc6ed9d1c964b3ddf7ad3b96ddd073bfa0'),
    ('A1A-784a29a612e94f7b', '7b7c91a5-febf-4999-9cc6-cb94b81ab99c'::uuid, 'f0f4b839449d3f093fcd40cb', 'has_baby_changing', NULL, true, '2026-08-10T14:10:09.588Z'::timestamptz, 'EXACT_SOURCE_ID', 'HIGH', 'Toilet Map UK', 'f6824fdc7cd29df8c1f45ba749c1b28d319fb34803c55459bbe748ef65937624', '7400626bc99061af7ba82c29969fc8929d7394c59afcfe574e1880521bad2b45', '4710b9ec7a9f5a83aa9e7225400b8a6046ce0e77', 'relief.apply-engine-1a.v1', 'bgwxrxkmyaihplaloely', '1de1a71186b80ce043b48fc5f4d6c4bc6ed9d1c964b3ddf7ad3b96ddd073bfa0'),
    ('A1A-33b20081f975a751', '7c5bbff3-1cfa-4d3e-916f-c89d12ff584a'::uuid, 'c5f65b256609c21ce0b3d170', 'is_accessible', NULL, true, '2026-08-07T10:31:44.518Z'::timestamptz, 'EXACT_SOURCE_ID', 'HIGH', 'Toilet Map UK', 'f6824fdc7cd29df8c1f45ba749c1b28d319fb34803c55459bbe748ef65937624', '7400626bc99061af7ba82c29969fc8929d7394c59afcfe574e1880521bad2b45', '4710b9ec7a9f5a83aa9e7225400b8a6046ce0e77', 'relief.apply-engine-1a.v1', 'bgwxrxkmyaihplaloely', '1de1a71186b80ce043b48fc5f4d6c4bc6ed9d1c964b3ddf7ad3b96ddd073bfa0'),
    ('A1A-0a21d1a5fb98b3e5', '7c5bbff3-1cfa-4d3e-916f-c89d12ff584a'::uuid, 'c5f65b256609c21ce0b3d170', 'is_gender_neutral', NULL, true, '2026-08-07T10:31:44.518Z'::timestamptz, 'EXACT_SOURCE_ID', 'HIGH', 'Toilet Map UK', 'f6824fdc7cd29df8c1f45ba749c1b28d319fb34803c55459bbe748ef65937624', '7400626bc99061af7ba82c29969fc8929d7394c59afcfe574e1880521bad2b45', '4710b9ec7a9f5a83aa9e7225400b8a6046ce0e77', 'relief.apply-engine-1a.v1', 'bgwxrxkmyaihplaloely', '1de1a71186b80ce043b48fc5f4d6c4bc6ed9d1c964b3ddf7ad3b96ddd073bfa0'),
    ('A1A-4b1851d440f08952', '88e5418e-2dbd-454e-9c6f-af53c5e45780'::uuid, '72d4de0ff7f5180a8c1ac83d', 'has_baby_changing', NULL, true, '2026-08-03T06:09:44.139Z'::timestamptz, 'EXACT_SOURCE_ID', 'HIGH', 'Toilet Map UK', 'f6824fdc7cd29df8c1f45ba749c1b28d319fb34803c55459bbe748ef65937624', '7400626bc99061af7ba82c29969fc8929d7394c59afcfe574e1880521bad2b45', '4710b9ec7a9f5a83aa9e7225400b8a6046ce0e77', 'relief.apply-engine-1a.v1', 'bgwxrxkmyaihplaloely', '1de1a71186b80ce043b48fc5f4d6c4bc6ed9d1c964b3ddf7ad3b96ddd073bfa0'),
    ('A1A-a5eee1368da842f2', '88e5418e-2dbd-454e-9c6f-af53c5e45780'::uuid, '72d4de0ff7f5180a8c1ac83d', 'is_gender_neutral', NULL, false, '2026-08-03T06:09:44.139Z'::timestamptz, 'EXACT_SOURCE_ID', 'HIGH', 'Toilet Map UK', 'f6824fdc7cd29df8c1f45ba749c1b28d319fb34803c55459bbe748ef65937624', '7400626bc99061af7ba82c29969fc8929d7394c59afcfe574e1880521bad2b45', '4710b9ec7a9f5a83aa9e7225400b8a6046ce0e77', 'relief.apply-engine-1a.v1', 'bgwxrxkmyaihplaloely', '1de1a71186b80ce043b48fc5f4d6c4bc6ed9d1c964b3ddf7ad3b96ddd073bfa0'),
    ('A1A-4ef92af4fd47ce10', '88e5418e-2dbd-454e-9c6f-af53c5e45780'::uuid, '72d4de0ff7f5180a8c1ac83d', 'requires_radar_key', NULL, true, '2026-08-03T06:09:44.139Z'::timestamptz, 'EXACT_SOURCE_ID', 'HIGH', 'Toilet Map UK', 'f6824fdc7cd29df8c1f45ba749c1b28d319fb34803c55459bbe748ef65937624', '7400626bc99061af7ba82c29969fc8929d7394c59afcfe574e1880521bad2b45', '4710b9ec7a9f5a83aa9e7225400b8a6046ce0e77', 'relief.apply-engine-1a.v1', 'bgwxrxkmyaihplaloely', '1de1a71186b80ce043b48fc5f4d6c4bc6ed9d1c964b3ddf7ad3b96ddd073bfa0'),
    ('A1A-89868359bdc93f84', '8c838ebd-4939-4913-98a5-4f85825bf7d2'::uuid, '2af1f5fe27a2e4a6ee9df327', 'has_baby_changing', NULL, false, '2026-08-01T17:19:41.923Z'::timestamptz, 'EXACT_SOURCE_ID', 'HIGH', 'Toilet Map UK', 'f6824fdc7cd29df8c1f45ba749c1b28d319fb34803c55459bbe748ef65937624', '7400626bc99061af7ba82c29969fc8929d7394c59afcfe574e1880521bad2b45', '4710b9ec7a9f5a83aa9e7225400b8a6046ce0e77', 'relief.apply-engine-1a.v1', 'bgwxrxkmyaihplaloely', '1de1a71186b80ce043b48fc5f4d6c4bc6ed9d1c964b3ddf7ad3b96ddd073bfa0'),
    ('A1A-fec6519dda44a86f', '8c838ebd-4939-4913-98a5-4f85825bf7d2'::uuid, '2af1f5fe27a2e4a6ee9df327', 'is_gender_neutral', NULL, false, '2026-08-01T17:19:41.923Z'::timestamptz, 'EXACT_SOURCE_ID', 'HIGH', 'Toilet Map UK', 'f6824fdc7cd29df8c1f45ba749c1b28d319fb34803c55459bbe748ef65937624', '7400626bc99061af7ba82c29969fc8929d7394c59afcfe574e1880521bad2b45', '4710b9ec7a9f5a83aa9e7225400b8a6046ce0e77', 'relief.apply-engine-1a.v1', 'bgwxrxkmyaihplaloely', '1de1a71186b80ce043b48fc5f4d6c4bc6ed9d1c964b3ddf7ad3b96ddd073bfa0'),
    ('A1A-0dae68e673cd6801', '8c838ebd-4939-4913-98a5-4f85825bf7d2'::uuid, '2af1f5fe27a2e4a6ee9df327', 'requires_radar_key', NULL, false, '2026-08-01T17:19:41.923Z'::timestamptz, 'EXACT_SOURCE_ID', 'HIGH', 'Toilet Map UK', 'f6824fdc7cd29df8c1f45ba749c1b28d319fb34803c55459bbe748ef65937624', '7400626bc99061af7ba82c29969fc8929d7394c59afcfe574e1880521bad2b45', '4710b9ec7a9f5a83aa9e7225400b8a6046ce0e77', 'relief.apply-engine-1a.v1', 'bgwxrxkmyaihplaloely', '1de1a71186b80ce043b48fc5f4d6c4bc6ed9d1c964b3ddf7ad3b96ddd073bfa0'),
    ('A1A-81b2ea41ab4d0a9c', 'a1fc23b9-33cd-4ba1-ad67-f9fe484c3a23'::uuid, 'fd83a87fa4acc5f1915ecad9', 'has_baby_changing', NULL, false, '2026-07-29T19:01:25.330Z'::timestamptz, 'EXACT_SOURCE_ID', 'HIGH', 'Toilet Map UK', 'f6824fdc7cd29df8c1f45ba749c1b28d319fb34803c55459bbe748ef65937624', '7400626bc99061af7ba82c29969fc8929d7394c59afcfe574e1880521bad2b45', '4710b9ec7a9f5a83aa9e7225400b8a6046ce0e77', 'relief.apply-engine-1a.v1', 'bgwxrxkmyaihplaloely', '1de1a71186b80ce043b48fc5f4d6c4bc6ed9d1c964b3ddf7ad3b96ddd073bfa0'),
    ('A1A-9abc60241199d9a4', 'a1fc23b9-33cd-4ba1-ad67-f9fe484c3a23'::uuid, 'fd83a87fa4acc5f1915ecad9', 'is_accessible', NULL, false, '2026-07-29T19:01:25.330Z'::timestamptz, 'EXACT_SOURCE_ID', 'HIGH', 'Toilet Map UK', 'f6824fdc7cd29df8c1f45ba749c1b28d319fb34803c55459bbe748ef65937624', '7400626bc99061af7ba82c29969fc8929d7394c59afcfe574e1880521bad2b45', '4710b9ec7a9f5a83aa9e7225400b8a6046ce0e77', 'relief.apply-engine-1a.v1', 'bgwxrxkmyaihplaloely', '1de1a71186b80ce043b48fc5f4d6c4bc6ed9d1c964b3ddf7ad3b96ddd073bfa0'),
    ('A1A-f4bf1fe6a37e8455', 'a1fc23b9-33cd-4ba1-ad67-f9fe484c3a23'::uuid, 'fd83a87fa4acc5f1915ecad9', 'is_gender_neutral', NULL, false, '2026-07-29T19:01:25.330Z'::timestamptz, 'EXACT_SOURCE_ID', 'HIGH', 'Toilet Map UK', 'f6824fdc7cd29df8c1f45ba749c1b28d319fb34803c55459bbe748ef65937624', '7400626bc99061af7ba82c29969fc8929d7394c59afcfe574e1880521bad2b45', '4710b9ec7a9f5a83aa9e7225400b8a6046ce0e77', 'relief.apply-engine-1a.v1', 'bgwxrxkmyaihplaloely', '1de1a71186b80ce043b48fc5f4d6c4bc6ed9d1c964b3ddf7ad3b96ddd073bfa0'),
    ('A1A-5408da6431ecfb7f', 'a4c31707-e414-454c-addd-e8e4bf34c6b7'::uuid, '47931cc3659d98b3ff90623d', 'has_baby_changing', NULL, true, '2026-08-06T10:24:38.363Z'::timestamptz, 'EXACT_SOURCE_ID', 'HIGH', 'Toilet Map UK', 'f6824fdc7cd29df8c1f45ba749c1b28d319fb34803c55459bbe748ef65937624', '7400626bc99061af7ba82c29969fc8929d7394c59afcfe574e1880521bad2b45', '4710b9ec7a9f5a83aa9e7225400b8a6046ce0e77', 'relief.apply-engine-1a.v1', 'bgwxrxkmyaihplaloely', '1de1a71186b80ce043b48fc5f4d6c4bc6ed9d1c964b3ddf7ad3b96ddd073bfa0'),
    ('A1A-c32e70aefb22f775', 'a4c31707-e414-454c-addd-e8e4bf34c6b7'::uuid, '47931cc3659d98b3ff90623d', 'requires_radar_key', NULL, false, '2026-08-06T10:24:38.363Z'::timestamptz, 'EXACT_SOURCE_ID', 'HIGH', 'Toilet Map UK', 'f6824fdc7cd29df8c1f45ba749c1b28d319fb34803c55459bbe748ef65937624', '7400626bc99061af7ba82c29969fc8929d7394c59afcfe574e1880521bad2b45', '4710b9ec7a9f5a83aa9e7225400b8a6046ce0e77', 'relief.apply-engine-1a.v1', 'bgwxrxkmyaihplaloely', '1de1a71186b80ce043b48fc5f4d6c4bc6ed9d1c964b3ddf7ad3b96ddd073bfa0'),
    ('A1A-0985469bdc5f469f', 'b38ccc30-9b2d-4d98-be93-52b7597e7469'::uuid, '43119c8c4a6c8435eb0a98c7', 'has_baby_changing', NULL, true, '2026-08-06T10:26:50.586Z'::timestamptz, 'EXACT_SOURCE_ID', 'HIGH', 'Toilet Map UK', 'f6824fdc7cd29df8c1f45ba749c1b28d319fb34803c55459bbe748ef65937624', '7400626bc99061af7ba82c29969fc8929d7394c59afcfe574e1880521bad2b45', '4710b9ec7a9f5a83aa9e7225400b8a6046ce0e77', 'relief.apply-engine-1a.v1', 'bgwxrxkmyaihplaloely', '1de1a71186b80ce043b48fc5f4d6c4bc6ed9d1c964b3ddf7ad3b96ddd073bfa0'),
    ('A1A-a5d4c79b305cf825', 'ba77f1fd-b878-4347-beeb-26f5a8a38291'::uuid, '2793dd03c8dcacd811e23691', 'has_baby_changing', NULL, true, '2026-08-05T16:59:29.210Z'::timestamptz, 'EXACT_SOURCE_ID', 'HIGH', 'Toilet Map UK', 'f6824fdc7cd29df8c1f45ba749c1b28d319fb34803c55459bbe748ef65937624', '7400626bc99061af7ba82c29969fc8929d7394c59afcfe574e1880521bad2b45', '4710b9ec7a9f5a83aa9e7225400b8a6046ce0e77', 'relief.apply-engine-1a.v1', 'bgwxrxkmyaihplaloely', '1de1a71186b80ce043b48fc5f4d6c4bc6ed9d1c964b3ddf7ad3b96ddd073bfa0'),
    ('A1A-14a2f2486797e478', 'ba77f1fd-b878-4347-beeb-26f5a8a38291'::uuid, '2793dd03c8dcacd811e23691', 'is_gender_neutral', NULL, true, '2026-08-05T16:59:29.210Z'::timestamptz, 'EXACT_SOURCE_ID', 'HIGH', 'Toilet Map UK', 'f6824fdc7cd29df8c1f45ba749c1b28d319fb34803c55459bbe748ef65937624', '7400626bc99061af7ba82c29969fc8929d7394c59afcfe574e1880521bad2b45', '4710b9ec7a9f5a83aa9e7225400b8a6046ce0e77', 'relief.apply-engine-1a.v1', 'bgwxrxkmyaihplaloely', '1de1a71186b80ce043b48fc5f4d6c4bc6ed9d1c964b3ddf7ad3b96ddd073bfa0'),
    ('A1A-1d279953b20c290b', 'cef8cd94-4722-4a0a-af99-d41d89162eaa'::uuid, '5577f4ba2cf8063eb3250cce', 'has_baby_changing', NULL, false, '2026-07-25T14:20:07.368Z'::timestamptz, 'EXACT_SOURCE_ID', 'HIGH', 'Toilet Map UK', 'f6824fdc7cd29df8c1f45ba749c1b28d319fb34803c55459bbe748ef65937624', '7400626bc99061af7ba82c29969fc8929d7394c59afcfe574e1880521bad2b45', '4710b9ec7a9f5a83aa9e7225400b8a6046ce0e77', 'relief.apply-engine-1a.v1', 'bgwxrxkmyaihplaloely', '1de1a71186b80ce043b48fc5f4d6c4bc6ed9d1c964b3ddf7ad3b96ddd073bfa0'),
    ('A1A-a4d2467049269502', 'cef8cd94-4722-4a0a-af99-d41d89162eaa'::uuid, '5577f4ba2cf8063eb3250cce', 'is_gender_neutral', NULL, false, '2026-07-25T14:20:07.368Z'::timestamptz, 'EXACT_SOURCE_ID', 'HIGH', 'Toilet Map UK', 'f6824fdc7cd29df8c1f45ba749c1b28d319fb34803c55459bbe748ef65937624', '7400626bc99061af7ba82c29969fc8929d7394c59afcfe574e1880521bad2b45', '4710b9ec7a9f5a83aa9e7225400b8a6046ce0e77', 'relief.apply-engine-1a.v1', 'bgwxrxkmyaihplaloely', '1de1a71186b80ce043b48fc5f4d6c4bc6ed9d1c964b3ddf7ad3b96ddd073bfa0'),
    ('A1A-0226ed79286f606a', 'cef8cd94-4722-4a0a-af99-d41d89162eaa'::uuid, '5577f4ba2cf8063eb3250cce', 'requires_radar_key', NULL, false, '2026-07-25T14:20:07.368Z'::timestamptz, 'EXACT_SOURCE_ID', 'HIGH', 'Toilet Map UK', 'f6824fdc7cd29df8c1f45ba749c1b28d319fb34803c55459bbe748ef65937624', '7400626bc99061af7ba82c29969fc8929d7394c59afcfe574e1880521bad2b45', '4710b9ec7a9f5a83aa9e7225400b8a6046ce0e77', 'relief.apply-engine-1a.v1', 'bgwxrxkmyaihplaloely', '1de1a71186b80ce043b48fc5f4d6c4bc6ed9d1c964b3ddf7ad3b96ddd073bfa0'),
    ('A1A-6102cd8dec46ae07', 'cf385907-c050-44d7-bd14-b5cb4be94a8e'::uuid, '2a7ea23fbbb9a8e0c3db5ffd', 'has_baby_changing', NULL, false, '2026-07-28T05:11:48.805Z'::timestamptz, 'EXACT_SOURCE_ID', 'HIGH', 'Toilet Map UK', 'f6824fdc7cd29df8c1f45ba749c1b28d319fb34803c55459bbe748ef65937624', '7400626bc99061af7ba82c29969fc8929d7394c59afcfe574e1880521bad2b45', '4710b9ec7a9f5a83aa9e7225400b8a6046ce0e77', 'relief.apply-engine-1a.v1', 'bgwxrxkmyaihplaloely', '1de1a71186b80ce043b48fc5f4d6c4bc6ed9d1c964b3ddf7ad3b96ddd073bfa0'),
    ('A1A-b3406849910b070a', 'cf385907-c050-44d7-bd14-b5cb4be94a8e'::uuid, '2a7ea23fbbb9a8e0c3db5ffd', 'is_gender_neutral', NULL, false, '2026-07-28T05:11:48.805Z'::timestamptz, 'EXACT_SOURCE_ID', 'HIGH', 'Toilet Map UK', 'f6824fdc7cd29df8c1f45ba749c1b28d319fb34803c55459bbe748ef65937624', '7400626bc99061af7ba82c29969fc8929d7394c59afcfe574e1880521bad2b45', '4710b9ec7a9f5a83aa9e7225400b8a6046ce0e77', 'relief.apply-engine-1a.v1', 'bgwxrxkmyaihplaloely', '1de1a71186b80ce043b48fc5f4d6c4bc6ed9d1c964b3ddf7ad3b96ddd073bfa0'),
    ('A1A-80634f42cbf633b6', 'cf385907-c050-44d7-bd14-b5cb4be94a8e'::uuid, '2a7ea23fbbb9a8e0c3db5ffd', 'requires_radar_key', NULL, true, '2026-07-28T05:11:48.805Z'::timestamptz, 'EXACT_SOURCE_ID', 'HIGH', 'Toilet Map UK', 'f6824fdc7cd29df8c1f45ba749c1b28d319fb34803c55459bbe748ef65937624', '7400626bc99061af7ba82c29969fc8929d7394c59afcfe574e1880521bad2b45', '4710b9ec7a9f5a83aa9e7225400b8a6046ce0e77', 'relief.apply-engine-1a.v1', 'bgwxrxkmyaihplaloely', '1de1a71186b80ce043b48fc5f4d6c4bc6ed9d1c964b3ddf7ad3b96ddd073bfa0'),
    ('A1A-85ae14976cf23ad3', 'cfa1b9d0-8976-4d41-8cc3-2150a35252a2'::uuid, '892d3b2712e46852deb18efa', 'has_baby_changing', NULL, true, '2026-08-09T09:01:38.129Z'::timestamptz, 'EXACT_SOURCE_ID', 'HIGH', 'Toilet Map UK', 'f6824fdc7cd29df8c1f45ba749c1b28d319fb34803c55459bbe748ef65937624', '7400626bc99061af7ba82c29969fc8929d7394c59afcfe574e1880521bad2b45', '4710b9ec7a9f5a83aa9e7225400b8a6046ce0e77', 'relief.apply-engine-1a.v1', 'bgwxrxkmyaihplaloely', '1de1a71186b80ce043b48fc5f4d6c4bc6ed9d1c964b3ddf7ad3b96ddd073bfa0'),
    ('A1A-7a4a02b1c593659f', 'cfa1b9d0-8976-4d41-8cc3-2150a35252a2'::uuid, '892d3b2712e46852deb18efa', 'is_gender_neutral', NULL, true, '2026-08-09T09:01:38.129Z'::timestamptz, 'EXACT_SOURCE_ID', 'HIGH', 'Toilet Map UK', 'f6824fdc7cd29df8c1f45ba749c1b28d319fb34803c55459bbe748ef65937624', '7400626bc99061af7ba82c29969fc8929d7394c59afcfe574e1880521bad2b45', '4710b9ec7a9f5a83aa9e7225400b8a6046ce0e77', 'relief.apply-engine-1a.v1', 'bgwxrxkmyaihplaloely', '1de1a71186b80ce043b48fc5f4d6c4bc6ed9d1c964b3ddf7ad3b96ddd073bfa0'),
    ('A1A-8c50e66d0952205f', 'e268da6e-7717-480b-8e73-cce1829e23c7'::uuid, 'ce9db1854310c73d5d981099', 'has_baby_changing', NULL, true, '2026-08-06T10:30:23.165Z'::timestamptz, 'EXACT_SOURCE_ID', 'HIGH', 'Toilet Map UK', 'f6824fdc7cd29df8c1f45ba749c1b28d319fb34803c55459bbe748ef65937624', '7400626bc99061af7ba82c29969fc8929d7394c59afcfe574e1880521bad2b45', '4710b9ec7a9f5a83aa9e7225400b8a6046ce0e77', 'relief.apply-engine-1a.v1', 'bgwxrxkmyaihplaloely', '1de1a71186b80ce043b48fc5f4d6c4bc6ed9d1c964b3ddf7ad3b96ddd073bfa0'),
    ('A1A-37aa9bedc41681ba', 'e268da6e-7717-480b-8e73-cce1829e23c7'::uuid, 'ce9db1854310c73d5d981099', 'requires_radar_key', NULL, true, '2026-08-06T10:30:23.165Z'::timestamptz, 'EXACT_SOURCE_ID', 'HIGH', 'Toilet Map UK', 'f6824fdc7cd29df8c1f45ba749c1b28d319fb34803c55459bbe748ef65937624', '7400626bc99061af7ba82c29969fc8929d7394c59afcfe574e1880521bad2b45', '4710b9ec7a9f5a83aa9e7225400b8a6046ce0e77', 'relief.apply-engine-1a.v1', 'bgwxrxkmyaihplaloely', '1de1a71186b80ce043b48fc5f4d6c4bc6ed9d1c964b3ddf7ad3b96ddd073bfa0');

DO $$
DECLARE
  v_count bigint;
  v_distinct_ids bigint;
  v_distinct_operations bigint;
BEGIN
  SELECT count(*), count(DISTINCT operation_id), count(DISTINCT (facility_id, source_record_id, field))
  INTO v_count, v_distinct_ids, v_distinct_operations
  FROM private.relief_apply_1a_approved_operations;

  IF v_count <> 48 OR v_distinct_ids <> 48 OR v_distinct_operations <> 48 THEN
    RAISE EXCEPTION 'Apply 1A approval registry is not exactly 48 unique operations';
  END IF;

  IF EXISTS (
    SELECT 1
    FROM private.relief_apply_1a_approved_operations
    WHERE source_name <> 'Toilet Map UK'
       OR source_checksum <> 'f6824fdc7cd29df8c1f45ba749c1b28d319fb34803c55459bbe748ef65937624'
       OR approved_plan_sha256 <> '7400626bc99061af7ba82c29969fc8929d7394c59afcfe574e1880521bad2b45'
       OR approved_manifest_sha256 <> '1de1a71186b80ce043b48fc5f4d6c4bc6ed9d1c964b3ddf7ad3b96ddd073bfa0'
       OR approved_review_commit <> '4710b9ec7a9f5a83aa9e7225400b8a6046ce0e77'
       OR apply_engine_version <> 'relief.apply-engine-1a.v1'
       OR project_ref <> 'bgwxrxkmyaihplaloely'
       OR expected_current_value IS NOT NULL
       OR matching_basis <> 'EXACT_SOURCE_ID'
       OR confidence <> 'HIGH'
  ) THEN
    RAISE EXCEPTION 'Apply 1A approval registry identity or shape mismatch';
  END IF;
END;
$$;

CREATE OR REPLACE FUNCTION private.relief_apply_1a_registry_immutable()
RETURNS trigger
LANGUAGE plpgsql
SET search_path = ''
AS $$
BEGIN
  RAISE EXCEPTION 'Apply 1A approval registry is immutable';
END;
$$;

DROP TRIGGER IF EXISTS relief_apply_1a_registry_immutable_trigger
  ON private.relief_apply_1a_approved_operations;
CREATE TRIGGER relief_apply_1a_registry_immutable_trigger
BEFORE INSERT OR UPDATE OR DELETE
ON private.relief_apply_1a_approved_operations
FOR EACH ROW
EXECUTE FUNCTION private.relief_apply_1a_registry_immutable();

COMMENT ON TABLE private.relief_apply_1a_approved_operations IS
  'Immutable control metadata for the exact approved Apply 1A operation set; not facility enrichment data.';

-- The function accepts approval gates only. It obtains the operation set from
-- the private registry, so a caller cannot substitute operations while
-- presenting the approved manifest hash.
CREATE OR REPLACE FUNCTION private.apply_relief_toilet_map_1a(
  p_project_ref text,
  p_plan_sha256 text,
  p_manifest_sha256 text,
  p_source_sha256 text,
  p_confirmation text
)
RETURNS jsonb
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = ''
AS $function$
DECLARE
  v_run_id uuid;
  v_existing_run_id uuid;
  v_registry_count bigint;
  v_distinct_ids bigint;
  v_distinct_operations bigint;
  v_actual_distribution jsonb;
  v_link_count bigint;
  v_facility_count_before bigint;
  v_facility_count_after bigint;
  v_source_count_before bigint;
  v_source_count_after bigint;
  v_source_digest_before text;
  v_source_digest_after text;
  v_publication_digest_before text;
  v_publication_digest_after text;
  v_rows integer;
  v_ready_count integer := 0;
  v_applied_count integer := 0;
  v_stale_count integer := 0;
  v_failed_count integer := 0;
  v_sqlstate text;
  v_target_value boolean;
  v_target_provenance jsonb;
  v_provenance_source text;
  v_provenance_status text;
  v_new_provenance jsonb;
  r record;
  v_facility public.facilities%ROWTYPE;
  v_source_link public.facility_sources%ROWTYPE;
BEGIN
  IF p_project_ref <> 'bgwxrxkmyaihplaloely'
     OR lower(coalesce(p_plan_sha256, '')) <> '7400626bc99061af7ba82c29969fc8929d7394c59afcfe574e1880521bad2b45'
     OR lower(coalesce(p_manifest_sha256, '')) <> '1de1a71186b80ce043b48fc5f4d6c4bc6ed9d1c964b3ddf7ad3b96ddd073bfa0'
     OR lower(coalesce(p_source_sha256, '')) <> 'f6824fdc7cd29df8c1f45ba749c1b28d319fb34803c55459bbe748ef65937624'
     OR p_confirmation <> 'APPLY_RELIEF_TOILET_MAP_1A_48' THEN
    RAISE EXCEPTION 'Apply 1A approval identity rejected';
  END IF;

  -- Serialize all attempts for the one approved manifest before looking up
  -- an existing committed run or creating an attempt audit row.
  PERFORM pg_catalog.pg_advisory_xact_lock(
    pg_catalog.hashtextextended(
      'relief.apply.1a:1de1a71186b80ce043b48fc5f4d6c4bc6ed9d1c964b3ddf7ad3b96ddd073bfa0',
      0
    )
  );

  SELECT id
  INTO v_existing_run_id
  FROM public.import_runs
  WHERE run_kind = 'apply_1a'
    AND lower(approved_manifest_sha256) = '1de1a71186b80ce043b48fc5f4d6c4bc6ed9d1c964b3ddf7ad3b96ddd073bfa0'
    AND transaction_outcome = 'committed'
  ORDER BY completed_at DESC NULLS LAST, id DESC
  LIMIT 1;

  IF v_existing_run_id IS NOT NULL THEN
    RETURN jsonb_build_object(
      'status', 'ALREADY_APPLIED',
      'run_id', v_existing_run_id,
      'approved_manifest_sha256', '1de1a71186b80ce043b48fc5f4d6c4bc6ed9d1c964b3ddf7ad3b96ddd073bfa0',
      'applied_count', 0,
      'mutations_committed', false
    );
  END IF;

  -- This row is outside the nested exception block so a rolled-back attempt
  -- remains durable while the facility/provenance work remains atomic.
  INSERT INTO public.import_runs (
    source_name,
    source_file_name,
    source_checksum,
    status,
    started_at,
    rows_received,
    rows_valid,
    run_kind,
    approved_plan_sha256,
    approved_manifest_sha256,
    approved_review_commit,
    apply_engine_version,
    project_ref,
    requested_operation_count,
    ready_count,
    applied_count,
    stale_count,
    failed_count,
    transaction_outcome,
    rollback_summary
  )
  VALUES (
    'Toilet Map UK',
    'TOILET_MAP_APPLY_1A_MANIFEST.json',
    'f6824fdc7cd29df8c1f45ba749c1b28d319fb34803c55459bbe748ef65937624',
    'started',
    pg_catalog.clock_timestamp(),
    48,
    48,
    'apply_1a',
    '7400626bc99061af7ba82c29969fc8929d7394c59afcfe574e1880521bad2b45',
    '1de1a71186b80ce043b48fc5f4d6c4bc6ed9d1c964b3ddf7ad3b96ddd073bfa0',
    '4710b9ec7a9f5a83aa9e7225400b8a6046ce0e77',
    'relief.apply-engine-1a.v1',
    'bgwxrxkmyaihplaloely',
    48,
    0,
    0,
    0,
    0,
    'not_started',
    NULL
  )
  RETURNING id INTO v_run_id;

  BEGIN
    -- These locks prevent non-target facility/source changes while the
    -- complete before/after assertions are evaluated. Affected facility rows
    -- are also explicitly locked below.
    LOCK TABLE public.facilities, public.facility_sources IN SHARE MODE;

    SELECT count(*), count(DISTINCT operation_id), count(DISTINCT (facility_id, source_record_id, field))
    INTO v_registry_count, v_distinct_ids, v_distinct_operations
    FROM private.relief_apply_1a_approved_operations;

    IF v_registry_count <> 48 OR v_distinct_ids <> 48 OR v_distinct_operations <> 48 THEN
      RAISE EXCEPTION 'Apply 1A registry cardinality or uniqueness precondition failed';
    END IF;

    SELECT coalesce(jsonb_object_agg(field, operation_count), '{}'::jsonb)
    INTO v_actual_distribution
    FROM (
      SELECT field, count(*)::integer AS operation_count
      FROM private.relief_apply_1a_approved_operations
      GROUP BY field
    ) AS distribution;

    IF v_actual_distribution <> '{"has_baby_changing": 16, "requires_radar_key": 14, "is_gender_neutral": 15, "is_accessible": 2, "is_free": 1}'::jsonb THEN
      RAISE EXCEPTION 'Apply 1A field distribution precondition failed';
    END IF;

    IF EXISTS (
      SELECT 1
      FROM private.relief_apply_1a_approved_operations
      WHERE field NOT IN (
              'has_baby_changing',
              'requires_radar_key',
              'is_gender_neutral',
              'is_accessible',
              'is_free'
            )
         OR expected_current_value IS NOT NULL
         OR proposed_value IS NULL
         OR matching_basis <> 'EXACT_SOURCE_ID'
         OR confidence <> 'HIGH'
         OR source_name <> 'Toilet Map UK'
         OR source_checksum <> 'f6824fdc7cd29df8c1f45ba749c1b28d319fb34803c55459bbe748ef65937624'
         OR approved_plan_sha256 <> '7400626bc99061af7ba82c29969fc8929d7394c59afcfe574e1880521bad2b45'
         OR approved_manifest_sha256 <> '1de1a71186b80ce043b48fc5f4d6c4bc6ed9d1c964b3ddf7ad3b96ddd073bfa0'
         OR approved_review_commit <> '4710b9ec7a9f5a83aa9e7225400b8a6046ce0e77'
         OR apply_engine_version <> 'relief.apply-engine-1a.v1'
         OR project_ref <> 'bgwxrxkmyaihplaloely'
         OR source_updated_at IS NULL
    ) THEN
      RAISE EXCEPTION 'Apply 1A registry identity or shape precondition failed';
    END IF;

    SELECT count(*) INTO v_facility_count_before FROM public.facilities;
    SELECT count(*) INTO v_source_count_before FROM public.facility_sources;
    SELECT pg_catalog.md5(
      coalesce(
        (SELECT jsonb_agg(to_jsonb(s) ORDER BY s.id)::text FROM public.facility_sources AS s),
        '[]'
      )
    ) INTO v_source_digest_before;
    SELECT pg_catalog.md5(
      coalesce(
        (
          SELECT jsonb_agg(
            jsonb_build_object('id', f.id, 'publication_status', f.publication_status)
            ORDER BY f.id
          )::text
          FROM public.facilities AS f
          WHERE f.id IN (
            SELECT DISTINCT facility_id
            FROM private.relief_apply_1a_approved_operations
          )
        ),
        '[]'
      )
    ) INTO v_publication_digest_before;

    -- Validate every operation before the first facility update.
    FOR r IN
      SELECT *
      FROM private.relief_apply_1a_approved_operations
      ORDER BY operation_id
    LOOP
      SELECT f.*
      INTO v_facility
      FROM public.facilities AS f
      WHERE f.id = r.facility_id
      FOR UPDATE;

      IF NOT FOUND THEN
        RAISE EXCEPTION 'Apply 1A facility precondition failed';
      END IF;

      SELECT count(*)
      INTO v_link_count
      FROM public.facility_sources AS fs
      WHERE fs.facility_id = r.facility_id
        AND fs.source_name = r.source_name
        AND fs.source_record_id = r.source_record_id;

      IF v_link_count <> 1 THEN
        RAISE EXCEPTION 'Apply 1A exact source-link precondition failed';
      END IF;

      SELECT fs.*
      INTO v_source_link
      FROM public.facility_sources AS fs
      WHERE fs.facility_id = r.facility_id
        AND fs.source_name = r.source_name
        AND fs.source_record_id = r.source_record_id;

      IF v_source_link.source_name <> 'Toilet Map UK'
         OR v_source_link.facility_id <> r.facility_id
         OR v_source_link.source_record_id <> r.source_record_id
         OR v_source_link.is_current IS NOT TRUE
         OR (
           v_source_link.source_updated_at IS NOT NULL
           AND v_source_link.source_updated_at > r.source_updated_at
         ) THEN
        RAISE EXCEPTION 'Apply 1A source-link freshness or identity precondition failed';
      END IF;

      v_target_value := CASE r.field
        WHEN 'has_baby_changing' THEN v_facility.has_baby_changing
        WHEN 'requires_radar_key' THEN v_facility.requires_radar_key
        WHEN 'is_gender_neutral' THEN v_facility.is_gender_neutral
        WHEN 'is_accessible' THEN v_facility.is_accessible
        WHEN 'is_free' THEN v_facility.is_free
        ELSE NULL
      END;

      IF v_target_value IS NOT NULL THEN
        RAISE EXCEPTION 'Apply 1A target field is no longer NULL';
      END IF;

      v_target_provenance := v_facility.field_provenance -> r.field;
      IF v_target_provenance IS NOT NULL THEN
        IF jsonb_typeof(v_target_provenance) <> 'object' THEN
          RAISE EXCEPTION 'Apply 1A target provenance is uninterpretable';
        END IF;

        v_provenance_source := lower(
          coalesce(
            nullif(pg_catalog.btrim(v_target_provenance ->> 'source'), ''),
            nullif(pg_catalog.btrim(v_target_provenance ->> 'source_name'), ''),
            ''
          )
        );
        v_provenance_status := lower(coalesce(v_target_provenance ->> 'verification_status', ''));

        IF v_provenance_source <> 'toilet map uk'
           OR v_provenance_status IN (
                'community_confirmed',
                'staff_verified',
                'source_verified',
                'current',
                'current_relief'
              ) THEN
          RAISE EXCEPTION 'Apply 1A target provenance is stronger or incompatible';
        END IF;
      END IF;
    END LOOP;

    v_ready_count := 48;

    -- Fixed, statically bounded update path. No operation value is ever used
    -- as an identifier or interpolated SQL fragment.
    FOR r IN
      SELECT *
      FROM private.relief_apply_1a_approved_operations
      ORDER BY operation_id
    LOOP
      SELECT fs.*
      INTO v_source_link
      FROM public.facility_sources AS fs
      WHERE fs.facility_id = r.facility_id
        AND fs.source_name = r.source_name
        AND fs.source_record_id = r.source_record_id;

      v_new_provenance := jsonb_build_object(
        'source', r.source_name,
        'source_name', r.source_name,
        'source_record_id', r.source_record_id,
        'source_updated_at', r.source_updated_at,
        'source_snapshot_checksum', r.source_checksum,
        'import_run_id', v_source_link.import_run_id,
        'apply_run_id', v_run_id,
        'field', r.field,
        'previous_value', NULL::boolean,
        'new_value', r.proposed_value,
        'basis', 'EXACT_SOURCE_ID',
        'confidence', 'HIGH',
        'policy_version', r.apply_engine_version,
        'apply_engine_version', r.apply_engine_version,
        'approved_plan_sha256', r.approved_plan_sha256,
        'approved_manifest_sha256', r.approved_manifest_sha256,
        'approved_review_commit', r.approved_review_commit,
        'recorded_at', pg_catalog.clock_timestamp()
      );

      IF r.field = 'has_baby_changing' THEN
        UPDATE public.facilities
        SET has_baby_changing = r.proposed_value,
            field_provenance = jsonb_set(
              coalesce(field_provenance, '{}'::jsonb),
              ARRAY[r.field],
              v_new_provenance,
              true
            )
        WHERE id = r.facility_id AND has_baby_changing IS NULL;
      ELSIF r.field = 'requires_radar_key' THEN
        UPDATE public.facilities
        SET requires_radar_key = r.proposed_value,
            field_provenance = jsonb_set(
              coalesce(field_provenance, '{}'::jsonb),
              ARRAY[r.field],
              v_new_provenance,
              true
            )
        WHERE id = r.facility_id AND requires_radar_key IS NULL;
      ELSIF r.field = 'is_gender_neutral' THEN
        UPDATE public.facilities
        SET is_gender_neutral = r.proposed_value,
            field_provenance = jsonb_set(
              coalesce(field_provenance, '{}'::jsonb),
              ARRAY[r.field],
              v_new_provenance,
              true
            )
        WHERE id = r.facility_id AND is_gender_neutral IS NULL;
      ELSIF r.field = 'is_accessible' THEN
        UPDATE public.facilities
        SET is_accessible = r.proposed_value,
            field_provenance = jsonb_set(
              coalesce(field_provenance, '{}'::jsonb),
              ARRAY[r.field],
              v_new_provenance,
              true
            )
        WHERE id = r.facility_id AND is_accessible IS NULL;
      ELSIF r.field = 'is_free' THEN
        UPDATE public.facilities
        SET is_free = r.proposed_value,
            field_provenance = jsonb_set(
              coalesce(field_provenance, '{}'::jsonb),
              ARRAY[r.field],
              v_new_provenance,
              true
            )
        WHERE id = r.facility_id AND is_free IS NULL;
      ELSE
        RAISE EXCEPTION 'Apply 1A encountered a non-allowlisted field branch';
      END IF;

      GET DIAGNOSTICS v_rows = ROW_COUNT;
      IF v_rows <> 1 THEN
        RAISE EXCEPTION 'Apply 1A affected-row precondition failed';
      END IF;
      v_applied_count := v_applied_count + 1;
    END LOOP;

    -- Postcheck remains inside the same transaction and before the committed
    -- audit outcome is written.
    SELECT count(*) INTO v_facility_count_after FROM public.facilities;
    SELECT count(*) INTO v_source_count_after FROM public.facility_sources;
    SELECT pg_catalog.md5(
      coalesce(
        (SELECT jsonb_agg(to_jsonb(s) ORDER BY s.id)::text FROM public.facility_sources AS s),
        '[]'
      )
    ) INTO v_source_digest_after;
    SELECT pg_catalog.md5(
      coalesce(
        (
          SELECT jsonb_agg(
            jsonb_build_object('id', f.id, 'publication_status', f.publication_status)
            ORDER BY f.id
          )::text
          FROM public.facilities AS f
          WHERE f.id IN (
            SELECT DISTINCT facility_id
            FROM private.relief_apply_1a_approved_operations
          )
        ),
        '[]'
      )
    ) INTO v_publication_digest_after;

    IF v_facility_count_after <> v_facility_count_before
       OR v_source_count_after <> v_source_count_before
       OR v_source_digest_after <> v_source_digest_before
       OR v_publication_digest_after <> v_publication_digest_before
       OR v_applied_count <> 48
       OR v_ready_count <> 48
       OR v_stale_count <> 0
       OR v_failed_count <> 0 THEN
      RAISE EXCEPTION 'Apply 1A transaction postcheck failed';
    END IF;

    FOR r IN
      SELECT *
      FROM private.relief_apply_1a_approved_operations
      ORDER BY operation_id
    LOOP
      SELECT f.*
      INTO v_facility
      FROM public.facilities AS f
      WHERE f.id = r.facility_id;

      v_target_value := CASE r.field
        WHEN 'has_baby_changing' THEN v_facility.has_baby_changing
        WHEN 'requires_radar_key' THEN v_facility.requires_radar_key
        WHEN 'is_gender_neutral' THEN v_facility.is_gender_neutral
        WHEN 'is_accessible' THEN v_facility.is_accessible
        WHEN 'is_free' THEN v_facility.is_free
        ELSE NULL
      END;

      IF v_target_value IS DISTINCT FROM r.proposed_value THEN
        RAISE EXCEPTION 'Apply 1A postcheck found an incorrect target value';
      END IF;

      v_target_provenance := v_facility.field_provenance -> r.field;
      IF jsonb_typeof(v_target_provenance) <> 'object'
         OR v_target_provenance ->> 'source' <> 'Toilet Map UK'
         OR v_target_provenance ->> 'source_record_id' <> r.source_record_id
         OR lower(v_target_provenance ->> 'source_snapshot_checksum') <> r.source_checksum
         OR (v_target_provenance ->> 'source_updated_at')::timestamptz <> r.source_updated_at
         OR v_target_provenance ->> 'apply_run_id' <> v_run_id::text
         OR v_target_provenance ->> 'field' <> r.field
         OR (v_target_provenance -> 'previous_value') IS DISTINCT FROM 'null'::jsonb
         OR v_target_provenance -> 'new_value' IS DISTINCT FROM to_jsonb(r.proposed_value)
         OR v_target_provenance ->> 'basis' <> 'EXACT_SOURCE_ID'
         OR v_target_provenance ->> 'confidence' <> 'HIGH'
         OR v_target_provenance ->> 'apply_engine_version' <> 'relief.apply-engine-1a.v1'
         OR v_target_provenance ->> 'approved_plan_sha256' <> '7400626bc99061af7ba82c29969fc8929d7394c59afcfe574e1880521bad2b45'
         OR v_target_provenance ->> 'approved_manifest_sha256' <> '1de1a71186b80ce043b48fc5f4d6c4bc6ed9d1c964b3ddf7ad3b96ddd073bfa0'
         OR v_target_provenance ->> 'approved_review_commit' <> '4710b9ec7a9f5a83aa9e7225400b8a6046ce0e77' THEN
        RAISE EXCEPTION 'Apply 1A provenance postcheck failed';
      END IF;

      SELECT fs.*
      INTO v_source_link
      FROM public.facility_sources AS fs
      WHERE fs.facility_id = r.facility_id
        AND fs.source_name = r.source_name
        AND fs.source_record_id = r.source_record_id;

      IF v_target_provenance ->> 'import_run_id' IS DISTINCT FROM v_source_link.import_run_id::text THEN
        RAISE EXCEPTION 'Apply 1A source import-run provenance postcheck failed';
      END IF;
    END LOOP;

    UPDATE public.import_runs
    SET status = 'completed',
        completed_at = pg_catalog.clock_timestamp(),
        rows_updated = 48,
        transaction_outcome = 'committed',
        ready_count = 48,
        applied_count = 48,
        stale_count = 0,
        failed_count = 0,
        rollback_summary = NULL
    WHERE id = v_run_id;

    GET DIAGNOSTICS v_rows = ROW_COUNT;
    IF v_rows <> 1 THEN
      RAISE EXCEPTION 'Apply 1A audit completion update failed';
    END IF;

    RETURN jsonb_build_object(
      'status', 'COMMITTED',
      'run_id', v_run_id,
      'approved_plan_sha256', '7400626bc99061af7ba82c29969fc8929d7394c59afcfe574e1880521bad2b45',
      'approved_manifest_sha256', '1de1a71186b80ce043b48fc5f4d6c4bc6ed9d1c964b3ddf7ad3b96ddd073bfa0',
      'requested_operation_count', 48,
      'ready_count', 48,
      'applied_count', 48,
      'stale_count', 0,
      'failed_count', 0,
      'mutations_committed', true
    );
  EXCEPTION WHEN OTHERS THEN
    -- The exception block is a PL/pgSQL subtransaction: all facility and
    -- provenance changes since BEGIN are rolled back. This audit UPDATE is
    -- performed after that rollback and contains only safe fixed metadata.
    v_sqlstate := SQLSTATE;
    v_stale_count := CASE WHEN v_stale_count = 0 THEN 1 ELSE v_stale_count END;
    v_failed_count := 1;

    UPDATE public.import_runs
    SET status = 'failed',
        completed_at = pg_catalog.clock_timestamp(),
        rows_updated = 0,
        ready_count = least(v_ready_count, 48),
        applied_count = 0,
        stale_count = least(v_stale_count, 48),
        failed_count = v_failed_count,
        transaction_outcome = 'rolled_back',
        error_summary = 'Apply 1A rolled back; no partial facility changes retained',
        rollback_summary = pg_catalog.format(
          'Apply 1A rolled back; SQLSTATE=%s; no facility or provenance partial change committed.',
          v_sqlstate
        )
    WHERE id = v_run_id;

    RETURN jsonb_build_object(
      'status', 'ROLLED_BACK',
      'run_id', v_run_id,
      'approved_manifest_sha256', '1de1a71186b80ce043b48fc5f4d6c4bc6ed9d1c964b3ddf7ad3b96ddd073bfa0',
      'requested_operation_count', 48,
      'ready_count', least(v_ready_count, 48),
      'applied_count', 0,
      'stale_count', least(v_stale_count, 48),
      'failed_count', v_failed_count,
      'mutations_committed', false
    );
  END;
END;
$function$;

COMMENT ON FUNCTION private.apply_relief_toilet_map_1a(text, text, text, text, text) IS
  'Privileged, exact-bound Apply 1A transaction. Operations come only from the immutable private registry.';

REVOKE ALL ON TABLE private.relief_apply_1a_approved_operations FROM PUBLIC, anon, authenticated;
REVOKE EXECUTE ON FUNCTION private.relief_apply_1a_registry_immutable() FROM PUBLIC, anon, authenticated;
REVOKE EXECUTE ON FUNCTION private.apply_relief_toilet_map_1a(text, text, text, text, text) FROM PUBLIC;
REVOKE EXECUTE ON FUNCTION private.apply_relief_toilet_map_1a(text, text, text, text, text) FROM anon;
REVOKE EXECUTE ON FUNCTION private.apply_relief_toilet_map_1a(text, text, text, text, text) FROM authenticated;

-- The migration never creates either privileged role. If the deployment
-- owner has provisioned the named operator role separately, grant only this
-- function and private-schema usage to it. A dedicated owner role should be
-- assigned by the deployment DBA before enabling the function; this migration
-- deliberately does not transfer ownership to an unprovisioned role.
DO $$
BEGIN
  IF EXISTS (SELECT 1 FROM pg_catalog.pg_roles WHERE rolname = 'relief_apply_owner') THEN
    EXECUTE 'GRANT USAGE ON SCHEMA private TO relief_apply_owner';
    EXECUTE 'GRANT SELECT ON TABLE private.relief_apply_1a_approved_operations TO relief_apply_owner';
    EXECUTE 'GRANT SELECT ON TABLE public.facilities, public.facility_sources TO relief_apply_owner';
    EXECUTE 'GRANT UPDATE (has_baby_changing, requires_radar_key, is_gender_neutral, is_accessible, is_free, field_provenance) ON TABLE public.facilities TO relief_apply_owner';
    EXECUTE 'GRANT SELECT ON TABLE public.import_runs TO relief_apply_owner';
    EXECUTE 'GRANT INSERT (source_name, source_file_name, source_checksum, status, started_at, rows_received, rows_valid, run_kind, approved_plan_sha256, approved_manifest_sha256, approved_review_commit, apply_engine_version, project_ref, requested_operation_count, ready_count, applied_count, stale_count, failed_count, transaction_outcome, rollback_summary) ON TABLE public.import_runs TO relief_apply_owner';
    EXECUTE 'GRANT UPDATE (status, completed_at, rows_updated, ready_count, applied_count, stale_count, failed_count, transaction_outcome, error_summary, rollback_summary) ON TABLE public.import_runs TO relief_apply_owner';
  END IF;

  IF EXISTS (SELECT 1 FROM pg_catalog.pg_roles WHERE rolname = 'relief_apply_operator') THEN
    EXECUTE 'GRANT USAGE ON SCHEMA private TO relief_apply_operator';
    EXECUTE 'GRANT EXECUTE ON FUNCTION private.apply_relief_toilet_map_1a(text, text, text, text, text) TO relief_apply_operator';
  END IF;

  IF EXISTS (SELECT 1 FROM pg_catalog.pg_roles WHERE rolname = 'relief_apply_owner') THEN
    EXECUTE 'ALTER FUNCTION private.apply_relief_toilet_map_1a(text, text, text, text, text) OWNER TO relief_apply_owner';
  END IF;
END;
$$;

COMMIT;

-- Documented rollback (not executed here):
--
-- DROP INDEX IF EXISTS public.import_runs_apply_1a_committed_manifest_key;
-- DROP INDEX IF EXISTS public.import_runs_apply_1a_manifest_lookup;
-- DROP TRIGGER IF EXISTS relief_apply_1a_registry_immutable_trigger
--   ON private.relief_apply_1a_approved_operations;
-- DROP FUNCTION IF EXISTS private.apply_relief_toilet_map_1a(text, text, text, text, text);
-- DROP FUNCTION IF EXISTS private.relief_apply_1a_registry_immutable();
-- DROP TABLE IF EXISTS private.relief_apply_1a_approved_operations;
-- DROP SCHEMA IF EXISTS private;
-- ALTER TABLE public.import_runs
--   DROP CONSTRAINT IF EXISTS import_runs_apply_1a_committed_check,
--   DROP CONSTRAINT IF EXISTS import_runs_apply_1a_outcome_check,
--   DROP CONSTRAINT IF EXISTS import_runs_apply_1a_identity_check,
--   DROP CONSTRAINT IF EXISTS import_runs_approval_hash_format_check,
--   DROP CONSTRAINT IF EXISTS import_runs_transaction_outcome_check,
--   DROP CONSTRAINT IF EXISTS import_runs_run_kind_check;
-- ALTER TABLE public.import_runs
--   DROP COLUMN IF EXISTS rollback_summary,
--   DROP COLUMN IF EXISTS transaction_outcome,
--   DROP COLUMN IF EXISTS failed_count,
--   DROP COLUMN IF EXISTS stale_count,
--   DROP COLUMN IF EXISTS applied_count,
--   DROP COLUMN IF EXISTS ready_count,
--   DROP COLUMN IF EXISTS requested_operation_count,
--   DROP COLUMN IF EXISTS project_ref,
--   DROP COLUMN IF EXISTS apply_engine_version,
--   DROP COLUMN IF EXISTS approved_review_commit,
--   DROP COLUMN IF EXISTS approved_manifest_sha256,
--   DROP COLUMN IF EXISTS approved_plan_sha256,
--   DROP COLUMN IF EXISTS run_kind;

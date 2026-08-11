-- Relief Apply 1A audit-run schema preparation
--
-- DESIGN-ONLY MIGRATION.
-- This file has not been deployed to Supabase. It intentionally contains no
-- INSERT/UPDATE/DELETE, no live Apply RPC, and no live data mutation.
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
          AND source_checksum = 'F6824FDC7CD29DF8C1F45BA749C1B28D319FB34803C55459BBE748EF65937624'
          AND approved_plan_sha256 = '7400626bc99061af7ba82c29969fc8929d7394c59afcfe574e1880521bad2b45'
          AND approved_manifest_sha256 = '1de1a71186b80ce043b48fc5f4d6c4bc6ed9d1c964b3ddf7ad3b96ddd073bfa0'
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

CREATE UNIQUE INDEX IF NOT EXISTS import_runs_apply_1a_manifest_key
  ON public.import_runs (run_kind, approved_manifest_sha256)
  WHERE run_kind = 'apply_1a' AND approved_manifest_sha256 IS NOT NULL;

COMMENT ON COLUMN public.import_runs.run_kind IS
  'Run family: import for the existing importer, apply_1a for the approved enrichment boundary.';
COMMENT ON COLUMN public.import_runs.transaction_outcome IS
  'Apply transaction result. committed is the only successful live mutation outcome.';
COMMENT ON COLUMN public.import_runs.rollback_summary IS
  'Operator-safe summary of a rejected or rolled-back Apply 1A attempt; never stores secrets.';

COMMIT;

-- Documented rollback (not executed here):
--
-- DROP INDEX IF EXISTS public.import_runs_apply_1a_manifest_key;
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

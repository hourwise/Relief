-- R5B: add one generic, manifest-backed audit representation for bounded
-- source applies. Historical apply_1a and apply_r4b contracts remain exact.

ALTER TABLE public.import_runs
  DROP CONSTRAINT import_runs_apply_1a_committed_check;

ALTER TABLE public.import_runs
  ADD CONSTRAINT import_runs_apply_1a_committed_check
  CHECK (
    transaction_outcome <> 'committed'::text
    OR (
      (
        run_kind = 'apply_1a'
        AND status = 'completed'
        AND completed_at IS NOT NULL
        AND requested_operation_count = 48
        AND ready_count = 48
        AND applied_count = 48
        AND stale_count = 0
        AND failed_count = 0
      )
      OR (
        run_kind = 'apply_r4b'
        AND status = 'completed'
        AND completed_at IS NOT NULL
        AND requested_operation_count = 89
        AND ready_count = 89
        AND applied_count = 89
        AND stale_count = 0
        AND failed_count = 0
      )
      OR (
        run_kind = 'governed_source_apply'
        AND status = 'completed'
        AND completed_at IS NOT NULL
        AND requested_operation_count > 0
        AND ready_count = requested_operation_count
        AND applied_count = requested_operation_count
        AND stale_count = 0
        AND failed_count = 0
      )
    )
  );

ALTER TABLE public.import_runs
  DROP CONSTRAINT import_runs_run_kind_check;

ALTER TABLE public.import_runs
  ADD CONSTRAINT import_runs_run_kind_check
  CHECK (
    run_kind = ANY (
      ARRAY[
        'import'::text,
        'apply_1a'::text,
        'apply_r4b'::text,
        'governed_source_apply'::text
      ]
    )
  );

ALTER TABLE public.import_runs
  ADD CONSTRAINT import_runs_governed_source_apply_identity_check
  CHECK (
    run_kind <> 'governed_source_apply'::text
    OR (
      source_name <> ''
      AND source_file_name IS NOT NULL
      AND source_file_name ~ '^docs/data/.+_PRODUCTION_APPLY_MANIFEST_[0-9-]+\\.json$'
      AND source_checksum IS NOT NULL
      AND lower(source_checksum) ~ '^[0-9a-f]{64}$'
      AND approved_manifest_sha256 IS NOT NULL
      AND lower(approved_manifest_sha256) = lower(source_checksum)
      AND apply_engine_version ~ '^relief\\.[a-z0-9][a-z0-9._-]*\\.v[0-9]+$'
      AND project_ref = 'bgwxrxkmyaihplaloely'
    )
  );

CREATE INDEX IF NOT EXISTS import_runs_governed_source_apply_manifest_lookup
  ON public.import_runs (run_kind, approved_manifest_sha256)
  WHERE run_kind = 'governed_source_apply'
    AND approved_manifest_sha256 IS NOT NULL;

CREATE UNIQUE INDEX IF NOT EXISTS import_runs_governed_source_apply_committed_manifest_key
  ON public.import_runs (run_kind, approved_manifest_sha256)
  WHERE run_kind = 'governed_source_apply'
    AND approved_manifest_sha256 IS NOT NULL
    AND transaction_outcome = 'committed';

COMMENT ON COLUMN public.import_runs.run_kind IS
  'Run family: import for the existing importer, apply_1a/apply_r4b for historical exact contracts, governed_source_apply for manifest-backed source expansion.';

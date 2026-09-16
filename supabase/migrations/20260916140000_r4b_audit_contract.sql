-- R4C: add the explicit audit contract required for the sealed local-authority R4B apply.
-- Existing Apply 1A rows remain governed by their original exact contract.

ALTER TABLE public.import_runs
  DROP CONSTRAINT import_runs_apply_1a_committed_check;

ALTER TABLE public.import_runs
  ADD CONSTRAINT import_runs_apply_1a_committed_check
  CHECK (
    transaction_outcome <> 'committed'
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
    )
  );

ALTER TABLE public.import_runs
  DROP CONSTRAINT import_runs_run_kind_check;

ALTER TABLE public.import_runs
  ADD CONSTRAINT import_runs_run_kind_check
  CHECK (run_kind = ANY (ARRAY['import'::text, 'apply_1a'::text, 'apply_r4b'::text]));

ALTER TABLE public.import_runs
  ADD CONSTRAINT import_runs_apply_r4b_identity_check
  CHECK (
    run_kind <> 'apply_r4b'
    OR (
      source_name = 'Local Authority OGL R4B'
      AND lower(source_checksum) = '0db20d9c6ea254125e5550de94e2303c50f5a3d12a7d4954f34589e30b101685'
      AND lower(approved_manifest_sha256) = '0db20d9c6ea254125e5550de94e2303c50f5a3d12a7d4954f34589e30b101685'
      AND apply_engine_version = 'relief.local-authority-ogl-r4b.v1'
      AND project_ref = 'bgwxrxkmyaihplaloely'
      AND requested_operation_count = 89
    )
  );

-- Correct the generic governed_source_apply identity predicate without
-- changing its scope or any historical run-kind contract.

ALTER TABLE public.import_runs
  DROP CONSTRAINT import_runs_governed_source_apply_identity_check;

ALTER TABLE public.import_runs
  ADD CONSTRAINT import_runs_governed_source_apply_identity_check
  CHECK (
    run_kind <> 'governed_source_apply'::text
    OR (
      source_name <> ''
      AND source_file_name IS NOT NULL
      AND source_file_name ~ '^docs/data/.+_PRODUCTION_APPLY_MANIFEST_[0-9-]+[.]json$'
      AND source_checksum IS NOT NULL
      AND lower(source_checksum) ~ '^[0-9a-f]{64}$'
      AND approved_manifest_sha256 IS NOT NULL
      AND lower(approved_manifest_sha256) = lower(source_checksum)
      AND apply_engine_version ~ '^relief[.][a-z0-9][a-z0-9._-]*[.]v[0-9]+$'
      AND project_ref = 'bgwxrxkmyaihplaloely'
    )
  );

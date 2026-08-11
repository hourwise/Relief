-- Disposable-only execution of the documented Apply 1A schema rollback.
-- This must never be used as a data-corrective rollback after Apply.

BEGIN;

DROP INDEX IF EXISTS public.import_runs_apply_1a_committed_manifest_key;
DROP INDEX IF EXISTS public.import_runs_apply_1a_manifest_lookup;
DROP TRIGGER IF EXISTS relief_apply_1a_registry_immutable_trigger
  ON private.relief_apply_1a_approved_operations;
DROP FUNCTION IF EXISTS private.apply_relief_toilet_map_1a(text, text, text, text, text);
DROP FUNCTION IF EXISTS private.relief_apply_1a_registry_immutable();
DROP TABLE IF EXISTS private.relief_apply_1a_approved_operations;
DROP SCHEMA IF EXISTS private;

ALTER TABLE public.import_runs
  DROP CONSTRAINT IF EXISTS import_runs_apply_1a_committed_check,
  DROP CONSTRAINT IF EXISTS import_runs_apply_1a_outcome_check,
  DROP CONSTRAINT IF EXISTS import_runs_apply_1a_identity_check,
  DROP CONSTRAINT IF EXISTS import_runs_approval_hash_format_check,
  DROP CONSTRAINT IF EXISTS import_runs_transaction_outcome_check,
  DROP CONSTRAINT IF EXISTS import_runs_run_kind_check;

ALTER TABLE public.import_runs
  DROP COLUMN IF EXISTS rollback_summary,
  DROP COLUMN IF EXISTS transaction_outcome,
  DROP COLUMN IF EXISTS failed_count,
  DROP COLUMN IF EXISTS stale_count,
  DROP COLUMN IF EXISTS applied_count,
  DROP COLUMN IF EXISTS ready_count,
  DROP COLUMN IF EXISTS requested_operation_count,
  DROP COLUMN IF EXISTS project_ref,
  DROP COLUMN IF EXISTS apply_engine_version,
  DROP COLUMN IF EXISTS approved_review_commit,
  DROP COLUMN IF EXISTS approved_manifest_sha256,
  DROP COLUMN IF EXISTS approved_plan_sha256,
  DROP COLUMN IF EXISTS run_kind;

COMMIT;

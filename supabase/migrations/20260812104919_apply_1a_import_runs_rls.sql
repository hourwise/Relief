-- Relief Apply 1A bounded audit-row RLS correction.
--
-- The deployed Apply migration already grants relief_apply_owner the exact
-- column-level INSERT/UPDATE privileges it needs on public.import_runs. The
-- production failure showed that RLS, not table-level privilege breadth, was
-- the missing boundary. These policies expose only the frozen Apply 1A audit
-- identity to the bounded owner role; application-facing roles remain
-- default-denied and relief_apply_operator receives no direct table policy.

BEGIN;

CREATE POLICY relief_apply_owner_apply_1a_select
ON public.import_runs
FOR SELECT
TO relief_apply_owner
USING (
  run_kind = 'apply_1a'
  AND source_name = 'Toilet Map UK'
  AND source_file_name = 'TOILET_MAP_APPLY_1A_MANIFEST.json'
  AND lower(coalesce(source_checksum, '')) = 'f6824fdc7cd29df8c1f45ba749c1b28d319fb34803c55459bbe748ef65937624'
  AND lower(coalesce(approved_plan_sha256, '')) = '7400626bc99061af7ba82c29969fc8929d7394c59afcfe574e1880521bad2b45'
  AND lower(coalesce(approved_manifest_sha256, '')) = '1de1a71186b80ce043b48fc5f4d6c4bc6ed9d1c964b3ddf7ad3b96ddd073bfa0'
  AND approved_review_commit = '4710b9ec7a9f5a83aa9e7225400b8a6046ce0e77'
  AND apply_engine_version = 'relief.apply-engine-1a.v1'
  AND project_ref = 'bgwxrxkmyaihplaloely'
);

CREATE POLICY relief_apply_owner_apply_1a_insert
ON public.import_runs
FOR INSERT
TO relief_apply_owner
WITH CHECK (
  run_kind = 'apply_1a'
  AND source_name = 'Toilet Map UK'
  AND source_file_name = 'TOILET_MAP_APPLY_1A_MANIFEST.json'
  AND lower(coalesce(source_checksum, '')) = 'f6824fdc7cd29df8c1f45ba749c1b28d319fb34803c55459bbe748ef65937624'
  AND lower(coalesce(approved_plan_sha256, '')) = '7400626bc99061af7ba82c29969fc8929d7394c59afcfe574e1880521bad2b45'
  AND lower(coalesce(approved_manifest_sha256, '')) = '1de1a71186b80ce043b48fc5f4d6c4bc6ed9d1c964b3ddf7ad3b96ddd073bfa0'
  AND approved_review_commit = '4710b9ec7a9f5a83aa9e7225400b8a6046ce0e77'
  AND apply_engine_version = 'relief.apply-engine-1a.v1'
  AND project_ref = 'bgwxrxkmyaihplaloely'
  AND requested_operation_count = 48
  AND rows_received = 48
  AND rows_valid = 48
  AND status = 'started'
  AND ready_count = 0
  AND applied_count = 0
  AND stale_count = 0
  AND failed_count = 0
  AND transaction_outcome = 'not_started'
  AND rollback_summary IS NULL
);

CREATE POLICY relief_apply_owner_apply_1a_update
ON public.import_runs
FOR UPDATE
TO relief_apply_owner
USING (
  run_kind = 'apply_1a'
  AND source_name = 'Toilet Map UK'
  AND source_file_name = 'TOILET_MAP_APPLY_1A_MANIFEST.json'
  AND lower(coalesce(source_checksum, '')) = 'f6824fdc7cd29df8c1f45ba749c1b28d319fb34803c55459bbe748ef65937624'
  AND lower(coalesce(approved_plan_sha256, '')) = '7400626bc99061af7ba82c29969fc8929d7394c59afcfe574e1880521bad2b45'
  AND lower(coalesce(approved_manifest_sha256, '')) = '1de1a71186b80ce043b48fc5f4d6c4bc6ed9d1c964b3ddf7ad3b96ddd073bfa0'
  AND approved_review_commit = '4710b9ec7a9f5a83aa9e7225400b8a6046ce0e77'
  AND apply_engine_version = 'relief.apply-engine-1a.v1'
  AND project_ref = 'bgwxrxkmyaihplaloely'
)
WITH CHECK (
  run_kind = 'apply_1a'
  AND source_name = 'Toilet Map UK'
  AND source_file_name = 'TOILET_MAP_APPLY_1A_MANIFEST.json'
  AND lower(coalesce(source_checksum, '')) = 'f6824fdc7cd29df8c1f45ba749c1b28d319fb34803c55459bbe748ef65937624'
  AND lower(coalesce(approved_plan_sha256, '')) = '7400626bc99061af7ba82c29969fc8929d7394c59afcfe574e1880521bad2b45'
  AND lower(coalesce(approved_manifest_sha256, '')) = '1de1a71186b80ce043b48fc5f4d6c4bc6ed9d1c964b3ddf7ad3b96ddd073bfa0'
  AND approved_review_commit = '4710b9ec7a9f5a83aa9e7225400b8a6046ce0e77'
  AND apply_engine_version = 'relief.apply-engine-1a.v1'
  AND project_ref = 'bgwxrxkmyaihplaloely'
  AND (
    (
      status = 'completed'
      AND transaction_outcome = 'committed'
      AND requested_operation_count = 48
      AND ready_count = 48
      AND applied_count = 48
      AND stale_count = 0
      AND failed_count = 0
      AND rows_updated = 48
      AND rollback_summary IS NULL
    )
    OR
    (
      status = 'failed'
      AND transaction_outcome = 'rolled_back'
      AND requested_operation_count = 48
      AND applied_count = 0
      AND rows_updated = 0
      AND failed_count = 1
      AND ready_count BETWEEN 0 AND 48
      AND stale_count BETWEEN 0 AND 48
      AND error_summary IS NOT NULL
      AND rollback_summary IS NOT NULL
    )
  )
);

COMMIT;

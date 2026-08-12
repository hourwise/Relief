-- Relief Apply 1A bounded facilities UPDATE-RLS correction.
--
-- The deployed Apply function already grants relief_apply_owner only the exact
-- six target-column UPDATE privileges. The production failure showed that the
-- facilities table had no UPDATE policy, so SELECT ... FOR UPDATE admitted no
-- rows under RLS. This forward migration adds one frozen-registry-bounded
-- policy; it does not broaden table privileges, roles, ownership, or grants.

BEGIN;

CREATE POLICY relief_apply_owner_apply_1a_facilities_update
ON public.facilities
FOR UPDATE
TO relief_apply_owner
USING (
  publication_status = 'published'::text
  AND EXISTS (
    SELECT 1
    FROM private.relief_apply_1a_approved_operations AS r
    WHERE r.facility_id = public.facilities.id
      AND r.project_ref = 'bgwxrxkmyaihplaloely'
      AND r.approved_plan_sha256 = '7400626bc99061af7ba82c29969fc8929d7394c59afcfe574e1880521bad2b45'
      AND r.approved_manifest_sha256 = '1de1a71186b80ce043b48fc5f4d6c4bc6ed9d1c964b3ddf7ad3b96ddd073bfa0'
      AND r.approved_review_commit = '4710b9ec7a9f5a83aa9e7225400b8a6046ce0e77'
      AND r.apply_engine_version = 'relief.apply-engine-1a.v1'
      AND r.source_checksum = 'f6824fdc7cd29df8c1f45ba749c1b28d319fb34803c55459bbe748ef65937624'
  )
)
WITH CHECK (
  publication_status = 'published'::text
  AND EXISTS (
    SELECT 1
    FROM private.relief_apply_1a_approved_operations AS r
    WHERE r.facility_id = public.facilities.id
      AND r.project_ref = 'bgwxrxkmyaihplaloely'
      AND r.approved_plan_sha256 = '7400626bc99061af7ba82c29969fc8929d7394c59afcfe574e1880521bad2b45'
      AND r.approved_manifest_sha256 = '1de1a71186b80ce043b48fc5f4d6c4bc6ed9d1c964b3ddf7ad3b96ddd073bfa0'
      AND r.approved_review_commit = '4710b9ec7a9f5a83aa9e7225400b8a6046ce0e77'
      AND r.apply_engine_version = 'relief.apply-engine-1a.v1'
      AND r.source_checksum = 'f6824fdc7cd29df8c1f45ba749c1b28d319fb34803c55459bbe748ef65937624'
  )
);

COMMIT;

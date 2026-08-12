-- Relief Apply 1A post-Apply sealing.
--
-- This forward migration preserves the completed Apply evidence and function
-- definition while removing the temporary execution and write surfaces that
-- existed only for the one-time production operation. It intentionally does
-- not change facilities, provenance, facility_sources, import_runs, or the
-- immutable approved-operation registry.

BEGIN;

CREATE TEMP TABLE relief_apply_1a_seal_baseline (
  audit_digest text NOT NULL,
  registry_digest text NOT NULL,
  facilities_digest text NOT NULL,
  source_digest text NOT NULL
) ON COMMIT DROP;

DO $$
DECLARE
  v_count bigint;
  v_function_owner text;
  v_function_security_definer boolean;
  v_function_search_path boolean;
BEGIN
  -- Fail closed if the completed Apply evidence is not exactly the approved
  -- state that this seal is authorized to close.
  SELECT count(*) INTO v_count
  FROM private.relief_apply_1a_approved_operations;
  IF v_count <> 48 THEN
    RAISE EXCEPTION 'Apply 1A seal precondition failed: registry rows = %, expected 48', v_count;
  END IF;

  SELECT count(*) INTO v_count
  FROM public.import_runs
  WHERE run_kind = 'apply_1a'
    AND source_name = 'Toilet Map UK'
    AND source_file_name = 'TOILET_MAP_APPLY_1A_MANIFEST.json'
    AND lower(coalesce(source_checksum, '')) = 'f6824fdc7cd29df8c1f45ba749c1b28d319fb34803c55459bbe748ef65937624'
    AND approved_plan_sha256 = '7400626bc99061af7ba82c29969fc8929d7394c59afcfe574e1880521bad2b45'
    AND approved_manifest_sha256 = '1de1a71186b80ce043b48fc5f4d6c4bc6ed9d1c964b3ddf7ad3b96ddd073bfa0'
    AND approved_review_commit = '4710b9ec7a9f5a83aa9e7225400b8a6046ce0e77'
    AND apply_engine_version = 'relief.apply-engine-1a.v1'
    AND project_ref = 'bgwxrxkmyaihplaloely'
    AND status = 'completed'
    AND transaction_outcome = 'committed'
    AND requested_operation_count = 48
    AND ready_count = 48
    AND applied_count = 48
    AND stale_count = 0
    AND failed_count = 0
    AND rows_updated = 48;
  IF v_count <> 1 THEN
    RAISE EXCEPTION 'Apply 1A seal precondition failed: committed approved-manifest rows = %, expected 1', v_count;
  END IF;

  SELECT count(*) INTO v_count
  FROM public.import_runs
  WHERE id = '390f7338-2099-4953-ae47-f9e49ff3691c'::uuid
    AND status = 'completed'
    AND transaction_outcome = 'committed'
    AND applied_count = 48
    AND rows_updated = 48;
  IF v_count <> 1 THEN
    RAISE EXCEPTION 'Apply 1A seal precondition failed: successful run evidence is missing or changed';
  END IF;

  SELECT count(*) INTO v_count
  FROM public.import_runs
  WHERE id = '676893a6-c7ac-4727-af82-4d6bb91faf9a'::uuid
    AND status = 'failed'
    AND transaction_outcome = 'rolled_back'
    AND applied_count = 0
    AND rows_updated = 0;
  IF v_count <> 1 THEN
    RAISE EXCEPTION 'Apply 1A seal precondition failed: historical rolled-back run evidence is missing or changed';
  END IF;

  SELECT count(*) INTO v_count
  FROM pg_catalog.pg_proc AS p
  WHERE p.oid = 'private.apply_relief_toilet_map_1a(text,text,text,text,text)'::regprocedure;
  IF v_count <> 1 THEN
    RAISE EXCEPTION 'Apply 1A seal precondition failed: function count = %, expected 1', v_count;
  END IF;

  SELECT
    pg_catalog.pg_get_userbyid(p.proowner),
    p.prosecdef,
    coalesce(p.proconfig, ARRAY[]::text[]) @> ARRAY['search_path=""']::text[]
  INTO v_function_owner, v_function_security_definer, v_function_search_path
  FROM pg_catalog.pg_proc AS p
  WHERE p.oid = 'private.apply_relief_toilet_map_1a(text,text,text,text,text)'::regprocedure;
  IF v_function_owner <> 'relief_apply_owner'
     OR v_function_security_definer IS DISTINCT FROM true
     OR v_function_search_path IS DISTINCT FROM true THEN
    RAISE EXCEPTION 'Apply 1A seal precondition failed: function owner/security/search_path identity is not frozen';
  END IF;

  SELECT count(*) INTO v_count
  FROM pg_catalog.pg_roles
  WHERE rolname IN ('relief_apply_owner', 'relief_apply_operator')
    AND rolcanlogin = false
    AND rolsuper = false
    AND rolbypassrls = false;
  IF v_count <> 2 THEN
    RAISE EXCEPTION 'Apply 1A seal precondition failed: bounded role state is not NOLOGIN/NOSUPERUSER/NOBYPASSRLS';
  END IF;

  SELECT count(*) INTO v_count
  FROM pg_catalog.pg_policies
  WHERE schemaname = 'public'
    AND tablename = 'facilities'
    AND policyname = 'relief_apply_owner_apply_1a_facilities_update'
    AND cmd = 'UPDATE';
  IF v_count <> 1 THEN
    RAISE EXCEPTION 'Apply 1A seal precondition failed: temporary facilities UPDATE policy is missing';
  END IF;

  SELECT count(*) INTO v_count
  FROM pg_catalog.pg_policies
  WHERE schemaname = 'public'
    AND tablename = 'import_runs'
    AND policyname = 'relief_apply_owner_apply_1a_insert'
    AND cmd = 'INSERT';
  IF v_count <> 1 THEN
    RAISE EXCEPTION 'Apply 1A seal precondition failed: temporary import_runs INSERT policy is missing';
  END IF;

  SELECT count(*) INTO v_count
  FROM pg_catalog.pg_policies
  WHERE schemaname = 'public'
    AND tablename = 'import_runs'
    AND policyname = 'relief_apply_owner_apply_1a_update'
    AND cmd = 'UPDATE';
  IF v_count <> 1 THEN
    RAISE EXCEPTION 'Apply 1A seal precondition failed: temporary import_runs UPDATE policy is missing';
  END IF;

  SELECT count(*) INTO v_count
  FROM pg_catalog.pg_policies
  WHERE schemaname = 'public'
    AND tablename = 'import_runs'
    AND policyname = 'relief_apply_owner_apply_1a_select'
    AND cmd = 'SELECT';
  IF v_count <> 1 THEN
    RAISE EXCEPTION 'Apply 1A seal precondition failed: frozen import_runs SELECT policy is missing';
  END IF;

  IF NOT pg_catalog.has_schema_privilege('relief_apply_operator', 'private', 'USAGE') THEN
    RAISE EXCEPTION 'Apply 1A seal precondition failed: operator private schema USAGE is absent';
  END IF;
  IF NOT pg_catalog.has_function_privilege(
    'relief_apply_operator',
    'private.apply_relief_toilet_map_1a(text,text,text,text,text)',
    'EXECUTE'
  ) THEN
    RAISE EXCEPTION 'Apply 1A seal precondition failed: operator function EXECUTE is absent';
  END IF;

  INSERT INTO pg_temp.relief_apply_1a_seal_baseline (
    audit_digest,
    registry_digest,
    facilities_digest,
    source_digest
  )
  SELECT
    pg_catalog.md5(coalesce((
      SELECT pg_catalog.jsonb_agg(pg_catalog.to_jsonb(i) ORDER BY i.id)::text
      FROM public.import_runs AS i
      WHERE i.id IN (
        '390f7338-2099-4953-ae47-f9e49ff3691c'::uuid,
        '676893a6-c7ac-4727-af82-4d6bb91faf9a'::uuid
      )
    ), '[]')),
    pg_catalog.md5(coalesce((
      SELECT pg_catalog.jsonb_agg(pg_catalog.to_jsonb(r) ORDER BY r.operation_id)::text
      FROM private.relief_apply_1a_approved_operations AS r
    ), '[]')),
    pg_catalog.md5(coalesce((
      SELECT pg_catalog.jsonb_agg(
        pg_catalog.jsonb_build_object(
          'id', f.id,
          'has_baby_changing', f.has_baby_changing,
          'requires_radar_key', f.requires_radar_key,
          'is_gender_neutral', f.is_gender_neutral,
          'is_accessible', f.is_accessible,
          'is_free', f.is_free,
          'field_provenance', f.field_provenance,
          'publication_status', f.publication_status
        ) ORDER BY f.id
      )::text
      FROM public.facilities AS f
      WHERE f.id IN (
        SELECT DISTINCT facility_id
        FROM private.relief_apply_1a_approved_operations
      )
    ), '[]')),
    pg_catalog.md5(coalesce((
      SELECT pg_catalog.jsonb_agg(pg_catalog.to_jsonb(s) ORDER BY s.id)::text
      FROM public.facility_sources AS s
    ), '[]'));
END;
$$;

-- Revoke only the temporary operator execution surface.
REVOKE EXECUTE ON FUNCTION private.apply_relief_toilet_map_1a(text, text, text, text, text)
  FROM relief_apply_operator;
REVOKE USAGE ON SCHEMA private FROM relief_apply_operator;

-- Remove only the frozen Apply facilities UPDATE path. The public published
-- SELECT policy is intentionally preserved.
DROP POLICY relief_apply_owner_apply_1a_facilities_update ON public.facilities;
REVOKE UPDATE (
  has_baby_changing,
  requires_radar_key,
  is_gender_neutral,
  is_accessible,
  is_free,
  field_provenance
) ON TABLE public.facilities FROM relief_apply_owner;

-- Remove only the temporary Apply audit INSERT/UPDATE path and retain the
-- frozen read-only SELECT policy and SELECT privilege.
DROP POLICY relief_apply_owner_apply_1a_insert ON public.import_runs;
DROP POLICY relief_apply_owner_apply_1a_update ON public.import_runs;
REVOKE INSERT (
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
) ON TABLE public.import_runs FROM relief_apply_owner;
REVOKE UPDATE (
  status,
  completed_at,
  rows_updated,
  ready_count,
  applied_count,
  stale_count,
  failed_count,
  transaction_outcome,
  error_summary,
  rollback_summary
) ON TABLE public.import_runs FROM relief_apply_owner;

DO $$
DECLARE
  v_count bigint;
  v_function_owner text;
  v_function_security_definer boolean;
  v_function_search_path boolean;
  v_audit_digest text;
  v_registry_digest text;
  v_facilities_digest text;
  v_source_digest text;
  v_baseline record;
BEGIN
  SELECT * INTO v_baseline FROM pg_temp.relief_apply_1a_seal_baseline;
  IF NOT FOUND THEN
    RAISE EXCEPTION 'Apply 1A seal postcondition failed: baseline is missing';
  END IF;

  IF pg_catalog.has_schema_privilege('relief_apply_operator', 'private', 'USAGE') THEN
    RAISE EXCEPTION 'Apply 1A seal postcondition failed: operator private schema USAGE remains';
  END IF;
  IF pg_catalog.has_function_privilege(
    'relief_apply_operator',
    'private.apply_relief_toilet_map_1a(text,text,text,text,text)',
    'EXECUTE'
  ) THEN
    RAISE EXCEPTION 'Apply 1A seal postcondition failed: operator function EXECUTE remains';
  END IF;

  SELECT count(*) INTO v_count
  FROM pg_catalog.pg_roles
  WHERE rolname = 'relief_apply_owner'
    AND rolcanlogin = false
    AND rolsuper = false
    AND rolbypassrls = false;
  IF v_count <> 1 THEN
    RAISE EXCEPTION 'Apply 1A seal postcondition failed: owner role state changed';
  END IF;

  SELECT count(*) INTO v_count
  FROM pg_catalog.pg_policies
  WHERE schemaname = 'public'
    AND tablename = 'facilities'
    AND policyname = 'relief_apply_owner_apply_1a_facilities_update';
  IF v_count <> 0 THEN
    RAISE EXCEPTION 'Apply 1A seal postcondition failed: facilities Apply UPDATE policy remains';
  END IF;

  IF pg_catalog.has_table_privilege('relief_apply_owner', 'public.facilities', 'UPDATE') THEN
    RAISE EXCEPTION 'Apply 1A seal postcondition failed: owner table-level facilities UPDATE remains';
  END IF;
  IF pg_catalog.has_column_privilege('relief_apply_owner', 'public.facilities', 'has_baby_changing', 'UPDATE')
     OR pg_catalog.has_column_privilege('relief_apply_owner', 'public.facilities', 'requires_radar_key', 'UPDATE')
     OR pg_catalog.has_column_privilege('relief_apply_owner', 'public.facilities', 'is_gender_neutral', 'UPDATE')
     OR pg_catalog.has_column_privilege('relief_apply_owner', 'public.facilities', 'is_accessible', 'UPDATE')
     OR pg_catalog.has_column_privilege('relief_apply_owner', 'public.facilities', 'is_free', 'UPDATE')
     OR pg_catalog.has_column_privilege('relief_apply_owner', 'public.facilities', 'field_provenance', 'UPDATE')
     OR pg_catalog.has_column_privilege('relief_apply_owner', 'public.facilities', 'publication_status', 'UPDATE') THEN
    RAISE EXCEPTION 'Apply 1A seal postcondition failed: owner facilities UPDATE column privilege remains';
  END IF;

  SELECT count(*) INTO v_count
  FROM pg_catalog.pg_policies
  WHERE schemaname = 'public'
    AND tablename = 'import_runs'
    AND policyname = 'relief_apply_owner_apply_1a_select'
    AND cmd = 'SELECT';
  IF v_count <> 1 THEN
    RAISE EXCEPTION 'Apply 1A seal postcondition failed: frozen import_runs SELECT policy is absent';
  END IF;
  SELECT count(*) INTO v_count
  FROM pg_catalog.pg_policies
  WHERE schemaname = 'public'
    AND tablename = 'import_runs'
    AND policyname IN ('relief_apply_owner_apply_1a_insert', 'relief_apply_owner_apply_1a_update');
  IF v_count <> 0 THEN
    RAISE EXCEPTION 'Apply 1A seal postcondition failed: import_runs Apply INSERT/UPDATE policy remains';
  END IF;

  IF pg_catalog.has_column_privilege('relief_apply_owner', 'public.import_runs', 'source_name', 'INSERT')
     OR pg_catalog.has_column_privilege('relief_apply_owner', 'public.import_runs', 'source_file_name', 'INSERT')
     OR pg_catalog.has_column_privilege('relief_apply_owner', 'public.import_runs', 'source_checksum', 'INSERT')
     OR pg_catalog.has_column_privilege('relief_apply_owner', 'public.import_runs', 'status', 'INSERT')
     OR pg_catalog.has_column_privilege('relief_apply_owner', 'public.import_runs', 'started_at', 'INSERT')
     OR pg_catalog.has_column_privilege('relief_apply_owner', 'public.import_runs', 'rows_received', 'INSERT')
     OR pg_catalog.has_column_privilege('relief_apply_owner', 'public.import_runs', 'rows_valid', 'INSERT')
     OR pg_catalog.has_column_privilege('relief_apply_owner', 'public.import_runs', 'run_kind', 'INSERT')
     OR pg_catalog.has_column_privilege('relief_apply_owner', 'public.import_runs', 'approved_plan_sha256', 'INSERT')
     OR pg_catalog.has_column_privilege('relief_apply_owner', 'public.import_runs', 'approved_manifest_sha256', 'INSERT')
     OR pg_catalog.has_column_privilege('relief_apply_owner', 'public.import_runs', 'approved_review_commit', 'INSERT')
     OR pg_catalog.has_column_privilege('relief_apply_owner', 'public.import_runs', 'apply_engine_version', 'INSERT')
     OR pg_catalog.has_column_privilege('relief_apply_owner', 'public.import_runs', 'project_ref', 'INSERT')
     OR pg_catalog.has_column_privilege('relief_apply_owner', 'public.import_runs', 'requested_operation_count', 'INSERT')
     OR pg_catalog.has_column_privilege('relief_apply_owner', 'public.import_runs', 'ready_count', 'INSERT')
     OR pg_catalog.has_column_privilege('relief_apply_owner', 'public.import_runs', 'applied_count', 'INSERT')
     OR pg_catalog.has_column_privilege('relief_apply_owner', 'public.import_runs', 'stale_count', 'INSERT')
     OR pg_catalog.has_column_privilege('relief_apply_owner', 'public.import_runs', 'failed_count', 'INSERT')
     OR pg_catalog.has_column_privilege('relief_apply_owner', 'public.import_runs', 'transaction_outcome', 'INSERT')
     OR pg_catalog.has_column_privilege('relief_apply_owner', 'public.import_runs', 'rollback_summary', 'INSERT') THEN
    RAISE EXCEPTION 'Apply 1A seal postcondition failed: owner Apply-specific import_runs INSERT privilege remains';
  END IF;
  IF pg_catalog.has_column_privilege('relief_apply_owner', 'public.import_runs', 'status', 'UPDATE')
     OR pg_catalog.has_column_privilege('relief_apply_owner', 'public.import_runs', 'completed_at', 'UPDATE')
     OR pg_catalog.has_column_privilege('relief_apply_owner', 'public.import_runs', 'rows_updated', 'UPDATE')
     OR pg_catalog.has_column_privilege('relief_apply_owner', 'public.import_runs', 'ready_count', 'UPDATE')
     OR pg_catalog.has_column_privilege('relief_apply_owner', 'public.import_runs', 'applied_count', 'UPDATE')
     OR pg_catalog.has_column_privilege('relief_apply_owner', 'public.import_runs', 'stale_count', 'UPDATE')
     OR pg_catalog.has_column_privilege('relief_apply_owner', 'public.import_runs', 'failed_count', 'UPDATE')
     OR pg_catalog.has_column_privilege('relief_apply_owner', 'public.import_runs', 'transaction_outcome', 'UPDATE')
     OR pg_catalog.has_column_privilege('relief_apply_owner', 'public.import_runs', 'error_summary', 'UPDATE')
     OR pg_catalog.has_column_privilege('relief_apply_owner', 'public.import_runs', 'rollback_summary', 'UPDATE') THEN
    RAISE EXCEPTION 'Apply 1A seal postcondition failed: owner Apply-specific import_runs UPDATE privilege remains';
  END IF;
  IF NOT pg_catalog.has_table_privilege('relief_apply_owner', 'public.import_runs', 'SELECT') THEN
    RAISE EXCEPTION 'Apply 1A seal postcondition failed: owner import_runs SELECT was removed';
  END IF;

  SELECT count(*) INTO v_count
  FROM private.relief_apply_1a_approved_operations;
  IF v_count <> 48 THEN
    RAISE EXCEPTION 'Apply 1A seal postcondition failed: registry rows changed';
  END IF;

  SELECT
    pg_catalog.pg_get_userbyid(p.proowner),
    p.prosecdef,
    coalesce(p.proconfig, ARRAY[]::text[]) @> ARRAY['search_path=""']::text[]
  INTO v_function_owner, v_function_security_definer, v_function_search_path
  FROM pg_catalog.pg_proc AS p
  WHERE p.oid = 'private.apply_relief_toilet_map_1a(text,text,text,text,text)'::regprocedure;
  IF v_function_owner <> 'relief_apply_owner'
     OR v_function_security_definer IS DISTINCT FROM true
     OR v_function_search_path IS DISTINCT FROM true THEN
    RAISE EXCEPTION 'Apply 1A seal postcondition failed: preserved function identity changed';
  END IF;

  IF pg_catalog.has_function_privilege('public', 'private.apply_relief_toilet_map_1a(text,text,text,text,text)', 'EXECUTE')
     OR pg_catalog.has_function_privilege('anon', 'private.apply_relief_toilet_map_1a(text,text,text,text,text)', 'EXECUTE')
     OR pg_catalog.has_function_privilege('authenticated', 'private.apply_relief_toilet_map_1a(text,text,text,text,text)', 'EXECUTE')
     OR pg_catalog.has_function_privilege('service_role', 'private.apply_relief_toilet_map_1a(text,text,text,text,text)', 'EXECUTE')
     OR pg_catalog.has_function_privilege('authenticator', 'private.apply_relief_toilet_map_1a(text,text,text,text,text)', 'EXECUTE') THEN
    RAISE EXCEPTION 'Apply 1A seal postcondition failed: application-facing EXECUTE privilege appears';
  END IF;

  SELECT count(*) INTO v_count
  FROM public.import_runs
  WHERE id = '390f7338-2099-4953-ae47-f9e49ff3691c'::uuid
    AND status = 'completed'
    AND transaction_outcome = 'committed'
    AND applied_count = 48
    AND rows_updated = 48;
  IF v_count <> 1 THEN
    RAISE EXCEPTION 'Apply 1A seal postcondition failed: successful audit row changed';
  END IF;
  SELECT count(*) INTO v_count
  FROM public.import_runs
  WHERE id = '676893a6-c7ac-4727-af82-4d6bb91faf9a'::uuid
    AND status = 'failed'
    AND transaction_outcome = 'rolled_back'
    AND applied_count = 0
    AND rows_updated = 0;
  IF v_count <> 1 THEN
    RAISE EXCEPTION 'Apply 1A seal postcondition failed: historical failed audit row changed';
  END IF;

  SELECT pg_catalog.md5(coalesce((
    SELECT pg_catalog.jsonb_agg(pg_catalog.to_jsonb(i) ORDER BY i.id)::text
    FROM public.import_runs AS i
    WHERE i.id IN (
      '390f7338-2099-4953-ae47-f9e49ff3691c'::uuid,
      '676893a6-c7ac-4727-af82-4d6bb91faf9a'::uuid
    )
  ), '[]')) INTO v_audit_digest;
  SELECT pg_catalog.md5(coalesce((
    SELECT pg_catalog.jsonb_agg(pg_catalog.to_jsonb(r) ORDER BY r.operation_id)::text
    FROM private.relief_apply_1a_approved_operations AS r
  ), '[]')) INTO v_registry_digest;
  SELECT pg_catalog.md5(coalesce((
    SELECT pg_catalog.jsonb_agg(
      pg_catalog.jsonb_build_object(
        'id', f.id,
        'has_baby_changing', f.has_baby_changing,
        'requires_radar_key', f.requires_radar_key,
        'is_gender_neutral', f.is_gender_neutral,
        'is_accessible', f.is_accessible,
        'is_free', f.is_free,
        'field_provenance', f.field_provenance,
        'publication_status', f.publication_status
      ) ORDER BY f.id
    )::text
    FROM public.facilities AS f
    WHERE f.id IN (
      SELECT DISTINCT facility_id
      FROM private.relief_apply_1a_approved_operations
    )
  ), '[]')) INTO v_facilities_digest;
  SELECT pg_catalog.md5(coalesce((
    SELECT pg_catalog.jsonb_agg(pg_catalog.to_jsonb(s) ORDER BY s.id)::text
    FROM public.facility_sources AS s
  ), '[]')) INTO v_source_digest;
  IF v_audit_digest <> v_baseline.audit_digest
     OR v_registry_digest <> v_baseline.registry_digest
     OR v_facilities_digest <> v_baseline.facilities_digest
     OR v_source_digest <> v_baseline.source_digest THEN
    RAISE EXCEPTION 'Apply 1A seal postcondition failed: preserved audit, registry, facility, or source data changed';
  END IF;
END;
$$;

COMMIT;

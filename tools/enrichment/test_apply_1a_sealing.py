#!/usr/bin/env python3
"""Disposable PostgreSQL regression for the post-Apply 1A seal.

The regression builds the approved Apply fixture, creates one durable rolled-
back attempt followed by one committed Apply, applies the new sealing
migration only to disposable databases, and proves that evidence remains
readable while every temporary write/execution path is closed.

It never connects to Supabase production.
"""

from __future__ import annotations

import json
import argparse
import re
import shutil
import sys
import uuid
from pathlib import Path
from typing import Any

try:
    from . import test_apply_1a_import_runs_rls as base
except ImportError:
    import test_apply_1a_import_runs_rls as base


ROOT = Path(__file__).resolve().parents[2]
FACILITIES_MIGRATION = next(ROOT.glob("supabase/migrations/*_apply_1a_facilities_update_rls.sql"))
SEAL_MIGRATION = next(ROOT.glob("supabase/migrations/*_seal_apply_1a_execution_path.sql"))
POSTCHECK_FAULT = ROOT / "tools/enrichment/disposable_apply_1a_postcheck_fault.sql"

REVIEW_COMMIT = "4710b9ec7a9f5a83aa9e7225400b8a6046ce0e77"
ENGINE_VERSION = "relief.apply-engine-1a.v1"
PRODUCTION_SUCCESS_RUN_ID = "390f7338-2099-4953-ae47-f9e49ff3691c"
PRODUCTION_FAILED_RUN_ID = "676893a6-c7ac-4727-af82-4d6bb91faf9a"
SUCCESS_RESULT = {
    "status": "COMMITTED",
    "requested_operation_count": 48,
    "ready_count": 48,
    "applied_count": 48,
    "stale_count": 0,
    "failed_count": 0,
    "mutations_committed": True,
}
FAILED_RESULT = {
    "status": "ROLLED_BACK",
    "applied_count": 0,
    "failed_count": 1,
    "mutations_committed": False,
}


def prepare_fixture(args: Any, database: str) -> None:
    base.load_apply_fixture(args, database)
    base.apply_corrective_migration(args, database)
    base.run_psql(
        args,
        database,
        sql="""
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
""",
    )
    base.run_psql(args, database, file=FACILITIES_MIGRATION)


def json_sql(args: Any, database: str, sql: str) -> dict[str, Any]:
    value = base.scalar(args, database, sql)
    try:
        parsed = json.loads(value)
    except json.JSONDecodeError as error:
        raise AssertionError(f"Expected JSON output, received {value!r}") from error
    if not isinstance(parsed, dict):
        raise AssertionError(f"Expected JSON object, received {parsed!r}")
    return parsed


def data_snapshot(args: Any, database: str) -> dict[str, Any]:
    return json_sql(
        args,
        database,
        """
SELECT json_build_object(
  'registry_digest', (SELECT md5(coalesce((SELECT jsonb_agg(to_jsonb(r) ORDER BY r.operation_id)::text FROM private.relief_apply_1a_approved_operations r), '[]'))),
  'facilities_digest', (SELECT md5(coalesce((SELECT jsonb_agg(jsonb_build_object(
      'id', f.id,
      'has_baby_changing', f.has_baby_changing,
      'requires_radar_key', f.requires_radar_key,
      'is_gender_neutral', f.is_gender_neutral,
      'is_accessible', f.is_accessible,
      'is_free', f.is_free,
      'field_provenance', f.field_provenance,
      'publication_status', f.publication_status
    ) ORDER BY f.id)::text
    FROM public.facilities f
    WHERE f.id IN (SELECT DISTINCT facility_id FROM private.relief_apply_1a_approved_operations)), '[]'))),
  'source_digest', (SELECT md5(coalesce((SELECT jsonb_agg(to_jsonb(s) ORDER BY s.id)::text FROM public.facility_sources s), '[]'))),
  'publication_digest', (SELECT md5(coalesce((SELECT jsonb_agg(jsonb_build_object('id', f.id, 'publication_status', f.publication_status) ORDER BY f.id)::text FROM public.facilities f WHERE f.id IN (SELECT DISTINCT facility_id FROM private.relief_apply_1a_approved_operations)), '[]')))
);
""",
    )


def audit_snapshot(args: Any, database: str) -> dict[str, Any]:
    return json_sql(
        args,
        database,
        """
SELECT json_build_object(
  'digest', (SELECT md5(coalesce((SELECT jsonb_agg(to_jsonb(i) ORDER BY i.id)::text FROM public.import_runs i WHERE i.run_kind='apply_1a'), '[]'))),
  'rows', (SELECT count(*) FROM public.import_runs WHERE run_kind='apply_1a'),
  'committed', (SELECT count(*) FROM public.import_runs WHERE run_kind='apply_1a' AND status='completed' AND transaction_outcome='committed'),
  'rolled_back', (SELECT count(*) FROM public.import_runs WHERE run_kind='apply_1a' AND status='failed' AND transaction_outcome='rolled_back')
);
""",
    )


def apply_two_run_history(args: Any, database: str) -> dict[str, Any]:
    rollback_data_before = data_snapshot(args, database)
    base.run_psql(args, database, file=POSTCHECK_FAULT)
    failed = base.apply_call(args, database)
    if {key: failed.get(key) for key in FAILED_RESULT} != FAILED_RESULT:
        raise AssertionError(f"Expected the disposable historical Apply attempt to roll back: {failed!r}")
    rollback_data_after = data_snapshot(args, database)
    if rollback_data_after != rollback_data_before:
        raise AssertionError(
            f"Rolled-back Apply changed disposable facility/provenance/source data: "
            f"{rollback_data_before!r} -> {rollback_data_after!r}"
        )

    base.run_psql(
        args,
        database,
        sql="""
DROP TRIGGER disposable_apply_1a_postcheck_trip_trigger ON public.facilities;
DROP FUNCTION public.disposable_apply_1a_postcheck_trip();
""",
    )
    committed_data_before = data_snapshot(args, database)
    committed = base.apply_call(args, database)
    if {key: committed.get(key) for key in SUCCESS_RESULT} != SUCCESS_RESULT:
        raise AssertionError(f"Expected the disposable second Apply attempt to commit: {committed!r}")
    committed_state = json_sql(
        args,
        database,
        f"""
WITH operation_state AS (
  SELECT o.field, o.proposed_value,
    CASE o.field
      WHEN 'has_baby_changing' THEN f.has_baby_changing
      WHEN 'requires_radar_key' THEN f.requires_radar_key
      WHEN 'is_gender_neutral' THEN f.is_gender_neutral
      WHEN 'is_accessible' THEN f.is_accessible
      WHEN 'is_free' THEN f.is_free
    END AS actual_value,
    f.field_provenance -> o.field AS provenance
  FROM private.relief_apply_1a_approved_operations o
  JOIN public.facilities f ON f.id=o.facility_id
), provenance_state AS (
  SELECT count(*) FILTER (
    WHERE provenance ->> 'source' = 'Toilet Map UK'
      AND provenance ->> 'source_name' = 'Toilet Map UK'
      AND provenance ->> 'basis' = 'EXACT_SOURCE_ID'
      AND provenance ->> 'confidence' = 'HIGH'
      AND provenance ->> 'source_snapshot_checksum' = '{base.SOURCE_SHA}'
      AND provenance ->> 'approved_plan_sha256' = '{base.PLAN_SHA}'
      AND provenance ->> 'approved_manifest_sha256' = '{base.MANIFEST_SHA}'
      AND provenance ->> 'approved_review_commit' = '{REVIEW_COMMIT}'
      AND provenance ->> 'apply_engine_version' = '{ENGINE_VERSION}'
      AND provenance -> 'previous_value' = 'null'::jsonb
  ) AS matching
  FROM operation_state
)
SELECT json_build_object(
  'target_correct', (SELECT count(*) FROM operation_state WHERE actual_value = proposed_value),
  'target_still_null', (SELECT count(*) FROM operation_state WHERE actual_value IS NULL),
  'provenance_matches', (SELECT matching FROM provenance_state),
  'successful_audit_row', (SELECT count(*) FROM public.import_runs WHERE id='{committed['run_id']}'::uuid AND status='completed' AND transaction_outcome='committed' AND applied_count=48 AND rows_updated=48)
);
""",
    )
    if committed_state != {"target_correct": 48, "target_still_null": 0, "provenance_matches": 48, "successful_audit_row": 1}:
        raise AssertionError(f"Disposable committed values/provenance are wrong: {committed_state!r}")
    committed_data_after = data_snapshot(args, database)
    if committed_data_after["source_digest"] != committed_data_before["source_digest"]:
        raise AssertionError("Committed disposable Apply changed facility_sources")
    if committed_data_after["publication_digest"] != committed_data_before["publication_digest"]:
        raise AssertionError("Committed disposable Apply changed publication status")

    # The production seal is intentionally bound to the accepted immutable
    # audit IDs. In disposable PostgreSQL only, replace the generated fixture
    # IDs with those accepted evidence IDs before applying the same migration.
    base.run_psql(
        args,
        database,
        sql=f"""
UPDATE public.import_runs
SET id='{PRODUCTION_FAILED_RUN_ID}'::uuid
WHERE id='{failed['run_id']}'::uuid;
UPDATE public.import_runs
SET id='{PRODUCTION_SUCCESS_RUN_ID}'::uuid
WHERE id='{committed['run_id']}'::uuid;
""",
    )
    failed["run_id"] = PRODUCTION_FAILED_RUN_ID
    committed["run_id"] = PRODUCTION_SUCCESS_RUN_ID

    audit = audit_snapshot(args, database)
    if audit["rows"] != 2 or audit["committed"] != 1 or audit["rolled_back"] != 1:
        raise AssertionError(f"Disposable two-run audit state is wrong: {audit!r}")
    return {
        "failed": failed,
        "committed": committed,
        "committed_state": committed_state,
        "audit_before_seal": audit,
        "data_before_seal": committed_data_after,
    }


def apply_seal(args: Any, database: str) -> None:
    base.run_psql(args, database, file=SEAL_MIGRATION)


def sealed_state(args: Any, database: str) -> dict[str, Any]:
    state = json_sql(
        args,
        database,
        """
SELECT json_build_object(
  'operator_login', (SELECT rolcanlogin FROM pg_roles WHERE rolname='relief_apply_operator'),
  'operator_schema_usage', has_schema_privilege('relief_apply_operator','private','USAGE'),
  'operator_execute', has_function_privilege('relief_apply_operator','private.apply_relief_toilet_map_1a(text,text,text,text,text)','EXECUTE'),
  'owner_login', (SELECT rolcanlogin FROM pg_roles WHERE rolname='relief_apply_owner'),
  'owner_bypassrls', (SELECT rolbypassrls FROM pg_roles WHERE rolname='relief_apply_owner'),
  'owner_facilities_table_update', has_table_privilege('relief_apply_owner','public.facilities','UPDATE'),
  'owner_facilities_column_update', coalesce((SELECT bool_or(has_column_privilege('relief_apply_owner','public.facilities',column_name,'UPDATE')) FROM (VALUES
    ('has_baby_changing'),('requires_radar_key'),('is_gender_neutral'),('is_accessible'),('is_free'),('field_provenance'),('publication_status')
  ) columns(column_name)), false),
  'owner_import_insert', coalesce((SELECT bool_or(has_column_privilege('relief_apply_owner','public.import_runs',column_name,'INSERT')) FROM (VALUES
    ('source_name'),('source_file_name'),('source_checksum'),('status'),('started_at'),('rows_received'),('rows_valid'),('run_kind'),('approved_plan_sha256'),('approved_manifest_sha256'),('approved_review_commit'),('apply_engine_version'),('project_ref'),('requested_operation_count'),('ready_count'),('applied_count'),('stale_count'),('failed_count'),('transaction_outcome'),('rollback_summary')
  ) columns(column_name)), false),
  'owner_import_update', coalesce((SELECT bool_or(has_column_privilege('relief_apply_owner','public.import_runs',column_name,'UPDATE')) FROM (VALUES
    ('status'),('completed_at'),('rows_updated'),('ready_count'),('applied_count'),('stale_count'),('failed_count'),('transaction_outcome'),('error_summary'),('rollback_summary')
  ) columns(column_name)), false),
  'owner_import_select', has_table_privilege('relief_apply_owner','public.import_runs','SELECT'),
  'facilities_apply_update_policies', (SELECT count(*) FROM pg_policies WHERE schemaname='public' AND tablename='facilities' AND policyname='relief_apply_owner_apply_1a_facilities_update'),
  'import_select_policies', (SELECT count(*) FROM pg_policies WHERE schemaname='public' AND tablename='import_runs' AND policyname='relief_apply_owner_apply_1a_select' AND cmd='SELECT'),
  'import_insert_policies', (SELECT count(*) FROM pg_policies WHERE schemaname='public' AND tablename='import_runs' AND policyname='relief_apply_owner_apply_1a_insert'),
  'import_update_policies', (SELECT count(*) FROM pg_policies WHERE schemaname='public' AND tablename='import_runs' AND policyname='relief_apply_owner_apply_1a_update'),
  'registry_rows', (SELECT count(*) FROM private.relief_apply_1a_approved_operations),
  'apply_audit_rows', (SELECT count(*) FROM public.import_runs WHERE run_kind='apply_1a'),
  'function_owner', (SELECT pg_get_userbyid(proowner) FROM pg_proc WHERE oid='private.apply_relief_toilet_map_1a(text,text,text,text,text)'::regprocedure),
  'function_security_definer', (SELECT prosecdef FROM pg_proc WHERE oid='private.apply_relief_toilet_map_1a(text,text,text,text,text)'::regprocedure),
  'function_search_path_empty', (SELECT coalesce(proconfig, ARRAY[]::text[]) @> ARRAY['search_path=""']::text[] FROM pg_proc WHERE oid='private.apply_relief_toilet_map_1a(text,text,text,text,text)'::regprocedure)
);
""",
    )
    expected = {
        "operator_login": False,
        "operator_schema_usage": False,
        "operator_execute": False,
        "owner_login": False,
        "owner_bypassrls": False,
        "owner_facilities_table_update": False,
        "owner_facilities_column_update": False,
        "owner_import_insert": False,
        "owner_import_update": False,
        "owner_import_select": True,
        "facilities_apply_update_policies": 0,
        "import_select_policies": 1,
        "import_insert_policies": 0,
        "import_update_policies": 0,
        "registry_rows": 48,
        "apply_audit_rows": 2,
        "function_owner": "relief_apply_owner",
        "function_security_definer": True,
        "function_search_path_empty": True,
    }
    if state != expected:
        raise AssertionError(f"Sealed privilege/policy state is wrong: {state!r}")
    return state


def privilege_failure(args: Any, database: str, sql: str, expected_fragment: str) -> str:
    result = base.run_psql(args, database, sql=sql, check=False, verbose_errors=True)
    combined = f"{result.stdout}\n{result.stderr}"
    if result.returncode == 0:
        raise AssertionError(f"Expected privilege failure, but SQL succeeded: {combined}")
    if not re.search(r"SQL state:\s*42501|42501", combined):
        raise AssertionError(f"Expected SQLSTATE 42501, received: {combined}")
    if expected_fragment.lower() not in combined.lower():
        raise AssertionError(f"Expected {expected_fragment!r} in privilege error: {combined}")
    return "SQLSTATE 42501: " + expected_fragment


def direct_write_negative_tests(args: Any, database: str) -> dict[str, Any]:
    target_id = base.scalar(
        args,
        database,
        "SELECT facility_id FROM private.relief_apply_1a_approved_operations ORDER BY operation_id LIMIT 1;",
    )
    operator_private = privilege_failure(
        args,
        database,
        "SET ROLE relief_apply_operator; SELECT count(*) FROM private.relief_apply_1a_approved_operations;",
        "permission denied for schema private",
    )
    operator_invoke = privilege_failure(
        args,
        database,
        f"SET ROLE relief_apply_operator; SELECT private.apply_relief_toilet_map_1a('{base.PROJECT_REF}','{base.PLAN_SHA}','{base.MANIFEST_SHA}','{base.SOURCE_SHA}','{base.CONFIRMATION}');",
        "permission denied for schema private",
    )
    owner_facility_update = privilege_failure(
        args,
        database,
        f"SET ROLE relief_apply_owner; UPDATE public.facilities SET is_free = is_free WHERE id='{target_id}'::uuid;",
        "permission denied for table facilities",
    )
    owner_import_insert = privilege_failure(
        args,
        database,
        "SET ROLE relief_apply_owner; INSERT INTO public.import_runs (source_name) VALUES ('blocked');",
        "permission denied for table import_runs",
    )
    owner_success_update = privilege_failure(
        args,
        database,
        "SET ROLE relief_apply_owner; UPDATE public.import_runs SET status = status WHERE id=(SELECT id FROM public.import_runs WHERE status='completed' AND transaction_outcome='committed' LIMIT 1);",
        "permission denied for table import_runs",
    )
    owner_failed_update = privilege_failure(
        args,
        database,
        "SET ROLE relief_apply_owner; UPDATE public.import_runs SET status = status WHERE id=(SELECT id FROM public.import_runs WHERE status='failed' AND transaction_outcome='rolled_back' LIMIT 1);",
        "permission denied for table import_runs",
    )
    evidence = json_sql(
        args,
        database,
        """
SET ROLE relief_apply_owner;
SELECT json_build_object(
  'audit_rows', (SELECT count(*) FROM public.import_runs WHERE run_kind='apply_1a'),
  'registry_rows', (SELECT count(*) FROM private.relief_apply_1a_approved_operations),
  'select_success_rows', (SELECT count(*) FROM public.import_runs WHERE status='completed' AND transaction_outcome='committed'),
  'select_failed_rows', (SELECT count(*) FROM public.import_runs WHERE status='failed' AND transaction_outcome='rolled_back')
);
""",
    )
    if evidence != {"audit_rows": 2, "registry_rows": 48, "select_success_rows": 1, "select_failed_rows": 1}:
        raise AssertionError(f"Owner read-only evidence path is wrong: {evidence!r}")
    return {
        "operator_private_schema": operator_private,
        "operator_invoke": operator_invoke,
        "owner_facility_update": owner_facility_update,
        "owner_import_insert": owner_import_insert,
        "owner_success_update": owner_success_update,
        "owner_failed_update": owner_failed_update,
        "owner_select": evidence,
    }


def owner_already_applied(args: Any, database: str, expected_run_id: str, before: dict[str, Any]) -> dict[str, Any]:
    result = base.apply_call(args, database)
    expected = {
        "status": "ALREADY_APPLIED",
        "run_id": expected_run_id,
        "applied_count": 0,
        "mutations_committed": False,
    }
    if {key: result.get(key) for key in expected} != expected:
        raise AssertionError(f"Sealed owner retry did not return the preserved committed run: {result!r}")
    after = data_snapshot(args, database)
    if after != before:
        raise AssertionError(f"Sealed owner retry changed disposable data: {before!r} -> {after!r}")
    audit = audit_snapshot(args, database)
    if audit["rows"] != 2 or audit["committed"] != 1 or audit["rolled_back"] != 1:
        raise AssertionError(f"Sealed owner retry changed audit history: {audit!r}")
    return {"result": result, "data_unchanged": after == before, "audit": audit}


def run_missing_committed_row_regression(args: Any, database: str) -> dict[str, Any]:
    prepare_fixture(args, database)
    history = apply_two_run_history(args, database)
    apply_seal(args, database)
    sealed_state(args, database)
    base.run_psql(
        args,
        database,
        sql="DELETE FROM public.import_runs WHERE id=(SELECT id FROM public.import_runs WHERE status='completed' AND transaction_outcome='committed' LIMIT 1);",
    )
    before = data_snapshot(args, database)
    result = base.run_psql(args, database, sql=base.apply_call_sql(), check=False, verbose_errors=True)
    combined = f"{result.stdout}\n{result.stderr}"
    if result.returncode == 0:
        raise AssertionError(f"Missing committed-row call unexpectedly succeeded: {combined}")
    if not re.search(r"SQL state:\s*42501|42501", combined) or "permission denied for table import_runs" not in combined.lower():
        raise AssertionError(f"Missing committed-row call did not fail closed at audit INSERT privilege: {combined}")
    after = data_snapshot(args, database)
    if after != before:
        raise AssertionError(f"Missing committed-row call changed disposable data: {before!r} -> {after!r}")
    audit = audit_snapshot(args, database)
    if audit["rows"] != 1 or audit["committed"] != 0 or audit["rolled_back"] != 1:
        raise AssertionError(f"Missing committed-row call inserted or changed audit evidence: {audit!r}")
    return {
        "history_before_delete": history["audit_before_seal"],
        "expected_error": "SQLSTATE 42501: permission denied for table import_runs",
        "no_new_audit_row": True,
        "data_unchanged": after == before,
        "audit_after": audit,
    }


def run_regression(args: Any) -> dict[str, Any]:
    suffix = uuid.uuid4().hex[:10]
    databases = {
        "sealed": f"relief_sealed_apply_{suffix}",
        "missing_marker": f"relief_missing_marker_{suffix}",
    }
    created: list[str] = []
    try:
        for database in databases.values():
            base.create_database(args, database)
            created.append(database)

        prepare_fixture(args, databases["sealed"])
        history = apply_two_run_history(args, databases["sealed"])
        before_seal = data_snapshot(args, databases["sealed"])
        audit_before_seal = audit_snapshot(args, databases["sealed"])
        apply_seal(args, databases["sealed"])
        state = sealed_state(args, databases["sealed"])
        after_seal = data_snapshot(args, databases["sealed"])
        audit_after_seal = audit_snapshot(args, databases["sealed"])
        if after_seal != before_seal or audit_after_seal != audit_before_seal:
            raise AssertionError("Sealing migration changed disposable Apply data or audit evidence")
        negative = direct_write_negative_tests(args, databases["sealed"])
        idempotency = owner_already_applied(args, databases["sealed"], history["committed"]["run_id"], before_seal)
        missing = run_missing_committed_row_regression(args, databases["missing_marker"])

        return {
            "migration": SEAL_MIGRATION.name,
            "history": history,
            "sealed_state": state,
            "successful_data_preserved": after_seal == before_seal,
            "successful_audit_preserved": audit_after_seal == audit_before_seal,
            "operator_invocation": negative["operator_invoke"],
            "direct_write_negative_tests": negative,
            "owner_already_applied": idempotency,
            "missing_committed_row_fail_closed": missing,
        }
    finally:
        for database in reversed(created):
            base.drop_database(args, database)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=55433)
    parser.add_argument("--user", default="postgres")
    parser.add_argument("--psql", default=shutil.which("psql") or "psql")
    args = parser.parse_args()
    try:
        result = run_regression(args)
    except Exception as error:
        print(f"ERROR: {error}", file=sys.stderr)
        return 1
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

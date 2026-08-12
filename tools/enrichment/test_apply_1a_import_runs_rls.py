#!/usr/bin/env python3
"""Disposable PostgreSQL regression test for the Apply 1A audit RLS gate.

The test deliberately proves both sides of the production incident:

* deployed Apply infrastructure plus RLS with no policies fails at the first
  ``import_runs`` INSERT with SQLSTATE 42501 and commits no data; and
* the forward policy migration permits exactly the bounded owner path,
  including committed-run visibility, idempotency, and durable rollback audit.

The script creates uniquely named disposable databases on a local PostgreSQL
17 endpoint and removes them in ``finally``. It never connects to Supabase.
"""

from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
import sys
import uuid
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
FIXTURE = ROOT / "tools/enrichment/disposable_apply_1a_fixture.sql"
SEED = ROOT / "tools/enrichment/disposable_apply_1a_seed.sql"
ROLES = ROOT / "supabase/roles.sql"
DEPLOYED_MIGRATION = ROOT / "supabase/migrations/20260811164202_apply_1a_audit_and_transaction.sql"
CORRECTIVE_MIGRATION = next(ROOT.glob("supabase/migrations/*_apply_1a_import_runs_rls.sql"))
POSTCHECK_FAULT = ROOT / "tools/enrichment/disposable_apply_1a_postcheck_fault.sql"

PROJECT_REF = "bgwxrxkmyaihplaloely"
PLAN_SHA = "7400626bc99061af7ba82c29969fc8929d7394c59afcfe574e1880521bad2b45"
MANIFEST_SHA = "1de1a71186b80ce043b48fc5f4d6c4bc6ed9d1c964b3ddf7ad3b96ddd073bfa0"
SOURCE_SHA = "f6824fdc7cd29df8c1f45ba749c1b28d319fb34803c55459bbe748ef65937624"
CONFIRMATION = "APPLY_RELIEF_TOILET_MAP_1A_48"


def psql_base(args: argparse.Namespace, database: str) -> list[str]:
    return [
        args.psql,
        "-X",
        "-w",
        "-h",
        args.host,
        "-p",
        str(args.port),
        "-U",
        args.user,
        "-d",
        database,
        "-v",
        "ON_ERROR_STOP=1",
        "-P",
        "pager=off",
        "-A",
        "-t",
    ]


def run_psql(
    args: argparse.Namespace,
    database: str,
    *,
    sql: str | None = None,
    file: Path | None = None,
    check: bool = True,
    verbose_errors: bool = False,
) -> subprocess.CompletedProcess[str]:
    command = psql_base(args, database)
    if verbose_errors:
        command.extend(["-v", "VERBOSITY=verbose"])
    if file is not None:
        command.extend(["-f", str(file)])
    else:
        command.extend(["-v", "ON_ERROR_STOP=1", "-c", sql or ""])
    result = subprocess.run(command, cwd=ROOT, text=True, capture_output=True, check=False)
    if check and result.returncode != 0:
        raise AssertionError(
            f"psql failed ({result.returncode}) for {database}:\n"
            f"STDOUT:\n{result.stdout}\nSTDERR:\n{result.stderr}"
        )
    return result


def scalar(args: argparse.Namespace, database: str, sql: str) -> str:
    result = run_psql(args, database, sql=sql)
    lines = [line.strip() for line in result.stdout.splitlines() if line.strip()]
    if not lines:
        raise AssertionError(f"Expected scalar output for SQL: {sql}")
    return lines[-1]


def json_scalar(args: argparse.Namespace, database: str, sql: str) -> dict[str, Any]:
    value = scalar(args, database, sql)
    try:
        parsed = json.loads(value)
    except json.JSONDecodeError as error:
        raise AssertionError(f"Expected JSON scalar for {database}, received {value!r}; SQL starts {sql.strip()[:120]!r}") from error
    if not isinstance(parsed, dict):
        raise AssertionError(f"Expected JSON object, received {parsed!r}")
    return parsed


def create_database(args: argparse.Namespace, name: str) -> None:
    run_psql(args, "postgres", sql=f'CREATE DATABASE "{name}"')


def drop_database(args: argparse.Namespace, name: str) -> None:
    run_psql(args, "postgres", sql=f'DROP DATABASE IF EXISTS "{name}" WITH (FORCE)')


def load_apply_fixture(args: argparse.Namespace, database: str) -> None:
    run_psql(args, database, file=FIXTURE)
    run_psql(args, database, file=ROLES)
    run_psql(args, database, file=DEPLOYED_MIGRATION)
    run_psql(args, database, file=SEED)
    run_psql(
        args,
        database,
        sql=(
            "DO $$ BEGIN "
            "IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname='service_role') THEN "
            "CREATE ROLE service_role NOLOGIN NOSUPERUSER NOCREATEDB NOCREATEROLE NOINHERIT; "
            "END IF; "
            "IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname='authenticator') THEN "
            "CREATE ROLE authenticator NOLOGIN NOSUPERUSER NOCREATEDB NOCREATEROLE NOINHERIT; "
            "END IF; END $$; "
            "ALTER TABLE public.import_runs ENABLE ROW LEVEL SECURITY;"
        ),
    )


def apply_corrective_migration(args: argparse.Namespace, database: str) -> None:
    run_psql(args, database, file=CORRECTIVE_MIGRATION)


def apply_call_sql() -> str:
    return f"""
SET ROLE relief_apply_owner;
SELECT private.apply_relief_toilet_map_1a(
  '{PROJECT_REF}', '{PLAN_SHA}', '{MANIFEST_SHA}', '{SOURCE_SHA}', '{CONFIRMATION}'
)::text;
"""


def apply_call(args: argparse.Namespace, database: str) -> dict[str, Any]:
    value = scalar(args, database, apply_call_sql())
    try:
        parsed = json.loads(value)
    except json.JSONDecodeError as error:
        raise AssertionError(f"Apply call did not return JSON for {database}: {value!r}") from error
    if not isinstance(parsed, dict):
        raise AssertionError(f"Apply call returned non-object JSON: {parsed!r}")
    return parsed


def snapshot(args: argparse.Namespace, database: str) -> dict[str, str]:
    return json_scalar(
        args,
        database,
        """
SELECT json_build_object(
  'facility_count', (SELECT count(*)::text FROM public.facilities),
  'source_count', (SELECT count(*)::text FROM public.facility_sources),
  'source_digest', (SELECT md5(coalesce((SELECT jsonb_agg(to_jsonb(s) ORDER BY s.id)::text FROM public.facility_sources s), '[]'))),
  'publication_digest', (SELECT md5(coalesce((SELECT jsonb_agg(jsonb_build_object('id', f.id, 'publication_status', f.publication_status) ORDER BY f.id)::text FROM public.facilities f WHERE f.id IN (SELECT DISTINCT facility_id FROM private.relief_apply_1a_approved_operations)), '[]')))
);
""",
    )


def verify_success_state(args: argparse.Namespace, database: str, before: dict[str, str]) -> dict[str, str]:
    after = snapshot(args, database)
    state = json_scalar(
        args,
        database,
        """
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
  JOIN public.facilities f ON f.id = o.facility_id
), provenance_check AS (
  SELECT count(*) FILTER (
    WHERE provenance ->> 'source' = 'Toilet Map UK'
      AND provenance ->> 'source_name' = 'Toilet Map UK'
      AND provenance ->> 'basis' = 'EXACT_SOURCE_ID'
      AND provenance ->> 'confidence' = 'HIGH'
      AND provenance ->> 'source_snapshot_checksum' = 'f6824fdc7cd29df8c1f45ba749c1b28d319fb34803c55459bbe748ef65937624'
      AND provenance ->> 'approved_plan_sha256' = '7400626bc99061af7ba82c29969fc8929d7394c59afcfe574e1880521bad2b45'
      AND provenance ->> 'approved_manifest_sha256' = '1de1a71186b80ce043b48fc5f4d6c4bc6ed9d1c964b3ddf7ad3b96ddd073bfa0'
      AND provenance ->> 'apply_engine_version' = 'relief.apply-engine-1a.v1'
      AND provenance -> 'previous_value' = 'null'::jsonb
  ) AS matching
  FROM operation_state
)
SELECT json_build_object(
  'apply_audit_rows', (SELECT count(*)::text FROM public.import_runs WHERE run_kind = 'apply_1a'),
  'target_correct', (SELECT count(*)::text FROM operation_state WHERE actual_value = proposed_value),
  'target_still_null', (SELECT count(*)::text FROM operation_state WHERE actual_value IS NULL),
  'provenance_matches', (SELECT matching::text FROM provenance_check),
  'source_count', (SELECT count(*)::text FROM public.facility_sources),
  'facility_count', (SELECT count(*)::text FROM public.facilities),
  'audit_status', (SELECT status FROM public.import_runs WHERE run_kind = 'apply_1a' LIMIT 1),
  'audit_outcome', (SELECT transaction_outcome FROM public.import_runs WHERE run_kind = 'apply_1a' LIMIT 1),
  'audit_rows_updated', (SELECT rows_updated::text FROM public.import_runs WHERE run_kind = 'apply_1a' LIMIT 1)
);
""",
    )
    expected = {
        "apply_audit_rows": "1",
        "target_correct": "48",
        "target_still_null": "0",
        "provenance_matches": "48",
        "source_count": before["source_count"],
        "facility_count": before["facility_count"],
        "audit_status": "completed",
        "audit_outcome": "committed",
        "audit_rows_updated": "48",
    }
    if state != expected:
        raise AssertionError(f"Unexpected corrected success state: {state!r}, expected {expected!r}")
    if after["source_digest"] != before["source_digest"]:
        raise AssertionError("Source-link digest changed during disposable Apply")
    if after["publication_digest"] != before["publication_digest"]:
        raise AssertionError("Publication-status digest changed during disposable Apply")
    return after


def verify_policies_and_access(args: argparse.Namespace, database: str) -> dict[str, Any]:
    result = json_scalar(
        args,
        database,
        """
SELECT json_build_object(
  'rls_enabled', (SELECT relrowsecurity FROM pg_catalog.pg_class c JOIN pg_catalog.pg_namespace n ON n.oid = c.relnamespace WHERE n.nspname='public' AND c.relname='import_runs'),
  'force_rls', (SELECT relforcerowsecurity FROM pg_catalog.pg_class c JOIN pg_catalog.pg_namespace n ON n.oid = c.relnamespace WHERE n.nspname='public' AND c.relname='import_runs'),
  'policy_count', (SELECT count(*)::text FROM pg_catalog.pg_policies WHERE schemaname='public' AND tablename='import_runs'),
  'policy_roles', (SELECT coalesce(json_agg(DISTINCT role_name ORDER BY role_name), '[]'::json) FROM pg_catalog.pg_policies p CROSS JOIN LATERAL unnest(p.roles) AS roles(role_name) WHERE p.schemaname='public' AND p.tablename='import_runs'),
  'table_insert', pg_catalog.has_table_privilege('relief_apply_owner','public.import_runs','INSERT'),
  'table_update', pg_catalog.has_table_privilege('relief_apply_owner','public.import_runs','UPDATE'),
  'column_insert', (SELECT bool_and(pg_catalog.has_column_privilege('relief_apply_owner','public.import_runs', column_name, 'INSERT')) FROM (VALUES ('source_name'),('source_file_name'),('source_checksum'),('status'),('started_at'),('rows_received'),('rows_valid'),('run_kind'),('approved_plan_sha256'),('approved_manifest_sha256'),('approved_review_commit'),('apply_engine_version'),('project_ref'),('requested_operation_count'),('ready_count'),('applied_count'),('stale_count'),('failed_count'),('transaction_outcome'),('rollback_summary')) AS columns(column_name)),
  'column_update', (SELECT bool_and(pg_catalog.has_column_privilege('relief_apply_owner','public.import_runs', column_name, 'UPDATE')) FROM (VALUES ('status'),('completed_at'),('rows_updated'),('ready_count'),('applied_count'),('stale_count'),('failed_count'),('transaction_outcome'),('error_summary'),('rollback_summary')) AS columns(column_name)),
  'anon_policy', (SELECT count(*)::text FROM pg_catalog.pg_policies p CROSS JOIN LATERAL unnest(p.roles) AS roles(role_name) WHERE p.schemaname='public' AND p.tablename='import_runs' AND role_name IN ('anon','authenticated','service_role','authenticator')),
  'owner_login', (SELECT rolcanlogin FROM pg_catalog.pg_roles WHERE rolname='relief_apply_owner'),
  'operator_login', (SELECT rolcanlogin FROM pg_catalog.pg_roles WHERE rolname='relief_apply_operator'),
  'owner_execute', pg_catalog.has_function_privilege('relief_apply_owner','private.apply_relief_toilet_map_1a(text,text,text,text,text)','EXECUTE'),
  'operator_execute', pg_catalog.has_function_privilege('relief_apply_operator','private.apply_relief_toilet_map_1a(text,text,text,text,text)','EXECUTE'),
  'public_execute', pg_catalog.has_function_privilege('public','private.apply_relief_toilet_map_1a(text,text,text,text,text)','EXECUTE'),
  'anon_execute', pg_catalog.has_function_privilege('anon','private.apply_relief_toilet_map_1a(text,text,text,text,text)','EXECUTE'),
  'authenticated_execute', pg_catalog.has_function_privilege('authenticated','private.apply_relief_toilet_map_1a(text,text,text,text,text)','EXECUTE'),
  'service_role_execute', pg_catalog.has_function_privilege('service_role','private.apply_relief_toilet_map_1a(text,text,text,text,text)','EXECUTE'),
  'authenticator_execute', pg_catalog.has_function_privilege('authenticator','private.apply_relief_toilet_map_1a(text,text,text,text,text)','EXECUTE')
);
""",
    )
    expected = {
        "rls_enabled": True,
        "force_rls": False,
        "policy_count": "3",
        "policy_roles": ["relief_apply_owner"],
        "table_insert": False,
        "table_update": False,
        "column_insert": True,
        "column_update": True,
        "anon_policy": "0",
        "owner_login": False,
        "operator_login": False,
        "owner_execute": True,
        "operator_execute": True,
        "public_execute": False,
        "anon_execute": False,
        "authenticated_execute": False,
        "service_role_execute": False,
        "authenticator_execute": False,
    }
    if result != expected:
        raise AssertionError(f"Unexpected policy/access state: {result!r}, expected {expected!r}")
    for role in ("anon", "authenticated", "service_role", "authenticator", "relief_apply_operator"):
        denied = run_psql(
            args,
            database,
            sql=f"SET ROLE {role}; SELECT count(*) FROM public.import_runs;",
            check=False,
        )
        if denied.returncode == 0:
            raise AssertionError(f"Application-facing/direct role {role} unexpectedly read import_runs")
    return result


def verify_rollback_state(args: argparse.Namespace, database: str, before: dict[str, str]) -> dict[str, str]:
    state = json_scalar(
        args,
        database,
        """
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
  JOIN public.facilities f ON f.id = o.facility_id
)
SELECT json_build_object(
  'audit_rows', (SELECT count(*)::text FROM public.import_runs WHERE run_kind='apply_1a'),
  'status', (SELECT status FROM public.import_runs WHERE run_kind='apply_1a' LIMIT 1),
  'outcome', (SELECT transaction_outcome FROM public.import_runs WHERE run_kind='apply_1a' LIMIT 1),
  'applied_count', (SELECT applied_count::text FROM public.import_runs WHERE run_kind='apply_1a' LIMIT 1),
  'rows_updated', (SELECT rows_updated::text FROM public.import_runs WHERE run_kind='apply_1a' LIMIT 1),
  'failed_count', (SELECT failed_count::text FROM public.import_runs WHERE run_kind='apply_1a' LIMIT 1),
  'target_null', (SELECT count(*)::text FROM operation_state WHERE actual_value IS NULL),
  'apply_run_id_present', (SELECT count(*)::text FROM operation_state WHERE provenance ->> 'apply_run_id' IS NOT NULL)
);
""",
    )
    expected = {
        "audit_rows": "1",
        "status": "failed",
        "outcome": "rolled_back",
        "applied_count": "0",
        "rows_updated": "0",
        "failed_count": "1",
        "target_null": "48",
        "apply_run_id_present": "0",
    }
    if state != expected:
        raise AssertionError(f"Unexpected rollback state: {state!r}, expected {expected!r}")
    after = snapshot(args, database)
    if after != before:
        raise AssertionError(f"Rollback changed disposable data snapshot: before={before!r}, after={after!r}")
    return state


def run_regression(args: argparse.Namespace) -> dict[str, Any]:
    suffix = uuid.uuid4().hex[:12]
    success_db = f"relief_apply_1a_rls_{suffix}"
    rollback_db = f"relief_apply_1a_rb_{suffix}"
    created: list[str] = []
    try:
        for database in (success_db, rollback_db):
            create_database(args, database)
            created.append(database)

        load_apply_fixture(args, success_db)
        old_before = snapshot(args, success_db)
        old_state = run_psql(args, success_db, sql=apply_call_sql(), check=False, verbose_errors=True)
        old_error = f"{old_state.stdout}\n{old_state.stderr}"
        if old_state.returncode == 0 or not re.search(r"42501|row-level security policy", old_error, re.IGNORECASE):
            raise AssertionError(f"Old-state regression did not reproduce SQLSTATE 42501:\n{old_error}")
        old_counts = json_scalar(
            args,
            success_db,
            """
SELECT json_build_object(
  'apply_audit_rows', (SELECT count(*)::text FROM public.import_runs WHERE run_kind='apply_1a'),
  'target_null', (SELECT count(*)::text FROM private.relief_apply_1a_approved_operations o JOIN public.facilities f ON f.id=o.facility_id WHERE CASE o.field WHEN 'has_baby_changing' THEN f.has_baby_changing WHEN 'requires_radar_key' THEN f.requires_radar_key WHEN 'is_gender_neutral' THEN f.is_gender_neutral WHEN 'is_accessible' THEN f.is_accessible WHEN 'is_free' THEN f.is_free END IS NULL),
  'apply_run_id_present', (SELECT count(*)::text FROM private.relief_apply_1a_approved_operations o JOIN public.facilities f ON f.id=o.facility_id WHERE f.field_provenance -> o.field ->> 'apply_run_id' IS NOT NULL)
);
""",
        )
        if old_counts != {"apply_audit_rows": "0", "target_null": "48", "apply_run_id_present": "0"}:
            raise AssertionError(f"Old-state regression mutated disposable data: {old_counts!r}")
        old_after = snapshot(args, success_db)
        if old_after != old_before:
            raise AssertionError(f"Old-state failure changed disposable snapshot: before={old_before!r}, after={old_after!r}")

        apply_corrective_migration(args, success_db)
        policy_state = verify_policies_and_access(args, success_db)
        before = snapshot(args, success_db)
        first = apply_call(args, success_db)
        expected_first = {"status": "COMMITTED", "requested_operation_count": 48, "ready_count": 48, "applied_count": 48, "stale_count": 0, "failed_count": 0, "mutations_committed": True}
        if {key: first.get(key) for key in expected_first} != expected_first:
            raise AssertionError(f"Unexpected corrected first call: {first!r}")
        after = verify_success_state(args, success_db, before)
        second = apply_call(args, success_db)
        if second.get("status") != "ALREADY_APPLIED" or second.get("applied_count") != 0 or second.get("run_id") != first.get("run_id"):
            raise AssertionError(f"Disposable idempotency regression failed: first={first!r}, second={second!r}")

        load_apply_fixture(args, rollback_db)
        apply_corrective_migration(args, rollback_db)
        rollback_before = snapshot(args, rollback_db)
        run_psql(args, rollback_db, file=POSTCHECK_FAULT)
        rollback_call = apply_call(args, rollback_db)
        if rollback_call.get("status") != "ROLLED_BACK" or rollback_call.get("mutations_committed") is not False:
            raise AssertionError(f"Unexpected rollback call result: {rollback_call!r}")
        rollback_state = verify_rollback_state(args, rollback_db, rollback_before)

        return {
            "corrective_migration": CORRECTIVE_MIGRATION.name,
            "old_state_sqlstate": "42501",
            "old_state_audit_rows": old_counts["apply_audit_rows"],
            "first_call": first,
            "second_call": second,
            "rollback_call": rollback_call,
            "rollback_audit": rollback_state,
            "policy_state": policy_state,
            "source_digest_unchanged": after["source_digest"] == before["source_digest"],
            "publication_digest_unchanged": after["publication_digest"] == before["publication_digest"],
            "databases": [success_db, rollback_db],
        }
    finally:
        for database in reversed(created):
            drop_database(args, database)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=55433)
    parser.add_argument("--user", default="postgres")
    parser.add_argument("--psql", default=shutil.which("psql") or "psql")
    args = parser.parse_args()
    if not CORRECTIVE_MIGRATION.exists():
        raise SystemExit("Corrective migration not found")
    try:
        result = run_regression(args)
    except Exception as error:
        print(f"ERROR: {error}", file=sys.stderr)
        return 1
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

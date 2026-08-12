#!/usr/bin/env python3
"""Disposable PostgreSQL 17 regression test for the facilities UPDATE policy.

This suite recreates the deployed facilities-RLS failure, applies only the new
forward facilities policy in disposable databases, and proves the bounded
owner path, rollback, idempotency, concurrency, and negative security cases.
It never connects to Supabase production.
"""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
import time
import uuid
from pathlib import Path
from typing import Any

try:
    from . import test_apply_1a_import_runs_rls as base
except ImportError:
    import test_apply_1a_import_runs_rls as base


ROOT = Path(__file__).resolve().parents[2]
FACILITIES_MIGRATION = next(ROOT.glob("supabase/migrations/*_apply_1a_facilities_update_rls.sql"))
PROJECT_REF = base.PROJECT_REF
PLAN_SHA = base.PLAN_SHA
MANIFEST_SHA = base.MANIFEST_SHA
SOURCE_SHA = base.SOURCE_SHA
REVIEW_COMMIT = "4710b9ec7a9f5a83aa9e7225400b8a6046ce0e77"
ENGINE_VERSION = "relief.apply-engine-1a.v1"
EXPECTED_DISTRIBUTION = {
    "has_baby_changing": 16,
    "requires_radar_key": 14,
    "is_gender_neutral": 15,
    "is_accessible": 2,
    "is_free": 1,
}
ADVISORY_SQL = (
    "SELECT pg_catalog.pg_advisory_xact_lock("
    "pg_catalog.hashtextextended("
    f"'relief.apply.1a:{MANIFEST_SHA}', 0))"
)


def scalar_json(args: argparse.Namespace, database: str, sql: str) -> Any:
    value = base.scalar(args, database, sql)
    try:
        return json.loads(value)
    except json.JSONDecodeError as error:
        raise AssertionError(f"Expected JSON output, received {value!r}") from error


def prepare_fixture(args: argparse.Namespace, database: str) -> None:
    base.load_apply_fixture(args, database)
    base.apply_corrective_migration(args, database)
    base.run_psql(
        args,
        database,
        sql=f"""
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


def apply_facilities_migration(args: argparse.Namespace, database: str) -> None:
    base.run_psql(args, database, file=FACILITIES_MIGRATION)


def apply_json(args: argparse.Namespace, database: str) -> dict[str, Any]:
    return base.apply_call(args, database)


def old_state_failure(args: argparse.Namespace, database: str) -> dict[str, Any]:
    before = base.snapshot(args, database)
    result = base.run_psql(args, database, sql=base.apply_call_sql(), verbose_errors=True)
    if result.returncode != 0:
        raise AssertionError(f"Old facilities-RLS call unexpectedly failed at SQL client level:\n{result.stderr}")
    outcome = json.loads([line.strip() for line in result.stdout.splitlines() if line.strip()][-1])
    expected = {
        "status": "ROLLED_BACK",
        "ready_count": 0,
        "applied_count": 0,
        "failed_count": 1,
        "mutations_committed": False,
    }
    if {key: outcome.get(key) for key in expected} != expected:
        raise AssertionError(f"Unexpected old-state facilities failure: {outcome!r}")
    audit = scalar_json(
        args,
        database,
        """
SELECT json_build_object(
  'rows', count(*),
  'failed', count(*) FILTER (WHERE status='failed'),
  'rolled_back', count(*) FILTER (WHERE transaction_outcome='rolled_back'),
  'rows_updated_zero', count(*) FILTER (WHERE rows_updated=0),
  'applied_zero', count(*) FILTER (WHERE applied_count=0),
  'rollback_summary_present', count(*) FILTER (WHERE rollback_summary IS NOT NULL)
)
FROM public.import_runs
WHERE run_kind='apply_1a';
""",
    )
    expected_audit = {
        "rows": 1,
        "failed": 1,
        "rolled_back": 1,
        "rows_updated_zero": 1,
        "applied_zero": 1,
        "rollback_summary_present": 1,
    }
    if audit != expected_audit:
        raise AssertionError(f"Unexpected old-state durable audit: {audit!r}")
    after = base.snapshot(args, database)
    if after != before:
        raise AssertionError(f"Old-state facilities failure mutated disposable data: {before!r} -> {after!r}")
    return {"call": outcome, "audit": audit, "snapshot_unchanged": after == before}


def facility_policies(args: argparse.Namespace, database: str) -> list[dict[str, Any]]:
    return scalar_json(
        args,
        database,
        """
SELECT coalesce(json_agg(row_to_json(p) ORDER BY p.policyname), '[]'::json)
FROM pg_catalog.pg_policies AS p
WHERE p.schemaname='public' AND p.tablename='facilities';
""",
    )


def access_state(args: argparse.Namespace, database: str) -> dict[str, Any]:
    result = scalar_json(
        args,
        database,
        """
SELECT json_build_object(
  'table_select', has_table_privilege('relief_apply_owner','public.facilities','SELECT'),
  'table_update', has_table_privilege('relief_apply_owner','public.facilities','UPDATE'),
  'column_update', (
    SELECT json_object_agg(column_name, has_column_privilege('relief_apply_owner','public.facilities',column_name,'UPDATE') ORDER BY column_name)
    FROM (VALUES
      ('has_baby_changing'),('requires_radar_key'),('is_gender_neutral'),
      ('is_accessible'),('is_free'),('field_provenance'),('publication_status')
    ) AS columns(column_name)
  ),
  'application_update_policies', (
    SELECT count(*)::text
    FROM pg_catalog.pg_policies AS p
    CROSS JOIN LATERAL unnest(p.roles) AS roles(role_name)
    WHERE p.schemaname='public' AND p.tablename='facilities'
      AND p.cmd='UPDATE'
      AND role_name IN ('public','anon','authenticated','service_role','authenticator','relief_apply_operator')
  ),
  'owner_execute', has_function_privilege('relief_apply_owner','private.apply_relief_toilet_map_1a(text,text,text,text,text)','EXECUTE'),
  'operator_execute', has_function_privilege('relief_apply_operator','private.apply_relief_toilet_map_1a(text,text,text,text,text)','EXECUTE'),
  'public_execute', has_function_privilege('public','private.apply_relief_toilet_map_1a(text,text,text,text,text)','EXECUTE'),
  'anon_execute', has_function_privilege('anon','private.apply_relief_toilet_map_1a(text,text,text,text,text)','EXECUTE'),
  'authenticated_execute', has_function_privilege('authenticated','private.apply_relief_toilet_map_1a(text,text,text,text,text)','EXECUTE'),
  'service_role_execute', has_function_privilege('service_role','private.apply_relief_toilet_map_1a(text,text,text,text,text)','EXECUTE'),
  'authenticator_execute', has_function_privilege('authenticator','private.apply_relief_toilet_map_1a(text,text,text,text,text)','EXECUTE')
);
""",
    )
    expected_columns = {
        "field_provenance": True,
        "has_baby_changing": True,
        "is_accessible": True,
        "is_free": True,
        "is_gender_neutral": True,
        "publication_status": False,
        "requires_radar_key": True,
    }
    if result != {
        "table_select": True,
        "table_update": False,
        "column_update": expected_columns,
        "application_update_policies": "0",
        "owner_execute": True,
        "operator_execute": True,
        "public_execute": False,
        "anon_execute": False,
        "authenticated_execute": False,
        "service_role_execute": False,
        "authenticator_execute": False,
    }:
        raise AssertionError(f"Facilities privilege or execute boundary changed: {result!r}")
    return result


def lock_count(args: argparse.Namespace, database: str, mode: str) -> int:
    if mode == "update":
        sql = f"""
SET ROLE relief_apply_owner;
WITH target_ids AS (
  SELECT DISTINCT facility_id FROM private.relief_apply_1a_approved_operations
), lockable AS MATERIALIZED (
  SELECT f.id
  FROM public.facilities AS f
  JOIN target_ids AS t ON t.facility_id=f.id
  FOR UPDATE
)
SELECT count(*) FROM lockable;
"""
    elif mode == "share":
        sql = """
SET ROLE relief_apply_owner;
WITH lockable AS MATERIALIZED (
  SELECT f.id FROM public.facilities AS f FOR SHARE
)
SELECT count(*) FROM lockable;
"""
    else:
        raise ValueError(mode)
    return int(base.scalar(args, database, sql))


def visible_target_count(args: argparse.Namespace, database: str) -> int:
    return int(
        base.scalar(
            args,
            database,
            """
SET ROLE relief_apply_owner;
WITH target_ids AS (
  SELECT DISTINCT facility_id FROM private.relief_apply_1a_approved_operations
)
SELECT count(*)
FROM public.facilities AS f
JOIN target_ids AS t ON t.facility_id=f.id;
""",
        )
    )


def policy_state(args: argparse.Namespace, database: str) -> dict[str, Any]:
    policies = facility_policies(args, database)
    update = [policy for policy in policies if policy["cmd"] == "UPDATE"]
    if len(update) != 1:
        raise AssertionError(f"Expected exactly one facilities UPDATE policy, found {update!r}")
    policy = update[0]
    expected_fragments = [
        "publication_status = 'published'::text",
        "EXISTS",
        "private.relief_apply_1a_approved_operations",
        "r.facility_id = facilities.id",
        PROJECT_REF,
        PLAN_SHA,
        MANIFEST_SHA,
        REVIEW_COMMIT,
        ENGINE_VERSION,
        SOURCE_SHA,
    ]
    # pg_policies normalizes the target-table qualification to the table name
    # in PostgreSQL 17; registry references remain schema-qualified.
    for expression in (policy["qual"], policy["with_check"]):
        if not expression or any(fragment not in expression for fragment in expected_fragments):
            raise AssertionError(f"Facilities policy expression is not the frozen bounded predicate: {expression!r}")
    if policy["qual"] != policy["with_check"]:
        raise AssertionError("Facilities USING and WITH CHECK predicates differ")
    if policy["roles"] != ["relief_apply_owner"] or policy["cmd"] != "UPDATE":
        raise AssertionError(f"Facilities policy role/command changed: {policy!r}")
    return {
        "policy_count": len(update),
        "policy_name": policy["policyname"],
        "role": policy["roles"],
        "command": policy["cmd"],
        "using": policy["qual"],
        "with_check": policy["with_check"],
        "all_policies": policies,
    }


def frozen_registry_state(args: argparse.Namespace, database: str) -> dict[str, Any]:
    state = scalar_json(
        args,
        database,
        f"""
SELECT json_build_object(
  'operations', count(*),
  'distinct_targets', count(DISTINCT facility_id),
  'identity_mismatches', count(*) FILTER (WHERE
    project_ref <> '{PROJECT_REF}'
    OR approved_plan_sha256 <> '{PLAN_SHA}'
    OR approved_manifest_sha256 <> '{MANIFEST_SHA}'
    OR approved_review_commit <> '{REVIEW_COMMIT}'
    OR apply_engine_version <> '{ENGINE_VERSION}'
    OR source_checksum <> '{SOURCE_SHA}'
  ),
  'distribution', (
    SELECT coalesce(json_object_agg(field, operation_count), '{{}}'::json)
    FROM (
      SELECT field, count(*)::integer AS operation_count
      FROM private.relief_apply_1a_approved_operations
      GROUP BY field
    ) AS distribution
  )
)
FROM private.relief_apply_1a_approved_operations;
""",
    )
    state["distribution"] = {key: int(value) for key, value in state["distribution"].items()}
    expected = {"operations": 48, "distinct_targets": 25, "identity_mismatches": 0, "distribution": EXPECTED_DISTRIBUTION}
    if state != expected:
        raise AssertionError(f"Frozen disposable registry identity changed: {state!r}")
    return state


def source_publication_state(args: argparse.Namespace, database: str) -> dict[str, Any]:
    state = scalar_json(
        args,
        database,
        """
WITH operation_links AS (
  SELECT o.operation_id, o.facility_id, o.source_name, o.source_record_id, o.source_updated_at,
         f.publication_status,
         count(fs.id) AS link_count,
         count(fs.id) FILTER (WHERE fs.facility_id=o.facility_id AND fs.source_name=o.source_name AND fs.source_record_id=o.source_record_id AND fs.is_current IS TRUE AND fs.source_updated_at=o.source_updated_at) AS exact_count
  FROM private.relief_apply_1a_approved_operations AS o
  JOIN public.facilities AS f ON f.id=o.facility_id
  LEFT JOIN public.facility_sources AS fs ON fs.facility_id=o.facility_id AND fs.source_name=o.source_name AND fs.source_record_id=o.source_record_id
  GROUP BY o.operation_id,o.facility_id,o.source_name,o.source_record_id,o.source_updated_at,f.publication_status
)
SELECT json_build_object(
  'operations', count(*),
  'bad_multiplicity', count(*) FILTER (WHERE link_count <> 1 OR exact_count <> 1),
  'non_current', count(*) FILTER (WHERE exact_count=0),
  'publication_differences', count(*) FILTER (WHERE publication_status <> 'published'),
  'facility_source_rows', (SELECT count(*) FROM public.facility_sources)
)
FROM operation_links;
""",
    )
    expected = {
        "operations": 48,
        "bad_multiplicity": 0,
        "non_current": 0,
        "publication_differences": 0,
        "facility_source_rows": 25,
    }
    if state != expected:
        raise AssertionError(f"Source-link/publication state changed: {state!r}")
    return state


def negative_security(args: argparse.Namespace, database: str) -> dict[str, Any]:
    nonapproved_id = "00000000-0000-0000-0000-000000000002"
    result = base.run_psql(
        args,
        database,
        sql=f"""
BEGIN;
SET ROLE relief_apply_owner;
UPDATE public.facilities SET is_free=false WHERE id='{nonapproved_id}'::uuid;
ROLLBACK;
""",
    )
    if "UPDATE 0" not in result.stdout:
        raise AssertionError(f"Non-approved published facility was update-eligible: {result.stdout!r}")
    result = {
        "nonapproved_for_update": lock_count_for_id(args, database, nonapproved_id),
        "nonapproved_update_output": "UPDATE 0",
    }
    if result["nonapproved_for_update"] != 0:
        raise AssertionError(f"Non-approved facility was lockable: {result!r}")
    access_state(args, database)
    return result


def lock_count_for_id(args: argparse.Namespace, database: str, facility_id: str) -> int:
    return int(
        base.scalar(
            args,
            database,
            f"""
SET ROLE relief_apply_owner;
WITH lockable AS MATERIALIZED (
  SELECT f.id FROM public.facilities AS f WHERE f.id='{facility_id}'::uuid FOR UPDATE
)
SELECT count(*) FROM lockable;
""",
        )
    )


def apply_process(args: argparse.Namespace, database: str) -> subprocess.Popen[str]:
    command = base.psql_base(args, database)
    command.extend(["-c", base.apply_call_sql()])
    return subprocess.Popen(command, cwd=ROOT, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)


def sql_process(args: argparse.Namespace, database: str, sql: str) -> subprocess.Popen[str]:
    command = base.psql_base(args, database)
    command.extend(["-c", sql])
    return subprocess.Popen(command, cwd=ROOT, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)


def process_json(process: subprocess.Popen[str], timeout: float = 90) -> dict[str, Any]:
    stdout, stderr = process.communicate(timeout=timeout)
    if process.returncode != 0:
        raise AssertionError(f"Concurrent psql failed ({process.returncode}):\n{stdout}\n{stderr}")
    lines = [line.strip() for line in stdout.splitlines() if line.strip()]
    if not lines:
        raise AssertionError(f"Concurrent psql returned no result: {stderr}")
    try:
        return json.loads(lines[-1])
    except json.JSONDecodeError as error:
        raise AssertionError(f"Concurrent Apply returned non-JSON: {stdout}\n{stderr}") from error


def concurrency_regression(args: argparse.Namespace, database: str, lock_database: str) -> dict[str, Any]:
    # Hold the exact Apply advisory lock so both calls are guaranteed to queue.
    advisory_holder = sql_process(
        args,
        database,
        f"BEGIN; {ADVISORY_SQL}; SELECT pg_sleep(3); ROLLBACK;",
    )
    time.sleep(0.5)
    first_process = apply_process(args, database)
    second_process = apply_process(args, database)
    first = process_json(first_process)
    second = process_json(second_process)
    advisory_holder.communicate(timeout=30)
    statuses = sorted([first.get("status"), second.get("status")])
    if statuses != ["ALREADY_APPLIED", "COMMITTED"]:
        raise AssertionError(f"Concurrent Apply calls did not serialize: {first!r}, {second!r}")
    committed = first if first.get("status") == "COMMITTED" else second
    already = first if first.get("status") == "ALREADY_APPLIED" else second
    if already.get("run_id") != committed.get("run_id") or already.get("applied_count") != 0:
        raise AssertionError(f"Concurrent idempotency result was not the committed run: {first!r}, {second!r}")
    audit_rows = int(base.scalar(args, database, "SELECT count(*) FROM public.import_runs WHERE run_kind='apply_1a' AND status='completed' AND transaction_outcome='committed';"))
    if audit_rows != 1:
        raise AssertionError(f"Concurrent calls created {audit_rows} committed audit rows")

    target_holder = sql_process(
        args,
        lock_database,
        """
BEGIN;
SET ROLE relief_apply_owner;
SELECT f.id
FROM public.facilities AS f
WHERE f.id = (
  SELECT facility_id
  FROM private.relief_apply_1a_approved_operations
  ORDER BY facility_id
  LIMIT 1
)
FOR UPDATE;
SELECT pg_sleep(3);
ROLLBACK;
""",
    )
    time.sleep(0.5)
    if target_holder.poll() is not None:
        stdout, stderr = target_holder.communicate(timeout=5)
        raise AssertionError(f"Target lock holder did not acquire its disposable row lock: {stdout}\n{stderr}")
    started = time.monotonic()
    target_process = apply_process(args, lock_database)
    target_result = process_json(target_process, timeout=90)
    elapsed = time.monotonic() - started
    target_holder.communicate(timeout=30)
    if target_result.get("status") != "COMMITTED" or elapsed < 1.5:
        raise AssertionError(f"Target row lock did not serialize the Apply validation/update sequence: result={target_result!r}, elapsed={elapsed:.3f}")
    return {
        "advisory_serialization": True,
        "first": first,
        "second": second,
        "committed_audit_rows": audit_rows,
        "target_row_lock_serialized": True,
        "target_lock_wait_seconds": round(elapsed, 3),
        "target_lock_result": target_result,
        "unrelated_facilities_locked": False,
    }


def run_regression(args: argparse.Namespace) -> dict[str, Any]:
    suffix = uuid.uuid4().hex[:10]
    databases = {
        "old": f"relief_old_fac_{suffix}",
        "success": f"relief_success_fac_{suffix}",
        "rollback": f"relief_rollback_fac_{suffix}",
        "concurrency": f"relief_concurrency_fac_{suffix}",
        "target_lock": f"relief_target_lock_fac_{suffix}",
    }
    created: list[str] = []
    try:
        for database in databases.values():
            base.create_database(args, database)
            created.append(database)

        prepare_fixture(args, databases["old"])
        old_visible = visible_target_count(args, databases["old"])
        if old_visible != 25:
            raise AssertionError(f"Old-state disposable ordinary SELECT did not expose 25 approved facilities: {old_visible}")
        old = old_state_failure(args, databases["old"])
        old["ordinary_select_approved"] = old_visible

        prepare_fixture(args, databases["success"])
        registry = frozen_registry_state(args, databases["success"])
        apply_facilities_migration(args, databases["success"])
        policy = policy_state(args, databases["success"])
        access = access_state(args, databases["success"])
        approved_for_update = lock_count(args, databases["success"], "update")
        nonapproved_for_update = lock_count_for_id(args, databases["success"], "00000000-0000-0000-0000-000000000002")
        initial_for_share = lock_count(args, databases["success"], "share")
        if approved_for_update != 25 or nonapproved_for_update != 0 or initial_for_share != 25:
            raise AssertionError(f"Unexpected corrected lock boundary: approved={approved_for_update}, nonapproved={nonapproved_for_update}, share={initial_for_share}")
        before = base.snapshot(args, databases["success"])
        first = apply_json(args, databases["success"])
        expected_first = {
            "status": "COMMITTED",
            "requested_operation_count": 48,
            "ready_count": 48,
            "applied_count": 48,
            "stale_count": 0,
            "failed_count": 0,
            "mutations_committed": True,
        }
        if {key: first.get(key) for key in expected_first} != expected_first:
            raise AssertionError(f"Corrected Apply did not commit exactly 48 operations: {first!r}")
        after = base.verify_success_state(args, databases["success"], before)
        source_publication = source_publication_state(args, databases["success"])
        second = apply_json(args, databases["success"])
        if second.get("status") != "ALREADY_APPLIED" or second.get("applied_count") != 0 or second.get("run_id") != first.get("run_id"):
            raise AssertionError(f"Corrected Apply was not idempotent: first={first!r}, second={second!r}")
        committed_rows = int(base.scalar(args, databases["success"], "SELECT count(*) FROM public.import_runs WHERE run_kind='apply_1a' AND status='completed' AND transaction_outcome='committed';"))
        if committed_rows != 1:
            raise AssertionError(f"Idempotent retry created an unexpected committed-row count: {committed_rows}")
        security = negative_security(args, databases["success"])

        prepare_fixture(args, databases["rollback"])
        apply_facilities_migration(args, databases["rollback"])
        rollback_before = base.snapshot(args, databases["rollback"])
        base.run_psql(args, databases["rollback"], file=base.POSTCHECK_FAULT)
        rollback = apply_json(args, databases["rollback"])
        if rollback.get("status") != "ROLLED_BACK" or rollback.get("mutations_committed") is not False:
            raise AssertionError(f"Controlled rollback returned an unexpected result: {rollback!r}")
        rollback_audit = base.verify_rollback_state(args, databases["rollback"], rollback_before)

        prepare_fixture(args, databases["concurrency"])
        apply_facilities_migration(args, databases["concurrency"])
        prepare_fixture(args, databases["target_lock"])
        apply_facilities_migration(args, databases["target_lock"])
        concurrency = concurrency_regression(args, databases["concurrency"], databases["target_lock"])

        return {
            "migration": FACILITIES_MIGRATION.name,
            "old_state": old,
            "registry": registry,
            "policy": policy,
            "access": access,
            "approved_for_update": approved_for_update,
            "nonapproved_for_update": nonapproved_for_update,
            "initial_for_share": initial_for_share,
            "first": first,
            "after": after,
            "second": second,
            "committed_rows_after_idempotency": committed_rows,
            "source_publication": source_publication,
            "source_digest_unchanged": before["source_digest"] == after["source_digest"],
            "publication_digest_unchanged": before["publication_digest"] == after["publication_digest"],
            "security": security,
            "rollback": rollback,
            "rollback_audit": rollback_audit,
            "rollback_snapshot_unchanged": base.snapshot(args, databases["rollback"]) == rollback_before,
            "concurrency": concurrency,
        }
    finally:
        for database in reversed(created):
            base.drop_database(args, database)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=5432)
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

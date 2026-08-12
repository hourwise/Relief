"""Synthetic and static tests for the design-stage Apply 1A write boundary."""

from __future__ import annotations

import copy
import os
import re
import sys
import threading
import unittest
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from unittest.mock import patch

try:
    from .apply_engine_1a import EXPECTED_APPROVED_MANIFEST_SHA256, EXPECTED_APPROVED_PLAN_SHA256, EXPECTED_SOURCE_CHECKSUM
    from .live_apply_1a import (
        LIVE_APPLY_CONFIRMATION,
        PRIVILEGED_DATABASE_ENV,
        LiveApplyGateError,
        SyntheticApplyCoordinator,
        apply_synthetic_transaction,
        execute_privileged_apply,
        future_execution_command,
        LIVE_EXECUTION_ENABLED,
        load_approved_operations,
        post_apply_verify,
        validate_approval_identity,
        validate_operation_set,
    )
except ImportError:  # Supports direct execution: python tools/enrichment/test_live_apply_1a.py
    ROOT_FOR_IMPORT = Path(__file__).resolve().parent
    sys.path.insert(0, str(ROOT_FOR_IMPORT))
    from apply_engine_1a import EXPECTED_APPROVED_MANIFEST_SHA256, EXPECTED_APPROVED_PLAN_SHA256, EXPECTED_SOURCE_CHECKSUM
    from live_apply_1a import (
        LIVE_APPLY_CONFIRMATION,
        PRIVILEGED_DATABASE_ENV,
        LiveApplyGateError,
        SyntheticApplyCoordinator,
        apply_synthetic_transaction,
        execute_privileged_apply,
        future_execution_command,
        LIVE_EXECUTION_ENABLED,
        load_approved_operations,
        post_apply_verify,
        validate_approval_identity,
        validate_operation_set,
    )


ROOT = Path(__file__).resolve().parents[2]
MIGRATION_PATH = next(ROOT.glob("supabase/migrations/*_apply_1a_audit_and_transaction.sql"))


def approved_operations() -> list[dict]:
    _, operations = load_approved_operations(ROOT)
    return operations


def synthetic_state(operations: list[dict]) -> dict:
    facilities = {}
    source_links = []
    for index, operation in enumerate(operations):
        facilities[operation["facility_id"]] = {
            "id": operation["facility_id"],
            "name": f"Synthetic facility {index + 1}",
            "publication_status": "published",
            "verification_status": "source_imported",
            "updated_at": "2026-08-11T00:00:00Z",
            "field_provenance": {"name": {"source": "Toilet Map UK", "field": "name"}} if index == 0 else {},
        }
        if not any(
            row["facility_id"] == operation["facility_id"]
            and row["source_record_id"] == operation["source_record_id"]
            for row in source_links
        ):
            source_links.append(
                {
                    "facility_id": operation["facility_id"],
                    "source_name": "Toilet Map UK",
                    "source_record_id": operation["source_record_id"],
                    "source_updated_at": operation["source_updated_at"],
                    "is_current": True,
                    "import_run_id": "synthetic-import-run",
                }
            )
        for field in ("is_accessible", "requires_radar_key", "has_baby_changing", "is_gender_neutral", "is_free"):
            facilities[operation["facility_id"]].setdefault(field, None)
    return {"facilities": facilities, "source_links": source_links, "audit_runs": {}}


def apply_identity_kwargs() -> dict[str, str]:
    return {
        "plan_sha256": EXPECTED_APPROVED_PLAN_SHA256,
        "manifest_sha256": EXPECTED_APPROVED_MANIFEST_SHA256,
        "source_sha256": EXPECTED_SOURCE_CHECKSUM,
        "project_ref": "bgwxrxkmyaihplaloely",
        "confirmation": LIVE_APPLY_CONFIRMATION,
    }


def registry_operations() -> set[tuple[str, str, str, str, bool]]:
    """Read the immutable SQL seed tuples for static exact-set assertions."""

    sql = MIGRATION_PATH.read_text(encoding="utf-8")
    rows = re.findall(
        r"\('(?P<operation>A1A-[^']+)', '(?P<facility>[0-9a-f-]+)'::uuid, "
        r"'(?P<source>[^']+)', '(?P<field>[^']+)', NULL, (?P<value>true|false),",
        sql,
    )
    return {
        (operation, facility, source, field, value == "true")
        for operation, facility, source, field, value in rows
    }


def registry_operation(operation: dict) -> tuple[str, str, str, str, bool]:
    return (
        operation["operation_id"],
        operation["facility_id"],
        operation["source_record_id"],
        operation["field"],
        operation["proposed_value"],
    )


class LiveApply1ATests(unittest.TestCase):
    def test_exact_approved_identities_are_accepted(self):
        manifest, operations = load_approved_operations(ROOT)
        self.assertEqual(manifest["approved_plan_sha256"], EXPECTED_APPROVED_PLAN_SHA256)
        self.assertEqual(manifest["manifest_sha256"], EXPECTED_APPROVED_MANIFEST_SHA256)
        self.assertEqual(len(operations), 48)
        validate_approval_identity(**apply_identity_kwargs())

    def test_upper_and_lower_approval_inputs_have_one_canonical_identity(self):
        lower = apply_identity_kwargs()
        upper = {
            **lower,
            "plan_sha256": lower["plan_sha256"].upper(),
            "manifest_sha256": lower["manifest_sha256"].upper(),
            "source_sha256": lower["source_sha256"].upper(),
        }
        validate_approval_identity(**lower)
        validate_approval_identity(**upper)

    def test_wrong_plan_sha_is_rejected(self):
        values = apply_identity_kwargs()
        values["plan_sha256"] = "0" * 64
        with self.assertRaises(LiveApplyGateError):
            validate_approval_identity(**values)

    def test_wrong_manifest_sha_is_rejected(self):
        values = apply_identity_kwargs()
        values["manifest_sha256"] = "0" * 64
        with self.assertRaises(LiveApplyGateError):
            validate_approval_identity(**values)

    def test_wrong_source_sha_is_rejected(self):
        values = apply_identity_kwargs()
        values["source_sha256"] = "0" * 64
        with self.assertRaises(LiveApplyGateError):
            validate_approval_identity(**values)

    def test_wrong_project_ref_is_rejected(self):
        values = apply_identity_kwargs()
        values["project_ref"] = "wrong-project"
        with self.assertRaises(LiveApplyGateError):
            validate_approval_identity(**values)

    def test_47_operations_are_rejected(self):
        with self.assertRaises(ValueError):
            validate_operation_set(approved_operations()[:-1])

    def test_49_operations_are_rejected(self):
        operations = approved_operations()
        extra = copy.deepcopy(operations[0])
        extra["operation_id"] = "A1A-extra-test-operation"
        with self.assertRaises(ValueError):
            validate_operation_set(operations + [extra])

    def test_registry_rejects_altered_facility_id(self):
        operations = approved_operations()
        altered = registry_operation(operations[0])
        altered = (altered[0], "11111111-1111-4111-8111-111111111111", *altered[2:])
        self.assertNotIn(altered, registry_operations())

    def test_registry_rejects_altered_source_id(self):
        operations = approved_operations()
        altered = registry_operation(operations[0])
        altered = (*altered[:2], "syntactically-valid-but-unapproved-source-id", *altered[3:])
        self.assertNotIn(altered, registry_operations())

    def test_registry_rejects_altered_field(self):
        operations = approved_operations()
        altered = registry_operation(operations[0])
        altered = (*altered[:3], "is_free", altered[4])
        self.assertNotIn(altered, registry_operations())

    def test_registry_rejects_altered_boolean(self):
        operations = approved_operations()
        altered = registry_operation(operations[0])
        altered = (*altered[:4], not altered[4])
        self.assertNotIn(altered, registry_operations())

    def test_registry_rejects_missing_extra_and_distribution_changes(self):
        operations = approved_operations()
        registry = registry_operations()
        approved = {registry_operation(operation) for operation in operations}
        self.assertEqual(registry, approved)
        self.assertNotEqual(registry, approved - {registry_operation(operations[-1])})
        extra = ("A1A-unapproved", "11111111-1111-4111-8111-111111111111", "extra-source", "is_free", True)
        self.assertNotIn(extra, registry)
        distribution = {field: sum(row[3] == field for row in registry) for field in {row[3] for row in registry}}
        self.assertEqual(
            distribution,
            {
                "has_baby_changing": 16,
                "requires_radar_key": 14,
                "is_gender_neutral": 15,
                "is_accessible": 2,
                "is_free": 1,
            },
        )

    def test_non_allowlisted_field_is_rejected(self):
        operation = copy.deepcopy(approved_operations()[0])
        operation["field"] = "name"
        operations = approved_operations()
        operations[0] = operation
        with self.assertRaises(ValueError):
            validate_operation_set(operations)

    def test_non_null_target_rejects_entire_transaction(self):
        operations = approved_operations()
        state = synthetic_state(operations)
        state["facilities"][operations[0]["facility_id"]][operations[0]["field"]] = False
        result = apply_synthetic_transaction(state, operations)
        self.assertEqual(result.audit["transaction_outcome"], "rolled_back")
        self.assertEqual(result.audit["applied_count"], 0)
        self.assertFalse(result.state["facilities"][operations[0]["facility_id"]][operations[0]["field"]])

    def test_source_link_mismatch_rejects_entire_transaction(self):
        operations = approved_operations()
        state = synthetic_state(operations)
        state["source_links"][0]["facility_id"] = "22222222-2222-2222-2222-222222222222"
        result = apply_synthetic_transaction(state, operations)
        self.assertEqual(result.audit["transaction_outcome"], "rolled_back")
        self.assertEqual(result.audit["applied_count"], 0)

    def test_stronger_provenance_rejects_entire_transaction(self):
        operations = approved_operations()
        state = synthetic_state(operations)
        first = operations[0]
        state["facilities"][first["facility_id"]]["field_provenance"][first["field"]] = {
            "source": "community_confirmed"
        }
        result = apply_synthetic_transaction(state, operations)
        self.assertEqual(result.audit["transaction_outcome"], "rolled_back")
        self.assertEqual(result.audit["applied_count"], 0)

    def test_missing_facility_rejects_entire_transaction(self):
        operations = approved_operations()
        state = synthetic_state(operations)
        del state["facilities"][operations[0]["facility_id"]]
        result = apply_synthetic_transaction(state, operations)
        self.assertEqual(result.audit["transaction_outcome"], "rolled_back")
        self.assertEqual(result.audit["applied_count"], 0)

    def test_audit_run_cannot_claim_success_after_rollback(self):
        operations = approved_operations()
        state = synthetic_state(operations)
        state["facilities"][operations[-1]["facility_id"]][operations[-1]["field"]] = True
        result = apply_synthetic_transaction(state, operations)
        self.assertNotEqual(result.audit["transaction_outcome"], "committed")
        self.assertEqual(result.state["audit_runs"][EXPECTED_APPROVED_MANIFEST_SHA256]["transaction_outcome"], "rolled_back")

    def test_all_48_succeed_atomically_in_synthetic_simulation(self):
        operations = approved_operations()
        state = synthetic_state(operations)
        result = apply_synthetic_transaction(state, operations)
        self.assertEqual(result.audit["transaction_outcome"], "committed")
        self.assertEqual(result.audit["applied_count"], 48)
        self.assertTrue(post_apply_verify(state, result.state, operations)["ok"])

    def test_operation_48_failure_leaves_zero_committed_synthetic_changes(self):
        operations = approved_operations()
        state = synthetic_state(operations)
        state["source_links"][-1]["is_current"] = False
        before_facilities = copy.deepcopy(state["facilities"])
        result = apply_synthetic_transaction(state, operations)
        self.assertEqual(result.audit["transaction_outcome"], "rolled_back")
        self.assertEqual(result.state["facilities"], before_facilities)

    def test_provenance_merge_preserves_unrelated_keys(self):
        operations = approved_operations()
        state = synthetic_state(operations)
        first = operations[0]
        before_unrelated = copy.deepcopy(state["facilities"][first["facility_id"]]["field_provenance"]["name"])
        result = apply_synthetic_transaction(state, operations)
        after_provenance = result.state["facilities"][first["facility_id"]]["field_provenance"]
        self.assertEqual(after_provenance["name"], before_unrelated)
        self.assertIn(first["field"], after_provenance)

    def test_same_manifest_cannot_be_applied_twice(self):
        operations = approved_operations()
        first_state = synthetic_state(operations)
        first = apply_synthetic_transaction(first_state, operations)
        second = apply_synthetic_transaction(first.state, operations)
        self.assertEqual(first.audit["transaction_outcome"], "committed")
        self.assertEqual(second.audit["transaction_outcome"], "already_applied")
        self.assertEqual(second.audit["applied_count"], 0)
        self.assertEqual(first.state["facilities"], second.state["facilities"])

    def test_rolled_back_manifest_is_retryable(self):
        operations = approved_operations()
        state = synthetic_state(operations)
        state["facilities"][operations[-1]["facility_id"]][operations[-1]["field"]] = True
        failed = apply_synthetic_transaction(state, operations)
        self.assertEqual(failed.audit["transaction_outcome"], "rolled_back")

        retry_state = synthetic_state(operations)
        retried = apply_synthetic_transaction(retry_state, operations)
        self.assertEqual(retried.audit["transaction_outcome"], "committed")
        self.assertEqual(retried.audit["applied_count"], 48)

    def test_concurrent_same_manifest_is_serialized_and_applies_once(self):
        operations = approved_operations()
        holder = {"state": synthetic_state(operations)}
        holder_lock = threading.Lock()
        coordinator = SyntheticApplyCoordinator()

        def run_once():
            with holder_lock:
                result = coordinator.run(holder["state"], operations)
                holder["state"] = result.state
                return result

        with ThreadPoolExecutor(max_workers=2) as pool:
            results = list(pool.map(lambda _: run_once(), range(2)))
        outcomes = {result.audit["transaction_outcome"] for result in results}
        self.assertEqual(outcomes, {"committed", "already_applied"})
        self.assertEqual(
            sum(value is not None for facility in holder["state"]["facilities"].values() for value in facility.values()),
            sum(value is not None for facility in results[0].state["facilities"].values() for value in facility.values()),
        )

    def test_normal_roles_have_no_privileged_apply_rpc_grant(self):
        sql = MIGRATION_PATH.read_text(encoding="utf-8").upper()
        self.assertIn("REVOKE EXECUTE ON FUNCTION PRIVATE.APPLY_RELIEF_TOILET_MAP_1A", sql)
        self.assertIn("FROM PUBLIC", sql)
        self.assertIn("FROM ANON", sql)
        self.assertIn("FROM AUTHENTICATED", sql)
        self.assertNotIn("GRANT EXECUTE ON FUNCTION PRIVATE.APPLY_RELIEF_TOILET_MAP_1A(TEXT, TEXT, TEXT, TEXT, TEXT) TO ANON", sql)
        self.assertNotIn("GRANT EXECUTE ON FUNCTION PRIVATE.APPLY_RELIEF_TOILET_MAP_1A(TEXT, TEXT, TEXT, TEXT, TEXT) TO AUTHENTICATED", sql)

    def test_audit_migration_is_guarded_and_pins_only_approved_identities(self):
        sql = MIGRATION_PATH.read_text(encoding="utf-8")
        self.assertIn("ADD COLUMN IF NOT EXISTS", sql)
        self.assertIn("CREATE UNIQUE INDEX IF NOT EXISTS import_runs_apply_1a_committed_manifest_key", sql)
        self.assertIn(EXPECTED_APPROVED_PLAN_SHA256, sql)
        self.assertIn(EXPECTED_APPROVED_MANIFEST_SHA256, sql)
        self.assertIn(EXPECTED_SOURCE_CHECKSUM, sql)
        self.assertIn("lower(source_checksum) = 'f6824fdc7cd29df8c1f45ba749c1b28d319fb34803c55459bbe748ef65937624'", sql)
        self.assertIn("Documented rollback", sql)
        self.assertIn("INSERT INTO PRIVATE.RELIEF_APPLY_1A_APPROVED_OPERATIONS", sql.upper())
        self.assertIn("UPDATE PUBLIC.IMPORT_RUNS", sql.upper())
        self.assertNotIn("INSERT INTO PUBLIC.FACILITIES", sql.upper())
        self.assertNotIn("INSERT INTO PUBLIC.FACILITY_SOURCES", sql.upper())
        self.assertNotIn("DELETE FROM PUBLIC.FACILITIES", sql.upper())
        self.assertNotIn("DELETE FROM PUBLIC.FACILITY_SOURCES", sql.upper())

    def test_private_registry_binds_exact_48_and_fixed_function_contract(self):
        sql = MIGRATION_PATH.read_text(encoding="utf-8")
        self.assertEqual(sql.count("('A1A-"), 48)
        self.assertIn("CREATE TABLE IF NOT EXISTS private.relief_apply_1a_approved_operations", sql)
        self.assertIn("CREATE OR REPLACE FUNCTION private.apply_relief_toilet_map_1a(", sql)
        self.assertNotIn("p_operations_json", sql)
        self.assertNotIn("jsonb)", sql.split("CREATE OR REPLACE FUNCTION private.apply_relief_toilet_map_1a(", 1)[1].split("$function$", 1)[0])
        self.assertIn("SECURITY DEFINER", sql)
        self.assertIn("SET search_path = ''", sql)
        for field in ("has_baby_changing", "requires_radar_key", "is_gender_neutral", "is_accessible", "is_free"):
            self.assertIn(f"IF r.field = '{field}'", sql)

    def test_registry_is_immutable_and_no_role_is_created(self):
        sql = MIGRATION_PATH.read_text(encoding="utf-8").upper()
        self.assertIn("BEFORE INSERT OR UPDATE OR DELETE", sql)
        self.assertIn("RELIEF_APPLY_1A_REGISTRY_IMMUTABLE", sql)
        self.assertNotIn("CREATE ROLE", sql)
        self.assertIn("GRANT EXECUTE ON FUNCTION PRIVATE.APPLY_RELIEF_TOILET_MAP_1A", sql)
        self.assertIn("RELIEF_APPLY_OPERATOR", sql)

    def test_owner_handoff_uses_temporary_create_and_reasserts_boundary(self):
        sql = MIGRATION_PATH.read_text(encoding="utf-8")
        temporary_create = "EXECUTE 'GRANT CREATE ON SCHEMA private TO relief_apply_owner'"
        ownership_transfer = "EXECUTE 'ALTER FUNCTION private.apply_relief_toilet_map_1a(text, text, text, text, text) OWNER TO relief_apply_owner'"
        temporary_revoke = "EXECUTE 'REVOKE CREATE ON SCHEMA private FROM relief_apply_owner'"

        self.assertLess(sql.index(temporary_create), sql.index(ownership_transfer))
        self.assertLess(sql.index(ownership_transfer), sql.index(temporary_revoke))
        self.assertIn("pg_catalog.has_schema_privilege('relief_apply_owner', 'private', 'CREATE')", sql)
        self.assertIn("pg_catalog.has_schema_privilege('relief_apply_operator', 'private', 'CREATE')", sql)
        self.assertNotIn("ALTER SCHEMA private OWNER TO relief_apply_owner", sql)
        self.assertNotIn("GRANT relief_apply_owner TO relief_apply_operator", sql)

    def test_live_execution_hard_lock_refuses_even_with_all_gates_and_env(self):
        self.assertFalse(LIVE_EXECUTION_ENABLED)
        with patch.dict(os.environ, {PRIVILEGED_DATABASE_ENV: "postgresql://review-only-placeholder"}, clear=False):
            with self.assertRaisesRegex(LiveApplyGateError, "hard-locked false"):
                execute_privileged_apply(
                    **apply_identity_kwargs(),
                    privileged_db_env=PRIVILEGED_DATABASE_ENV,
                )

    def test_no_create_delete_unpublish_or_source_link_mutation_path_exists(self):
        source = (MIGRATION_PATH.read_text(encoding="utf-8") + (ROOT / "tools/enrichment/live_apply_1a.py").read_text(encoding="utf-8")).upper()
        for forbidden in (
            "INSERT INTO PUBLIC.FACILITIES",
            "INSERT INTO PUBLIC.FACILITY_SOURCES",
            "DELETE FROM PUBLIC.FACILITIES",
            "DELETE FROM PUBLIC.FACILITY_SOURCES",
            "CREATE FACILITY",
            "PUBLICATION_STATUS =",
            "FACILITY_SOURCES SET",
        ):
            self.assertNotIn(forbidden, source)

    def test_post_apply_verifier_detects_wrong_field(self):
        operations = approved_operations()
        state = synthetic_state(operations)
        result = apply_synthetic_transaction(state, operations)
        changed = copy.deepcopy(result.state)
        changed["facilities"][operations[0]["facility_id"]][operations[0]["field"]] = not operations[0]["proposed_value"]
        verification = post_apply_verify(state, changed, operations)
        self.assertFalse(verification["ok"])
        self.assertTrue(any(item.startswith("WRONG_POSTCHECK_VALUE") for item in verification["failures"]))

    def test_post_apply_verifier_detects_missing_provenance(self):
        operations = approved_operations()
        state = synthetic_state(operations)
        result = apply_synthetic_transaction(state, operations)
        changed = copy.deepcopy(result.state)
        del changed["facilities"][operations[0]["facility_id"]]["field_provenance"][operations[0]["field"]]
        verification = post_apply_verify(state, changed, operations)
        self.assertFalse(verification["ok"])
        self.assertTrue(any(item.startswith("MISSING_POSTCHECK_PROVENANCE") for item in verification["failures"]))

    def test_post_apply_verifier_detects_unexpected_facility_count_change(self):
        operations = approved_operations()
        state = synthetic_state(operations)
        result = apply_synthetic_transaction(state, operations)
        changed = copy.deepcopy(result.state)
        changed["facilities"]["new-facility"] = {"id": "new-facility"}
        verification = post_apply_verify(state, changed, operations)
        self.assertFalse(verification["ok"])
        self.assertIn("FACILITY_COUNT_CHANGED", verification["failures"])

    def test_future_command_contains_all_interlocks_and_no_secret(self):
        command = future_execution_command()
        for token in (
            "--apply",
            "--project-ref bgwxrxkmyaihplaloely",
            f"--plan-sha {EXPECTED_APPROVED_PLAN_SHA256}",
            f"--manifest-sha {EXPECTED_APPROVED_MANIFEST_SHA256}",
            f"--source-sha {EXPECTED_SOURCE_CHECKSUM.upper()}",
            f"--confirm {LIVE_APPLY_CONFIRMATION}",
            f"--privileged-db-env {PRIVILEGED_DATABASE_ENV}",
        ):
            self.assertIn(token, command)
        self.assertNotIn("service_role=", command)
        self.assertNotIn("postgresql://", command)


if __name__ == "__main__":
    unittest.main(verbosity=2)

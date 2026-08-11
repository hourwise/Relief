"""Synthetic and static tests for the design-stage Apply 1A write boundary."""

from __future__ import annotations

import copy
import sys
import threading
import unittest
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

try:
    from .apply_engine_1a import EXPECTED_APPROVED_MANIFEST_SHA256, EXPECTED_APPROVED_PLAN_SHA256, EXPECTED_SOURCE_CHECKSUM
    from .live_apply_1a import (
        LIVE_APPLY_CONFIRMATION,
        PRIVILEGED_DATABASE_ENV,
        LiveApplyGateError,
        SyntheticApplyCoordinator,
        apply_synthetic_transaction,
        future_execution_command,
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
        future_execution_command,
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


class LiveApply1ATests(unittest.TestCase):
    def test_exact_approved_identities_are_accepted(self):
        manifest, operations = load_approved_operations(ROOT)
        self.assertEqual(manifest["approved_plan_sha256"], EXPECTED_APPROVED_PLAN_SHA256)
        self.assertEqual(manifest["manifest_sha256"], EXPECTED_APPROVED_MANIFEST_SHA256)
        self.assertEqual(len(operations), 48)
        validate_approval_identity(**apply_identity_kwargs())

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
        self.assertNotIn("GRANT EXECUTE", sql)
        self.assertNotIn("TO ANON", sql)
        self.assertNotIn("TO AUTHENTICATED", sql)

    def test_audit_migration_is_guarded_and_pins_only_approved_identities(self):
        sql = MIGRATION_PATH.read_text(encoding="utf-8")
        self.assertIn("ADD COLUMN IF NOT EXISTS", sql)
        self.assertIn("CREATE UNIQUE INDEX IF NOT EXISTS", sql)
        self.assertIn(EXPECTED_APPROVED_PLAN_SHA256, sql)
        self.assertIn(EXPECTED_APPROVED_MANIFEST_SHA256, sql)
        self.assertIn(EXPECTED_SOURCE_CHECKSUM.upper(), sql)
        self.assertIn("Documented rollback", sql)
        self.assertNotIn("INSERT INTO", sql.upper())
        self.assertNotIn("UPDATE public.", sql.upper())
        self.assertNotIn("DELETE FROM", sql.upper())

    def test_no_create_delete_unpublish_or_source_link_mutation_path_exists(self):
        source = (MIGRATION_PATH.read_text(encoding="utf-8") + (ROOT / "tools/enrichment/live_apply_1a.py").read_text(encoding="utf-8")).upper()
        for forbidden in ("INSERT INTO", "DELETE FROM", "DROP TABLE", "CREATE FACILITY", "PUBLICATION_STATUS =", "FACILITY_SOURCES SET"):
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

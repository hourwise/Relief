#!/usr/bin/env python3
"""Synthetic tests for the read-only Apply Engine 1A simulator."""

from __future__ import annotations

import copy
import sys
import unittest
from pathlib import Path

try:
    from .apply_engine_1a import (
        ALLOWED_FIELDS,
        APPLY_ENGINE_VERSION,
        EXPECTED_SOURCE_CHECKSUM,
        build_manifest,
        build_simulation,
        evaluate_operation,
        load_json,
        merged_provenance,
        simulate_apply,
        validate_entry_shape,
        validate_manifest_identity,
    )
except ImportError:  # Supports direct execution: python tools/enrichment/test_apply_engine_1a.py
    from apply_engine_1a import (
        ALLOWED_FIELDS,
        APPLY_ENGINE_VERSION,
        EXPECTED_SOURCE_CHECKSUM,
        build_manifest,
        build_simulation,
        evaluate_operation,
        load_json,
        merged_provenance,
        simulate_apply,
        validate_entry_shape,
        validate_manifest_identity,
    )


ROOT = Path(__file__).resolve().parents[2]
PLAN_PATH = ROOT / "docs/data/TOILET_MAP_PROPOSED_APPLY_PLAN_2026-08.json"


def operation(field: str = "is_accessible", proposed: bool = True) -> dict:
    return {
        "operation_id": "A1A-test-0001",
        "plan_schema_version": "1.0",
        "apply_engine_version": APPLY_ENGINE_VERSION,
        "facility_id": "11111111-1111-1111-1111-111111111111",
        "canonical_source_name": "Toilet Map UK",
        "source_record_id": "source-1",
        "source_checksum": EXPECTED_SOURCE_CHECKSUM.upper(),
        "source_updated_at": "2026-08-05T12:00:00Z",
        "field": field,
        "expected_current_value": None,
        "proposed_value": proposed,
        "matching_basis": "EXACT_SOURCE_ID",
        "confidence": "HIGH",
        "provenance_to_be_recorded": {
            "source": "Toilet Map UK",
            "source_record_id": "source-1",
            "source_updated_at": "2026-08-05T12:00:00Z",
            "field": field,
            "previous_value": None,
            "new_value": proposed,
            "basis": "EXACT_SOURCE_ID",
            "policy_version": APPLY_ENGINE_VERSION,
            "recorded_at": "transaction_timestamp",
        },
        "reason": "synthetic test",
        "approved_review_commit": "4710b9ec7a9f5a83aa9e7225400b8a6046ce0e77",
    }


def state(op: dict, current=None, provenance=None) -> dict:
    return {
        "snapshot_mode": "synthetic fixture",
        "facilities": {
            op["facility_id"]: {
                "id": op["facility_id"],
                "name": "Synthetic Facility",
                "updated_at": "2026-08-11T00:00:00Z",
                "verification_status": "source_imported",
                op["field"]: current,
                "field_provenance": provenance if provenance is not None else {},
            }
        },
        "source_links": [
            {
                "facility_id": op["facility_id"],
                "source_name": "Toilet Map UK",
                "source_record_id": op["source_record_id"],
                "source_updated_at": op["source_updated_at"],
                "is_current": True,
                "import_run_id": "run-1",
            }
        ],
    }


class ApplyEngine1ATests(unittest.TestCase):
    def test_exact_allowed_null_to_true_is_accepted(self):
        op = operation(proposed=True)
        self.assertEqual(evaluate_operation(op, state(op), "2026-08-11T14:00:00Z")["status"], "READY")

    def test_exact_allowed_null_to_false_is_accepted(self):
        op = operation(proposed=False)
        self.assertEqual(evaluate_operation(op, state(op), "2026-08-11T14:00:00Z")["status"], "READY")

    def test_non_allowlisted_field_is_rejected(self):
        op = operation(field="name")
        with self.assertRaises(ValueError):
            validate_entry_shape({
                "category": "would_enrich_existing",
                "proposed_action": "AUTO_ENRICH",
                "affected_fields": ["name"],
                "confidence": "HIGH",
                "current_value": None,
                "proposed_value": True,
                "relief_facility_id": op["facility_id"],
                "source_record_id": op["source_record_id"],
                "provenance_that_would_be_recorded": {"basis": "EXACT_SOURCE_ID"},
            })

    def test_non_null_current_value_is_rejected(self):
        op = operation()
        result = evaluate_operation(op, state(op, current=False), "2026-08-11T14:00:00Z")
        self.assertIn("TARGET_FIELD_NOT_NULL", result["failures"])

    def test_source_link_mismatch_is_rejected(self):
        op = operation()
        fixture = state(op)
        fixture["source_links"][0]["facility_id"] = "22222222-2222-2222-2222-222222222222"
        self.assertIn("MISSING_OR_MISMATCHED_SOURCE_LINK", evaluate_operation(op, fixture, "2026-08-11T14:00:00Z")["failures"])

    def test_stale_changed_baseline_is_rejected(self):
        op = operation()
        fixture = state(op)
        fixture["source_links"][0]["source_updated_at"] = "2099-01-01T00:00:00Z"
        self.assertIn("SOURCE_TIMESTAMP_NEWER_THAN_APPROVED", evaluate_operation(op, fixture, "2026-08-11T14:00:00Z")["failures"])

    def test_stronger_provenance_is_rejected(self):
        op = operation()
        fixture = state(op, provenance={op["field"]: {"source": "community_confirmed"}})
        self.assertIn("STRONGER_OR_UNINTERPRETABLE_PROVENANCE", evaluate_operation(op, fixture, "2026-08-11T14:00:00Z")["failures"])

    def test_wrong_source_checksum_is_rejected(self):
        plan = load_json(PLAN_PATH)
        manifest = build_manifest(plan, "plan-hash")
        with self.assertRaises(ValueError):
            validate_manifest_identity(manifest, "plan-hash", "0" * 64)

    def test_wrong_plan_hash_and_version_are_rejected(self):
        plan = load_json(PLAN_PATH)
        manifest = build_manifest(plan, "plan-hash")
        with self.assertRaises(ValueError):
            validate_manifest_identity(manifest, "different-plan-hash", EXPECTED_SOURCE_CHECKSUM)
        changed = copy.deepcopy(manifest)
        changed["apply_engine_version"] = "relief.apply-engine-other.v1"
        with self.assertRaises(ValueError):
            validate_manifest_identity(changed, "plan-hash", EXPECTED_SOURCE_CHECKSUM)

    def test_create_new_entry_is_rejected(self):
        with self.assertRaises(ValueError):
            validate_entry_shape({"category": "would_create_new", "proposed_action": "CREATE_NEW", "affected_fields": []})

    def test_manual_review_entry_is_rejected(self):
        with self.assertRaises(ValueError):
            validate_entry_shape({"category": "would_require_manual_review", "proposed_action": "MANUAL_REVIEW", "affected_fields": ["is_free"]})

    def test_provenance_merge_preserves_unrelated_fields(self):
        op = operation()
        fixture = state(op, provenance={"access_notes": {"source": "Toilet Map UK", "field": "notes"}})
        before, after, _ = merged_provenance(fixture["facilities"][op["facility_id"]], op, fixture["source_links"][0], "2026-08-11T14:00:00Z")
        self.assertEqual(before["access_notes"], after["access_notes"])
        self.assertIn(op["field"], after)

    def test_manifest_is_deterministic(self):
        plan = load_json(PLAN_PATH)
        first = build_manifest(plan, "plan-hash")
        second = build_manifest(plan, "plan-hash")
        self.assertEqual(first["manifest_sha256"], second["manifest_sha256"])
        self.assertEqual(first["operations"], second["operations"])

    def test_repeated_manifest_is_idempotent(self):
        op = operation()
        fixture = state(op)
        first = simulate_apply(fixture, [op], "2026-08-11T14:00:00Z")
        result = evaluate_operation(op, first["state"], "2026-08-11T14:00:00Z", idempotent=True)
        self.assertEqual(result["status"], "IDEMPOTENT_NOOP")

    def test_partial_failure_has_rollback_semantics(self):
        first = operation()
        second = copy.deepcopy(first)
        second["operation_id"] = "A1A-test-0002"
        second["facility_id"] = "22222222-2222-2222-2222-222222222222"
        fixture = state(first)
        fixture["facilities"][second["facility_id"]] = copy.deepcopy(fixture["facilities"][first["facility_id"]])
        fixture["facilities"][second["facility_id"]]["id"] = second["facility_id"]
        fixture["source_links"].append({**fixture["source_links"][0], "facility_id": second["facility_id"]})
        result = simulate_apply(fixture, [first, second], "2026-08-11T14:00:00Z", fail_at=1)
        self.assertTrue(result["rolled_back"])
        self.assertEqual(result["state"], fixture)

    def test_exact_operation_count_is_enforced(self):
        plan = load_json(PLAN_PATH)
        selected_index = next(index for index, entry in enumerate(plan["entries"]) if entry.get("category") == "would_enrich_existing")
        plan["entries"].pop(selected_index)
        with self.assertRaises(ValueError):
            build_manifest(plan, "plan-hash")

    def test_no_mutation_path_exists_in_engine(self):
        source = (ROOT / "tools/enrichment/apply_engine_1a.py").read_text(encoding="utf-8")
        for token in ("POST", "PATCH", "PUT", "DELETE", "supabase_execute_sql", "apply_migration"):
            self.assertNotIn(token, source)

    def test_simulation_reports_zero_persistent_differences(self):
        op = operation()
        fixture = state(op)
        manifest = {
            "approved_plan_sha256": "plan-hash",
            "manifest_sha256": "manifest-hash",
            "operations": [op],
        }
        simulation = build_simulation(ROOT, manifest, fixture, copy.deepcopy(fixture), "2026-08-11T14:00:00Z", "synthetic fixture")
        self.assertEqual(simulation["before_after_database_comparison"]["persistent_data_differences"], 0)
        self.assertEqual(simulation["safety_statement"]["database_mutations_committed"], 0)


if __name__ == "__main__":
    raise SystemExit(unittest.main())

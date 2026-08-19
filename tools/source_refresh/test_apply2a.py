"""Tests for the bounded Refresh 2A existing-facility decision package."""

from __future__ import annotations

import copy
import unittest

from tools.source_refresh.apply2a import build_apply2a_package


def operation(operation_id: str, reason: str, *, category: str = "REVIEW_REQUIRED", field: str = "is_accessible", before=None, after=True, provenance=None, candidate: bool = True) -> dict:
    return {
        "operation_id": operation_id,
        "category": category,
        "target_facility_id": "facility-1" if not field.startswith("__") else None,
        "source_record_id": "source-1",
        "target_field": field,
        "before_value": before,
        "proposed_after_value": after,
        "source_evidence": {"source_checksum": "abc", "source_version": "v1"},
        "current_provenance": provenance,
        "review_reason_code": reason,
        "review_assessment": {
            "safety_critical": False,
            "ambiguous": False,
            "stronger_provenance_risk": bool(provenance),
            "unknown_to_false_certainty_risk": False,
            "material_user_visible_change": field == "open_hours",
            "urgent_search_impact": field == "open_hours",
        },
        "apply_2_candidate": candidate,
    }


class Apply2ATests(unittest.TestCase):
    def test_safe_boolean_is_the_only_execution_candidate(self) -> None:
        manifest = {"operations": [operation("safe", "SAFE_BOOLEAN_ENRICHMENT", category="SAFE_CANDIDATE", before=None, after=True)]}
        report, package = build_apply2a_package(manifest, expected_existing_count=None)
        self.assertEqual(report["decision_counts"], {"APPLY_SOURCE": 1})
        self.assertEqual(package["operation_count"], 1)
        self.assertEqual(package["operations"][0]["decision"], "APPLY_SOURCE")
        self.assertEqual(package["canonical_mutations"], 0)
        self.assertEqual(package["production_mutations"], 0)

    def test_conflict_with_provenance_is_protected(self) -> None:
        manifest = {"operations": [operation("protected", "SOURCE_CANONICAL_CONFLICT", before=False, after=True, provenance={"source": "Toilet Map UK"})]}
        report, package = build_apply2a_package(manifest, expected_existing_count=None)
        self.assertEqual(report["decision_counts"], {"PROTECTED": 1})
        self.assertEqual(package["operations"], [])

    def test_unprotected_conflict_keeps_canonical(self) -> None:
        manifest = {"operations": [operation("conflict", "SOURCE_CANONICAL_CONFLICT", before=False, after=True)]}
        report, package = build_apply2a_package(manifest, expected_existing_count=None)
        self.assertEqual(report["decision_counts"], {"KEEP_CANONICAL": 1})
        self.assertEqual(package["operation_count"], 0)

    def test_hours_are_deferred_for_external_verification(self) -> None:
        hours = {"monday": {"open": "09:00", "close": "17:00"}}
        manifest = {"operations": [operation("hours", "UNSUPPORTED_ENRICHMENT", field="open_hours", before=None, after=hours)]}
        report, package = build_apply2a_package(manifest, expected_existing_count=None)
        self.assertEqual(report["decision_counts"], {"DEFER_EXTERNAL_VERIFICATION": 1})
        self.assertEqual(package["operation_count"], 0)

    def test_out_of_scope_operations_are_not_packaged(self) -> None:
        new = operation("new", "NEW_FACILITY", field="__facility_creation__", candidate=True)
        stale = operation("stale", "STALE_SOURCE_RECORD", field="__stale__", candidate=False)
        manifest = {"operations": [new, stale]}
        report, package = build_apply2a_package(manifest, expected_existing_count=None)
        self.assertEqual(report["decisions"], [])
        self.assertEqual(package["operations"], [])

    def test_build_is_deterministic(self) -> None:
        source = operation("safe", "SAFE_BOOLEAN_ENRICHMENT", category="SAFE_CANDIDATE", before=None, after=False)
        first = build_apply2a_package({"operations": [source]}, expected_existing_count=None)
        second = build_apply2a_package({"operations": [copy.deepcopy(source)]}, expected_existing_count=None)
        self.assertEqual(first, second)


if __name__ == "__main__":
    unittest.main()

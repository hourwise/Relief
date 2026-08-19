"""Tests for the bounded Refresh 2B new-facility decision package."""

from __future__ import annotations

import copy
import unittest

from tools.source_refresh.apply2b import build_apply2b_package


def operation(operation_id: str, name: str, *, collision: bool = False, source_id: str | None = None, latitude: float = 51.5, longitude: float = -0.1) -> dict:
    return {
        "operation_id": operation_id,
        "category": "REVIEW_REQUIRED",
        "target_facility_id": None,
        "source_record_id": source_id or f"source-{operation_id}",
        "target_field": "__facility_creation__",
        "proposed_after_value": {"name": name, "town": "Test", "latitude": latitude, "longitude": longitude},
        "source_evidence": {
            "source_name": "Toilet Map UK",
            "source_url": "https://www.toiletmap.org.uk/dataset",
            "licence": "CC BY 4.0",
            "source_version": "2026-08-18T01:00:00+00:00",
            "source_checksum": "5600358ce06ca5dfdc0060968b26e8c9e05a1cb5c9dbe0455cdf3951f480ad7f",
        },
        "review_reason_code": "NEW_FACILITY",
        "review_assessment": {"safety_critical": True, "ambiguous": True},
        "apply_2_candidate": True,
        "collision_candidate": collision,
    }


class Apply2BTests(unittest.TestCase):
    def test_valid_candidate_is_prepared_without_execution(self) -> None:
        report, manifest = build_apply2b_package({"operations": [operation("one", "Library Toilet")]}, expected_candidate_count=None)
        self.assertEqual(report["decision_counts"], {"PREPARE_INSERT_CANDIDATE": 1})
        self.assertEqual(manifest["operation_count"], 1)
        self.assertEqual(manifest["operations"][0]["decision"], "PREPARE_INSERT_CANDIDATE")
        self.assertEqual(manifest["facility_inserts"], 0)
        self.assertEqual(manifest["production_mutations"], 0)

    def test_refresh_collision_is_deferred(self) -> None:
        report, manifest = build_apply2b_package({"operations": [operation("collision", "Tesco", collision=True)]}, expected_candidate_count=None)
        self.assertEqual(report["decision_counts"], {"DEFER_EXTERNAL_VERIFICATION": 1})
        self.assertEqual(manifest["operations"], [])

    def test_same_name_nearby_source_rows_are_both_deferred(self) -> None:
        first = operation("first", "Becky’s Barn Cafe", latitude=52.63, longitude=-2.26)
        second = operation("second", "Becky's Barn Cafe", latitude=52.631, longitude=-2.259)
        report, manifest = build_apply2b_package({"operations": [first, second]}, expected_candidate_count=None)
        self.assertEqual(report["decision_counts"], {"DEFER_EXTERNAL_VERIFICATION": 2})
        self.assertEqual(manifest["operations"], [])

    def test_placeholder_is_quarantined(self) -> None:
        report, manifest = build_apply2b_package({"operations": [operation("placeholder", "Does not exist")]}, expected_candidate_count=None)
        self.assertEqual(report["decision_counts"], {"QUARANTINE": 1})
        self.assertEqual(manifest["operations"], [])

    def test_out_of_scope_operations_are_not_packaged(self) -> None:
        existing = copy.deepcopy(operation("existing", "Existing", source_id="existing-source"))
        existing["target_facility_id"] = "facility-1"
        existing["target_field"] = "is_accessible"
        report, manifest = build_apply2b_package({"operations": [existing]}, expected_candidate_count=None)
        self.assertEqual(report["decisions"], [])
        self.assertEqual(manifest["operations"], [])

    def test_build_is_deterministic(self) -> None:
        source = operation("one", "Library Toilet")
        first = build_apply2b_package({"operations": [source]}, expected_candidate_count=None)
        second = build_apply2b_package({"operations": [copy.deepcopy(source)]}, expected_candidate_count=None)
        self.assertEqual(first, second)


if __name__ == "__main__":
    unittest.main()

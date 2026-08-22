"""Focused deterministic invariants for TfL physical-unit semantics Batch 2."""

from __future__ import annotations

import unittest

from .tfl_physical_unit_semantics import (
    ALLOWED_CLASSIFICATIONS,
    ATTRIBUTION,
    COORDINATE_SCOPE,
    build_package,
    row_fingerprint,
    source_identity,
    stable_json,
    verify_frozen_inputs,
)


class TfLPhysicalUnitSemanticsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.package = build_package()
        cls.rows = cls.package["adjudications"]

    def test_frozen_source_hashes_and_attribution(self) -> None:
        source = verify_frozen_inputs()
        self.assertEqual(source["zip_sha256"], "19c50772febd1a3d7625f59e079b7590c5da4ed70424d6f552cfd7db1611e2ce")
        self.assertEqual(source["reconciliation_sha256"], "65cc9cc8c41b7b3a003524610b674c7f2eae96ff7fe5116f38f2d2856cb777cb")
        self.assertEqual(source["attribution"], ATTRIBUTION)

    def test_batch_is_exactly_fourteen_and_source_identity_is_unique(self) -> None:
        self.assertEqual(len(self.rows), 14)
        identities = [row["source_record_id"] for row in self.rows]
        self.assertEqual(len(set(identities)), 14)
        self.assertTrue(all(identity.startswith("tfl:") for identity in identities))
        self.assertTrue(all(row["publisher_identity"]["StationUniqueId"] for row in self.rows))
        self.assertTrue(all(row["publisher_identity"]["Id"] for row in self.rows))

    def test_row_fingerprint_and_classification_are_deterministic(self) -> None:
        first = build_package()
        second = build_package()
        self.assertEqual(stable_json(first), stable_json(second))
        for row in self.rows:
            self.assertEqual(row["source_row_fingerprint"], row["source_row"]["raw_row_fingerprint"])
            self.assertIn(row["physical_unit_classification"], ALLOWED_CLASSIFICATIONS)
            self.assertEqual(row["source_record_id"], source_identity({
                "StationUniqueId": row["publisher_identity"]["StationUniqueId"],
                "Id": row["publisher_identity"]["Id"],
            }))
            self.assertEqual(len(row["source_row_fingerprint"]), 64)
        self.assertEqual(row_fingerprint({"a": "b", "c": 1}), row_fingerprint({"c": 1, "a": "b"}))

    def test_no_row_is_physical_unit_promotion_ready(self) -> None:
        self.assertEqual(self.package["summary"]["classification_counts"]["PHYSICAL_UNIT_PROMOTION_READY"], 0)
        self.assertEqual(self.package["summary"]["classification_counts"]["OBSERVATION_ONLY"], 14)
        self.assertEqual(self.package["summary"]["classification_counts"]["HUMAN_ADJUDICATION_REQUIRED"], 0)
        self.assertTrue(all(row["proposed_future_unit_key"] is None for row in self.rows))
        self.assertTrue(all(row["human_review_required"] for row in self.rows))

    def test_coordinates_and_observation_state_fail_closed(self) -> None:
        for row in self.rows:
            self.assertEqual(row["coordinate_scope"], COORDINATE_SCOPE)
            self.assertNotEqual(row["coordinate_scope"], "TOILET_LEVEL")
            self.assertEqual(row["observation_state"]["toilet_unit_id"], None)
            self.assertFalse(row["observation_state"]["physical_unit_asserted"])
            self.assertEqual(row["observation_state"]["unit_link_status"], "UNLINKED")
            self.assertIsNone(row["proposed_future_attributes"])

    def test_accessibility_baby_changing_and_gender_do_not_create_units(self) -> None:
        source_rows_with_attributes = [
            row for row in self.rows
            if row["source_row"]["is_accessible"]
            or row["source_row"]["has_baby_changing"]
            or row["source_row"]["toilet_type"] in {"MALE", "FEMALE", "UNISEX"}
        ]
        self.assertEqual(len(source_rows_with_attributes), 14)
        self.assertTrue(all(row["physical_unit_classification"] != "PHYSICAL_UNIT_PROMOTION_READY" for row in source_rows_with_attributes))

    def test_whole_source_risk_and_production_boundary(self) -> None:
        whole = self.package["whole_source_semantics"]
        self.assertEqual(whole["station_count_in_stations_csv"], 509)
        self.assertEqual(whole["toilet_row_count"], 410)
        self.assertEqual(whole["source_identity"]["unique_identity_count"], 410)
        self.assertEqual(whole["source_identity"]["duplicate_identity_count"], 0)
        self.assertGreater(whole["duplicate_and_topology_risk"]["potential_duplicate_physical_identity_rows"], 0)
        self.assertEqual(self.package["summary"]["physical_units_created"], 0)
        self.assertEqual(self.package["summary"]["physical_unit_mappings_inferred"], 0)
        self.assertEqual(self.package["production_verification"]["total_production_mutations"], 0)
        self.assertFalse(self.package["future_promotion_contract"]["executable"])

    def test_preexisting_provenance_encoding_discrepancy_is_recorded_not_repaired(self) -> None:
        check = self.package["production_verification"]["provenance_source_name_check"]
        self.assertTrue(check["preexisting_encoding_discrepancy"])
        self.assertEqual(check["observed_replacement_character_count"], 14)
        self.assertEqual(check["observed_exact_expected_name_count"], 0)
        self.assertFalse(check["correction_executed"])


if __name__ == "__main__":
    unittest.main()

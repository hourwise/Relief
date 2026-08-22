"""Focused invariants for the bounded 14-observation production plan."""

from __future__ import annotations

import unittest

from .tfl_existing_parent_observation_apply import (
    COORDINATE_SCOPE,
    build_apply_plan,
    observed_attributes,
    reproduce_frozen_14_cohort,
)


class TfLExistingParentObservationApplyTests(unittest.TestCase):
    def setUp(self) -> None:
        self.rows = reproduce_frozen_14_cohort()
        self.plan = build_apply_plan(self.rows)

    def test_exact_cohort_and_parent_cardinality(self) -> None:
        self.assertEqual(len(self.rows), 14)
        self.assertEqual(len({row["source_identity"]["source_record_id"] for row in self.rows}), 14)
        self.assertEqual(len({row["source_identity"]["StationUniqueId"] for row in self.rows}), 14)
        self.assertEqual(len({row["canonical_facility_id"] for row in self.rows}), 14)
        self.assertEqual(self.plan["scope"]["prior_operation_entries"], 28)
        self.assertEqual(self.plan["scope"]["batch_1_contamination"], 0)
        self.assertEqual(self.plan["scope"]["new_parent_contamination"], 0)

    def test_source_identity_and_observation_key_are_stable(self) -> None:
        for operation in self.plan["operations"]:
            identity = operation["source_identity"]["source_record_id"]
            self.assertEqual(operation["observation_key"], identity)
            self.assertEqual(operation["source_record_id"], identity)
            self.assertRegex(identity, r"^tfl:[^:]+:toilet:[^:]+$")

    def test_source_rows_are_not_physical_units(self) -> None:
        for operation in self.plan["operations"]:
            self.assertEqual(operation["coordinate_scope"], COORDINATE_SCOPE)
            self.assertFalse(operation["physical_unit_asserted"])
            self.assertEqual(operation["unit_link_status"], "UNLINKED")
            self.assertIsNone(operation["toilet_unit_id"])
            self.assertFalse(operation["observed_attributes"]["physical_unit_asserted"])
            self.assertEqual(operation["observed_attributes"]["unit_link_status"], "UNLINKED")

    def test_unknowns_and_source_attributes_are_preserved(self) -> None:
        for row in self.rows:
            attrs = observed_attributes(row)
            self.assertEqual(attrs["source_facts"], row["source_facts"])
            self.assertEqual(attrs["provenance"]["attribution"], "Data provided by Transport for London")
            self.assertEqual(attrs["provenance"]["frozen_source"]["zip_sha256"], "19c50772febd1a3d7625f59e079b7590c5da4ed70424d6f552cfd7db1611e2ce")

    def test_plan_has_no_unbounded_or_mutating_path(self) -> None:
        self.assertFalse(self.plan["production_apply"]["executable"])
        self.assertEqual(self.plan["operation_counts"]["facility_inserts"], 0)
        self.assertEqual(self.plan["operation_counts"]["canonical_facility_updates"], 0)
        self.assertEqual(self.plan["operation_counts"]["toilet_unit_inserts"], 0)
        self.assertEqual(self.plan["operation_counts"]["toilet_unit_source_links"], 0)
        self.assertEqual(self.plan["import_run_decision"]["create_count"], 0)


if __name__ == "__main__":
    unittest.main()

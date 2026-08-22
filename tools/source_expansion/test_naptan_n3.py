"""Focused deterministic tests for the N3 source-level transport contract."""

from __future__ import annotations

import json
import unittest
from pathlib import Path

from tools.source_expansion.naptan_n3 import (
    NaptanN3Error,
    deep_hierarchy_analysis,
    multi_parent_analysis,
    national_profile,
    normalize_complexes,
    parse_xml,
)


FIXTURE = Path(__file__).parent / "fixtures" / "naptan_n3_sample.xml"


class NaptanN3Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.data, _ = parse_xml(FIXTURE)
        cls.normalized = normalize_complexes(cls.data)

    def test_single_area_and_parent_interchange_are_preserved(self) -> None:
        roots = {row["root_stop_area_identity"]: row for row in self.normalized["complexes"]}
        root = roots["naptan-stop-area:ROOT"]
        self.assertEqual(root["complex_type"], "MULTIMODAL_PARENT_COMPLEX")
        self.assertEqual(root["stop_area_count"], 6)
        self.assertEqual(root["modes"], ["bus_coach", "metro_tram_underground", "rail"])
        self.assertEqual(root["complex_identity"], "naptan-stop-area:ROOT")

    def test_multi_parent_stop_point_is_not_assigned_to_one_parent(self) -> None:
        multi = multi_parent_analysis(self.data, self.normalized)
        self.assertEqual(multi["total_multi_parent_stop_points"], 1)
        example = multi["examples"][0]
        self.assertEqual(len(example["parent_stop_area_identities"]), 2)
        self.assertIn("PRESERVE_ALL_PARENTS", example["handling"])

    def test_orphan_reference_is_explicit_and_does_not_fabricate_area(self) -> None:
        self.assertIn("naptan-stop-area:UNKNOWN", self.data["defects"]["MISSING_MEMBER_PARENT"])
        self.assertNotIn("naptan-stop-area:UNKNOWN", self.data["areas"])

    def test_deep_hierarchy_and_inactive_member_are_preserved(self) -> None:
        deep = deep_hierarchy_analysis(self.data)
        self.assertEqual(deep["maximum_depth"], 4)
        root = next(row for row in self.normalized["complexes"] if row["root_stop_area_identity"] == "naptan-stop-area:ROOT")
        self.assertEqual(root["status"], "MIXED")

    def test_geometry_scope_is_explicit_and_derived_only_when_needed(self) -> None:
        root = next(row for row in self.normalized["complexes"] if row["root_stop_area_identity"] == "naptan-stop-area:ROOT")
        self.assertEqual(root["geometry_scope"], "PUBLISHER_PARENT_AREA_COORDINATE")
        self.assertNotIn("TOILET", root["geometry_scope"])

    def test_defect_isolation_does_not_create_a_complex_for_missing_parent(self) -> None:
        self.assertNotIn("naptan-stop-area:UNKNOWN", {row["complex_identity"] for row in self.normalized["complexes"]})

    def test_source_order_independence_and_replay_are_deterministic(self) -> None:
        first, _ = parse_xml(FIXTURE)
        second, _ = parse_xml(FIXTURE)
        self.assertEqual(first, second)
        self.assertEqual(normalize_complexes(first), normalize_complexes(second))
        profile = national_profile(first, self.normalized, multi_parent_analysis(first, self.normalized), deep_hierarchy_analysis(first))
        self.assertFalse(profile["canonical_facility_mutations"]["production_execution"])
        self.assertTrue(all(value == 0 for key, value in profile["canonical_facility_mutations"].items() if key != "production_execution"))

    def test_no_apply_or_mutation_code_exists(self) -> None:
        source = Path(__file__).with_name("naptan_n3.py").read_text(encoding="utf-8")
        self.assertNotIn("supabase_execute_sql", source)
        self.assertNotIn("INSERT INTO", source.upper())
        self.assertNotIn("UPDATE PUBLIC", source.upper())

    def test_invalid_duplicate_publisher_identity_fails_closed(self) -> None:
        duplicate = FIXTURE.with_name("naptan_n3_duplicate.xml")
        duplicate.write_text(FIXTURE.read_text(encoding="utf-8").replace("</StopPoints>", "<StopPoint Status=\"active\"><AtcoCode>TESTN30001</AtcoCode></StopPoint></StopPoints>"), encoding="utf-8")
        try:
            with self.assertRaises(NaptanN3Error):
                parse_xml(duplicate)
        finally:
            duplicate.unlink()


if __name__ == "__main__":
    unittest.main()

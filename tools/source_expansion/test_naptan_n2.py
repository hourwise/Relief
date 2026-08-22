import json
import unittest
from pathlib import Path

from tools.source_expansion.naptan_n2 import compare_n1_n2, parse_xml, stop_area_identity


FIXTURE = Path(__file__).parent / "fixtures" / "naptan_n2_sample.xml"
ARTIFACT_ROOT = Path(__file__).parents[2] / "docs" / "data"


class NaptanN2Tests(unittest.TestCase):
    def test_stop_area_identity_is_publisher_based(self):
        self.assertEqual(stop_area_identity("a1"), "naptan-stop-area:A1")

    def test_publisher_memberships_and_multi_parent_are_preserved(self):
        parsed, _ = parse_xml(FIXTURE)
        profile = parsed["profile"]
        self.assertEqual(profile["stop_points"]["total"], 3)
        self.assertEqual(profile["stop_areas"]["total"], 2)
        self.assertEqual(profile["memberships"]["total_rows"], 4)
        self.assertEqual(profile["stop_points"]["multiple_parents"], 1)
        self.assertEqual(profile["stop_points"]["one_parent"], 2)
        self.assertEqual(profile["memberships"]["spatial_memberships_inferred"], 0)

    def test_area_modes_are_derived_from_declared_member_stop_types(self):
        parsed, _ = parse_xml(FIXTURE)
        area = parsed["areas"]["naptan-stop-area:A2"]
        self.assertEqual(area["modes"], ["bus_coach", "rail"])
        self.assertEqual(area["coordinate_scope"], "STOP_AREA_LEVEL")

    def test_no_missing_references_or_duplicate_memberships(self):
        parsed, _ = parse_xml(FIXTURE)
        memberships = parsed["profile"]["memberships"]
        self.assertEqual(memberships["missing_stop_area_references"], 0)
        self.assertEqual(memberships["missing_stop_point_references"], 0)
        self.assertEqual(memberships["duplicate_memberships"], 0)

    def test_n1_n2_comparison_is_deterministic_and_fail_closed(self):
        n1 = [{"tfl_station_id": "S1", "classification": "NO_MATCH"}, {"tfl_station_id": "S2", "classification": "HIGH_CONFIDENCE_NAME_GEO_MATCH"}]
        n2 = [{"tfl_station_id": "S1", "classification": "HIGH_CONFIDENCE_STOPAREA_MATCH", "candidates": [{"member_count": 2}]}, {"tfl_station_id": "S2", "classification": "AMBIGUOUS_TRANSPORT_COMPLEX", "candidates": []}]
        comparison = compare_n1_n2(n1, n2)
        self.assertEqual(comparison["n1_no_match_resolved_to_high_confidence"], 1)
        self.assertEqual(comparison["n1_high_confidence_contradicted"], 1)
        self.assertEqual(comparison["high_confidence_matches_with_multiple_publisher_member_nodes"], 1)
        self.assertTrue(comparison["hierarchy_does_not_authorize_facility_or_toilet_creation"])

    def test_repeat_parse_is_deterministic(self):
        first, _ = parse_xml(FIXTURE)
        second, _ = parse_xml(FIXTURE)
        self.assertEqual(first["profile"], second["profile"])
        self.assertEqual(first["areas"], second["areas"])

    def test_artifacts_are_declarative_and_zero_mutation(self):
        artifact = ARTIFACT_ROOT / "NAPTAN_N2_RELIEF_DRY_RUN_2026-08-22.json"
        if not artifact.exists():
            self.skipTest("N2 derived artifact is generated after the parser fixture tests")
        dry = json.loads(artifact.read_text(encoding="utf-8"))
        plan = dry["production_mutation_plan"]
        self.assertFalse(plan["production_execution"])
        self.assertTrue(all(value == 0 for key, value in plan.items() if key != "production_execution"))
        source = Path(__file__).with_name("naptan_n2.py").read_text(encoding="utf-8")
        self.assertNotIn("supabase_execute_sql", source)
        self.assertNotIn("INSERT INTO", source.upper())


if __name__ == "__main__":
    unittest.main()

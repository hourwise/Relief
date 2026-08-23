"""Focused deterministic tests for the N4A source-graph contract."""

from __future__ import annotations

import copy
import json
import unittest
from pathlib import Path

from tools.source_expansion import naptan_n4a


ROOT = Path(__file__).parent
FIXTURES = ROOT / "fixtures"


class NaptanN4ATests(unittest.TestCase):
    def setUp(self) -> None:
        self.snapshot_a = naptan_n4a.load_fixture(FIXTURES / "naptan_n4a_snapshot_a.json")
        self.snapshot_b = naptan_n4a.load_fixture(FIXTURES / "naptan_n4a_snapshot_b.json")

    def test_snapshot_identity_and_hash_are_deterministic(self) -> None:
        checksum = "A" * 64
        key = naptan_n4a.source_snapshot_key("naptan", checksum)
        self.assertEqual(key, "naptan:sha256:" + "a" * 64)
        self.assertEqual(key, naptan_n4a.source_snapshot_key("naptan", checksum))

    def test_publisher_identity_and_duplicate_detection(self) -> None:
        self.assertEqual(naptan_n4a.publisher_identity("naptan", " sa1 ", "STOP_AREA"), "naptan:stop-area:SA1")
        duplicate = copy.deepcopy(self.snapshot_a)
        duplicate["places"].append(copy.deepcopy(duplicate["places"][0]))
        with self.assertRaises(naptan_n4a.NaptanN4AError):
            naptan_n4a.validate_snapshot(duplicate)

    def test_memberships_preserve_multi_parent_and_duplicate_occurrence(self) -> None:
        summary = naptan_n4a.validate_snapshot(self.snapshot_a)
        self.assertEqual(summary["membership_count"], 6)
        n2_parents = {
            row["publisher_place_identity"]
            for row in self.snapshot_a["memberships"]
            if row["publisher_node_identity"] == "naptan-stop-point:N2"
        }
        self.assertEqual(n2_parents, {"naptan-stop-area:METRO", "naptan-stop-area:ROOT"})
        self.assertEqual(next(row for row in self.snapshot_a["memberships"] if row["publisher_node_identity"].endswith(":N4"))["duplicate_occurrence_count"], 2)

    def test_graph_validation_surfaces_unresolved_parent_without_fabrication(self) -> None:
        result = naptan_n4a.graph_validation(self.snapshot_a)
        self.assertFalse(result["can_mark_snapshot_validated"])
        self.assertEqual(result["cycle_nodes"], [])
        self.assertEqual(result["unresolved_parent_edges"][0]["kind"], "UNRESOLVED_MISSING_PARENT")

    def test_cycle_is_quarantined(self) -> None:
        cyclic = copy.deepcopy(self.snapshot_b)
        cyclic["parents"].append({
            "publisher_child_identity": "naptan-stop-area:ROOT",
            "publisher_parent_identity": "naptan-stop-area:DEEP3",
            "resolution_status": "RESOLVED",
            "duplicate_occurrence_count": 1,
        })
        result = naptan_n4a.graph_validation(cyclic)
        self.assertFalse(result["can_mark_snapshot_validated"])
        self.assertTrue(result["cycle_nodes"])

    def test_projection_never_selects_one_of_two_different_roots(self) -> None:
        projected = naptan_n4a.project_complexes(self.snapshot_a)
        self.assertEqual(projected["production_execution"], False)
        self.assertIn("naptan-stop-area:DEEP3", projected["unresolved_place_identities"])
        roots = {row["complex_identity"] for row in projected["complexes"]}
        self.assertIn("naptan-stop-area:ROOT", roots)
        self.assertIn("naptan-stop-area:ROOT2", roots)

    def test_source_order_does_not_change_projection(self) -> None:
        shuffled = copy.deepcopy(self.snapshot_a)
        shuffled["places"] = list(reversed(shuffled["places"]))
        shuffled["parents"] = list(reversed(shuffled["parents"]))
        shuffled["memberships"] = list(reversed(shuffled["memberships"]))
        self.assertEqual(naptan_n4a.project_complexes(self.snapshot_a), naptan_n4a.project_complexes(shuffled))

    def test_publisher_and_derived_geometry_are_separate(self) -> None:
        for row in self.snapshot_a["places"] + self.snapshot_a["nodes"]:
            self.assertIn(row["coordinate_scope"], {"NONE", "STOP_AREA_LEVEL", "TRANSPORT_STOP_LEVEL"})
        for complex_row in naptan_n4a.project_complexes(self.snapshot_a)["complexes"]:
            self.assertNotIn("latitude", complex_row)
            self.assertNotIn("longitude", complex_row)

    def test_replay_is_idempotent(self) -> None:
        first = naptan_n4a.replay_plan(self.snapshot_a)
        existing = {kind: set(values) for kind, values in naptan_n4a._row_keys(self.snapshot_a).items()}
        second = naptan_n4a.replay_plan(self.snapshot_a, existing)
        self.assertGreater(sum(first["counts"].values()), 0)
        self.assertEqual(second["counts"], {"snapshot": 0, "places": 0, "nodes": 0, "memberships": 0, "parents": 0})
        self.assertFalse(first["production_execution"])

    def test_snapshot_change_diff_is_explainable(self) -> None:
        diff = naptan_n4a.snapshot_diff(self.snapshot_a, self.snapshot_b)
        self.assertIn("naptan-stop-point:N5", diff["nodes"]["added"])
        self.assertIn("naptan-stop-point:N4", diff["nodes"]["removed"])
        self.assertIn("naptan-stop-point:N1", diff["nodes"]["changed"])
        self.assertTrue(diff["memberships"]["added"] or diff["memberships"]["removed"])
        self.assertFalse(diff["production_execution"])

    def test_unresolved_parent_can_become_resolved_in_next_snapshot(self) -> None:
        self.assertFalse(naptan_n4a.graph_validation(self.snapshot_a)["can_mark_snapshot_validated"])
        self.assertTrue(naptan_n4a.graph_validation(self.snapshot_b)["can_mark_snapshot_validated"])

    def test_candidate_migration_is_additive_and_private(self) -> None:
        result = naptan_n4a.validate_candidate_migration()
        self.assertEqual(set(result["tables"]), naptan_n4a.EXPECTED_TABLES)
        self.assertEqual(result["forbidden_patterns_found"], [])
        self.assertTrue(result["security_contract_present"])
        self.assertFalse(result["production_execution"])

    def test_scale_estimate_is_frozen_to_n3_counts(self) -> None:
        estimate = naptan_n4a.national_scale_estimate()
        self.assertEqual(estimate["source_place_rows"], 97270)
        self.assertEqual(estimate["source_node_rows"], 436428)
        self.assertEqual(estimate["publisher_membership_element_rows"], 169530)
        self.assertEqual(estimate["unique_membership_key_rows"], 169527)
        self.assertEqual(estimate["membership_rows_after_exact_duplicate_coalescing"], 169527)
        self.assertEqual(estimate["membership_duplicate_occurrence_total"], 3)
        self.assertEqual(estimate["unresolved_member_parent_edge_rows"], 2804)
        self.assertEqual(estimate["distinct_missing_member_parent_identity_rows"], 1543)
        self.assertEqual(estimate["unresolved_area_parent_edge_rows"], 92)
        self.assertEqual(estimate["distinct_missing_area_parent_identity_rows"], 41)
        self.assertEqual(estimate["normalized_projection_persistence"], "none in N4A; deterministic projection only")

    def test_no_production_mutation_surface_in_module(self) -> None:
        text = Path(naptan_n4a.__file__).read_text(encoding="utf-8").upper()
        self.assertNotIn("SUPABASE_CLIENT", text)
        self.assertNotIn("EXECUTE_SQL", text)
        self.assertNotIn("CREATE_CLIENT", text)


if __name__ == "__main__":
    unittest.main()

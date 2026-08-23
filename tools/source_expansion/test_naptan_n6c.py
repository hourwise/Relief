"""Tests for the deterministic, read-only N6C 60-case register."""

from __future__ import annotations

import json
import unittest
from pathlib import Path

from tools.source_expansion.naptan_n6c import (
    EXPECTED_AMBIGUOUS_COUNT,
    EXPECTED_CASE_COUNT,
    EXPECTED_PROPOSED_COUNT,
    HUMAN_PENDING,
    PRODUCTION_WRITE_CAPABILITY,
    build_case_register,
)


class NaptanN6CTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.repo_root = Path(__file__).resolve().parents[2]
        cls.data_dir = cls.repo_root / "docs" / "data"
        cls.migration = cls.repo_root / "supabase" / "migrations" / "20260822170000_naptan_transport_source_graph.sql"
        cls.register = build_case_register(cls.data_dir, cls.migration)

    def test_production_write_capability_is_false(self) -> None:
        self.assertFalse(PRODUCTION_WRITE_CAPABILITY)

    def test_scope_is_exactly_51_plus_9(self) -> None:
        self.assertEqual(self.register["scope"]["total_cases"], EXPECTED_CASE_COUNT)
        self.assertEqual(self.register["scope"]["proposed_existing_canonical_cases"], EXPECTED_PROPOSED_COUNT)
        self.assertEqual(self.register["scope"]["ambiguous_collision_cases"], EXPECTED_AMBIGUOUS_COUNT)
        self.assertEqual(len(self.register["cases"]), EXPECTED_CASE_COUNT)

    def test_case_ids_are_unique_and_source_cohorts_are_complete(self) -> None:
        cases = self.register["cases"]
        self.assertEqual(len({case["case_id"] for case in cases}), EXPECTED_CASE_COUNT)
        self.assertEqual(sum(case["source_classification"]["n6a"] == "PROPOSED_CANONICAL_MATCH" for case in cases), EXPECTED_PROPOSED_COUNT)
        self.assertEqual(sum(case["source_classification"]["n6a"] == "AMBIGUOUS_CANONICAL_MATCH" for case in cases), EXPECTED_AMBIGUOUS_COUNT)
        proposed = json.loads((self.data_dir / "NAPTAN_N6B_51_PROPOSED_MATCH_REVIEW_2026-08-23.json").read_text(encoding="utf-8"))
        ambiguous = json.loads((self.data_dir / "NAPTAN_N6B_9_AMBIGUITY_REVIEW_2026-08-23.json").read_text(encoding="utf-8"))
        self.assertEqual(
            {case["source_identity"]["complex_identity"] for case in cases},
            {case["complex_identity"] for case in proposed["cases"] + ambiguous["cases"]},
        )

    def test_known_collision_examples_are_retained(self) -> None:
        names = {
            case["source_identity"]["source_name"]
            for case in self.register["cases"]
            if case["source_classification"]["n6a"] == "AMBIGUOUS_CANONICAL_MATCH"
        }
        for expected in {
            "Cockfosters Underground Station",
            "Wapping Wharf",
            "Oakwood Station",
            "Oakwood Underground Station",
            "Falkirk Grahamston Station",
            "Dunoon Ferry Terminal",
            "Canary Wharf Underground Station",
            "Hillingdon Underground Station",
            "North Greenwich Underground Station",
        }:
            self.assertIn(expected, names)

    def test_out_of_scope_populations_do_not_enter(self) -> None:
        for case in self.register["cases"]:
            self.assertNotEqual(case["source_identity"]["source_mode"], "bus_coach")
            self.assertNotEqual(case["source_classification"]["n6a"], "PROPOSED_NEW_TRANSPORT_PLACE")
            self.assertNotEqual(case["source_classification"]["n6a"], "SUPPORTING_SOURCE_ONLY")

    def test_all_human_decisions_are_pending_without_fake_metadata(self) -> None:
        for case in self.register["cases"]:
            human = case["human_adjudication"]
            self.assertEqual(human["decision"], HUMAN_PENDING)
            self.assertIsNone(human["reviewer"])
            self.assertIsNone(human["rationale"])
            self.assertIsNone(human["review_timestamp"])

    def test_ambiguities_retain_competition_and_no_nearest_tie_breaker(self) -> None:
        ambiguous = [case for case in self.register["cases"] if case["source_classification"]["n6a"] == "AMBIGUOUS_CANONICAL_MATCH"]
        self.assertEqual(len(ambiguous), EXPECTED_AMBIGUOUS_COUNT)
        for case in ambiguous:
            self.assertTrue(case["candidate_evidence"]["candidate_facilities"])
            self.assertTrue(case["candidate_evidence"]["competing_source_complexes"])
            self.assertTrue(case["competition_is_not_resolved_by_nearest_distance"])
            self.assertEqual(case["n6c_machine_recommendation"], "RECOMMEND_COLLISION_REVIEW")
            self.assertIn("NEAREST_DISTANCE_IS_NOT_A_TIE_BREAKER", case["collision_warnings"])

    def test_multimodal_cases_are_subplace_aware(self) -> None:
        multimodal = [case for case in self.register["cases"] if case["source_identity"]["source_mode"] == "multimodal"]
        self.assertTrue(multimodal)
        for case in multimodal:
            self.assertIn("MULTIMODAL_COMPLEX_REQUIRES_SUBPLACE_AWARE_RECONCILIATION", case["mode_specific_policy_warnings"])
            self.assertTrue(case["subplace_warnings"] or case["collision_warnings"])

    def test_transport_place_is_not_toilet_facility_and_proximity_is_not_proof(self) -> None:
        for case in self.register["cases"]:
            self.assertIn("PUBLISHER_COMPLEX_COORDINATE_IS_NOT_TOILET_UNIT_COORDINATE", case["evidence_deficiencies"])
            self.assertTrue(case["downstream_eligibility_state"].endswith("NOT_AUTHORIZED"))

    def test_repeat_build_is_identical(self) -> None:
        self.assertEqual(self.register, build_case_register(self.data_dir, self.migration))

    def test_n6b_authoritative_inputs_remain_unchanged(self) -> None:
        manifest = json.loads((self.data_dir / "NAPTAN_N6B_FINAL_DECISION_MANIFEST_2026-08-23.json").read_text(encoding="utf-8"))
        self.assertEqual(manifest["total_production_mutations"], 0)
        self.assertEqual(self.register["n6a_baseline"]["normalized_projection"]["normalized_complexes"], 93751)
        self.assertEqual(self.register["n6a_baseline"]["tfl_reproduction"]["actual_n3_counts"], self.register["n6a_baseline"]["tfl_reproduction"]["expected_n3_counts"])

    def test_emitted_queue_and_manifest_are_exactly_read_only(self) -> None:
        queue = json.loads((self.data_dir / "NAPTAN_N6C_HUMAN_REVIEW_QUEUE_2026-08-23.json").read_text(encoding="utf-8"))
        manifest = json.loads((self.data_dir / "NAPTAN_N6C_FINAL_DECISION_MANIFEST_2026-08-23.json").read_text(encoding="utf-8"))
        self.assertEqual(queue["count"], EXPECTED_CASE_COUNT)
        self.assertTrue(all(row["human_decision"] == HUMAN_PENDING for row in queue["cases"]))
        self.assertEqual(manifest["total_production_mutations"], 0)

    def test_runtime_has_no_sql_or_apply_path(self) -> None:
        source = (self.repo_root / "tools" / "source_expansion" / "naptan_n6c.py").read_text(encoding="utf-8").lower()
        self.assertNotIn("--apply", source)
        self.assertNotIn("supabase_execute_sql", source)
        self.assertNotIn("def apply", source)


if __name__ == "__main__":
    unittest.main()

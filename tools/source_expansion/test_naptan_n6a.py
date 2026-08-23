"""Unit tests for the read-only N6A reconciliation contract."""

from __future__ import annotations

import unittest

from tools.source_expansion.naptan_n6a import (
    CandidateEvidence,
    NaptanN6AError,
    PRODUCTION_WRITE_CAPABILITY,
    assert_read_only_sql,
    classify_candidate,
    emit_contract,
    normalize_matching_text,
    stable_candidate_key,
    token_subset_compatible,
)


class NaptanN6ATests(unittest.TestCase):
    def test_production_write_capability_is_disabled(self) -> None:
        self.assertFalse(PRODUCTION_WRITE_CAPABILITY)
        self.assertFalse(emit_contract()["production_write_capability"])

    def test_name_normalization_is_conservative_and_deterministic(self) -> None:
        self.assertEqual(normalize_matching_text("  North—Station / A  "), "north station a")
        self.assertTrue(token_subset_compatible("Hanwell Rail Station", "Hanwell Rail Station"))
        self.assertTrue(token_subset_compatible("Hanwell Rail Station", "Hanwell Rail Station Platform 1"))
        self.assertFalse(token_subset_compatible("Station", "Central Station"))

    def test_candidate_key_is_semantic(self) -> None:
        key = stable_candidate_key("snapshot", "complex", "facility")
        self.assertEqual(key, "snapshot|complex|facility")
        with self.assertRaises(NaptanN6AError):
            stable_candidate_key("", "complex", "facility")

    def test_read_only_guard_rejects_mutations(self) -> None:
        assert_read_only_sql("select 1")
        assert_read_only_sql("-- comment\nselect count(*) from public.facilities")
        for sql in ("insert into x values (1)", "update x set a=1", "delete from x", "create temp table x(a int)"):
            with self.assertRaises(NaptanN6AError):
                assert_read_only_sql(sql)

    def test_official_identifier_precedes_other_evidence(self) -> None:
        result = classify_candidate(
            CandidateEvidence(official_identifier=True, source_mode="rail"), has_candidate=True
        )
        self.assertEqual(result, "EXISTING_CANONICAL_MATCH")

    def test_proximity_only_is_not_a_match(self) -> None:
        result = classify_candidate(
            CandidateEvidence(distance_metres=20, source_mode="rail"), has_candidate=True
        )
        self.assertEqual(result, "AMBIGUOUS_CANONICAL_MATCH")

    def test_exact_name_and_geometry_is_a_proposal_only(self) -> None:
        result = classify_candidate(
            CandidateEvidence(exact_normalized_name=True, distance_metres=75, source_mode="rail"),
            has_candidate=True,
        )
        self.assertEqual(result, "PROPOSED_CANONICAL_MATCH")

    def test_competing_candidates_are_ambiguous(self) -> None:
        result = classify_candidate(
            CandidateEvidence(exact_normalized_name=True, distance_metres=20, candidate_count=2, source_mode="rail"),
            has_candidate=True,
        )
        self.assertEqual(result, "AMBIGUOUS_CANONICAL_MATCH")

    def test_bus_source_defaults_to_supporting_only(self) -> None:
        result = classify_candidate(CandidateEvidence(source_mode="bus_coach"), has_candidate=False)
        self.assertEqual(result, "SUPPORTING_SOURCE_ONLY")


if __name__ == "__main__":
    unittest.main()

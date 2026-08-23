"""Unit tests for the read-only N6B product-governance contract."""

from __future__ import annotations

import unittest
import json
from pathlib import Path

from tools.source_expansion.naptan_n6a import NaptanN6AError
from tools.source_expansion.naptan_n6b import (
    N6A_CLASSIFICATION_TOTALS,
    N6A_MODE_COUNTS,
    N6B_REVIEW_OUTCOMES,
    PRODUCTION_WRITE_CAPABILITY,
    classify_n6a_rows,
    n6b_policy_manifest,
)


class NaptanN6BTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.repo_root = Path(__file__).resolve().parents[2]
        cls.data_dir = cls.repo_root / "docs" / "data"

    def _artifact(self, name: str) -> dict:
        return json.loads((self.data_dir / name).read_text(encoding="utf-8"))

    def test_production_write_capability_is_false(self) -> None:
        self.assertFalse(PRODUCTION_WRITE_CAPABILITY)

    def test_policy_labels_are_explicit_and_conservative(self) -> None:
        manifest = n6b_policy_manifest()
        self.assertIn("ORDINARY_BUS_STOPS_SUPPORTING_SOURCE_ONLY", manifest["policy_labels"])
        self.assertIn("DIRECT_TOILET_EVIDENCE_REQUIRED_FOR_NEW_CANONICAL_TRANSPORT_FACILITY", manifest["policy_labels"])
        self.assertFalse(manifest["architecture_recommendation"]["schema_change_in_n6b"])

    def test_review_outcomes_are_bounded(self) -> None:
        self.assertEqual(
            set(N6B_REVIEW_OUTCOMES),
            {"ELIGIBLE_FOR_FUTURE_LINK_REVIEW", "REQUIRES_HUMAN_ADJUDICATION", "SUPPORTING_CONTEXT_ONLY", "INSUFFICIENT_TOILET_EVIDENCE"},
        )

    def test_n6a_baseline_constants_reconcile(self) -> None:
        self.assertEqual(sum(N6A_MODE_COUNTS.values()), 93751)
        self.assertEqual(sum(N6A_CLASSIFICATION_TOTALS.values()), 93751)

    def test_51_and_9_review_cohorts_are_complete_and_unique(self) -> None:
        proposed = self._artifact("NAPTAN_N6B_51_PROPOSED_MATCH_REVIEW_2026-08-23.json")
        ambiguous = self._artifact("NAPTAN_N6B_9_AMBIGUITY_REVIEW_2026-08-23.json")
        self.assertEqual(proposed["count"], 51)
        self.assertEqual(ambiguous["count"], 9)
        self.assertEqual(len(proposed["cases"]), 51)
        self.assertEqual(len(ambiguous["cases"]), 9)
        self.assertEqual(len({case["complex_identity"] for case in proposed["cases"]}), 51)
        self.assertEqual(len({case["complex_identity"] for case in ambiguous["cases"]}), 9)

    def test_n6a_classification_contract_and_source_graph_are_preserved(self) -> None:
        mode = self._artifact("NAPTAN_N6A_MODE_RELEVANCE_2026-08-23.json")
        baseline = self._artifact("NAPTAN_N6B_SOURCE_BASELINE_2026-08-23.json")
        self.assertEqual(mode["classification_totals"], N6A_CLASSIFICATION_TOTALS)
        self.assertEqual(baseline["source_graph_counts"]["total"], 706745)
        self.assertEqual(baseline["source_graph_mutations"], 0)

    def test_final_manifest_is_analysis_only(self) -> None:
        manifest = self._artifact("NAPTAN_N6B_FINAL_DECISION_MANIFEST_2026-08-23.json")
        self.assertEqual(manifest["total_production_mutations"], 0)
        self.assertTrue(all("promotion" not in label.lower() or "not" in label.lower() for label in manifest["classifications"]))

    def test_empty_candidate_input_is_safe(self) -> None:
        self.assertEqual(classify_n6a_rows([]), [])

    def test_n6b_does_not_expose_an_apply_flag(self) -> None:
        with self.assertRaises(NaptanN6AError):
            from tools.source_expansion.naptan_n6a import assert_read_only_sql

            assert_read_only_sql("insert into public.facilities(id) values ('x')")


if __name__ == "__main__":
    unittest.main()

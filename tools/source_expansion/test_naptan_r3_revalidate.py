import json
import unittest
from pathlib import Path

from .naptan_r3_revalidate import (
    EXPECTED_REVIEW_POOL,
    EXPECTED_STRICT_POOL,
    PRODUCTION_WRITE_CAPABILITY,
    TOOL_VERSION,
)


ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / "docs" / "data"


class NaptanR3RevalidationTests(unittest.TestCase):
    def test_write_capability_is_disabled_and_no_apply_switch_exists(self) -> None:
        self.assertFalse(PRODUCTION_WRITE_CAPABILITY)
        source = (ROOT / "tools" / "source_expansion" / "naptan_r3_revalidate.py").read_text(encoding="utf-8")
        self.assertNotIn("--apply", source)

    def test_committed_pool_has_exact_strict_and_review_counts(self) -> None:
        register = json.loads(
            (DATA / "LOCAL_AUTHORITY_OGL_COMBINED_CANDIDATE_REGISTER_2026-08-23.json").read_text(encoding="utf-8")
        )
        strict = [row for row in register["entries"] if row["classification"] == "CONSERVATIVE_NET_NEW"]
        review = [row for row in register["entries"] if row["classification"] == "POSSIBLE_NET_NEW_REVIEW"]
        self.assertEqual(len(strict), EXPECTED_STRICT_POOL)
        self.assertEqual(len(review), EXPECTED_REVIEW_POOL)
        self.assertEqual(len({row["candidate_id"] for row in strict}), EXPECTED_STRICT_POOL)

    def test_only_strict_pool_is_in_apply_manifest(self) -> None:
        manifest = json.loads(
            (DATA / "LOCAL_AUTHORITY_OGL_R3_PRODUCTION_APPLY_MANIFEST_2026-09-16.json").read_text(encoding="utf-8")
        )
        self.assertEqual(manifest["tool_version"], TOOL_VERSION)
        self.assertEqual(manifest["candidate_count"], EXPECTED_STRICT_POOL)
        self.assertEqual(manifest["review_candidates_excluded"], EXPECTED_REVIEW_POOL)
        self.assertFalse(manifest["production_apply_authorized"])
        self.assertFalse(manifest["canonical_insertion_authorized"])
        self.assertEqual(manifest["mutation_count_this_transaction"], 0)
        self.assertEqual(len(manifest["candidates"]), EXPECTED_STRICT_POOL)
        self.assertEqual(len({row["candidate_id"] for row in manifest["candidates"]}), EXPECTED_STRICT_POOL)

    def test_source_revalidation_records_causeway_drift_without_identity_drift(self) -> None:
        evidence = json.loads(
            (DATA / "LOCAL_AUTHORITY_OGL_R3_SOURCE_REVALIDATION_2026-09-16.json").read_text(encoding="utf-8")
        )
        self.assertEqual(evidence["strict_pool"]["revalidated"], EXPECTED_STRICT_POOL)
        self.assertEqual(evidence["strict_pool"]["missing_source_identities"], [])
        self.assertEqual(evidence["strict_pool"]["coordinate_mismatches"], [])
        drift = evidence["source_payload_drift"]
        self.assertEqual(len(drift), 1)
        self.assertEqual(drift[0]["source_id"], "causeway-coast-and-glens-public-toilets")
        self.assertEqual(drift[0]["status"], "PAYLOAD_CHANGED_IDENTITIES_STABLE")
        self.assertTrue(drift[0]["identity_stable"])


if __name__ == "__main__":
    unittest.main()

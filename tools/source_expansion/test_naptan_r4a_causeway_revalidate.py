import json
import unittest
from pathlib import Path

from . import naptan_r4a_causeway_revalidate as r4a


class NaptanR4ACausewayTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.root = Path(__file__).parents[2]
        cls.data_dir = cls.root / "docs" / "data"

    def test_production_write_capability_is_disabled(self):
        self.assertFalse(r4a.PRODUCTION_WRITE_CAPABILITY)
        source = (self.root / "tools/source_expansion/naptan_r4a_causeway_revalidate.py").read_text(encoding="utf-8")
        self.assertNotIn("--apply", source)
        self.assertNotIn("supabase_execute_sql", source)

    def test_r3_manifest_is_immutable_and_complete(self):
        manifest_path = self.data_dir / "LOCAL_AUTHORITY_OGL_R3_PRODUCTION_APPLY_MANIFEST_2026-09-16.json"
        self.assertEqual(r4a.sha256_bytes(manifest_path.read_bytes()), r4a.R3_MANIFEST_SHA256)
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        self.assertEqual(manifest["candidate_count"], 89)
        self.assertEqual(len(manifest["candidates"]), 89)
        self.assertEqual(manifest["review_candidates_excluded"], 7)

    def test_causeway_revalidation_reaches_all_five_candidates(self):
        evidence = json.loads((self.data_dir / "LOCAL_AUTHORITY_OGL_R4A_CAUSEWAY_SOURCE_REVALIDATION_2026-09-16.json").read_text(encoding="utf-8"))
        self.assertEqual(evidence["current_r4a_payload"]["sha256"], r4a.EXPECTED_R3_CAUSEWAY_SHA256)
        self.assertEqual(evidence["causeway_r3_candidate_count"], 5)
        self.assertEqual(evidence["candidate_impact_counts"], {"UNCHANGED": 5})
        self.assertEqual(evidence["comparisons"]["r3_to_r4a"]["missing_record_ids"], [])
        self.assertEqual(evidence["comparisons"]["r3_to_r4a"]["added_record_ids"], [])
        self.assertTrue(evidence["comparisons"]["r3_to_r4a"]["byte_identical"])

    def test_replacement_manifest_is_non_authorizing_and_preserves_scope(self):
        manifest = json.loads((self.data_dir / "LOCAL_AUTHORITY_OGL_R4_PRODUCTION_APPLY_MANIFEST_2026-09-16.json").read_text(encoding="utf-8"))
        self.assertEqual(manifest["candidate_count"], 89)
        self.assertEqual(len(manifest["candidates"]), 89)
        self.assertEqual(manifest["review_rows_in_apply_manifest"], 0)
        self.assertFalse(manifest["production_apply_authorized"])
        self.assertFalse(manifest["canonical_insertion_authorized"])
        self.assertEqual(manifest["production_mutations"], 0)
        self.assertEqual(manifest["causeway_current_sha256"], r4a.EXPECTED_R3_CAUSEWAY_SHA256)

    def test_replacement_manifest_seal_matches_content(self):
        manifest_path = self.data_dir / "LOCAL_AUTHORITY_OGL_R4_PRODUCTION_APPLY_MANIFEST_2026-09-16.json"
        seal = json.loads((self.data_dir / "LOCAL_AUTHORITY_OGL_R4_APPLY_MANIFEST_SEAL_2026-09-16.json").read_text(encoding="utf-8"))
        self.assertEqual(seal["manifest_sha256"], r4a.sha256_bytes(manifest_path.read_bytes()))
        self.assertEqual(seal["candidate_count"], 89)
        self.assertFalse(seal["production_apply_authorized"])
        self.assertEqual(seal["production_mutations"], 0)


if __name__ == "__main__":
    unittest.main()

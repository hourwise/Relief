from __future__ import annotations

import unittest

from .local_authority_ogl_pilot import (
    OFFICIAL_ATTRIBUTION,
    PRODUCTION_WRITE_CAPABILITY,
    SOURCE_CATALOG,
    classify_production_match,
    normalize_name,
    normalize_postcode,
)


class LocalAuthorityOglPilotTests(unittest.TestCase):
    def test_selected_sources_have_resource_level_fingerprints_and_ogl(self) -> None:
        self.assertEqual(len(SOURCE_CATALOG), 2)
        for source in SOURCE_CATALOG.values():
            self.assertEqual(source["licence"], "Open Government Licence v3.0")
            self.assertTrue(source["resource_url"].startswith("https://"))
            self.assertEqual(len(source["expected_sha256"]), 64)
            self.assertGreater(source["expected_bytes"], 0)

    def test_normalization_is_conservative_and_separate_from_raw_text(self) -> None:
        self.assertEqual(normalize_name("  St Leonard’s Place — Public Toilets "), "st leonard s place public toilets")
        self.assertEqual(normalize_postcode("yo1 2ew"), "YO12EW")
        self.assertEqual(OFFICIAL_ATTRIBUTION, "Contains public sector information licensed under the Open Government Licence v3.0.")

    def test_direct_toilet_evidence_is_not_inferred_from_a_place_name(self) -> None:
        self.assertTrue("toilet" in normalize_name("Main Street Public Toilets"))
        self.assertFalse("toilet" in normalize_name("Town Hall"))

    def test_existing_guard_prefers_exact_postcode_and_bounded_proximity(self) -> None:
        self.assertEqual(classify_production_match({"source_record_id": "a", "distance_m": 99.9, "exact_postcode": False, "token_subset": False})["candidate_status"], "LIKELY_EXISTING_OR_DUPLICATE")
        self.assertEqual(classify_production_match({"source_record_id": "b", "distance_m": 900, "exact_postcode": True, "token_subset": False})["candidate_status"], "LIKELY_EXISTING_OR_DUPLICATE")
        self.assertEqual(classify_production_match({"source_record_id": "c", "distance_m": 200, "exact_postcode": False, "token_subset": True})["candidate_status"], "LIKELY_EXISTING_OR_DUPLICATE")

    def test_conservative_candidate_requires_no_facility_within_250m(self) -> None:
        broad = classify_production_match({"source_record_id": "a", "distance_m": 250.1, "exact_postcode": False, "token_subset": False})
        near = classify_production_match({"source_record_id": "b", "distance_m": 249.9, "exact_postcode": False, "token_subset": False})
        self.assertTrue(broad["conservative_net_new"])
        self.assertFalse(near["conservative_net_new"])

    def test_production_write_capability_is_false(self) -> None:
        self.assertFalse(PRODUCTION_WRITE_CAPABILITY)


if __name__ == "__main__":
    unittest.main()

from __future__ import annotations

import unittest

from .local_authority_ogl_pilot import (
    OFFICIAL_ATTRIBUTION,
    PRODUCTION_WRITE_CAPABILITY,
    SOURCE_CATALOG,
    classify_production_match,
    compare_records_to_production,
    cross_source_deduplicate,
    deduplicate_source_records,
    distance_meters,
    normalize_name,
    normalize_postcode,
    normalize_tabular_record,
    osgb36_to_wgs84,
)


class LocalAuthorityOglPilotTests(unittest.TestCase):
    def test_selected_sources_have_resource_level_fingerprints_and_ogl(self) -> None:
        self.assertGreaterEqual(len(SOURCE_CATALOG), 6)
        for source_id in ("city-of-york-public-toilets", "causeway-coast-and-glens-public-toilets"):
            source = SOURCE_CATALOG[source_id]
            self.assertEqual(source["licence"], "Open Government Licence v3.0")
            self.assertEqual(len(source["expected_sha256"]), 64)
            self.assertGreater(source["expected_bytes"], 0)
        for source in SOURCE_CATALOG.values():
            self.assertTrue(source["resource_url"].startswith("https://"))
            self.assertTrue(source["licence"])

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

    def test_osgb36_conversion_returns_valid_wgs84(self) -> None:
        latitude, longitude = osgb36_to_wgs84(518072, 103649)
        self.assertAlmostEqual(latitude, 50.84, delta=0.05)
        self.assertAlmostEqual(longitude, -0.33, delta=0.08)
        self.assertTrue(-90 <= latitude <= 90 and -180 <= longitude <= 180)

    def test_tabular_normalization_uses_stable_publisher_identity(self) -> None:
        row = {
            "UPRN": "60001449",
            "LocationText": "BEACH GREEN PUBLIC CONVENIENCES",
            "StreetAddress": "BRIGHTON ROAD LANCING",
            "Postcode": "",
            "GeoX": "518072",
            "GeoY": "103649",
            "ServiceTypeLabel": "Public toilets",
            "AccessibleCategory": "Unisex",
            "OpeningHours": "09:00-21:00",
            "ChargeAmount": "",
            "ManagedBy": "ADC",
            "ExtractDate": "07/07/2014",
        }
        record = normalize_tabular_record(row, "adur-public-toilets", 1, "a" * 64)
        self.assertEqual(record["source_record_id"], "Adur public toilets:60001449")
        self.assertTrue(record["source_identity_stable"])
        self.assertTrue(record["direct_toilet_evidence"])
        self.assertIsNotNone(record["latitude"])

    def test_internal_and_cross_source_deduplication_are_deterministic(self) -> None:
        base = {
            "source_namespace": "a",
            "source_dataset": "A",
            "name": "Market Public Toilets",
            "address": "High Street",
            "postcode": None,
            "postcode_normalized": "",
            "latitude": 51.0,
            "longitude": -1.0,
            "source_identity_stable": True,
        }
        first = {**base, "source_record_id": "A:1"}
        duplicate = {**base, "source_record_id": "A:2", "name": "Market Disabled Toilets", "latitude": 51.00005}
        unique = {**base, "source_record_id": "A:3", "name": "Remote Toilets", "latitude": 51.01}
        deduped, duplicate_count = deduplicate_source_records([unique, duplicate, first])
        self.assertEqual(len(deduped), 2)
        self.assertEqual(duplicate_count, 1)
        cross_duplicate = {**duplicate, "source_namespace": "b", "source_record_id": "B:1"}
        cross, cross_count = cross_source_deduplicate([deduped[0], cross_duplicate])
        self.assertEqual(len(cross), 1)
        self.assertEqual(cross_count, 1)

    def test_production_comparison_preserves_classification_guards(self) -> None:
        record = normalize_tabular_record(
            {
                "UPRN": "1",
                "LocationText": "Remote Public Toilet",
                "StreetAddress": "Remote Road",
                "Postcode": "AB1 2CD",
                "GeoX": "518072",
                "GeoY": "103649",
                "ServiceTypeLabel": "Public toilets",
            },
            "adur-public-toilets",
            1,
            "b" * 64,
        )
        facilities = [{"id": "f1", "name": "Nearby Facility", "postcode": "ZZ1 1ZZ", "latitude": record["latitude"], "longitude": record["longitude"] + 0.01}]
        compared = compare_records_to_production([record], facilities)
        self.assertEqual(compared[0]["classification"], "CONSERVATIVE_NET_NEW")
        self.assertGreater(compared[0]["nearest_relief_distance_m"], 250)
        self.assertAlmostEqual(distance_meters(record["latitude"], record["longitude"], record["latitude"], record["longitude"]), 0.0, places=5)


if __name__ == "__main__":
    unittest.main()

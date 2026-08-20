from __future__ import annotations

import unittest

from .pipeline import analyze_duplicates, build_report, normalize_esd_rows, normalize_tfl_bus_rows
from .sheffield import build_sheffield_package


class SourceExpansionTests(unittest.TestCase):
    def test_tfl_example_preserves_unknown_coordinates_and_boolean_semantics(self) -> None:
        records = normalize_tfl_bus_rows([
            {"BUS STATIONS": "Canning Town", "PUBLIC TOILETS": "Yes", "NOTES": "24 hr access"},
            {"BUS STATIONS": "Harrow", "PUBLIC TOILETS": "No", "NOTES": ""},
        ], "tfl_bus_public_toilets")
        self.assertEqual(records[0]["source_boolean_public_toilets"], True)
        self.assertEqual(records[1]["source_boolean_public_toilets"], False)
        self.assertIsNone(records[0]["latitude"])
        self.assertIn("missing latitude/longitude", records[0]["validation_errors"][0])

    def test_esd_rows_do_not_treat_osgb36_as_wgs84(self) -> None:
        records = normalize_esd_rows([{
            "UPRN": "1001",
            "LocationText": "Town toilets",
            "GeoX": "553096",
            "GeoY": "154729",
            "CoordinateReferenceSystem": "OSGB36",
            "AccessibleCategory": "Female and male",
        }], "rother_public_toilets")
        self.assertEqual(records[0]["source_record_id"], "1001")
        self.assertIsNone(records[0]["latitude"])
        self.assertTrue(records[0]["validation_errors"])

    def test_geojson_point_coordinates_are_preserved_as_wgs84(self) -> None:
        records = normalize_esd_rows([{
            "UPRN": "2001",
            "LocationText": "Sheffield toilets",
            "__latitude": 53.3811,
            "__longitude": -1.4701,
        }], "sheffield_public_toilets")
        self.assertEqual(records[0]["latitude"], 53.3811)
        self.assertEqual(records[0]["longitude"], -1.4701)
        self.assertEqual(records[0]["validation_errors"], [])

    def test_duplicate_and_mutation_boundaries_are_explicit(self) -> None:
        records = normalize_tfl_bus_rows([
            {"BUS STATIONS": "A", "PUBLIC TOILETS": "Yes"},
            {"BUS STATIONS": "A", "PUBLIC TOILETS": "No"},
        ], "tfl_bus_public_toilets")
        duplicate = analyze_duplicates(records)
        self.assertEqual(duplicate["duplicate_source_record_ids"], ["station:a"])
        report = build_report({
            "source_id": "tfl_bus_public_toilets", "source_name": "TfL", "publisher": "TfL",
            "source_url": "https://tfl.gov.uk", "licence_identifier": "TfL terms",
            "licence_url": "https://tfl.gov.uk/info-for/open-data-users/", "required_attribution": "Data provided by Transport for London",
        }, records, raw_checksum="abc", retrieved_at="2026-08-20T00:00:00Z", source_version="example")
        self.assertEqual(report["mutations"]["production_mutations"], 0)
        self.assertEqual(report["mutations"]["facility_inserts"], 0)
        self.assertTrue(report["production_reconciliation"]["match_policy"])

    def test_sheffield_package_has_no_supportable_operations(self) -> None:
        records = [{"source_record_id": str(i), "name": None} for i in range(41)]
        package = build_sheffield_package({
            "source": {"source_id": "sheffield_public_toilets", "source_name": "Sheffield", "publisher": "Sheffield City Council", "source_url": "https://example.invalid", "licence_identifier": "OGL", "raw_checksum": "abc", "retrieved_at": "2026-08-20T00:00:00Z"},
            "records": records,
        }, [str(i) for i in range(18)], [str(i) for i in range(18, 41)])
        self.assertEqual(package["decision_summary"]["INSERT"], 0)
        self.assertEqual(package["decision_summary"]["SOURCE_LINK"], 0)
        self.assertEqual(package["decision_summary"]["ENRICHMENT"], 0)
        self.assertEqual(package["decision_summary"]["DEFER_EXTERNAL_VERIFICATION"], 41)
        self.assertEqual(package["production_boundary"]["production_mutations"], 0)

    def test_read_only_production_match_summary_is_recorded_without_mutation(self) -> None:
        report = build_report({
            "source_id": "sheffield_public_toilets", "source_name": "Sheffield", "publisher": "Sheffield City Council",
            "source_url": "https://example.invalid", "licence_identifier": "OGL",
            "licence_url": "https://example.invalid/licence", "required_attribution": "Sheffield City Council",
        }, [], raw_checksum="abc", retrieved_at="2026-08-20T00:00:00Z", source_version="fixture",
            production_match_summary={"nearby_within_approx_100m": 2, "exact_source_links": 0})
        self.assertEqual(report["production_reconciliation"]["nearby_within_approx_100m"], 2)
        self.assertEqual(report["mutations"]["production_mutations"], 0)


if __name__ == "__main__":
    unittest.main()

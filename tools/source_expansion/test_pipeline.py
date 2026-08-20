from __future__ import annotations

import unittest

from .pipeline import analyze_duplicates, build_report, normalize_esd_rows, normalize_tfl_bus_rows


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


if __name__ == "__main__":
    unittest.main()

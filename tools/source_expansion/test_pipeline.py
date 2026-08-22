from __future__ import annotations

import unittest

from .pipeline import analyze_duplicates, build_report, normalize_esd_rows, normalize_tfl_bus_rows
from .model_adjudication import (
    STATION_LEVEL_PRECISION,
    aggregate_at_least_one,
    classify_position_precision,
    classify_tfl_physical_relationship,
    reclassify_frozen_tfl_operations,
    tfl_source_identity,
    tfl_source_record_id,
)
from .tfl_unit_readiness import (
    READINESS_CLASSIFICATION,
    build_readiness_package,
    classify_insert_row,
    json_safe,
)
from .sheffield import build_sheffield_package
from .tfl_detailed import normalize_tfl_feed, reconcile_toilets


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

    def test_tfl_detailed_feed_joins_station_identity_and_preserves_station_precision(self) -> None:
        rows = normalize_tfl_feed({
            "Stations.csv": [{"UniqueId": "HUBTEST", "Name": "Test Station"}],
            "StationPoints.csv": [{"StationUniqueId": "HUBTEST", "Lat": "51.5", "Lon": "-0.1", "UniqueId": "point-1"}],
            "Toilets.csv": [{
                "StationUniqueId": "HUBTEST", "Id": "7", "Type": "Unisex", "IsAccessible": "TRUE",
                "HasBabyChanging": "FALSE", "IsInsideGateLine": "TRUE", "Location": "Ticket hall",
                "IsFeeCharged": "FALSE", "IsManagedByTfL": "TRUE",
            }],
        })
        self.assertEqual(rows[0]["stable_tfl_station_id"], "HUBTEST")
        self.assertEqual(rows[0]["stable_tfl_toilet_id"], "7")
        self.assertEqual(rows[0]["station_name"], "Test Station")
        self.assertEqual(rows[0]["station_coordinates"]["latitude"], 51.5)
        self.assertEqual(rows[0]["positional_precision"], "STATION_LEVEL_ONLY; TOILET_COORDINATES_NOT_PROVIDED")

    def test_tfl_multiple_toilets_do_not_collapse_into_one_relief_facility(self) -> None:
        tables = {
            "Stations.csv": [{"UniqueId": "HUBTEST", "Name": "Test Station"}],
            "StationPoints.csv": [{"StationUniqueId": "HUBTEST", "Lat": "51.5", "Lon": "-0.1"}],
            "Toilets.csv": [
                {"StationUniqueId": "HUBTEST", "Id": "1", "Type": "Male", "IsAccessible": "TRUE", "HasBabyChanging": "FALSE", "IsInsideGateLine": "TRUE", "Location": "Ticket hall", "IsFeeCharged": "FALSE", "IsManagedByTfL": "TRUE"},
                {"StationUniqueId": "HUBTEST", "Id": "2", "Type": "Female", "IsAccessible": "TRUE", "HasBabyChanging": "FALSE", "IsInsideGateLine": "TRUE", "Location": "Ticket hall", "IsFeeCharged": "FALSE", "IsManagedByTfL": "TRUE"},
            ],
        }
        reconciled = reconcile_toilets(normalize_tfl_feed(tables), [{
            "id": "facility-1", "name": "Test Station", "address": None, "town": "London",
            "latitude": 51.5, "longitude": -0.1, "is_accessible": None,
            "has_baby_changing": None, "is_free": None, "is_gender_neutral": None,
        }], [])
        self.assertEqual(len(reconciled), 2)
        self.assertTrue(all(row["model_review_required"] for row in reconciled))
        self.assertTrue(all(row["proposed_operations"] == [] for row in reconciled))

    def test_tfl_identity_is_station_and_toilet_id(self) -> None:
        self.assertEqual(tfl_source_identity("910GTEST", "7"), ("910GTEST", "7"))
        self.assertEqual(tfl_source_record_id("910GTEST", "7"), "tfl:910GTEST:toilet:7")

    def test_source_gender_rows_are_not_automatically_collapsed(self) -> None:
        rows = [
            {"StationUniqueId": "HUBTEST", "Id": "1", "Type": "Male"},
            {"StationUniqueId": "HUBTEST", "Id": "2", "Type": "Female"},
            {"StationUniqueId": "HUBTEST", "Id": "3", "Type": "Unisex"},
        ]
        self.assertEqual(classify_tfl_physical_relationship(rows), "SOURCE_DISTINCT_PHYSICAL_UNKNOWN")
        self.assertEqual(len({tfl_source_record_id(r["StationUniqueId"], r["Id"]) for r in rows}), 3)

    def test_station_coordinates_retain_station_level_precision(self) -> None:
        row = {"station_coordinates": {"latitude": 51.5, "longitude": -0.1}}
        self.assertEqual(classify_position_precision(row), STATION_LEVEL_PRECISION)
        self.assertNotEqual(classify_position_precision(row), "TOILET_LEVEL")

    def test_multiple_source_rows_can_share_one_parent_without_proving_rooms(self) -> None:
        rows = [
            {"StationUniqueId": "HUBTEST", "Id": "1", "Type": "Male"},
            {"StationUniqueId": "HUBTEST", "Id": "2", "Type": "Female"},
        ]
        self.assertEqual(len(rows), 2)
        self.assertEqual(classify_tfl_physical_relationship(rows), "SOURCE_DISTINCT_PHYSICAL_UNKNOWN")

    def test_duplicate_source_identity_is_not_a_new_physical_unit(self) -> None:
        rows = [
            {"StationUniqueId": "HUBTEST", "Id": "1"},
            {"StationUniqueId": "HUBTEST", "Id": "1"},
        ]
        self.assertEqual(classify_tfl_physical_relationship(rows), "SAME_UNIT_MULTI_SOURCE")

    def test_parent_aggregate_is_at_least_one_and_does_not_overwrite_children(self) -> None:
        child_values = [True, False, None]
        self.assertTrue(aggregate_at_least_one(child_values))
        self.assertEqual(child_values, [True, False, None])
        self.assertIsNone(aggregate_at_least_one([None, None]))

    def test_frozen_tfl_reclassification_is_non_executable(self) -> None:
        report = {
            "counts": {"toilet_row_count": 410},
            "proposal": {"proposed_operation_counts_after_model_guard": {"INSERT": 58, "SOURCE_LINK": 14, "ENRICHMENT": 14}},
            "reconciliation": {"model_review_rows": 328, "model_review_existing_facilities": 124, "unresolved_positional_or_model_cases": 338},
        }
        result = reclassify_frozen_tfl_operations(report)
        self.assertEqual(result["production_mutations"], 0)
        self.assertTrue(result["operations_not_executed"])
        self.assertEqual(result["operation_handling"]["INSERT"]["count"], 58)

    def test_unit_readiness_does_not_promote_same_location_multi_rows(self) -> None:
        rows = [
            {"StationUniqueId": "HUBTEST", "Id": "1", "toilet_location_description": "Ticket hall"},
            {"StationUniqueId": "HUBTEST", "Id": "2", "toilet_location_description": "Ticket hall"},
        ]
        row = {
            "stable_tfl_station_id": "HUBTEST",
            "stable_tfl_toilet_id": "1",
            "station_name": "Test Station",
            "station/public_location": "London, TfL station network",
            "toilet_location_description": "Ticket hall",
            "toilet_type": "MALE",
            "station_coordinates": {"latitude": 51.5, "longitude": -0.1},
            "positional_precision": STATION_LEVEL_PRECISION,
            "best_existing_candidate": None,
            "candidate_count": 0,
        }
        result = classify_insert_row(row, rows)
        self.assertEqual(result["classification"], "PHYSICAL_UNIT_AMBIGUOUS")
        self.assertFalse(result["unit_payload_safe"])

    def test_unit_readiness_does_not_invent_parent_from_station_coordinates(self) -> None:
        row = {
            "stable_tfl_station_id": "HUBTEST",
            "stable_tfl_toilet_id": "1",
            "station_name": "Test Station",
            "station/public_location": "London, TfL station network",
            "toilet_location_description": "Ticket hall",
            "toilet_type": "UNISEX",
            "station_coordinates": {"latitude": 51.5, "longitude": -0.1},
            "positional_precision": STATION_LEVEL_PRECISION,
            "best_existing_candidate": None,
            "candidate_count": 0,
        }
        result = classify_insert_row(row, [row])
        self.assertEqual(result["classification"], "OTHER_NO_GO")
        self.assertIsNone(result["parent_facility_id"])

    def test_unit_readiness_report_is_zero_mutation_and_json_safe(self) -> None:
        report = {
            "records": [],
            "counts": {"station_count": 0, "toilet_row_count": 0},
            "source": {
                "retrieval_utc": "2026-08-21T00:00:00Z",
                "source_url": "https://example.invalid/tfl.zip",
                "required_attribution": "Data provided by Transport for London",
                "terms_url": "https://example.invalid/terms",
            },
            "feed_schema_verification": {"stations_with_multiple_toilets": 0},
        }
        result = json_safe(build_readiness_package(report))
        self.assertEqual(result["readiness_classification"], READINESS_CLASSIFICATION)
        self.assertEqual(result["production_mutations"], 0)
        self.assertEqual(result["proposal_payloads"]["future_mutation_counts"]["facility_mutations"], 0)
        self.assertTrue(result["operations_not_executed"])
        self.assertFalse(result["tfl_promotion"])


if __name__ == "__main__":
    unittest.main()

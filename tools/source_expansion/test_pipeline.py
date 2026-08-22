from __future__ import annotations

import json
from pathlib import Path
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
from .tfl_human_adjudication import (
    BATCH_CLASSIFICATION,
    assert_adjudication_invariants,
    build_adjudication_package,
)
from .tfl_existing_parent_observation_audit import (
    AUDIT_CLASSIFICATION,
    ROW_OUTCOMES,
    assert_audit_invariants,
    build_audit_package,
    reproduce_cohort,
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

    def test_tfl_batch_one_reproduces_exact_frozen_9_plus_49_cohort(self) -> None:
        repository_root = Path(__file__).resolve().parents[2]
        frozen_path = repository_root / "tools/source_expansion/cache/tfl-detailed-2026-08-21/tfl-reconciliation.json"
        report = json.loads(frozen_path.read_text(encoding="utf-8"))
        package = build_adjudication_package(report, {
            "counts": {
                "facilities": 15620,
                "facility_sources": 15620,
                "import_runs": 5,
                "toilet_map_import_staging": 0,
                "toilet_units": 0,
                "toilet_unit_sources": 0,
            }
        })
        self.assertEqual(package["classification"], BATCH_CLASSIFICATION)
        self.assertEqual(package["scope"]["source_rows"], 58)
        self.assertEqual(len(package["new_parent_adjudications"]), 9)
        self.assertEqual(len(package["physical_unit_adjudications"]), 49)
        identities = [
            item["source_identity"]["source_record_id"]
            for item in package["new_parent_adjudications"] + package["physical_unit_adjudications"]
        ]
        self.assertEqual(len(identities), len(set(identities)))
        self.assertEqual(package["invariants"]["source_identity_duplicates"], 0)

    def test_tfl_batch_one_unresolved_rows_have_zero_operations_and_no_toilet_precision(self) -> None:
        repository_root = Path(__file__).resolve().parents[2]
        report = json.loads((repository_root / "tools/source_expansion/cache/tfl-detailed-2026-08-21/tfl-reconciliation.json").read_text(encoding="utf-8"))
        package = build_adjudication_package(report, {"counts": {
            "facilities": 15620, "facility_sources": 15620, "import_runs": 5,
            "toilet_map_import_staging": 0, "toilet_units": 0, "toilet_unit_sources": 0,
        }})
        assert_adjudication_invariants(package)
        self.assertEqual(package["approved_future_operations"]["counts"], {
            "facility_inserts": 0,
            "facility_source_links": 0,
            "toilet_unit_inserts": 0,
            "toilet_unit_source_links": 0,
        })
        self.assertTrue(all(
            row["decision"] == "STILL_UNRESOLVED"
            for row in package["new_parent_adjudications"] + package["physical_unit_adjudications"]
        ))
        self.assertTrue(all(
            row["source_fields"]["positional_precision"] == "STATION_LEVEL_ONLY; TOILET_COORDINATES_NOT_PROVIDED"
            for row in package["new_parent_adjudications"] + package["physical_unit_adjudications"]
        ))

    def test_tfl_batch_one_preserves_rows_without_gender_id_or_row_count_collapse(self) -> None:
        repository_root = Path(__file__).resolve().parents[2]
        report = json.loads((repository_root / "tools/source_expansion/cache/tfl-detailed-2026-08-21/tfl-reconciliation.json").read_text(encoding="utf-8"))
        package = build_adjudication_package(report, {"counts": {
            "facilities": 15620, "facility_sources": 15620, "import_runs": 5,
            "toilet_map_import_staging": 0, "toilet_units": 0, "toilet_unit_sources": 0,
        }})
        for topology in package["station_topologies"]:
            source_ids = [row["source_record_id"] for row in topology["source_rows"]]
            self.assertEqual(len(source_ids), len(set(source_ids)))
            self.assertEqual(topology["source_rows_to_physical_units"], {})
            self.assertIsNone(topology["proposed_physical_unit_count"])
        self.assertFalse(package["invariants"]["gender_only_unit_creation"])
        self.assertFalse(package["invariants"]["source_id_only_unit_creation"])
        self.assertFalse(package["invariants"]["row_count_only_unit_creation"])
        self.assertFalse(package["approved_future_operations"]["executable"])

    def test_tfl_existing_parent_audit_reproduces_28_entries_over_14_unique_rows(self) -> None:
        repository_root = Path(__file__).resolve().parents[2]
        readiness = json.loads((repository_root / "docs/data/RELIEF_TFL_TOILET_UNIT_PROMOTION_READINESS_2026-08-22.json").read_text(encoding="utf-8"))
        batch_1 = json.loads((repository_root / "docs/data/RELIEF_TFL_HUMAN_ADJUDICATION_BATCH_1_2026-08-22.json").read_text(encoding="utf-8"))
        cohort = reproduce_cohort(readiness, batch_1)
        self.assertEqual(cohort["operation_entries_total"], 28)
        self.assertEqual(cohort["source_link_operation_entries"], 14)
        self.assertEqual(cohort["enrichment_operation_entries"], 14)
        self.assertEqual(cohort["unique_source_rows"], 14)
        self.assertEqual(cohort["batch_1_overlap_count"], 0)
        self.assertEqual(cohort["new_parent_overlap_count"], 0)
        self.assertEqual(len({row["source_record_id"] for row in cohort["unique_rows"]}), 14)

    def test_tfl_existing_parent_observations_never_become_units(self) -> None:
        repository_root = Path(__file__).resolve().parents[2]
        readiness = json.loads((repository_root / "docs/data/RELIEF_TFL_TOILET_UNIT_PROMOTION_READINESS_2026-08-22.json").read_text(encoding="utf-8"))
        package = build_audit_package(readiness)
        self.assertEqual(package["classification"], AUDIT_CLASSIFICATION)
        self.assertEqual(package["row_classification_counts"], {
            "SAFE_FACILITY_LEVEL_OBSERVATION": 0,
            "SAFE_EXISTING_MODEL_MAPPING": 0,
            "REQUIRES_ADDITIVE_SOURCE_OBSERVATION_MODEL": 14,
            "STILL_UNRESOLVED": 0,
            "SOURCE_ROW_INVALID": 0,
        })
        self.assertEqual(package["proposed_future_operations"]["counts"]["toilet_unit_inserts"], 0)
        self.assertEqual(package["proposed_future_operations"]["counts"]["canonical_facility_enrichments"], 0)
        self.assertTrue(all(not row["physical_unit_asserted"] for row in package["rows"]))
        self.assertTrue(all(row["outcome"] in ROW_OUTCOMES for row in package["rows"]))
        assert_audit_invariants(package)

    def test_tfl_existing_parent_audit_preserves_station_coordinate_precision_and_provenance(self) -> None:
        repository_root = Path(__file__).resolve().parents[2]
        readiness = json.loads((repository_root / "docs/data/RELIEF_TFL_TOILET_UNIT_PROMOTION_READINESS_2026-08-22.json").read_text(encoding="utf-8"))
        package = build_audit_package(readiness)
        self.assertTrue(package["invariants"]["station_coordinates_station_level_only"])
        self.assertEqual(package["source"]["attribution"], "Data provided by Transport for London")
        self.assertTrue(package["proposed_future_operations"]["executable"] is False)
        self.assertEqual(package["production_safety"]["production_mutations"], 0)


if __name__ == "__main__":
    unittest.main()

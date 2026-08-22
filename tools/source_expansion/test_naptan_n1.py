import csv
import hashlib
import json
import tempfile
import unittest
from pathlib import Path

from tools.source_expansion.naptan_n1 import (
    EXPECTED_HEADERS,
    NaptanSourceError,
    RELIEF_PLACE_TYPES,
    STOP_TYPE_CLASSIFICATIONS,
    iter_rows,
    normalize_text,
    parse_row,
    sha256_file,
    source_identity,
)


FIXTURE = Path(__file__).parent / "fixtures" / "naptan_n1_sample.csv"
ARTIFACT_ROOT = Path(__file__).parents[2] / "docs" / "data"


class NaptanN1Tests(unittest.TestCase):
    def test_fixture_hash_and_row_identity_are_deterministic(self):
        first = sha256_file(FIXTURE)
        second = hashlib.sha256(FIXTURE.read_bytes()).hexdigest().upper()
        self.assertEqual(first, second)
        rows = list(iter_rows(FIXTURE))
        self.assertEqual([r["source_identity"] for r in rows], ["naptan:TEST000001", "naptan:TEST000002", "naptan:TEST000003"])
        self.assertEqual(rows[0]["common_name"], "Unicode — Stop")
        self.assertEqual(rows[0]["coordinate_scope"], "TRANSPORT_STOP_LEVEL")

    def test_replacement_character_fails_closed(self):
        with self.assertRaises(NaptanSourceError):
            normalize_text("Bad\ufffdvalue")

    def test_publisher_identity_is_not_row_position(self):
        row = {"ATCOCode": " abC123 ", **{h: "" for h in EXPECTED_HEADERS if h != "ATCOCode"}}
        self.assertEqual(source_identity(row), "naptan:ABC123")

    def test_duplicate_publisher_identity_is_detectable(self):
        rows = list(iter_rows(FIXTURE))
        duplicate = dict(rows[0])
        self.assertEqual(duplicate["source_identity"], rows[0]["source_identity"])
        self.assertNotEqual(duplicate["source_identity"], rows[1]["source_identity"])

    def test_stop_type_classification_is_explicit(self):
        self.assertEqual(STOP_TYPE_CLASSIFICATIONS["RLY"][0], "RELIEF_TRANSPORT_PLACE_CANDIDATE")
        self.assertEqual(STOP_TYPE_CLASSIFICATIONS["RSE"][0], "RELIEF_SUPPORTING_NODE")
        self.assertEqual(STOP_TYPE_CLASSIFICATIONS["BCT"][0], "RELIEF_SUPPORTING_NODE")
        self.assertNotIn("BCT", RELIEF_PLACE_TYPES)

    def test_multi_node_fixture_does_not_create_multiple_relief_facilities(self):
        rows = list(iter_rows(FIXTURE))
        same_name = [r for r in rows if r["normalized_name"].startswith("central rail")]
        self.assertEqual(len(same_name), 2)
        self.assertTrue(all(r["stop_type"] in {"RLY", "RSE"} for r in same_name))
        self.assertEqual(len({r["source_identity"] for r in same_name}), 2)
        self.assertEqual(len([r for r in same_name if r["stop_type"] in RELIEF_PLACE_TYPES]), 1)

    def test_coordinate_scope_is_not_toilet_scope(self):
        row = list(iter_rows(FIXTURE))[0]
        self.assertEqual(row["coordinate_scope"], "TRANSPORT_STOP_LEVEL")
        self.assertNotEqual(row["coordinate_scope"], "TOILET_LEVEL")

    def test_fixture_serialization_is_repeatable(self):
        def serialize():
            return json.dumps(list(iter_rows(FIXTURE)), sort_keys=True, ensure_ascii=False)
        self.assertEqual(serialize(), serialize())

    def test_no_production_mutation_path_is_exposed(self):
        source = Path(__file__).with_name("naptan_n1.py").read_text(encoding="utf-8")
        self.assertNotIn("supabase_execute_sql", source)
        self.assertNotIn("INSERT INTO", source.upper())
        self.assertNotIn("--apply", source)

    def test_generated_manifest_records_frozen_download_hash(self):
        manifest_path = ARTIFACT_ROOT / "NAPTAN_N1_SOURCE_MANIFEST_2026-08-22.json"
        self.assertTrue(manifest_path.exists())
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        self.assertEqual(manifest["sha256"], "FF981876B8442122E058634769F290F6E775F454D80D82B465491E2E5006D3C2")
        self.assertEqual(manifest["file_inventory"][0]["sha256"], manifest["sha256"])
        self.assertEqual(manifest["licence"]["name"], "Open Government Licence v3.0")

    def test_generated_profile_has_no_synthetic_hierarchy(self):
        profile = json.loads((ARTIFACT_ROOT / "NAPTAN_N1_SEMANTIC_PROFILE_2026-08-22.json").read_text(encoding="utf-8"))
        self.assertEqual(profile["duplicate_publisher_identity_rows"], 0)
        self.assertEqual(profile["hierarchy"]["stop_area_count"], None)
        self.assertEqual(profile["hierarchy"]["status"], "NOT_PRESENT_IN_RETRIEVED_NATIONAL_STOPS_CSV")

    def test_generated_dry_run_is_declarative_zero_mutation(self):
        dry_run = json.loads((ARTIFACT_ROOT / "NAPTAN_N1_RELIEF_DRY_RUN_2026-08-22.json").read_text(encoding="utf-8"))
        self.assertEqual(dry_run["facility_snapshot"], "tools/source_expansion/cache/tfl-detailed-2026-08-21/production-published-facilities.json")
        self.assertFalse(dry_run["production_mutation_plan"]["production_execution"])
        self.assertEqual(dry_run["production_mutation_plan"]["facilities_inserts"], 0)
        self.assertEqual(dry_run["production_mutation_plan"]["observations_inserts"], 0)


if __name__ == "__main__":
    unittest.main()

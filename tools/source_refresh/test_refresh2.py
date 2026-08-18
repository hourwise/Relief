"""Focused, offline tests for the governed Refresh 2 preparation boundary."""

from __future__ import annotations

import csv
import tempfile
import unittest
from pathlib import Path

from tools.enrichment.pipeline import ToiletMapAdapter
from tools.source_refresh.refresh2 import (
    build_operations,
    classify_source_snapshot,
    source_field_differences,
)


def source_row(source_id: str, *, name: str = "Central Toilet", latitude: str = "53.4", longitude: str = "-3.0", no_payment: str = "", accessible: str = "", opening_times: str = "") -> dict[str, str]:
    return {
        "id": source_id,
        "name": name,
        "latitude": latitude,
        "longitude": longitude,
        "active": "true",
        "areas": '{"name":"Liverpool"}',
        "no_payment": no_payment,
        "accessible": accessible,
        "radar": "",
        "baby_change": "",
        "all_gender": "",
        "opening_times": opening_times,
        "updated_at": "2026-08-18T00:00:00.000Z",
    }


class Refresh2Tests(unittest.TestCase):
    def test_same_snapshot_is_all_unchanged(self) -> None:
        rows = [source_row("same")]
        report = classify_source_snapshot(rows, rows)
        self.assertEqual(report["new_ids"], [])
        self.assertEqual(report["changed_ids"], [])
        self.assertEqual(report["unchanged_ids"], ["same"])
        self.assertTrue(report["counts_reconcile"])

    def test_new_changed_and_missing_are_distinct(self) -> None:
        previous = [source_row("same"), source_row("removed", name="Removed Toilet")]
        current = [source_row("same", name="Renamed Toilet"), source_row("new")]
        report = classify_source_snapshot(previous, current)
        self.assertEqual(report["new_ids"], ["new"])
        self.assertEqual(report["changed_ids"], ["same"])
        self.assertEqual(report["missing_ids"], ["removed"])
        self.assertEqual(report["quarantined_rows"], 0)

    def test_invalid_id_duplicate_id_and_invalid_coordinates(self) -> None:
        current = [source_row("", name="No ID"), source_row("dup"), source_row("dup"), source_row("bad", latitude="0", longitude="0")]
        report = classify_source_snapshot([], current)
        self.assertEqual(report["invalid_rows"], 2)
        self.assertEqual(report["duplicate_source_ids"], ["dup"])
        self.assertEqual(report["duplicate_source_id_rows"], 2)
        self.assertEqual(report["quarantined_rows"], 4)
        self.assertTrue(report["counts_reconcile"])

    def test_unknown_boolean_is_not_false_and_true_to_missing_is_a_diff(self) -> None:
        old = source_row("one", accessible="true")
        new = source_row("one", accessible="")
        differences = source_field_differences(old, new)
        self.assertEqual([(item["field"], item["old"], item["new"]) for item in differences if item["field"] == "is_accessible"], [("is_accessible", True, None)])
        self.assertIsNone(ToiletMapAdapter().read(self._csv([source_row("unknown")]))[0].is_accessible)

    def test_field_level_diff_includes_opening_hours_semantics(self) -> None:
        old = source_row("hours", opening_times='[["09:00","17:00"],[],[],[],[],[],[]]')
        new = source_row("hours", opening_times='[["10:00","18:00"],[],[],[],[],[],[]]')
        fields = source_field_differences(old, new)
        self.assertEqual(fields[0]["field"], "opening_hours")
        self.assertEqual(fields[0]["old"]["monday"], {"open": "09:00", "close": "17:00"})
        self.assertEqual(fields[0]["new"]["monday"], {"open": "10:00", "close": "18:00"})

    def test_exact_boolean_enrichment_is_safe_but_stronger_provenance_is_protected(self) -> None:
        candidates = ToiletMapAdapter().read(self._csv([source_row("linked", accessible="true")]))
        facility = {"id": "facility-1", "name": "Central Toilet", "town": "Liverpool", "latitude": 53.4, "longitude": -3.0, "is_accessible": None, "field_provenance": {}}
        link = {"facility_id": "facility-1", "source_name": "Toilet Map UK", "source_record_id": "linked"}
        safe = build_operations(candidates, [facility], [link], source_version="2026-08-18T01:00:00Z", source_checksum="abc")
        self.assertEqual(safe["operation_counts"], {"SAFE_CANDIDATE": 1})
        protected_facility = dict(facility, field_provenance={"is_accessible": {"source": "community-confirmed", "field": "is_accessible"}})
        protected = build_operations(candidates, [protected_facility], [link], source_version="2026-08-18T01:00:00Z", source_checksum="abc")
        self.assertEqual(protected["operation_counts"], {"PROTECTED": 1})

    def test_nearby_separate_facility_is_not_automatically_collapsed(self) -> None:
        candidates = ToiletMapAdapter().read(self._csv([source_row("new", name="Station Toilet", latitude="53.4001", longitude="-3.0001")]))
        facility = {"id": "facility-1", "name": "Library Toilet", "town": "Liverpool", "latitude": 53.4, "longitude": -3.0, "is_accessible": None, "field_provenance": {}}
        result = build_operations(candidates, [facility], [], source_version="2026-08-18T01:00:00Z", source_checksum="abc")
        self.assertEqual(result["new_facility_candidates"], 1)
        self.assertEqual(result["duplicate_collision_candidates"], [])
        self.assertEqual(result["canonical_mutations"], 0)

    def test_operation_identity_and_order_are_deterministic(self) -> None:
        rows = [source_row("b", accessible="true"), source_row("a", no_payment="true")]
        candidates = ToiletMapAdapter().read(self._csv(rows))
        facilities = [
            {"id": "facility-b", "name": "Central Toilet", "town": "Liverpool", "latitude": 53.4, "longitude": -3.0, "is_accessible": None, "is_free": None, "field_provenance": {}},
            {"id": "facility-a", "name": "Central Toilet", "town": "Liverpool", "latitude": 53.4, "longitude": -3.0, "is_accessible": None, "is_free": None, "field_provenance": {}},
        ]
        links = [{"facility_id": "facility-b", "source_name": "Toilet Map UK", "source_record_id": "b"}, {"facility_id": "facility-a", "source_name": "Toilet Map UK", "source_record_id": "a"}]
        first = build_operations(candidates, facilities, links, source_version="v", source_checksum="abc")
        second = build_operations(candidates, facilities, links, source_version="v", source_checksum="abc")
        self.assertEqual(first["operations"], second["operations"])
        self.assertEqual([item["source_record_id"] for item in first["operations"]], ["a", "b"])
        self.assertEqual(first["canonical_mutations"], 0)

    @staticmethod
    def _csv(rows: list[dict[str, str]]) -> Path:
        directory = Path(tempfile.mkdtemp())
        path = directory / "source.csv"
        with path.open("w", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, fieldnames=sorted(rows[0]))
            writer.writeheader()
            writer.writerows(rows)
        return path


if __name__ == "__main__":
    unittest.main()

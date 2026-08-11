#!/usr/bin/env python3
"""Synthetic tests for the read-only enrichment foundation."""

from __future__ import annotations

import csv
import json
import tempfile
import unittest
from pathlib import Path

try:
    from .pipeline import (
        NormalizedCandidate,
        ToiletMapAdapter,
        field_differences,
        match_candidate,
        build_facility_index,
        reconcile,
    )
except ImportError:  # Supports direct execution: python tools/enrichment/test_pipeline.py
    from pipeline import (
        NormalizedCandidate,
        ToiletMapAdapter,
        field_differences,
        match_candidate,
        build_facility_index,
        reconcile,
    )


def candidate(**overrides):
    values = {
        "source_name": "Toilet Map UK",
        "source_record_id": "source-1",
        "source_url": None,
        "source_licence": "CC BY 4.0",
        "source_updated_at": "2026-08-11T00:00:00Z",
        "name": "Central Toilet",
        "address": None,
        "town": "Testtown",
        "postcode": None,
        "latitude": 53.0,
        "longitude": -2.0,
        "opening_hours": None,
        "is_free": None,
        "is_accessible": None,
        "requires_radar_key": None,
        "has_baby_changing": None,
        "is_gender_neutral": None,
        "is_family_friendly": None,
        "has_staff_nearby": None,
        "other_fields": {},
        "raw_hash": "hash",
        "source_status": "active",
        "validation_errors": [],
        "quality_warnings": [],
    }
    values.update(overrides)
    return NormalizedCandidate(**values)


class EnrichmentFoundationTests(unittest.TestCase):
    def setUp(self):
        self.facility = {
            "id": "facility-1",
            "name": "Central Toilet",
            "address": "High Street",
            "town": "Testtown",
            "postcode": "TE1 1AA",
            "latitude": 53.0,
            "longitude": -2.0,
            "open_hours": None,
            "is_free": None,
            "is_accessible": True,
            "requires_radar_key": None,
            "has_baby_changing": None,
            "is_gender_neutral": None,
            "is_family_friendly": None,
            "has_staff_nearby": None,
        }

    def test_toilet_map_adapter_preserves_unknowns_and_source_fields(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "input.csv"
            fieldnames = ["id", "active", "name", "areas", "latitude", "longitude", "opening_times", "no_payment", "accessible", "all_gender", "children", "updated_at"]
            with path.open("w", newline="", encoding="utf-8") as handle:
                writer = csv.DictWriter(handle, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerow({
                    "id": "a",
                    "active": "true",
                    "name": "Example",
                    "areas": json.dumps({"name": "Testtown"}),
                    "latitude": "53.0",
                    "longitude": "-2.0",
                    "opening_times": json.dumps([["09:00", "17:00"], [], ["10:00", "16:00"], [], [], [], []]),
                    "no_payment": "",
                    "accessible": "false",
                    "all_gender": "true",
                    "children": "true",
                    "updated_at": "2026-08-11T00:00:00Z",
                })
            parsed = ToiletMapAdapter().read(path)[0]
        self.assertIsNone(parsed.is_free)
        self.assertFalse(parsed.is_accessible)
        self.assertTrue(parsed.is_gender_neutral)
        self.assertIsNone(parsed.is_family_friendly)
        self.assertEqual(parsed.town, "Testtown")
        self.assertEqual(parsed.opening_hours["monday"], {"open": "09:00", "close": "17:00"})
        self.assertNotIn("tuesday", parsed.opening_hours)
        self.assertTrue(parsed.other_fields["children"])

    def test_exact_source_id_is_strongest_match(self):
        current = {"facility-1": self.facility}
        links = {"source-1": [{"facility_id": "facility-1"}]}
        decision = match_candidate(candidate(source_record_id="source-1", latitude=50.0, longitude=0.0), current, links, build_facility_index(current.values()))
        self.assertEqual(decision.decision, "EXACT_SOURCE_ID")
        self.assertEqual(decision.facility_id, "facility-1")

    def test_high_confidence_match_requires_name_and_distance(self):
        current = {"facility-1": self.facility}
        decision = match_candidate(candidate(source_record_id="unseen", latitude=53.0002, longitude=-2.0001), current, {}, build_facility_index(current.values()))
        self.assertEqual(decision.decision, "HIGH_CONFIDENCE_MATCH")

    def test_ambiguous_match_is_not_auto_selected(self):
        second = dict(self.facility, id="facility-2", latitude=53.00035, longitude=-2.00005)
        current = {"facility-1": self.facility, "facility-2": second}
        decision = match_candidate(candidate(source_record_id="unseen", latitude=53.0002, longitude=-2.0001), current, {}, build_facility_index(current.values()))
        self.assertEqual(decision.decision, "AMBIGUOUS")
        self.assertIsNone(decision.facility_id)

    def test_likely_new_is_conservative(self):
        current = {"facility-1": self.facility}
        decision = match_candidate(candidate(source_record_id="new", name="Riverside Pavilion", latitude=53.1, longitude=-2.1), current, {}, build_facility_index(current.values()))
        self.assertEqual(decision.decision, "LIKELY_NEW")

    def test_invalid_record_is_not_invented(self):
        current = {"facility-1": self.facility}
        bad = candidate(source_record_id="bad", name=None, latitude=None, longitude=None, validation_errors=["invalid latitude/longitude"])
        decision = match_candidate(bad, current, {}, build_facility_index(current.values()))
        self.assertEqual(decision.decision, "INVALID_SOURCE_RECORD")

    def test_field_differences_preserve_unknown_and_conflict_categories(self):
        source = candidate(is_free=True, is_accessible=False, opening_hours={"monday": {"open": "09:00", "close": "17:00"}})
        diff = field_differences(source, self.facility)
        self.assertIn("is_free", [item["field"] for item in diff["enrichment"]])
        self.assertIn("opening_hours", [item["field"] for item in diff["enrichment"]])
        self.assertIn("is_accessible", [item["field"] for item in diff["conflicts"]])
        self.assertIn("address", [item["field"] for item in diff["omissions"]])

    def test_opening_hours_source_adds_one_day(self):
        self.facility["open_hours"] = {"monday": {"open": "09:00", "close": "17:00"}}
        source = candidate(opening_hours={
            "monday": {"open": "09:00", "close": "17:00"},
            "tuesday": {"open": "09:00", "close": "17:00"},
        })
        diff = field_differences(source, self.facility)
        self.assertEqual(diff["enrichment"][0]["added_days"], ["tuesday"])
        self.assertEqual(diff["conflicts"], [])
        self.assertEqual([item for item in diff["omissions"] if item["field"] == "opening_hours"], [])

    def test_opening_hours_conflict_is_day_level(self):
        self.facility["open_hours"] = {"monday": {"open": "09:00", "close": "17:00"}}
        source = candidate(opening_hours={"monday": {"open": "10:00", "close": "17:00"}})
        diff = field_differences(source, self.facility)
        self.assertEqual(diff["conflicts"][0]["conflicting_days"], ["monday"])

    def test_opening_hours_source_omits_relief_day(self):
        self.facility["open_hours"] = {
            "monday": {"open": "09:00", "close": "17:00"},
            "tuesday": {"open": "09:00", "close": "17:00"},
        }
        source = candidate(opening_hours={"monday": {"open": "09:00", "close": "17:00"}})
        diff = field_differences(source, self.facility)
        opening_omissions = [item for item in diff["omissions"] if item["field"] == "opening_hours"]
        self.assertEqual(opening_omissions[0]["omitted_days"], ["tuesday"])

    def test_opening_hours_identical_partial_schedule_is_same(self):
        hours = {"monday": {"open": "09:00", "close": "17:00"}}
        self.facility["open_hours"] = hours
        diff = field_differences(candidate(opening_hours=hours), self.facility)
        self.assertIn("opening_hours", diff["same"])
        self.assertEqual(diff["enrichment"], [])
        self.assertEqual(diff["conflicts"], [])
        self.assertEqual([item for item in diff["omissions"] if item["field"] == "opening_hours"], [])

    def test_opening_hours_relief_empty_source_known_is_enrichment(self):
        source = candidate(opening_hours={"monday": {"open": "09:00", "close": "17:00"}})
        diff = field_differences(source, self.facility)
        self.assertEqual(diff["enrichment"][0]["field"], "opening_hours")

    def test_malformed_source_hours_remain_unknown(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "malformed.csv"
            fieldnames = ["id", "active", "name", "latitude", "longitude", "opening_times"]
            with path.open("w", newline="", encoding="utf-8") as handle:
                writer = csv.DictWriter(handle, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerow({
                    "id": "malformed",
                    "active": "true",
                    "name": "Example",
                    "latitude": "53.0",
                    "longitude": "-2.0",
                    "opening_times": "not-json",
                })
            parsed = ToiletMapAdapter().read(path)[0]
        self.assertIsNone(parsed.opening_hours)
        self.assertIn("opening_times present but not a usable seven-day time array", parsed.quality_warnings)

    def test_removed_and_missing_source_records_are_reported_without_mutation_path(self):
        removed = candidate(source_record_id="source-1", source_status="removed")
        source_links = [
            {"source_name": "Toilet Map UK", "source_record_id": "source-1", "facility_id": "facility-1", "is_current": True},
            {"source_name": "Toilet Map UK", "source_record_id": "source-missing", "facility_id": "facility-1", "is_current": True},
        ]
        report = reconcile([removed], [self.facility], source_links, {"facility_count": 1}, {"canonical_name": "Toilet Map UK"}, {"generated_at": "now"})
        self.assertEqual(report["summary"]["upstream_removed_inactive_records"], 1)
        self.assertEqual(report["summary"]["previously_linked_relief_records_absent_upstream"], 1)

    def test_dry_run_has_no_mutating_http_method(self):
        for filename in ("dry_run.py", "review.py"):
            source = Path(__file__).with_name(filename).read_text(encoding="utf-8")
            if filename == "dry_run.py":
                self.assertIn('method="GET"', source)
            self.assertNotIn('method="POST"', source)
            self.assertNotIn('method="PATCH"', source)
            self.assertNotIn('method="PUT"', source)
            self.assertNotIn('method="DELETE"', source)
            self.assertNotIn("supabase_execute", source)
            self.assertNotIn("apply_migration", source)


if __name__ == "__main__":
    unittest.main()

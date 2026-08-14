#!/usr/bin/env python3
"""Fixture tests for source registry, snapshots, and review diffs."""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from .framework import diff_records, load_registry, snapshot_bytes


ROOT = Path(__file__).resolve().parents[2]


class SourceRefreshTests(unittest.TestCase):
    def test_registry_contains_required_current_and_template_entries(self) -> None:
        registry = load_registry(ROOT / "tools/source_refresh/source_registry.json")
        self.assertEqual(set(registry), {
            "toilet_map_uk",
            "council_changing_places_ogl",
            "tfl_toilet_accessibility",
            "council_toilets_ogl_template",
        })
        self.assertEqual(registry["toilet_map_uk"]["current_status"], "CURRENT_SOURCE_READY")
        self.assertTrue(registry["tfl_toilet_accessibility"]["source_url"] is None)

    def test_snapshot_is_content_addressed_and_immutable(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            metadata = snapshot_bytes(
                b"id,name\n1,Central\n",
                "fixture",
                Path(directory),
                retrieved_at="2026-08-14T00:00:00Z",
                source_file_or_api_version="fixture-v1",
                parser_normalizer_version="test-v1",
            )
            self.assertTrue(metadata["immutable"])
            self.assertEqual(metadata["last_seen_at"], "2026-08-14T00:00:00Z")
            self.assertEqual(metadata["current_status"], "CURRENT")
            self.assertEqual(metadata["checksum"], "c124acba5606f50c288e1bbcb34afec855c648f1a8672644a6927e3eb655563f")

    def test_diff_reports_new_missing_changed_duplicates_and_zero_mutations(self) -> None:
        report = diff_records(
            [{"id": "old", "name": "Old"}, {"id": "same", "name": "Same"}],
            [
                {"id": "same", "name": "Changed"},
                {"id": "new", "name": "New"},
                {"id": "new", "name": "Duplicate"},
            ],
        )
        self.assertEqual(report["new"], ["new"])
        self.assertEqual(report["missing_or_stale"], ["old"])
        self.assertEqual(report["changed"], ["same"])
        self.assertEqual(report["duplicate_ids"], ["current:new"])
        self.assertEqual(report["record_status"]["old"], "STALE_OR_MISSING")
        self.assertEqual(report["record_status"]["same"], "CHANGED")
        self.assertEqual(report["record_status"]["new"], "NEW")
        self.assertEqual(report["canonical_mutations"], 0)
        self.assertTrue(report["review_required"])


if __name__ == "__main__":
    unittest.main()

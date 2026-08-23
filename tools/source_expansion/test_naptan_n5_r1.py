"""Small deterministic count-semantics tests for N5-R1."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from tools.source_expansion.naptan_n5_r1 import (
    direct_element_counter,
    independent_key_counter,
    schema_static_audit,
)


FIXTURE = """<?xml version="1.0" encoding="UTF-8"?>
<NaPTAN xmlns="http://www.naptan.org.uk/">
  <StopPoints>
    <StopPoint><AtcoCode>NODE-A</AtcoCode><StopAreas><StopAreaRef>AREA-1</StopAreaRef><StopAreaRef>AREA-1</StopAreaRef><StopAreaRef>MISSING</StopAreaRef></StopAreas></StopPoint>
    <StopPoint><AtcoCode>NODE-B</AtcoCode><StopAreas><StopAreaRef>MISSING</StopAreaRef></StopAreas></StopPoint>
    <StopPoint><AtcoCode>NODE-C</AtcoCode><StopAreas><StopAreaRef>AREA-1</StopAreaRef><StopAreaRef>AREA-2</StopAreaRef></StopAreas></StopPoint>
  </StopPoints>
  <StopAreas>
    <StopArea><StopAreaCode>AREA-1</StopAreaCode><ParentStopAreaRef>MISSING-PARENT</ParentStopAreaRef><ParentStopAreaRef>MISSING-PARENT</ParentStopAreaRef></StopArea>
    <StopArea><StopAreaCode>AREA-2</StopAreaCode><ParentStopAreaRef>MISSING-PARENT</ParentStopAreaRef></StopArea>
  </StopAreas>
</NaPTAN>
"""


class NaptanN5R1Tests(unittest.TestCase):
    def with_fixture(self):
        handle = tempfile.NamedTemporaryFile(suffix=".xml", delete=False)
        handle.write(FIXTURE.encode("utf-8"))
        handle.close()
        self.addCleanup(lambda: Path(handle.name).unlink(missing_ok=True))
        return Path(handle.name)

    def test_raw_unique_duplicate_arithmetic_and_unresolved_identity_semantics(self):
        path = self.with_fixture()
        direct = direct_element_counter(path)
        keyed = independent_key_counter(path)
        self.assertEqual(direct["publisher_membership_element_count"], 6)
        self.assertEqual(keyed["publisher_membership_element_count"], 6)
        self.assertEqual(keyed["unique_membership_key_count"], 5)
        self.assertEqual(keyed["duplicate_membership_extra_occurrence_count"], 1)
        self.assertEqual(keyed["stored_membership_row_count"], 5)
        self.assertEqual(keyed["unresolved_membership_edge_count"], 2)
        self.assertEqual(keyed["distinct_missing_member_parent_identity_count"], 1)
        self.assertEqual(keyed["missing_member_parent_identity_frequency"]["naptan-stop-area:MISSING"], 2)
        self.assertEqual(keyed["publisher_membership_element_count"], keyed["unique_membership_key_count"] + keyed["duplicate_membership_extra_occurrence_count"])

    def test_parent_edge_arithmetic_and_unresolved_identity_semantics(self):
        keyed = independent_key_counter(self.with_fixture())
        self.assertEqual(keyed["publisher_parent_element_count"], 3)
        self.assertEqual(keyed["unique_parent_edge_count"], 2)
        self.assertEqual(keyed["stored_parent_row_count"], 2)
        self.assertEqual(keyed["duplicate_parent_extra_occurrence_count"], 1)
        self.assertEqual(keyed["unresolved_parent_edge_count"], 2)
        self.assertEqual(keyed["distinct_missing_area_parent_identity_count"], 1)
        self.assertEqual(keyed["missing_area_parent_identity_frequency"]["naptan-stop-area:MISSING-PARENT"], 2)
        self.assertEqual(keyed["publisher_parent_element_count"], keyed["unique_parent_edge_count"] + keyed["duplicate_parent_extra_occurrence_count"])

    def test_schema_audit_preserves_sealed_migration(self):
        repo_root = Path(__file__).parents[2]
        audit = schema_static_audit(repo_root)
        self.assertEqual(audit["classification"], "N4A_SCHEMA_SUPPORTS_CORRECTED_COUNTS")
        self.assertTrue(audit["sealed_hash_exact"])
        self.assertTrue(all(audit["checks"].values()))


if __name__ == "__main__":
    unittest.main()

"""Unit tests for the N5-R2 plan/apply guard (no database access)."""

from __future__ import annotations

import unittest
from pathlib import Path

from tools.source_expansion.naptan_n5_r2 import (
    EXPECTED_BASE_URL,
    EXPECTED_VALUES,
    N5R2Error,
    RestClient,
    _semantically_equal,
    load_contract,
    plan_summary,
    snapshot_payload,
)


ROOT = Path(__file__).resolve().parents[2]
CONTRACT = ROOT / "docs/data/NAPTAN_N5_R1_CORRECTED_INGESTION_CONTRACT_2026-08-23.json"


class NaptanN5R2Tests(unittest.TestCase):
    def test_authoritative_corrected_contract_is_loaded(self) -> None:
        contract = load_contract(CONTRACT)
        self.assertEqual(contract["values"]["stored_membership_row_count"], 169_527)
        self.assertNotEqual(contract["values"]["stored_membership_row_count"], 169_524)

    def test_snapshot_identity_and_contract_metadata_are_deterministic(self) -> None:
        model = {
            "source_snapshot_key": "naptan:sha256:abc",
            "source_url": "https://naptan.api.dft.gov.uk/v1/access-nodes?dataFormat=xml",
            "values": {"publisher_membership_element_count": 169_530},
        }
        row = snapshot_payload(model)
        self.assertEqual(row["source_namespace"], "naptan")
        self.assertEqual(row["source_checksum_sha256"], "6fc7e40e2af3b30e9fd117bdac313b58f3385bff26517fd78d5554da12b4183a")
        self.assertEqual(row["ingestion_state"], "CAPTURED")
        self.assertEqual(row["row_counts"]["contract_version"], "N5-R1-2026-08-23")

    def test_database_float_round_trip_is_tolerated_but_not_material_difference(self) -> None:
        self.assertTrue(_semantically_equal(51.520387323967256, 51.5203873239673))
        self.assertFalse(_semantically_equal(51.520387323967256, 51.520387323))

    def test_rest_client_rejects_non_allowlisted_tables(self) -> None:
        client = RestClient(EXPECTED_BASE_URL, "test-key")
        with self.assertRaises(N5R2Error):
            client._url("facilities")

    def test_plan_summary_requires_explicit_apply(self) -> None:
        model = {
            "source": {"exact": True},
            "contract_version": "N5-R1-2026-08-23",
            "source_snapshot_key": "naptan:sha256:abc",
            "source_url": "https://example.invalid",
            "retrieved_at": "2026-08-22T00:00:00Z",
            "licence": "Open Government Licence v3.0",
            "attribution": "Contains public sector information licensed under the Open Government Licence v3.0.",
            "parser_version": "test",
            "values": {"total_stored_source_graph_rows": EXPECTED_VALUES["total_stored_source_graph_rows"]},
            "mode_distribution": {},
            "complex_type_distribution": {},
            "duplicate_membership_keys": [],
            "duplicate_membership_counts": {},
            "n3_projection": {},
            "expected_counts": {},
        }
        summary = plan_summary(model, {table: 0 for table in ("transport_source_snapshots", "transport_source_places", "transport_source_nodes", "transport_source_memberships", "transport_source_place_parents")})
        self.assertTrue(summary["apply_required"])
        self.assertEqual(summary["production_mutations_in_plan"], 0)
        self.assertTrue(summary["superseded_membership_expectation_not_used"])


if __name__ == "__main__":
    unittest.main()

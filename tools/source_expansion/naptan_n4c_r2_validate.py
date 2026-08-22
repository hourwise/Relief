"""Fail-closed offline validation for N4C-R2 evidence.

This validator reads repository evidence only. It does not connect to
Supabase, execute SQL, repair migrations, or apply migrations.
"""

from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / "docs" / "data"
MIGRATIONS = ROOT / "supabase" / "migrations"
N4A = MIGRATIONS / "20260822170000_naptan_transport_source_graph.sql"
EXPECTED_N4A = "087A389B8CEAC021B12708BC55C39022CB38D5459510EFFB6CF057CEF232C44E"
PAIRS = {
    "20260814115817": "20260814113440",
    "20260816210130": "20260816205543",
    "20260817062603": "20260816220000",
    "20260821213435": "20260821211239",
    "20260822100920": "20260822092938",
}


def read_json(name: str) -> dict:
    return json.loads((DATA / name).read_text(encoding="utf-8"))


def main() -> None:
    assert hashlib.sha256(N4A.read_bytes()).hexdigest().upper() == EXPECTED_N4A

    plan = read_json("NAPTAN_N4C_R2_REPAIR_COMMANDS_2026-08-22.json")
    assert plan["operation_count"] == 10
    assert plan["excluded_versions"] == ["20260814135046", "20260822170000"]
    assert plan["expected_schema_delta"] == 0
    assert plan["expected_application_data_delta"] == 0
    assert all(pair["production_version"] in PAIRS for pair in plan["approved_pairs"])
    assert all(command["version"] in PAIRS or command["version"] in PAIRS.values() for command in plan["commands"])

    execution = read_json("NAPTAN_N4C_R2_EXECUTION_EVIDENCE_2026-08-22.json")
    assert execution["commands_executed"] == 10
    assert execution["successful_commands"] == 10
    assert execution["failed_commands"] == 0
    assert execution["exit_codes"] == [0] * 10
    assert execution["schema_mutations"] == 0
    assert execution["application_data_mutations"] == 0
    assert execution["auth_mutations"] == 0
    assert execution["naptan_ingestion_rows"] == 0

    pre = read_json("NAPTAN_N4C_R2_PRE_REPAIR_LEDGER_2026-08-22.json")
    post = read_json("NAPTAN_N4C_R2_POST_REPAIR_LEDGER_2026-08-22.json")
    assert pre["n4a_present"] is False
    assert post["n4a_present"] is False
    assert post["only_local_only_version"] == "20260822170000"
    assert post["all_local_historical_versions_aligned"] is True

    diff = read_json("NAPTAN_N4C_R2_LEDGER_DIFF_2026-08-22.json")
    assert len(diff["changed_pairs"]) == 5
    assert diff["n4a"]["before"] == "absent"
    assert diff["n4a"]["after"] == "absent"
    assert diff["schema_delta"] == 0
    assert diff["application_data_delta"] == 0

    immutability = read_json("NAPTAN_N4C_R2_PRODUCTION_IMMUTABILITY_2026-08-22.json")
    assert immutability["counts_before"] == immutability["counts_after"]
    assert all(value == 0 for value in immutability["count_deltas"].values())
    assert immutability["n4a_tables_before"] == [] and immutability["n4a_tables_after"] == []

    security = read_json("NAPTAN_N4C_R2_SECURITY_IMMUTABILITY_2026-08-22.json")
    assert security["rls_before_after_equal"] is True
    assert security["policies_before_after_equal"] is True
    assert security["account_functions_before_after_equal"] is True
    assert security["security_mutations"] == 0

    dry_run = read_json("NAPTAN_N4C_R2_DRY_RUN_EVIDENCE_2026-08-22.json")
    assert dry_run["exit_code"] == 0
    assert dry_run["pending_migrations"] == ["20260822170000_naptan_transport_source_graph.sql"]
    assert dry_run["only_n4a_pending"] is True
    assert dry_run["n4a_applied"] is False

    isolation = read_json("NAPTAN_N4C_R2_N4A_ISOLATION_2026-08-22.json")
    assert isolation["classification"] == "ONLY_N4A_PENDING_PROVEN"
    assert isolation["sha256"] == EXPECTED_N4A

    readiness = read_json("NAPTAN_N4C_R2_READINESS_2026-08-22.json")
    assert readiness["classification"] == "N4C_PRODUCTION_SCHEMA_APPLY_READY_FOR_SEPARATE_AUTHORIZATION"
    assert readiness["n4c_authorized"] is False
    assert readiness["n5_authorized"] is False

    versions = []
    names = []
    for migration in sorted(MIGRATIONS.glob("*.sql")):
        match = re.match(r"^(\d+)_([^.]+)\.sql$", migration.name)
        assert match, migration.name
        versions.append(match.group(1))
        names.append(match.group(2))
    assert len(versions) == len(set(versions))
    assert len(names) == len(set(names))
    assert "20260822170000" in versions
    assert "20260814135046" in versions
    assert "20260814124706" not in versions

    print("N4C-R2 validation passed: ten repairs, zero schema/data effects, and exactly one N4A dry-run migration.")


if __name__ == "__main__":
    main()

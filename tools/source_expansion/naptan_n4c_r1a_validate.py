"""Fail-closed offline validation for N4C-R1A repository canonicalisation.

This validator reads repository files only. It never connects to Supabase and
contains no migration-repair, migration-push, SQL-write, or production path.
"""

from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
MIGRATIONS = ROOT / "supabase" / "migrations"
DATA = ROOT / "docs" / "data"
N4A = MIGRATIONS / "20260822170000_naptan_transport_source_graph.sql"
ACCOUNT_V2 = MIGRATIONS / "20260814135046_account_deletion_cleanup_contract.sql"
ACCOUNT_V1 = MIGRATIONS / "20260814124706_account_deletion_cleanup_contract.sql"
ACCOUNT_V1_EVIDENCE = DATA / "NAPTAN_N4C_R1A_SUPERSEDED_ACCOUNT_MIGRATION_V1_2026-08-22.sql"

SEALED_N4A_SHA256 = "087A389B8CEAC021B12708BC55C39022CB38D5459510EFFB6CF057CEF232C44E"
ACCOUNT_V1_SHA256 = "854C2ECD3F1EB9A43809710CF7887375BD02DB7FA4A0A98A868303743D27627F"
ACCOUNT_PRODUCTION_STATEMENT_MD5 = "86accd93b46b873626465a9025e7d33c"
ACCOUNT_PRODUCTION_STATEMENT_SHA256 = "432d61cc4784f741d9c09c3a905cdd84a9d17244dfb5231fd87e3a8a4c32df0a"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest().upper()


def body_without_terminal_newline(path: Path) -> bytes:
    content = path.read_bytes()
    return content[:-1] if content.endswith(b"\n") else content


def read_json(name: str) -> dict:
    return json.loads((DATA / name).read_text(encoding="utf-8"))


def main() -> None:
    assert sha256(N4A) == SEALED_N4A_SHA256
    assert not ACCOUNT_V1.exists()
    assert ACCOUNT_V1_EVIDENCE.exists()
    assert sha256(ACCOUNT_V1_EVIDENCE) == ACCOUNT_V1_SHA256
    assert ACCOUNT_V1_EVIDENCE.stat().st_size == 7026

    account_body = body_without_terminal_newline(ACCOUNT_V2)
    assert hashlib.md5(account_body).hexdigest() == ACCOUNT_PRODUCTION_STATEMENT_MD5
    assert hashlib.sha256(account_body).hexdigest() == ACCOUNT_PRODUCTION_STATEMENT_SHA256
    account_text = ACCOUNT_V2.read_text(encoding="utf-8")
    assert account_text.count("'20260814.1'") == 0
    assert account_text.count("'20260814.2'") == 2

    versions = []
    names = []
    for migration in sorted(MIGRATIONS.glob("*.sql")):
        match = re.match(r"^(\d+)_([^.]+)\.sql$", migration.name)
        assert match, migration.name
        versions.append(match.group(1))
        names.append(match.group(2))
    assert len(versions) == 18
    assert len(versions) == len(set(versions))
    assert len(names) == len(set(names))
    assert "20260814124706" not in versions
    assert "20260814135046" in versions
    assert "20260822170000" in versions

    matrix = read_json("NAPTAN_N4C_R1_MIGRATION_MISMATCH_MATRIX_2026-08-22.json")
    settled = {row["production_version"]: row["classification"] for row in matrix["rows"]}
    assert settled["20260814115817"] == "EXACT_EQUIVALENT_LOCAL_MIGRATION"
    assert settled["20260816210130"] == "SEMANTICALLY_EQUIVALENT_LOCAL_MIGRATION"
    assert settled["20260817062603"] == "EXACT_EQUIVALENT_LOCAL_MIGRATION"
    assert settled["20260821213435"] == "SEMANTICALLY_EQUIVALENT_LOCAL_MIGRATION"
    assert settled["20260822100920"] == "SEMANTICALLY_EQUIVALENT_LOCAL_MIGRATION"

    canonical = read_json("NAPTAN_N4C_R1A_CANONICALISATION_DECISION_2026-08-22.json")
    assert canonical["repository_canonicalisation"] == "REPOSITORY_MIGRATION_HISTORY_CANONICALISED"
    assert canonical["historical_lineage"] == "LOCAL_V1_SUPERSEDED_BY_PRODUCTION_V2"

    isolation = read_json("NAPTAN_N4C_R1A_N4A_ISOLATION_2026-08-22.json")
    assert isolation["classification"] == "ONLY_N4A_PENDING_AFTER_LEDGER_REPAIR"
    assert isolation["sealed_n4a_sha256"] == SEALED_N4A_SHA256

    repair = read_json("NAPTAN_N4C_R1A_FUTURE_LEDGER_REPAIR_PLAN_2026-08-22.json")
    assert repair["commands_executed"] == []
    assert repair["production_mutations"] == 0
    assert repair["migration_ledger_mutations"] == 0
    assert all(command["execute"] is False for command in repair["commands"])

    print("N4C-R1A validation passed: exact v2 body, preserved v1, unique active inventory, five settled aliases, and N4A isolation model.")


if __name__ == "__main__":
    main()

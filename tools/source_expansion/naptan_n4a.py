"""Read-only N4A schema/replay contract helpers.

This module validates declarative NaPTAN snapshot fixtures and the candidate
SQL migration. It has no Supabase client, no apply flag, and no production
mutation path.
"""

from __future__ import annotations

import hashlib
import json
import re
from collections import defaultdict
from pathlib import Path
from typing import Any


MIGRATION_PATH = Path(__file__).parents[2] / "supabase" / "migrations" / "20260822170000_naptan_transport_source_graph.sql"
ALLOWED_SNAPSHOT_STATES = {"CAPTURED", "VALIDATING", "VALIDATED", "INGESTED", "FAILED", "SUPERSEDED"}
EXPECTED_TABLES = {
    "transport_source_snapshots",
    "transport_source_places",
    "transport_source_nodes",
    "transport_source_memberships",
    "transport_source_place_parents",
}


class NaptanN4AError(ValueError):
    pass


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest().upper()


def stable_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def source_snapshot_key(source_namespace: str, checksum_sha256: str) -> str:
    namespace = source_namespace.strip()
    checksum = checksum_sha256.strip().lower()
    if not namespace or not re.fullmatch(r"[0-9a-f]{64}", checksum):
        raise NaptanN4AError("snapshot namespace/checksum is invalid")
    return f"{namespace}:sha256:{checksum}"


def publisher_identity(namespace: str, publisher_id: str, kind: str) -> str:
    value = publisher_id.strip().upper()
    if not value:
        raise NaptanN4AError("publisher identity is empty")
    if kind == "STOP_AREA":
        return f"{namespace}:stop-area:{value}"
    if kind == "STOP_POINT":
        return f"{namespace}:stop-point:{value}"
    raise NaptanN4AError(f"unsupported publisher kind {kind!r}")


def membership_key(node_identity: str, place_identity: str) -> str:
    if not node_identity or not place_identity:
        raise NaptanN4AError("membership identities are required")
    return f"{node_identity}|{place_identity}"


def parent_edge_key(child_identity: str, parent_identity: str) -> str:
    if not child_identity or not parent_identity:
        raise NaptanN4AError("parent edge identities are required")
    return f"{child_identity}|{parent_identity}"


def validate_snapshot(snapshot: dict[str, Any]) -> dict[str, Any]:
    metadata = snapshot.get("metadata", {})
    namespace = str(metadata.get("source_namespace", "")).strip()
    checksum = str(metadata.get("source_checksum_sha256", "")).strip().lower()
    key = source_snapshot_key(namespace, checksum)
    if metadata.get("source_snapshot_key") != key:
        raise NaptanN4AError("source_snapshot_key is not deterministic")
    if metadata.get("ingestion_state", "CAPTURED") not in ALLOWED_SNAPSHOT_STATES:
        raise NaptanN4AError("invalid snapshot lifecycle state")
    places = snapshot.get("places", [])
    nodes = snapshot.get("nodes", [])
    memberships = snapshot.get("memberships", [])
    parents = snapshot.get("parents", [])
    place_ids = [row["publisher_identity"] for row in places]
    node_ids = [row["publisher_identity"] for row in nodes]
    if len(place_ids) != len(set(place_ids)):
        raise NaptanN4AError("duplicate StopArea publisher identity")
    if len(node_ids) != len(set(node_ids)):
        raise NaptanN4AError("duplicate StopPoint publisher identity")
    if len({membership_key(row["publisher_node_identity"], row["publisher_place_identity"]) for row in memberships}) != len(memberships):
        raise NaptanN4AError("duplicate membership identity")
    if len({parent_edge_key(row["publisher_child_identity"], row["publisher_parent_identity"]) for row in parents}) != len(parents):
        raise NaptanN4AError("duplicate parent-edge identity")
    return {
        "snapshot_key": key,
        "place_count": len(places),
        "node_count": len(nodes),
        "membership_count": len(memberships),
        "parent_edge_count": len(parents),
    }


def _row_keys(snapshot: dict[str, Any]) -> dict[str, set[str]]:
    validate_snapshot(snapshot)
    metadata = snapshot["metadata"]
    snapshot_key = metadata["source_snapshot_key"]
    return {
        "snapshot": {snapshot_key},
        "places": {f"{snapshot_key}|place|{row['publisher_identity']}" for row in snapshot.get("places", [])},
        "nodes": {f"{snapshot_key}|node|{row['publisher_identity']}" for row in snapshot.get("nodes", [])},
        "memberships": {f"{snapshot_key}|membership|{membership_key(row['publisher_node_identity'], row['publisher_place_identity'])}" for row in snapshot.get("memberships", [])},
        "parents": {f"{snapshot_key}|parent|{parent_edge_key(row['publisher_child_identity'], row['publisher_parent_identity'])}" for row in snapshot.get("parents", [])},
    }


def replay_plan(snapshot: dict[str, Any], existing_keys: dict[str, set[str]] | None = None) -> dict[str, Any]:
    expected = _row_keys(snapshot)
    existing = existing_keys or {key: set() for key in expected}
    operations = {kind: sorted(keys - existing.get(kind, set())) for kind, keys in expected.items()}
    return {
        "snapshot_key": snapshot["metadata"]["source_snapshot_key"],
        "operations": operations,
        "counts": {kind: len(values) for kind, values in operations.items()},
        "production_execution": False,
    }


def snapshot_diff(before: dict[str, Any], after: dict[str, Any]) -> dict[str, Any]:
    validate_snapshot(before)
    validate_snapshot(after)

    def keyed(rows: list[dict[str, Any]], key: str) -> dict[str, dict[str, Any]]:
        return {row[key]: row for row in rows}

    before_places = keyed(before.get("places", []), "publisher_identity")
    after_places = keyed(after.get("places", []), "publisher_identity")
    before_nodes = keyed(before.get("nodes", []), "publisher_identity")
    after_nodes = keyed(after.get("nodes", []), "publisher_identity")
    before_memberships = {membership_key(row["publisher_node_identity"], row["publisher_place_identity"]): row for row in before.get("memberships", [])}
    after_memberships = {membership_key(row["publisher_node_identity"], row["publisher_place_identity"]): row for row in after.get("memberships", [])}
    before_parents = {parent_edge_key(row["publisher_child_identity"], row["publisher_parent_identity"]): row for row in before.get("parents", [])}
    after_parents = {parent_edge_key(row["publisher_child_identity"], row["publisher_parent_identity"]): row for row in after.get("parents", [])}

    def changes(left: dict[str, dict[str, Any]], right: dict[str, dict[str, Any]]) -> dict[str, list[str]]:
        left_ids, right_ids = set(left), set(right)
        common = left_ids & right_ids
        return {
            "added": sorted(right_ids - left_ids),
            "removed": sorted(left_ids - right_ids),
            "changed": sorted(identity for identity in common if stable_json(left[identity]) != stable_json(right[identity])),
            "unchanged": sorted(identity for identity in common if stable_json(left[identity]) == stable_json(right[identity])),
        }

    return {
        "before_snapshot_key": before["metadata"]["source_snapshot_key"],
        "after_snapshot_key": after["metadata"]["source_snapshot_key"],
        "places": changes(before_places, after_places),
        "nodes": changes(before_nodes, after_nodes),
        "memberships": changes(before_memberships, after_memberships),
        "parents": changes(before_parents, after_parents),
        "production_execution": False,
    }


def graph_validation(snapshot: dict[str, Any]) -> dict[str, Any]:
    validate_snapshot(snapshot)
    places = {row["publisher_identity"] for row in snapshot.get("places", [])}
    parent_map: defaultdict[str, set[str]] = defaultdict(set)
    unresolved = []
    for row in snapshot.get("parents", []):
        child = row["publisher_child_identity"]
        parent = row["publisher_parent_identity"]
        if child not in places:
            unresolved.append({"kind": "UNRESOLVED_MISSING_CHILD", "edge": parent_edge_key(child, parent)})
        if parent not in places:
            unresolved.append({"kind": "UNRESOLVED_MISSING_PARENT", "edge": parent_edge_key(child, parent)})
        if child in places and parent in places:
            parent_map[child].add(parent)
    cycles: set[str] = set()

    def visit(node: str, trail: tuple[str, ...]) -> None:
        if node in trail:
            cycles.update(trail[trail.index(node):])
            return
        for parent in sorted(parent_map.get(node, set())):
            visit(parent, trail + (node,))

    for place in sorted(places):
        visit(place, ())
    return {
        "unresolved_parent_edges": unresolved,
        "cycle_nodes": sorted(cycles),
        "can_mark_snapshot_validated": not unresolved and not cycles,
        "production_execution": False,
    }


def project_complexes(snapshot: dict[str, Any]) -> dict[str, Any]:
    """Project resolved root identities without persisting derived complexes."""
    validate_snapshot(snapshot)
    places = {row["publisher_identity"]: row for row in snapshot.get("places", [])}
    parent_map: defaultdict[str, set[str]] = defaultdict(set)
    blocked_places: set[str] = set()
    for row in snapshot.get("parents", []):
        child = row.get("publisher_child_identity")
        parent = row.get("publisher_parent_identity")
        if row.get("resolution_status", "RESOLVED") != "RESOLVED" or child not in places or parent not in places:
            if child in places:
                blocked_places.add(child)
        elif child in places and parent in places:
            parent_map[child].add(parent)
    memo: dict[str, str | None] = {}
    visiting: set[str] = set()

    def root(place: str) -> str | None:
        if place in memo:
            return memo[place]
        if place in visiting:
            memo[place] = None
            return None
        if place in blocked_places:
            memo[place] = None
            return None
        visiting.add(place)
        resolved_parent_roots = [root(parent) for parent in sorted(parent_map.get(place, set()))]
        parent_roots = {resolved for resolved in resolved_parent_roots if resolved is not None}
        unresolved_parent = any(resolved is None for resolved in resolved_parent_roots)
        result = None if unresolved_parent or len(parent_roots) > 1 else (next(iter(parent_roots)) if parent_roots else place)
        visiting.discard(place)
        memo[place] = result
        return result

    for place in sorted(places):
        root(place)
    complexes = []
    for root_id in sorted(place for place in places if root(place) == place):
        members = sorted(place for place in places if root(place) == root_id)
        complexes.append({
            "complex_identity": root_id,
            "root_stop_area_identity": root_id,
            "place_identities": members,
            "projection_kind": "DETERMINISTIC_PROJECTION",
        })
    unresolved = sorted(place for place, resolved_root in memo.items() if resolved_root is None)
    return {"complexes": complexes, "unresolved_place_identities": unresolved, "production_execution": False}


def validate_candidate_migration(path: Path = MIGRATION_PATH) -> dict[str, Any]:
    sql = path.read_text(encoding="utf-8")
    upper = sql.upper()
    missing = sorted(table for table in EXPECTED_TABLES if f"CREATE TABLE PUBLIC.{table.upper()}" not in upper)
    forbidden = [pattern for pattern in ("INSERT INTO", "UPDATE PUBLIC.FACILITIES", "DELETE FROM PUBLIC.FACILITIES", "CREATE POLICY") if pattern in upper]
    required_security = all(token in upper for token in (
        "ENABLE ROW LEVEL SECURITY",
        "REVOKE ALL ON TABLE PUBLIC.TRANSPORT_SOURCE_SNAPSHOTS",
        "GRANT ALL ON TABLE PUBLIC.TRANSPORT_SOURCE_SNAPSHOTS",
        "TO SERVICE_ROLE",
    ))
    if missing or forbidden or not required_security:
        raise NaptanN4AError(f"candidate migration failed static validation: missing={missing}, forbidden={forbidden}, security={required_security}")
    return {
        "migration": str(path),
        "sha256": sha256_file(path),
        "tables": sorted(EXPECTED_TABLES),
        "forbidden_patterns_found": forbidden,
        "security_contract_present": required_security,
        "production_execution": False,
    }


def load_fixture(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def national_scale_estimate() -> dict[str, Any]:
    return {
        "snapshot_rows": 1,
        "source_place_rows": 97270,
        "source_node_rows": 436428,
        "membership_rows_after_exact_duplicate_coalescing": 169524,
        "membership_duplicate_occurrence_total": 3,
        "parent_edge_rows": 3519,
        "unresolved_member_parent_reference_rows": 1543,
        "unresolved_area_parent_reference_rows": 41,
        "normalized_projection_rows": 93751,
        "normalized_projection_persistence": "none in N4A; deterministic projection only",
        "note": "Counts are one current national snapshot; future snapshots append source facts and repeat edge rows per snapshot.",
    }

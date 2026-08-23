"""Governed N5-R2 NaPTAN source-graph planner and production loader.

The default mode is read-only planning. Production DML is available only with
``--apply`` and is restricted to the five N4A source-graph tables. The source
model is built from the committed N3 parser and the N5-R1 keyed-count
contract; this module does not create canonical Relief data.
"""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import math
import os
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any, Iterable

from tools.source_expansion.naptan_n3 import (
    deep_hierarchy_analysis,
    multi_parent_analysis,
    normalize_complexes,
    parse_xml,
)
from tools.source_expansion.naptan_n5_r1 import (
    FROZEN_BYTES,
    FROZEN_SHA256,
    independent_key_counter,
    verify_frozen_source,
)


EXPECTED_PROJECT_REF = "bgwxrxkmyaihplaloely"
EXPECTED_BASE_URL = f"https://{EXPECTED_PROJECT_REF}.supabase.co"
SOURCE_URL = "https://naptan.api.dft.gov.uk/v1/access-nodes?dataFormat=xml"
SOURCE_SNAPSHOT_KEY = f"naptan:sha256:{FROZEN_SHA256.lower()}"
RETRIEVED_AT = "2026-08-22T14:48:39.4826193Z"
LICENCE = "Open Government Licence v3.0"
ATTRIBUTION = "Contains public sector information licensed under the Open Government Licence v3.0."
PARSER_VERSION = "relief.naptan.n5-r2.v1"
CONTRACT_VERSION = "N5-R1-2026-08-23"
N4A_RELATIVE_PATH = "supabase/migrations/20260822170000_naptan_transport_source_graph.sql"
N4A_SHA256 = "087A389B8CEAC021B12708BC55C39022CB38D5459510EFFB6CF057CEF232C44E"

TABLES = (
    "transport_source_snapshots",
    "transport_source_places",
    "transport_source_nodes",
    "transport_source_memberships",
    "transport_source_place_parents",
)
NON_SOURCE_TABLES = {
    "facilities",
    "facility_sources",
    "facility_source_observations",
    "import_runs",
    "toilet_map_import_staging",
    "toilet_units",
    "toilet_unit_sources",
}

EXPECTED_VALUES = {
    "source_snapshot_rows": 1,
    "stop_area_rows": 97_270,
    "stop_point_rows": 436_428,
    "publisher_membership_element_count": 169_530,
    "unique_membership_key_count": 169_527,
    "stored_membership_row_count": 169_527,
    "duplicate_membership_extra_occurrence_count": 3,
    "publisher_parent_element_count": 3_519,
    "unique_parent_edge_count": 3_519,
    "stored_parent_row_count": 3_519,
    "unresolved_membership_edge_count": 2_804,
    "distinct_missing_member_parent_identity_count": 1_543,
    "unresolved_parent_edge_count": 92,
    "distinct_missing_area_parent_identity_count": 41,
    "normalized_complexes": 93_751,
    "single_area_complexes": 91_757,
    "parent_area_complexes": 559,
    "multimodal_parent_complexes": 1_435,
    "unresolved_area_nodes": 93,
    "multi_parent_nodes": 701,
    "two_parent_nodes": 667,
    "three_parent_nodes": 34,
    "shared_root_multi_parent_nodes": 73,
    "cross_complex_or_unresolved_multi_parent_nodes": 628,
    "maximum_hierarchy_depth": 13,
    "hierarchy_cycles": 0,
    "total_stored_source_graph_rows": 706_745,
}

EXPECTED_DUPLICATE_KEYS = {
    "naptan-stop-point:64801285|naptan-stop-area:648G1285",
    "naptan-stop-point:64804134|naptan-stop-area:648G221434",
    "naptan-stop-point:64804135|naptan-stop-area:648G221434",
}

EXPECTED_MODE_COUNTS = {
    "bus_coach": 75_920,
    "multimodal": 1_541,
    "no_mode": 13_591,
    "metro_tram_underground": 641,
    "rail": 1_519,
    "ferry_port": 470,
    "air": 65,
    "taxi": 4,
}


class N5R2Error(RuntimeError):
    """Raised for a fail-closed N5-R2 gate or production conflict."""


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest().upper()


def n4a_hash(repo_root: Path) -> str:
    return sha256_file(repo_root / N4A_RELATIVE_PATH)


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def load_contract(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if payload.get("authoritative") is not True or payload.get("contract_version") != CONTRACT_VERSION:
        raise N5R2Error("authoritative N5-R1 contract marker is missing")
    source = payload.get("source", {})
    if source.get("expected_byte_size") != FROZEN_BYTES or source.get("expected_sha256") != FROZEN_SHA256:
        raise N5R2Error("N5-R1 source contract does not contain the frozen source hash/size")
    values = payload.get("values", {})
    contract_mapping = {
        "source_snapshot_rows": "source_snapshot_rows",
        "stop_area_rows": "stop_area_rows",
        "stop_point_rows": "stop_point_rows",
        "publisher_membership_element_count": "publisher_membership_element_count",
        "unique_membership_key_count": "unique_membership_key_count",
        "stored_membership_row_count": "stored_membership_row_count",
        "duplicate_membership_extra_occurrence_count": "duplicate_membership_extra_occurrence_count",
        "publisher_parent_element_count": "publisher_parent_element_count",
        "unique_parent_edge_count": "unique_parent_edge_count",
        "stored_parent_row_count": "stored_parent_row_count",
        "unresolved_membership_edge_count": "unresolved_membership_edge_count",
        "distinct_missing_member_parent_identity_count": "distinct_missing_member_parent_identity_count",
        "unresolved_parent_edge_count": "unresolved_parent_edge_count",
        "distinct_missing_area_parent_identity_count": "distinct_missing_area_parent_identity_count",
        "normalized_complexes": "normalized_complexes",
        "total_stored_source_graph_rows": "total_stored_source_graph_rows",
    }
    for expected_name, contract_name in contract_mapping.items():
        if values.get(contract_name) != EXPECTED_VALUES[expected_name]:
            raise N5R2Error(f"N5-R1 contract mismatch for {contract_name}: {values.get(contract_name)!r}")
    if values.get("stored_membership_row_count") == 169_524:
        raise N5R2Error("superseded 169524 membership expectation was selected")
    return payload


def _as_none(value: str | None) -> str | None:
    value = (value or "").strip()
    return value or None


def _point_identity(n3_identity: str) -> str:
    prefix, separator, value = n3_identity.partition(":")
    if prefix != "naptan" or not separator or not value:
        raise N5R2Error(f"unexpected N3 point identity {n3_identity!r}")
    return f"naptan-stop-point:{value.upper()}"


def build_source_model(source_path: Path, contract: dict[str, Any]) -> dict[str, Any]:
    started = time.perf_counter()
    source_meta = verify_frozen_source(source_path)
    data, n3_parse_seconds = parse_xml(source_path)
    keyed = independent_key_counter(source_path)
    normalized = normalize_complexes(data)
    multi = multi_parent_analysis(data, normalized)
    deep = deep_hierarchy_analysis(data)

    type_counts: dict[str, int] = {}
    mode_counts: dict[str, int] = {}
    for row in normalized["complexes"]:
        type_counts[row["complex_type"]] = type_counts.get(row["complex_type"], 0) + 1
        mode = "multimodal" if len(row["modes"]) > 1 else (row["modes"][0] if row["modes"] else "no_mode")
        mode_counts[mode] = mode_counts.get(mode, 0) + 1

    actual = {
        "source_snapshot_rows": 1,
        "stop_area_rows": len(data["areas"]),
        "stop_point_rows": len(data["points"]),
        "publisher_membership_element_count": keyed["publisher_membership_element_count"],
        "unique_membership_key_count": keyed["unique_membership_key_count"],
        "stored_membership_row_count": keyed["stored_membership_row_count"],
        "duplicate_membership_extra_occurrence_count": keyed["duplicate_membership_extra_occurrence_count"],
        "publisher_parent_element_count": keyed["publisher_parent_element_count"],
        "unique_parent_edge_count": keyed["unique_parent_edge_count"],
        "stored_parent_row_count": keyed["stored_parent_row_count"],
        "unresolved_membership_edge_count": keyed["unresolved_membership_edge_count"],
        "distinct_missing_member_parent_identity_count": keyed["distinct_missing_member_parent_identity_count"],
        "unresolved_parent_edge_count": keyed["unresolved_parent_edge_count"],
        "distinct_missing_area_parent_identity_count": keyed["distinct_missing_area_parent_identity_count"],
        "normalized_complexes": len(normalized["complexes"]),
        "single_area_complexes": type_counts.get("SINGLE_AREA_COMPLEX", 0),
        "parent_area_complexes": type_counts.get("PARENT_AREA_COMPLEX", 0),
        "multimodal_parent_complexes": type_counts.get("MULTIMODAL_PARENT_COMPLEX", 0),
        "unresolved_area_nodes": sum(1 for root, _state in normalized["roots"].values() if root is None),
        "multi_parent_nodes": multi["total_multi_parent_stop_points"],
        "two_parent_nodes": multi["parent_count_distribution"].get("2", 0),
        "three_parent_nodes": multi["parent_count_distribution"].get("3", 0),
        "shared_root_multi_parent_nodes": multi["shared_common_complex_count"],
        "cross_complex_or_unresolved_multi_parent_nodes": multi["cross_complex_or_unresolved_count"],
        "maximum_hierarchy_depth": deep["maximum_depth"],
        "hierarchy_cycles": len(deep["cycle_nodes"]),
        "total_stored_source_graph_rows": 1 + len(data["areas"]) + len(data["points"]) + keyed["stored_membership_row_count"] + keyed["stored_parent_row_count"],
    }
    mismatches = {key: {"expected": EXPECTED_VALUES[key], "actual": value} for key, value in actual.items() if EXPECTED_VALUES.get(key) != value}
    if mismatches:
        raise N5R2Error(f"corrected N5-R1 contract mismatch: {json.dumps(mismatches, sort_keys=True)}")
    duplicate_keys = {row["membership_key"] for row in keyed["exact_duplicate_memberships"]}
    if duplicate_keys != EXPECTED_DUPLICATE_KEYS:
        raise N5R2Error(f"duplicate key mismatch: {sorted(duplicate_keys)}")
    if set(mode_counts) != set(EXPECTED_MODE_COUNTS) or mode_counts != EXPECTED_MODE_COUNTS:
        raise N5R2Error(f"mode distribution mismatch: {mode_counts}")

    areas = data["areas"]
    points = data["points"]
    area_ids = set(areas)
    point_rows: list[dict[str, Any]] = []
    point_identity_by_n3: dict[str, str] = {}
    for n3_id in sorted(points):
        row = points[n3_id]
        stored_id = _point_identity(n3_id)
        point_identity_by_n3[n3_id] = stored_id
        has_coords = row["latitude"] is not None and row["longitude"] is not None
        point_rows.append({
            "publisher_identity": stored_id,
            "publisher_id": row["publisher_id"],
            "source_stop_type": row["stop_type"],
            "normalized_mode": row["mode"],
            "display_name": row["name"],
            "normalized_name": row["normalized_name"],
            "source_status": _as_none(row["status"]),
            "source_modification": _as_none(row["modification"]),
            "publisher_latitude": row["latitude"] if has_coords else None,
            "publisher_longitude": row["longitude"] if has_coords else None,
            "coordinate_scope": "TRANSPORT_STOP_LEVEL" if has_coords else "NONE",
            "source_attributes": {"source_structure": "StopPoint"},
        })

    area_rows: list[dict[str, Any]] = []
    for area_id in sorted(areas):
        row = areas[area_id]
        has_coords = row["latitude"] is not None and row["longitude"] is not None
        area_rows.append({
            "publisher_identity": area_id,
            "publisher_id": row["publisher_id"],
            "place_kind": "STOP_AREA",
            "display_name": row["name"],
            "normalized_name": row["normalized_name"],
            "source_type": row["area_type"],
            "administrative_area_code": _as_none(row["administrative_area_code"]),
            "source_status": _as_none(row["status"]),
            "source_modification": _as_none(row["modification"]),
            "publisher_latitude": row["latitude"] if has_coords else None,
            "publisher_longitude": row["longitude"] if has_coords else None,
            "coordinate_scope": "STOP_AREA_LEVEL" if has_coords else "NONE",
            "source_attributes": {"source_structure": "StopArea"},
        })

    duplicate_count_by_key = {row["membership_key"]: row["raw_occurrence_count"] for row in keyed["exact_duplicate_memberships"]}
    membership_rows: list[dict[str, Any]] = []
    for n3_id in sorted(data["point_parents"]):
        node_id = point_identity_by_n3[n3_id]
        for place_id in sorted(data["point_parents"][n3_id]):
            key = f"{node_id}|{place_id}"
            place_exists = place_id in area_ids
            membership_rows.append({
                "publisher_node_identity": node_id,
                "publisher_place_identity": place_id,
                "membership_key": key,
                "resolution_status": "RESOLVED" if place_exists else "UNRESOLVED_MISSING_PLACE",
                "duplicate_occurrence_count": duplicate_count_by_key.get(key, 1),
                "source_attributes": {"source_structure": "StopPoint.StopAreas.StopAreaRef"},
                "_node_n3_identity": n3_id,
                "_place_exists": place_exists,
            })

    parent_rows: list[dict[str, Any]] = []
    for child_id in sorted(data["parent_map"]):
        for parent_id in sorted(data["parent_map"][child_id]):
            parent_exists = parent_id in area_ids
            key = f"{child_id}|{parent_id}"
            parent_rows.append({
                "publisher_child_identity": child_id,
                "publisher_parent_identity": parent_id,
                "parent_edge_key": key,
                "resolution_status": "RESOLVED" if parent_exists else "UNRESOLVED_MISSING_PARENT",
                "duplicate_occurrence_count": 1,
                "source_attributes": {"source_structure": "StopArea.ParentStopAreaRef"},
                "_child_exists": True,
                "_parent_exists": parent_exists,
            })

    expected_counts = {
        "snapshots": 1,
        "places": len(area_rows),
        "nodes": len(point_rows),
        "memberships": len(membership_rows),
        "parent_edges": len(parent_rows),
        "total_stored_source_graph_rows": 1 + len(area_rows) + len(point_rows) + len(membership_rows) + len(parent_rows),
    }
    if expected_counts["total_stored_source_graph_rows"] != EXPECTED_VALUES["total_stored_source_graph_rows"]:
        raise N5R2Error(f"planned stored-row total mismatch: {expected_counts}")

    return {
        "source": source_meta,
        "contract_version": contract.get("contract_version"),
        "parser_version": PARSER_VERSION,
        "source_snapshot_key": SOURCE_SNAPSHOT_KEY,
        "source_url": SOURCE_URL,
        "retrieved_at": RETRIEVED_AT,
        "licence": LICENCE,
        "attribution": ATTRIBUTION,
        "values": actual,
        "mode_distribution": mode_counts,
        "complex_type_distribution": type_counts,
        "duplicate_membership_keys": sorted(duplicate_keys),
        "duplicate_membership_counts": {key: duplicate_count_by_key[key] for key in sorted(duplicate_count_by_key)},
        "n3_projection": {
            "normalized_complexes": len(normalized["complexes"]),
            "single_area_complexes": type_counts.get("SINGLE_AREA_COMPLEX", 0),
            "parent_area_complexes": type_counts.get("PARENT_AREA_COMPLEX", 0),
            "multimodal_parent_complexes": type_counts.get("MULTIMODAL_PARENT_COMPLEX", 0),
            "unresolved_area_nodes": actual["unresolved_area_nodes"],
            "multi_parent_nodes": multi["total_multi_parent_stop_points"],
            "shared_root_multi_parent_nodes": multi["shared_common_complex_count"],
            "cross_complex_or_unresolved_multi_parent_nodes": multi["cross_complex_or_unresolved_count"],
            "maximum_hierarchy_depth": deep["maximum_depth"],
            "hierarchy_cycles": len(deep["cycle_nodes"]),
        },
        "expected_counts": expected_counts,
        "chunk_plan": {table: {"batch_size": 2_000, "planned_rows": count} for table, count in {
            "transport_source_snapshots": 1,
            "transport_source_places": len(area_rows),
            "transport_source_nodes": len(point_rows),
            "transport_source_memberships": len(membership_rows),
            "transport_source_place_parents": len(parent_rows),
        }.items()},
        "mutation_table_allowlist": list(TABLES),
        "non_source_mutation_allowlist": [],
        "performance": {"n3_parse_seconds": round(n3_parse_seconds, 3), "planner_seconds": round(time.perf_counter() - started, 3)},
        "_area_rows": area_rows,
        "_point_rows": point_rows,
        "_membership_rows": membership_rows,
        "_parent_rows": parent_rows,
    }


class RestClient:
    """Small allowlisted PostgREST client with no write retries."""

    def __init__(self, base_url: str, api_key: str, page_size: int = 1_000) -> None:
        if base_url.rstrip("/") != EXPECTED_BASE_URL:
            raise N5R2Error("production base URL is not the exact Relief project URL")
        if not api_key or any(character.isspace() for character in api_key):
            raise N5R2Error("missing or malformed service-role key")
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.page_size = page_size

    def _url(self, table: str, params: dict[str, str] | None = None) -> str:
        if table not in TABLES:
            raise N5R2Error(f"REST table outside N5-R2 allowlist: {table}")
        url = f"{self.base_url}/rest/v1/{table}"
        if params:
            url += "?" + urllib.parse.urlencode(params)
        return url

    def request(self, method: str, table: str, *, params: dict[str, str] | None = None, payload: Any = None, headers: dict[str, str] | None = None, range_header: str | None = None) -> tuple[int, dict[str, str], Any]:
        request_headers = {
            "apikey": self.api_key,
            "Authorization": f"Bearer {self.api_key}",
            "Accept": "application/json",
        }
        if payload is not None:
            request_headers["Content-Type"] = "application/json"
        if headers:
            request_headers.update(headers)
        if range_header:
            request_headers["Range"] = range_header
        body = None if payload is None else json.dumps(payload, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
        request = urllib.request.Request(self._url(table, params), data=body, headers=request_headers, method=method)
        try:
            with urllib.request.urlopen(request, timeout=180) as response:
                raw = response.read()
                content_type = response.headers.get("Content-Type", "")
                value = json.loads(raw.decode("utf-8")) if raw and "json" in content_type else None
                return response.status, dict(response.headers.items()), value
        except urllib.error.HTTPError as error:
            raw = error.read(4096)
            detail = raw.decode("utf-8", errors="replace")
            raise N5R2Error(f"PostgREST {method} {table} failed ({error.code}): {detail[:1000]}") from error
        except urllib.error.URLError as error:
            raise N5R2Error(f"PostgREST {method} {table} network failure: {error.reason}") from error

    def count(self, table: str) -> int:
        status, headers, value = self.request(
            "GET",
            table,
            params={"select": "id"},
            headers={"Prefer": "count=exact"},
            range_header="0-0",
        )
        if status < 200 or status >= 300:
            raise N5R2Error(f"unexpected count status {status} for {table}")
        content_range = headers.get("Content-Range", "")
        if "/" in content_range:
            total = content_range.rsplit("/", 1)[1]
            if total.isdigit():
                return int(total)
        return len(value or [])

    def insert_batch(self, table: str, rows: list[dict[str, Any]]) -> None:
        if not rows:
            return
        self.request("POST", table, payload=rows, headers={"Prefer": "return=minimal"})

    def insert_one_returning(self, table: str, row: dict[str, Any]) -> dict[str, Any]:
        status, _headers, value = self.request("POST", table, payload=[row], headers={"Prefer": "return=representation"})
        if status < 200 or status >= 300 or not isinstance(value, list) or len(value) != 1:
            raise N5R2Error(f"expected one returned row from {table}")
        return value[0]

    def patch_snapshot(self, snapshot_id: str, payload: dict[str, Any]) -> None:
        self.request(
            "PATCH",
            "transport_source_snapshots",
            params={"id": f"eq.{snapshot_id}"},
            payload=payload,
            headers={"Prefer": "return=minimal"},
        )

    def fetch_all(self, table: str, select: str, order_column: str) -> list[dict[str, Any]]:
        rows: list[dict[str, Any]] = []
        last_value: str | None = None
        while True:
            params = {"select": select, "order": f"{order_column}.asc"}
            if last_value is not None:
                # Offset pagination becomes progressively more expensive on
                # the national node table. All replay keys are non-null and
                # deterministic, so use an indexed keyset boundary instead.
                params[order_column] = f"gt.{last_value}"
            status, _headers, value = self.request(
                "GET",
                table,
                params=params,
                headers={},
                range_header=f"0-{self.page_size - 1}",
            )
            if status < 200 or status >= 300 or not isinstance(value, list):
                raise N5R2Error(f"unexpected read response from {table}")
            rows.extend(value)
            if len(value) < self.page_size:
                break
            last_value = value[-1].get(order_column)
            if not last_value:
                raise N5R2Error(f"keyset pagination column {order_column} was empty in {table}")
        return rows


def snapshot_payload(model: dict[str, Any]) -> dict[str, Any]:
    return {
        "source_namespace": "naptan",
        "product_name": "NaPTAN national XML access-node and StopArea package",
        "source_snapshot_key": model["source_snapshot_key"],
        "source_url": model["source_url"],
        "source_checksum_sha256": FROZEN_SHA256.lower(),
        "source_byte_size": FROZEN_BYTES,
        "retrieved_at": RETRIEVED_AT,
        "licence": LICENCE,
        "attribution": ATTRIBUTION,
        "parser_version": PARSER_VERSION,
        "source_schema_version": None,
        "ingestion_state": "CAPTURED",
        "row_counts": {**model["values"], "contract_version": CONTRACT_VERSION, "raw_publisher_membership_elements": 169_530, "unique_membership_keys": 169_527, "duplicate_extra_occurrences": 3, "duplicate_occurrence_semantics": "total_occurrences_per_logical_key"},
    }


def _strip_private(row: dict[str, Any]) -> dict[str, Any]:
    return {key: value for key, value in row.items() if not key.startswith("_")}


def _canonical_timestamp(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value).replace("Z", "+00:00")
    try:
        parsed = dt.datetime.fromisoformat(text).astimezone(dt.timezone.utc)
    except ValueError:
        return str(value)
    # PostgreSQL timestamptz stores microseconds; the governed source record
    # carries seven fractional digits, so compare at database precision.
    return parsed.replace(microsecond=(parsed.microsecond // 1)).isoformat().replace("+00:00", "Z")


def _semantically_equal(expected: Any, actual: Any) -> bool:
    if isinstance(expected, float) and isinstance(actual, (float, int)):
        return math.isclose(expected, float(actual), rel_tol=0.0, abs_tol=1e-12)
    if isinstance(expected, dict) and isinstance(actual, dict):
        return set(expected) == set(actual) and all(_semantically_equal(expected[key], actual[key]) for key in expected)
    if isinstance(expected, list) and isinstance(actual, list):
        return len(expected) == len(actual) and all(_semantically_equal(left, right) for left, right in zip(expected, actual))
    return expected == actual


def production_preflight(client: RestClient) -> dict[str, Any]:
    counts = {table: client.count(table) for table in TABLES}
    if any(counts.values()):
        raise N5R2Error(f"SOURCE GRAPH IS NOT EMPTY: {counts}")
    return {"source_graph_counts": counts, "expected_all_zero": True, "conflicts": 0}


def apply_model(model: dict[str, Any], client: RestClient, progress_path: Path, batch_size: int) -> dict[str, Any]:
    started = time.perf_counter()
    preflight = production_preflight(client)
    progress: dict[str, Any] = {
        "status": "STARTING",
        "source_sha256": FROZEN_SHA256,
        "source_byte_size": FROZEN_BYTES,
        "project_ref": EXPECTED_PROJECT_REF,
        "mutation_table_allowlist": list(TABLES),
        "preflight": preflight,
        "chunks": [],
        "committed_inserts": {table: 0 for table in TABLES},
        "retry_count": 0,
    }
    write_json(progress_path, progress)
    snapshot_id: str | None = None
    try:
        returned = client.insert_one_returning("transport_source_snapshots", snapshot_payload(model))
        snapshot_id = returned.get("id")
        if not snapshot_id:
            raise N5R2Error("snapshot insert did not return an id")
        progress["snapshot_id"] = snapshot_id
        progress["committed_inserts"]["transport_source_snapshots"] = 1
        write_json(progress_path, progress)

        for table, key in (("transport_source_places", "_area_rows"), ("transport_source_nodes", "_point_rows")):
            rows = model[key]
            for chunk_number, start in enumerate(range(0, len(rows), batch_size), start=1):
                chunk = [{"snapshot_id": snapshot_id, **row} for row in rows[start : start + batch_size]]
                chunk_started = time.perf_counter()
                client.insert_batch(table, chunk)
                elapsed = time.perf_counter() - chunk_started
                record = {"table": table, "chunk": chunk_number, "planned_rows": len(chunk), "attempted_rows": len(chunk), "inserted_rows": len(chunk), "elapsed_seconds": round(elapsed, 3), "retry_count": 0, "status": "COMMITTED"}
                progress["chunks"].append(record)
                progress["committed_inserts"][table] += len(chunk)
                write_json(progress_path, progress)

        place_rows = client.fetch_all("transport_source_places", "id,publisher_identity", "publisher_identity")
        node_rows = client.fetch_all("transport_source_nodes", "id,publisher_identity", "publisher_identity")
        place_ids = {row["publisher_identity"]: row["id"] for row in place_rows}
        node_ids = {row["publisher_identity"]: row["id"] for row in node_rows}
        if len(place_ids) != len(model["_area_rows"]) or len(node_ids) != len(model["_point_rows"]):
            raise N5R2Error("identity map cardinality does not equal inserted place/node rows")

        for table, key in (("transport_source_memberships", "_membership_rows"), ("transport_source_place_parents", "_parent_rows")):
            rows = model[key]
            payload_rows = []
            for row in rows:
                output = {"snapshot_id": snapshot_id, **_strip_private(row)}
                if table == "transport_source_memberships":
                    output["node_id"] = node_ids.get(row["publisher_node_identity"])
                    output["place_id"] = place_ids.get(row["publisher_place_identity"])
                else:
                    output["child_place_id"] = place_ids.get(row["publisher_child_identity"])
                    output["parent_place_id"] = place_ids.get(row["publisher_parent_identity"])
                payload_rows.append(output)
            for chunk_number, start in enumerate(range(0, len(payload_rows), batch_size), start=1):
                chunk = payload_rows[start : start + batch_size]
                chunk_started = time.perf_counter()
                client.insert_batch(table, chunk)
                elapsed = time.perf_counter() - chunk_started
                record = {"table": table, "chunk": chunk_number, "planned_rows": len(chunk), "attempted_rows": len(chunk), "inserted_rows": len(chunk), "elapsed_seconds": round(elapsed, 3), "retry_count": 0, "status": "COMMITTED"}
                progress["chunks"].append(record)
                progress["committed_inserts"][table] += len(chunk)
                write_json(progress_path, progress)

        client.patch_snapshot(snapshot_id, {"ingestion_state": "INGESTED"})
        final_counts = {table: client.count(table) for table in TABLES}
        expected_counts = {
            "transport_source_snapshots": 1,
            "transport_source_places": EXPECTED_VALUES["stop_area_rows"],
            "transport_source_nodes": EXPECTED_VALUES["stop_point_rows"],
            "transport_source_memberships": EXPECTED_VALUES["stored_membership_row_count"],
            "transport_source_place_parents": EXPECTED_VALUES["stored_parent_row_count"],
        }
        if final_counts != expected_counts:
            raise N5R2Error(f"N5_R2_GRAPH_COUNT_MISMATCH: {final_counts}")
        progress.update({"status": "SUCCEEDED", "final_counts": final_counts, "elapsed_seconds": round(time.perf_counter() - started, 3)})
        write_json(progress_path, progress)
        return progress
    except Exception as error:
        progress.update({"status": "PARTIAL_OR_FAILED", "error": str(error), "elapsed_seconds": round(time.perf_counter() - started, 3)})
        write_json(progress_path, progress)
        raise


def _expected_place_rows(model: dict[str, Any], snapshot_id: str) -> dict[str, dict[str, Any]]:
    return {row["publisher_identity"]: {"snapshot_id": snapshot_id, **row} for row in model["_area_rows"]}


def _expected_node_rows(model: dict[str, Any], snapshot_id: str) -> dict[str, dict[str, Any]]:
    return {row["publisher_identity"]: {"snapshot_id": snapshot_id, **row} for row in model["_point_rows"]}


def verify_existing_graph(model: dict[str, Any], client: RestClient, evidence_path: Path) -> dict[str, Any]:
    """Read every explicit source fact and prove the identical replay is a no-op."""
    snapshot_rows = client.fetch_all("transport_source_snapshots", "id,source_namespace,product_name,source_snapshot_key,source_url,source_checksum_sha256,source_byte_size,retrieved_at,licence,attribution,parser_version,source_schema_version,ingestion_state,row_counts", "source_snapshot_key")
    if len(snapshot_rows) != 1:
        raise N5R2Error(f"expected one production snapshot, found {len(snapshot_rows)}")
    snapshot = snapshot_rows[0]
    snapshot_id = snapshot["id"]
    expected_snapshot = snapshot_payload(model)
    snapshot_differences = {
        key: {"expected": expected_snapshot.get(key), "actual": snapshot.get(key)}
        for key in expected_snapshot
        if key not in {"ingestion_state", "retrieved_at"}
        and expected_snapshot.get(key) != snapshot.get(key)
    }
    if _canonical_timestamp(expected_snapshot.get("retrieved_at")) != _canonical_timestamp(snapshot.get("retrieved_at")):
        snapshot_differences["retrieved_at"] = {
            "expected": _canonical_timestamp(expected_snapshot.get("retrieved_at")),
            "actual": _canonical_timestamp(snapshot.get("retrieved_at")),
        }
    if snapshot.get("ingestion_state") != "INGESTED":
        snapshot_differences["ingestion_state"] = {"expected": "INGESTED", "actual": snapshot.get("ingestion_state")}

    place_rows = client.fetch_all("transport_source_places", "snapshot_id,publisher_identity,publisher_id,place_kind,display_name,normalized_name,source_type,administrative_area_code,source_status,source_modification,publisher_latitude,publisher_longitude,coordinate_scope,source_attributes", "publisher_identity")
    node_rows = client.fetch_all("transport_source_nodes", "snapshot_id,publisher_identity,publisher_id,source_stop_type,normalized_mode,display_name,normalized_name,source_status,source_modification,publisher_latitude,publisher_longitude,coordinate_scope,source_attributes", "publisher_identity")
    membership_rows = client.fetch_all("transport_source_memberships", "snapshot_id,node_id,place_id,publisher_node_identity,publisher_place_identity,membership_key,resolution_status,duplicate_occurrence_count,source_attributes", "membership_key")
    parent_rows = client.fetch_all("transport_source_place_parents", "snapshot_id,child_place_id,parent_place_id,publisher_child_identity,publisher_parent_identity,parent_edge_key,resolution_status,duplicate_occurrence_count,source_attributes", "parent_edge_key")

    place_ids = {row["publisher_identity"]: row.get("id") for row in client.fetch_all("transport_source_places", "id,publisher_identity", "publisher_identity")}
    node_ids = {row["publisher_identity"]: row.get("id") for row in client.fetch_all("transport_source_nodes", "id,publisher_identity", "publisher_identity")}
    expected_places = _expected_place_rows(model, snapshot_id)
    expected_nodes = _expected_node_rows(model, snapshot_id)
    expected_memberships: dict[str, dict[str, Any]] = {}
    for row in model["_membership_rows"]:
        expected_memberships[row["membership_key"]] = {
            "snapshot_id": snapshot_id,
            "node_id": node_ids.get(row["publisher_node_identity"]),
            "place_id": place_ids.get(row["publisher_place_identity"]),
            **_strip_private(row),
        }
    expected_parents: dict[str, dict[str, Any]] = {}
    for row in model["_parent_rows"]:
        expected_parents[row["parent_edge_key"]] = {
            "snapshot_id": snapshot_id,
            "child_place_id": place_ids.get(row["publisher_child_identity"]),
            "parent_place_id": place_ids.get(row["publisher_parent_identity"]),
            **_strip_private(row),
        }

    def differences(rows: list[dict[str, Any]], expected: dict[str, dict[str, Any]], key: str) -> list[dict[str, Any]]:
        actual_by_key = {row[key]: row for row in rows}
        diff: list[dict[str, Any]] = []
        if set(actual_by_key) != set(expected):
            diff.append({"key": key, "missing": len(set(expected) - set(actual_by_key)), "unexpected": len(set(actual_by_key) - set(expected))})
        for row_key in sorted(set(expected) & set(actual_by_key)):
            actual_row = actual_by_key[row_key]
            expected_row = expected[row_key]
            mismatched = {
                field: {"expected": expected_row.get(field), "actual": actual_row.get(field)}
                for field in expected_row
                if not _semantically_equal(expected_row.get(field), actual_row.get(field))
            }
            if mismatched:
                diff.append({"key": row_key, "fields": mismatched})
                if len(diff) >= 20:
                    break
        return diff

    checks = {
        "snapshot_metadata_differences": snapshot_differences,
        "place_differences": differences(place_rows, expected_places, "publisher_identity"),
        "node_differences": differences(node_rows, expected_nodes, "publisher_identity"),
        "membership_differences": differences(membership_rows, expected_memberships, "membership_key"),
        "parent_differences": differences(parent_rows, expected_parents, "parent_edge_key"),
    }
    if any(checks.values()):
        raise N5R2Error(f"identical replay comparison found differences: {json.dumps(checks, sort_keys=True)[:6000]}")
    result = {
        "classification": "SECOND_PASS_ZERO_MUTATIONS",
        "proposed_new_rows": {"snapshots": 0, "places": 0, "nodes": 0, "memberships": 0, "parent_edges": 0},
        "conflicts": 0,
        "differing_existing_publisher_rows": 0,
        "gratuitous_updates": 0,
        "canonical_changes": 0,
        "read_only": True,
        "production_rows_compared": {"snapshots": len(snapshot_rows), "places": len(place_rows), "nodes": len(node_rows), "memberships": len(membership_rows), "parent_edges": len(parent_rows)},
        "checks": {key: value for key, value in checks.items()},
    }
    write_json(evidence_path, result)
    return result


def plan_summary(model: dict[str, Any], target_counts: dict[str, int] | None = None) -> dict[str, Any]:
    return {
        "classification": "CORRECTED_N5_R1_CONTRACT_REPRODUCED",
        "source": model["source"],
        "contract_version": model["contract_version"],
        "source_snapshot_key": model["source_snapshot_key"],
        "source_url": model["source_url"],
        "retrieved_at": model["retrieved_at"],
        "licence": model["licence"],
        "attribution": model["attribution"],
        "parser_version": model["parser_version"],
        "values": model["values"],
        "mode_distribution": model["mode_distribution"],
        "complex_type_distribution": model["complex_type_distribution"],
        "duplicate_membership_keys": model["duplicate_membership_keys"],
        "duplicate_membership_counts": model["duplicate_membership_counts"],
        "n3_projection": model["n3_projection"],
        "expected_counts": model["expected_counts"],
        "target_counts_before_write": target_counts,
        "proposed_new_rows": {"snapshots": 1, "places": 97_270, "nodes": 436_428, "memberships": 169_527, "parent_edges": 3_519},
        "mutation_table_allowlist": list(TABLES),
        "prohibited_tables": sorted(NON_SOURCE_TABLES),
        "production_mutations_in_plan": 0,
        "apply_required": True,
        "superseded_membership_expectation_not_used": True,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Plan or explicitly apply the governed N5-R2 NaPTAN source graph")
    parser.add_argument("source", type=Path)
    parser.add_argument("--repo-root", type=Path, default=Path.cwd())
    parser.add_argument("--contract", type=Path, required=True)
    parser.add_argument("--base-url", default=EXPECTED_BASE_URL)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--progress", type=Path)
    parser.add_argument("--idempotency-out", type=Path)
    parser.add_argument("--batch-size", type=int, default=2_000)
    parser.add_argument("--apply", action="store_true", help="explicitly enable production DML")
    parser.add_argument("--verify", action="store_true", help="read-only compare the production graph with the exact source")
    args = parser.parse_args()
    if args.batch_size < 100 or args.batch_size > 5_000:
        raise SystemExit("--batch-size must be between 100 and 5000")
    if args.apply and args.verify:
        raise SystemExit("--apply and --verify are mutually exclusive")
    expected_hash = n4a_hash(args.repo_root)
    if expected_hash != N4A_SHA256:
        raise SystemExit(f"sealed N4A migration hash mismatch: {expected_hash}")
    contract = load_contract(args.contract)
    model = build_source_model(args.source, contract)
    api_key = os.environ.get("N5_SERVICE_ROLE_KEY", "")
    target_counts = None
    client = None
    if api_key:
        client = RestClient(args.base_url, api_key)
        target_counts = {table: client.count(table) for table in TABLES}
    elif args.apply or args.verify:
        raise SystemExit("N5_SERVICE_ROLE_KEY is required for --apply/--verify")
    summary = plan_summary(model, target_counts)
    write_json(args.out, summary)
    if args.apply:
        assert client is not None
        if any(target_counts.values()):
            raise SystemExit(f"SOURCE GRAPH IS NOT EMPTY: {target_counts}")
        before_hash = n4a_hash(args.repo_root)
        if before_hash != N4A_SHA256:
            raise SystemExit(f"sealed N4A migration changed before DML: {before_hash}")
        progress_path = args.progress or args.out.with_name(args.out.stem + "_progress.json")
        result = apply_model(model, client, progress_path, args.batch_size)
        if n4a_hash(args.repo_root) != N4A_SHA256:
            raise SystemExit("sealed N4A migration changed after DML")
        print(json.dumps({"status": result["status"], "final_counts": result["final_counts"], "progress": str(progress_path)}, sort_keys=True))
    elif args.verify:
        assert client is not None
        evidence_path = args.idempotency_out or args.out.with_name(args.out.stem + "_idempotency.json")
        result = verify_existing_graph(model, client, evidence_path)
        print(json.dumps({"classification": result["classification"], "rows_compared": result["production_rows_compared"], "evidence": str(evidence_path)}, sort_keys=True))
    else:
        print(json.dumps({"mode": "plan-only", "out": str(args.out), "target_counts_before_write": target_counts, "expected_total_rows": EXPECTED_VALUES["total_stored_source_graph_rows"]}, sort_keys=True))


if __name__ == "__main__":
    try:
        main()
    except (N5R2Error, OSError, ValueError, json.JSONDecodeError) as error:
        print(f"N5-R2 STOP: {error}", file=sys.stderr)
        raise SystemExit(2)

"""Read-only normalization and evidence for additional public toilet sources.

This module intentionally stops before canonical matching writes.  It accepts a
local source snapshot, emits normalized evidence, and marks records that lack
the identity/coordinates required for a future governed ingestion.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

from tools.source_refresh.framework import canonical_json, load_registry, sha256_bytes, snapshot_bytes


TOOL_VERSION = "relief.uk-public-source-expansion.v1"
COORDINATE_TOLERANCE_DEGREES = 0.0005


def _clean(value: Any) -> str | None:
    text = "" if value is None else str(value).strip()
    return text or None


def _slug(value: str) -> str:
    value = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
    return value or "unnamed"


def _bool_or_none(value: Any) -> bool | None:
    text = _clean(value)
    if text is None:
        return None
    if text.lower() in {"yes", "true", "1", "y", "available"}:
        return True
    if text.lower() in {"no", "false", "0", "n", "unavailable"}:
        return False
    return None


def _number(value: Any) -> float | None:
    text = _clean(value)
    if text is None:
        return None
    try:
        return float(text)
    except ValueError:
        return None


def normalize_tfl_bus_rows(rows: Iterable[dict[str, Any]], source_id: str) -> list[dict[str, Any]]:
    """Normalize the public TfL example without inventing station coordinates."""
    normalized = []
    for row in rows:
        name = _clean(row.get("BUS STATIONS") or row.get("station") or row.get("name"))
        if not name:
            continue
        toilets = _bool_or_none(row.get("PUBLIC TOILETS") or row.get("public_toilets"))
        normalized.append({
            "source_id": source_id,
            "source_record_id": f"station:{_slug(name)}",
            "name": name,
            "address": None,
            "postcode": None,
            "town": "London",
            "latitude": None,
            "longitude": None,
            "is_free": None,
            "is_accessible": None,
            "has_baby_changing": None,
            "access_notes": _clean(row.get("NOTES") or row.get("notes")),
            "source_boolean_public_toilets": toilets,
            "normalization_status": "ENRICHMENT_ONLY_MISSING_COORDINATES",
            "validation_errors": ["missing latitude/longitude; do not insert as a facility"],
        })
    return normalized


def normalize_esd_rows(rows: Iterable[dict[str, Any]], source_id: str) -> list[dict[str, Any]]:
    """Normalize the common Local Government Association Public Toilets schema."""
    normalized = []
    for index, row in enumerate(rows, start=1):
        name = _clean(row.get("LocationText") or row.get("Name") or row.get("name"))
        record_id = _clean(row.get("UPRN") or row.get("uprn") or row.get("id")) or f"row-{index}"
        latitude = _number(row.get("Latitude") or row.get("latitude") or row.get("__latitude"))
        longitude = _number(row.get("Longitude") or row.get("longitude") or row.get("__longitude"))
        errors = []
        if not name:
            errors.append("missing name")
        if latitude is None or longitude is None:
            errors.append("missing WGS84 latitude/longitude; OSGB36 GeoX/GeoY cannot be treated as WGS84")
        normalized.append({
            "source_id": source_id,
            "source_record_id": record_id,
            "name": name,
            "address": _clean(row.get("StreetAddress") or row.get("Address") or row.get("address")),
            "postcode": _clean(row.get("Postcode") or row.get("postcode")),
            "town": _clean(row.get("GeoAreaLabel") or row.get("town")),
            "latitude": latitude,
            "longitude": longitude,
            "is_free": None if _clean(row.get("ChargeAmount")) in {None, "Not set"} else False,
            "is_accessible": _bool_or_none(row.get("AccessibleCategory") or row.get("Accessible")),
            "has_baby_changing": _bool_or_none(row.get("BabyChange")),
            "requires_radar_key": _bool_or_none(row.get("RADARKeyNeeded")),
            "access_notes": _clean(row.get("Notes")),
            "source_updated_at": _clean(row.get("ExtractDate") or row.get("Updated")),
            "normalization_status": "NORMALIZED_WITH_WARNINGS" if errors else "NORMALIZED",
            "validation_errors": errors,
        })
    return normalized


def normalize_rows(source_id: str, rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    if source_id == "tfl_bus_public_toilets":
        return normalize_tfl_bus_rows(rows, source_id)
    return normalize_esd_rows(rows, source_id)


def _coordinate_key(row: dict[str, Any]) -> tuple[int, int] | None:
    lat, lon = row.get("latitude"), row.get("longitude")
    if lat is None or lon is None:
        return None
    return (round(float(lat) / COORDINATE_TOLERANCE_DEGREES), round(float(lon) / COORDINATE_TOLERANCE_DEGREES))


def analyze_duplicates(records: list[dict[str, Any]]) -> dict[str, Any]:
    by_id: dict[str, list[dict[str, Any]]] = defaultdict(list)
    by_coordinate: dict[tuple[int, int], list[str]] = defaultdict(list)
    for record in records:
        by_id[str(record["source_record_id"])].append(record)
        key = _coordinate_key(record)
        if key:
            by_coordinate[key].append(str(record["source_record_id"]))
    duplicate_ids = sorted(identifier for identifier, group in by_id.items() if len(group) > 1)
    coordinate_collisions = sorted(sorted(ids) for ids in by_coordinate.values() if len(ids) > 1)
    return {
        "duplicate_source_record_ids": duplicate_ids,
        "coordinate_collision_groups": coordinate_collisions,
        "duplicate_count": len(duplicate_ids),
        "coordinate_collision_count": len(coordinate_collisions),
    }


def compare_with_production(records: list[dict[str, Any]], production_rows: list[dict[str, Any]]) -> dict[str, Any]:
    """Perform only conservative identity/coordinate comparisons on a read-only snapshot."""
    existing_exact = set()
    existing_names: Counter[str] = Counter()
    for row in production_rows:
        source_id = _clean(row.get("source_record_id"))
        if source_id:
            existing_exact.add(source_id)
        name = _clean(row.get("name"))
        if name:
            existing_names[name.casefold()] += 1
    exact = [record["source_record_id"] for record in records if record["source_record_id"] in existing_exact]
    same_name = [record["source_record_id"] for record in records if record.get("name") and existing_names[record["name"].casefold()]]
    return {
        "production_snapshot_rows": len(production_rows),
        "exact_source_record_matches": sorted(set(exact)),
        "same_name_matches_not_resolved": sorted(set(same_name)),
        "match_policy": "source identity only; name-only matches remain unresolved and require review",
    }


def build_report(source: dict[str, Any], records: list[dict[str, Any]], *, raw_checksum: str, retrieved_at: str, source_version: str | None, production_rows: list[dict[str, Any]] | None = None, production_match_summary: dict[str, Any] | None = None) -> dict[str, Any]:
    duplicate_report = analyze_duplicates(records)
    status_counts = Counter(record["normalization_status"] for record in records)
    errors = Counter(error for record in records for error in record.get("validation_errors", []))
    decisions = Counter("REVIEW_REQUIRED" if record.get("validation_errors") else "PREPARE_FOR_MATCHING" for record in records)
    production_reconciliation = compare_with_production(records, production_rows or [])
    if production_match_summary:
        production_reconciliation.update(production_match_summary)
    report = {
        "tool_version": TOOL_VERSION,
        "classification": "UK PUBLIC SOURCE EXPANSION — DISCOVERY / INGESTION PREPARATION / PRODUCTION APPLY NOT AUTHORIZED",
        "source": {
            "source_id": source["source_id"],
            "source_name": source["source_name"],
            "publisher": source["publisher"],
            "source_url": source["source_url"],
            "licence_identifier": source["licence_identifier"],
            "licence_url": source["licence_url"],
            "required_attribution": source["required_attribution"],
            "source_version": source_version,
            "retrieved_at": retrieved_at,
            "raw_checksum": raw_checksum,
        },
        "record_counts": {
            "received": len(records),
            "normalization_status": dict(sorted(status_counts.items())),
            "decision_counts": dict(sorted(decisions.items())),
            "validation_errors": dict(sorted(errors.items())),
        },
        "duplicate_analysis": duplicate_report,
        "production_reconciliation": production_reconciliation,
        "null_semantics": "Unknown source values remain null; no false boolean or coordinate certainty is introduced.",
        "mutations": {
            "canonical_mutations": 0,
            "production_mutations": 0,
            "facility_inserts": 0,
            "facility_updates": 0,
            "facility_deletes": 0,
            "facility_source_mutations": 0,
            "provenance_mutations": 0,
            "import_run_mutations": 0,
            "staging_mutations": 0,
        },
        "records": records,
    }
    return report


def _read_rows(path: Path) -> list[dict[str, Any]]:
    if path.suffix.lower() in {".json", ".geojson"}:
        value = json.loads(path.read_text(encoding="utf-8"))
        if isinstance(value, dict):
            value = value.get("features", value.get("records", value.get("data", [])))
            if value and isinstance(value[0], dict) and "properties" in value[0]:
                converted = []
                for item in value:
                    row = dict(item["properties"])
                    geometry = item.get("geometry") or {}
                    coordinates = geometry.get("coordinates") if isinstance(geometry, dict) else None
                    if geometry.get("type") == "Point" and isinstance(coordinates, list) and len(coordinates) >= 2:
                        row["__longitude"] = coordinates[0]
                        row["__latitude"] = coordinates[1]
                    converted.append(row)
                value = converted
        if not isinstance(value, list):
            raise ValueError("input JSON must contain records, data, or GeoJSON features")
        return [dict(row) for row in value]
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return [dict(row) for row in csv.DictReader(handle)]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build read-only UK public-source expansion evidence")
    parser.add_argument("--registry", default=str(Path(__file__).with_name("source_registry.json")))
    parser.add_argument("--source-id", required=True)
    parser.add_argument("--input", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--snapshot-root", default=str(Path(__file__).with_name("cache")))
    parser.add_argument("--production-snapshot", help="Optional JSON list of public facility rows from a read-only query")
    parser.add_argument("--retrieved-at", default=datetime.now(timezone.utc).isoformat())
    parser.add_argument("--source-version")
    parser.add_argument("--nearby-match-count", type=int, help="Read-only production count for source rows with a facility within the agreed proximity window")
    parser.add_argument("--no-nearby-match-count", type=int, help="Read-only production count for source rows without a facility within the agreed proximity window")
    parser.add_argument("--exact-source-link-count", type=int, help="Read-only production count for exact source-record links")
    args = parser.parse_args(argv)
    registry = load_registry(Path(args.registry))
    source = registry[args.source_id]
    payload = Path(args.input).read_bytes()
    metadata = snapshot_bytes(payload, args.source_id, Path(args.snapshot_root), retrieved_at=args.retrieved_at, source_file_or_api_version=args.source_version, parser_normalizer_version=source["parser_normalizer_version"])
    production_rows = json.loads(Path(args.production_snapshot).read_text(encoding="utf-8")) if args.production_snapshot else []
    production_match_summary = {
        "production_snapshot_scope": "read-only source-row proximity aggregate supplied from production SQL; approximate 100m latitude/longitude bounding window",
    }
    if args.nearby_match_count is not None:
        production_match_summary["nearby_within_approx_100m"] = args.nearby_match_count
    if args.no_nearby_match_count is not None:
        production_match_summary["no_nearby_within_approx_100m"] = args.no_nearby_match_count
    if args.exact_source_link_count is not None:
        production_match_summary["exact_source_links"] = args.exact_source_link_count
    report = build_report(source, normalize_rows(args.source_id, _read_rows(Path(args.input))), raw_checksum=sha256_bytes(payload), retrieved_at=args.retrieved_at, source_version=args.source_version, production_rows=production_rows, production_match_summary=production_match_summary)
    report["snapshot_metadata"] = metadata
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(canonical_json(report) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

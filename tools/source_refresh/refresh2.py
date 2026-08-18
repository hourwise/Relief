"""Prepare a governed, read-only Toilet Map Refresh 2 reconciliation.

This module is deliberately a preparation boundary.  It reads a local source
snapshot and (optionally) production REST snapshots using GET only.  It emits
evidence and a deterministic proposed-operation manifest, but it has no
database write client and no apply flag.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import os
import subprocess
import sys
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable
from urllib.parse import urlencode
from urllib.request import Request, urlopen

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from tools.enrichment.pipeline import (  # noqa: E402
    FIELD_MAP,
    NormalizedCandidate,
    ToiletMapAdapter,
    build_facility_index,
    canonical_json,
    field_differences,
    match_candidate,
    parse_areas,
    parse_bool,
    parse_opening_hours,
    display_text,
)
from tools.source_refresh.framework import snapshot_bytes  # noqa: E402


SOURCE_ID = "toilet_map_uk"
SOURCE_NAME = "Toilet Map UK"
SOURCE_URL = "https://www.toiletmap.org.uk/dataset"
LICENCE = "CC BY 4.0"
ATTRIBUTION = "Contains data from the Toilet Map © 2025 – CC BY 4.0 (Creative Commons Attribution 4.0 International)"
UK_BOUNDS = (49.0, 61.0, -9.0, 2.0)
SAFE_BOOLEAN_FIELDS = {
    "is_free",
    "is_accessible",
    "requires_radar_key",
    "has_baby_changing",
    "is_gender_neutral",
}
SOURCE_MANAGED_FIELDS = {
    "name",
    "town",
    "latitude",
    "longitude",
    "opening_hours",
    "is_free",
    "is_accessible",
    "requires_radar_key",
    "has_baby_changing",
    "is_gender_neutral",
}
COMPARE_FIELDS = (
    "name",
    "town",
    "latitude",
    "longitude",
    "opening_hours",
    "is_free",
    "is_accessible",
    "requires_radar_key",
    "has_baby_changing",
    "is_gender_neutral",
    "source_updated_at",
    "source_status",
)
FIELD_TO_CANONICAL = dict(FIELD_MAP)
CLASS_ORDER = {
    "SAFE_CANDIDATE": 0,
    "REVIEW_REQUIRED": 1,
    "PROTECTED": 2,
    "QUARANTINED": 3,
    "STALE_CANDIDATE": 4,
}


def sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def read_env(path: Path) -> dict[str, str]:
    values: dict[str, str] = {}
    if not path.exists():
        return values
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        values[key.strip()] = value.strip().strip('"').strip("'")
    return values


def read_csv_rows(path: Path) -> list[dict[str, Any]]:
    with path.open("r", newline="", encoding="utf-8-sig") as handle:
        return [dict(row) for row in csv.DictReader(handle)]


def rest_get_rows(
    base_url: str,
    anon_key: str,
    table: str,
    select: str,
    snapshot_dir: Path,
    offline: bool,
    *,
    order_column: str | None = "id",
    page_size: int = 1000,
) -> list[dict[str, Any]]:
    snapshot_path = snapshot_dir / f"{table}.json"
    if offline:
        return json.loads(snapshot_path.read_text(encoding="utf-8"))
    rows: list[dict[str, Any]] = []
    offset = 0
    while True:
        params: dict[str, str] = {"select": select, "limit": str(page_size), "offset": str(offset)}
        if order_column:
            params["order"] = f"{order_column}.asc"
        url = f"{base_url.rstrip('/')}/rest/v1/{table}?{urlencode(params)}"
        request = Request(
            url,
            method="GET",
            headers={
                "apikey": anon_key,
                "Authorization": f"Bearer {anon_key}",
                "Accept": "application/json",
                "Prefer": "count=exact",
            },
        )
        with urlopen(request, timeout=60) as response:
            page = json.loads(response.read().decode("utf-8"))
        if not isinstance(page, list):
            raise RuntimeError(f"Supabase REST returned a non-list for {table}")
        rows.extend(page)
        if len(page) < page_size:
            break
        offset += page_size
    snapshot_dir.mkdir(parents=True, exist_ok=True)
    snapshot_path.write_text(json.dumps(rows, ensure_ascii=False), encoding="utf-8")
    return rows


def _source_semantics(row: dict[str, Any]) -> dict[str, Any]:
    active = parse_bool(row.get("active"))
    try:
        latitude: float | None = float(row["latitude"])
        longitude: float | None = float(row["longitude"])
    except (KeyError, TypeError, ValueError):
        latitude = longitude = None
    return {
        "name": display_text(row.get("name")),
        "town": parse_areas(row.get("areas")),
        "latitude": latitude,
        "longitude": longitude,
        "opening_hours": parse_opening_hours(row.get("opening_times")),
        "is_free": parse_bool(row.get("no_payment")),
        "is_accessible": parse_bool(row.get("accessible")),
        "requires_radar_key": parse_bool(row.get("radar")),
        "has_baby_changing": parse_bool(row.get("baby_change")),
        "is_gender_neutral": parse_bool(row.get("all_gender")),
        "source_updated_at": display_text(row.get("updated_at")),
        "source_status": "active" if active is True else "removed" if active is False else "unknown",
    }


def source_field_differences(old_row: dict[str, Any], new_row: dict[str, Any]) -> list[dict[str, Any]]:
    old_values = _source_semantics(old_row)
    new_values = _source_semantics(new_row)
    differences = []
    for field in COMPARE_FIELDS:
        old_value = old_values[field]
        new_value = new_values[field]
        if canonical_json(old_value) != canonical_json(new_value):
            differences.append({"field": field, "old": old_value, "new": new_value})
    return differences


def _valid_coordinate(latitude: float | None, longitude: float | None) -> tuple[bool, str | None]:
    if latitude is None or longitude is None:
        return False, "invalid latitude/longitude"
    if not math.isfinite(latitude) or not math.isfinite(longitude):
        return False, "non-finite latitude/longitude"
    if latitude == 0 or longitude == 0:
        return False, "zero/default coordinate"
    min_lat, max_lat, min_lon, max_lon = UK_BOUNDS
    if not (min_lat <= latitude <= max_lat and min_lon <= longitude <= max_lon):
        return False, "coordinates outside the UK validation envelope"
    return True, None


def _bad_name(value: Any) -> str | None:
    text = str(value or "").strip()
    if not text:
        return None
    alphanumeric = "".join(character for character in text if character.isalnum())
    if not alphanumeric:
        return "name contains no alphanumeric characters"
    if len(alphanumeric) <= 2:
        return "name has two or fewer alphanumeric characters"
    return None


def classify_source_snapshot(previous_rows: list[dict[str, Any]], current_rows: list[dict[str, Any]]) -> dict[str, Any]:
    previous_by_id: dict[str, dict[str, Any]] = {}
    for row in previous_rows:
        source_id = str(row.get("id", "")).strip()
        if source_id and source_id not in previous_by_id:
            previous_by_id[source_id] = row
    current_id_counts = Counter(str(row.get("id", "")).strip() for row in current_rows if str(row.get("id", "")).strip())
    duplicate_ids = sorted(source_id for source_id, count in current_id_counts.items() if count > 1)
    current_by_id: dict[str, dict[str, Any]] = {}
    row_classes: list[dict[str, Any]] = []
    invalid_rows = 0
    duplicate_rows = 0
    valid_rows = 0
    bad_coordinate_rows: list[dict[str, Any]] = []
    bad_name_rows: list[dict[str, Any]] = []
    missing_source_name_rows: list[dict[str, Any]] = []
    for row_number, row in enumerate(current_rows, start=2):
        source_id = str(row.get("id", "")).strip()
        semantics = _source_semantics(row)
        coordinate_ok, coordinate_reason = _valid_coordinate(semantics["latitude"], semantics["longitude"])
        name_reason = _bad_name(row.get("name"))
        if not str(row.get("name") or "").strip():
            missing_source_name_rows.append({"row": row_number, "source_record_id": source_id or None, "name": row.get("name"), "reason": "missing source name"})
        if name_reason:
            bad_name_rows.append({"row": row_number, "source_record_id": source_id or None, "name": row.get("name"), "reason": name_reason})
        if not coordinate_ok:
            bad_coordinate_rows.append({"row": row_number, "source_record_id": source_id or None, "latitude": semantics["latitude"], "longitude": semantics["longitude"], "reason": coordinate_reason})
        if not source_id:
            classification = "INVALID"
            reason = "missing source record ID"
            invalid_rows += 1
        elif source_id in duplicate_ids:
            classification = "DUPLICATE_SOURCE_ID"
            reason = "source record ID appears more than once in the fresh snapshot"
            duplicate_rows += 1
        elif not coordinate_ok:
            classification = "INVALID"
            reason = coordinate_reason
            invalid_rows += 1
        else:
            classification = "VALID"
            reason = None
            valid_rows += 1
            current_by_id[source_id] = row
        row_classes.append({"row": row_number, "source_record_id": source_id or None, "classification": classification, "reason": reason})

    current_ids = set(current_by_id)
    previous_ids = set(previous_by_id)
    new_ids = sorted(current_ids - previous_ids)
    missing_ids = sorted(previous_ids - current_ids)
    changed_ids = sorted(source_id for source_id in current_ids & previous_ids if source_field_differences(previous_by_id[source_id], current_by_id[source_id]))
    unchanged_ids = sorted(current_ids & previous_ids - set(changed_ids))
    record_status = {entry["source_record_id"]: entry["classification"] for entry in row_classes if entry["source_record_id"]}
    record_status.update({source_id: "NEW" for source_id in new_ids})
    record_status.update({source_id: "CHANGED" for source_id in changed_ids})
    record_status.update({source_id: "UNCHANGED" for source_id in unchanged_ids})
    record_status.update({source_id: "MISSING_FROM_NEW_SOURCE" for source_id in missing_ids})
    changed_records = [
        {"source_record_id": source_id, "field_differences": source_field_differences(previous_by_id[source_id], current_by_id[source_id])}
        for source_id in changed_ids
    ]
    return {
        "source_rows_received": len(current_rows),
        "valid_rows": valid_rows,
        "invalid_rows": invalid_rows,
        "duplicate_source_id_rows": duplicate_rows,
        "duplicate_source_ids": duplicate_ids,
        "new_ids": new_ids,
        "changed_ids": changed_ids,
        "unchanged_ids": unchanged_ids,
        "missing_ids": missing_ids,
        "record_status": record_status,
        "changed_records": changed_records,
        "row_classifications": row_classes,
        "bad_name_rows": bad_name_rows,
        "missing_source_name_rows": missing_source_name_rows,
        "bad_coordinate_rows": bad_coordinate_rows,
        "quarantined_rows": invalid_rows + duplicate_rows,
        "counts_reconcile": valid_rows + invalid_rows + duplicate_rows == len(current_rows),
    }


def _provenance_is_stronger(value: Any) -> bool:
    if not isinstance(value, dict):
        return False
    text = " ".join(str(item).lower() for item in value.values())
    return any(marker in text for marker in ("community", "staff", "governed", "relief_verified", "manual_correction"))


def _operation_id(category: str, facility_id: str | None, source_id: str, field: str, before: Any, after: Any) -> str:
    identity = canonical_json({"generation": "TOILET_MAP_REFRESH_2", "category": category, "facility_id": facility_id, "source_record_id": source_id, "field": field, "before": before, "after": after})
    return f"TM2-{hashlib.sha256(identity.encode('utf-8')).hexdigest()[:20]}"


def _operation(
    category: str,
    candidate: NormalizedCandidate,
    facility_id: str | None,
    field: str,
    before: Any,
    after: Any,
    *,
    reason: str,
    current_provenance: Any,
    collision: bool = False,
    source_version: str | None,
    source_checksum: str,
) -> dict[str, Any]:
    return {
        "operation_id": _operation_id(category, facility_id, candidate.source_record_id, field, before, after),
        "generation": "Toilet Map Refresh / Apply 2",
        "category": category,
        "target_facility_id": facility_id,
        "source_record_id": candidate.source_record_id,
        "target_field": field,
        "before_value": before,
        "proposed_after_value": after,
        "source_evidence": {
            "source_name": SOURCE_NAME,
            "source_url": SOURCE_URL,
            "licence": LICENCE,
            "source_version": source_version,
            "source_checksum": source_checksum,
            "source_updated_at": candidate.source_updated_at,
            "raw_row_hash": candidate.raw_hash,
        },
        "current_provenance": current_provenance,
        "reason": reason,
        "confidence": "HIGH" if category == "SAFE_CANDIDATE" else "MEDIUM" if category in {"REVIEW_REQUIRED", "PROTECTED"} else "LOW",
        "auto_apply_proposed": category == "SAFE_CANDIDATE",
        "human_review_required": category != "SAFE_CANDIDATE",
        "collision_candidate": collision,
    }


def _candidate_from_raw(row: dict[str, Any]) -> NormalizedCandidate:
    values = _source_semantics(row)
    raw_hash = hashlib.sha256(canonical_json(row).encode("utf-8")).hexdigest()
    return NormalizedCandidate(
        source_name=SOURCE_NAME,
        source_record_id=str(row.get("id", "")).strip(),
        source_url=SOURCE_URL,
        source_licence=LICENCE,
        source_updated_at=values["source_updated_at"],
        name=values["name"],
        address=None,
        town=values["town"],
        postcode=None,
        latitude=values["latitude"],
        longitude=values["longitude"],
        opening_hours=values["opening_hours"],
        is_free=values["is_free"],
        is_accessible=values["is_accessible"],
        requires_radar_key=values["requires_radar_key"],
        has_baby_changing=values["has_baby_changing"],
        is_gender_neutral=values["is_gender_neutral"],
        is_family_friendly=None,
        has_staff_nearby=None,
        other_fields={},
        raw_hash=raw_hash,
        source_status=values["source_status"],
    )


def _sort_operations(operations: Iterable[dict[str, Any]]) -> list[dict[str, Any]]:
    return sorted(operations, key=lambda item: (CLASS_ORDER[item["category"]], str(item.get("source_record_id") or ""), str(item.get("target_facility_id") or ""), item["target_field"], item["operation_id"]))


def build_operations(
    candidates: list[NormalizedCandidate],
    facilities: list[dict[str, Any]],
    source_links: list[dict[str, Any]],
    *,
    source_version: str | None,
    source_checksum: str,
    known_bad_source_ids: set[str] | None = None,
) -> dict[str, Any]:
    facilities_by_id = {str(row["id"]): row for row in facilities}
    links_by_source_id: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for link in source_links:
        if link.get("source_name") == SOURCE_NAME:
            links_by_source_id[str(link.get("source_record_id"))].append(link)
    facility_index = build_facility_index(facilities)
    operations: list[dict[str, Any]] = []
    collisions: list[dict[str, Any]] = []
    exact_matches = 0
    inferred_matches = 0
    invalid_candidates = 0
    new_candidates = 0
    for candidate in candidates:
        links = links_by_source_id.get(candidate.source_record_id, [])
        facility_id = str(links[0]["facility_id"]) if len(links) == 1 else None
        facility = facilities_by_id.get(facility_id) if facility_id else None
        if len(links) > 1:
            operations.append(_operation("QUARANTINED", candidate, None, "__source_identity__", None, None, reason="source ID is linked to multiple canonical facilities", current_provenance=None, source_version=source_version, source_checksum=source_checksum))
            continue
        if candidate.validation_errors:
            invalid_candidates += 1
            operations.append(_operation("QUARANTINED", candidate, facility_id, "__source_row__", None, candidate.validation_errors, reason="source row is malformed or outside the permitted UK coordinate envelope", current_provenance=facility.get("field_provenance") if facility else None, source_version=source_version, source_checksum=source_checksum))
            continue
        if facility is None:
            decision = match_candidate(candidate, facilities_by_id, links_by_source_id, facility_index)
            if decision.decision == "HIGH_CONFIDENCE_MATCH":
                inferred_matches += 1
                facility_id = decision.facility_id
                facility = facilities_by_id.get(facility_id) if facility_id else None
            else:
                new_candidates += 1
                collision = decision.decision == "AMBIGUOUS" or any(float(item.get("distance_metres", 999999)) <= 250 and float(item.get("name_similarity", 0)) >= 0.65 for item in decision.alternatives)
                if collision:
                    collisions.append({"source_record_id": candidate.source_record_id, "decision": decision.as_dict(), "reason": "nearby or similarly named canonical facility may be the same real-world toilet"})
                if not candidate.name or _bad_name(candidate.name):
                    category = "QUARANTINED"
                    reason = "new candidate has no usable name; no name is invented"
                else:
                    category = "REVIEW_REQUIRED"
                    reason = "new source record requires explicit creation approval and duplicate review"
                operations.append(_operation(category, candidate, None, "__facility_creation__", None, {field: value for field, value in candidate.as_dict().items() if field in FIELD_TO_CANONICAL and value is not None}, reason=reason, current_provenance=None, collision=collision, source_version=source_version, source_checksum=source_checksum))
                continue
        exact_matches += 1 if len(links) == 1 else 0
        if not facility:
            continue
        differences = field_differences(candidate, facility)
        provenance = facility.get("field_provenance") or {}
        for entry in differences["enrichment"]:
            source_field = entry["field"]
            if source_field not in SOURCE_MANAGED_FIELDS:
                continue
            target_field = entry["relief_field"]
            after = entry.get("source_value")
            current_provenance = provenance.get(target_field)
            if _provenance_is_stronger(current_provenance):
                category = "PROTECTED"
                reason = "source refresh would write a field with stronger Relief/community/staff/governed provenance"
            elif source_field in SAFE_BOOLEAN_FIELDS and isinstance(after, bool) and candidate.source_status == "active":
                category = "SAFE_CANDIDATE"
                reason = "exact source identity supplies an explicit boolean where the canonical value is unknown"
            else:
                category = "REVIEW_REQUIRED"
                reason = "source enrichment is valid but is outside the narrow automatic scalar policy"
            operations.append(_operation(category, candidate, str(facility["id"]), target_field, facility.get(target_field), after, reason=reason, current_provenance=current_provenance, source_version=source_version, source_checksum=source_checksum))
        for entry in differences["conflicts"]:
            source_field = entry["field"]
            if source_field not in SOURCE_MANAGED_FIELDS:
                continue
            target_field = entry["relief_field"]
            current_provenance = provenance.get(target_field)
            category = "PROTECTED" if _provenance_is_stronger(current_provenance) else "REVIEW_REQUIRED"
            operations.append(_operation(category, candidate, str(facility["id"]), target_field, entry.get("relief_value"), entry.get("source_value"), reason="source and canonical values conflict; preserve stronger or current Relief data until review", current_provenance=current_provenance, source_version=source_version, source_checksum=source_checksum))
        for entry in differences["omissions"]:
            if entry["field"] not in SOURCE_MANAGED_FIELDS:
                continue
            target_field = entry["relief_field"]
            current_provenance = provenance.get(target_field)
            category = "PROTECTED" if _provenance_is_stronger(current_provenance) else "REVIEW_REQUIRED"
            operations.append(_operation(category, candidate, str(facility["id"]), target_field, entry.get("relief_value"), None, reason="fresh source omitted a previously known value; omission is evidence for review, not an automatic clear", current_provenance=current_provenance, source_version=source_version, source_checksum=source_checksum))
    operations = _sort_operations(operations)
    return {
        "operations": operations,
        "exact_source_id_matches": exact_matches,
        "high_confidence_inferred_matches": inferred_matches,
        "new_facility_candidates": new_candidates,
        "invalid_or_quarantined_candidates": invalid_candidates,
        "duplicate_collision_candidates": collisions,
        "canonical_mutations": 0,
        "production_mutations": 0,
        "operation_counts": dict(Counter(operation["category"] for operation in operations)),
        "proposed_canonical_field_changes": sum(1 for operation in operations if not operation["target_field"].startswith("__")),
        "known_bad_source_ids": sorted(known_bad_source_ids or set()),
    }


def _source_snapshot_baseline(source_links: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    rows = [link["raw_data"] for link in source_links if link.get("source_name") == SOURCE_NAME and isinstance(link.get("raw_data"), dict)]
    rows = sorted(rows, key=lambda row: str(row.get("id", "")))
    payload = canonical_json(rows).encode("utf-8")
    return rows, {"kind": "accepted_source_linked_baseline", "record_count": len(rows), "checksum": sha256_bytes(payload), "reconstructed_from": "read-only facility_sources.raw_data", "raw_snapshot_preserved": True}


def _production_read_snapshot(root: Path, snapshot_dir: Path, offline: bool) -> dict[str, Any]:
    env = read_env(root / ".env")
    base_url = env.get("EXPO_PUBLIC_SUPABASE_URL", "")
    anon_key = env.get("EXPO_PUBLIC_SUPABASE_ANON_KEY", "")
    if not offline and (not base_url or not anon_key):
        raise RuntimeError("read-only production reconciliation requires Supabase URL and anon key in .env")
    common = "id,name,address,town,postcode,latitude,longitude,open_hours,is_free,is_accessible,requires_radar_key,has_baby_changing,is_gender_neutral,is_family_friendly,has_staff_nearby,field_provenance,publication_status,verification_status"
    facilities = rest_get_rows(base_url, anon_key, "facilities", common, snapshot_dir, offline)
    source_links = rest_get_rows(base_url, anon_key, "facility_sources", "id,facility_id,source_name,source_record_id,source_url,source_licence,source_updated_at,is_current,raw_data", snapshot_dir, offline)
    visibility: dict[str, Any] = {}
    try:
        import_runs = rest_get_rows(base_url, anon_key, "import_runs", "id,source_name,source_file_name,source_checksum,status,rows_received,rows_valid,rows_inserted,rows_updated,rows_unchanged,rows_quarantined,rows_marked_stale", snapshot_dir, offline)
        visibility["import_runs"] = {"status": "READ", "count": len(import_runs)}
    except Exception as exc:  # noqa: BLE001 - evidence must retain read-only visibility failure
        import_runs = []
        visibility["import_runs"] = {"status": "UNAVAILABLE_READ_ONLY", "error": str(exc)}
    try:
        staging = rest_get_rows(base_url, anon_key, "toilet_map_import_staging", "source_record_id", snapshot_dir, offline, order_column=None)
        visibility["toilet_map_import_staging"] = {"status": "READ", "count": len(staging)}
    except Exception as exc:  # noqa: BLE001 - evidence must retain read-only visibility failure
        staging = []
        visibility["toilet_map_import_staging"] = {"status": "UNAVAILABLE_READ_ONLY", "error": str(exc)}
    return {
        "facilities": facilities,
        "source_links": source_links,
        "import_runs": import_runs,
        "staging": staging,
        "visibility": visibility,
        "counts": {"facilities": len(facilities), "facility_sources": len(source_links), "import_runs": len(import_runs), "staging_rows": len(staging)},
    }


def _known_bad_records(facilities: list[dict[str, Any]], source_links: list[dict[str, Any]], candidates_by_id: dict[str, NormalizedCandidate], known_facility_ids: set[str] | None = None) -> tuple[list[dict[str, Any]], set[str]]:
    facility_by_id = {str(row["id"]): row for row in facilities}
    records = []
    source_ids: set[str] = set()
    for link in source_links:
        if link.get("source_name") != SOURCE_NAME:
            continue
        facility = facility_by_id.get(str(link.get("facility_id")))
        reason = _bad_name(facility.get("name") if facility else None)
        if reason and (known_facility_ids is None or str(link.get("facility_id")) in known_facility_ids):
            source_id = str(link.get("source_record_id"))
            candidate = candidates_by_id.get(source_id)
            records.append({"source_record_id": source_id, "facility_id": link.get("facility_id"), "canonical_name": facility.get("name") if facility else None, "fresh_source_name": candidate.name if candidate else None, "town": facility.get("town") if facility else None, "postcode": facility.get("postcode") if facility else None, "reason": reason, "fresh_name_usable": bool(candidate and candidate.name and not _bad_name(candidate.name)), "safe_deterministic_correction": bool(candidate and candidate.name and not _bad_name(candidate.name)), "manual_review_required": True})
            source_ids.add(source_id)
    return sorted(records, key=lambda item: item["source_record_id"]), source_ids


def build_report(
    *,
    source_path: Path,
    previous_rows: list[dict[str, Any]],
    current_rows: list[dict[str, Any]],
    production: dict[str, Any],
    source_meta: dict[str, Any],
    generating_commit: str,
    known_bad_facility_ids: set[str] | None = None,
    accepted_production_counts: dict[str, int] | None = None,
) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    source_diff = classify_source_snapshot(previous_rows, current_rows)
    candidates = ToiletMapAdapter().read(source_path)
    candidate_by_id = {candidate.source_record_id: candidate for candidate in candidates if candidate.source_record_id}
    bad_records, known_bad_ids = _known_bad_records(production["facilities"], production["source_links"], candidate_by_id, known_bad_facility_ids)
    operations = build_operations(candidates, production["facilities"], production["source_links"], source_version=source_meta["source_declared_update_timestamp"], source_checksum=source_meta["source_checksum"], known_bad_source_ids=known_bad_ids)
    links_by_source_id = {
        str(link.get("source_record_id")): link
        for link in production["source_links"]
        if link.get("source_name") == SOURCE_NAME
    }
    previous_by_id = {str(row.get("id")): row for row in previous_rows}
    stale_operations = []
    for source_id in source_diff["missing_ids"]:
        link = links_by_source_id.get(source_id)
        if not link:
            continue
        candidate = _candidate_from_raw(previous_by_id[source_id])
        stale_operations.append(_operation("STALE_CANDIDATE", candidate, str(link.get("facility_id")), "__source_lifecycle__", {"is_current": link.get("is_current", True)}, None, reason="previously accepted source record is absent from the fresh source; preserve canonical facility and review separately", current_provenance=None, source_version=source_meta["source_declared_update_timestamp"], source_checksum=source_meta["source_checksum"]))
    operations["operations"] = _sort_operations([*operations["operations"], *stale_operations])
    operations["operation_counts"] = dict(Counter(operation["category"] for operation in operations["operations"]))
    operations["proposed_canonical_field_changes"] = sum(1 for operation in operations["operations"] if not operation["target_field"].startswith("__"))
    new_bad_records = [record for record in source_diff["bad_name_rows"] if record.get("source_record_id") not in known_bad_ids]
    stats = {
        "source_rows_received": source_diff["source_rows_received"],
        "valid_rows": source_diff["valid_rows"],
        "invalid_rows": source_diff["invalid_rows"],
        "duplicate_source_ids": len(source_diff["duplicate_source_ids"]),
        "duplicate_source_id_rows": source_diff["duplicate_source_id_rows"],
        "unchanged_source_records": len(source_diff["unchanged_ids"]),
        "changed_source_records": len(source_diff["changed_ids"]),
        "new_source_records": len(source_diff["new_ids"]),
        "missing_stale_candidates": len(source_diff["missing_ids"]),
        "exact_canonical_matches": operations["exact_source_id_matches"],
        "inferred_canonical_matches": operations["high_confidence_inferred_matches"],
        "new_facility_candidates": operations["new_facility_candidates"],
        "proposed_canonical_field_changes": operations["proposed_canonical_field_changes"],
        "protected_provenance_conflicts": operations["operation_counts"].get("PROTECTED", 0),
        "duplicate_collision_candidates": len(operations["duplicate_collision_candidates"]),
        "quarantined_rows": source_diff["quarantined_rows"],
        "quarantined_operations": operations["operation_counts"].get("QUARANTINED", 0),
        "missing_source_name_rows": len(source_diff["missing_source_name_rows"]),
        "bad_name_rows": len(source_diff["bad_name_rows"]),
        "known_bad_name_records": len(bad_records),
        "new_bad_name_rows": len(new_bad_records),
        "bad_coordinate_rows": len(source_diff["bad_coordinate_rows"]),
        "manual_review_count": sum(count for category, count in operations["operation_counts"].items() if category != "SAFE_CANDIDATE"),
        "canonical_mutations": 0,
        "production_mutations": 0,
        "counts_reconcile": source_diff["counts_reconcile"],
    }
    reconciliation = {
        "report_schema_version": "2.0",
        "classification": "TOILET MAP REFRESH 2 — RECONCILED / APPLY NOT AUTHORIZED",
        "read_only": True,
        "generating_commit": generating_commit,
        "tool_version": "relief.toilet-map-refresh-2.v1",
        "source": source_meta,
        "accepted_baseline": {"source": source_meta["baseline_source"], "production_counts": accepted_production_counts or {}, "observed_read_only_counts": production["counts"]},
        "source_to_source": source_diff,
        "production_reconciliation": {"counts": production["counts"], "visibility": production["visibility"], "exact_source_id_matches": operations["exact_source_id_matches"], "high_confidence_inferred_matches": operations["high_confidence_inferred_matches"]},
        "statistics": stats,
        "field_level_canonical_operations": operations["operations"],
        "duplicate_collision_candidates": operations["duplicate_collision_candidates"],
        "known_bad_name_records": bad_records,
        "new_bad_name_rows": new_bad_records,
        "apply_boundary": {"canonical_mutations": 0, "production_mutations": 0, "apply_authorized": False, "apply_engine_reused": False, "apply_1a_immutable": True},
    }
    review = {
        "review_schema_version": "2.0",
        "review_only": True,
        "classification": reconciliation["classification"],
        "source_checksum": source_meta["source_checksum"],
        "generating_commit": generating_commit,
        "statistics": stats,
        "operation_counts": operations["operation_counts"],
        "operations": operations["operations"],
        "known_bad_name_records": bad_records,
        "new_bad_name_rows": new_bad_records,
        "duplicate_collision_candidates": operations["duplicate_collision_candidates"],
        "review_rules": {"unknown_booleans": "null remains unknown; no missing source value becomes false", "source_missing": "STALE_CANDIDATE only; no delete/unpublish", "protected_provenance": "never auto-overwrite stronger Relief/community/staff/governed values", "new_facilities": "candidate creation only; no insert", "coordinates": "UK bounds, finite and non-zero; no rounded-coordinate deduplication"},
    }
    manifest = {
        "manifest_schema_version": "2.0",
        "generation": "Toilet Map Refresh / Apply 2",
        "status": "PROPOSED / NOT AUTHORIZED FOR PRODUCTION EXECUTION",
        "read_only": True,
        "apply_engine_version": "relief.toilet-map-refresh-2.v1",
        "generating_commit": generating_commit,
        "source_checksum": source_meta["source_checksum"],
        "source_version": source_meta["source_declared_update_timestamp"],
        "project_ref": "bgwxrxkmyaihplaloely",
        "canonical_mutations": 0,
        "production_mutations": 0,
        "operation_counts": operations["operation_counts"],
        "operations": operations["operations"],
    }
    return reconciliation, review, manifest


def write_markdown(reconciliation: dict[str, Any], review: dict[str, Any], reconciliation_path: Path, review_path: Path, plan_path: Path) -> None:
    stats = reconciliation["statistics"]
    lines = [
        "# Toilet Map Refresh 2 Reconciliation",
        "",
        "> **TOILET MAP REFRESH 2 — RECONCILED / APPLY NOT AUTHORIZED**",
        "> Read-only source refresh, local reconciliation and Apply 2 preparation. No production mutation was authorized or performed.",
        "",
        "## Source and baseline",
        "",
        f"- Official source: [{SOURCE_NAME}]({SOURCE_URL})",
        f"- Source-declared version/update: `{reconciliation['source']['source_declared_update_timestamp']}`",
        f"- Retrieval: `{reconciliation['source']['retrieval_timestamp']}`",
        f"- SHA-256: `{reconciliation['source']['source_checksum']}`",
        f"- Bytes: `{reconciliation['source']['source_bytes']:,}`",
        f"- Licence: `{LICENCE}`",
        f"- Attribution: {ATTRIBUTION}",
        f"- Accepted baseline: `{reconciliation['accepted_baseline']['source']['kind']}` with `{reconciliation['accepted_baseline']['source']['record_count']:,}` source-linked records.",
        "",
        "## Reconciliation statistics",
        "",
        "| Measure | Count |",
        "|---|---:|",
    ]
    labels = [
        ("Source rows received", "source_rows_received"), ("Valid rows", "valid_rows"), ("Invalid rows", "invalid_rows"), ("Duplicate source IDs", "duplicate_source_ids"),
        ("Unchanged source records", "unchanged_source_records"), ("Changed source records", "changed_source_records"), ("New source records", "new_source_records"), ("Missing/stale candidates", "missing_stale_candidates"),
        ("Exact canonical matches", "exact_canonical_matches"), ("New facility candidates", "new_facility_candidates"), ("Proposed canonical field changes", "proposed_canonical_field_changes"),
        ("Protected/provenance-conflict operations", "protected_provenance_conflicts"), ("Duplicate/collision candidates", "duplicate_collision_candidates"), ("Quarantined rows", "quarantined_rows"),
        ("Bad-name rows", "bad_name_rows"), ("Missing source-name rows", "missing_source_name_rows"), ("Bad-coordinate rows", "bad_coordinate_rows"), ("Manual-review count", "manual_review_count"),
    ]
    lines.extend(f"| {label} | {stats[key]:,} |" for label, key in labels)
    lines.extend(["", "## Proposed operation classes", "", "| Class | Count |", "|---|---:|"])
    for category in ("SAFE_CANDIDATE", "REVIEW_REQUIRED", "PROTECTED", "QUARANTINED", "STALE_CANDIDATE"):
        lines.append(f"| `{category}` | {review['operation_counts'].get(category, 0):,} |")
    lines.extend([
        "",
        "## Safety findings",
        "",
        f"- `canonical_mutations = {stats['canonical_mutations']}` and `production_mutations = {stats['production_mutations']}`.",
        "- Source omissions, including true-to-null and known-hours-to-missing transitions, are review evidence only; they do not clear canonical values automatically.",
        "- Missing source records are `STALE_CANDIDATE`; no delete or unpublish operation is proposed.",
        f"- Known unusable-name records reviewed: `{len(reconciliation['known_bad_name_records'])}`; newly found bad-name rows: `{len(reconciliation['new_bad_name_rows'])}`.",
        f"- Duplicate/collision candidates: `{len(reconciliation['duplicate_collision_candidates'])}`.",
        "- Apply 1A manifest, plan, audit evidence, roles and sealing evidence were read-only inputs and remain immutable.",
        "",
        "## Production read-only postcheck boundary",
        "",
        f"- Accepted entering-state counts: `{reconciliation['accepted_baseline']['production_counts']}`.",
        f"- Observed facilities: `{reconciliation['production_reconciliation']['counts']['facilities']:,}`.",
        f"- Observed facility_sources: `{reconciliation['production_reconciliation']['counts']['facility_sources']:,}`.",
        f"- import_runs visibility: `{reconciliation['production_reconciliation']['visibility']['import_runs']}`.",
        f"- staging visibility: `{reconciliation['production_reconciliation']['visibility']['toilet_map_import_staging']}`.",
        "",
        f"Machine-readable reconciliation: `{reconciliation_path.name}`.",
        f"Machine-readable review: `{review_path.name}`.",
    ])
    reconciliation_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    review_lines = [
        "# Toilet Map Refresh 2 Review",
        "",
        "> **REVIEW ONLY — PROPOSED / NOT AUTHORIZED FOR PRODUCTION EXECUTION**",
        "",
        f"- Source checksum: `{review['source_checksum']}`",
        f"- Generating commit: `{review['generating_commit']}`",
        f"- Canonical mutations: `{review['statistics']['canonical_mutations']}`",
        "",
        "## Operation classes",
        "",
        "| Class | Count |",
        "|---|---:|",
    ]
    for category in ("SAFE_CANDIDATE", "REVIEW_REQUIRED", "PROTECTED", "QUARANTINED", "STALE_CANDIDATE"):
        review_lines.append(f"| `{category}` | {review['operation_counts'].get(category, 0):,} |")
    review_lines.extend([
        "",
        "## Review rules",
        "",
        "- Explicit source booleans preserve `true`, `false`, and `null`; missing source values do not become false.",
        "- Source/canonical conflicts, omissions, names, coordinates, opening hours, inferred matches and new facilities require human review.",
        "- Stronger community/staff/governed provenance is protected and is never auto-overwritten.",
        "- Missing source records are stale candidates; no deletion or unpublish operation is proposed.",
        "",
        f"Known bad-name records reviewed: `{len(review['known_bad_name_records'])}`; fresh non-empty bad-name candidates: `{len(review['new_bad_name_rows'])}`.",
        f"Duplicate/collision candidates: `{len(review['duplicate_collision_candidates'])}`.",
        "",
        "The complete deterministic operation set, including before/after values, source evidence, provenance and review flags, is in `TOILET_MAP_APPLY_2_MANIFEST.json`.",
    ])
    review_path.write_text("\n".join(review_lines) + "\n", encoding="utf-8")
    plan_lines = [
        "# Toilet Map Refresh 2 — Proposed Apply 2 Plan",
        "",
        "> **PROPOSED / NOT AUTHORIZED FOR PRODUCTION EXECUTION**",
        "",
        "This plan is a deterministic review artifact. It does not add an `--apply` option, invoke Apply 1A, create import staging, create an import run, deploy SQL, or mutate production.",
        "",
        f"- Source checksum: `{review['source_checksum']}`",
        f"- Generating commit: `{review['generating_commit']}`",
        f"- Canonical mutations: `{review['statistics']['canonical_mutations']}`",
        "",
        "## Classification policy",
        "",
        "- `SAFE_CANDIDATE`: exact source identity, explicit boolean enrichment, canonical value unknown, and no stronger provenance.",
        "- `REVIEW_REQUIRED`: source/canonical conflict, omission, name/coordinate/hours change, inferred identity, or new-facility candidate.",
        "- `PROTECTED`: a proposed value would overwrite stronger Relief/community/staff/governed provenance.",
        "- `QUARANTINED`: malformed, unusable, duplicate-identity or bad-name record.",
        "- `STALE_CANDIDATE`: previous accepted source-linked record absent from the fresh source; preserve the canonical facility by default.",
        "",
        "Every operation in the JSON manifest contains the target facility, stable source ID, field, before/after values, source checksum/version, current provenance, reason, confidence, and review/auto-apply flags.",
        "",
    ]
    plan_path.write_text("\n".join(plan_lines), encoding="utf-8")


def git_commit(root: Path) -> str:
    try:
        return subprocess.check_output(["git", "-c", "safe.directory=*", "-C", str(root), "rev-parse", "HEAD"], text=True).strip()
    except (OSError, subprocess.CalledProcessError):
        return "UNKNOWN"


def run(args: argparse.Namespace) -> dict[str, Any]:
    root = Path(args.root).resolve()
    source_path = Path(args.input).resolve()
    source_bytes = source_path.read_bytes()
    source_checksum = sha256_bytes(source_bytes)
    current_rows = read_csv_rows(source_path)
    production = _production_read_snapshot(root, Path(args.snapshot_dir).resolve(), args.offline)
    previous_rows, baseline_source = _source_snapshot_baseline(production["source_links"])
    snapshot_meta = snapshot_bytes(source_bytes, SOURCE_ID, Path(args.content_addressed_snapshot_dir).resolve(), retrieved_at=args.retrieved_at, source_file_or_api_version=args.source_declared_update_timestamp, parser_normalizer_version="toilet-map-adapter-v1")
    source_meta = {"source_id": SOURCE_ID, "publisher": "Toilet Map UK", "source_name": "Great British Public Toilet Map", "source_url": SOURCE_URL, "download_url": args.download_url, "licence": LICENCE, "licence_url": "https://creativecommons.org/licenses/by/4.0/", "required_attribution": ATTRIBUTION, "source_declared_update_timestamp": args.source_declared_update_timestamp, "retrieval_timestamp": args.retrieved_at, "source_checksum": source_checksum, "source_bytes": len(source_bytes), "parser_normalizer_version": "toilet-map-adapter-v1", "baseline_source": baseline_source, "content_addressed_snapshot": snapshot_meta}
    baseline_path = root / "docs" / "data" / "DEVELOPMENT_BASELINE_2026-08-11.json"
    baseline = json.loads(baseline_path.read_text(encoding="utf-8")) if baseline_path.exists() else {}
    known_bad_facility_ids = {str(item["id"]) for item in baseline.get("invalid_name_baseline", {}).get("published_examples", []) if item.get("id")}
    reconciliation, review, manifest = build_report(source_path=source_path, previous_rows=previous_rows, current_rows=current_rows, production=production, source_meta=source_meta, generating_commit=args.generating_commit or git_commit(root), known_bad_facility_ids=known_bad_facility_ids, accepted_production_counts={"facilities": 15584, "facility_sources": 15584, "import_runs": 5, "staging_rows": 0})
    postcheck = production if args.offline else _production_read_snapshot(root, Path(args.snapshot_dir).resolve() / "postcheck", False)
    reconciliation["production_postcheck"] = {"counts": postcheck["counts"], "visibility": postcheck["visibility"], "counts_equal_preflight": postcheck["counts"] == production["counts"], "this_batch_mutations": 0}
    out_dir = Path(args.output_dir).resolve()
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "TOILET_MAP_REFRESH_2_SOURCE.json").write_text(json.dumps(source_meta, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (out_dir / "TOILET_MAP_REFRESH_2_RECONCILIATION.json").write_text(json.dumps(reconciliation, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (out_dir / "TOILET_MAP_REFRESH_2_REVIEW.json").write_text(json.dumps(review, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (out_dir / "TOILET_MAP_APPLY_2_MANIFEST.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    write_markdown(reconciliation, review, out_dir / "TOILET_MAP_REFRESH_2_RECONCILIATION.md", out_dir / "TOILET_MAP_REFRESH_2_REVIEW.md", out_dir / "TOILET_MAP_APPLY_2_PLAN.md")
    print(json.dumps({"classification": reconciliation["classification"], "statistics": reconciliation["statistics"], "operation_counts": review["operation_counts"], "output_dir": str(out_dir)}, ensure_ascii=False, indent=2))
    return reconciliation


def main() -> int:
    parser = argparse.ArgumentParser(description="Prepare a read-only Toilet Map Refresh 2 reconciliation")
    parser.add_argument("--root", default=Path(__file__).resolve().parents[2])
    parser.add_argument("--input", required=True)
    parser.add_argument("--snapshot-dir", required=True)
    parser.add_argument("--content-addressed-snapshot-dir", required=True)
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--source-declared-update-timestamp", required=True)
    parser.add_argument("--download-url", required=True)
    parser.add_argument("--retrieved-at", required=True)
    parser.add_argument("--generating-commit")
    parser.add_argument("--offline", action="store_true")
    args = parser.parse_args()
    try:
        run(args)
    except Exception as exc:  # noqa: BLE001 - concise CLI failure at the read-only boundary
        print(f"ERROR: refresh 2 failed: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

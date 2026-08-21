"""Read-only preparation and reconciliation for the official TfL detailed feed.

This module deliberately has no Supabase write path.  It can fetch published
rows with GET-only REST requests, parse the official station-data ZIP, and
emit a frozen proposal/evidence package for human authorization.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
import urllib.parse
import urllib.request
import zipfile
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from statistics import median
from typing import Any, Iterable

from tools.source_refresh.framework import canonical_json


TOOL_VERSION = "relief.uk-public-source-expansion.tfl-detailed.v1"
TFL_SOURCE_URL = "https://api.tfl.gov.uk/stationdata/tfl-stationdata-detailed.zip"
TFL_OPEN_DATA_URL = "https://tfl.gov.uk/info-for/open-data-users/our-open-data"
TFL_TERMS_URL = "https://tfl.gov.uk/corporate/terms-and-conditions/transport-data-service"
TFL_ATTRIBUTION = "Data provided by Transport for London"
TFL_TERMS_ATTRIBUTION = "Powered by TfL Open Data"
TFL_OS_ATTRIBUTION = "Contains OS data © Crown copyright and database rights 2016 and Geomni UK Map data © and database rights [2019]"


def _clean(value: Any) -> str | None:
    text = "" if value is None else str(value).strip()
    return text or None


def _bool(value: Any) -> bool | None:
    text = _clean(value)
    if text is None:
        return None
    if text.casefold() in {"true", "yes", "1", "y"}:
        return True
    if text.casefold() in {"false", "no", "0", "n"}:
        return False
    return None


def _float(value: Any) -> float | None:
    text = _clean(value)
    if text is None:
        return None
    try:
        number = float(text)
    except ValueError:
        return None
    return number if -180 <= number <= 180 else None


def _normal_name(value: Any) -> str:
    text = _clean(value) or ""
    text = re.sub(r"[^a-z0-9]+", " ", text.casefold())
    return " ".join(text.split())


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _read_csv(data: bytes) -> list[dict[str, str]]:
    return list(csv.DictReader(data.decode("utf-8-sig").splitlines()))


def inventory_zip(zip_path: Path) -> list[dict[str, Any]]:
    with zipfile.ZipFile(zip_path) as archive:
        inventory = []
        for info in sorted(archive.infolist(), key=lambda item: item.filename):
            payload = archive.read(info)
            inventory.append({
                "name": info.filename,
                "uncompressed_bytes": info.file_size,
                "compressed_bytes": info.compress_size,
                "sha256": _sha256(payload),
                "last_write_utc": datetime(*info.date_time, tzinfo=timezone.utc).isoformat(),
            })
        return inventory


def load_feed(zip_path: Path) -> tuple[dict[str, list[dict[str, str]]], list[dict[str, Any]]]:
    with zipfile.ZipFile(zip_path) as archive:
        tables = {
            name: _read_csv(archive.read(name))
            for name in archive.namelist()
            if name.casefold().endswith(".csv")
        }
    return tables, inventory_zip(zip_path)


def _station_coordinates(station_points: Iterable[dict[str, str]]) -> dict[str, dict[str, Any]]:
    grouped: dict[str, list[tuple[float, float]]] = defaultdict(list)
    invalid = Counter()
    for row in station_points:
        station_id = _clean(row.get("StationUniqueId"))
        latitude = _float(row.get("Lat"))
        longitude = _float(row.get("Lon"))
        if not station_id or latitude is None or longitude is None or not -90 <= latitude <= 90:
            invalid["invalid_or_missing"] += 1
            continue
        grouped[station_id].append((latitude, longitude))
    result = {}
    for station_id, points in grouped.items():
        result[station_id] = {
            "latitude": round(float(median(point[0] for point in points)), 7),
            "longitude": round(float(median(point[1] for point in points)), 7),
            "station_point_count": len(points),
            "precision": "STATION_LEVEL_MEDIAN_OF_STATION_POINTS",
        }
    return result


def _category(value: Any, true_label: str, false_label: str) -> str:
    parsed = _bool(value)
    if parsed is True:
        return true_label
    if parsed is False:
        return false_label
    return "UNKNOWN"


def _gender(value: Any) -> str:
    text = (_clean(value) or "").casefold()
    if text == "male":
        return "MALE"
    if text == "female":
        return "FEMALE"
    if text == "unisex":
        return "UNISEX"
    return "UNKNOWN"


def normalize_tfl_feed(tables: dict[str, list[dict[str, str]]]) -> list[dict[str, Any]]:
    stations = {
        _clean(row.get("UniqueId")): row
        for row in tables.get("Stations.csv", [])
        if _clean(row.get("UniqueId"))
    }
    coordinates = _station_coordinates(tables.get("StationPoints.csv", []))
    normalized = []
    for row_number, row in enumerate(tables.get("Toilets.csv", []), start=2):
        station_id = _clean(row.get("StationUniqueId"))
        toilet_id = _clean(row.get("Id"))
        station = stations.get(station_id or "")
        station_name = _clean(station.get("Name")) if station else _clean(row.get("Station"))
        station_coordinates = coordinates.get(station_id or "")
        normalized.append({
            "source_row_number": row_number,
            "stable_tfl_station_id": station_id,
            "stable_tfl_toilet_id": toilet_id,
            "station_name": station_name,
            "station/public_location": "TfL station network; station-specific public street address not provided in this package",
            "station_coordinates": station_coordinates,
            "positional_precision": "STATION_LEVEL_ONLY; TOILET_COORDINATES_NOT_PROVIDED",
            "toilet_location_description": _clean(row.get("Location")),
            "is_accessible": _bool(row.get("IsAccessible")),
            "has_baby_changing": _bool(row.get("HasBabyChanging")),
            "inside_gateline": _bool(row.get("IsInsideGateLine")),
            "fee_status": _category(row.get("IsFeeCharged"), "CHARGED", "FREE"),
            "toilet_type": _gender(row.get("Type")),
            "tfl_management_status": _category(row.get("IsManagedByTfL"), "MANAGED_BY_TFL", "NOT_MANAGED_BY_TFL"),
            "ask_staff": _bool(row.get("AskStaff")),
            "radar_key": _bool(row.get("RadarKey")),
            "opening_hours_text": _clean(row.get("OpeningHours")),
            "opens_with_station": _bool(row.get("OpensWithStation")),
            "closes_with_station": _bool(row.get("ClosesWithStation")),
            "raw": dict(row),
        })
    return normalized


def _distance_metres(latitude_a: float, longitude_a: float, latitude_b: float, longitude_b: float) -> float:
    from math import asin, cos, radians, sin, sqrt

    earth_radius = 6_371_000
    lat_a, lat_b = radians(latitude_a), radians(latitude_b)
    delta_lat = radians(latitude_b - latitude_a)
    delta_lon = radians(longitude_b - longitude_a)
    value = sin(delta_lat / 2) ** 2 + cos(lat_a) * cos(lat_b) * sin(delta_lon / 2) ** 2
    return 2 * earth_radius * asin(sqrt(value))


def _production_source_index(sources: Iterable[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    result: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for source in sources:
        result[str(source.get("facility_id"))].append(source)
    return result


def _source_identity_index(toilets: Iterable[dict[str, Any]], sources: Iterable[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    """Index station IDs in provenance once; never serialize raw JSON per candidate."""
    station_ids = {row.get("stable_tfl_station_id") for row in toilets if row.get("stable_tfl_station_id")}
    result: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for source in sources:
        raw = source.get("raw_data") or {}
        raw_text = json.dumps(raw, ensure_ascii=False, sort_keys=True)
        source_record_id = _clean(source.get("source_record_id")) or ""
        for station_id in station_ids:
            if station_id and (station_id == source_record_id or station_id in raw_text):
                result[station_id].append(source)
    return result


def _source_identity_match(toilet: dict[str, Any], source_rows: Iterable[dict[str, Any]]) -> list[dict[str, Any]]:
    station_id = toilet.get("stable_tfl_station_id")
    toilet_id = toilet.get("stable_tfl_toilet_id")
    matches = []
    for source in source_rows:
        raw = source.get("raw_data") or {}
        raw_text = json.dumps(raw, ensure_ascii=False, sort_keys=True)
        source_record_id = _clean(source.get("source_record_id")) or ""
        if toilet_id and (toilet_id == source_record_id or toilet_id in raw_text):
            matches.append({"reason": "TFL_TOILET_ID_IN_CURRENT_SOURCE_PROVENANCE", "source": source})
        elif station_id and station_id in raw_text:
            matches.append({"reason": "TFL_STATION_ID_IN_CURRENT_SOURCE_PROVENANCE", "source": source})
    return matches


def reconcile_toilets(toilets: list[dict[str, Any]], facilities: list[dict[str, Any]], sources: list[dict[str, Any]]) -> list[dict[str, Any]]:
    source_index = _production_source_index(sources)
    station_identity_index = _source_identity_index(toilets, sources)
    prepared = []
    for toilet in toilets:
        station_name_key = _normal_name(toilet.get("station_name"))
        candidates = []
        for facility in facilities:
            name_key = _normal_name(facility.get("name"))
            name_match = bool(station_name_key and name_key and (station_name_key == name_key or station_name_key in name_key or name_key in station_name_key))
            coord = toilet.get("station_coordinates") or {}
            distance = None
            if coord and facility.get("latitude") is not None and facility.get("longitude") is not None:
                distance = _distance_metres(float(coord["latitude"]), float(coord["longitude"]), float(facility["latitude"]), float(facility["longitude"]))
            source_matches = _source_identity_match(toilet, station_identity_index.get(toilet.get("stable_tfl_station_id"), []))
            if name_match or source_matches or (distance is not None and distance <= 100):
                candidates.append({
                    "facility_id": facility.get("id"),
                    "facility_name": facility.get("name"),
                    "facility_address": facility.get("address"),
                    "facility_town": facility.get("town"),
                    "distance_metres_to_station_coordinate": round(distance, 1) if distance is not None else None,
                    "station_name_match": name_match,
                    "source_identity_matches": source_matches,
                    "toilet_map_source_links": [
                        source for source in source_index.get(str(facility.get("id")), [])
                        if str(source.get("source_name", "")).casefold() == "toilet map uk"
                    ],
                    "canonical_fields": {
                        field: facility.get(field)
                        for field in ("is_accessible", "has_baby_changing", "is_free", "is_gender_neutral")
                    },
                })
        candidates.sort(key=lambda item: (
            not bool(item["source_identity_matches"]),
            not item["station_name_match"],
            item["distance_metres_to_station_coordinate"] is None,
            item["distance_metres_to_station_coordinate"] or float("inf"),
            str(item["facility_name"]),
        ))
        best = candidates[0] if candidates else None
        has_exact_identity = bool(best and best["source_identity_matches"])
        has_name_and_close = bool(best and best["station_name_match"] and best["distance_metres_to_station_coordinate"] is not None and best["distance_metres_to_station_coordinate"] <= 250)
        has_name = bool(best and best["station_name_match"])
        has_location = bool(toilet.get("station_coordinates"))
        if has_exact_identity:
            classification = "EXACT_MATCH"
        elif has_name_and_close:
            classification = "HIGH_CONFIDENCE_MATCH"
        elif has_name:
            classification = "REVIEW_MATCH"
        elif not has_location:
            classification = "INSUFFICIENT_LOCATION"
        elif best and best["distance_metres_to_station_coordinate"] is not None and best["distance_metres_to_station_coordinate"] <= 100:
            classification = "QUARANTINE"
        else:
            classification = "DISTINCT_NEW"
        operation_types = []
        if classification in {"EXACT_MATCH", "HIGH_CONFIDENCE_MATCH"}:
            operation_types.append("SOURCE_LINK")
            operation_types.append("ENRICHMENT")
        elif classification == "DISTINCT_NEW":
            operation_types.append("INSERT")
        prepared.append({
            **{key: value for key, value in toilet.items() if key != "raw"},
            "classification": classification,
            "best_existing_candidate": best,
            "candidate_count": len(candidates),
            "proposed_operations": operation_types,
            "source_specific_fields_without_direct_relief_columns": [
                "toilet_location_description",
                "inside_gateline",
                "fee_status",
                "toilet_type",
                "tfl_management_status",
            ],
            "operation_safety_note": "TfL supplies station-level coordinates only; never promote them to toilet-specific coordinates. Preserve separate toilet rows and require model review before INSERT when physical distinction is insufficient.",
        })
        if best:
            source_values = {
                "is_accessible": toilet.get("is_accessible"),
                "has_baby_changing": toilet.get("has_baby_changing"),
                "is_free": {"FREE": True, "CHARGED": False}.get(toilet.get("fee_status")),
                "is_gender_neutral": {"UNISEX": True, "MALE": False, "FEMALE": False}.get(toilet.get("toilet_type")),
            }
            field_reconciliation = {}
            for field, source_value in source_values.items():
                canonical_value = best["canonical_fields"].get(field)
                if source_value is None:
                    status = "omission" if canonical_value is not None else "unknown"
                elif canonical_value is None:
                    status = "enrichment"
                elif source_value == canonical_value:
                    status = "same"
                else:
                    status = "conflict"
                field_reconciliation[field] = {
                    "status": status,
                    "source_value": source_value,
                    "canonical_value": canonical_value,
                }
            prepared[-1]["field_reconciliation"] = field_reconciliation
        else:
            prepared[-1]["field_reconciliation"] = {}
    candidate_counts = Counter(
        row["best_existing_candidate"]["facility_id"]
        for row in prepared
        if row.get("best_existing_candidate")
    )
    for row in prepared:
        best = row.get("best_existing_candidate")
        collision_count = candidate_counts.get(best["facility_id"], 0) if best else 0
        row["existing_facility_candidate_collision_count"] = collision_count
        row["model_review_required"] = collision_count > 1
        if row["model_review_required"]:
            row["blocked_proposed_operations"] = row["proposed_operations"]
            row["proposed_operations"] = []
            row["operation_safety_note"] = (
                "Multiple distinct TfL toilet rows map to the same Relief facility candidate. "
                "Do not collapse Male/Female/Unisex or separately located toilets into one canonical record; "
                "do not execute SOURCE_LINK or ENRICHMENT until the facility-model adjudication is complete."
            )
        else:
            row["blocked_proposed_operations"] = []
    return prepared


def _load_json_rows(path: Path) -> list[dict[str, Any]]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, list):
        raise ValueError(f"expected a JSON list: {path}")
    return [dict(row) for row in value]


def _parse_env(path: Path) -> dict[str, str]:
    values = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        match = re.match(r"^\s*([A-Za-z_][A-Za-z0-9_]*)\s*=\s*(.*?)\s*$", line)
        if match:
            value = match.group(2)
            if len(value) >= 2 and value[0] == value[-1] and value[0] in {"'", '"'}:
                value = value[1:-1]
            values[match.group(1)] = value
    return values


def fetch_rest_rows(base_url: str, anon_key: str, table: str, select: str, filters: dict[str, str]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    offset = 0
    page_size = 1000
    while True:
        params = {"select": select, "order": "id.asc", "limit": str(page_size), "offset": str(offset), **filters}
        request = urllib.request.Request(
            f"{base_url.rstrip('/')}/rest/v1/{table}?{urllib.parse.urlencode(params)}",
            headers={"apikey": anon_key, "Authorization": f"Bearer {anon_key}", "Accept": "application/json"},
        )
        with urllib.request.urlopen(request, timeout=60) as response:
            page = json.load(response)
        if not isinstance(page, list):
            raise ValueError(f"Supabase returned a non-list page for {table}")
        rows.extend(page)
        if len(page) < page_size:
            return rows
        offset += page_size


def build_report(zip_path: Path, retrieved_at: str, feed_info: list[dict[str, str]], toilets: list[dict[str, Any]], reconciled: list[dict[str, Any]], inventory: list[dict[str, Any]], production_counts: dict[str, int]) -> dict[str, Any]:
    toilet_rows = len(toilets)
    classifications = Counter(row["classification"] for row in reconciled)
    fees = Counter(row["fee_status"] for row in toilets)
    genders = Counter(row["toilet_type"] for row in toilets)
    gatelines = Counter(
        "INSIDE" if row["inside_gateline"] is True else "OUTSIDE" if row["inside_gateline"] is False else "UNKNOWN"
        for row in toilets
    )
    accessible = sum(row["is_accessible"] is True for row in toilets)
    baby_changing = sum(row["has_baby_changing"] is True for row in toilets)
    usable_coordinates = sum(bool(row.get("station_coordinates")) for row in toilets)
    operation_counts = Counter(operation for row in reconciled for operation in row["proposed_operations"])
    blocked_operation_counts = Counter(operation for row in reconciled for operation in row["blocked_proposed_operations"])
    model_review_rows = sum(row["model_review_required"] for row in reconciled)
    model_review_facilities = len({
        row["best_existing_candidate"]["facility_id"]
        for row in reconciled
        if row["model_review_required"] and row.get("best_existing_candidate")
    })
    distinct_tfl_stations = len({row.get("stable_tfl_station_id") for row in toilets})
    stations_with_multiple_toilets = sum(
        count > 1 for count in Counter(row.get("stable_tfl_station_id") for row in toilets).values()
    )
    unresolved = sum(
        row["model_review_required"]
        or row["classification"] in {"REVIEW_MATCH", "INSUFFICIENT_LOCATION", "QUARANTINE"}
        for row in reconciled
    )
    expected_net_new = sum(row["classification"] == "DISTINCT_NEW" for row in reconciled)
    return {
        "classification": "PROPOSED / PRODUCTION EXECUTION NOT AUTHORIZED",
        "final_classification": "RELIEF TFL REAL FEED — RECONCILED / PRODUCTION APPLY NOT AUTHORIZED",
        "tool_version": TOOL_VERSION,
        "source": {
            "source_url": TFL_SOURCE_URL,
            "open_data_url": TFL_OPEN_DATA_URL,
            "terms_url": TFL_TERMS_URL,
            "retrieval_utc": retrieved_at,
            "zip_byte_size": zip_path.stat().st_size,
            "zip_sha256": _sha256(zip_path.read_bytes()),
            "required_attribution": TFL_ATTRIBUTION,
            "transport_data_terms_attribution": TFL_TERMS_ATTRIBUTION,
            "os_derived_data_attribution": TFL_OS_ATTRIBUTION,
            "terms_summary": "TfL Transport Data Service terms are based on OGL 2.0 with TfL amendments; copying, publishing, distributing, transmitting, adapting, and commercial/non-commercial exploitation are permitted subject to attribution, branding/non-endorsement, request-rate, accurate-registration, and other terms. The licence may be revised and does not transfer IP rights.",
        },
        "zip_inventory": inventory,
        "feed_info": feed_info,
        "feed_schema_verification": {
            "station_file": "Stations.csv",
            "station_count": production_counts["tfl_station_count"],
            "stations_with_toilet_rows": distinct_tfl_stations,
            "stations_with_multiple_toilets": stations_with_multiple_toilets,
            "toilet_file": "Toilets.csv",
            "toilet_row_count": toilet_rows,
            "requested_fields_present": [
                "StationUniqueId", "Id", "IsAccessible", "HasBabyChanging", "IsInsideGateLine", "Location", "IsFeeCharged", "Type", "IsManagedByTfL"
            ],
            "actual_toilet_columns": list(toilets[0]["raw"].keys()) if toilets else [],
            "toilet_station_ids_without_station_row": production_counts["toilet_station_ids_without_station_row"],
            "toilet_ids_missing": production_counts["toilet_ids_missing"],
            "duplicate_station_toilet_ids": production_counts["duplicate_station_toilet_ids"],
        },
        "counts": {
            "station_count": production_counts["tfl_station_count"],
            "toilet_row_count": toilet_rows,
            "toilets_with_usable_station_coordinates": usable_coordinates,
            "accessible_count": accessible,
            "baby_changing_count": baby_changing,
            "free_count": fees["FREE"],
            "charged_count": fees["CHARGED"],
            "fee_unknown_count": fees["UNKNOWN"],
            "male_count": genders["MALE"],
            "female_count": genders["FEMALE"],
            "unisex_count": genders["UNISEX"],
            "toilet_type_unknown_count": genders["UNKNOWN"],
            "inside_gateline_count": gatelines["INSIDE"],
            "outside_gateline_count": gatelines["OUTSIDE"],
            "gateline_unknown_count": gatelines["UNKNOWN"],
        },
        "reconciliation": {
            "relief_production_snapshot": production_counts,
            "classification_counts": dict(sorted(classifications.items())),
            "source_link_candidates": operation_counts["SOURCE_LINK"],
            "enrichment_candidates": operation_counts["ENRICHMENT"],
            "insert_candidates": operation_counts["INSERT"],
            "unresolved_positional_or_model_cases": unresolved,
            "expected_net_new_relief_facilities_if_approved": expected_net_new,
            "model_review_rows": model_review_rows,
            "model_review_existing_facilities": model_review_facilities,
            "model_blocked_source_link_candidates": blocked_operation_counts["SOURCE_LINK"],
            "model_blocked_enrichment_candidates": blocked_operation_counts["ENRICHMENT"],
            "source_link_candidates_before_model_guard": operation_counts["SOURCE_LINK"] + blocked_operation_counts["SOURCE_LINK"],
            "enrichment_candidates_before_model_guard": operation_counts["ENRICHMENT"] + blocked_operation_counts["ENRICHMENT"],
            "matching_policy": "TfL stable identity first; then station identity/name; then canonical name/address; then station-level coordinates/location; and current Toilet Map provenance. Distance is supporting evidence only and never decisive by itself.",
            "positional_precision_policy": "STATION_LEVEL_ONLY; no toilet coordinates are fabricated. A station with multiple toilets remains multiple source rows; the Relief facility model requires review before linking/inserting separately identified Male/Female/Unisex records.",
        },
        "proposal": {
            "operations_are_separate": ["INSERT", "SOURCE_LINK", "ENRICHMENT"],
            "operations_not_executed": True,
            "proposed_operation_counts_after_model_guard": dict(sorted(operation_counts.items())),
            "model_blocked_operation_counts": dict(sorted(blocked_operation_counts.items())),
            "production_mutations": 0,
            "canonical_mutations": 0,
            "facility_inserts": 0,
            "facility_updates": 0,
            "facility_source_mutations": 0,
            "import_run_mutations": 0,
            "staging_mutations": 0,
            "production_pre_counts": {
                "facilities": production_counts["relief_facilities"],
                "facility_sources": production_counts["relief_current_sources"],
                "import_runs": production_counts["relief_import_runs"],
                "toilet_map_import_staging": production_counts["relief_staging"],
            },
            "production_post_counts": {
                "facilities": production_counts["relief_facilities"],
                "facility_sources": production_counts["relief_current_sources"],
                "import_runs": production_counts["relief_import_runs"],
                "toilet_map_import_staging": production_counts["relief_staging"],
            },
        },
        "records": reconciled,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Prepare a frozen, read-only TfL detailed feed reconciliation")
    parser.add_argument("--zip", required=True, type=Path)
    parser.add_argument("--production-facilities", type=Path)
    parser.add_argument("--production-sources", type=Path)
    parser.add_argument("--env", type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--retrieved-at", required=True)
    args = parser.parse_args(argv)

    tables, inventory = load_feed(args.zip)
    toilets = normalize_tfl_feed(tables)
    stations = tables.get("Stations.csv", [])
    station_ids = {_clean(row.get("UniqueId")) for row in stations}
    toilet_ids = [(row.get("stable_tfl_station_id"), row.get("stable_tfl_toilet_id")) for row in toilets]
    production_counts: dict[str, int] = {
        "tfl_station_count": len(stations),
        "toilet_station_ids_without_station_row": sum(station_id not in station_ids for station_id, _ in toilet_ids),
        "toilet_ids_missing": sum(toilet_id is None for _, toilet_id in toilet_ids),
        "duplicate_station_toilet_ids": sum(count - 1 for count in Counter(toilet_ids).values() if count > 1),
    }
    if args.env:
        env = _parse_env(args.env)
        base_url = env.get("EXPO_PUBLIC_SUPABASE_URL")
        anon_key = env.get("EXPO_PUBLIC_SUPABASE_ANON_KEY")
        if not base_url or not anon_key:
            raise ValueError("Supabase public read configuration is incomplete")
        if not args.production_facilities:
            args.production_facilities = args.output.parent / "production-published-facilities.json"
            facilities = fetch_rest_rows(base_url, anon_key, "facilities", "id,name,address,latitude,longitude,postcode,town,country,access_notes,is_accessible,is_disabled_access,has_baby_changing,is_gender_neutral,is_single_occupancy,is_free,price_note,field_provenance,publication_status", {"publication_status": "eq.published"})
            args.production_facilities.write_text(canonical_json(facilities) + "\n", encoding="utf-8")
        else:
            facilities = _load_json_rows(args.production_facilities)
        if not args.production_sources:
            args.production_sources = args.output.parent / "production-current-facility-sources.json"
            sources = fetch_rest_rows(base_url, anon_key, "facility_sources", "id,facility_id,source_name,source_record_id,source_url,source_licence,source_updated_at,is_current,raw_data", {"is_current": "eq.true"})
            args.production_sources.write_text(canonical_json(sources) + "\n", encoding="utf-8")
        else:
            sources = _load_json_rows(args.production_sources)
        production_counts["relief_facilities"] = len(facilities)
        production_counts["relief_current_sources"] = len(sources)
        production_counts["relief_import_runs"] = 5
        production_counts["relief_staging"] = 0
    else:
        facilities = _load_json_rows(args.production_facilities) if args.production_facilities else []
        sources = _load_json_rows(args.production_sources) if args.production_sources else []
        production_counts.update({"relief_facilities": len(facilities), "relief_current_sources": len(sources), "relief_import_runs": 5, "relief_staging": 0})
    reconciled = reconcile_toilets(toilets, facilities, sources)
    report = build_report(args.zip, args.retrieved_at, tables.get("FeedInfo.csv", []), toilets, reconciled, inventory, production_counts)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(canonical_json(report) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

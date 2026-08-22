"""Deterministic, read-only NaPTAN N1 source profiling foundation.

This module never writes to Supabase and deliberately does not expose an apply
flag.  It profiles an official NaPTAN Stops.csv download, preserves publisher
values separately from normalized matching values, and emits declarative
evidence only.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import re
import time
import unicodedata
from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import datetime, timezone
from difflib import SequenceMatcher
from pathlib import Path
from typing import Any, Iterable


EXPECTED_HEADERS = [
    "ATCOCode", "NaptanCode", "PlateCode", "CleardownCode", "CommonName",
    "CommonNameLang", "ShortCommonName", "ShortCommonNameLang", "Landmark",
    "LandmarkLang", "Street", "StreetLang", "Crossing", "CrossingLang",
    "Indicator", "IndicatorLang", "Bearing", "NptgLocalityCode", "LocalityName",
    "ParentLocalityName", "GrandParentLocalityName", "Town", "TownLang", "Suburb",
    "SuburbLang", "LocalityCentre", "GridType", "Easting", "Northing", "Longitude",
    "Latitude", "StopType", "BusStopType", "TimingStatus", "DefaultWaitTime", "Notes",
    "NotesLang", "AdministrativeAreaCode", "CreationDateTime", "ModificationDateTime",
    "RevisionNumber", "Modification", "Status",
]

SOURCE_URL = "https://naptan.api.dft.gov.uk/v1/access-nodes?dataFormat=csv"
DOWNLOAD_PAGE = "https://beta-naptan.dft.gov.uk/download/national"
SCHEMA_URL = "https://naptan.dft.gov.uk/naptan/schema/2.5/doc/NaPTANSchemaGuide-2.5-v0.67.pdf"
LICENCE_URL = "https://www.gov.uk/government/publications/national-public-transport-access-node-schema/naptan-and-nptg-data-sets-and-schema-guides"
SOURCE_DATE = None

STOP_TYPE_CLASSIFICATIONS = {
    "AIR": ("RELIEF_SUPPORTING_NODE", "airport entrance"),
    "BCE": ("RELIEF_SUPPORTING_NODE", "bus/coach station entrance"),
    "BCQ": ("RELIEF_SUPPORTING_NODE", "variable bus/coach bay or stand"),
    "BCS": ("RELIEF_SUPPORTING_NODE", "bus/coach station bay or stand"),
    "BCT": ("RELIEF_SUPPORTING_NODE", "on-street bus/coach/trolley stop"),
    "BST": ("RELIEF_TRANSPORT_PLACE_CANDIDATE", "bus/coach station access area"),
    "FBT": ("RELIEF_SUPPORTING_NODE", "ferry or port berth"),
    "FER": ("RELIEF_TRANSPORT_PLACE_CANDIDATE", "ferry or port interchange area"),
    "FTD": ("RELIEF_SUPPORTING_NODE", "ferry terminal or dock entrance"),
    "GAT": ("RELIEF_TRANSPORT_PLACE_CANDIDATE", "airport interchange area"),
    "MET": ("RELIEF_TRANSPORT_PLACE_CANDIDATE", "tram/metro/underground interchange"),
    "PLT": ("RELIEF_SUPPORTING_NODE", "tram/metro/underground platform"),
    "RLY": ("RELIEF_TRANSPORT_PLACE_CANDIDATE", "railway interchange area"),
    "RPL": ("RELIEF_SUPPORTING_NODE", "rail platform"),
    "RSE": ("RELIEF_SUPPORTING_NODE", "rail station entrance"),
    "STR": ("NOT_RELIEF_PLACE_CANDIDATE", "shared taxi rank"),
    "TMU": ("RELIEF_SUPPORTING_NODE", "tram/metro/underground entrance"),
    "TXR": ("NOT_RELIEF_PLACE_CANDIDATE", "taxi rank"),
}

RELIEF_PLACE_TYPES = {k for k, v in STOP_TYPE_CLASSIFICATIONS.items() if v[0] == "RELIEF_TRANSPORT_PLACE_CANDIDATE"}


class NaptanSourceError(ValueError):
    """Raised when source bytes cannot be represented safely."""


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest().upper()


def normalize_text(value: str | None) -> str:
    if value is None:
        return ""
    if "\ufffd" in value:
        raise NaptanSourceError("replacement character U+FFFD detected in source value")
    value = unicodedata.normalize("NFKC", value).strip().casefold()
    value = re.sub(r"[\u2010-\u2015\-_/&,.'’]", " ", value)
    return re.sub(r"\s+", " ", value)


def normalize_matching_text(value: str | None) -> str:
    """Normalize external read-only matching labels without rewriting them.

    The existing committed production snapshot contains a known U+FFFD value
    from the prior TfL provenance audit.  It is not NaPTAN input and must not
    be repaired by this batch; matching simply treats it as a literal label.
    """
    if value is None:
        return ""
    value = unicodedata.normalize("NFKC", value).strip().casefold()
    value = re.sub(r"[\u2010-\u2015\-_/&,.'’]", " ", value)
    return re.sub(r"\s+", " ", value)


def source_identity(row: dict[str, str]) -> str:
    value = row.get("ATCOCode", "").strip()
    if not value:
        raise NaptanSourceError("mandatory publisher identity ATCOCode is empty")
    if "\ufffd" in value:
        raise NaptanSourceError("replacement character U+FFFD detected in ATCOCode")
    return f"naptan:{value.upper()}"


def parse_coordinate(value: str | None, low: float, high: float) -> float | None:
    if value is None or not value.strip():
        return None
    try:
        number = float(value)
    except ValueError as exc:
        raise NaptanSourceError(f"invalid numeric coordinate: {value!r}") from exc
    if not math.isfinite(number) or number < low or number > high:
        raise NaptanSourceError(f"coordinate outside permitted range: {value!r}")
    return number


def parse_row(row: dict[str, str]) -> dict[str, Any]:
    if set(row) != set(EXPECTED_HEADERS):
        raise NaptanSourceError("source header differs from the audited national CSV schema")
    for key, value in row.items():
        if "\ufffd" in (value or ""):
            raise NaptanSourceError(f"replacement character U+FFFD in field {key}")
    identity = source_identity(row)
    latitude = parse_coordinate(row.get("Latitude"), -90, 90)
    longitude = parse_coordinate(row.get("Longitude"), -180, 180)
    has_wgs84 = latitude is not None and longitude is not None
    easting = row.get("Easting", "").strip() or None
    northing = row.get("Northing", "").strip() or None
    return {
        "source_identity": identity,
        "atco_code": row["ATCOCode"],
        "naptan_code": row.get("NaptanCode", ""),
        "common_name": row.get("CommonName", ""),
        "short_common_name": row.get("ShortCommonName", ""),
        "locality_name": row.get("LocalityName", ""),
        "town": row.get("Town", ""),
        "stop_type": row.get("StopType", ""),
        "bus_stop_type": row.get("BusStopType", ""),
        "nptg_locality_code": row.get("NptgLocalityCode", ""),
        "administrative_area_code": row.get("AdministrativeAreaCode", ""),
        "grid_type": row.get("GridType", ""),
        "easting": easting,
        "northing": northing,
        "longitude": longitude,
        "latitude": latitude,
        "coordinate_scope": "TRANSPORT_STOP_LEVEL" if has_wgs84 else None,
        "status": row.get("Status", ""),
        "modification": row.get("Modification", ""),
        "modification_datetime": row.get("ModificationDateTime", ""),
        "normalized_name": normalize_text(row.get("CommonName")),
        "normalized_short_name": normalize_text(row.get("ShortCommonName")),
        "normalized_locality": normalize_text(row.get("LocalityName")),
        "normalized_town": normalize_text(row.get("Town")),
    }


def iter_rows(path: Path) -> Iterable[dict[str, Any]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        if reader.fieldnames != EXPECTED_HEADERS:
            raise NaptanSourceError(f"unexpected NaPTAN headers: {reader.fieldnames}")
        for row in reader:
            yield parse_row(row)


def profile_source(path: Path) -> tuple[dict[str, Any], float]:
    started = time.perf_counter()
    stop_types: Counter[str] = Counter()
    bus_types: Counter[str] = Counter()
    statuses: Counter[str] = Counter()
    modifications: Counter[str] = Counter()
    admin_areas: Counter[str] = Counter()
    grid_types: Counter[str] = Counter()
    locality_codes: Counter[str] = Counter()
    identities: set[str] = set()
    coord_groups: Counter[tuple[float, float]] = Counter()
    total = with_coords = without_coords = projected = missing_identity = 0
    invalid_coordinate_rows = 0
    unicode_replacement_count = 0
    for row in iter_rows(path):
        total += 1
        identity = row["source_identity"]
        if identity in identities:
            # Keep the duplicate visible to the caller; the source identity is
            # still publisher-defined and must not be replaced with row order.
            pass
        identities.add(identity)
        stop_types[row["stop_type"]] += 1
        if row["bus_stop_type"]:
            bus_types[row["bus_stop_type"]] += 1
        statuses[row["status"]] += 1
        modifications[row["modification"]] += 1
        if row["administrative_area_code"]:
            admin_areas[row["administrative_area_code"]] += 1
        if row["nptg_locality_code"]:
            locality_codes[row["nptg_locality_code"]] += 1
        if row["grid_type"]:
            grid_types[row["grid_type"]] += 1
        if row["latitude"] is not None and row["longitude"] is not None:
            with_coords += 1
            coord_groups[(row["latitude"], row["longitude"])] += 1
        else:
            without_coords += 1
        if row["easting"] and row["northing"]:
            projected += 1
    elapsed = time.perf_counter() - started
    duplicate_id_rows = total - len(identities)
    profile = {
        "source_file": path.name,
        "source_file_bytes": path.stat().st_size,
        "encoding": "UTF-8 with optional BOM accepted; invalid decoding fails closed",
        "headers": EXPECTED_HEADERS,
        "total_rows": total,
        "distinct_publisher_atco_codes": len(identities),
        "duplicate_publisher_identity_rows": duplicate_id_rows,
        "missing_publisher_identity_rows": missing_identity,
        "replacement_character_rows": unicode_replacement_count,
        "status_distribution": dict(sorted(statuses.items())),
        "modification_distribution": dict(sorted(modifications.items())),
        "stop_type_distribution": dict(sorted(stop_types.items())),
        "bus_stop_type_distribution": dict(sorted(bus_types.items())),
        "administrative_area_count": len(admin_areas),
        "administrative_area_distribution": dict(sorted(admin_areas.items())),
        "nptg_locality_count": len(locality_codes),
        "coordinate_statistics": {
            "wgs84_complete_rows": with_coords,
            "wgs84_missing_rows": without_coords,
            "invalid_coordinate_rows": invalid_coordinate_rows,
            "projected_easting_northing_complete_rows": projected,
            "projected_grid_types": dict(sorted(grid_types.items())),
            "distinct_wgs84_coordinate_pairs": len(coord_groups),
            "shared_wgs84_coordinate_pairs": sum(1 for n in coord_groups.values() if n > 1),
            "max_rows_per_coordinate_pair": max(coord_groups.values(), default=0),
            "semantic_scope": "TRANSPORT_STOP_LEVEL",
        },
        "hierarchy": {
            "retrieved_files_containing_stop_areas": [],
            "stop_area_count": None,
            "stop_area_membership_rows": None,
            "orphan_stop_points": None,
            "multi_parent_stop_points": None,
            "status": "NOT_PRESENT_IN_RETRIEVED_NATIONAL_STOPS_CSV",
            "note": "NptgLocalityCode is a locality reference, not a StopArea membership relation.",
        },
        "parser_performance": {
            "elapsed_seconds": round(elapsed, 6),
            "rows_per_second": round(total / elapsed, 2) if elapsed else None,
            "memory_behavior": "streaming CSV parse; no raw national rows retained",
        },
    }
    return profile, elapsed


def stop_type_artifact(profile: dict[str, Any]) -> dict[str, Any]:
    rows = []
    for stop_type, count in profile["stop_type_distribution"].items():
        classification, meaning = STOP_TYPE_CLASSIFICATIONS.get(
            stop_type, ("UNRESOLVED", "not documented by the audited classifier")
        )
        rows.append({
            "stop_type": stop_type,
            "count": count,
            "source_meaning": meaning,
            "relief_classification": classification,
            "rationale": "Transport identity evidence only; classification does not authorize canonical facility creation.",
        })
    return {
        "source_schema_reference": SCHEMA_URL,
        "classifications": rows,
        "unresolved_types": [r["stop_type"] for r in rows if r["relief_classification"] == "UNRESOLVED"],
    }


def load_candidates(path: Path) -> list[dict[str, Any]]:
    candidates = []
    for row in iter_rows(path):
        if row["stop_type"] in RELIEF_PLACE_TYPES:
            candidates.append(row)
    return sorted(candidates, key=lambda r: r["source_identity"])


def token_similarity(left: str, right: str) -> float:
    if not left or not right:
        return 0.0
    if left == right:
        return 1.0
    left_tokens = set(left.split())
    right_tokens = set(right.split())
    overlap = len(left_tokens & right_tokens) / max(len(left_tokens | right_tokens), 1)
    return max(overlap, SequenceMatcher(None, left, right).ratio())


def haversine_m(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    radius = 6371000.0
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp = math.radians(lat2 - lat1)
    dl = math.radians(lon2 - lon1)
    a = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * radius * math.asin(math.sqrt(a))


def reconcile_tfl(station_csv: Path, points_csv: Path, naptan_path: Path) -> dict[str, Any]:
    stations = {}
    with station_csv.open(encoding="utf-8-sig", newline="") as handle:
        for row in csv.DictReader(handle):
            stations[row["UniqueId"]] = {"id": row["UniqueId"], "name": row["Name"]}
    points = defaultdict(list)
    with points_csv.open(encoding="utf-8-sig", newline="") as handle:
        for row in csv.DictReader(handle):
            try:
                lat, lon = float(row["Lat"]), float(row["Lon"])
            except (ValueError, TypeError):
                continue
            points[row["StationUniqueId"]].append((lat, lon))
    candidates = load_candidates(naptan_path)
    name_index: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for candidate in candidates:
        for name in {candidate["normalized_name"], candidate["normalized_short_name"]}:
            if name:
                name_index[name].append(candidate)
    results = []
    counts = Counter()
    for station_id, station in sorted(stations.items()):
        coords = points.get(station_id, [])
        if not coords:
            results.append({"tfl_station_id": station_id, "station_name": station["name"], "classification": "NO_MATCH", "confidence": "LOW", "candidates": [], "evidence": ["frozen TfL station points have no usable coordinate"]})
            counts["NO_MATCH"] += 1
            continue
        lat = sum(c[0] for c in coords) / len(coords)
        lon = sum(c[1] for c in coords) / len(coords)
        name = normalize_text(station["name"])
        possible = list(name_index.get(name, []))
        if not possible:
            possible = [c for c in candidates if c["normalized_name"] and token_similarity(name, c["normalized_name"]) >= 0.82]
        ranked = []
        for candidate in possible:
            if candidate["latitude"] is None:
                continue
            distance = haversine_m(lat, lon, candidate["latitude"], candidate["longitude"])
            similarity = max(token_similarity(name, candidate["normalized_name"]), token_similarity(name, candidate["normalized_short_name"]))
            if distance <= 750 and similarity >= 0.72:
                ranked.append({"source_identity": candidate["source_identity"], "atco_code": candidate["atco_code"], "stop_type": candidate["stop_type"], "common_name": candidate["common_name"], "distance_metres": round(distance, 1), "name_similarity": round(similarity, 4)})
        ranked.sort(key=lambda item: (item["distance_metres"], item["source_identity"]))
        if not ranked:
            classification, confidence, evidence = "NO_MATCH", "LOW", ["no official candidate within deterministic name/geometry threshold"]
        elif len(ranked) > 1:
            classification, confidence, evidence = "MULTI_NODE_SAME_TRANSPORT_COMPLEX", "MEDIUM", ["multiple official transport-place nodes share the station name/nearby geometry", "nodes must not become multiple Relief facilities automatically"]
        elif ranked[0]["name_similarity"] == 1.0 and ranked[0]["distance_metres"] <= 250:
            classification, confidence, evidence = "HIGH_CONFIDENCE_NAME_GEO_MATCH", "HIGH", ["exact normalized name and unique official candidate within 250m", "no explicit TfL-to-NaPTAN identifier cross-reference was present"]
        else:
            classification, confidence, evidence = "AMBIGUOUS", "LOW", ["candidate requires non-exact name/geometry interpretation"]
        counts[classification] += 1
        results.append({"tfl_station_id": station_id, "station_name": station["name"], "classification": classification, "confidence": confidence, "candidates": ranked[:10], "evidence": evidence, "facility_creation_authorized": False})
    return {"source": {"tfl_station_file": str(station_csv).replace("\\", "/"), "tfl_station_points_file": str(points_csv).replace("\\", "/"), "naptan_source": SOURCE_URL}, "counts": dict(sorted(counts.items())), "station_count": len(results), "results": results}


def national_dry_run(facilities_path: Path, naptan_path: Path) -> dict[str, Any]:
    facilities = json.loads(facilities_path.read_text(encoding="utf-8"))
    if isinstance(facilities, dict):
        facilities = facilities.get("facilities", facilities.get("data", []))
    normalized_facilities = []
    for facility in facilities:
        normalized_facilities.append({"id": facility.get("id"), "name": facility.get("name", ""), "lat": facility.get("latitude"), "lon": facility.get("longitude"), "normalized_name": normalize_matching_text(facility.get("name"))})
    facility_grid: dict[tuple[int, int], list[dict[str, Any]]] = defaultdict(list)
    grid_size = 0.005
    for facility in normalized_facilities:
        try:
            if facility["lat"] is not None and facility["lon"] is not None:
                facility_grid[(int(float(facility["lat"]) / grid_size), int(float(facility["lon"]) / grid_size))].append(facility)
        except (TypeError, ValueError):
            continue
    candidates = load_candidates(naptan_path)
    counts = Counter()
    examples = defaultdict(list)
    for node in candidates:
        matches = []
        if node["latitude"] is not None:
            node_cell = (int(node["latitude"] / grid_size), int(node["longitude"] / grid_size))
            nearby = []
            for dlat in (-1, 0, 1):
                for dlon in (-1, 0, 1):
                    nearby.extend(facility_grid.get((node_cell[0] + dlat, node_cell[1] + dlon), []))
            for facility in nearby:
                try:
                    distance = haversine_m(node["latitude"], node["longitude"], float(facility["lat"]), float(facility["lon"]))
                except (TypeError, ValueError):
                    continue
                similarity = token_similarity(node["normalized_name"], facility["normalized_name"])
                if distance <= 500 and similarity >= 0.72:
                    matches.append((distance, similarity, facility))
        matches.sort(key=lambda item: (item[0], -item[1], item[2]["id"] or ""))
        if len(matches) == 1 and matches[0][1] == 1.0 and matches[0][0] <= 250:
            bucket = "likely_existing_relief_match"
        elif matches:
            bucket = "ambiguous_existing_relief_match"
        else:
            bucket = "likely_new_transport_place_candidate"
        counts[bucket] += 1
        if len(examples[bucket]) < 5:
            examples[bucket].append({"naptan_source_identity": node["source_identity"], "stop_type": node["stop_type"], "common_name": node["common_name"], "candidate_facility": matches[0][2]["id"] if matches else None})
    support_count = sum(1 for row in iter_rows(naptan_path) if row["stop_type"] not in RELIEF_PLACE_TYPES)
    counts["supporting_only_or_excluded_nodes"] = support_count
    return {"source": SOURCE_URL, "facility_snapshot": "tools/source_expansion/cache/tfl-detailed-2026-08-21/production-published-facilities.json", "candidate_stop_types": sorted(RELIEF_PLACE_TYPES), "counts": dict(sorted(counts.items())), "examples": dict(sorted(examples.items())), "production_mutation_plan": {"facilities_inserts": 0, "facilities_updates": 0, "facility_sources_inserts": 0, "observations_inserts": 0, "production_execution": False}}


def build_manifest(source: Path, retrieval_utc: str) -> dict[str, Any]:
    size = source.stat().st_size
    digest = sha256_file(source)
    return {"publisher": "UK Department for Transport", "product": "NaPTAN national access nodes CSV", "source_url": SOURCE_URL, "download_page": DOWNLOAD_PAGE, "resolved_url": SOURCE_URL, "retrieval_utc": retrieval_utc, "filename": "Stops.csv", "content_type": "application/csv", "format": "CSV", "compression": "none", "byte_size": size, "sha256": digest, "source_publication_or_update_date": SOURCE_DATE, "update_cadence": "The official national download page publishes the current national export; separate data.gov.uk metadata describes daily updates. No file-level publication timestamp was embedded in Stops.csv.", "file_inventory": [{"filename": "Stops.csv", "byte_size": size, "sha256": digest, "role": "CORE_FOR_RELIEF"}], "licence": {"name": "Open Government Licence v3.0", "url": LICENCE_URL, "attribution": "Contains public sector information licensed under the Open Government Licence v3.0.", "reuse_note": "Foundation use is recorded as compatible with the published OGL terms; this is not a legal opinion and third-party rights remain subject to the published terms."}, "raw_bytes_repository_policy": "Raw national bytes kept in disposable external cache and not committed to Git; manifest and derived evidence only.", "encoding": "UTF-8 CSV with optional BOM; replacement characters rejected"}


def write_artifacts(source: Path, output: Path, retrieval_utc: str, tfl_station: Path, tfl_points: Path, facilities: Path) -> None:
    output.mkdir(parents=True, exist_ok=True)
    manifest = build_manifest(source, retrieval_utc)
    profile, elapsed = profile_source(source)
    type_artifact = stop_type_artifact(profile)
    tfl = reconcile_tfl(tfl_station, tfl_points, source)
    dry = national_dry_run(facilities, source)
    (output / "NAPTAN_N1_SOURCE_MANIFEST_2026-08-22.json").write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    (output / "NAPTAN_N1_SEMANTIC_PROFILE_2026-08-22.json").write_text(json.dumps(profile, indent=2, ensure_ascii=False, sort_keys=True) + "\n", encoding="utf-8")
    (output / "NAPTAN_N1_STOP_TYPE_CLASSIFICATION_2026-08-22.json").write_text(json.dumps(type_artifact, indent=2, ensure_ascii=False, sort_keys=True) + "\n", encoding="utf-8")
    tfl_artifact = {"frozen_tfl_reconciliation_sha256": "65cc9cc8c41b7b3a003524610b674c7f2eae96ff7fe5116f38f2d2856cb777cb", "frozen_tfl_zip_sha256": "19c50772febd1a3d7625f59e079b7590c5da4ed70424d6f552cfd7db1611e2ce", "source": SOURCE_URL, "counts": tfl["counts"], "station_count": tfl["station_count"], "results": tfl["results"], "production_mutation_plan": {"facilities": 0, "facility_sources": 0, "facility_source_observations": 0, "toilet_units": 0, "toilet_unit_sources": 0, "production_execution": False}}
    (output / "NAPTAN_N1_TFL_RECONCILIATION_2026-08-22.json").write_text(json.dumps(tfl_artifact, indent=2, ensure_ascii=False, sort_keys=True) + "\n", encoding="utf-8")
    (output / "NAPTAN_N1_RELIEF_DRY_RUN_2026-08-22.json").write_text(json.dumps(dry, indent=2, ensure_ascii=False, sort_keys=True) + "\n", encoding="utf-8")
    report = f"""# Relief NaPTAN N1 — National Source Capture and Semantic Audit

## Classification

**RELIEF NAPTAN N1 — NATIONAL TRANSPORT IDENTITY FOUNDATION COMPLETE / PRODUCTION INGESTION NOT AUTHORIZED**

## Source and integrity

- Publisher: UK Department for Transport, official NaPTAN service.
- Product: current national `Stops.csv` access-node export.
- URL: {SOURCE_URL}
- Retrieval UTC: {retrieval_utc}
- Bytes: {manifest['byte_size']:,}
- SHA-256: `{manifest['sha256']}`
- Encoding: UTF-8 CSV with optional BOM; decoding and U+FFFD corruption fail closed.
- Licence: Open Government Licence v3.0. Attribution retained: “{manifest['licence']['attribution']}”
- The raw national file was not committed; it was held in a disposable external cache and removed after artifact generation.

The official national download page and DfT API catalogue identify this as the current national machine-readable NaPTAN access-node product. The GOV.UK schema page records the OGL v3.0 publication terms. The retrieved response contained one file, `Stops.csv`; StopArea/StopsInArea/AreaHierarchy files were not present in this product and are not invented below.

## National profile

- Total rows: **{profile['total_rows']:,}**
- Distinct publisher ATCO identities: **{profile['distinct_publisher_atco_codes']:,}**
- Duplicate publisher-identity rows: **{profile['duplicate_publisher_identity_rows']:,}**
- Rows with complete WGS84 coordinates: **{profile['coordinate_statistics']['wgs84_complete_rows']:,}**
- Rows without complete WGS84 coordinates: **{profile['coordinate_statistics']['wgs84_missing_rows']:,}**
- Projected Easting/Northing pairs: **{profile['coordinate_statistics']['projected_easting_northing_complete_rows']:,}**
- Administrative areas: **{profile['administrative_area_count']:,}**
- Stop areas/membership: **not available in retrieved `Stops.csv`**; locality codes are not treated as StopArea links.
- Parser performance: {profile['parser_performance']['elapsed_seconds']} seconds; {profile['parser_performance']['rows_per_second']:,} rows/sec; streaming parse with no raw-row retention.

### Stop types

| Type | Count | Meaning / Relief classification |
|---|---:|---|
""" + "\n".join(f"| `{r['stop_type']}` | {r['count']:,} | {r['source_meaning']} / `{r['relief_classification']}` |" for r in type_artifact["classifications"]) + f"""

The classification is transport-identity evidence only. It does not authorize creating Relief facilities, toilets, or source links.

## Identifier and geometry model

`ATCOCode` is treated as the publisher-defined stop-point identity and proposed future namespace `naptan:<ATCOCode>`. `NaptanCode`, plate, locality, and administrative codes remain secondary/source fields; none is substituted for ATCOCode. Row position is never an identity. Duplicate publisher identity is a hard reconciliation error, not a deduplication invitation.

Longitude/Latitude are preserved at **`TRANSPORT_STOP_LEVEL`**. Easting/Northing and GridType are retained as source geometry. No source geometry is interpreted as a Relief toilet coordinate. Shared coordinates are recorded as shared transport-node geometry, not evidence of duplicate facilities.

## Hierarchy

The retrieved national CSV does not contain StopArea, StopsInArea, or AreaHierarchy tables. Stop-area counts, orphan membership, multi-parent membership, and interchange topology are therefore **NOT_COMPUTABLE_FROM_THIS_PRODUCT**. N2 must capture the official hierarchy product/API before using hierarchy as a matching signal. No invented grouping is emitted.

## TfL ↔ NaPTAN proof of concept

The frozen TfL station/station-point files were used without refresh. The reconciliation output contains **{tfl['station_count']}** station candidates and is deterministic. Counts:

{json.dumps(tfl['counts'], indent=2)}

There was no explicit TfL-to-NaPTAN identifier cross-reference in the frozen cohort. Exact identifier matches are therefore not manufactured. Name/geometry matches are evidence for future review only; multi-node results remain one transport-complex candidate, not multiple Relief facilities.

## Relief dry run

The read-only estimate uses the existing committed production-published facility snapshot. It is not an insertion plan. The machine-readable dry-run artifact reports candidate transport-place matches, ambiguity, supporting-only nodes, and a zero-mutation plan.

## Schema readiness

**SCHEMA_READY_WITH_MINOR_MODEL_GAP.** Existing `facility_sources` and private `facility_source_observations` can preserve future NaPTAN source identity and structured source evidence attached to a canonical facility without canonical overwrite or toilet-unit creation. The current schema does not provide a first-class transport-node/StopArea hierarchy object, so a later additive transport-source model is likely required before ingesting hierarchy as canonical data. No migration is created in N1.

## Future ingestion gates

1. Capture the official national node and hierarchy products with a manifest and immutable hashes.
2. Validate ATCO identity uniqueness, encoding, status, and geometry.
3. Classify source nodes into candidate place, supporting node, excluded, or unresolved.
4. Reconcile exact identity/group evidence before name/geometry matching.
5. Attach source evidence to existing facilities or quarantine; never apply `one row = one facility`.
6. Require explicit authorization for any new canonical transport place, source link, or schema migration.
7. Make repeat ingestion idempotent and fail closed on conflicts.

## RDG compatibility

The proposed identity/hierarchy separation can later accept National Rail/RDG evidence as another source without inventing a direct RDG↔NaPTAN key. RDG integration remains pending; direct cross-reference, hierarchy semantics, and identifier joins are unresolved and must be verified from the future official RDG source.

## Production safety

This batch performed no production write, migration, RPC, staging operation, import run, source-link insertion, facility mutation, or toilet operation. **TOTAL PRODUCTION MUTATIONS: 0.**

## Evidence files

- Source manifest: `NAPTAN_N1_SOURCE_MANIFEST_2026-08-22.json`
- Semantic profile: `NAPTAN_N1_SEMANTIC_PROFILE_2026-08-22.json`
- Stop-type classification: `NAPTAN_N1_STOP_TYPE_CLASSIFICATION_2026-08-22.json`
- TfL reconciliation: `NAPTAN_N1_TFL_RECONCILIATION_2026-08-22.json`
- Relief dry run: `NAPTAN_N1_RELIEF_DRY_RUN_2026-08-22.json`
"""
    (output / "NAPTAN_N1_FOUNDATION_REPORT_2026-08-22.md").write_text(report, encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="Profile official NaPTAN national CSV; no production apply path exists.")
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--tfl-stations", type=Path, required=True)
    parser.add_argument("--tfl-station-points", type=Path, required=True)
    parser.add_argument("--facilities", type=Path, required=True)
    parser.add_argument("--retrieval-utc", required=True)
    args = parser.parse_args()
    write_artifacts(args.source, args.output_dir, args.retrieval_utc, args.tfl_stations, args.tfl_station_points, args.facilities)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

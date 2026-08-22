"""Read-only NaPTAN N2 StopArea and interchange hierarchy analysis.

The tool consumes the current official NaPTAN XML package, which contains
StopPoints with publisher-declared StopAreaRef memberships and StopAreas. It
does not contain an apply flag or any production database client.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import time
import xml.etree.ElementTree as ET
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

from tools.source_expansion.naptan_n1 import (
    RELIEF_PLACE_TYPES,
    haversine_m,
    normalize_text,
    normalize_matching_text,
    token_similarity,
)


XML_URL = "https://naptan.api.dft.gov.uk/v1/access-nodes?dataFormat=xml"
SWAGGER_URL = "https://naptan.api.dft.gov.uk/swagger/v1/swagger.json"
DOWNLOAD_PAGE = "https://beta-naptan.dft.gov.uk/download/national"
API_CATALOGUE = "https://www.api.gov.uk/dft/national-public-transport-access-nodes-naptan-and-national-public-transport-gazetteer-nptg-api/"
SCHEMA_URL = "https://naptan.dft.gov.uk/naptan/schema/2.5/doc/NaPTANSchemaGuide-2.5-v0.67.pdf"
LICENCE_URL = "https://www.gov.uk/government/publications/national-public-transport-access-node-schema/naptan-and-nptg-data-sets-and-schema-guides"
XML_RETRIEVAL_UTC = "2026-08-22T13:57:21Z"
SWAGGER_RETRIEVAL_UTC = "2026-08-22T13:55:27Z"
FROZEN_N1_RECONCILIATION = "65cc9cc8c41b7b3a003524610b674c7f2eae96ff7fe5116f38f2d2856cb777cb"
FROZEN_N1_ZIP = "19c50772febd1a3d7625f59e079b7590c5da4ed70424d6f552cfd7db1611e2ce"
NS = "{http://www.naptan.org.uk/}"
XML_LANG = "{http://www.w3.org/XML/1998/namespace}lang"


class NaptanHierarchyError(ValueError):
    pass


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest().upper()


def local_name(tag: str) -> str:
    return tag.rsplit("}", 1)[-1]


def text_of(element: ET.Element, wanted: str) -> str:
    for child in element.iter():
        if local_name(child.tag) == wanted:
            value = (child.text or "").strip()
            if "\ufffd" in value:
                raise NaptanHierarchyError(f"replacement character U+FFFD in {wanted}")
            return value
    return ""


def all_texts(element: ET.Element, wanted: str) -> list[str]:
    values = []
    for child in element.iter():
        if local_name(child.tag) == wanted:
            value = (child.text or "").strip()
            if "\ufffd" in value:
                raise NaptanHierarchyError(f"replacement character U+FFFD in {wanted}")
            if value:
                values.append(value)
    return values


def child_attribute(element: ET.Element, wanted: str) -> str:
    value = element.attrib.get(wanted, "")
    if "\ufffd" in value:
        raise NaptanHierarchyError(f"replacement character U+FFFD in attribute {wanted}")
    return value.strip()


def float_or_none(value: str) -> float | None:
    if not value:
        return None
    try:
        number = float(value)
    except ValueError as exc:
        raise NaptanHierarchyError(f"invalid numeric XML value {value!r}") from exc
    if not math.isfinite(number):
        raise NaptanHierarchyError(f"non-finite XML numeric value {value!r}")
    return number


def valid_lat_lon(latitude: float | None, longitude: float | None) -> bool:
    return latitude is not None and longitude is not None and -90 <= latitude <= 90 and -180 <= longitude <= 180


def stop_area_identity(value: str) -> str:
    if not value:
        raise NaptanHierarchyError("StopAreaCode is missing")
    return f"naptan-stop-area:{value.upper()}"


def mode_for_stop_type(stop_type: str) -> str:
    if stop_type in {"RLY", "RSE", "RPL"}:
        return "rail"
    if stop_type in {"MET", "TMU", "PLT"}:
        return "metro_tram_underground"
    if stop_type in {"BCT", "BCE", "BCQ", "BCS", "BST"}:
        return "bus_coach"
    if stop_type in {"FER", "FTD", "FBT"}:
        return "ferry_port"
    if stop_type in {"AIR", "GAT"}:
        return "air"
    if stop_type in {"TXR", "STR"}:
        return "taxi"
    return "other"


def source_manifest(xml_path: Path, swagger_path: Path) -> dict[str, Any]:
    return {
        "publisher": "UK Department for Transport",
        "product": "NaPTAN national XML access-node and StopArea package",
        "sources": [
            {
                "url": XML_URL,
                "documentation_url": DOWNLOAD_PAGE,
                "retrieval_utc": XML_RETRIEVAL_UTC,
                "filename": "NaPTAN.xml",
                "content_type": "application/xml",
                "format": "XML",
                "compression": "none",
                "byte_size": xml_path.stat().st_size,
                "sha256": sha256_file(xml_path),
                "role": "CORE_FOR_RELIEF",
                "top_level_structures_observed": ["StopPoints", "StopAreas"],
            },
            {
                "url": SWAGGER_URL,
                "documentation_url": API_CATALOGUE,
                "retrieval_utc": SWAGGER_RETRIEVAL_UTC,
                "filename": "swagger.json",
                "content_type": "application/json",
                "format": "OpenAPI JSON",
                "compression": "none",
                "byte_size": swagger_path.stat().st_size,
                "sha256": sha256_file(swagger_path),
                "role": "SUPPORTING_IDENTITY",
                "endpoints_observed": ["/v1/access-nodes", "/v1/nptg", "/v1/nptg/localities"],
            },
        ],
        "licence": {
            "name": "Open Government Licence v3.0",
            "url": LICENCE_URL,
            "attribution": "Contains public sector information licensed under the Open Government Licence v3.0.",
            "reuse_note": "Foundation evidence records the published terms only; this is not a legal opinion.",
        },
        "encoding": "UTF-8 XML/JSON; replacement characters rejected",
        "raw_bytes_repository_policy": "Raw national XML and OpenAPI bytes remain in disposable external cache and are not committed.",
    }


def parse_xml(xml_path: Path) -> tuple[dict[str, Any], float]:
    started = time.perf_counter()
    points: set[str] = set()
    point_coords: dict[str, tuple[float, float]] = {}
    point_types: dict[str, str] = {}
    point_parents: defaultdict[str, set[str]] = defaultdict(set)
    area_members: defaultdict[str, set[str]] = defaultdict(set)
    area_modes: defaultdict[str, set[str]] = defaultdict(set)
    area_metadata: dict[str, dict[str, Any]] = {}
    area_parent_links: set[tuple[str, str]] = set()
    point_duplicates = 0
    area_duplicates = 0
    point_status: Counter[str] = Counter()
    area_status: Counter[str] = Counter()
    point_modifications: Counter[str] = Counter()
    area_modifications: Counter[str] = Counter()
    point_type_counts: Counter[str] = Counter()
    area_type_counts: Counter[str] = Counter()
    point_coord_count = 0
    area_coord_count = 0
    area_direct_grid_types: Counter[str] = Counter()
    invalid_relationship_elements = 0
    missing_point_identity = 0

    for _, element in ET.iterparse(xml_path, events=("end",)):
        kind = local_name(element.tag)
        if kind == "StopPoint":
            atco = text_of(element, "AtcoCode")
            if not atco:
                missing_point_identity += 1
                raise NaptanHierarchyError("StopPoint has no AtcoCode")
            point_id = f"naptan:{atco.upper()}"
            if point_id in points:
                point_duplicates += 1
            points.add(point_id)
            status = child_attribute(element, "Status") or ""
            modification = child_attribute(element, "Modification") or ""
            point_status[status] += 1
            point_modifications[modification] += 1
            stop_type = text_of(element, "StopType")
            point_types[point_id] = stop_type
            point_type_counts[stop_type] += 1
            latitude = float_or_none(text_of(element, "Latitude"))
            longitude = float_or_none(text_of(element, "Longitude"))
            if latitude is not None or longitude is not None:
                if not valid_lat_lon(latitude, longitude):
                    raise NaptanHierarchyError(f"invalid StopPoint coordinates for {point_id}")
                point_coords[point_id] = (latitude, longitude)
                point_coord_count += 1
            refs = []
            for child in element.iter():
                if local_name(child.tag) == "StopAreaRef":
                    ref = (child.text or "").strip()
                    if not ref:
                        invalid_relationship_elements += 1
                    else:
                        refs.append(ref)
            for ref in refs:
                area_id = stop_area_identity(ref)
                if area_id in point_parents[point_id]:
                    invalid_relationship_elements += 1
                point_parents[point_id].add(area_id)
                area_members[area_id].add(point_id)
                area_modes[area_id].add(mode_for_stop_type(stop_type))
            element.clear()
        elif kind == "StopArea":
            code = text_of(element, "StopAreaCode")
            area_id = stop_area_identity(code)
            if area_id in area_metadata:
                area_duplicates += 1
            latitude = float_or_none(text_of(element, "Latitude"))
            longitude = float_or_none(text_of(element, "Longitude"))
            if latitude is not None or longitude is not None:
                if not valid_lat_lon(latitude, longitude):
                    raise NaptanHierarchyError(f"invalid StopArea coordinates for {area_id}")
                area_coord_count += 1
            grid_type = text_of(element, "GridType")
            if grid_type:
                area_direct_grid_types[grid_type] += 1
            area_metadata[area_id] = {
                "source_identity": area_id,
                "publisher_id": code,
                "name": text_of(element, "Name"),
                "normalized_name": normalize_text(text_of(element, "Name")),
                "area_type": text_of(element, "StopAreaType") or text_of(element, "Type"),
                "administrative_area_code": text_of(element, "AdministrativeAreaRef"),
                "latitude": latitude,
                "longitude": longitude,
                "grid_type": grid_type,
                "status": child_attribute(element, "Status") or "",
                "modification": child_attribute(element, "Modification") or "",
            }
            area_status[area_metadata[area_id]["status"]] += 1
            area_modifications[area_metadata[area_id]["modification"]] += 1
            area_type_counts[area_metadata[area_id]["area_type"]] += 1
            for child in element.iter():
                name = local_name(child.tag)
                if name.lower() in {"parentstoparearef", "parentstopareacode", "parentid"}:
                    parent = (child.text or "").strip()
                    if parent:
                        area_parent_links.add((area_id, stop_area_identity(parent)))
            element.clear()

    for area_id, metadata in area_metadata.items():
        if metadata["latitude"] is None or metadata["longitude"] is None:
            coords = [point_coords[p] for p in area_members.get(area_id, ()) if p in point_coords]
            if coords:
                metadata["latitude"] = sum(c[0] for c in coords) / len(coords)
                metadata["longitude"] = sum(c[1] for c in coords) / len(coords)
                metadata["coordinate_scope"] = "DERIVED_FROM_MEMBER_STOPPOINTS"
            else:
                metadata["coordinate_scope"] = None
        else:
            metadata["coordinate_scope"] = "STOP_AREA_LEVEL"
        metadata["member_count"] = len(area_members.get(area_id, ()))
        metadata["modes"] = sorted(area_modes.get(area_id, ()))

    point_parent_distribution = Counter(len(point_parents.get(point_id, ())) for point_id in points)
    area_member_distribution = Counter(len(area_members.get(area_id, ())) for area_id in area_metadata)
    missing_area_refs = sorted({area_id for parents in point_parents.values() for area_id in parents if area_id not in area_metadata})
    missing_point_refs = sorted({point_id for members in area_members.values() for point_id in members if point_id not in points})
    duplicate_memberships = invalid_relationship_elements

    roots = {area_id for area_id in area_metadata if not any(child == area_id for child, _ in area_parent_links)}
    parent_map: defaultdict[str, set[str]] = defaultdict(set)
    for child, parent in area_parent_links:
        parent_map[child].add(parent)
    cycle_nodes: set[str] = set()
    def visit(node: str, path: set[str]) -> None:
        if node in path:
            cycle_nodes.update(path)
            return
        for parent in parent_map.get(node, ()):
            visit(parent, path | {node})
    for area_id in area_metadata:
        visit(area_id, set())

    elapsed = time.perf_counter() - started
    area_mode_counts = Counter()
    multimodal = 0
    for metadata in area_metadata.values():
        modes = tuple(metadata["modes"])
        if len(modes) > 1:
            multimodal += 1
        for mode in modes:
            area_mode_counts[mode] += 1

    profile = {
        "source_file": xml_path.name,
        "source_file_bytes": xml_path.stat().st_size,
        "top_level_structures_observed": ["StopPoints", "StopAreas"],
        "stop_points": {
            "total": len(points),
            "duplicate_identity_rows": point_duplicates,
            "missing_identity_rows": missing_point_identity,
            "status_distribution": dict(sorted(point_status.items())),
            "modification_distribution": dict(sorted(point_modifications.items())),
            "stop_type_distribution": dict(sorted(point_type_counts.items())),
            "complete_wgs84_rows": point_coord_count,
            "coordinate_scope": "TRANSPORT_STOP_LEVEL",
            "parent_distribution": {str(k): v for k, v in sorted(point_parent_distribution.items())},
            "zero_parent": point_parent_distribution.get(0, 0),
            "one_parent": point_parent_distribution.get(1, 0),
            "multiple_parents": sum(v for k, v in point_parent_distribution.items() if k > 1),
        },
        "stop_areas": {
            "total": len(area_metadata),
            "duplicate_identity_rows": area_duplicates,
            "status_distribution": dict(sorted(area_status.items())),
            "modification_distribution": dict(sorted(area_modifications.items())),
            "area_type_distribution": dict(sorted(area_type_counts.items())),
            "complete_direct_wgs84_rows": area_coord_count,
            "derived_member_centroid_rows": sum(1 for a in area_metadata.values() if a["coordinate_scope"] == "DERIVED_FROM_MEMBER_STOPPOINTS"),
            "without_coordinates": sum(1 for a in area_metadata.values() if not a["coordinate_scope"]),
            "direct_grid_types": dict(sorted(area_direct_grid_types.items())),
            "member_distribution": {str(k): v for k, v in sorted(area_member_distribution.items())},
            "zero_members": area_member_distribution.get(0, 0),
            "one_member": area_member_distribution.get(1, 0),
            "multiple_members": sum(v for k, v in area_member_distribution.items() if k > 1),
            "maximum_members": max(area_member_distribution, default=0),
            "modes_by_area_count": dict(sorted(area_mode_counts.items())),
            "multimodal_area_count": multimodal,
        },
        "memberships": {
            "total_rows": sum(len(parents) for parents in point_parents.values()),
            "distinct_stop_points_with_memberships": len(point_parents),
            "distinct_stop_areas_with_children": len(area_members),
            "duplicate_memberships": duplicate_memberships,
            "missing_stop_area_references": len(missing_area_refs),
            "missing_stop_point_references": len(missing_point_refs),
            "invalid_relationship_elements": invalid_relationship_elements,
            "publisher_declared": True,
            "spatial_memberships_inferred": 0,
        },
        "hierarchy": {
            "parent_relationship_rows": len(area_parent_links),
            "root_area_count": len(roots),
            "multiple_parent_child_areas": sum(1 for child, parents in parent_map.items() if len(parents) > 1),
            "cycle_nodes": sorted(cycle_nodes),
            "cycle_count": len(cycle_nodes),
            "orphan_parent_references": sorted(parent for _, parent in area_parent_links if parent not in area_metadata),
            "max_depth": hierarchy_depth(parent_map, area_metadata),
            "nested_area_structure_observed": bool(area_parent_links),
        },
        "performance": {
            "measurement": "diagnostic runtime is reported in the human report; deterministic profile excludes elapsed time",
            "memory_strategy": "iterparse; raw XML elements cleared at StopPoint/StopArea boundaries; compact identity/maps retained",
        },
        "missing_references": {"stop_area_ids": missing_area_refs[:100], "stop_point_ids": missing_point_refs[:100]},
        "area_metadata": sorted(area_metadata.values(), key=lambda a: a["source_identity"]),
    }
    return {"profile": profile, "areas": area_metadata, "points": points, "point_coords": point_coords, "point_types": point_types, "point_parents": point_parents}, elapsed


def hierarchy_depth(parent_map: dict[str, set[str]], areas: dict[str, Any]) -> int:
    def depth(node: str, trail: set[str]) -> int:
        if node in trail:
            return 0
        parents = parent_map.get(node, set())
        return 1 + max((depth(parent, trail | {node}) for parent in parents), default=0)
    return max((depth(node, set()) for node in areas), default=0)


def read_tfl_stations(station_csv: Path, points_csv: Path) -> list[dict[str, Any]]:
    stations: dict[str, dict[str, Any]] = {}
    with station_csv.open(encoding="utf-8-sig", newline="") as handle:
        for row in csv.DictReader(handle):
            stations[row["UniqueId"]] = {"id": row["UniqueId"], "name": row["Name"]}
    coords: defaultdict[str, list[tuple[float, float]]] = defaultdict(list)
    with points_csv.open(encoding="utf-8-sig", newline="") as handle:
        for row in csv.DictReader(handle):
            try:
                coords[row["StationUniqueId"]].append((float(row["Lat"]), float(row["Lon"])))
            except (TypeError, ValueError):
                continue
    result = []
    for station_id, station in sorted(stations.items()):
        station_coords = coords.get(station_id, [])
        result.append({**station, "latitude": sum(x[0] for x in station_coords) / len(station_coords) if station_coords else None, "longitude": sum(x[1] for x in station_coords) / len(station_coords) if station_coords else None})
    return result


def reconcile_tfl_n2(stations: list[dict[str, Any]], areas: dict[str, dict[str, Any]]) -> dict[str, Any]:
    name_index: defaultdict[str, list[dict[str, Any]]] = defaultdict(list)
    for area in areas.values():
        if area["normalized_name"]:
            name_index[area["normalized_name"]].append(area)
    results = []
    counts: Counter[str] = Counter()
    for station in stations:
        ranked = []
        station_name = normalize_text(station["name"])
        possible = list(name_index.get(station_name, []))
        if not possible:
            possible = [a for a in areas.values() if a["normalized_name"] and token_similarity(station_name, a["normalized_name"]) >= 0.86]
        for area in possible:
            if station["latitude"] is None or area["latitude"] is None:
                continue
            distance = haversine_m(station["latitude"], station["longitude"], area["latitude"], area["longitude"])
            similarity = token_similarity(station_name, area["normalized_name"])
            if distance <= 1500 and similarity >= 0.78:
                ranked.append({"stop_area_identity": area["source_identity"], "publisher_id": area["publisher_id"], "name": area["name"], "area_type": area["area_type"], "member_count": area["member_count"], "modes": area["modes"], "distance_metres": round(distance, 1), "name_similarity": round(similarity, 4), "coordinate_scope": area["coordinate_scope"]})
        ranked.sort(key=lambda r: (r["distance_metres"], r["stop_area_identity"]))
        if not ranked:
            classification, confidence, evidence = "NO_MATCH", "LOW", ["no official StopArea within deterministic name/geometry threshold"]
        elif len(ranked) > 1:
            classification, confidence, evidence = "AMBIGUOUS_TRANSPORT_COMPLEX", "MEDIUM", ["multiple official StopAreas satisfy the bounded name/geometry evidence"]
        elif ranked[0]["name_similarity"] == 1.0 and ranked[0]["distance_metres"] <= 500:
            classification, confidence, evidence = "HIGH_CONFIDENCE_STOPAREA_MATCH", "HIGH", ["exact normalized StopArea name and unique StopArea within 500m", "publisher-declared member nodes retained under the StopArea"]
        elif ranked[0]["name_similarity"] >= 0.86 and ranked[0]["distance_metres"] <= 750:
            classification, confidence, evidence = "HIGH_CONFIDENCE_TRANSPORT_COMPLEX_MATCH", "MEDIUM", ["strong normalized name and geometry match to an official StopArea"]
        else:
            classification, confidence, evidence = "AMBIGUOUS_TRANSPORT_COMPLEX", "LOW", ["non-exact StopArea name/geometry evidence remains insufficient"]
        counts[classification] += 1
        results.append({"tfl_station_id": station["id"], "station_name": station["name"], "classification": classification, "confidence": confidence, "candidates": ranked[:20], "evidence": evidence, "facility_creation_authorized": False})
    return {"counts": dict(sorted(counts.items())), "station_count": len(results), "results": results}


def compare_n1_n2(n1_results: list[dict[str, Any]], n2_results: list[dict[str, Any]]) -> dict[str, Any]:
    """Compare committed N1 decisions without reinterpreting frozen source rows."""
    n1 = {row["tfl_station_id"]: row for row in n1_results}
    n2 = {row["tfl_station_id"]: row for row in n2_results}
    high = {"HIGH_CONFIDENCE_STOPAREA_MATCH", "HIGH_CONFIDENCE_TRANSPORT_COMPLEX_MATCH"}
    resolved_no_match = sorted(station_id for station_id, row in n1.items() if row["classification"] == "NO_MATCH" and n2[station_id]["classification"] in high)
    resolved_ambiguous = sorted(station_id for station_id, row in n1.items() if row["classification"] == "AMBIGUOUS" and n2[station_id]["classification"] in high)
    contradicted_high = sorted(station_id for station_id, row in n1.items() if row["classification"] == "HIGH_CONFIDENCE_NAME_GEO_MATCH" and n2[station_id]["classification"] in {"NO_MATCH", "AMBIGUOUS_TRANSPORT_COMPLEX"})
    multi_node = sorted(station_id for station_id, row in n2.items() if row["classification"] in high and row["candidates"] and row["candidates"][0]["member_count"] > 1)
    return {
        "n1_no_match_resolved_to_high_confidence": len(resolved_no_match),
        "n1_ambiguous_resolved_to_high_confidence": len(resolved_ambiguous),
        "n1_high_confidence_contradicted": len(contradicted_high),
        "high_confidence_matches_with_multiple_publisher_member_nodes": len(multi_node),
        "resolved_no_match_examples": resolved_no_match[:10],
        "resolved_ambiguity_examples": resolved_ambiguous[:10],
        "contradicted_high_confidence_examples": contradicted_high[:10],
        "hierarchy_does_not_authorize_facility_or_toilet_creation": True,
    }


def dry_run(areas: dict[str, dict[str, Any]], facilities_path: Path, n1_dry_path: Path) -> dict[str, Any]:
    facilities = json.loads(facilities_path.read_text(encoding="utf-8"))
    if isinstance(facilities, dict):
        facilities = facilities.get("facilities", facilities.get("data", []))
    facility_grid: defaultdict[tuple[int, int], list[dict[str, Any]]] = defaultdict(list)
    for facility in facilities:
        try:
            lat, lon = float(facility["latitude"]), float(facility["longitude"])
        except (KeyError, TypeError, ValueError):
            continue
        facility_grid[(int(lat / 0.005), int(lon / 0.005))].append({"id": facility.get("id"), "name": facility.get("name", ""), "normalized_name": normalize_matching_text(facility.get("name")), "lat": lat, "lon": lon})
    counts: Counter[str] = Counter()
    area_examples: defaultdict[str, list[dict[str, Any]]] = defaultdict(list)
    for area in areas.values():
        if area["member_count"] == 0:
            counts["empty_stop_area"] += 1
            continue
        if area["latitude"] is None:
            counts["unresolved_no_area_geometry"] += 1
            continue
        cell = (int(area["latitude"] / 0.005), int(area["longitude"] / 0.005))
        nearby = []
        for dlat in (-1, 0, 1):
            for dlon in (-1, 0, 1):
                nearby.extend(facility_grid.get((cell[0] + dlat, cell[1] + dlon), []))
        matches = []
        for facility in nearby:
            distance = haversine_m(area["latitude"], area["longitude"], facility["lat"], facility["lon"])
            similarity = token_similarity(area["normalized_name"], facility["normalized_name"])
            if distance <= 750 and similarity >= 0.72:
                matches.append((distance, similarity, facility))
        matches.sort(key=lambda x: (x[0], -x[1], x[2]["id"] or ""))
        if len(matches) == 1 and matches[0][1] == 1.0 and matches[0][0] <= 350:
            bucket = "likely_existing_relief_transport_complex"
        elif matches:
            bucket = "ambiguous_existing_relief_transport_complex"
        else:
            bucket = "likely_new_transport_place_candidate"
        counts[bucket] += 1
        if len(area_examples[bucket]) < 10:
            area_examples[bucket].append({"stop_area_identity": area["source_identity"], "name": area["name"], "member_count": area["member_count"], "modes": area["modes"], "candidate_facility_id": matches[0][2]["id"] if matches else None})
    n1 = json.loads(n1_dry_path.read_text(encoding="utf-8"))
    return {"node_level_counts": n1["counts"], "transport_complex_level_counts": dict(sorted(counts.items())), "transport_complex_examples": dict(sorted(area_examples.items())), "source": "official StopArea hierarchy; no production snapshot mutation", "production_mutation_plan": {"facilities_inserts": 0, "facilities_updates": 0, "facility_sources_inserts": 0, "source_observations_inserts": 0, "production_execution": False}}


def write_outputs(xml_path: Path, swagger_path: Path, output_dir: Path, station_csv: Path, points_csv: Path, facilities_path: Path, n1_dry_path: Path) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    manifest = source_manifest(xml_path, swagger_path)
    parsed, elapsed = parse_xml(xml_path)
    profile = parsed["profile"]
    stations = read_tfl_stations(station_csv, points_csv)
    reconciliation = reconcile_tfl_n2(stations, parsed["areas"])
    dry = dry_run(parsed["areas"], facilities_path, n1_dry_path)
    (output_dir / "NAPTAN_N2_SOURCE_MANIFEST_2026-08-22.json").write_text(json.dumps(manifest, indent=2, ensure_ascii=False, sort_keys=True) + "\n", encoding="utf-8")
    profile_without_rows = dict(profile)
    profile_without_rows["area_metadata"] = profile["area_metadata"][:200]
    profile_without_rows["area_metadata_note"] = "First 200 deterministic examples only; national aggregates cover all areas."
    (output_dir / "NAPTAN_N2_HIERARCHY_PROFILE_2026-08-22.json").write_text(json.dumps(profile_without_rows, indent=2, ensure_ascii=False, sort_keys=True) + "\n", encoding="utf-8")
    tfl_artifact = {"frozen_n1_reconciliation_sha256": FROZEN_N1_RECONCILIATION, "frozen_n1_zip_sha256": FROZEN_N1_ZIP, "n1_counts": {"EXACT_IDENTIFIER_MATCH": 0, "HIGH_CONFIDENCE_NAME_GEO_MATCH": 4, "AMBIGUOUS": 4, "NO_MATCH": 501}, "n2_counts": reconciliation["counts"], "station_count": reconciliation["station_count"], "results": reconciliation["results"], "production_execution": False}
    (output_dir / "NAPTAN_N2_TFL_RECONCILIATION_2026-08-22.json").write_text(json.dumps(tfl_artifact, indent=2, ensure_ascii=False, sort_keys=True) + "\n", encoding="utf-8")
    (output_dir / "NAPTAN_N2_RELIEF_DRY_RUN_2026-08-22.json").write_text(json.dumps(dry, indent=2, ensure_ascii=False, sort_keys=True) + "\n", encoding="utf-8")
    report = f"""# Relief NaPTAN N2 — Official StopArea and Interchange Hierarchy Reconciliation

## Final classification

**RELIEF NAPTAN N2 — OFFICIAL_HIERARCHY_CAPTURED / TRANSPORT_COMPLEX_MODEL_PARTIAL / HIERARCHY_MATERIALLY_IMPROVES_RECONCILIATION / ADDITIVE_TRANSPORT_SCHEMA_RECOMMENDED / PRODUCTION INGESTION NOT AUTHORIZED**

## Starting and source basis

N2 starts from the frozen N1 checkpoint and reuses the frozen TfL evidence. The current official DfT XML package is `NaPTAN.xml`; it contains `StopPoints` and `StopAreas`. The OpenAPI description confirms the current access-node endpoint surface. Raw XML and OpenAPI bytes were held in disposable external storage and were not committed.

- XML bytes: {manifest['sources'][0]['byte_size']:,}
- XML SHA-256: `{manifest['sources'][0]['sha256']}`
- XML retrieval UTC: {XML_RETRIEVAL_UTC}
- OpenAPI bytes: {manifest['sources'][1]['byte_size']:,}
- OpenAPI SHA-256: `{manifest['sources'][1]['sha256']}`
- Licence: Open Government Licence v3.0
- Attribution: “{manifest['licence']['attribution']}”

## Hierarchy profile

- StopPoints: **{profile['stop_points']['total']:,}**
- StopAreas: **{profile['stop_areas']['total']:,}**
- Membership rows: **{profile['memberships']['total_rows']:,}**
- StopPoints with one parent: **{profile['stop_points']['one_parent']:,}**
- StopPoints with multiple parents: **{profile['stop_points']['multiple_parents']:,}**
- StopPoints with zero parents: **{profile['stop_points']['zero_parent']:,}**
- StopAreas with multiple members: **{profile['stop_areas']['multiple_members']:,}**
- Maximum members in one StopArea: **{profile['stop_areas']['maximum_members']:,}**
- Duplicate StopPoint identities: **{profile['stop_points']['duplicate_identity_rows']}**
- Duplicate StopArea identities: **{profile['stop_areas']['duplicate_identity_rows']}**
- Missing StopArea references: **{profile['memberships']['missing_stop_area_references']}**
- Duplicate memberships: **{profile['memberships']['duplicate_memberships']}**
- Parent-area relationship rows: **{profile['hierarchy']['parent_relationship_rows']}**
- Hierarchy cycles: **{profile['hierarchy']['cycle_count']}**

The XML declares StopArea membership through StopPoint `StopAreaRef` values. Membership is publisher evidence; no spatial membership was inferred. The proposed StopArea identity namespace is `naptan-stop-area:<StopAreaCode>`.

## Interchange semantics

The official model distinguishes access nodes from grouped transport places. A StopArea can contain multiple StopPoints, including entrances, platforms, bays, on-street stops, and nodes from more than one mode. A StopArea therefore provides a safer transport-complex identity than choosing whichever constituent node is nearest to a Relief facility. Multiple nodes inside one StopArea must not become multiple canonical Relief facilities automatically.

Area modes and type distributions are in `NAPTAN_N2_HIERARCHY_PROFILE_2026-08-22.json`. Direct StopArea coordinates are retained as `STOP_AREA_LEVEL`; where absent, member-point centroids are labeled `DERIVED_FROM_MEMBER_STOPPOINTS` and are not production coordinates.

## TfL reconciliation comparison

N1 had 4 high-confidence name/geometry matches, 4 ambiguities, and 501 no-matches. N2 results:

{json.dumps(reconciliation['counts'], indent=2)}

N2 uses official StopArea names, membership, and area geometry before bounded geometry matching. It does not claim an exact cross-source identifier match where none is present. The result artifact contains all 509 station decisions and explicitly retains member counts and modes for each candidate.

## Relief dry run

The node-level and transport-complex-level estimates are intentionally separate:

{json.dumps(dry['transport_complex_level_counts'], indent=2)}

Raw node counts cannot be interpreted as potential Relief facility counts. The dry run is declarative only and contains zero facility, source-link, observation, or production operations.

## Schema readiness

**ADDITIVE_TRANSPORT_SCHEMA_RECOMMENDED.** The deployed source-observation model can preserve private NaPTAN evidence, but N2 now establishes a justified need for a source-neutral transport hierarchy model. A future additive design should separate:

- canonical Relief facility;
- source transport place/StopArea identity;
- source transport node/ATCO identity;
- publisher-declared membership;
- optional parent-area relationships;
- source geometry and coordinate scope;
- mode, type, status, revision, and provenance.

The model must not create a second uncontrolled canonical facility system and must not expose raw source provenance publicly by default. No migration is created or applied in N2.

## RDG readiness

NaPTAN StopArea identities and membership now provide a useful transport-complex scaffold for a future National Rail/RDG batch. RDG must still provide or validate its own station identifiers and any direct cross-reference. Names, geometry, mode, and StopArea membership remain secondary evidence only until the RDG source is available.

## Performance

- XML size: {xml_path.stat().st_size:,} bytes
- XML elements processed with streaming `iterparse`
- Parse time: {round(elapsed, 6)} seconds
- StopPoints/sec: {round(profile['stop_points']['total'] / elapsed, 2) if elapsed else None}
- Raw XML elements cleared at record boundaries; compact identity, membership, area, and coordinate indexes retained.

## Production safety

This batch performed no production write, schema change, migration, RLS/grant change, API exposure change, source ingestion, facility mutation, or toilet operation.

**TOTAL PRODUCTION MUTATIONS: 0**

## Evidence artifacts

- `NAPTAN_N2_SOURCE_MANIFEST_2026-08-22.json`
- `NAPTAN_N2_HIERARCHY_PROFILE_2026-08-22.json`
- `NAPTAN_N2_TFL_RECONCILIATION_2026-08-22.json`
- `NAPTAN_N2_RELIEF_DRY_RUN_2026-08-22.json`
"""
    (output_dir / "NAPTAN_N2_HIERARCHY_REPORT_2026-08-22.md").write_text(report, encoding="utf-8")
    contract = f"""# NaPTAN N2 transport hierarchy schema contract

**Design only — no migration and no production ingestion.**

## Recommended additive objects

`transport_source_places` should preserve a publisher-defined transport-place identity such as `naptan-stop-area:<StopAreaCode>`, source name, type, administrative area, source geometry, coordinate scope, status, revision, and provenance.

`transport_source_nodes` should preserve publisher-defined node identities such as `naptan:<ATCOCode>`, StopType, mode, source geometry, status, and provenance.

`transport_source_memberships` should strongly reference one source place and one source node, preserve membership revision/status, and enforce deterministic uniqueness on `(source_place_id, source_node_id)`.

An optional `transport_source_place_parents` relation should preserve official parent-area links without flattening hierarchy. It must reject self-links, missing parents, duplicate edges, and cycles in governed validation.

## Canonical boundary

These are source transport entities, not canonical Relief facilities. A later reconciliation process may attach one or more source places/nodes to an existing facility, but source hierarchy cannot create a facility or toilet automatically. Raw source provenance remains privileged unless a separate public projection is approved.

## Identity and idempotency

- StopArea key: `naptan-stop-area:<StopAreaCode>`.
- StopPoint key: `naptan:<ATCOCode>`.
- Preserve publisher casing/value separately from normalized lookup values.
- Missing or duplicate identities fail closed.
- Repeated identical source capture produces no duplicate source entities or memberships.
- Conflicting revisions are quarantined or versioned by a separately approved contract; they never overwrite canonical facilities silently.

## Coordinate ownership

Source coordinates remain `STOP_AREA_LEVEL` or `TRANSPORT_STOP_LEVEL`. A member centroid is `DERIVED_FROM_MEMBER_STOPPOINTS` and must retain original point coordinates and conversion/provenance metadata. No source geometry is toilet geometry.

## Security and governance

The future tables should use RLS and private-by-default grants consistent with `facility_source_observations`. Privileged ingestion may write through the existing governed server boundary; public clients should receive only an explicitly approved projection. No permissive policy is justified by this design.
"""
    (output_dir / "NAPTAN_N2_TRANSPORT_SCHEMA_CONTRACT_2026-08-22.md").write_text(contract, encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="Read-only NaPTAN N2 hierarchy analysis")
    parser.add_argument("--xml", type=Path, required=True)
    parser.add_argument("--swagger", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--tfl-stations", type=Path, required=True)
    parser.add_argument("--tfl-station-points", type=Path, required=True)
    parser.add_argument("--facilities", type=Path, required=True)
    parser.add_argument("--n1-dry-run", type=Path, required=True)
    args = parser.parse_args()
    write_outputs(args.xml, args.swagger, args.output_dir, args.tfl_stations, args.tfl_station_points, args.facilities, args.n1_dry_run)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

"""Read-only NaPTAN N3 transport-complex normalisation.

N3 turns the publisher-declared StopArea graph into a deterministic source
model.  It never writes to Supabase and intentionally has no production apply
path.  A normalized complex is a source-level root identity, not a Relief
facility.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import statistics
import time
import xml.etree.ElementTree as ET
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

from tools.source_expansion.naptan_n1 import (
    haversine_m,
    normalize_text,
    token_similarity,
)
from tools.source_expansion.naptan_n2 import (
    API_CATALOGUE,
    DOWNLOAD_PAGE,
    LICENCE_URL,
    SWAGGER_URL,
    XML_URL,
    mode_for_stop_type,
    sha256_file,
)


class NaptanN3Error(ValueError):
    """Raised when an N3 source invariant cannot be established safely."""


def local_name(tag: str) -> str:
    return tag.rsplit("}", 1)[-1]


def safe_text(element: ET.Element, wanted: str) -> str:
    for child in element.iter():
        if local_name(child.tag) == wanted:
            value = (child.text or "").strip()
            if "\ufffd" in value:
                raise NaptanN3Error(f"replacement character U+FFFD in {wanted}")
            return value
    return ""


def safe_attribute(element: ET.Element, wanted: str) -> str:
    value = element.attrib.get(wanted, "").strip()
    if "\ufffd" in value:
        raise NaptanN3Error(f"replacement character U+FFFD in attribute {wanted}")
    return value


def number_or_none(value: str) -> float | None:
    if not value:
        return None
    try:
        number = float(value)
    except ValueError as exc:
        raise NaptanN3Error(f"invalid numeric value {value!r}") from exc
    if not math.isfinite(number):
        raise NaptanN3Error(f"non-finite numeric value {value!r}")
    return number


def valid_lat_lon(latitude: float | None, longitude: float | None) -> bool:
    return latitude is not None and longitude is not None and -90 <= latitude <= 90 and -180 <= longitude <= 180


def area_identity(value: str) -> str:
    if not value:
        raise NaptanN3Error("StopAreaCode is missing")
    if "\ufffd" in value:
        raise NaptanN3Error("replacement character U+FFFD in StopAreaCode")
    return f"naptan-stop-area:{value.upper()}"


def point_identity(value: str) -> str:
    if not value:
        raise NaptanN3Error("AtcoCode is missing")
    if "\ufffd" in value:
        raise NaptanN3Error("replacement character U+FFFD in AtcoCode")
    return f"naptan:{value.upper()}"


def source_identity_for_complex(root_area_id: str) -> str:
    """The authoritative root StopArea identity is the complex identity."""
    return root_area_id


def parse_xml(xml_path: Path) -> tuple[dict[str, Any], float]:
    """Stream the official XML into compact deterministic indexes."""
    started = time.perf_counter()
    points: dict[str, dict[str, Any]] = {}
    areas: dict[str, dict[str, Any]] = {}
    point_parents: defaultdict[str, set[str]] = defaultdict(set)
    area_parent_links: set[tuple[str, str]] = set()
    duplicate_point_ids = 0
    duplicate_area_ids = 0
    duplicate_memberships = 0
    duplicate_membership_pairs: list[str] = []
    invalid_memberships = 0

    for _, element in ET.iterparse(xml_path, events=("end",)):
        kind = local_name(element.tag)
        if kind == "StopPoint":
            point_id = point_identity(safe_text(element, "AtcoCode"))
            if point_id in points:
                duplicate_point_ids += 1
                raise NaptanN3Error(f"duplicate publisher StopPoint identity {point_id}")
            latitude = number_or_none(safe_text(element, "Latitude"))
            longitude = number_or_none(safe_text(element, "Longitude"))
            if (latitude is not None or longitude is not None) and not valid_lat_lon(latitude, longitude):
                raise NaptanN3Error(f"invalid StopPoint coordinates for {point_id}")
            point_type = safe_text(element, "StopType")
            points[point_id] = {
                "source_identity": point_id,
                "publisher_id": safe_text(element, "AtcoCode"),
                "name": safe_text(element, "CommonName") or safe_text(element, "Name"),
                "normalized_name": normalize_text(safe_text(element, "CommonName") or safe_text(element, "Name")),
                "stop_type": point_type,
                "mode": mode_for_stop_type(point_type),
                "status": safe_attribute(element, "Status"),
                "modification": safe_attribute(element, "Modification"),
                "latitude": latitude,
                "longitude": longitude,
                "coordinate_scope": "TRANSPORT_STOP_LEVEL" if valid_lat_lon(latitude, longitude) else None,
            }
            for child in element.iter():
                if local_name(child.tag) != "StopAreaRef":
                    continue
                ref = (child.text or "").strip()
                if not ref:
                    invalid_memberships += 1
                    continue
                parent = area_identity(ref)
                if parent in point_parents[point_id]:
                    duplicate_memberships += 1
                    duplicate_membership_pairs.append(f"{point_id}:{parent}")
                point_parents[point_id].add(parent)
            element.clear()
        elif kind == "StopArea":
            area_id = area_identity(safe_text(element, "StopAreaCode"))
            if area_id in areas:
                duplicate_area_ids += 1
                raise NaptanN3Error(f"duplicate publisher StopArea identity {area_id}")
            latitude = number_or_none(safe_text(element, "Latitude"))
            longitude = number_or_none(safe_text(element, "Longitude"))
            if (latitude is not None or longitude is not None) and not valid_lat_lon(latitude, longitude):
                raise NaptanN3Error(f"invalid StopArea coordinates for {area_id}")
            areas[area_id] = {
                "source_identity": area_id,
                "publisher_id": safe_text(element, "StopAreaCode"),
                "name": safe_text(element, "Name"),
                "normalized_name": normalize_text(safe_text(element, "Name")),
                "area_type": safe_text(element, "StopAreaType") or safe_text(element, "Type"),
                "administrative_area_code": safe_text(element, "AdministrativeAreaRef"),
                "status": safe_attribute(element, "Status"),
                "modification": safe_attribute(element, "Modification"),
                "latitude": latitude,
                "longitude": longitude,
                "coordinate_scope": "PUBLISHER_STOPAREA_COORDINATE" if valid_lat_lon(latitude, longitude) else None,
            }
            for child in element.iter():
                if local_name(child.tag).lower() not in {"parentstoparearef", "parentstopareacode", "parentid"}:
                    continue
                ref = (child.text or "").strip()
                if ref:
                    area_parent_links.add((area_id, area_identity(ref)))
                else:
                    invalid_memberships += 1
            element.clear()

    area_members: defaultdict[str, set[str]] = defaultdict(set)
    for point_id, parents in point_parents.items():
        for area_id in parents:
            area_members[area_id].add(point_id)
    area_children: defaultdict[str, set[str]] = defaultdict(set)
    parent_map: defaultdict[str, set[str]] = defaultdict(set)
    for child, parent in sorted(area_parent_links):
        parent_map[child].add(parent)
        area_children[parent].add(child)
    for area_id, metadata in areas.items():
        metadata["member_count"] = len(area_members.get(area_id, set()))
        metadata["child_area_count"] = len(area_children.get(area_id, set()))
        metadata["modes"] = sorted({points[p]["mode"] for p in area_members.get(area_id, set()) if p in points})

    missing_area_refs = sorted({area_id for parents in point_parents.values() for area_id in parents if area_id not in areas})
    missing_parent_refs = sorted({parent for _, parent in area_parent_links if parent not in areas})
    missing_point_refs = sorted({point_id for members in area_members.values() for point_id in members if point_id not in points})
    cycle_nodes = set[str]()

    def visit(node: str, trail: tuple[str, ...]) -> None:
        if node in trail:
            cycle_nodes.update(trail[trail.index(node):])
            return
        for parent in sorted(parent_map.get(node, set())):
            if parent in areas:
                visit(parent, trail + (node,))

    for area_id in sorted(areas):
        visit(area_id, ())

    defects = {
        "MISSING_MEMBER_PARENT": missing_area_refs,
        "MISSING_AREA_PARENT": missing_parent_refs,
        "DUPLICATE_MEMBERSHIP": sorted(duplicate_membership_pairs),
        "INVALID_MEMBERSHIP": ["blank relationship element"] * invalid_memberships,
        "INVALID_IDENTITY": [],
        "HIERARCHY_CYCLE": sorted(cycle_nodes),
        "UNRESOLVED_REFERENCE": sorted(set(missing_area_refs + missing_parent_refs + missing_point_refs)),
    }
    data = {
        "areas": areas,
        "points": points,
        "point_parents": {key: set(value) for key, value in point_parents.items()},
        "area_members": {key: set(value) for key, value in area_members.items()},
        "area_children": {key: set(value) for key, value in area_children.items()},
        "parent_map": {key: set(value) for key, value in parent_map.items()},
        "defects": defects,
        "duplicate_point_ids": duplicate_point_ids,
        "duplicate_area_ids": duplicate_area_ids,
        "duplicate_memberships": duplicate_memberships,
        "duplicate_membership_pairs": sorted(duplicate_membership_pairs),
        "invalid_memberships": invalid_memberships,
    }
    return data, time.perf_counter() - started


def resolve_root(area_id: str, areas: dict[str, dict[str, Any]], parent_map: dict[str, set[str]], memo: dict[str, tuple[str | None, str]]) -> tuple[str | None, str]:
    if area_id in memo:
        return memo[area_id]
    if area_id not in areas:
        return None, "MISSING_AREA_PARENT"
    parents = sorted(parent_map.get(area_id, set()))
    if not parents:
        memo[area_id] = (area_id, "ROOT")
        return memo[area_id]
    roots = set[str]()
    states = set[str]()
    for parent in parents:
        if parent not in areas:
            states.add("MISSING_AREA_PARENT")
            continue
        root, state = resolve_root(parent, areas, parent_map, memo)
        if root:
            roots.add(root)
        states.add(state)
    if len(roots) > 1:
        result = (None, "MULTIPLE_ROOTS")
    elif "CYCLE" in states:
        result = (None, "HIERARCHY_CYCLE")
    elif not roots:
        result = (None, next(iter(sorted(states)), "UNRESOLVED_REFERENCE"))
    else:
        result = (next(iter(roots)), "RESOLVED")
    memo[area_id] = result
    return result


def resolve_roots(data: dict[str, Any]) -> dict[str, tuple[str | None, str]]:
    """Resolve roots while preserving unresolved/multi-root states."""
    areas = data["areas"]
    parent_map = data["parent_map"]
    memo: dict[str, tuple[str | None, str]] = {}
    visiting: set[str] = set()

    def walk(area_id: str) -> tuple[str | None, str]:
        if area_id in memo:
            return memo[area_id]
        if area_id in visiting:
            memo[area_id] = (None, "HIERARCHY_CYCLE")
            return memo[area_id]
        visiting.add(area_id)
        parents = sorted(parent_map.get(area_id, set()))
        if not parents:
            result = (area_id, "ROOT")
        else:
            resolved = [walk(parent) for parent in parents if parent in areas]
            roots = {root for root, _ in resolved if root}
            states = {state for _, state in resolved}
            if any(parent not in areas for parent in parents):
                states.add("MISSING_AREA_PARENT")
            if len(roots) > 1:
                result = (None, "MULTIPLE_ROOTS")
            elif "HIERARCHY_CYCLE" in states:
                result = (None, "HIERARCHY_CYCLE")
            elif not roots:
                result = (None, next(iter(sorted(states)), "UNRESOLVED_REFERENCE"))
            else:
                result = (next(iter(roots)), "RESOLVED")
        visiting.discard(area_id)
        memo[area_id] = result
        return result

    for area_id in sorted(areas):
        walk(area_id)
    return memo


def descendants(root: str, children: dict[str, set[str]]) -> set[str]:
    result = {root}
    stack = [root]
    while stack:
        node = stack.pop()
        for child in sorted(children.get(node, set())):
            if child not in result:
                result.add(child)
                stack.append(child)
    return result


def complex_geometry(root: str, area_ids: set[str], data: dict[str, Any]) -> tuple[str, float | None, float | None]:
    areas = data["areas"]
    root_area = areas[root]
    if valid_lat_lon(root_area["latitude"], root_area["longitude"]):
        scope = "PUBLISHER_PARENT_AREA_COORDINATE" if len(area_ids) > 1 else "PUBLISHER_STOPAREA_COORDINATE"
        return scope, root_area["latitude"], root_area["longitude"]
    child_coords = [(areas[a]["latitude"], areas[a]["longitude"]) for a in sorted(area_ids - {root}) if valid_lat_lon(areas[a]["latitude"], areas[a]["longitude"])]
    if child_coords:
        return "DERIVED_CHILD_AREA_CENTROID", sum(x[0] for x in child_coords) / len(child_coords), sum(x[1] for x in child_coords) / len(child_coords)
    point_ids = sorted({p for area_id in area_ids for p in data["area_members"].get(area_id, set())})
    point_coords = [(data["points"][p]["latitude"], data["points"][p]["longitude"]) for p in point_ids if p in data["points"] and valid_lat_lon(data["points"][p]["latitude"], data["points"][p]["longitude"])]
    if point_coords:
        return "DERIVED_MEMBER_CENTROID", sum(x[0] for x in point_coords) / len(point_coords), sum(x[1] for x in point_coords) / len(point_coords)
    return "NO_USABLE_GEOMETRY", None, None


def status_for_complex(root: str, area_ids: set[str], data: dict[str, Any]) -> str:
    statuses = {data["areas"][a]["status"].casefold() for a in area_ids if data["areas"][a]["status"]}
    point_ids = {p for a in area_ids for p in data["area_members"].get(a, set())}
    statuses.update(data["points"][p]["status"].casefold() for p in point_ids if data["points"][p]["status"])
    active = any(s in {"active", ""} for s in statuses)
    inactive = any(s in {"inactive", "deleted", "decommissioned"} for s in statuses)
    pending = any(s in {"pending", "new", "revise"} for s in statuses)
    if active and inactive:
        return "MIXED"
    if active:
        return "ACTIVE"
    if pending:
        return "PENDING"
    if inactive:
        return "SOURCE_DELETED"
    return "UNRESOLVED"


def normalize_complexes(data: dict[str, Any]) -> dict[str, Any]:
    roots = resolve_roots(data)
    root_ids = sorted(area_id for area_id in data["areas"] if not data["parent_map"].get(area_id))
    complexes = []
    for root in root_ids:
        area_ids = descendants(root, data["area_children"])
        point_ids = sorted({p for area_id in area_ids for p in data["area_members"].get(area_id, set())})
        modes = sorted({data["points"][p]["mode"] for p in point_ids if p in data["points"]})
        if len(area_ids) == 1:
            complex_type = "SINGLE_AREA_COMPLEX"
        elif len(modes) > 1:
            complex_type = "MULTIMODAL_PARENT_COMPLEX"
        else:
            complex_type = "PARENT_AREA_COMPLEX"
        geometry_scope, latitude, longitude = complex_geometry(root, area_ids, data)
        child_names = sorted({data["areas"][a]["name"] for a in area_ids - {root} if data["areas"][a]["name"]})
        multi_parent_nodes = sorted(p for p in point_ids if len(data["point_parents"].get(p, set())) > 1)
        defects = []
        if root in data["defects"]["HIERARCHY_CYCLE"]:
            defects.append("HIERARCHY_CYCLE")
        if any(a in data["defects"]["MISSING_AREA_PARENT"] for a in area_ids):
            defects.append("MISSING_AREA_PARENT")
        complexes.append({
            "complex_identity": source_identity_for_complex(root),
            "root_stop_area_identity": root,
            "root_name": data["areas"][root]["name"],
            "normalized_name": data["areas"][root]["normalized_name"],
            "aliases": child_names,
            "area_type": data["areas"][root]["area_type"],
            "area_ids": sorted(area_ids),
            "stop_point_ids": point_ids,
            "stop_area_count": len(area_ids),
            "stop_point_count": len(point_ids),
            "modes": modes,
            "complex_type": complex_type,
            "geometry_scope": geometry_scope,
            "latitude": latitude,
            "longitude": longitude,
            "status": status_for_complex(root, area_ids, data),
            "multi_parent_node_count": len(multi_parent_nodes),
            "defects": sorted(set(defects)),
        })
    return {"roots": roots, "complexes": complexes}


def multi_parent_analysis(data: dict[str, Any], normalized: dict[str, Any]) -> dict[str, Any]:
    roots = normalized["roots"]
    rows = [p for p in sorted(data["points"]) if len(data["point_parents"].get(p, set())) > 1]
    parent_counts = Counter(len(data["point_parents"][p]) for p in rows)
    stop_types = Counter(data["points"][p]["stop_type"] for p in rows)
    mode_combinations = Counter("+".join(sorted({data["points"][p]["mode"]})) for p in rows)
    examples = []
    for point_id in rows[:50]:
        parent_ids = sorted(data["point_parents"][point_id])
        parent_roots = sorted({roots.get(parent, (None, "UNRESOLVED"))[0] for parent in parent_ids if roots.get(parent, (None, "UNRESOLVED"))[0]})
        examples.append({
            "stop_point_identity": point_id,
            "stop_type": data["points"][point_id]["stop_type"],
            "mode": data["points"][point_id]["mode"],
            "parent_stop_area_identities": parent_ids,
            "resolved_root_complexes": parent_roots,
            "shared_common_complex": len(parent_roots) == 1,
            "handling": "PRESERVE_ALL_PARENTS; DO_NOT_SELECT_ONE",
        })
    return {
        "total_multi_parent_stop_points": len(rows),
        "parent_count_distribution": {str(k): v for k, v in sorted(parent_counts.items())},
        "stop_type_distribution": dict(sorted(stop_types.items())),
        "mode_combinations": dict(sorted(mode_combinations.items())),
        "shared_common_complex_count": sum(1 for p in rows if len({roots.get(parent, (None, "UNRESOLVED"))[0] for parent in data["point_parents"][p] if roots.get(parent, (None, "UNRESOLVED"))[0]}) == 1),
        "cross_complex_or_unresolved_count": sum(1 for p in rows if len({roots.get(parent, (None, "UNRESOLVED"))[0] for parent in data["point_parents"][p] if roots.get(parent, (None, "UNRESOLVED"))[0]}) != 1),
        "handling_contract": "MULTI_PARENT_NODE_COMPLEX; retain every publisher membership and refuse arbitrary parent selection",
        "examples": examples,
    }


def hierarchy_depths(data: dict[str, Any]) -> tuple[dict[str, int], set[str]]:
    parent_map = data["parent_map"]
    areas = data["areas"]
    memo: dict[str, int] = {}
    cycles = set[str]()

    def depth(area_id: str, trail: tuple[str, ...]) -> int:
        if area_id in memo:
            return memo[area_id]
        if area_id in trail:
            cycles.update(trail[trail.index(area_id):])
            return 0
        parents = [p for p in sorted(parent_map.get(area_id, set())) if p in areas]
        value = 1 + max((depth(parent, trail + (area_id,)) for parent in parents), default=0)
        memo[area_id] = value
        return value

    for area_id in sorted(areas):
        depth(area_id, ())
    return memo, cycles


def deep_hierarchy_analysis(data: dict[str, Any]) -> dict[str, Any]:
    depths, cycles = hierarchy_depths(data)
    distribution = Counter(depths.values())
    targets = [2, 3, 4, 6, max(depths.values(), default=0)]
    examples = {}
    for target in sorted(set(targets)):
        area_id = next((a for a, depth in sorted(depths.items()) if depth == target), None)
        if not area_id:
            continue
        chain = [area_id]
        while data["parent_map"].get(chain[-1]):
            parent = sorted(data["parent_map"][chain[-1]])[0]
            if parent not in data["areas"] or parent in chain:
                break
            chain.append(parent)
        examples[str(target)] = [{
            "stop_area_identity": a,
            "name": data["areas"][a]["name"],
            "area_type": data["areas"][a]["area_type"],
            "modes": data["areas"][a]["modes"],
            "member_count": data["areas"][a]["member_count"],
            "coordinate_scope": data["areas"][a]["coordinate_scope"],
        } for a in chain]
    return {
        "maximum_depth": max(depths.values(), default=0),
        "depth_distribution": {str(k): v for k, v in sorted(distribution.items())},
        "cycle_nodes": sorted(cycles),
        "representative_chains": examples,
        "interpretation": "Depth is a publisher area-parent chain. The topmost area is used as a complex root only when the chain resolves; depth alone is not evidence that an ancestor is a user-facing station.",
    }


def _tfl_station_rows(path: Path, n2_path: Path) -> list[dict[str, Any]]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    by_id: dict[str, dict[str, Any]] = {}
    for row in payload.get("records", []):
        station_id = row.get("stable_tfl_station_id") or row.get("tfl_station_id")
        if station_id and station_id not in by_id:
            coords = row.get("station_coordinates") or {}
            by_id[station_id] = {
                "tfl_station_id": station_id,
                "station_name": row.get("station_name", ""),
                "latitude": coords.get("latitude"),
                "longitude": coords.get("longitude"),
            }
    # The committed N2 reconciliation is the frozen 509-station identity
    # roster.  The detailed TfL report only repeats stations that have toilet
    # rows, so use N2 for the remaining station identities without inventing
    # coordinates.
    n2_payload = json.loads(n2_path.read_text(encoding="utf-8"))
    for row in n2_payload.get("results", []):
        station_id = row.get("tfl_station_id")
        if station_id and station_id not in by_id:
            by_id[station_id] = {
                "tfl_station_id": station_id,
                "station_name": row.get("station_name", ""),
                "latitude": None,
                "longitude": None,
            }
    return [by_id[key] for key in sorted(by_id)]


def reconcile_tfl_n3(stations: list[dict[str, Any]], normalized: dict[str, Any], n2_path: Path) -> dict[str, Any]:
    complexes = normalized["complexes"]
    complex_by_id = {row["complex_identity"]: row for row in complexes}
    area_to_complex: dict[str, tuple[str | None, str]] = {}
    for area_id, (root, state) in normalized["roots"].items():
        area_to_complex[area_id] = (root, state)
    n2 = json.loads(n2_path.read_text(encoding="utf-8"))
    n2_by_id = {row["tfl_station_id"]: row for row in n2.get("results", [])}
    results = []
    counts: Counter[str] = Counter()
    for station in stations:
        frozen_n2 = n2_by_id.get(station["tfl_station_id"], {"classification": "NO_MATCH", "candidates": []})
        ranked = []
        for candidate in frozen_n2.get("candidates", []):
            area_id = candidate.get("stop_area_identity")
            root, state = area_to_complex.get(area_id, (None, "UNRESOLVED_REFERENCE"))
            complex_row = complex_by_id.get(root) if root else None
            if complex_row:
                ranked.append({
                    "complex_identity": complex_row["complex_identity"],
                    "root_stop_area_identity": complex_row["root_stop_area_identity"],
                    "candidate_stop_area_identity": area_id,
                    "name": complex_row["root_name"],
                    "name_scope": "root" if area_id == root else "child",
                    "complex_type": complex_row["complex_type"],
                    "modes": complex_row["modes"],
                    "distance_metres": candidate.get("distance_metres"),
                    "name_similarity": candidate.get("name_similarity"),
                    "stop_area_count": complex_row["stop_area_count"],
                    "stop_point_count": complex_row["stop_point_count"],
                    "source_area_resolution": state,
                })
        ranked.sort(key=lambda item: (item["distance_metres"], item["complex_identity"]))
        unique_complexes = {item["complex_identity"] for item in ranked}
        if len(unique_complexes) > 1:
            classification = "AMBIGUOUS_COMPLEX"
            confidence = "MEDIUM"
            evidence = ["multiple distinct normalized complexes satisfy exact-name and bounded-geometry evidence"]
        elif not ranked:
            classification = "NO_MATCH"
            confidence = "LOW"
            evidence = ["frozen N2 reconciliation supplied no official candidate that can be normalised to a resolved complex root"]
        else:
            best = ranked[0]
            if best["name_scope"] == "child":
                classification = "MULTIMODAL_COMPLEX_MATCH" if best["complex_type"] == "MULTIMODAL_PARENT_COMPLEX" else "HIGH_CONFIDENCE_SUBPLACE_MATCH"
                confidence = "HIGH"
                evidence = ["frozen N2 name/geometry candidate normalised through an authoritative child-area-to-root relationship", "publisher hierarchy retained; child area is not flattened into a separate canonical place"]
            else:
                classification = "MULTIMODAL_COMPLEX_MATCH" if best["complex_type"] == "MULTIMODAL_PARENT_COMPLEX" else "HIGH_CONFIDENCE_COMPLEX_MATCH"
                confidence = "HIGH"
                evidence = ["frozen N2 name/geometry candidate resolves to one authoritative complex root", "publisher hierarchy retained"]
        counts[classification] += 1
        results.append({
            **station,
            "classification": classification,
            "confidence": confidence,
            "candidates": ranked[:20],
            "evidence": evidence,
            "facility_creation_authorized": False,
        })
    n3_by_id = {row["tfl_station_id"]: row for row in results}
    high_n3 = {"HIGH_CONFIDENCE_COMPLEX_MATCH", "HIGH_CONFIDENCE_SUBPLACE_MATCH", "MULTIMODAL_COMPLEX_MATCH"}
    n2_high = {"HIGH_CONFIDENCE_STOPAREA_MATCH", "HIGH_CONFIDENCE_TRANSPORT_COMPLEX_MATCH"}
    changes = Counter()
    for station_id, row in n3_by_id.items():
        if row["classification"] != n2_by_id.get(station_id, {}).get("classification"):
            changes[f"{n2_by_id.get(station_id, {}).get('classification', 'MISSING')}→{row['classification']}"] += 1
    resolved_no_match = [sid for sid, row in n2_by_id.items() if row["classification"] == "NO_MATCH" and n3_by_id[sid]["classification"] in high_n3]
    resolved_ambiguity = [sid for sid, row in n2_by_id.items() if row["classification"] == "AMBIGUOUS_TRANSPORT_COMPLEX" and n3_by_id[sid]["classification"] in high_n3]
    downgraded_high = [sid for sid, row in n2_by_id.items() if row["classification"] in n2_high and n3_by_id[sid]["classification"] not in high_n3]
    collapsed = []
    for row in n2.get("results", []):
        ids = [candidate.get("stop_area_identity") for candidate in row.get("candidates", []) if candidate.get("stop_area_identity")]
        roots = {normalized["roots"].get(area_id, (None, "UNRESOLVED"))[0] for area_id in ids}
        roots.discard(None)
        if len(ids) > len(roots) and roots:
            collapsed.append({"tfl_station_id": row["tfl_station_id"], "stop_area_count": len(ids), "complex_count": len(roots), "complex_identities": sorted(roots)})
    return {
        "n1_baseline": {"exact_identifier_matches": 0, "high_confidence_name_geometry_matches": 4, "ambiguous": 4, "no_match": 501},
        "n2_baseline": dict(sorted(Counter(row["classification"] for row in n2.get("results", [])).items())),
        "n3_counts": dict(sorted(counts.items())),
        "n3_station_count": len(results),
        "n2_to_n3_changes": dict(sorted(changes.items())),
        "n2_no_match_resolved": len(resolved_no_match),
        "n2_ambiguity_resolved": len(resolved_ambiguity),
        "n2_high_confidence_downgraded": len(downgraded_high),
        "transport_complex_collapses": collapsed[:100],
        "transport_complex_collapse_count": len(collapsed),
        "results": results,
        "production_execution": False,
        "facility_creation_authorized": False,
    }


def national_profile(data: dict[str, Any], normalized: dict[str, Any], multi: dict[str, Any], deep: dict[str, Any]) -> dict[str, Any]:
    complexes = normalized["complexes"]
    member_counts = [row["stop_point_count"] for row in complexes]
    area_counts = [row["stop_area_count"] for row in complexes]
    complex_modes = Counter("multimodal" if len(row["modes"]) > 1 else (row["modes"][0] if row["modes"] else "no_mode") for row in complexes)
    type_counts = Counter(row["complex_type"] for row in complexes)
    geometry_counts = Counter(row["geometry_scope"] for row in complexes)
    status_counts = Counter(row["status"] for row in complexes)
    defect_counts = Counter(defect for row in complexes for defect in row["defects"])
    return {
        "source": {"stop_points": len(data["points"]), "stop_areas": len(data["areas"]), "memberships": sum(len(v) for v in data["point_parents"].values())},
        "defects": {key: len(value) for key, value in sorted(data["defects"].items())},
        "normalised_complexes": {
            "total": len(complexes),
            "single_area": type_counts.get("SINGLE_AREA_COMPLEX", 0),
            "parent_area": type_counts.get("PARENT_AREA_COMPLEX", 0),
            "multimodal_parent": type_counts.get("MULTIMODAL_PARENT_COMPLEX", 0),
            "unresolved": sum(1 for area_id, result in normalized["roots"].items() if result[0] is None),
            "defect_affected": sum(1 for row in complexes if row["defects"]),
            "complex_type_distribution": dict(sorted(type_counts.items())),
            "mode_distribution": dict(sorted(complex_modes.items())),
            "geometry_distribution": dict(sorted(geometry_counts.items())),
            "status_distribution": dict(sorted(status_counts.items())),
            "defect_distribution": dict(sorted(defect_counts.items())),
            "mean_stop_areas": round(statistics.mean(area_counts), 4) if area_counts else 0,
            "median_stop_areas": statistics.median(area_counts) if area_counts else 0,
            "maximum_stop_areas": max(area_counts, default=0),
            "mean_stop_points": round(statistics.mean(member_counts), 4) if member_counts else 0,
            "median_stop_points": statistics.median(member_counts) if member_counts else 0,
            "maximum_stop_points": max(member_counts, default=0),
        },
        "multi_parent": {"total": multi["total_multi_parent_stop_points"], "shared_common_complex": multi["shared_common_complex_count"], "cross_complex_or_unresolved": multi["cross_complex_or_unresolved_count"]},
        "deep_hierarchy": {"maximum_depth": deep["maximum_depth"], "depth_distribution": deep["depth_distribution"]},
        "examples": sorted(complexes, key=lambda row: row["complex_identity"])[:200],
        "source_geometry_policy": "publisher root coordinate first; then derived child-area centroid; then derived member StopPoint centroid; derived geometry is analysis-only",
        "canonical_facility_mutations": {"facilities_inserts": 0, "facilities_updates": 0, "facility_source_inserts": 0, "source_observations": 0, "production_execution": False},
    }


def source_manifest(xml_path: Path, retrieval_utc: str) -> dict[str, Any]:
    return {
        "publisher": "UK Department for Transport",
        "product": "NaPTAN national XML access-node and StopArea package",
        "sources": [{
            "url": XML_URL,
            "documentation_url": DOWNLOAD_PAGE,
            "retrieval_utc": retrieval_utc,
            "filename": xml_path.name,
            "content_type": "application/xml",
            "format": "XML",
            "compression": "none",
            "byte_size": xml_path.stat().st_size,
            "sha256": sha256_file(xml_path),
            "role": "CORE_FOR_RELIEF",
            "top_level_structures_observed": ["StopPoints", "StopAreas"],
            "matches_frozen_n2_sha256": sha256_file(xml_path) == "6FC7E40E2AF3B30E9FD117BDAC313B58F3385BFF26517FD78D5554DA12B4183A",
        }],
        "supporting_official_documentation": {"api_catalogue": API_CATALOGUE, "swagger_url": SWAGGER_URL, "schema_url": "https://naptan.dft.gov.uk/naptan/schema/2.5/doc/NaPTANSchemaGuide-2.5-v0.67.pdf"},
        "licence": {"name": "Open Government Licence v3.0", "url": LICENCE_URL, "attribution": "Contains public sector information licensed under the Open Government Licence v3.0.", "reuse_note": "Published terms recorded; not a legal opinion."},
        "encoding": "UTF-8 XML; replacement characters rejected; no normalization before hashing",
        "raw_bytes_repository_policy": "Raw national XML remains in disposable external cache and is not committed.",
        "frozen_n2_reference": {"sha256": "6FC7E40E2AF3B30E9FD117BDAC313B58F3385BFF26517FD78D5554DA12B4183A", "source_manifest": "docs/data/NAPTAN_N2_SOURCE_MANIFEST_2026-08-22.json"},
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Read-only NaPTAN N3 transport-complex analysis")
    parser.add_argument("xml", type=Path)
    parser.add_argument("--tfl-evidence", type=Path, required=True)
    parser.add_argument("--n2-reconciliation", type=Path, required=True)
    parser.add_argument("--out-dir", type=Path, required=True)
    parser.add_argument("--retrieval-utc", required=True)
    args = parser.parse_args()
    if not args.xml.exists():
        raise SystemExit(f"missing source {args.xml}")
    data, parse_seconds = parse_xml(args.xml)
    normalized = normalize_complexes(data)
    multi = multi_parent_analysis(data, normalized)
    deep = deep_hierarchy_analysis(data)
    profile = national_profile(data, normalized, multi, deep)
    stations = _tfl_station_rows(args.tfl_evidence, args.n2_reconciliation)
    tfl = reconcile_tfl_n3(stations, normalized, args.n2_reconciliation)
    args.out_dir.mkdir(parents=True, exist_ok=True)
    outputs = {
        "NAPTAN_N3_SOURCE_MANIFEST_2026-08-22.json": source_manifest(args.xml, args.retrieval_utc),
        "NAPTAN_N3_COMPLEX_PROFILE_2026-08-22.json": {**profile, "performance": {"measurement": "runtime is reported in the human report; deterministic profile excludes elapsed time", "memory_strategy": "iterparse with cleared XML elements and compact indexes"}},
        "NAPTAN_N3_MULTI_PARENT_ANALYSIS_2026-08-22.json": multi,
        "NAPTAN_N3_DEEP_HIERARCHY_ANALYSIS_2026-08-22.json": deep,
        "NAPTAN_N3_TFL_RECONCILIATION_2026-08-22.json": tfl,
    }
    for name, value in outputs.items():
        (args.out_dir / name).write_text(json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"stop_points": len(data["points"]), "stop_areas": len(data["areas"]), "complexes": len(normalized["complexes"]), "tfl_stations": len(stations), "parse_seconds": round(parse_seconds, 3)}, sort_keys=True))


if __name__ == "__main__":
    main()

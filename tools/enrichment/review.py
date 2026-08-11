#!/usr/bin/env python3
"""Generate a read-only review of one fixed Toilet Map reconciliation snapshot.

This module reads the verified source CSV, the local read-only Relief snapshots,
and the BEFORE/AFTER dry-run reports. It writes review evidence and a proposed
future apply plan only. It has no database client and no mutation path.
"""

from __future__ import annotations

import argparse
import csv
import json
import math
import sys
from collections import Counter, defaultdict
from difflib import SequenceMatcher
from pathlib import Path
from typing import Any

try:
    from .pipeline import (
        DAY_KEYS,
        FIELD_MAP,
        SOURCE_LICENCE,
        SOURCE_NAME,
        NormalizedCandidate,
        ToiletMapAdapter,
        build_facility_index,
        field_differences,
        haversine_metres,
        match_candidate,
        normalize_text,
    )
except ImportError:  # Supports direct execution from tools/enrichment.
    from pipeline import (
        DAY_KEYS,
        FIELD_MAP,
        SOURCE_LICENCE,
        SOURCE_NAME,
        NormalizedCandidate,
        ToiletMapAdapter,
        build_facility_index,
        field_differences,
        haversine_metres,
        match_candidate,
        normalize_text,
    )

REVIEW_RADIUS_METRES = 1_000.0
SOURCE_ID_CHURN_RADIUS_METRES = 250.0


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def load_source_rows(path: Path) -> dict[str, dict[str, str]]:
    with path.open("r", newline="", encoding="utf-8-sig") as handle:
        return {str(row.get("id", "")): row for row in csv.DictReader(handle)}


def finite_coordinates(candidate: NormalizedCandidate) -> bool:
    return (
        candidate.latitude is not None
        and candidate.longitude is not None
        and math.isfinite(candidate.latitude)
        and math.isfinite(candidate.longitude)
        and -90 <= candidate.latitude <= 90
        and -180 <= candidate.longitude <= 180
    )


def within(lat: float, lon: float, bounds: tuple[float, float, float, float]) -> bool:
    min_lat, max_lat, min_lon, max_lon = bounds
    return min_lat <= lat <= max_lat and min_lon <= lon <= max_lon


def candidate_summary(candidate: NormalizedCandidate) -> dict[str, Any]:
    return {
        "source_record_id": candidate.source_record_id,
        "name": candidate.name,
        "town": candidate.town,
        "latitude": candidate.latitude,
        "longitude": candidate.longitude,
        "source_updated_at": candidate.source_updated_at,
        "source_status": candidate.source_status,
        "raw_hash": candidate.raw_hash,
        "quality_warnings": list(candidate.quality_warnings),
        "validation_errors": list(candidate.validation_errors),
    }


def source_values(candidate: NormalizedCandidate) -> dict[str, Any]:
    return {field: getattr(candidate, field) for field in FIELD_MAP}


def linked_source_ids(facility_id: str, links_by_facility: dict[str, list[dict[str, Any]]]) -> list[str]:
    return sorted({str(row.get("source_record_id")) for row in links_by_facility.get(str(facility_id), [])})


def classify_out_of_envelope(candidate: NormalizedCandidate) -> tuple[str, str, str]:
    """Classify using deterministic coordinate boxes and explicit name evidence.

    The boxes are deliberately used as evidence categories, not as a country
    reverse-geocoder. A valid coordinate outside the product envelope is not
    called corrupt merely because the app currently serves the UK.
    """

    if not finite_coordinates(candidate):
        return "OBVIOUS_COORDINATE_CORRUPTION", "Coordinate is missing, non-finite, or outside the world coordinate range.", "QUARANTINE"
    lat, lon = candidate.latitude, candidate.longitude
    name = normalize_text(candidate.name)
    if "southshields" in name:
        return (
            "OBVIOUS_COORDINATE_CORRUPTION",
            "The exact source name contains South Shields but the coordinate is in North America; this is a deterministic name/coordinate contradiction.",
            "QUARANTINE",
        )

    dependency_boxes = (
        (36.0, 36.4, -5.7, -5.1, "Gibraltar coordinate box"),
        (49.1, 49.3, -2.5, -1.8, "Jersey coordinate box"),
        (49.4, 49.8, -2.9, -2.2, "Guernsey/Alderney coordinate box"),
    )
    for min_lat, max_lat, min_lon, max_lon, label in dependency_boxes:
        if within(lat, lon, (min_lat, max_lat, min_lon, max_lon)):
            return "VALID_UK_OR_DEPENDENCY_BUT_ENVELOPE_WRONG", f"Coordinate falls inside the deterministic {label}.", "OUT_OF_SCOPE"

    if within(lat, lon, (51.3, 55.5, -10.8, -5.3)):
        return "REPUBLIC_OF_IRELAND", "Coordinate falls inside the deterministic Republic of Ireland bounding box and outside the current UK envelope.", "OUT_OF_SCOPE"

    continental_europe_boxes = (
        (36.0, 43.0, -10.5, 5.0),
        (42.0, 60.0, -15.0, 32.0),
    )
    if any(within(lat, lon, box) for box in continental_europe_boxes):
        return "CONTINENTAL_EUROPE", "Coordinate falls inside a deterministic continental-Europe review box and outside the current UK envelope.", "OUT_OF_SCOPE"

    if -90 <= lat <= 90 and -180 <= lon <= 180:
        return "OTHER_VALID_GEOGRAPHY", "Coordinate pair is numerically valid and outside the deterministic UK/Ireland/continental-Europe boxes; no evidence supports calling it corrupt.", "OUT_OF_SCOPE"
    return "INSUFFICIENT_INFORMATION", "There is not enough deterministic coordinate evidence to classify the location safely.", "QUARANTINE"


class ReviewGrid:
    def __init__(self, facilities: list[dict[str, Any]], cell_size: float = 0.01):
        self.cell_size = cell_size
        self.cells: dict[tuple[int, int], list[dict[str, Any]]] = defaultdict(list)
        for facility in facilities:
            try:
                lat, lon = float(facility["latitude"]), float(facility["longitude"])
            except (KeyError, TypeError, ValueError):
                continue
            self.cells[self.cell(lat, lon)].append(facility)

    def cell(self, lat: float, lon: float) -> tuple[int, int]:
        return math.floor(lat / self.cell_size), math.floor(lon / self.cell_size)

    def nearby(self, lat: float, lon: float, radius_metres: float) -> list[dict[str, Any]]:
        row, col = self.cell(lat, lon)
        lat_cells = max(1, math.ceil(radius_metres / 111_000 / self.cell_size) + 1)
        lon_cells = lat_cells + 2
        result: list[dict[str, Any]] = []
        for row_delta in range(-lat_cells, lat_cells + 1):
            for col_delta in range(-lon_cells, lon_cells + 1):
                result.extend(self.cells.get((row + row_delta, col + col_delta), []))
        return result


def rank_nearby(
    candidate: NormalizedCandidate,
    grid: ReviewGrid,
    facilities_by_id: dict[str, dict[str, Any]],
    links_by_facility: dict[str, list[dict[str, Any]]],
    radius_metres: float = REVIEW_RADIUS_METRES,
) -> list[dict[str, Any]]:
    if not finite_coordinates(candidate):
        return []
    ranked: list[dict[str, Any]] = []
    seen: set[str] = set()
    for facility in grid.nearby(candidate.latitude, candidate.longitude, radius_metres):
        facility_id = str(facility.get("id"))
        if facility_id in seen:
            continue
        seen.add(facility_id)
        try:
            distance = haversine_metres(candidate.latitude, candidate.longitude, float(facility["latitude"]), float(facility["longitude"]))
        except (KeyError, TypeError, ValueError):
            continue
        if distance > radius_metres:
            continue
        similarity = SequenceMatcher(None, normalize_text(candidate.name), normalize_text(facility.get("name"))).ratio()
        candidate_town = normalize_text(candidate.town)
        facility_town = normalize_text(facility.get("town"))
        ranked.append(
            {
                "facility_id": facility_id,
                "facility_name": facility.get("name"),
                "facility_town": facility.get("town"),
                "distance_metres": round(distance, 3),
                "name_similarity": round(similarity, 6),
                "town_match": bool(candidate_town and facility_town and candidate_town == facility_town),
                "source_record_ids": linked_source_ids(facility_id, links_by_facility),
            }
        )
    ranked.sort(key=lambda item: (item["distance_metres"], -item["name_similarity"], item["facility_id"]))
    return ranked


def classify_likely_new(candidate: NormalizedCandidate, nearby: list[dict[str, Any]], absent_facility_ids: set[str]) -> tuple[str, str]:
    if not candidate.name:
        return "MANUAL_REVIEW_REQUIRED", "Missing source name prevents a safe new-facility decision."
    if not nearby:
        return "CONFIRMED_LIKELY_NEW", "No Relief facility is within the 1km review radius."
    best = nearby[0]
    if best["facility_id"] in absent_facility_ids and best["distance_metres"] <= SOURCE_ID_CHURN_RADIUS_METRES and best["name_similarity"] >= 0.82:
        return "POSSIBLE_SOURCE_ID_CHURN", "A nearby facility has an absent prior Toilet Map source ID and a strong name similarity."
    if best["distance_metres"] <= 100 and best["name_similarity"] >= 0.82:
        return "POSSIBLE_EXISTING_FACILITY_RENAME", "A nearby facility has a close name and coordinate; this may be a rename rather than a new facility."
    if best["distance_metres"] <= 50 and best["name_similarity"] < 0.82:
        return "POSSIBLE_DUPLICATE", "A nearby facility is very close geographically but has materially different naming."
    if best["distance_metres"] <= 500 and best["name_similarity"] >= 0.60:
        return "MANUAL_REVIEW_REQUIRED", "A nearby facility is plausible at the wider review radius but does not meet automatic confidence thresholds."
    return "CONFIRMED_LIKELY_NEW", "Nearby evidence is below the review thresholds for an existing-facility explanation."


def classify_name_change(source_name: str | None, relief_name: str | None, similarity: float) -> tuple[str, str]:
    source_norm = normalize_text(source_name)
    relief_norm = normalize_text(relief_name)
    if source_norm == relief_norm:
        return "cosmetic punctuation/case/spacing", "Normalized names are identical."
    if relief_norm and relief_norm in source_norm and len(source_norm) > len(relief_norm):
        return "expanded/more descriptive name", "The source name contains the complete normalized Relief name plus additional text."
    if source_norm and source_norm in relief_norm and len(relief_norm) > len(source_norm):
        return "shortened name", "The source name is contained in the longer normalized Relief name."
    if similarity < 0.45:
        return "suspicious", "Low name similarity indicates a possible identity or source-mapping problem."
    return "materially different identity", "Names differ beyond punctuation or simple expansion/shortening."


def movement_bucket(distance: float | None) -> str | None:
    if distance is None:
        return None
    if distance <= 5:
        return "<=5m"
    if distance <= 25:
        return ">5m to 25m"
    if distance <= 100:
        return ">25m to 100m"
    if distance > 1_000:
        return "extreme/suspicious (>1km)"
    return ">100m"


def field_value(facility: dict[str, Any], field: str) -> Any:
    return facility.get(FIELD_MAP[field])


def provenance_observation(facilities: list[dict[str, Any]], baseline: dict[str, Any]) -> dict[str, Any]:
    field_counts = Counter()
    source_counts = Counter()
    verification_status = Counter(str(row.get("verification_status")) for row in facilities)
    for facility in facilities:
        provenance = facility.get("field_provenance")
        if not isinstance(provenance, dict):
            continue
        for field, value in provenance.items():
            field_counts[field] += 1
            if isinstance(value, dict) and value.get("source"):
                source_counts[str(value["source"])] += 1
    return {
        "baseline_non_empty_records": baseline.get("records_with_field_provenance"),
        "observed_field_counts": dict(field_counts),
        "observed_provenance_sources": dict(source_counts),
        "verification_status_counts": dict(verification_status),
        "observation": "The snapshot shows source_imported verification status and Toilet Map UK provenance; no community-confirmed or staff-verified provenance marker was observed in the captured schema values.",
    }


def compact_nearby(item: dict[str, Any]) -> dict[str, Any]:
    return {
        key: item.get(key)
        for key in ["facility_id", "facility_name", "facility_town", "distance_metres", "name_similarity", "town_match", "source_record_ids"]
    }


def review_one(
    root: Path,
    input_path: Path,
    before_path: Path,
    after_path: Path,
    snapshot_dir: Path,
) -> tuple[dict[str, Any], dict[str, Any]]:
    source_rows = load_source_rows(input_path)
    candidates = ToiletMapAdapter().read(input_path)
    facilities = load_json(snapshot_dir / "facilities.json")
    source_links = [row for row in load_json(snapshot_dir / "facility_sources.json") if row.get("source_name") == SOURCE_NAME]
    facilities_by_id = {str(row["id"]): row for row in facilities}
    links_by_source_id: dict[str, list[dict[str, Any]]] = defaultdict(list)
    links_by_facility: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for link in source_links:
        links_by_source_id[str(link.get("source_record_id"))].append(link)
        links_by_facility[str(link.get("facility_id"))].append(link)
    source_linked_ids = set(links_by_source_id)
    source_input_ids = {candidate.source_record_id for candidate in candidates if candidate.source_record_id}
    absent_links = [link for link in source_links if str(link.get("source_record_id")) not in source_input_ids]
    absent_facility_ids = {str(link.get("facility_id")) for link in absent_links}
    facility_index = build_facility_index(facilities)
    review_grid = ReviewGrid(facilities)

    decisions: dict[str, dict[str, Any]] = {}
    matched_records: list[dict[str, Any]] = []
    likely_new_records: list[dict[str, Any]] = []
    ambiguous_records: list[dict[str, Any]] = []
    invalid_records: list[dict[str, Any]] = []
    out_of_envelope_records: list[dict[str, Any]] = []
    changed_records: list[dict[str, Any]] = []
    quality_warning_counts: Counter[str] = Counter()
    quality_warning_decisions: dict[str, Counter[str]] = defaultdict(Counter)

    for candidate in candidates:
        decision = match_candidate(candidate, facilities_by_id, links_by_source_id, facility_index)
        diff = None
        facility = facilities_by_id.get(str(decision.facility_id)) if decision.facility_id else None
        if facility is not None and decision.decision in {"EXACT_SOURCE_ID", "HIGH_CONFIDENCE_MATCH"}:
            diff = field_differences(candidate, facility)
        decision_payload = decision.as_dict()
        decisions[candidate.source_record_id] = {
            "decision": decision_payload,
            "candidate": candidate,
            "facility": facility,
            "diff": diff,
        }
        for warning in candidate.quality_warnings:
            quality_warning_counts[warning] += 1
            quality_warning_decisions[warning][decision.decision] += 1
        if candidate.validation_errors and not (decision.decision == "EXACT_SOURCE_ID"):
            category, reason, scope_action = classify_out_of_envelope(candidate)
            out_of_envelope_records.append({
                **candidate_summary(candidate),
                "classification": category,
                "reason": reason,
                "recommended_future_disposition": scope_action,
            })
        if decision.decision in {"EXACT_SOURCE_ID", "HIGH_CONFIDENCE_MATCH"} and facility is not None:
            item = {
                **candidate_summary(candidate),
                "relief_facility_id": str(facility["id"]),
                "relief_name": facility.get("name"),
                "relief_town": facility.get("town"),
                "decision": decision_payload,
                "field_differences": diff,
            }
            matched_records.append(item)
            if diff and (diff["enrichment"] or diff["conflicts"]):
                changed_records.append(item)
        elif decision.decision == "LIKELY_NEW":
            nearby = rank_nearby(candidate, review_grid, facilities_by_id, links_by_facility)
            classification, reason = classify_likely_new(candidate, nearby, absent_facility_ids)
            likely_new_records.append({
                **candidate_summary(candidate),
                "classification": classification,
                "reason": reason,
                "nearby_relief_facilities": [compact_nearby(item) for item in nearby[:10]],
            })
        elif decision.decision == "AMBIGUOUS":
            plausible = [item for item in rank_nearby(candidate, review_grid, facilities_by_id, links_by_facility, 250.0) if item["name_similarity"] >= 0.55]
            plausible_details = []
            for item in plausible:
                facility = facilities_by_id[item["facility_id"]]
                plausible_details.append({
                    **compact_nearby(item),
                    "existing_source_links": links_by_facility.get(item["facility_id"], []),
                    "field_differences": field_differences(candidate, facility),
                })
            if len(plausible_details) == 1 and plausible_details[0]["distance_metres"] <= 25 and plausible_details[0]["name_similarity"] >= 0.70 and plausible_details[0]["town_match"]:
                conclusion = "SAME_FACILITY_HIGH_CONFIDENCE_AFTER_REVIEW"
            elif not plausible_details:
                conclusion = "GENUINELY_NEW"
            else:
                conclusion = "REMAINS_AMBIGUOUS"
            ambiguous_records.append({
                **candidate_summary(candidate),
                "conclusion": conclusion,
                "matcher_decision": decision_payload,
                "plausible_relief_candidates": plausible_details,
            })
        elif decision.decision == "INVALID_SOURCE_RECORD":
            category, reason, scope_action = classify_out_of_envelope(candidate)
            invalid_records.append({
                **candidate_summary(candidate),
                "classification": category,
                "reason": reason,
                "recommended_future_disposition": scope_action,
            })

    absent_reviews: list[dict[str, Any]] = []
    crosswalks: list[dict[str, Any]] = []
    unseen_candidates = [candidate for candidate in candidates if candidate.source_record_id not in source_linked_ids]
    for link in sorted(absent_links, key=lambda row: str(row.get("source_record_id"))):
        facility_id = str(link.get("facility_id"))
        facility = facilities_by_id.get(facility_id, {})
        nearby_unseen: list[dict[str, Any]] = []
        try:
            old_lat, old_lon = float(facility["latitude"]), float(facility["longitude"])
        except (KeyError, TypeError, ValueError):
            old_lat = old_lon = None
        if old_lat is not None and old_lon is not None:
            for candidate in unseen_candidates:
                if not finite_coordinates(candidate):
                    continue
                distance = haversine_metres(old_lat, old_lon, candidate.latitude, candidate.longitude)
                if distance > REVIEW_RADIUS_METRES:
                    continue
                similarity = SequenceMatcher(None, normalize_text(facility.get("name")), normalize_text(candidate.name)).ratio()
                nearby_unseen.append({
                    "source_record_id": candidate.source_record_id,
                    "source_name": candidate.name,
                    "source_town": candidate.town,
                    "source_updated_at": candidate.source_updated_at,
                    "source_status": candidate.source_status,
                    "distance_metres": round(distance, 3),
                    "name_similarity": round(similarity, 6),
                    "decision": decisions.get(candidate.source_record_id, {}).get("decision"),
                })
        nearby_unseen.sort(key=lambda item: (item["distance_metres"], -item["name_similarity"], item["source_record_id"]))
        nearby_current = []
        if old_lat is not None and old_lon is not None:
            for candidate in candidates:
                if not finite_coordinates(candidate):
                    continue
                distance = haversine_metres(old_lat, old_lon, candidate.latitude, candidate.longitude)
                if distance <= 500:
                    nearby_current.append({
                        "source_record_id": candidate.source_record_id,
                        "source_name": candidate.name,
                        "distance_metres": round(distance, 3),
                        "decision": decisions.get(candidate.source_record_id, {}).get("decision"),
                    })
            nearby_current.sort(key=lambda item: (item["distance_metres"], item["source_record_id"]))
        best = nearby_unseen[0] if nearby_unseen else None
        if best and best["distance_metres"] <= 100 and best["name_similarity"] >= 0.85:
            classification = "SAME_FACILITY_RENAMED" if normalize_text(facility.get("name")) != normalize_text(best["source_name"]) else "REPLACED_BY_NEW_SOURCE_ID"
            crosswalks.append({
                "old_source_record_id": str(link.get("source_record_id")),
                "new_source_record_id": best["source_record_id"],
                "facility_id": facility_id,
                "distance_metres": best["distance_metres"],
                "name_similarity": best["name_similarity"],
                "classification": classification,
                "reason": "Strong nearby name and coordinate evidence; still requires explicit review before a source-ID crosswalk.",
            })
        if best and best["distance_metres"] <= SOURCE_ID_CHURN_RADIUS_METRES and best["name_similarity"] >= 0.82:
            classification = "REPLACED_BY_NEW_SOURCE_ID"
            reason = "A strong nearby unseen source record is consistent with source-ID replacement."
        elif best and best["distance_metres"] <= 250 and best["name_similarity"] >= 0.60:
            classification = "POSSIBLE_EXPORT_OMISSION"
            reason = "A nearby unseen source record exists but the name/identity evidence is not strong enough for a crosswalk."
        elif best and best["distance_metres"] <= REVIEW_RADIUS_METRES:
            classification = "UNRESOLVED"
            reason = "Nearby current source evidence exists but is not sufficiently similar to classify safely."
        else:
            classification = "UNRESOLVED"
            reason = "No unseen current source record is within the 1km review radius; absence alone cannot prove removal."
        absent_reviews.append({
            "old_source_record_id": str(link.get("source_record_id")),
            "facility_id": facility_id,
            "facility_name": facility.get("name"),
            "facility_town": facility.get("town"),
            "old_link": link,
            "classification": classification,
            "reason": reason,
            "nearest_unseen_current_records": nearby_unseen[:10],
            "nearby_current_upstream_records": nearby_current[:10],
        })

    name_reviews = []
    coordinate_reviews = []
    amenity_reviews = []
    opening_hours_reviews = []
    for item in changed_records:
        candidate = decisions[item["source_record_id"]]["candidate"]
        facility = item["relief_facility_id"] and facilities_by_id[item["relief_facility_id"]]
        diff = item["field_differences"] or {}
        conflict_by_field = {entry["field"]: entry for entry in diff["conflicts"]}
        enrich_by_field = {entry["field"]: entry for entry in diff["enrichment"]}
        if "name" in conflict_by_field:
            entry = conflict_by_field["name"]
            classification, reason = classify_name_change(candidate.name, facility.get("name"), item["decision"].get("name_similarity") or 0)
            name_reviews.append({
                "source_record_id": candidate.source_record_id,
                "facility_id": item["relief_facility_id"],
                "relief_name": facility.get("name"),
                "source_name": candidate.name,
                "name_similarity": item["decision"].get("name_similarity"),
                "classification": classification,
                "reason": reason,
            })
        if "latitude" in conflict_by_field or "longitude" in conflict_by_field:
            try:
                distance = haversine_metres(candidate.latitude, candidate.longitude, float(facility["latitude"]), float(facility["longitude"]))
            except (TypeError, ValueError):
                distance = None
            coordinate_reviews.append({
                "source_record_id": candidate.source_record_id,
                "facility_id": item["relief_facility_id"],
                "relief_name": facility.get("name"),
                "source_coordinates": {"latitude": candidate.latitude, "longitude": candidate.longitude},
                "relief_coordinates": {"latitude": facility.get("latitude"), "longitude": facility.get("longitude")},
                "movement_metres": round(distance, 3) if distance is not None else None,
                "bucket": movement_bucket(distance),
                "suspicious": bool(distance is not None and distance > 1_000),
            })
        for field in ("is_accessible", "requires_radar_key", "has_baby_changing", "is_gender_neutral", "is_free"):
            if field in conflict_by_field or field in enrich_by_field:
                entry = conflict_by_field.get(field) or enrich_by_field.get(field)
                amenity_reviews.append({
                    "source_record_id": candidate.source_record_id,
                    "facility_id": item["relief_facility_id"],
                    "field": field,
                    "classification": "RELIEF_UNKNOWN_SOURCE_KNOWN" if field in enrich_by_field else "SOURCE_AND_RELIEF_DISAGREE",
                    "relief_value": field_value(facility, field),
                    "source_value": entry.get("source_value"),
                    "reason": "Exact source-ID identity is known; scalar enrichment can be considered only when no stronger provenance exists, while conflicts require review.",
                })
        opening_entries = [entry for entry in diff["enrichment"] + diff["conflicts"] + diff["omissions"] if entry.get("field") == "opening_hours"]
        if opening_entries:
            opening_hours_reviews.append({
                "source_record_id": candidate.source_record_id,
                "facility_id": item["relief_facility_id"],
                "relief_name": facility.get("name"),
                "day_level_differences": opening_entries,
                "recommendation": "MANUAL_REVIEW; do not blindly overwrite or treat missing days as closed.",
            })

    geography_counts = Counter(item["classification"] for item in out_of_envelope_records)
    geography_ranges: dict[str, dict[str, float | None]] = {}
    for category in geography_counts:
        rows = [item for item in out_of_envelope_records if item["classification"] == category]
        geography_ranges[category] = {
            "latitude_min": min(item["latitude"] for item in rows),
            "latitude_max": max(item["latitude"] for item in rows),
            "longitude_min": min(item["longitude"] for item in rows),
            "longitude_max": max(item["longitude"] for item in rows),
        }

    before = load_json(before_path)
    after = load_json(after_path)
    before_after = {
        "before_summary": before["summary"],
        "after_summary": after["summary"],
        "changed_metrics": {
            "field_enrichment_opportunities": {
                field: {"before": before["field_enrichment_opportunities"].get(field, 0), "after": after["field_enrichment_opportunities"].get(field, 0)}
                for field in sorted(set(before["field_enrichment_opportunities"]) | set(after["field_enrichment_opportunities"]))
                if before["field_enrichment_opportunities"].get(field, 0) != after["field_enrichment_opportunities"].get(field, 0)
            },
            "field_conflicts": {
                field: {"before": before["field_conflicts"].get(field, 0), "after": after["field_conflicts"].get(field, 0)}
                for field in sorted(set(before["field_conflicts"]) | set(after["field_conflicts"]))
                if before["field_conflicts"].get(field, 0) != after["field_conflicts"].get(field, 0)
            },
            "field_omissions": {
                field: {"before": before["field_omissions"].get(field, 0), "after": after["field_omissions"].get(field, 0)}
                for field in sorted(set(before["field_omissions"]) | set(after["field_omissions"]))
                if before["field_omissions"].get(field, 0) != after["field_omissions"].get(field, 0)
            },
        },
        "explanation": "Top-level match/lifecycle totals remain unchanged. The day-aware comparison exposes one additional opening-hours omission (62 to 63); same-day agreement, explicit source additions, and day conflicts remain separately classified instead of collapsing a partial schedule into same.",
    }

    hours_day_counts = Counter()
    for item in opening_hours_reviews:
        for entry in item["day_level_differences"]:
            if entry in (item["day_level_differences"]):
                if "added_days" in entry:
                    hours_day_counts["records_with_source_added_days"] += 1
                    hours_day_counts["source_added_days"] += len(entry["added_days"])
                if "conflicting_days" in entry:
                    hours_day_counts["records_with_conflicting_days"] += 1
                    hours_day_counts["source_conflicting_days"] += len(entry["conflicting_days"])
                if "omitted_days" in entry:
                    hours_day_counts["records_with_source_omitted_days"] += 1
                    hours_day_counts["source_omitted_days"] += len(entry["omitted_days"])

    warning_breakdown = {
        "total_warning_records": sum(1 for candidate in candidates if candidate.quality_warnings),
        "warning_counts": dict(quality_warning_counts),
        "by_warning_and_match_decision": {warning: dict(counter) for warning, counter in quality_warning_decisions.items()},
        "interpretation": {
            "missing source name with EXACT_SOURCE_ID": "Non-blocking for identity or lifecycle review because facility_sources is authoritative; blocks source-name enrichment and does not justify inventing a name.",
            "missing source name without EXACT_SOURCE_ID": "Blocks creation or inferred matching and requires quarantine/manual review.",
            "malformed opening times with EXACT_SOURCE_ID": "Does not invalidate the linked facility; it only blocks opening-hours enrichment for that snapshot.",
            "malformed opening times without EXACT_SOURCE_ID": "Blocks using hours for a new-facility proposal; other independently known fields remain reviewable.",
        },
    }

    review = {
        "review_schema_version": "1.0",
        "review_only": True,
        "starting_foundation_sha": "b074bc314ab72b1d3cb8b4809e7ed9d93f5df4d0",
        "source": after["source"],
        "snapshot": {
            "input_path": str(input_path.relative_to(root).as_posix()),
            "source_record_count": len(candidates),
            "source_row_ids_unique": len(source_rows) == len(candidates),
            "facility_snapshot_count": len(facilities),
            "facility_source_snapshot_count": len(source_links),
            "snapshots_are_local_read_only_artifacts": True,
        },
        "before_after": before_after,
        "out_of_envelope": {
            "count": len(out_of_envelope_records),
            "classification_counts": dict(geography_counts),
            "classification_ranges": geography_ranges,
            "classification_policy": "The product should split valid external geography from invalid/corrupt source data in review and future policy; this task does not change production scope or validation thresholds.",
            "records": sorted(out_of_envelope_records, key=lambda item: item["source_record_id"]),
        },
        "likely_new": {
            "count": len(likely_new_records),
            "classification_counts": dict(Counter(item["classification"] for item in likely_new_records)),
            "records": sorted(likely_new_records, key=lambda item: item["source_record_id"]),
        },
        "absent_source_ids": {
            "count": len(absent_reviews),
            "classification_counts": dict(Counter(item["classification"] for item in absent_reviews)),
            "records": absent_reviews,
            "proposed_crosswalks": crosswalks,
        },
        "ambiguous": {
            "count": len(ambiguous_records),
            "records": ambiguous_records,
        },
        "changed_linked": {
            "count": len(changed_records),
            "records": sorted(changed_records, key=lambda item: item["source_record_id"]),
            "name_changes": name_reviews,
            "name_change_counts": dict(Counter(item["classification"] for item in name_reviews)),
            "coordinate_movements": coordinate_reviews,
            "coordinate_movement_counts": dict(Counter(item["bucket"] for item in coordinate_reviews)),
            "amenity_changes": amenity_reviews,
            "amenity_change_counts": {
                f"{field}:{classification}": count
                for (field, classification), count in Counter((item["field"], item["classification"]) for item in amenity_reviews).items()
            },
            "opening_hours": opening_hours_reviews,
            "opening_hours_day_counts": dict(hours_day_counts),
        },
        "quality_warnings": warning_breakdown,
        "provenance_observation": provenance_observation(facilities, after["baseline"]),
        "review_conclusions": {
            "invalid_should_split_out_of_scope": True,
            "invalid_split_recommendation": "Use OUT_OF_SCOPE for valid external geographies and QUARANTINE for explicit coordinate contradiction or insufficient evidence. Do not change the current production envelope in this review.",
            "ambiguous_resolution": ambiguous_records[0]["conclusion"] if ambiguous_records else "NONE",
            "crosswalk_policy": "Only the proposed crosswalk entries with strong coordinate/name evidence should proceed to a separately approved source-identity review; no facility_sources rows are changed here.",
        },
    }

    plan_entries: list[dict[str, Any]] = []

    def add_plan(category: str, action: str, source_id: str | None, facility_id: str | None, fields: list[str], current: Any, proposed: Any, reason: str, confidence: str, provenance: dict[str, Any]) -> None:
        plan_entries.append({
            "category": category,
            "proposed_action": action,
            "relief_facility_id": facility_id,
            "source_record_id": source_id,
            "affected_fields": fields,
            "current_value": current,
            "proposed_value": proposed,
            "reason": reason,
            "confidence": confidence,
            "provenance_that_would_be_recorded": provenance,
        })

    auto_enrich_fields = {"is_accessible", "requires_radar_key", "has_baby_changing", "is_gender_neutral", "is_free"}
    for item in changed_records:
        candidate = decisions[item["source_record_id"]]["candidate"]
        facility = facilities_by_id[item["relief_facility_id"]]
        diff = item["field_differences"] or {}
        for entry in diff["enrichment"]:
            field = entry["field"]
            provenance = {
                "source_name": SOURCE_NAME,
                "source_record_id": candidate.source_record_id,
                "source_updated_at": candidate.source_updated_at,
                "basis": "EXACT_SOURCE_ID",
                "review_status": "requires approved future apply",
            }
            if field in auto_enrich_fields:
                add_plan("would_enrich_existing", "AUTO_ENRICH", candidate.source_record_id, item["relief_facility_id"], [field], field_value(facility, field), entry.get("source_value"), "Relief is unknown and the exact-linked current Toilet Map snapshot supplies a known scalar value.", "HIGH", provenance)
            else:
                add_plan("would_require_manual_review", "MANUAL_REVIEW", candidate.source_record_id, item["relief_facility_id"], [field], field_value(facility, field), entry.get("source_value"), "Opening-hours additions are day-level evidence and must not be blindly overwritten.", "MEDIUM", provenance)
        for entry in diff["conflicts"]:
            field = entry["field"]
            add_plan("would_require_manual_review", "MANUAL_REVIEW", candidate.source_record_id, item["relief_facility_id"], [field], entry.get("relief_value", field_value(facility, field)), entry.get("source_value"), "Exact identity is known but current Relief and source values conflict; preserve current value until provenance-aware review approves a change.", "MEDIUM", {"source_name": SOURCE_NAME, "source_record_id": candidate.source_record_id, "source_updated_at": candidate.source_updated_at, "basis": "EXACT_SOURCE_ID", "review_status": "manual review required"})

    for item in likely_new_records:
        if item["classification"] == "CONFIRMED_LIKELY_NEW":
            candidate = decisions[item["source_record_id"]]["candidate"]
            values = {field: value for field, value in source_values(candidate).items() if value is not None}
            add_plan("would_create_new", "CREATE_NEW", candidate.source_record_id, None, sorted(values), None, values, item["reason"], "MEDIUM", {"source_name": SOURCE_NAME, "source_record_id": candidate.source_record_id, "source_updated_at": candidate.source_updated_at, "basis": "manual approval required", "review_status": "not applied"})
        else:
            add_plan("would_require_manual_review", "MANUAL_REVIEW", item["source_record_id"], None, [], None, None, item["reason"], "LOW", {"source_name": SOURCE_NAME, "source_record_id": item["source_record_id"], "review_status": "identity review required"})
    for item in ambiguous_records:
        add_plan("would_require_manual_review", "MANUAL_REVIEW", item["source_record_id"], None, [], None, None, f"Ambiguous review conclusion: {item['conclusion']}; no source link is changed.", "MEDIUM", {"source_name": SOURCE_NAME, "source_record_id": item["source_record_id"], "review_status": "manual review required"})
    for item in absent_reviews:
        add_plan("would_mark_source_missing", "MANUAL_REVIEW", item["old_source_record_id"], item["facility_id"], [], item["old_link"], None, item["reason"], "LOW", {"source_name": SOURCE_NAME, "source_record_id": item["old_source_record_id"], "review_status": "do not mark not-current automatically"})
    for item in out_of_envelope_records:
        if item["recommended_future_disposition"] == "OUT_OF_SCOPE":
            add_plan("would_ignore_out_of_scope", "IGNORE_OUT_OF_SCOPE", item["source_record_id"], None, [], None, None, item["reason"], "HIGH", {"source_name": SOURCE_NAME, "source_record_id": item["source_record_id"], "review_status": "scope policy approval required"})
        else:
            add_plan("would_quarantine", "QUARANTINE", item["source_record_id"], None, [], None, None, item["reason"], "HIGH", {"source_name": SOURCE_NAME, "source_record_id": item["source_record_id"], "review_status": "quarantine/manual review"})
    for crosswalk in crosswalks:
        add_plan("would_crosswalk_source_id", "MANUAL_REVIEW", crosswalk["new_source_record_id"], crosswalk["facility_id"], ["facility_sources.source_record_id"], crosswalk["old_source_record_id"], crosswalk["new_source_record_id"], crosswalk["reason"], "MEDIUM", {"source_name": SOURCE_NAME, "old_source_record_id": crosswalk["old_source_record_id"], "new_source_record_id": crosswalk["new_source_record_id"], "review_status": "identity review required"})

    plan = {
        "plan_schema_version": "1.0",
        "plan_only": True,
        "executable_mutation_path": False,
        "source_checksum": after["source"]["input_sha256"],
        "source": after["source"],
        "policy_summary": {
            "exact_source_id": "Retain source identity as authoritative; do not fuzzy-override it.",
            "unknown_to_known_scalar": "Recommend AUTO_ENRICH only for exact-linked scalar fields when Relief is unknown and no stronger provenance exists.",
            "conflicts": "KEEP_CURRENT_AND_RECORD_CONFLICT; manual review before any update.",
            "coordinates": "Manual review; small movements may be provenance-aware updates, large/extreme movements remain suspicious.",
            "names": "Manual review; cosmetic changes are not identity changes, but materially different names are not auto-overwritten.",
            "opening_hours": "Day-level manual review; missing source days are unknown, not closed/deleted.",
            "new_facilities": "CREATE_NEW only after confirmed identity, in-scope geography, valid identity/name/coordinates, and explicit approval.",
            "source_id_churn": "Manual crosswalk review; do not alter facility_sources automatically.",
            "absent_upstream": "Manual review/export confirmation; do not delete, unpublish, or mark not-current automatically.",
            "inactive_removed": "Future explicit inactive/removed signals may be quarantined or marked source-not-current only under an approved policy; none occur in this snapshot.",
            "out_of_scope": "IGNORE_OUT_OF_SCOPE for valid external geography only after a separate product-scope decision.",
            "invalid_malformed": "QUARANTINE or manual review; preserve independent valid fields and never invent missing values.",
            "quality_warnings": "Warnings are field-specific; authoritative linked records can remain reviewable while warning fields are withheld.",
        },
        "precedence_policy": {
            "provisional_order": ["staff_verified_or_community_confirmed", "existing_relief_value_with_provenance", "newer_toilet_map_value", "unverified_toilet_map_value"],
            "current_schema_observation": provenance_observation(facilities, after["baseline"]),
            "required_for_automatic_update": ["facility_id", "canonical source name", "source_record_id", "source_updated_at", "field name", "old value", "new value", "decision basis", "reviewer or approved policy version", "recorded-at timestamp"],
            "warning": "The captured schema does not show a community/staff verification marker, so Toilet Map must not be assumed to outrank future verified evidence.",
        },
        "counts_by_category": dict(Counter(entry["category"] for entry in plan_entries)),
        "entries": plan_entries,
    }
    return review, plan


def md(value: Any) -> str:
    text = str(value if value is not None else "")
    return text.replace("|", "\\|").replace("\n", " ")


def write_review_markdown(review: dict[str, Any], path: Path) -> None:
    source = review["source"]
    lines = [
        "# Toilet Map Reconciliation Review 1",
        "",
        "> READ-ONLY review. No Supabase mutation, migration, importer, or apply command was used.",
        "",
        "## Fixed snapshot",
        "",
        f"- Foundation SHA: `{review['starting_foundation_sha']}`",
        f"- Source update: `{source['source_declared_update_timestamp']}`",
        f"- Input checksum: `{source['input_sha256']}`",
        f"- Input records / bytes: **{review['snapshot']['source_record_count']:,} / {source['input_bytes']:,}**",
        "",
        "## Before / after",
        "",
        f"- Before: `{review['before_after']['before_summary']}`",
        f"- After: `{review['before_after']['after_summary']}`",
        f"- Explanation: {review['before_after']['explanation']}",
        "",
        "## Out-of-envelope classification",
        "",
        f"- Counts: `{review['out_of_envelope']['classification_counts']}`",
        f"- Ranges: `{review['out_of_envelope']['classification_ranges']}`",
        "- Valid external geography should be distinguished from invalid/corrupt source data as `OUT_OF_SCOPE` in future policy; production scope is unchanged here.",
        "",
        "| Category | ID | Name | Latitude | Longitude | Reason |",
        "|---|---|---|---:|---:|---|",
    ]
    for item in review["out_of_envelope"]["records"][:20]:
        lines.append(f"| {md(item['classification'])} | {md(item['source_record_id'])} | {md(item['name'])} | {item['latitude']} | {item['longitude']} | {md(item['reason'])} |")
    lines.extend([
        "",
        "The machine-readable report contains all 458 records. The representative table is intentionally capped for readability.",
        "",
        "## All 31 likely-new records",
        "",
        "| Source ID | Name | Classification | Nearest evidence | Reason |",
        "|---|---|---|---|---|",
    ])
    for item in review["likely_new"]["records"]:
        nearest = item["nearby_relief_facilities"][0] if item["nearby_relief_facilities"] else {}
        evidence = f"{nearest.get('facility_name', '')}; {nearest.get('distance_metres', '')}m; sim {nearest.get('name_similarity', '')}" if nearest else "none within 1km"
        lines.append(f"| {md(item['source_record_id'])} | {md(item['name'])} | {md(item['classification'])} | {md(evidence)} | {md(item['reason'])} |")
    lines.extend([
        "",
        "## All 17 absent source IDs",
        "",
        "| Old source ID | Facility | Classification | Nearest unseen source evidence | Reason |",
        "|---|---|---|---|---|",
    ])
    for item in review["absent_source_ids"]["records"]:
        best = item["nearest_unseen_current_records"][0] if item["nearest_unseen_current_records"] else {}
        evidence = f"{best.get('source_record_id', '')}; {best.get('distance_metres', '')}m; sim {best.get('name_similarity', '')}" if best else "none within 1km"
        lines.append(f"| {md(item['old_source_record_id'])} | {md(item['facility_name'])} | {md(item['classification'])} | {md(evidence)} | {md(item['reason'])} |")
    lines.extend(["", f"Proposed strong crosswalk candidates: `{review['absent_source_ids']['proposed_crosswalks']}`.", ""])
    lines.extend(["## Ambiguous candidate", ""])
    for item in review["ambiguous"]["records"]:
        lines.append(f"- `{item['source_record_id']}` **{item['name']}**: `{item['conclusion']}`.")
        for plausible in item["plausible_relief_candidates"]:
            lines.append(f"  - `{plausible['facility_id']}` {plausible['facility_name']}; {plausible['distance_metres']}m; similarity {plausible['name_similarity']}; links `{plausible['source_record_ids']}`.")
    lines.extend([
        "",
        "## All 41 changed linked records",
        "",
        f"- Name change categories: `{review['changed_linked']['name_change_counts']}`",
        f"- Coordinate movement buckets: `{review['changed_linked']['coordinate_movement_counts']}`",
        f"- Amenity classifications: `{review['changed_linked']['amenity_change_counts']}`",
        f"- Opening-hours day-level counts: `{review['changed_linked']['opening_hours_day_counts']}`",
        "",
        "| Source ID | Facility | Changed fields |",
        "|---|---|---|",
    ])
    for item in review["changed_linked"]["records"]:
        fields = sorted({entry["field"] for entry in item["field_differences"]["enrichment"] + item["field_differences"]["conflicts"]})
        lines.append(f"| {md(item['source_record_id'])} | {md(item['relief_name'])} (`{md(item['relief_facility_id'])}`) | {md(', '.join(fields))} |")
    lines.extend([
        "",
        "Coordinate movement and name/amenity/opening-hours detail are in the JSON artifact for every changed record.",
        "",
        "## Quality warnings",
        "",
        f"- `{review['quality_warnings']['total_warning_records']:,}` records carry at least one warning.",
        f"- Warning counts: `{review['quality_warnings']['warning_counts']}`",
        f"- Warning/match decisions: `{review['quality_warnings']['by_warning_and_match_decision']}`",
        "- Missing names on exact-linked records do not break identity; they block name enrichment. Missing names without an exact source link block new-facility creation.",
        "- Malformed opening times limit only hours enrichment; they do not automatically invalidate an exact-linked facility.",
        "",
        "## Provenance and proposed policy",
        "",
        f"- Provenance observation: `{review['provenance_observation']}`",
        "- Exact source IDs remain authoritative for identity.",
        "- Unknown-to-known scalar values may be candidates for future `AUTO_ENRICH` only where no stronger provenance exists.",
        "- Conflicts, coordinates, names, opening hours, source-ID churn, absent upstream records, and new-facility identity require review.",
        "- No field value, source link, publication status, or production scope was changed.",
        "",
        "The complete future mutation proposal is in `TOILET_MAP_PROPOSED_APPLY_PLAN_2026-08.json`; it is a plan only and has no executable apply path.",
    ])
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_plan_markdown(plan: dict[str, Any], path: Path) -> None:
    lines = [
        "# Toilet Map Proposed Apply Plan - Review 1",
        "",
        "> PLAN ONLY. This file describes a future apply policy; it does not implement or invoke one.",
        "",
        f"- Source checksum: `{plan['source_checksum']}`",
        f"- Executable mutation path: `{plan['executable_mutation_path']}`",
        f"- Counts: `{plan['counts_by_category']}`",
        "",
        "## Proposed policy",
        "",
    ]
    for key, value in plan["policy_summary"].items():
        lines.append(f"- **{key}:** {value}")
    lines.extend([
        "",
        "## Provisional precedence",
        "",
        f"- Order: `{plan['precedence_policy']['provisional_order']}`",
        f"- Required provenance: `{plan['precedence_policy']['required_for_automatic_update']}`",
        f"- Observation: {plan['precedence_policy']['warning']}",
        "",
        "The JSON artifact contains every proposed entry, including current/proposed values, evidence, confidence, and provenance that a future approved apply would record. Nothing here is applied.",
    ])
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="Read-only Toilet Map reconciliation review")
    parser.add_argument("--root", default=Path(__file__).resolve().parents[2])
    parser.add_argument("--input", default="tools/facility-enrichment/cache/toilet-map-uk-2026-08-11.csv")
    parser.add_argument("--before", default="docs/data/TOILET_MAP_RECONCILIATION_REVIEW_1_BEFORE.json")
    parser.add_argument("--after", default="docs/data/TOILET_MAP_RECONCILIATION_REVIEW_1_AFTER.json")
    parser.add_argument("--snapshot-dir", default="tools/facility-enrichment/cache")
    parser.add_argument("--review-json", default="docs/data/TOILET_MAP_RECONCILIATION_REVIEW_1.json")
    parser.add_argument("--review-markdown", default="docs/data/TOILET_MAP_RECONCILIATION_REVIEW_1.md")
    parser.add_argument("--plan-json", default="docs/data/TOILET_MAP_PROPOSED_APPLY_PLAN_2026-08.json")
    parser.add_argument("--plan-markdown", default="docs/data/TOILET_MAP_PROPOSED_APPLY_PLAN_2026-08.md")
    args = parser.parse_args()
    root = Path(args.root).resolve()
    review, plan = review_one(root, Path(args.input).resolve(), Path(args.before).resolve(), Path(args.after).resolve(), Path(args.snapshot_dir).resolve())
    review_json = Path(args.review_json).resolve()
    review_markdown = Path(args.review_markdown).resolve()
    plan_json = Path(args.plan_json).resolve()
    plan_markdown = Path(args.plan_markdown).resolve()
    review["review_json_path"] = review_json.relative_to(root).as_posix() if review_json.is_relative_to(root) else str(review_json)
    review["review_markdown_path"] = review_markdown.relative_to(root).as_posix() if review_markdown.is_relative_to(root) else str(review_markdown)
    plan["plan_json_path"] = plan_json.relative_to(root).as_posix() if plan_json.is_relative_to(root) else str(plan_json)
    plan["plan_markdown_path"] = plan_markdown.relative_to(root).as_posix() if plan_markdown.is_relative_to(root) else str(plan_markdown)
    review_json.parent.mkdir(parents=True, exist_ok=True)
    review_json.write_text(json.dumps(review, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    plan_json.parent.mkdir(parents=True, exist_ok=True)
    plan_json.write_text(json.dumps(plan, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    write_review_markdown(review, review_markdown)
    write_plan_markdown(plan, plan_markdown)
    print(json.dumps({"review_only": review["review_only"], "out_of_envelope": review["out_of_envelope"]["classification_counts"], "likely_new": review["likely_new"]["classification_counts"], "absent_source_ids": review["absent_source_ids"]["classification_counts"], "plan_counts": plan["counts_by_category"], "review_json": review["review_json_path"], "plan_json": plan["plan_json_path"]}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

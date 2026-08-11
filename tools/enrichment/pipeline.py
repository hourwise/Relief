"""Generic source-adapter, matching, and reconciliation primitives.

This module deliberately has no database client and no write path. The dry-run
CLI supplies read-only Relief snapshots and a source adapter supplies
``NormalizedCandidate`` records. A future source can implement the same
adapter boundary without changing the matcher or reconciliation logic.
"""

from __future__ import annotations

import csv
import hashlib
import json
import math
import re
import unicodedata
from collections import Counter, defaultdict
from dataclasses import asdict, dataclass, field
from difflib import SequenceMatcher
from pathlib import Path
from typing import Any, Iterable, Protocol

SOURCE_NAME = "Toilet Map UK"
SOURCE_LICENCE = "CC BY 4.0"
DAY_KEYS = ("monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday")
MATCH_RADIUS_METRES = 250.0

FIELD_MAP = {
    "name": "name",
    "address": "address",
    "town": "town",
    "postcode": "postcode",
    "latitude": "latitude",
    "longitude": "longitude",
    "opening_hours": "open_hours",
    "is_free": "is_free",
    "is_accessible": "is_accessible",
    "requires_radar_key": "requires_radar_key",
    "has_baby_changing": "has_baby_changing",
    "is_gender_neutral": "is_gender_neutral",
    "is_family_friendly": "is_family_friendly",
    "has_staff_nearby": "has_staff_nearby",
}


def parse_bool(value: Any) -> bool | None:
    if value is None or str(value).strip() == "":
        return None
    value = str(value).strip().lower()
    if value in {"true", "1", "yes", "y"}:
        return True
    if value in {"false", "0", "no", "n"}:
        return False
    return None


def normalize_text(value: Any) -> str:
    if value is None:
        return ""
    text = unicodedata.normalize("NFKD", str(value)).encode("ascii", "ignore").decode("ascii")
    return re.sub(r"[^a-z0-9]+", "", text.lower())


def display_text(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def parse_areas(value: str | None) -> str | None:
    if not value or not value.strip():
        return None
    try:
        parsed = json.loads(value)
    except (TypeError, json.JSONDecodeError):
        return None
    if isinstance(parsed, dict):
        return display_text(parsed.get("name"))
    if isinstance(parsed, list):
        for entry in parsed:
            if isinstance(entry, dict) and display_text(entry.get("name")):
                return display_text(entry.get("name"))
    return None


def parse_opening_hours(value: str | None) -> dict[str, dict[str, str]] | None:
    """Keep only explicit source time pairs; empty/malformed values stay unknown."""
    if not value or not value.strip():
        return None
    try:
        parsed = json.loads(value)
    except (TypeError, json.JSONDecodeError):
        return None
    if not isinstance(parsed, list) or len(parsed) != 7:
        return None
    result: dict[str, dict[str, str]] = {}
    for day, entry in zip(DAY_KEYS, parsed):
        if not isinstance(entry, list) or len(entry) < 2:
            continue
        opening = display_text(entry[0])
        closing = display_text(entry[1])
        if opening and closing:
            result[day] = {"open": opening, "close": closing}
    return result or None


def canonical_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def known_value(value: Any) -> bool:
    return value is not None and value != "" and value != {} and value != []


def values_equal(left: Any, right: Any, field_name: str) -> bool:
    if field_name in {"latitude", "longitude"}:
        try:
            return abs(float(left) - float(right)) <= 0.00001
        except (TypeError, ValueError):
            return False
    if field_name == "opening_hours":
        return canonical_json(left) == canonical_json(right)
    return left == right


def haversine_metres(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    radius = 6_371_000.0
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    d_phi = math.radians(lat2 - lat1)
    d_lambda = math.radians(lon2 - lon1)
    a = math.sin(d_phi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(d_lambda / 2) ** 2
    return radius * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


@dataclass
class NormalizedCandidate:
    source_name: str
    source_record_id: str
    source_url: str | None
    source_licence: str
    source_updated_at: str | None
    name: str | None
    address: str | None
    town: str | None
    postcode: str | None
    latitude: float | None
    longitude: float | None
    opening_hours: dict[str, Any] | None
    is_free: bool | None
    is_accessible: bool | None
    requires_radar_key: bool | None
    has_baby_changing: bool | None
    is_gender_neutral: bool | None
    is_family_friendly: bool | None
    has_staff_nearby: bool | None
    other_fields: dict[str, Any]
    raw_hash: str
    source_status: str
    validation_errors: list[str] = field(default_factory=list)
    quality_warnings: list[str] = field(default_factory=list)

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


class SourceAdapter(Protocol):
    source_name: str

    def read(self, input_path: Path) -> list[NormalizedCandidate]:
        ...


class ToiletMapAdapter:
    """First adapter: official Toilet Map UK CSV -> source-neutral candidates."""

    source_name = SOURCE_NAME

    def read(self, input_path: Path) -> list[NormalizedCandidate]:
        with input_path.open("r", newline="", encoding="utf-8-sig") as handle:
            rows = list(csv.DictReader(handle))
        id_counts = Counter(display_text(row.get("id")) for row in rows)
        candidates: list[NormalizedCandidate] = []
        for row in rows:
            source_id = display_text(row.get("id")) or ""
            raw_hash = hashlib.sha256(canonical_json(row).encode("utf-8")).hexdigest()
            active = parse_bool(row.get("active"))
            status = "active" if active is True else "removed" if active is False else "unknown"
            name = display_text(row.get("name"))
            town = parse_areas(row.get("areas"))
            try:
                latitude = float(row["latitude"])
                longitude = float(row["longitude"])
            except (KeyError, TypeError, ValueError):
                latitude = longitude = None

            errors: list[str] = []
            warnings: list[str] = []
            if not source_id:
                errors.append("missing source record ID")
            if id_counts.get(source_id, 0) > 1 and source_id:
                errors.append("duplicate source record ID in input snapshot")
            if latitude is None or longitude is None:
                errors.append("invalid latitude/longitude")
            elif not (49.0 <= latitude <= 61.0 and -9.0 <= longitude <= 2.0):
                errors.append("coordinates outside the UK validation envelope")
            if not name:
                warnings.append("missing source name")
            if active is None:
                warnings.append("active status is unknown")
            if row.get("opening_times", "").strip() and parse_opening_hours(row.get("opening_times")) is None:
                warnings.append("opening_times present but not a usable seven-day time array")

            other_fields = {
                key: parse_bool(row.get(key))
                for key in ("attended", "automatic", "men", "women", "urinal_only", "children")
            }
            other_fields.update(
                {
                    "notes": display_text(row.get("notes")),
                    "payment_details": display_text(row.get("payment_details")),
                    "verified_at": display_text(row.get("verified_at")),
                    "area_id": display_text(row.get("area_id")),
                    "source_active": active,
                }
            )
            candidates.append(
                NormalizedCandidate(
                    source_name=SOURCE_NAME,
                    source_record_id=source_id,
                    source_url=None,
                    source_licence=SOURCE_LICENCE,
                    source_updated_at=display_text(row.get("updated_at")),
                    name=name,
                    address=None,
                    town=town,
                    postcode=None,
                    latitude=latitude,
                    longitude=longitude,
                    opening_hours=parse_opening_hours(row.get("opening_times")),
                    is_free=parse_bool(row.get("no_payment")),
                    is_accessible=parse_bool(row.get("accessible")),
                    requires_radar_key=parse_bool(row.get("radar")),
                    has_baby_changing=parse_bool(row.get("baby_change")),
                    is_gender_neutral=parse_bool(row.get("all_gender")),
                    # Toilet Map's `children` flag is not silently reinterpreted
                    # as Relief's family-friendly field.
                    is_family_friendly=None,
                    has_staff_nearby=None,
                    other_fields=other_fields,
                    raw_hash=raw_hash,
                    source_status=status,
                    validation_errors=errors,
                    quality_warnings=warnings,
                )
            )
        return candidates


@dataclass
class MatchDecision:
    decision: str
    facility_id: str | None
    distance_metres: float | None
    name_similarity: float | None
    town_match: bool | None
    reasons: list[str]
    alternatives: list[dict[str, Any]] = field(default_factory=list)

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


def _cell(lat: float, lon: float, size: float = 0.0025) -> tuple[int, int]:
    return (math.floor(lat / size), math.floor(lon / size))


def _nearby_facilities(index: dict[tuple[int, int], list[dict[str, Any]]], candidate: NormalizedCandidate) -> list[dict[str, Any]]:
    if candidate.latitude is None or candidate.longitude is None:
        return []
    row, col = _cell(candidate.latitude, candidate.longitude)
    nearby: list[dict[str, Any]] = []
    for row_delta in range(-3, 4):
        for col_delta in range(-3, 4):
            nearby.extend(index.get((row + row_delta, col + col_delta), []))
    return nearby


def build_facility_index(facilities: Iterable[dict[str, Any]]) -> dict[tuple[int, int], list[dict[str, Any]]]:
    index: dict[tuple[int, int], list[dict[str, Any]]] = defaultdict(list)
    for facility in facilities:
        try:
            lat, lon = float(facility["latitude"]), float(facility["longitude"])
        except (KeyError, TypeError, ValueError):
            continue
        row = dict(facility)
        row["latitude"], row["longitude"] = lat, lon
        index[_cell(lat, lon)].append(row)
    return index


def _candidate_rank(candidate: NormalizedCandidate, facility: dict[str, Any]) -> dict[str, Any] | None:
    if candidate.latitude is None or candidate.longitude is None:
        return None
    try:
        distance = haversine_metres(candidate.latitude, candidate.longitude, float(facility["latitude"]), float(facility["longitude"]))
    except (KeyError, TypeError, ValueError):
        return None
    name_similarity = SequenceMatcher(None, normalize_text(candidate.name), normalize_text(facility.get("name"))).ratio()
    candidate_town = normalize_text(candidate.town)
    facility_town = normalize_text(facility.get("town"))
    town_match = bool(candidate_town and facility_town and candidate_town == facility_town)
    town_unknown = not candidate_town or not facility_town
    distance_score = max(0.0, 1.0 - min(distance, MATCH_RADIUS_METRES) / MATCH_RADIUS_METRES)
    score = name_similarity * 0.65 + (1.0 if town_match else 0.0) * 0.15 + distance_score * 0.20
    return {
        "facility_id": str(facility.get("id")),
        "distance_metres": distance,
        "name_similarity": name_similarity,
        "town_match": town_match,
        "town_unknown": town_unknown,
        "score": score,
        "facility_name": facility.get("name"),
        "facility_town": facility.get("town"),
    }


def match_candidate(
    candidate: NormalizedCandidate,
    facilities_by_id: dict[str, dict[str, Any]],
    source_links_by_id: dict[str, list[dict[str, Any]]],
    facility_index: dict[tuple[int, int], list[dict[str, Any]]],
) -> MatchDecision:
    linked = source_links_by_id.get(candidate.source_record_id, [])
    if len(linked) == 1:
        facility_id = str(linked[0]["facility_id"])
        facility = facilities_by_id.get(facility_id)
        if facility is not None:
            return MatchDecision(
                "EXACT_SOURCE_ID",
                facility_id,
                haversine_metres(candidate.latitude, candidate.longitude, float(facility["latitude"]), float(facility["longitude"]))
                if candidate.latitude is not None and candidate.longitude is not None
                else None,
                1.0 if normalize_text(candidate.name) == normalize_text(facility.get("name")) else SequenceMatcher(None, normalize_text(candidate.name), normalize_text(facility.get("name"))).ratio(),
                normalize_text(candidate.town) == normalize_text(facility.get("town")) if candidate.town and facility.get("town") else None,
                ["existing facility_sources linkage is the strongest identity signal"],
            )
    if len(linked) > 1:
        return MatchDecision("AMBIGUOUS", None, None, None, None, ["source ID links to multiple facilities"])
    if candidate.validation_errors or not candidate.name:
        reasons = list(candidate.validation_errors)
        if not candidate.name:
            reasons.append("no source name available for conservative inferred matching")
        return MatchDecision("INVALID_SOURCE_RECORD", None, None, None, None, reasons)

    ranked = [r for r in (_candidate_rank(candidate, f) for f in _nearby_facilities(facility_index, candidate)) if r is not None]
    viable = [r for r in ranked if (r["distance_metres"] <= MATCH_RADIUS_METRES and r["name_similarity"] >= 0.55) or (r["name_similarity"] >= 0.95 and r["distance_metres"] <= 500)]
    viable.sort(key=lambda r: (-r["score"], r["distance_metres"], r["facility_id"]))
    if not viable:
        return MatchDecision("LIKELY_NEW", None, None, None, None, ["no candidate within the provisional search envelope"])

    best = viable[0]
    second = viable[1] if len(viable) > 1 else None
    alternatives = viable[:3]
    high = (
        best["name_similarity"] >= 0.93
        and best["distance_metres"] <= 60
        and (best["town_match"] or best["town_unknown"])
    ) or (
        best["name_similarity"] >= 0.97
        and best["distance_metres"] <= 150
        and (best["town_match"] or best["town_unknown"])
    )
    close_competitor = second is not None and (best["score"] - second["score"] < 0.15)
    if high and not close_competitor:
        return MatchDecision(
            "HIGH_CONFIDENCE_MATCH",
            best["facility_id"],
            best["distance_metres"],
            best["name_similarity"],
            best["town_match"],
            ["name similarity and geographic proximity meet the conservative high-confidence threshold"],
            alternatives,
        )
    if close_competitor or (best["name_similarity"] >= 0.65 and best["distance_metres"] <= MATCH_RADIUS_METRES):
        return MatchDecision(
            "AMBIGUOUS",
            None,
            best["distance_metres"],
            best["name_similarity"],
            best["town_match"],
            ["one or more plausible facilities remain too close in score for an automatic merge"],
            alternatives,
        )
    return MatchDecision("LIKELY_NEW", None, best["distance_metres"], best["name_similarity"], best["town_match"], ["nearby evidence is below the conservative match threshold"], alternatives)


def field_differences(candidate: NormalizedCandidate, facility: dict[str, Any]) -> dict[str, Any]:
    enrichment: list[dict[str, Any]] = []
    conflicts: list[dict[str, Any]] = []
    omissions: list[dict[str, Any]] = []
    same: list[str] = []
    for source_field, facility_field in FIELD_MAP.items():
        source_value = getattr(candidate, source_field)
        relief_value = facility.get(facility_field)
        if source_field == "opening_hours":
            if not known_value(source_value):
                if known_value(relief_value):
                    omissions.append({
                        "field": source_field,
                        "relief_field": facility_field,
                        "omitted_days": sorted(relief_value) if isinstance(relief_value, dict) else None,
                        "relief_value": relief_value,
                    })
                else:
                    same.append(source_field)
                continue
            if not known_value(relief_value):
                enrichment.append({
                    "field": source_field,
                    "relief_field": facility_field,
                    "source_value": source_value,
                })
                continue
            if isinstance(source_value, dict) and isinstance(relief_value, dict):
                same_days = []
                added_days = []
                conflicting_days = []
                omitted_days = []
                for day in DAY_KEYS:
                    source_day = source_value.get(day)
                    relief_day = relief_value.get(day)
                    if source_day is not None and relief_day is None:
                        added_days.append(day)
                    elif source_day is None and relief_day is not None:
                        omitted_days.append(day)
                    elif source_day == relief_day:
                        same_days.append(day)
                    else:
                        conflicting_days.append(day)
                if added_days:
                    enrichment.append({
                        "field": source_field,
                        "relief_field": facility_field,
                        "added_days": added_days,
                        "source_value": {day: source_value[day] for day in added_days},
                    })
                if conflicting_days:
                    conflicts.append({
                        "field": source_field,
                        "relief_field": facility_field,
                        "conflicting_days": conflicting_days,
                        "source_value": {day: source_value[day] for day in conflicting_days},
                        "relief_value": {day: relief_value[day] for day in conflicting_days},
                    })
                if omitted_days:
                    omissions.append({
                        "field": source_field,
                        "relief_field": facility_field,
                        "omitted_days": omitted_days,
                        "relief_value": {day: relief_value[day] for day in omitted_days},
                    })
                if not added_days and not conflicting_days and not omitted_days:
                    same.append(source_field)
                # Missing source days mean unknown, not closed or deleted.
                continue
            if values_equal(source_value, relief_value, source_field):
                same.append(source_field)
            else:
                conflicts.append({
                    "field": source_field,
                    "relief_field": facility_field,
                    "source_value": source_value,
                    "relief_value": relief_value,
                })
            continue
        if not known_value(source_value):
            if known_value(relief_value):
                omissions.append({"field": source_field, "relief_field": facility_field, "relief_value": relief_value})
            else:
                same.append(source_field)
        elif not known_value(relief_value):
            enrichment.append({"field": source_field, "relief_field": facility_field, "source_value": source_value})
        elif values_equal(source_value, relief_value, source_field):
            same.append(source_field)
        else:
            conflicts.append({"field": source_field, "relief_field": facility_field, "source_value": source_value, "relief_value": relief_value})
    return {"same": same, "enrichment": enrichment, "conflicts": conflicts, "omissions": omissions}


def _example(candidate: NormalizedCandidate, decision: MatchDecision, diff: dict[str, Any] | None = None, lifecycle: str | None = None) -> dict[str, Any]:
    result = {
        "source_record_id": candidate.source_record_id,
        "name": candidate.name,
        "town": candidate.town,
        "latitude": candidate.latitude,
        "longitude": candidate.longitude,
        "source_status": candidate.source_status,
        "quality_warnings": candidate.quality_warnings,
        "validation_errors": candidate.validation_errors,
        "decision": decision.as_dict(),
    }
    if lifecycle:
        result["lifecycle"] = lifecycle
    if diff:
        result["field_differences"] = diff
    return result


def _sample(items: list[dict[str, Any]], count: int = 10) -> list[dict[str, Any]]:
    return items[:count]


def reconcile(
    candidates: list[NormalizedCandidate],
    facilities: list[dict[str, Any]],
    source_links: list[dict[str, Any]],
    baseline: dict[str, Any],
    source_metadata: dict[str, Any],
    input_metadata: dict[str, Any],
) -> dict[str, Any]:
    facilities_by_id = {str(row["id"]): row for row in facilities}
    source_links = [row for row in source_links if row.get("source_name") == SOURCE_NAME]
    source_links_by_id: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in source_links:
        source_links_by_id[str(row.get("source_record_id"))].append(row)
    facility_index = build_facility_index(facilities)
    input_ids = {c.source_record_id for c in candidates if c.source_record_id}
    metrics = Counter()
    field_opportunities: Counter[str] = Counter()
    field_conflicts: Counter[str] = Counter()
    field_omissions: Counter[str] = Counter()
    examples: dict[str, list[dict[str, Any]]] = defaultdict(list)
    inferred_facilities: dict[str, list[str]] = defaultdict(list)
    duplicate_input_ids = sorted(source_id for source_id, count in Counter(c.source_record_id for c in candidates if c.source_record_id).items() if count > 1)
    changed_records: list[dict[str, Any]] = []
    removed_records: list[dict[str, Any]] = []
    invalid_records: list[dict[str, Any]] = []
    ambiguous_records: list[dict[str, Any]] = []
    likely_new_records: list[dict[str, Any]] = []

    for candidate in candidates:
        decision = match_candidate(candidate, facilities_by_id, source_links_by_id, facility_index)
        if candidate.validation_errors:
            metrics["invalid_source_records"] += 1
        if candidate.quality_warnings:
            metrics["source_quality_warnings"] += 1
        metrics[decision.decision] += 1
        diff = None
        lifecycle = None
        if decision.decision in {"EXACT_SOURCE_ID", "HIGH_CONFIDENCE_MATCH"} and decision.facility_id in facilities_by_id:
            facility = facilities_by_id[decision.facility_id]
            diff = field_differences(candidate, facility)
            for item in diff["enrichment"]:
                field_opportunities[item["field"]] += 1
            for item in diff["conflicts"]:
                field_conflicts[item["field"]] += 1
            for item in diff["omissions"]:
                field_omissions[item["field"]] += 1
            if candidate.source_status == "removed":
                lifecycle = "upstream_removed_or_inactive"
                metrics["upstream_removed_inactive_records"] += 1
                removed_records.append(_example(candidate, decision, diff, lifecycle))
            elif diff["enrichment"] or diff["conflicts"]:
                lifecycle = "existing_source_record_changed"
                metrics["changed_linked_records"] += 1
                changed_records.append(_example(candidate, decision, diff, lifecycle))
            else:
                lifecycle = "existing_source_record_unchanged"
                metrics["unchanged_linked_records"] += 1
            if decision.decision == "HIGH_CONFIDENCE_MATCH":
                inferred_facilities[decision.facility_id].append(candidate.source_record_id)
            if candidate.quality_warnings and len(examples["invalid_or_quality"]) < 10:
                examples["invalid_or_quality"].append(_example(candidate, decision, diff, lifecycle))
        elif decision.decision == "AMBIGUOUS":
            ambiguous_records.append(_example(candidate, decision))
        elif decision.decision == "LIKELY_NEW":
            likely_new_records.append(_example(candidate, decision))
        elif decision.decision == "INVALID_SOURCE_RECORD":
            invalid_records.append(_example(candidate, decision))

    missing_linked: list[dict[str, Any]] = []
    seen_missing: set[str] = set()
    for link in source_links:
        source_id = str(link.get("source_record_id"))
        if source_id in input_ids or source_id in seen_missing:
            continue
        seen_missing.add(source_id)
        facility = facilities_by_id.get(str(link.get("facility_id")), {})
        missing_linked.append(
            {
                "source_record_id": source_id,
                "facility_id": link.get("facility_id"),
                "facility_name": facility.get("name"),
                "facility_town": facility.get("town"),
                "source_name": link.get("source_name"),
                "is_current": link.get("is_current"),
                "reason": "previously linked source ID is absent from the current source snapshot; no automatic unpublish/delete",
            }
        )
    metrics["previously_linked_records_absent_upstream"] = len(missing_linked)

    duplicate_clusters = []
    for facility_id, source_ids in sorted(inferred_facilities.items()):
        if len(source_ids) > 1:
            facility = facilities_by_id.get(facility_id, {})
            duplicate_clusters.append({"facility_id": facility_id, "facility_name": facility.get("name"), "inferred_source_record_ids": sorted(source_ids), "reason": "multiple unseen source records independently inferred to the same Relief facility"})
    for source_id in duplicate_input_ids:
        duplicate_clusters.append({"source_record_id": source_id, "reason": "duplicate source record ID appears more than once in the input snapshot"})
    metrics["potential_duplicate_clusters"] = len(duplicate_clusters)

    source_status_counts = Counter(c.source_status for c in candidates)
    validation_error_counts = Counter(error for c in candidates for error in c.validation_errors)
    quality_warning_counts = Counter(warning for c in candidates for warning in c.quality_warnings)
    summary = {
        "relief_baseline_facility_count": baseline.get("facility_count"),
        "current_toilet_map_input_record_count": len(candidates),
        "current_toilet_map_active_records": source_status_counts.get("active", 0),
        "current_toilet_map_removed_or_inactive_records": source_status_counts.get("removed", 0),
        "current_toilet_map_unknown_status_records": source_status_counts.get("unknown", 0),
        "exact_source_id_matches": metrics["EXACT_SOURCE_ID"],
        "high_confidence_inferred_matches": metrics["HIGH_CONFIDENCE_MATCH"],
        "ambiguous_candidates": metrics["AMBIGUOUS"],
        "likely_new_facilities": metrics["LIKELY_NEW"],
        "unchanged_linked_records": metrics["unchanged_linked_records"],
        "changed_linked_records": metrics["changed_linked_records"],
        "upstream_removed_inactive_records": metrics["upstream_removed_inactive_records"] + source_status_counts.get("removed", 0) - metrics["upstream_removed_inactive_records"],
        "previously_linked_relief_records_absent_upstream": metrics["previously_linked_records_absent_upstream"],
        "invalid_source_records": metrics["INVALID_SOURCE_RECORD"],
        "source_quality_warning_records": metrics["source_quality_warnings"],
        "potential_duplicate_clusters": metrics["potential_duplicate_clusters"],
    }
    # A removed source record without a usable match is still a removed source
    # record; count it once in the lifecycle metric.
    summary["upstream_removed_inactive_records"] = source_status_counts.get("removed", 0)

    return {
        "report_schema_version": "1.0",
        "generated_at": input_metadata.get("generated_at"),
        "read_only": True,
        "source": source_metadata,
        "baseline": baseline,
        "input": {
            **input_metadata,
            "source_status_counts": dict(source_status_counts),
            "validation_error_counts": dict(validation_error_counts),
            "quality_warning_counts": dict(quality_warning_counts),
        },
        "matching_rules": {
            "source_id": "Existing facility_sources (source_name + source_record_id) is authoritative; no fuzzy match can override it.",
            "search_radius_metres": MATCH_RADIUS_METRES,
            "high_confidence": [
                "name similarity >= 0.93 and distance <= 60m with matching or unknown town",
                "or name similarity >= 0.97 and distance <= 150m with matching or unknown town",
                "a close competing candidate makes the result AMBIGUOUS instead",
            ],
            "ambiguous": "Plausible nearby candidates with insufficient score margin remain AMBIGUOUS.",
            "likely_new": "No conservative high-confidence match; no automatic merge is proposed.",
            "invalid_source_record": "Missing source identity, unusable coordinates, out-of-envelope coordinates, duplicate input ID without an authoritative linkage, or missing name when no source-ID match exists.",
            "missing_values": "Missing upstream fields remain unknown/omitted; they never become false and never clear an existing Relief value.",
        },
        "summary": summary,
        "field_enrichment_opportunities": dict(field_opportunities),
        "field_conflicts": dict(field_conflicts),
        "field_omissions": dict(field_omissions),
        "potential_duplicate_clusters": duplicate_clusters[:100],
        "examples": {
            "likely_new": _sample(likely_new_records),
            "changed": _sample(changed_records),
            "ambiguous": _sample(ambiguous_records),
            "upstream_removed_or_inactive": _sample(removed_records),
            "previously_linked_absent_upstream": _sample(missing_linked),
            "invalid_or_source_quality": _sample(invalid_records + examples["invalid_or_quality"]),
            "field_conflicts": _sample([item for item in changed_records if item.get("field_differences", {}).get("conflicts")]),
        },
    }

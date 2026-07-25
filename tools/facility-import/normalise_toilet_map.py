#!/usr/bin/env python3
"""Normalise Toilet Map UK CSV into a standardised CSV for staging import."""

import csv
import json
import sys
from pathlib import Path

DAY_KEYS = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]


def to_bool(val: str):
    """Convert Toilet Map string booleans. Empty/unknown → None."""
    if not val or val.strip() == "":
        return None
    s = val.strip().lower()
    if s in ("yes", "true", "1"):
        return True
    if s in ("no", "false", "0"):
        return False
    return None


def parse_areas(val: str) -> str:
    """Extract town name from the areas JSON field."""
    if not val or val.strip() == "":
        return ""
    try:
        areas = json.loads(val)
        if isinstance(areas, dict):
            return areas.get("name", "")
        if isinstance(areas, list) and areas:
            return areas[0].get("name", "")
    except (json.JSONDecodeError, TypeError):
        pass
    return ""


def transform_opening_hours(raw_hours):
    """Transform the7-element Mon-Sun array into a weekday-keyed object.

    Toilet Map format: [["09:00","17:00"], ..., ["09:00","17:00"]]
    Index 0 = Monday, index 6 = Sunday.

    Output: {"monday": {"open": "09:00", "close": "17:00"}, ...}
    Empty sub-array [] means closed that day → null.
    Missing or malformed data → key omitted (unknown, not closed).
    """
    if not isinstance(raw_hours, list) or len(raw_hours) != 7:
        return None

    result = {}
    for i, day_key in enumerate(DAY_KEYS):
        entry = raw_hours[i]
        if not isinstance(entry, list) or len(entry) < 2:
            # Empty array or malformed → closed
            result[day_key] = None
            continue

        open_time = str(entry[0]).strip()
        close_time = str(entry[1]).strip()

        if not open_time or not close_time:
            result[day_key] = None
            continue

        result[day_key] = {"open": open_time, "close": close_time}

    return result


def normalise_row(row: dict) -> dict | None:
    """Convert a single Toilet Map CSV row to a normalised row dict."""
    source_id = row.get("id", "").strip()
    if not source_id:
        return None

    # Skip inactive facilities
    if to_bool(row.get("active", "")) is False:
        return None

    try:
        lat = float(row["latitude"])
        lng = float(row["longitude"])
    except (ValueError, TypeError, KeyError):
        return None

    # UK bounding box check
    if not (49.0 <= lat <= 61.0 and -9.0 <= lng <= 2.0):
        return None

    name = row.get("name", "").strip() or "Unnamed Toilet"

    # Do NOT use geohash as postcode — Toilet Map doesn't provide postcodes
    postcode = None

    # Do NOT use facility name as address — use town only
    town = parse_areas(row.get("areas", ""))

    # Parse opening_times and transform to weekday-keyed object
    opening_hours = None
    raw_hours = row.get("opening_times", "").strip()
    if raw_hours:
        try:
            parsed = json.loads(raw_hours)
            opening_hours = transform_opening_hours(parsed)
        except (json.JSONDecodeError, TypeError):
            opening_hours = None

    return {
        "source_record_id": source_id,
        "name": name,
        "latitude": round(lat, 6),
        "longitude": round(lng, 6),
        "address": town or "",
        "postcode": postcode,
        "town": town,
        "is_accessible": to_bool(row.get("accessible", "")),
        "has_baby_changing": to_bool(row.get("baby_change", "")),
        "requires_radar_key": to_bool(row.get("radar", "")),
        "is_free": to_bool(row.get("no_payment", "")),
        "opening_hours": opening_hours,
        "source_updated_at": row.get("updated_at", "").strip() or None,
        "raw_data": row,
    }


def normalise_file(input_path: Path, output_path: Path) -> int:
    """Normalise a Toilet Map CSV file. Returns row count."""
    rows = []
    skipped = 0

    with open(input_path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for i, row in enumerate(reader):
            out = normalise_row(row)
            if out:
                rows.append(out)
            else:
                skipped += 1

    if not rows:
        print("No valid rows after normalisation.")
        return 0

    fieldnames = [
        "source_record_id", "name", "latitude", "longitude",
        "address", "postcode", "town",
        "is_accessible", "has_baby_changing", "requires_radar_key", "is_free",
        "opening_hours", "source_updated_at", "raw_data",
    ]

    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            out = dict(row)
            out["raw_data"] = json.dumps(out.get("raw_data") or {})
            out["opening_hours"] = json.dumps(out.get("opening_hours") or {})
            writer.writerow(out)

    print(f"Normalised {len(rows)} rows ({skipped} skipped) -> {output_path}")
    return len(rows)


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: normalise_toilet_map.py <input.csv> <output.csv>")
        sys.exit(1)
    normalise_file(Path(sys.argv[1]), Path(sys.argv[2]))

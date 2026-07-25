#!/usr/bin/env python3
"""Normalise Toilet Map UK GeoJSON into a CSV for staging import."""

import csv
import json
import sys
from pathlib import Path


def parse_opening_hours(properties: dict) -> dict | None:
    """Best-effort parse of opening hours from Toilet Map properties."""
    raw = properties.get("openingHours") or properties.get("opening_hours")
    if not raw:
        return None

    days = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]
    hours: dict = {}

    if isinstance(raw, str):
        # Simple "Mo-Fr 08:00-18:00; Sa 09:00-13:00" style
        for part in raw.split(";"):
            part = part.strip()
            if not part:
                continue
            # Very rough parse — just store the raw string per day
            for day in days:
                if day[:2].lower() in part.lower() or day[:3].lower() in part.lower():
                    hours[day] = part.strip()
        if hours:
            return hours

    if isinstance(raw, dict):
        return raw

    return None


def normalise(feature: dict) -> dict | None:
    """Convert a single GeoJSON feature to a normalised row dict."""
    props = feature.get("properties", {})
    geom = feature.get("geometry", {})

    source_id = props.get("id") or props.get("ref") or props.get("osmId")
    if not source_id:
        return None

    coords = geom.get("coordinates", [None, None])
    lng = coords[0] if len(coords) > 0 else None
    lat = coords[1] if len(coords) > 1 else None

    if lat is None or lng is None:
        return None

    # UK bounding box sanity check (rough)
    if not (49.0 <= lat <= 61.0 and -9.0 <= lng <= 2.0):
        return None

    name = props.get("name") or props.get("title") or "Unknown"
    address_parts = [
        props.get("street"),
        props.get("addressLocality"),
        props.get("addressRegion"),
    ]
    address = ", ".join(p for p in address_parts if p) or ""

    def to_bool(val):
        if val is None:
            return None
        if isinstance(val, bool):
            return val
        s = str(val).lower().strip()
        if s in ("yes", "true", "1"):
            return True
        if s in ("no", "false", "0"):
            return False
        return None

    return {
        "source_record_id": str(source_id),
        "name": name,
        "latitude": round(lat, 6),
        "longitude": round(lng, 6),
        "address": address,
        "postcode": props.get("postalCode") or props.get("postcode") or "",
        "town": props.get("addressLocality") or props.get("town") or "",
        "is_accessible": to_bool(props.get("accessible") or props.get("wheelchair")),
        "has_baby_changing": to_bool(props.get("babyChanging")),
        "requires_radar_key": to_bool(props.get("radarKey")),
        "is_free": to_bool(props.get("free")),
        "opening_hours": parse_opening_hours(props),
        "source_updated_at": props.get("dateModified") or props.get("lastVerified"),
        "raw_data": props,
    }


def normalise_file(input_path: Path, output_path: Path) -> int:
    """Normalise a GeoJSON file to CSV. Returns row count."""
    with open(input_path) as f:
        geojson = json.load(f)

    features = geojson.get("features", [])
    if not features:
        print("No features found in input file.")
        return 0

    rows = []
    skipped = 0
    for feature in features:
        row = normalise(feature)
        if row:
            rows.append(row)
        else:
            skipped += 1

    if not rows:
        print("No valid rows after normalisation.")
        return 0

    fieldnames = list(rows[0].keys())
    # Move raw_data to end and serialise as JSON string
    fieldnames.remove("raw_data")
    fieldnames.append("raw_data")

    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            out = dict(row)
            out["raw_data"] = json.dumps(out.get("raw_data") or {})
            out["opening_hours"] = json.dumps(out.get("opening_hours") or {})
            writer.writerow(out)

    print(f"Normalised {len(rows)} rows ({skipped} skipped) → {output_path}")
    return len(rows)


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: normalise_toilet_map.py <input.geojson> <output.csv>")
        sys.exit(1)
    normalise_file(Path(sys.argv[1]), Path(sys.argv[2]))

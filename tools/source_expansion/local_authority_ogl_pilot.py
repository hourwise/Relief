"""Deterministic, read-only pilot adapter for local-authority OGL toilet data.

This module is deliberately smaller than a production ingestion framework.  It
normalizes the two selected pilot resources, validates their disposable raw
snapshot fingerprints, and classifies supplied *read-only* production-match
evidence.  It has no database client and no production-write path.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import unicodedata
from collections import Counter
from pathlib import Path
from typing import Any, Iterable


TOOL_VERSION = "relief.local-authority-ogl-pilot-1.v1"
PRODUCTION_WRITE_CAPABILITY = False
OFFICIAL_ATTRIBUTION = "Contains public sector information licensed under the Open Government Licence v3.0."
OGL_IDENTIFIER = "Open Government Licence v3.0"
OGL_URL = "https://www.nationalarchives.gov.uk/doc/open-government-licence/version/3/"

SOURCE_CATALOG: dict[str, dict[str, Any]] = {
    "city-of-york-public-toilets": {
        "publisher": "City of York Council",
        "dataset": "Location of Public Toilets in York",
        "catalogue_url": "https://www.data.gov.uk/dataset/e49697a4-da67-429a-ac02-2a3d32023a12/public-toilets",
        "resource_url": "https://maps.york.gov.uk/arcgis/rest/services/Public/LV_TranStreetCare/MapServer/0/query?where=1%3D1&outFields=*&returnGeometry=true&f=geojson",
        "service_url": "https://maps.york.gov.uk/arcgis/rest/services/Public/LV_TranStreetCare/MapServer/0",
        "licence": OGL_IDENTIFIER,
        "licence_url": OGL_URL,
        "catalogue_last_updated": "2022-03-09",
        "source_record_id_field": "OBJECTID",
        "expected_bytes": 6495,
        "expected_sha256": "1da412b6731b8c07ced75a663098d9dee55cba4747503399b588572c2c4b5b12",
        "expected_features": 18,
        "record_type_field": "SERVICETYPELABEL",
    },
    "causeway-coast-and-glens-public-toilets": {
        "publisher": "Causeway Coast and Glens Borough Council / OpenDataNI",
        "dataset": "Public Toilet Locations in Causeway Coast and Glens",
        "catalogue_url": "https://www.data.gov.uk/dataset/62eab2d2-2627-4616-8f12-412b48c80e35/public-toilet-locations-in-causeway-coast-and-glens11",
        "resource_url": "https://services.arcgis.com/kNPftFdcdm7bfDuO/arcgis/rest/services/Public_Toilets_CCGBC/FeatureServer/0/query?where=1%3D1&outFields=*&returnGeometry=true&f=geojson",
        "service_url": "https://services.arcgis.com/kNPftFdcdm7bfDuO/arcgis/rest/services/Public_Toilets_CCGBC/FeatureServer/0",
        "licence": OGL_IDENTIFIER,
        "licence_url": OGL_URL,
        "catalogue_last_updated": "2024-07-27",
        "service_metadata_last_edit": "2026-03-19",
        "source_record_id_field": "GlobalID",
        "expected_bytes": 33341,
        "expected_sha256": "50eabf55fa58be22bcd09d1f9d0d94a61b17278e7f3434ad832b4df9cb884279",
        "expected_features": 52,
        "record_type_field": None,
    },
}


def canonical_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def _clean(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _number(value: Any) -> float | None:
    if value is None or value == "":
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def normalize_name(value: Any) -> str:
    """Conservative name form used only for comparison, never as source text."""
    text = unicodedata.normalize("NFKC", _clean(value) or "").casefold()
    text = re.sub(r"[^\w]+", " ", text, flags=re.UNICODE)
    return re.sub(r"\s+", " ", text).strip()


def normalize_postcode(value: Any) -> str:
    return re.sub(r"[^A-Z0-9]", "", (_clean(value) or "").upper())


def _feature_coordinates(feature: dict[str, Any]) -> tuple[float | None, float | None]:
    geometry = feature.get("geometry") or {}
    coordinates = geometry.get("coordinates") if isinstance(geometry, dict) else None
    if geometry.get("type") != "Point" or not isinstance(coordinates, list) or len(coordinates) < 2:
        return None, None
    return _number(coordinates[1]), _number(coordinates[0])


def _feature_id(properties: dict[str, Any], source: dict[str, Any], fallback: int) -> str:
    field = source["source_record_id_field"]
    value = _clean(properties.get(field))
    if value is None:
        value = _clean(properties.get("OBJECTID"))
    if value is None:
        value = f"row-{fallback}"
    return f"{source['dataset']}:{value}"


def normalize_geojson_feature(feature: dict[str, Any], source_id: str, ordinal: int) -> dict[str, Any]:
    source = SOURCE_CATALOG[source_id]
    properties = dict(feature.get("properties") or {})
    latitude, longitude = _feature_coordinates(feature)
    if source_id == "city-of-york-public-toilets":
        name = _clean(properties.get("LOCATIONTEXT"))
        address = _clean(properties.get("STREETADDRESS"))
        postcode = _clean(properties.get("POSTCODE"))
        toilet_type = _clean(properties.get("SERVICETYPELABEL"))
        accessibility = None
        opening_hours = None
        charge = None
        last_updated = None
    else:
        name = _clean(properties.get("Name"))
        address = _clean(properties.get("Address"))
        postcode = _clean(properties.get("Postcode"))
        toilet_type = "Public toilets"
        accessibility = _clean(properties.get("Disabled_A"))
        opening_hours = _clean(properties.get("Opening_Ho"))
        charge = _clean(properties.get("Payment_Re"))
        last_updated = _clean(properties.get("EditDate"))
    errors: list[str] = []
    if not name:
        errors.append("missing name")
    if latitude is None or longitude is None:
        errors.append("missing WGS84 point geometry")
    if toilet_type not in {"Public toilets", "Changing Places"}:
        errors.append("record does not explicitly identify a public toilet facility")
    return {
        "source_namespace": source_id,
        "source_dataset": source["dataset"],
        "source_record_id": _feature_id(properties, source, ordinal),
        "name": name,
        "address": address,
        "postcode": postcode,
        "latitude": latitude,
        "longitude": longitude,
        "toilet_type": toilet_type,
        "accessibility": accessibility,
        "opening_hours": opening_hours,
        "status": None,
        "charge": charge,
        "operator": source["publisher"],
        "last_updated": last_updated,
        "name_normalized": normalize_name(name),
        "postcode_normalized": normalize_postcode(postcode),
        "raw_source_fingerprint": sha256_bytes(canonical_json(feature).encode("utf-8")),
        "licence": source["licence"],
        "attribution": OFFICIAL_ATTRIBUTION,
        "direct_toilet_evidence": not errors or "record does not explicitly identify a public toilet facility" not in errors,
        "validation_errors": errors,
    }


def load_geojson(path: Path, source_id: str) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    if source_id not in SOURCE_CATALOG:
        raise ValueError(f"unknown pilot source: {source_id}")
    payload = path.read_bytes()
    source = SOURCE_CATALOG[source_id]
    actual_sha = sha256_bytes(payload)
    if len(payload) != source["expected_bytes"] or actual_sha != source["expected_sha256"]:
        raise ValueError(
            f"source fingerprint mismatch for {source_id}: {len(payload)} bytes / {actual_sha}"
        )
    document = json.loads(payload.decode("utf-8"))
    features = document.get("features") if isinstance(document, dict) else None
    if not isinstance(features, list):
        raise ValueError("pilot input must be a GeoJSON FeatureCollection")
    records = [normalize_geojson_feature(feature, source_id, index) for index, feature in enumerate(features, start=1)]
    if len(records) != source["expected_features"]:
        raise ValueError(f"feature count mismatch for {source_id}: {len(records)}")
    return {
        "source_id": source_id,
        "byte_size": len(payload),
        "sha256": actual_sha,
        "feature_count": len(records),
        "licence": source["licence"],
        "attribution": OFFICIAL_ATTRIBUTION,
    }, sorted(records, key=lambda row: row["source_record_id"])


def _tokens(value: str | None) -> set[str]:
    return {token for token in normalize_name(value).split() if token}


def classify_production_match(match: dict[str, Any]) -> dict[str, Any]:
    """Apply the bounded pilot guard to one read-only nearest-facility result."""
    distance = _number(match.get("distance_m"))
    exact_postcode = bool(match.get("exact_postcode"))
    token_subset = bool(match.get("token_subset"))
    existing = exact_postcode or (distance is not None and distance <= 100) or (
        token_subset and distance is not None and distance <= 250
    )
    broad_status = "LIKELY_EXISTING_OR_DUPLICATE" if existing else "CREDIBLE_NET_NEW_CANDIDATE"
    conservative = broad_status == "CREDIBLE_NET_NEW_CANDIDATE" and not (
        distance is not None and distance <= 250
    )
    return {
        **match,
        "candidate_status": broad_status,
        "conservative_net_new": conservative,
        "guard_reasons": sorted([
            reason
            for reason, present in {
                "EXACT_POSTCODE": exact_postcode,
                "WITHIN_100M": distance is not None and distance <= 100,
                "TOKEN_SUBSET_WITHIN_250M": token_subset and distance is not None and distance <= 250,
            }.items()
            if present
        ]),
    }


def classify_matches(records: Iterable[dict[str, Any]], matches: Iterable[dict[str, Any]]) -> list[dict[str, Any]]:
    records_by_id = {record["source_record_id"]: record for record in records}
    match_rows = list(matches)
    match_ids = [str(row.get("source_record_id")) for row in match_rows]
    if len(match_ids) != len(set(match_ids)):
        raise ValueError("duplicate production comparison source_record_id")
    missing = sorted(set(records_by_id) - set(match_ids))
    extra = sorted(set(match_ids) - set(records_by_id))
    if missing or extra:
        raise ValueError(f"production comparison coverage mismatch: missing={missing}, extra={extra}")
    return [
        classify_production_match({**row, "source_name_normalized": records_by_id[row["source_record_id"]]["name_normalized"]})
        for row in sorted(match_rows, key=lambda row: str(row["source_record_id"]))
    ]


def summarize(records: Iterable[dict[str, Any]], matches: Iterable[dict[str, Any]]) -> dict[str, Any]:
    records_list = list(records)
    classified = list(matches)
    by_source = Counter(row["source_namespace"] for row in records_list)
    by_status = Counter(row["candidate_status"] for row in classified)
    conservative = sum(1 for row in classified if row["conservative_net_new"])
    return {
        "tool_version": TOOL_VERSION,
        "production_write_capability": PRODUCTION_WRITE_CAPABILITY,
        "records": len(records_list),
        "records_by_source": dict(sorted(by_source.items())),
        "direct_toilet_evidence_records": sum(1 for row in records_list if row["direct_toilet_evidence"]),
        "normalization_error_records": sum(1 for row in records_list if row["validation_errors"]),
        "candidate_status_counts": dict(sorted(by_status.items())),
        "credible_net_new_candidates": by_status["CREDIBLE_NET_NEW_CANDIDATE"],
        "conservative_net_new_candidates": conservative,
        "production_mutations": 0,
        "guard": {
            "existing_or_duplicate": "exact postcode OR within 100m OR normalized source-name token subset within 250m",
            "conservative_net_new": "broad candidate and no nearest facility within 250m",
            "proximity_only_is_not_proof": True,
        },
    }


def _read_matches(path: Path) -> list[dict[str, Any]]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(value, dict):
        value = value.get("records")
    if not isinstance(value, list):
        raise ValueError("comparison input must be a JSON list")
    return value


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Normalize selected council OGL toilet resources without production writes")
    parser.add_argument("--input", action="append", nargs=2, metavar=("SOURCE_ID", "PATH"), required=True)
    parser.add_argument("--comparison", type=Path, required=True, help="read-only production comparison JSON")
    parser.add_argument("--output", type=Path, required=True, help="local evidence output path")
    args = parser.parse_args(argv)
    if PRODUCTION_WRITE_CAPABILITY:
        raise RuntimeError("production write capability must remain disabled")
    manifests = []
    records = []
    for source_id, source_path in sorted(args.input):
        manifest, source_records = load_geojson(Path(source_path), source_id)
        manifests.append(manifest)
        records.extend(source_records)
    records.sort(key=lambda row: (row["source_namespace"], row["source_record_id"]))
    matches = classify_matches(records, _read_matches(args.comparison))
    payload = {
        "tool_version": TOOL_VERSION,
        "production_write_capability": PRODUCTION_WRITE_CAPABILITY,
        "source_manifests": manifests,
        "records": records,
        "comparison": matches,
        "summary": summarize(records, matches),
    }
    args.output.write_text(canonical_json(payload) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

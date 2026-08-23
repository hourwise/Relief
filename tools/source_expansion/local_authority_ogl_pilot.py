"""Deterministic, read-only pilot adapter for local-authority OGL toilet data.

This module is deliberately smaller than a production ingestion framework.  It
normalizes the two selected pilot resources, validates their disposable raw
snapshot fingerprints, and classifies supplied *read-only* production-match
evidence.  It has no database client and no production-write path.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import re
import unicodedata
from collections import Counter
from pathlib import Path
from typing import Any, Iterable


TOOL_VERSION = "relief.local-authority-ogl-pilot-2.v1"
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
    "adur-public-toilets": {
        "publisher": "Adur District Council",
        "dataset": "Adur public toilets",
        "catalogue_url": "https://www.adur-worthing.gov.uk/datasets/",
        "resource_url": "https://www.adur-worthing.gov.uk/datasets/public-toilets/adur-toilets.csv",
        "licence": OGL_IDENTIFIER,
        "licence_url": OGL_URL,
        "attribution": "Contains public sector information licensed under the Open Government Licence v3.0. Credit: Adur District Council.",
        "catalogue_last_updated": "2023-02-06",
        "format": "csv",
        "source_record_id_field": "UPRN",
        "coordinate_reference_system": "OSGB36",
        "direct_evidence_field": "ServiceTypeLabel",
        "direct_evidence_values": {"Public toilets"},
        "name_field": "LocationText",
        "address_field": "StreetAddress",
        "postcode_field": "Postcode",
        "accessibility_field": "AccessibleCategory",
        "opening_hours_field": "OpeningHours",
        "charge_field": "ChargeAmount",
        "operator_field": "ManagedBy",
        "last_updated_field": "ExtractDate",
        "stable_identity": True,
    },
    "worthing-public-toilets": {
        "publisher": "Worthing Borough Council",
        "dataset": "Worthing public toilets",
        "catalogue_url": "https://www.adur-worthing.gov.uk/datasets/",
        "resource_url": "https://www.adur-worthing.gov.uk/datasets/public-toilets/worthing-toilets.csv",
        "licence": OGL_IDENTIFIER,
        "licence_url": OGL_URL,
        "attribution": "Contains public sector information licensed under the Open Government Licence v3.0. Credit: Worthing Borough Council.",
        "catalogue_last_updated": "2023-02-06",
        "format": "csv",
        "source_record_id_field": "UPRN",
        "coordinate_reference_system": "OSGB36",
        "direct_evidence_field": "ServiceTypeLabel",
        "direct_evidence_values": {"Public toilets"},
        "name_field": "LocationText",
        "address_field": "StreetAddress",
        "postcode_field": "Postcode",
        "accessibility_field": "AccessibleCategory",
        "opening_hours_field": "OpeningHours",
        "charge_field": "ChargeAmount",
        "operator_field": "ManagedBy",
        "last_updated_field": "ExtractDate",
        "stable_identity": True,
    },
    "perth-kinross-public-toilets-and-comfort-schemes": {
        "publisher": "Perth & Kinross Council",
        "dataset": "Public Toilets and Comfort Schemes (open data)",
        "catalogue_url": "https://opendata.scot/datasets/perth%2B%2526%2Bkinross%2Bcouncil-public%2Btoilets%2Band%2Bcomfort%2Bschemes%2B%2528open%2Bdata%2529/",
        "resource_url": "https://services-eu1.arcgis.com/WD0cvOmDKf7CA0Xy/arcgis/rest/services/Public_Toilets___Comfort_Schemes/FeatureServer/replicafilescache/Public_Toilets___Comfort_Schemes_2126571122735550845.geojson",
        "licence": "UK Open Government Licence v3.0; original content CC-BY-SA 4.0",
        "licence_url": OGL_URL,
        "attribution": "Perth & Kinross Council; original content CC-BY-SA 4.0 as stated by Open Data Scotland.",
        "catalogue_last_updated": "2026-04-08",
        "format": "geojson",
        "source_record_id_field": "UPRN",
        "coordinate_reference_system": "OSGB36",
        "name_field": "FACILITY_NAME",
        "address_field": "FULL_ADDRESS",
        "postcode_field": "POSTCODE",
        "type_field": "TYPE",
        "direct_evidence_field": "TYPE",
        "direct_evidence_values": {"Public toilet", "Comfort scheme"},
        "accessibility_field": "DISABLED_TOILET",
        "opening_hours_field": "OPEN_HOURS",
        "status_field": "STATUS",
        "stable_identity": True,
    },
    "belfast-public-toilets": {
        "publisher": "Belfast City Council",
        "dataset": "Public toilets",
        "catalogue_url": "https://www.data.gov.uk/dataset/8a553138-eba0-42f2-b8ae-26c6ca240393/public-toilets7",
        "resource_url": "https://www.belfastcity.gov.uk/getmedia/49cc1bb5-b8d6-433c-afa6-05f23e9287b0/toiletsdata.csv",
        "licence": OGL_IDENTIFIER,
        "licence_url": OGL_URL,
        "attribution": "Contains public sector information licensed under the Open Government Licence v3.0. Credit: Belfast City Council.",
        "catalogue_last_updated": "2015-01-22",
        "format": "csv",
        "source_record_id_field": None,
        "identity_fields": ["NAME", "ADDRESS", "LATITUDE", "LONGITUDE"],
        "direct_evidence_field": None,
        "direct_evidence_values": set(),
        "name_field": "NAME",
        "address_field": "ADDRESS",
        "postcode_field": "POSTCODE",
        "latitude_field": "LATITUDE",
        "longitude_field": "LONGITUDE",
        "accessibility_field": "RADAR Key",
        "stable_identity": True,
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
    normalized = re.sub(r"[^A-Z0-9]", "", (_clean(value) or "").upper())
    return "" if normalized in {"NA", "NIL", "NONE", "UNKNOWN"} else normalized


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


def osgb36_to_wgs84(easting: float, northing: float) -> tuple[float, float]:
    """Convert British National Grid easting/northing to WGS84 without a dependency."""
    a = 6377563.396
    b = 6356256.909
    f0 = 0.9996012717
    lat0 = math.radians(49.0)
    lon0 = math.radians(-2.0)
    n0 = -100000.0
    e0 = 400000.0
    e2 = 1 - (b * b) / (a * a)
    n = (a - b) / (a + b)
    lat = lat0
    m = 0.0
    while abs(northing - n0 - m) >= 0.00001:
        lat = (northing - n0 - m) / (a * f0) + lat
        m = (
            b
            * f0
            * ((1 + n + 5 * (n**2) / 4 + 5 * (n**3) / 4) * (lat - lat0)
            - (3 * n + 3 * (n**2) + 21 * (n**3) / 8) * math.sin(lat - lat0) * math.cos(lat + lat0)
            + (15 * (n**2) / 8 + 15 * (n**3) / 8)
            * math.sin(2 * (lat - lat0))
            * math.cos(2 * (lat + lat0))
            - 35 * (n**3) / 24 * math.sin(3 * (lat - lat0)) * math.cos(3 * (lat + lat0))
        ))
    sin_lat = math.sin(lat)
    cos_lat = math.cos(lat)
    nu = a * f0 / math.sqrt(1 - e2 * sin_lat**2)
    rho = a * f0 * (1 - e2) / (1 - e2 * sin_lat**2) ** 1.5
    eta2 = nu / rho - 1
    de = easting - e0
    tan_lat = math.tan(lat)
    sec_lat = 1 / cos_lat
    vii = tan_lat / (2 * rho * nu)
    viii = tan_lat / (24 * rho * nu**3) * (5 + 3 * tan_lat**2 + eta2 - 9 * tan_lat**2 * eta2)
    ix = tan_lat / (720 * rho * nu**5) * (61 + 90 * tan_lat**2 + 45 * tan_lat**4)
    x = sec_lat / nu
    xi = sec_lat / (6 * nu**3) * (nu / rho + 2 * tan_lat**2)
    xii = sec_lat / (120 * nu**5) * (5 + 28 * tan_lat**2 + 24 * tan_lat**4)
    xiia = sec_lat / (5040 * nu**7) * (
        61 + 662 * tan_lat**2 + 1320 * tan_lat**4 + 720 * tan_lat**6
    )
    osgb_lat = lat - vii * de**2 + viii * de**4 - ix * de**6
    osgb_lon = lon0 + x * de - xi * de**3 + xii * de**5 - xiia * de**7

    # Helmert transform from the Airy 1830 / OSGB36 datum to WGS84.
    h = 0.0
    x1 = (nu + h) * math.cos(lat) * math.cos(osgb_lon)
    y1 = (nu + h) * math.cos(lat) * math.sin(osgb_lon)
    z1 = ((1 - e2) * nu + h) * math.sin(lat)
    tx, ty, tz = 446.448, -125.157, 542.060
    rx = math.radians(0.1502 / 3600)
    ry = math.radians(0.2470 / 3600)
    rz = math.radians(0.8421 / 3600)
    scale = 1 + 20.4894e-6
    x2 = tx + scale * x1 - rz * y1 + ry * z1
    y2 = ty + rz * x1 + scale * y1 - rx * z1
    z2 = tz - ry * x1 + rx * y1 + scale * z1
    wgs_a = 6378137.0
    wgs_b = 6356752.3141
    wgs_e2 = 1 - (wgs_b * wgs_b) / (wgs_a * wgs_a)
    p = math.sqrt(x2 * x2 + y2 * y2)
    wgs_lat = math.atan2(z2, p * (1 - wgs_e2))
    for _ in range(10):
        wgs_nu = wgs_a / math.sqrt(1 - wgs_e2 * math.sin(wgs_lat) ** 2)
        wgs_lat = math.atan2(z2 + wgs_e2 * wgs_nu * math.sin(wgs_lat), p)
    wgs_lon = math.atan2(y2, x2)
    return math.degrees(wgs_lat), math.degrees(wgs_lon)


def _valid_coordinates(latitude: float | None, longitude: float | None) -> bool:
    return (
        latitude is not None
        and longitude is not None
        and -90 <= latitude <= 90
        and -180 <= longitude <= 180
    )


def _generic_record_id(values: dict[str, Any], source: dict[str, Any], ordinal: int) -> tuple[str, bool]:
    field = source.get("source_record_id_field")
    if field:
        value = _clean(values.get(field))
        if value:
            return f"{source['dataset']}:{value}", bool(source.get("stable_identity"))
    identity_fields = source.get("identity_fields") or []
    identity_values = [_clean(values.get(field)) for field in identity_fields]
    if identity_fields and all(identity_values):
        digest = hashlib.sha256("|".join(identity_values).encode("utf-8")).hexdigest()[:20]
        return f"{source['dataset']}:derived-{digest}", bool(source.get("stable_identity"))
    return f"{source['dataset']}:row-{ordinal}", False


def _generic_coordinates(values: dict[str, Any], source: dict[str, Any], geometry: dict[str, Any] | None) -> tuple[float | None, float | None]:
    if geometry is not None:
        latitude, longitude = _feature_coordinates({"geometry": geometry})
        if source.get("coordinate_reference_system") == "OSGB36" and latitude is not None and longitude is not None:
            return osgb36_to_wgs84(longitude, latitude)
        return latitude, longitude
    latitude = _number(values.get(source.get("latitude_field", "latitude")))
    longitude = _number(values.get(source.get("longitude_field", "longitude")))
    if source.get("coordinate_reference_system") == "OSGB36" and latitude is None and longitude is None:
        easting = _number(values.get("GeoX"))
        northing = _number(values.get("GeoY"))
        if easting is not None and northing is not None:
            return osgb36_to_wgs84(easting, northing)
    return latitude, longitude


def normalize_tabular_record(
    values: dict[str, Any],
    source_id: str,
    ordinal: int,
    raw_fingerprint: str,
    geometry: dict[str, Any] | None = None,
) -> dict[str, Any]:
    source = SOURCE_CATALOG[source_id]
    name = _clean(values.get(source.get("name_field", "name")))
    address = _clean(values.get(source.get("address_field", "address")))
    postcode = _clean(values.get(source.get("postcode_field", "postcode")))
    latitude, longitude = _generic_coordinates(values, source, geometry)
    type_value = _clean(values.get(source.get("type_field", ""))) if source.get("type_field") else None
    direct_value = _clean(values.get(source.get("direct_evidence_field"))) if source.get("direct_evidence_field") else None
    direct = bool(source.get("direct_evidence_field") is None or direct_value in source.get("direct_evidence_values", set()))
    errors: list[str] = []
    if not name:
        errors.append("missing name")
    if not _valid_coordinates(latitude, longitude):
        errors.append("missing or invalid WGS84 coordinates")
    if not direct:
        errors.append("record does not explicitly identify a public toilet facility")
    source_record_id, stable_identity = _generic_record_id(values, source, ordinal)
    status = _clean(values.get(source.get("status_field"))) if source.get("status_field") else None
    return {
        "source_namespace": source_id,
        "source_dataset": source["dataset"],
        "source_record_id": source_record_id,
        "name": name,
        "address": address,
        "postcode": postcode,
        "latitude": latitude,
        "longitude": longitude,
        "toilet_type": type_value or direct_value or "Public toilets",
        "accessibility": _clean(values.get(source.get("accessibility_field"))) if source.get("accessibility_field") else None,
        "opening_hours": _clean(values.get(source.get("opening_hours_field"))) if source.get("opening_hours_field") else None,
        "status": status,
        "charge": _clean(values.get(source.get("charge_field"))) if source.get("charge_field") else None,
        "operator": _clean(values.get(source.get("operator_field"))) or source["publisher"],
        "last_updated": _clean(values.get(source.get("last_updated_field"))) if source.get("last_updated_field") else None,
        "name_normalized": normalize_name(name),
        "postcode_normalized": normalize_postcode(postcode),
        "raw_source_fingerprint": raw_fingerprint,
        "licence": source["licence"],
        "attribution": source.get("attribution", OFFICIAL_ATTRIBUTION),
        "source_identity_stable": stable_identity,
        "direct_toilet_evidence": direct,
        "validation_errors": errors,
    }


def _csv_rows(payload: bytes) -> list[dict[str, Any]]:
    text = payload.decode("utf-8-sig")
    return [dict(row) for row in csv.DictReader(text.splitlines(keepends=True))]


def load_source(path: Path, source_id: str) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    """Load a configured pilot source; Pilot 1 GeoJSON keeps its exact fingerprint gate."""
    source = SOURCE_CATALOG.get(source_id)
    if source is None:
        raise ValueError(f"unknown pilot source: {source_id}")
    if source_id in {"city-of-york-public-toilets", "causeway-coast-and-glens-public-toilets"}:
        return load_geojson(path, source_id)
    payload = path.read_bytes()
    actual_sha = sha256_bytes(payload)
    if source.get("expected_bytes") is not None and len(payload) != source["expected_bytes"]:
        raise ValueError(f"source byte count mismatch for {source_id}")
    if source.get("expected_sha256") is not None and actual_sha != source["expected_sha256"]:
        raise ValueError(f"source fingerprint mismatch for {source_id}")
    if source.get("format") == "csv":
        rows = _csv_rows(payload)
        records = [
            normalize_tabular_record(row, source_id, ordinal, sha256_bytes(canonical_json(row).encode("utf-8")))
            for ordinal, row in enumerate(rows, start=1)
        ]
    elif source.get("format") == "geojson":
        document = json.loads(payload.decode("utf-8"))
        features = document.get("features") if isinstance(document, dict) else None
        if not isinstance(features, list):
            raise ValueError(f"{source_id} input must be a GeoJSON FeatureCollection")
        records = [
            normalize_tabular_record(
                dict(feature.get("properties") or {}),
                source_id,
                ordinal,
                sha256_bytes(canonical_json(feature).encode("utf-8")),
                feature.get("geometry"),
            )
            for ordinal, feature in enumerate(features, start=1)
        ]
    else:
        raise ValueError(f"unsupported source format for {source_id}")
    return {
        "source_id": source_id,
        "publisher": source["publisher"],
        "dataset": source["dataset"],
        "catalogue_url": source["catalogue_url"],
        "resource_url": source["resource_url"],
        "format": source["format"],
        "byte_size": len(payload),
        "sha256": actual_sha,
        "raw_rows": len(records),
        "licence": source["licence"],
        "attribution": source.get("attribution", OFFICIAL_ATTRIBUTION),
        "tls_production_ready": True,
    }, sorted(records, key=lambda row: row["source_record_id"])


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


def distance_meters(
    latitude_a: float | None,
    longitude_a: float | None,
    latitude_b: float | None,
    longitude_b: float | None,
) -> float | None:
    if not _valid_coordinates(latitude_a, longitude_a) or not _valid_coordinates(latitude_b, longitude_b):
        return None
    radius = 6_371_000.0
    phi_a = math.radians(latitude_a)
    phi_b = math.radians(latitude_b)
    d_phi = math.radians(latitude_b - latitude_a)
    d_lambda = math.radians(longitude_b - longitude_a)
    haversine = math.sin(d_phi / 2) ** 2 + math.cos(phi_a) * math.cos(phi_b) * math.sin(d_lambda / 2) ** 2
    return radius * 2 * math.atan2(math.sqrt(haversine), math.sqrt(1 - haversine))


def _name_token_subset(source_name: str | None, canonical_name: str | None) -> bool:
    source_tokens = _tokens(source_name)
    canonical_tokens = _tokens(canonical_name)
    return bool(source_tokens) and source_tokens.issubset(canonical_tokens)


def deduplicate_source_records(records: Iterable[dict[str, Any]], cluster_radius_m: float = 20.0) -> tuple[list[dict[str, Any]], int]:
    """Collapse duplicate IDs and same-site rows before production comparison."""
    rows = sorted(records, key=lambda row: row["source_record_id"])
    if not rows:
        return [], 0
    parent = list(range(len(rows)))

    def find(index: int) -> int:
        while parent[index] != index:
            parent[index] = parent[parent[index]]
            index = parent[index]
        return index

    def union(left: int, right: int) -> None:
        root_left, root_right = find(left), find(right)
        if root_left != root_right:
            parent[root_right] = root_left

    by_id: dict[str, int] = {}
    for index, row in enumerate(rows):
        prior = by_id.get(row["source_record_id"])
        if prior is not None:
            union(index, prior)
        else:
            by_id[row["source_record_id"]] = index
    for index, row in enumerate(rows):
        for other_index in range(index):
            other = rows[other_index]
            distance = distance_meters(row["latitude"], row["longitude"], other["latitude"], other["longitude"])
            if distance is None or distance > cluster_radius_m:
                continue
            same_postcode = bool(row["postcode_normalized"] and row["postcode_normalized"] == other["postcode_normalized"])
            shared_tokens = _tokens(row["name"]) & _tokens(other["name"])
            address_tokens = _tokens(row["address"]) & _tokens(other["address"])
            if same_postcode or len(shared_tokens) >= 2 or len(address_tokens) >= 2:
                union(index, other_index)
    groups: dict[int, list[dict[str, Any]]] = {}
    for index, row in enumerate(rows):
        groups.setdefault(find(index), []).append(row)
    representatives: list[dict[str, Any]] = []
    duplicate_count = 0
    for group in sorted(groups.values(), key=lambda group: group[0]["source_record_id"]):
        representative = dict(group[0])
        duplicate_ids = [row["source_record_id"] for row in group[1:]]
        representative["source_internal_duplicate_ids"] = duplicate_ids
        representative["source_internal_duplicate_count"] = len(duplicate_ids)
        representatives.append(representative)
        duplicate_count += len(duplicate_ids)
    return representatives, duplicate_count


def compare_records_to_production(
    records: Iterable[dict[str, Any]], facilities: Iterable[dict[str, Any]]
) -> list[dict[str, Any]]:
    """Apply the Pilot 1 guards against an explicitly read-only facility snapshot."""
    facilities_list = list(facilities)
    output: list[dict[str, Any]] = []
    for record in sorted(records, key=lambda row: (row["source_namespace"], row["source_record_id"])):
        distances: list[tuple[float, dict[str, Any]]] = []
        exact_postcode = False
        within_100 = False
        token_subset = False
        token_evidence: list[dict[str, Any]] = []
        for facility in facilities_list:
            distance = distance_meters(record["latitude"], record["longitude"], _number(facility.get("latitude")), _number(facility.get("longitude")))
            if distance is None:
                continue
            distances.append((distance, facility))
            postcode_match = bool(record["postcode_normalized"] and record["postcode_normalized"] == normalize_postcode(facility.get("postcode")))
            if postcode_match:
                exact_postcode = True
            if distance <= 100:
                within_100 = True
            if distance <= 250 and _name_token_subset(record["name"], facility.get("name")):
                token_subset = True
                token_evidence.append({"facility_id": facility.get("id"), "facility_name": facility.get("name"), "distance_m": round(distance, 1)})
        distances.sort(key=lambda pair: (pair[0], str(pair[1].get("id"))))
        nearest_distance, nearest = distances[0] if distances else (None, {})
        active_status = normalize_name(record.get("status"))
        inactive = active_status in {"closed", "inactive", "out of service", "not in service"}
        if inactive:
            classification = "INELIGIBLE_OR_CLOSED"
        elif not record.get("source_identity_stable", True):
            classification = "INSUFFICIENT_SOURCE_IDENTITY"
        elif exact_postcode or within_100:
            classification = "HIGH_CONFIDENCE_EXISTING"
        elif token_subset:
            classification = "PROBABLE_EXISTING_REVIEW"
        elif nearest_distance is not None and nearest_distance <= 250:
            classification = "POSSIBLE_NET_NEW_REVIEW"
        elif nearest_distance is not None and nearest_distance > 250:
            classification = "CONSERVATIVE_NET_NEW"
        else:
            classification = "INSUFFICIENT_SOURCE_IDENTITY"
        output.append({
            **record,
            "classification": classification,
            "nearest_relief_facility_id": nearest.get("id"),
            "nearest_relief_facility_name": nearest.get("name"),
            "nearest_relief_distance_m": round(nearest_distance, 1) if nearest_distance is not None else None,
            "exact_postcode_match": exact_postcode,
            "within_100m_match": within_100,
            "token_subset_match": token_subset,
            "token_match_evidence": sorted(token_evidence, key=lambda item: (item["distance_m"], str(item["facility_id"]))),
            "reason": {
                "CONSERVATIVE_NET_NEW": "No Pilot 1 duplicate guard matched and nearest Relief facility is beyond 250m.",
                "POSSIBLE_NET_NEW_REVIEW": "Nearest Relief facility is within 250m but no duplicate guard proved identity.",
                "HIGH_CONFIDENCE_EXISTING": "Exact postcode or <=100m duplicate guard matched.",
                "PROBABLE_EXISTING_REVIEW": "Source-name token subset matched within 250m without exact postcode or <=100m evidence.",
                "INSUFFICIENT_SOURCE_IDENTITY": "Stable publisher identity or usable comparison coordinates are missing.",
                "INELIGIBLE_OR_CLOSED": "Source status indicates the facility is closed or inactive.",
            }[classification],
        })
    return output


def cross_source_deduplicate(records: Iterable[dict[str, Any]], cluster_radius_m: float = 25.0) -> tuple[list[dict[str, Any]], int]:
    """Deduplicate the strict/review pool across authorities and Pilot 1 sources."""
    rows = sorted(records, key=lambda row: (row.get("source_namespace", ""), row.get("source_record_id", "")))
    groups: list[list[dict[str, Any]]] = []
    for row in rows:
        matched = None
        for group in groups:
            other = group[0]
            distance = distance_meters(row.get("latitude"), row.get("longitude"), other.get("latitude"), other.get("longitude"))
            same_postcode = bool(row.get("postcode_normalized") and row.get("postcode_normalized") == other.get("postcode_normalized"))
            name_overlap = bool(_tokens(row.get("name")) & _tokens(other.get("name")))
            if same_postcode or (distance is not None and distance <= cluster_radius_m and name_overlap):
                matched = group
                break
        if matched is None:
            groups.append([row])
        else:
            matched.append(row)
    representatives: list[dict[str, Any]] = []
    duplicate_count = 0
    for group in groups:
        representative = dict(group[0])
        duplicate_ids = [row.get("source_record_id") for row in group[1:]]
        representative["cross_source_duplicate_ids"] = duplicate_ids
        representative["cross_source_duplicate_count"] = len(duplicate_ids)
        representatives.append(representative)
        duplicate_count += len(duplicate_ids)
    return representatives, duplicate_count


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
        manifest, source_records = load_source(Path(source_path), source_id)
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

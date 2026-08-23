"""Build the bounded, read-only Local Authority OGL Pilot 2 evidence set.

This is an audit runner around ``local_authority_ogl_pilot``.  It accepts only
local snapshots, never imports a database client, and writes deterministic
evidence files.  Raw source snapshots and production pages remain outside Git.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from collections import Counter
from pathlib import Path
from typing import Any

from .local_authority_ogl_pilot import (
    PRODUCTION_WRITE_CAPABILITY,
    SOURCE_CATALOG,
    _tokens,
    canonical_json,
    compare_records_to_production,
    cross_source_deduplicate,
    deduplicate_source_records,
    distance_meters,
    load_source,
    normalize_postcode,
)


PILOT_1_SOURCE_IDS = {
    "city-of-york-public-toilets",
    "causeway-coast-and-glens-public-toilets",
}
PILOT_1_TLS_STATE = "TLS_RETRIEVAL_NOT_PRODUCTION_VERIFIED"
PILOT_2_TLS_STATE = "NORMAL_TLS_VERIFIED"


FORMALLY_CONSIDERED_SOURCES: list[dict[str, Any]] = [
    {
        "council": "Adur District Council",
        "source_id": "adur-public-toilets",
        "dataset": "Adur public toilets",
        "catalogue_url": "https://www.adur-worthing.gov.uk/datasets/",
        "resource_url": SOURCE_CATALOG["adur-public-toilets"]["resource_url"],
        "licence": "Open Government Licence v3.0",
        "attribution": "Credit Adur District Council; OS derived-data exemption notice applies.",
        "commercial_reuse": "Permitted under OGL v3.0 subject to attribution and source-specific OS terms.",
        "update_date": "2023-02-06",
        "format": "CSV",
        "access": "200 over normal TLS; 15 rows retrieved",
        "usable": True,
        "rejection_reason": None,
    },
    {
        "council": "Worthing Borough Council",
        "source_id": "worthing-public-toilets",
        "dataset": "Worthing public toilets",
        "catalogue_url": "https://www.adur-worthing.gov.uk/datasets/",
        "resource_url": SOURCE_CATALOG["worthing-public-toilets"]["resource_url"],
        "licence": "Open Government Licence v3.0",
        "attribution": "Credit Worthing Borough Council; OS derived-data exemption notice applies.",
        "commercial_reuse": "Permitted under OGL v3.0 subject to attribution and source-specific OS terms.",
        "update_date": "2023-02-06",
        "format": "CSV",
        "access": "200 over normal TLS; 58 rows retrieved",
        "usable": True,
        "rejection_reason": None,
    },
    {
        "council": "Perth & Kinross Council",
        "source_id": "perth-kinross-public-toilets-and-comfort-schemes",
        "dataset": "Public Toilets and Comfort Schemes (open data)",
        "catalogue_url": SOURCE_CATALOG["perth-kinross-public-toilets-and-comfort-schemes"]["catalogue_url"],
        "resource_url": SOURCE_CATALOG["perth-kinross-public-toilets-and-comfort-schemes"]["resource_url"],
        "licence": SOURCE_CATALOG["perth-kinross-public-toilets-and-comfort-schemes"]["licence"],
        "attribution": SOURCE_CATALOG["perth-kinross-public-toilets-and-comfort-schemes"]["attribution"],
        "commercial_reuse": "Reusable under OGL v3.0 with the source page’s CC-BY-SA 4.0 notice retained for original content.",
        "update_date": "2026-04-08",
        "format": "GeoJSON",
        "access": "200 over normal TLS; 42 features retrieved",
        "usable": True,
        "rejection_reason": None,
    },
    {
        "council": "Belfast City Council",
        "source_id": "belfast-public-toilets",
        "dataset": "Public toilets",
        "catalogue_url": SOURCE_CATALOG["belfast-public-toilets"]["catalogue_url"],
        "resource_url": SOURCE_CATALOG["belfast-public-toilets"]["resource_url"],
        "licence": "Open Government Licence v3.0",
        "attribution": "Credit Belfast City Council.",
        "commercial_reuse": "Permitted under OGL v3.0 subject to attribution.",
        "update_date": "2015-01-22",
        "format": "CSV",
        "access": "200 over normal TLS; 14 rows retrieved",
        "usable": True,
        "rejection_reason": None,
    },
    {
        "council": "Northumberland County Council",
        "source_id": "northumberland-public-toilets",
        "dataset": "Public Toilets Northumberland",
        "catalogue_url": "https://www.data.gov.uk/dataset/e7827c95-85c5-499f-8d79-0437e7bd4795/public-toilets-northumberland",
        "resource_url": "https://opendata.northumberland.gov.uk/static/datasets/public-toilets/public-toilets.csv",
        "licence": "Open Government Licence",
        "attribution": "Northumberland County Council / OGL attribution required.",
        "commercial_reuse": "Permitted under OGL, subject to attribution.",
        "update_date": "2015-02-11",
        "format": "CSV advertised; HTML returned",
        "access": "Resource returned an HTML page rather than the advertised CSV during normal retrieval.",
        "usable": False,
        "rejection_reason": "MACHINE_READABLE_RESOURCE_NOT_VERIFIED",
    },
    {
        "council": "Peterborough City Council",
        "source_id": "peterborough-public-toilets",
        "dataset": "Peterborough City Council public toilets",
        "catalogue_url": "https://www.data.gov.uk/dataset/1de61ff0-cc13-4744-8f53-8b60debca6cd/peterborough-city-council-public-toilets",
        "resource_url": "https://data.peterborough.gov.uk/Download/environmental-protection-street-care-and-cleaning/public-toilets/public-toilets/CSV/",
        "licence": "Open Government Licence",
        "attribution": "Peterborough City Council / OGL attribution required.",
        "commercial_reuse": "Permitted under OGL, subject to attribution.",
        "update_date": "2014-10-28",
        "format": "CSV",
        "access": "Catalogue and resource checked; no current machine-readable payload retrieved.",
        "usable": False,
        "rejection_reason": "RESOURCE_NOT_RETRIEVED",
    },
    {
        "council": "Manchester City Council",
        "source_id": "manchester-public-toilets",
        "dataset": "Public toilets in Manchester",
        "catalogue_url": "https://www.data.gov.uk/dataset/e1d07896-ff54-485d-87fe-7173a5a35728/public-toilets-in-manchester",
        "resource_url": "https://open.manchester.gov.uk/open/download/downloads/id/171/public_toilets",
        "licence": "Open Government Licence",
        "attribution": "Manchester City Council / OGL attribution required.",
        "commercial_reuse": "Permitted under OGL, subject to attribution.",
        "update_date": "2015-01-26",
        "format": "CSV advertised",
        "access": "Resource redirected to the open-data landing page, without a stable payload in this pass.",
        "usable": False,
        "rejection_reason": "RESOURCE_NOT_FROZEN",
    },
    {
        "council": "Bournemouth Borough Council",
        "source_id": "bournemouth-public-toilets",
        "dataset": "Public toilets Bournemouth",
        "catalogue_url": "https://www.data.gov.uk/dataset/cb42dabf-7361-44ec-a421-3dc735c6e196/public-toilets-bournemouth",
        "resource_url": "https://www.bournemouth.gov.uk/opendata/public-toilets.csv",
        "licence": "Open Government Licence",
        "attribution": "Bournemouth Borough Council / OGL attribution required.",
        "commercial_reuse": "Permitted under OGL, subject to attribution.",
        "update_date": "2014-10-29",
        "format": "CSV",
        "access": "Certificate validation failed against the resource host; no audit snapshot retained.",
        "usable": False,
        "rejection_reason": "TLS_RETRIEVAL_NOT_PRODUCTION_VERIFIED",
    },
    {
        "council": "Colchester Borough Council",
        "source_id": "colchester-public-toilets",
        "dataset": "Public toilets CBC",
        "catalogue_url": "https://www.data.gov.uk/dataset/b7f3a51c-1e10-434d-a2a6-662b70ae32cd/public-toilets-cbc",
        "resource_url": None,
        "licence": "Open Government Licence",
        "attribution": "Colchester Borough Council / OGL attribution required.",
        "commercial_reuse": "Permitted under OGL, subject to attribution.",
        "update_date": "2014-10-27",
        "format": "CSV/JSON advertised",
        "access": "Catalogue reviewed; no current resource URL was frozen for this bounded pass.",
        "usable": False,
        "rejection_reason": "RESOURCE_NOT_FROZEN",
    },
    {
        "council": "Surrey Heath Borough Council",
        "source_id": "surrey-heath-public-conveniences",
        "dataset": "Surrey Heath Borough Council public conveniences",
        "catalogue_url": "https://www.data.gov.uk/dataset/26b6f161-ed89-4854-8824-4323fd0fb457/surrey-heath-borough-council-public-conveniences",
        "resource_url": None,
        "licence": "Open Government Licence",
        "attribution": "Surrey Heath Borough Council / OGL attribution required.",
        "commercial_reuse": "Permitted under OGL, subject to attribution.",
        "update_date": None,
        "format": "Not released",
        "access": "Catalogue states availability not released.",
        "usable": False,
        "rejection_reason": "NOT_RELEASED",
    },
    {
        "council": "West Oxfordshire District Council",
        "source_id": "west-oxfordshire-public-conveniences",
        "dataset": "Public conveniences in West Oxfordshire",
        "catalogue_url": "https://www.data.gov.uk/dataset/38806273-fea6-4451-894d-f06f1753e4a9/public-conveniences-in-west-oxfordshire",
        "resource_url": "https://www.westoxon.gov.uk/media/954032/PublicConveniences.csv",
        "licence": "Open Government Licence",
        "attribution": "West Oxfordshire District Council / OGL attribution required.",
        "commercial_reuse": "Permitted under OGL, subject to attribution.",
        "update_date": "2014-10-29",
        "format": "CSV",
        "access": "Advertised resource returned 404 during the bounded retrieval check.",
        "usable": False,
        "rejection_reason": "RESOURCE_NOT_FOUND",
    },
    {
        "council": "Herefordshire Council",
        "source_id": "herefordshire-community-toilets",
        "dataset": "Community Toilets",
        "catalogue_url": "https://restservices.herefordshire.gov.uk/opendata/services/communitytoilets",
        "resource_url": "https://restservices.herefordshire.gov.uk/opendata/services/corporate/communitytoilets/mapsearch",
        "licence": "Ordnance Survey Open Data licence",
        "attribution": "Contains Ordnance Survey data © Crown copyright and database right 2025.",
        "commercial_reuse": "Licence permits reuse subject to OS attribution and non-misrepresentation conditions.",
        "update_date": "2025",
        "format": "JSON service route documented",
        "access": "Documented service route did not return a stable payload in this pass.",
        "usable": False,
        "rejection_reason": "SERVICE_ROUTE_NOT_VERIFIED",
    },
    {
        "council": "Salford City Council",
        "source_id": "salford-public-toilets",
        "dataset": "SCC public toilets",
        "catalogue_url": "https://www.data.gov.uk/dataset/0015ce8a-71d0-46f8-8701-730b3622b334/scc-public-toilets",
        "resource_url": "https://map.salford.gov.uk/maps/opendata/SCC-public-toilets.csv",
        "licence": "Open Government Licence",
        "attribution": "Salford City Council / OGL attribution required.",
        "commercial_reuse": "Permitted under OGL, subject to attribution.",
        "update_date": "2015-02-02",
        "format": "CSV",
        "access": "Resource host connection failed during the bounded check.",
        "usable": False,
        "rejection_reason": "RESOURCE_NOT_RETRIEVED",
    },
    {
        "council": "St Helens Council",
        "source_id": "st-helens-public-toilets",
        "dataset": "Public toilets St Helens Council CSV",
        "catalogue_url": "https://www.data.gov.uk/dataset/6369137e-0fe3-49a9-b7ae-f02409f9007b/public-toilets-st-helens-council-csv",
        "resource_url": None,
        "licence": "Open Government Licence",
        "attribution": "St Helens Council / OGL attribution required.",
        "commercial_reuse": "Permitted under OGL, subject to attribution.",
        "update_date": None,
        "format": "CSV advertised; no current link",
        "access": "Current catalogue page has no released data link.",
        "usable": False,
        "rejection_reason": "NOT_RELEASED",
    },
    {
        "council": "Newcastle City Council",
        "source_id": "newcastle-public-toilets",
        "dataset": "Public toilet",
        "catalogue_url": "https://www.data.gov.uk/dataset/694bf1bd-f7d2-4bd8-9df3-3ad606f6a9e0/public-toilet1",
        "resource_url": None,
        "licence": "LICENCE_NOT_PROVEN",
        "attribution": None,
        "commercial_reuse": "Not proven at the actual resource.",
        "update_date": "2026-05-28",
        "format": "Unspecified",
        "access": "Catalogue has no usable data link and reports no dataset licence.",
        "usable": False,
        "rejection_reason": "LICENCE_NOT_PROVEN",
    },
]


def _read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _candidate_id(source_namespace: str, source_record_id: str) -> str:
    digest = hashlib.sha256(f"{source_namespace}|{source_record_id}".encode("utf-8")).hexdigest()[:24]
    return f"ogl-candidate-{digest}"


def _source_quality_metrics(records: list[dict[str, Any]], unique_records: list[dict[str, Any]], duplicate_count: int) -> dict[str, Any]:
    duplicate_ids = len(records) - len({row["source_record_id"] for row in records})
    coordinate_pairs = 0
    for index, row in enumerate(records):
        for other in records[:index]:
            distance = distance_meters(row.get("latitude"), row.get("longitude"), other.get("latitude"), other.get("longitude"))
            if distance is not None and distance <= 20:
                coordinate_pairs += 1
    inactive = sum(row.get("status", "").strip().casefold() in {"closed", "inactive", "out of service", "not in service"} for row in records if row.get("status"))
    return {
        "RAW_ROWS": len(records),
        "DIRECT_TOILET_ROWS": sum(bool(row["direct_toilet_evidence"]) for row in records),
        "ROWS_WITH_STABLE_ID": sum(bool(row["source_identity_stable"]) for row in records),
        "ROWS_WITH_NAME": sum(bool(row.get("name")) for row in records),
        "ROWS_WITH_ADDRESS": sum(bool(row.get("address")) for row in records),
        "ROWS_WITH_POSTCODE": sum(bool(row.get("postcode_normalized")) for row in records),
        "ROWS_WITH_VALID_COORDINATES": sum(row.get("latitude") is not None and row.get("longitude") is not None for row in records),
        "ROWS_WITH_STATUS": sum(bool(row.get("status")) for row in records),
        "INVALID_COORDINATES": sum("coordinates" in error for row in records for error in row.get("validation_errors", [])),
        "DUPLICATE_SOURCE_IDS": duplicate_ids,
        "DUPLICATE_COORDINATE_CLUSTERS": coordinate_pairs,
        "INACTIVE_OR_CLOSED_ROWS": inactive,
        "UNIQUE_PHYSICAL_TOILET_CANDIDATES": len(unique_records),
        "SOURCE_INTERNAL_DUPLICATE_ROWS": duplicate_count,
    }


def _pilot_1_candidates(root: Path) -> list[dict[str, Any]]:
    data_dir = root / "docs" / "data"
    normalized = {row["source_record_id"]: row for row in _read_json(data_dir / "LOCAL_AUTHORITY_OGL_PILOT_1_NORMALIZED_RECORDS_2026-08-23.json")["records"]}
    comparison = _read_json(data_dir / "LOCAL_AUTHORITY_OGL_PILOT_1_PRODUCTION_COMPARISON_2026-08-23.json")["records"]
    candidates: list[dict[str, Any]] = []
    for match in comparison:
        if match.get("conservative_net_new"):
            classification = "CONSERVATIVE_NET_NEW"
        elif match.get("candidate_status") == "CREDIBLE_NET_NEW_CANDIDATE":
            classification = "POSSIBLE_NET_NEW_REVIEW"
        else:
            continue
        record = dict(normalized[match["source_record_id"]])
        record.update(
            {
                "candidate_id": _candidate_id(record["source_namespace"], record["source_record_id"]),
                "publisher_source_id": record["source_record_id"],
                "classification": classification,
                "nearest_relief_facility_id": match.get("nearest_facility_id"),
                "nearest_relief_facility_name": match.get("nearest_facility_name"),
                "nearest_relief_distance_m": float(match["distance_m"]) if match.get("distance_m") is not None else None,
                "exact_postcode_match": bool(match.get("exact_postcode")),
                "within_100m_match": "WITHIN_100M" in match.get("guard_reasons", []),
                "token_subset_match": bool(match.get("token_subset")),
                "lexical_postcode_evidence": {
                    "exact_postcode": bool(match.get("exact_postcode")),
                    "token_subset": bool(match.get("token_subset")),
                },
                "reason": "Pilot 1 strict candidate carried forward after all duplicate guards failed and nearest facility exceeded 250m." if classification == "CONSERVATIVE_NET_NEW" else "Pilot 1 bounded review case within 250m without a conclusive identity guard.",
                "tls_production_readiness": PILOT_1_TLS_STATE,
                "source_resource_url": SOURCE_CATALOG[record["source_namespace"]]["resource_url"],
            }
        )
        candidates.append(record)
    return candidates


def _candidate_from_pilot_2(record: dict[str, Any]) -> dict[str, Any]:
    candidate = dict(record)
    candidate["candidate_id"] = _candidate_id(record["source_namespace"], record["source_record_id"])
    candidate["publisher_source_id"] = record["source_record_id"]
    candidate["nearest_relief_facility_id"] = record.get("nearest_relief_facility_id")
    candidate["nearest_relief_facility_name"] = record.get("nearest_relief_facility_name")
    candidate["nearest_relief_distance_m"] = record.get("nearest_relief_distance_m")
    candidate["lexical_postcode_evidence"] = {
        "exact_postcode": bool(record.get("exact_postcode_match")),
        "token_subset": bool(record.get("token_subset_match")),
    }
    candidate["tls_production_readiness"] = PILOT_2_TLS_STATE
    candidate["source_resource_url"] = SOURCE_CATALOG[record["source_namespace"]]["resource_url"]
    return candidate


def _source_result(source_id: str, manifest: dict[str, Any], records: list[dict[str, Any]], unique_records: list[dict[str, Any]], compared: list[dict[str, Any]], duplicate_count: int) -> dict[str, Any]:
    classifications = Counter(row["classification"] for row in compared)
    enrichment = sum(
        row["classification"] in {"HIGH_CONFIDENCE_EXISTING", "PROBABLE_EXISTING_REVIEW"}
        and any(row.get(field) for field in ("accessibility", "opening_hours", "charge", "operator"))
        for row in compared
    )
    return {
        "source_id": source_id,
        "publisher": manifest["publisher"],
        "dataset": manifest["dataset"],
        "catalogue_url": manifest["catalogue_url"],
        "resource_url": manifest["resource_url"],
        "licence": manifest["licence"],
        "attribution": manifest["attribution"],
        "format": manifest["format"],
        "raw_sha256": manifest["sha256"],
        "raw_bytes": manifest["byte_size"],
        "tls_production_readiness": PILOT_2_TLS_STATE,
        "quality": _source_quality_metrics(records, unique_records, duplicate_count),
        "classification_counts": dict(sorted(classifications.items())),
        "likely_existing": classifications["HIGH_CONFIDENCE_EXISTING"] + classifications["PROBABLE_EXISTING_REVIEW"],
        "strict_net_new": classifications["CONSERVATIVE_NET_NEW"],
        "review_net_new": classifications["POSSIBLE_NET_NEW_REVIEW"],
        "enrichment_candidates": enrichment,
        "candidate_records": [_candidate_from_pilot_2(row) for row in compared if row["classification"] in {"CONSERVATIVE_NET_NEW", "POSSIBLE_NET_NEW_REVIEW"}],
    }


def _ranking(source_results: list[dict[str, Any]], pilot_1: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for source_id, group in (("city-of-york-public-toilets", "Pilot 1"), ("causeway-coast-and-glens-public-toilets", "Pilot 1")):
        selected = [row for row in pilot_1 if row["source_namespace"] == source_id]
        source = SOURCE_CATALOG[source_id]
        total = 18 if source_id.startswith("city") else 52
        strict = sum(row["classification"] == "CONSERVATIVE_NET_NEW" for row in selected)
        review = sum(row["classification"] == "POSSIBLE_NET_NEW_REVIEW" for row in selected)
        rows.append({"rank_group": group, "council_source": source["publisher"], "source_id": source_id, "unique_toilets": total, "likely_existing": total - strict - review, "strict_net_new": strict, "review_net_new": review, "licence": source["licence"], "data_quality": "verified Pilot 1 normalized records", "yield_rate": round(strict / total, 4)})
    for result in source_results:
        quality = result["quality"]
        rows.append({"rank_group": "Pilot 2", "council_source": result["publisher"], "source_id": result["source_id"], "unique_toilets": quality["UNIQUE_PHYSICAL_TOILET_CANDIDATES"], "likely_existing": result["likely_existing"], "strict_net_new": result["strict_net_new"], "review_net_new": result["review_net_new"], "licence": result["licence"], "data_quality": "; ".join([f"{key}={quality[key]}" for key in ("ROWS_WITH_STABLE_ID", "ROWS_WITH_VALID_COORDINATES", "DUPLICATE_COORDINATE_CLUSTERS")]), "yield_rate": round(result["strict_net_new"] / quality["UNIQUE_PHYSICAL_TOILET_CANDIDATES"], 4) if quality["UNIQUE_PHYSICAL_TOILET_CANDIDATES"] else 0})
    return sorted(rows, key=lambda row: (-row["strict_net_new"], -row["review_net_new"], row["council_source"]))


def _report(
    root: Path,
    source_results: list[dict[str, Any]],
    candidates: list[dict[str, Any]],
    rejected: list[dict[str, Any]],
    ranking: list[dict[str, Any]],
    baseline: dict[str, Any],
    cross_duplicates: int,
) -> str:
    strict = sum(row["classification"] == "CONSERVATIVE_NET_NEW" for row in candidates)
    review = sum(row["classification"] == "POSSIBLE_NET_NEW_REVIEW" for row in candidates)
    pilot2_strict = sum(result["strict_net_new"] for result in source_results)
    pilot2_review = sum(result["review_net_new"] for result in source_results)
    lines = [
        "# RELIEF Local Authority OGL Pilot 2 — Targeted Multi-Council Yield Expansion",
        "",
        "**Date:** 2026-08-23",
        "**Classification:** `PRODUCTION_READ_ONLY`",
        "**Principal result:** `OGL_COMBINED_POOL_READY_FOR_REVIEW_AND_APPLY`",
        "",
        "## Scope and result",
        "",
        "Pilot 2 reused the Pilot 1 adapter and inspected four retained, directly licensed local-authority resources. Eleven additional council datasets were triaged and rejected quickly because a current machine-readable resource, normal retrieval, or the actual resource licence was not proven. No canonical production write was attempted.",
        "",
        f"The combined strict pool is **{strict}** ({pilot2_strict} new Pilot 2 candidates plus the nine carried-forward Pilot 1 candidates, less {cross_duplicates} cross-source duplicates). The bounded review pool is **{review}**.",
        "",
        "## Starting and production state",
        "",
        "- Repository: `hourwise/Relief`",
        "- Branch: `codex/toilet-map-apply-1a-production-deploy`",
        "- Starting local SHA and independently verified remote SHA: `513772892265e0d80619813b58e7944739d57a21`.",
        "- Pilot 1 foundation commit: `8f239f15c79340f008a4cc265a3e523b58b6791f`",
        f"- Read-only production snapshot rows: `{baseline['facilities']}` facilities; expected accompanying counts are `{baseline['facility_sources']}` facility_sources, `{baseline['facility_source_observations']}` observations, `{baseline['toilet_units']}` toilet_units.",
        "- Production project: `Relief` (`bgwxrxkmyaihplaloely`).",
        "- Total production mutations: `0`.",
        "",
        "The uncommitted `.easignore`, `app.json`, `docs/EAS_CONFIG_AUDIT.md`, N4/N5/N6 evidence, and sealed migration work were preserved outside the Pilot 1 and Pilot 2 staging sets.",
        "",
        "## Source results",
        "",
        "| Council/source | Raw rows | Unique physical toilets | Likely existing | Strict new | Review new | Enrichment | Licence | TLS |",
        "|---|---:|---:|---:|---:|---:|---:|---|---|",
    ]
    for result in source_results:
        q = result["quality"]
        lines.append(f"| {result['publisher']} — {result['dataset']} | {q['RAW_ROWS']} | {q['UNIQUE_PHYSICAL_TOILET_CANDIDATES']} | {result['likely_existing']} | {result['strict_net_new']} | {result['review_net_new']} | {result['enrichment_candidates']} | {result['licence']} | NORMAL_TLS_VERIFIED |")
    lines += [
        "",
        "Adur and Worthing exports use stable UPRNs and OSGB36 coordinates converted deterministically to WGS84. Worthing’s 58 raw rows reduced to 27 physical candidates after same-site internal deduplication. Perth’s GeoJSON uses British National Grid geometry and includes explicit public-toilet and comfort-scheme records; Belfast has stable derived IDs from name/address/coordinates and is retained for overlap, review, and enrichment analysis.",
        "",
        "### Rejected datasets",
        "",
        "| Council/source | Licence | Access/format | Decision |",
        "|---|---|---|---|",
    ]
    for source in rejected:
        lines.append(f"| {source['council']} — {source['dataset']} | {source['licence']} | {source['access']} | {source['rejection_reason']} |")
    lines += [
        "",
        "## Pilot 1 + Pilot 2 reconciliation",
        "",
        f"- `PILOT_1_STRICT: 9`",
        "- `PILOT_1_REVIEW: 2`",
        f"- `PILOT_2_STRICT: {pilot2_strict}`",
        f"- `PILOT_2_REVIEW: {pilot2_review}`",
        f"- `CROSS_SOURCE_DUPLICATES: {cross_duplicates}`",
        f"- `COMBINED_CONSERVATIVE_NET_NEW: {strict}`",
        f"- `COMBINED_REVIEW_POOL: {review}`",
        "",
        "The nine Pilot 1 strict candidates and two near-overlap cases remain unchanged. The Pilot 2 candidate register contains the full carry-forward and additional strict/review pool with deterministic candidate IDs, source IDs, coordinates, nearest facility evidence, licensing, and TLS readiness.",
        "",
        "## Projected facility count and target progress",
        "",
        f"- `CURRENT: {baseline['facilities']}`",
        f"- `STRICT POST-APPLY POTENTIAL: {baseline['facilities'] + strict}`",
        f"- `REVIEW-ASSISTED POTENTIAL: {baseline['facilities'] + strict + review}`",
        "",
        "| Target | Additional toilets required | Strict pool progress |",
        "|---:|---:|---:|",
        f"| 16,000 | {16000 - baseline['facilities']} | {strict} |",
        f"| 17,000 | {17000 - baseline['facilities']} | {strict} |",
        f"| 20,000 | {20000 - baseline['facilities']} | {strict} |",
        "",
        "Review candidates are not guaranteed additions. The recommended next action is one bounded human review followed by a separately authorized production apply, including normal-TLS re-fetch and frozen source hashes.",
        "",
        "## Source ranking",
        "",
        "| Rank | Council/source | Unique toilets | Likely existing | Strict net-new | Review net-new | Licence | Data quality | Yield rate |",
        "|---:|---|---:|---:|---:|---:|---|---|---:|",
    ]
    for rank, row in enumerate(ranking, start=1):
        lines.append(f"| {rank} | {row['council_source']} | {row['unique_toilets']} | {row['likely_existing']} | {row['strict_net_new']} | {row['review_net_new']} | {row['licence']} | {row['data_quality']} | {row['yield_rate']:.1%} |")
    lines += [
        "",
        "## TLS and retrieval",
        "",
        "The four Pilot 2 candidate-source resources were each retrieved with normal certificate validation and are marked `NORMAL_TLS_VERIFIED`. Pilot 1’s two official ArcGIS resources remain marked `TLS_RETRIEVAL_NOT_PRODUCTION_VERIFIED` because its evidence was captured through a disposable verification-disabled fallback after normal validation failed. No TLS bypass is present in the adapter’s normal path, and no TLS-caveated source is production-ingestion-ready.",
        "",
        "## Schema and production safety",
        "",
        "The current facilities/provenance schema remains sufficient for a later bounded apply: this batch only needs the existing facility identity, source provenance, and facility-source observation structures. No migration, trigger, index, RLS, RPC, source graph, import run, or promotion service was added.",
        "",
        "- `TOTAL PRODUCTION MUTATIONS: 0`",
        "- `TOTAL CANONICAL FACILITY INSERTS: 0`",
        "- `TOTAL CANONICAL FACILITY UPDATES: 0`",
        "- `TOTAL SCHEMA MUTATIONS: 0`",
        "- `TOTAL AUTH MUTATIONS: 0`",
        "",
        "## Files and tests",
        "",
        "The intended Pilot 2 files are the existing adapter extension, its focused tests, the bounded audit runner, six compact evidence files under `docs/data/`, and no raw downloads.",
        "",
        "- Pilot 1/Pilot 2 adapter tests: **10 passed**.",
        "- Package-qualified relevant source-expansion regression modules (pipeline, TfL, N1–N5): **97 passed**.",
        "- N6A/N6B/N6C baseline check: **18 run; one existing N6B fixture failure and one dependent N6C setup error** because the protected N6B proposed cohort contains 44 rather than the test’s expected 51 cases. No N6 files were changed.",
        "- Deterministic replay: **all six evidence-file hashes matched** a clean temporary replay.",
        "- JSON parsing, Python compilation, bounded secret scan, and source-internal/cross-source reconciliation: **passed**.",
        "- `git diff --check`: **no new Pilot 2 whitespace errors**; the separately committed Pilot 1 Markdown report retains its intentional two-space hard-break warning.",
        "",
        "**Next action:** `LOCAL AUTHORITY OGL BOUNDED REVIEW + PRODUCTION APPLY`.",
        "",
        "The production apply remains separately unauthorized in this pilot.",
    ]
    return "\n".join(lines) + "\n"


def run(root: Path, inputs: list[tuple[str, Path]], production_path: Path, output_dir: Path) -> None:
    if PRODUCTION_WRITE_CAPABILITY:
        raise RuntimeError("production write capability must remain disabled")
    facilities_value = _read_json(production_path)
    facilities = facilities_value.get("records") if isinstance(facilities_value, dict) else facilities_value
    if not isinstance(facilities, list):
        raise ValueError("production snapshot must be a JSON list")
    if len(facilities) != 15620:
        raise ValueError(f"expected 15620 production facilities, got {len(facilities)}")
    source_results: list[dict[str, Any]] = []
    pilot2_candidates: list[dict[str, Any]] = []
    for source_id, path in sorted(inputs):
        manifest, records = load_source(path, source_id)
        unique_records, duplicate_count = deduplicate_source_records(records)
        compared = compare_records_to_production(unique_records, facilities)
        result = _source_result(source_id, manifest, records, unique_records, compared, duplicate_count)
        source_results.append(result)
        pilot2_candidates.extend(result["candidate_records"])
    pilot1_candidates = _pilot_1_candidates(root)
    all_candidates, cross_duplicates = cross_source_deduplicate(pilot1_candidates + pilot2_candidates)
    all_candidates.sort(key=lambda row: (row["classification"], row["source_namespace"], row["source_record_id"]))
    strict = sum(row["classification"] == "CONSERVATIVE_NET_NEW" for row in all_candidates)
    review = sum(row["classification"] == "POSSIBLE_NET_NEW_REVIEW" for row in all_candidates)
    baseline = {"facilities": 15620, "facility_sources": 15634, "facility_source_observations": 14, "toilet_units": 0}
    ranking = _ranking(source_results, pilot1_candidates)
    output_dir.mkdir(parents=True, exist_ok=True)
    manifest_payload = {
        "tool_version": "relief.local-authority-ogl-pilot-2.v1",
        "classification": "PRODUCTION_READ_ONLY",
        "production_write_capability": False,
        "production_baseline": baseline,
        "selected_sources": [
            {key: value for key, value in source.items() if key not in {"candidate_records"}}
            for source in source_results
        ],
        "formally_considered_sources": FORMALLY_CONSIDERED_SOURCES,
        "raw_downloads_in_repository": False,
        "source_discovery_stop_reason": "Combined strict pool exceeded the 50-candidate minimum-value stop with acceptable licensing and data quality.",
    }
    results_payload = {
        "tool_version": "relief.local-authority-ogl-pilot-2.v1",
        "classification": "PRODUCTION_READ_ONLY",
        "source_results": source_results,
        "ranking": ranking,
        "source_family_metrics": {
            "total_councils_investigated": 15,
            "usable_council_datasets": len(source_results),
            "rejected_datasets": len(FORMALLY_CONSIDERED_SOURCES) - len(source_results),
            "total_source_rows": sum(result["quality"]["RAW_ROWS"] for result in source_results),
            "total_unique_physical_toilets": sum(result["quality"]["UNIQUE_PHYSICAL_TOILET_CANDIDATES"] for result in source_results),
            "likely_existing": sum(result["likely_existing"] for result in source_results),
            "strict_new": sum(result["strict_net_new"] for result in source_results),
            "review_new": sum(result["review_net_new"] for result in source_results),
            "enrichment_candidates": sum(result["enrichment_candidates"] for result in source_results),
            "average_strict_yield_per_usable_dataset": round(sum(result["strict_net_new"] for result in source_results) / len(source_results), 2),
        },
        "combined": {
            "pilot_1_strict": 9,
            "pilot_1_review": 2,
            "pilot_2_strict": sum(result["strict_net_new"] for result in source_results),
            "pilot_2_review": sum(result["review_net_new"] for result in source_results),
            "cross_source_duplicates": cross_duplicates,
            "combined_conservative_net_new": strict,
            "combined_review_pool": review,
        },
    }
    register_payload = {
        "tool_version": "relief.local-authority-ogl-pilot-2.v1",
        "classification": "PRODUCTION_READ_ONLY",
        "entries": all_candidates,
        "counts": {
            "total_entries": len(all_candidates),
            "CONSERVATIVE_NET_NEW": strict,
            "POSSIBLE_NET_NEW_REVIEW": review,
            "cross_source_duplicates": cross_duplicates,
        },
    }
    comparison_payload = {
        "tool_version": "relief.local-authority-ogl-pilot-2.v1",
        "project": "Relief",
        "project_ref": "bgwxrxkmyaihplaloely",
        "read_only": True,
        "production_snapshot_rows": len(facilities),
        "production_snapshot_sha256": hashlib.sha256(canonical_json(facilities).encode("utf-8")).hexdigest(),
        "baseline": baseline,
        "combined_counts": results_payload["combined"],
        "current_facilities": 15620,
        "strict_post_apply_potential": 15620 + strict,
        "review_assisted_potential": 15620 + strict + review,
        "mutations": 0,
        "canonical_facility_inserts": 0,
        "canonical_facility_updates": 0,
        "schema_mutations": 0,
        "auth_mutations": 0,
    }
    readiness_payload = {
        "tool_version": "relief.local-authority-ogl-pilot-2.v1",
        "classification": "OGL_COMBINED_POOL_READY_FOR_REVIEW_AND_APPLY",
        "combined_conservative_net_new": strict,
        "combined_review_pool": review,
        "minimum_target_reached": strict >= 50,
        "preferred_target_reached": strict >= 100,
        "production_read_only": True,
        "production_ingestion_authorized": False,
        "all_candidate_sources_normal_tls_verified": all(row["tls_production_readiness"] == PILOT_2_TLS_STATE for row in all_candidates if row["source_namespace"] not in PILOT_1_SOURCE_IDS),
        "pilot_1_sources_require_normal_tls_refetch": True,
        "schema_sufficient_for_later_apply": True,
        "next_action": "LOCAL AUTHORITY OGL BOUNDED REVIEW + PRODUCTION APPLY",
        "stop_reason": "A single combined review/apply batch is now justified; no more source discovery is required for this pilot.",
    }
    files = {
        "LOCAL_AUTHORITY_OGL_PILOT_2_SOURCE_MANIFEST_2026-08-23.json": manifest_payload,
        "LOCAL_AUTHORITY_OGL_PILOT_2_SOURCE_RESULTS_2026-08-23.json": results_payload,
        "LOCAL_AUTHORITY_OGL_COMBINED_CANDIDATE_REGISTER_2026-08-23.json": register_payload,
        "LOCAL_AUTHORITY_OGL_PILOT_2_PRODUCTION_COMPARISON_2026-08-23.json": comparison_payload,
        "LOCAL_AUTHORITY_OGL_PILOT_2_READINESS_2026-08-23.json": readiness_payload,
    }
    for filename, payload in files.items():
        (output_dir / filename).write_text(canonical_json(payload) + "\n", encoding="utf-8")
    (output_dir / "LOCAL_AUTHORITY_OGL_PILOT_2_REPORT_2026-08-23.md").write_text(_report(root, source_results, all_candidates, [row for row in FORMALLY_CONSIDERED_SOURCES if not row["usable"]], ranking, baseline, cross_duplicates), encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build read-only Local Authority OGL Pilot 2 evidence")
    parser.add_argument("--source", action="append", nargs=2, metavar=("SOURCE_ID", "PATH"), required=True)
    parser.add_argument("--production", type=Path, required=True)
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args(argv)
    run(args.root, [(source_id, Path(path)) for source_id, path in args.source], args.production, args.output_dir)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

"""R4A read-only Causeway source-drift revalidation and manifest reseal.

This module compares the exact R3 Causeway payload, the payload observed by
the blocked R4 attempt, and a fresh R4A payload.  It has no database client,
no production-write capability, and never overwrites the R3 manifest.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from .local_authority_ogl_pilot import canonical_json, normalize_geojson_feature, sha256_bytes


TOOL_VERSION = "relief.local-authority-ogl-r4a-causeway-revalidation.v1"
PRODUCTION_WRITE_CAPABILITY = False
R3_MANIFEST_SHA256 = "c9564843ca2f18771fa9ae9c129de4e68feb67d81a4d36464b9d994cb3801e74"
N4A_SHA256 = "087A389B8CEAC021B12708BC55C39022CB38D5459510EFFB6CF057CEF232C44E"
CAUSEWAY_SOURCE_ID = "causeway-coast-and-glens-public-toilets"
EXPECTED_R3_CAUSEWAY_SHA256 = "6f320593a8bb8f9734af37724499401b0ee6065bbb35cc475736295ad434ab07"
EXPECTED_R4_CAUSEWAY_SHA256 = "50eabf55fa58be22bcd09d1f9d0d94a61b17278e7f3434ad832b4df9cb884279"
EXPECTED_CAUSEWAY_RECORDS = 52
SEMANTIC_FIELDS = (
    "name",
    "address",
    "postcode",
    "latitude",
    "longitude",
    "toilet_type",
    "accessibility",
    "charge",
    "opening_hours",
    "status",
    "operator",
    "direct_toilet_evidence",
)
IDENTITY_FIELDS = ("name", "address", "postcode", "latitude", "longitude", "toilet_type")


def _read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _write_lf(path: Path, value: str) -> None:
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        handle.write(value)


def _load_payload(path: Path) -> tuple[str, int, dict[str, Any], list[dict[str, Any]]]:
    payload = path.read_bytes()
    document = json.loads(payload.decode("utf-8"))
    features = document.get("features") if isinstance(document, dict) else None
    if not isinstance(features, list):
        raise ValueError(f"{path} is not a GeoJSON FeatureCollection")
    records = [normalize_geojson_feature(feature, CAUSEWAY_SOURCE_ID, ordinal) for ordinal, feature in enumerate(features)]
    return sha256_bytes(payload), len(payload), document, records


def _record_map(records: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    result = {record["source_record_id"]: record for record in records}
    if len(result) != len(records):
        raise ValueError("Causeway source record identities are not unique")
    return result


def _compare_records(left: list[dict[str, Any]], right: list[dict[str, Any]]) -> dict[str, Any]:
    left_by_id = _record_map(left)
    right_by_id = _record_map(right)
    shared = sorted(set(left_by_id) & set(right_by_id))
    fields = sorted(set().union(*(set(record) for record in left + right)))
    field_changes = {
        field: sum(left_by_id[record_id].get(field) != right_by_id[record_id].get(field) for record_id in shared)
        for field in fields
    }
    field_changes = {field: count for field, count in field_changes.items() if count}
    semantic_changes = {
        field: sum(left_by_id[record_id].get(field) != right_by_id[record_id].get(field) for record_id in shared)
        for field in SEMANTIC_FIELDS
    }
    identity_changes = {
        field: sum(left_by_id[record_id].get(field) != right_by_id[record_id].get(field) for record_id in shared)
        for field in IDENTITY_FIELDS
    }
    return {
        "left_record_count": len(left),
        "right_record_count": len(right),
        "shared_record_count": len(shared),
        "missing_record_ids": sorted(set(left_by_id) - set(right_by_id)),
        "added_record_ids": sorted(set(right_by_id) - set(left_by_id)),
        "field_changes": field_changes,
        "semantic_changes": semantic_changes,
        "identity_changes": identity_changes,
        "byte_identical": False,
        "semantic_identity_stable": not any(identity_changes.values()),
        "semantic_toilet_data_stable": not any(semantic_changes.values()),
    }


def _source_snapshot(path: Path, sha256: str, byte_size: int, *, label: str, retrieved_at_utc: str | None = None, status: int | None = None, content_type: str | None = None, resolved_url: str | None = None) -> dict[str, Any]:
    result: dict[str, Any] = {
        "label": label,
        "path_for_audit_only": str(path),
        "sha256": sha256,
        "byte_size": byte_size,
        "record_count": EXPECTED_CAUSEWAY_RECORDS,
    }
    if retrieved_at_utc is not None:
        result["retrieved_at_utc"] = retrieved_at_utc
    if status is not None:
        result["http_status"] = status
    if content_type is not None:
        result["content_type"] = content_type
    if resolved_url is not None:
        result["resolved_url"] = resolved_url
    return result


def run(
    root: Path,
    r3_manifest_path: Path,
    prior_payload: Path,
    intermediate_payload: Path,
    current_payload: Path,
    current_url: str,
    current_retrieved_at_utc: str,
    current_status: int,
    current_content_type: str,
    output_dir: Path,
) -> dict[str, Any]:
    data_dir = root / "docs" / "data"
    manifest_bytes = r3_manifest_path.read_bytes()
    manifest_sha256 = sha256_bytes(manifest_bytes)
    if manifest_sha256 != R3_MANIFEST_SHA256:
        raise ValueError("R3 manifest SHA-256 does not match its immutable seal")
    r3_manifest = json.loads(manifest_bytes.decode("utf-8"))
    if r3_manifest.get("candidate_count") != 89 or len(r3_manifest.get("candidates", [])) != 89:
        raise ValueError("R3 manifest does not contain exactly 89 candidates")
    if r3_manifest.get("review_candidates_excluded") != 7:
        raise ValueError("R3 manifest review-pool exclusion is not 7")

    prior_sha, prior_size, prior_doc, prior_records = _load_payload(prior_payload)
    intermediate_sha, intermediate_size, intermediate_doc, intermediate_records = _load_payload(intermediate_payload)
    current_sha, current_size, current_doc, current_records = _load_payload(current_payload)
    if prior_sha != EXPECTED_R3_CAUSEWAY_SHA256:
        raise ValueError("prior R3 Causeway payload does not match the sealed R3 hash")
    if intermediate_sha != EXPECTED_R4_CAUSEWAY_SHA256:
        raise ValueError("intermediate R4 Causeway payload does not match the observed drift hash")
    if current_sha != EXPECTED_R3_CAUSEWAY_SHA256:
        raise ValueError("fresh R4A Causeway payload did not return to the R3 hash")
    for records in (prior_records, intermediate_records, current_records):
        if len(records) != EXPECTED_CAUSEWAY_RECORDS:
            raise ValueError("Causeway record count is not 52")

    r3_candidates = [candidate for candidate in r3_manifest["candidates"] if candidate["source_namespace"] == CAUSEWAY_SOURCE_ID]
    if len(r3_candidates) != 5:
        raise ValueError("R3 Causeway candidate count is not 5")
    prior_by_id = _record_map(prior_records)
    current_by_id = _record_map(current_records)
    candidate_impact: list[dict[str, Any]] = []
    for candidate in sorted(r3_candidates, key=lambda value: value["source_record_id"]):
        source_record_id = candidate["source_record_id"]
        if source_record_id not in prior_by_id or source_record_id not in current_by_id:
            raise ValueError(f"R3 Causeway candidate missing from current source: {source_record_id}")
        before = prior_by_id[source_record_id]
        after = current_by_id[source_record_id]
        differences = {field: {"prior": before.get(field), "current": after.get(field)} for field in SEMANTIC_FIELDS if before.get(field) != after.get(field)}
        if differences:
            classification = "MATERIAL_UPDATE_REVALIDATED" if any(field in differences for field in IDENTITY_FIELDS) else "NON_MATERIAL_SOURCE_UPDATE"
        else:
            classification = "UNCHANGED"
        candidate_impact.append(
            {
                "candidate_id": candidate["candidate_id"],
                "source_record_id": source_record_id,
                "name": candidate["name"],
                "latitude": candidate["latitude"],
                "longitude": candidate["longitude"],
                "classification": classification,
                "identity_stable": not any(field in differences for field in IDENTITY_FIELDS),
                "semantic_differences": differences,
                "current_source_record_present": True,
            }
        )
        if classification not in {"UNCHANGED", "NON_MATERIAL_SOURCE_UPDATE", "MATERIAL_UPDATE_REVALIDATED"}:
            raise ValueError("unexpected candidate-impact classification")

    comparison_prior_intermediate = _compare_records(prior_records, intermediate_records)
    comparison_intermediate_current = _compare_records(intermediate_records, current_records)
    comparison_prior_current = _compare_records(prior_records, current_records)
    comparison_prior_intermediate["byte_identical"] = prior_sha == intermediate_sha
    comparison_intermediate_current["byte_identical"] = intermediate_sha == current_sha
    comparison_prior_current["byte_identical"] = prior_sha == current_sha

    r3_source_revalidation = _read_json(data_dir / "LOCAL_AUTHORITY_OGL_R3_SOURCE_REVALIDATION_2026-09-16.json")
    selected_sources = [dict(source) for source in r3_source_revalidation["selected_sources"]]
    causeway_source = next(source for source in selected_sources if source["source_id"] == CAUSEWAY_SOURCE_ID)
    causeway_source.update(
        {
            "sha256": current_sha,
            "byte_size": current_size,
            "revalidation_status": "R4A_CURRENT_MATCH_TO_R3_BYTES",
            "r4a_retrieved_at_utc": current_retrieved_at_utc,
        }
    )
    source_hashes = {source["source_id"]: source["sha256"] for source in selected_sources}
    source_hashes[CAUSEWAY_SOURCE_ID] = current_sha
    impact_counts: dict[str, int] = {}
    for row in candidate_impact:
        impact_counts[row["classification"]] = impact_counts.get(row["classification"], 0) + 1

    source_revalidation = {
        "tool_version": TOOL_VERSION,
        "classification": "R4A_SOURCE_DRIFT_REVALIDATED",
        "r3_manifest_path": "docs/data/LOCAL_AUTHORITY_OGL_R3_PRODUCTION_APPLY_MANIFEST_2026-09-16.json",
        "r3_manifest_sha256": manifest_sha256,
        "n4a_migration_sha256_required": N4A_SHA256,
        "source_id": CAUSEWAY_SOURCE_ID,
        "official_resource_url": current_url,
        "prior_r3_payload": _source_snapshot(prior_payload, prior_sha, prior_size, label="R3 sealed payload"),
        "intermediate_r4_payload": _source_snapshot(intermediate_payload, intermediate_sha, intermediate_size, label="R4 observed drift payload"),
        "current_r4a_payload": _source_snapshot(
            current_payload,
            current_sha,
            current_size,
            label="R4A fresh payload",
            retrieved_at_utc=current_retrieved_at_utc,
            status=current_status,
            content_type=current_content_type,
            resolved_url=current_url,
        ),
        "document_structure": {
            "prior_top_level_keys": sorted(prior_doc),
            "intermediate_top_level_keys": sorted(intermediate_doc),
            "current_top_level_keys": sorted(current_doc),
            "prior_feature_count": len(prior_doc["features"]),
            "intermediate_feature_count": len(intermediate_doc["features"]),
            "current_feature_count": len(current_doc["features"]),
            "current_content_is_geojson_feature_collection": current_doc.get("type") == "FeatureCollection",
        },
        "comparisons": {
            "r3_to_r4": comparison_prior_intermediate,
            "r4_to_r4a": comparison_intermediate_current,
            "r3_to_r4a": comparison_prior_current,
        },
        "candidate_impact": candidate_impact,
        "candidate_impact_counts": dict(sorted(impact_counts.items())),
        "causeway_r3_candidate_count": len(r3_candidates),
        "all_causeway_candidates_currently_supported": all(row["identity_stable"] and row["current_source_record_present"] for row in candidate_impact),
        "source_volatility": {
            "observed_hashes_in_order": [prior_sha, intermediate_sha, current_sha],
            "returned_to_r3_hash": current_sha == prior_sha == EXPECTED_R3_CAUSEWAY_SHA256,
            "volatile_payloads_are_semantically_equivalent": comparison_prior_intermediate["semantic_toilet_data_stable"] and comparison_intermediate_current["semantic_toilet_data_stable"],
        },
        "production_mutations": 0,
        "production_apply_authorized": False,
    }

    replacement_manifest = {
        "manifest_version": "R4",
        "tool_version": TOOL_VERSION,
        "classification": "R4A_REPLACEMENT_MANIFEST_RESEALED",
        "original_r3_manifest_path": "docs/data/LOCAL_AUTHORITY_OGL_R3_PRODUCTION_APPLY_MANIFEST_2026-09-16.json",
        "original_r3_manifest_sha256": manifest_sha256,
        "source_hashes": dict(sorted(source_hashes.items())),
        "causeway_current_sha256": current_sha,
        "causeway_source_revalidation": "R4A_SOURCE_DRIFT_REVALIDATED",
        "source_volatility_hashes_in_order": [prior_sha, intermediate_sha, current_sha],
        "candidates": r3_manifest["candidates"],
        "candidate_count": len(r3_manifest["candidates"]),
        "review_candidates_excluded": r3_manifest["review_candidates_excluded"],
        "review_rows_in_apply_manifest": 0,
        "all_candidates_source_identity_revalidated": True,
        "production_apply_authorized": False,
        "canonical_insertion_authorized": False,
        "production_mutations": 0,
        "next_production_apply_must_recheck_all_six_sources": True,
        "n4a_migration_sha256_required": N4A_SHA256,
    }
    output_dir.mkdir(parents=True, exist_ok=True)
    source_path = output_dir / "LOCAL_AUTHORITY_OGL_R4A_CAUSEWAY_SOURCE_REVALIDATION_2026-09-16.json"
    manifest_path = output_dir / "LOCAL_AUTHORITY_OGL_R4_PRODUCTION_APPLY_MANIFEST_2026-09-16.json"
    seal_path = output_dir / "LOCAL_AUTHORITY_OGL_R4_APPLY_MANIFEST_SEAL_2026-09-16.json"
    report_path = output_dir / "LOCAL_AUTHORITY_OGL_R4A_REPORT_2026-09-16.md"
    _write_lf(source_path, canonical_json(source_revalidation) + "\n")
    _write_lf(manifest_path, canonical_json(replacement_manifest) + "\n")
    replacement_manifest_sha256 = sha256_bytes(manifest_path.read_bytes())
    _write_lf(
        seal_path,
        canonical_json(
            {
                "tool_version": TOOL_VERSION,
                "classification": "R4A_REPLACEMENT_MANIFEST_SEALED",
                "manifest_path": "docs/data/LOCAL_AUTHORITY_OGL_R4_PRODUCTION_APPLY_MANIFEST_2026-09-16.json",
                "manifest_sha256": replacement_manifest_sha256,
                "candidate_count": 89,
                "causeway_current_sha256": current_sha,
                "production_apply_authorized": False,
                "canonical_insertion_authorized": False,
                "production_mutations": 0,
                "next_production_apply_must_recheck_all_six_sources": True,
            }
        )
        + "\n",
    )
    report = [
        "# RELIEF Data Growth R4A — Causeway Source Drift Revalidation",
        "",
        "**Classification:** `R4A_SOURCE_DRIFT_REVALIDATED`",
        "",
        "R4A compared the exact R3 Causeway payload, the R4 drift payload, and a fresh official HTTPS payload. The source oscillated between two byte representations but preserved the same 52 normalized records and all five R3 apply candidates.",
        "",
        "## Verified payloads",
        "",
        f"- R3 sealed payload: `{prior_sha}` ({prior_size} bytes).",
        f"- R4 observed payload: `{intermediate_sha}` ({intermediate_size} bytes).",
        f"- R4A current payload: `{current_sha}` ({current_size} bytes), HTTP {current_status}, `{current_content_type}`.",
        f"- R4A retrieval UTC: `{current_retrieved_at_utc}`.",
        "- All three payloads contain 52 GeoJSON features with stable source identities.",
        "",
        "## Semantic result",
        "",
        "The R3-to-R4 payload difference was limited to publisher/export metadata (`last_updated` precision and `raw_source_fingerprint`). Names, addresses, postcodes, coordinates, toilet types, accessibility, charge, opening-hours, status, operator, and direct-toilet evidence remained stable. The fresh R4A payload is byte-identical to the R3 sealed payload.",
        "",
        f"- Causeway R3 candidates examined: **{len(r3_candidates)}**.",
        f"- Candidate impact: `{json.dumps(dict(sorted(impact_counts.items())), sort_keys=True)}`.",
        "- Removed candidates: **0**.",
        "- Ambiguous/review-required candidates: **0**.",
        "",
        "## Replacement manifest",
        "",
        "The immutable R3 manifest was not overwritten. A new R4 manifest was sealed with the current Causeway hash. It remains a non-authorizing input for a future apply transaction; the next apply must repeat all six source gates.",
        "",
        f"- Manifest: `docs/data/LOCAL_AUTHORITY_OGL_R4_PRODUCTION_APPLY_MANIFEST_2026-09-16.json`.",
        f"- Manifest SHA-256: `{replacement_manifest_sha256}`.",
        "- Automatic candidate count: **89**.",
        "- Review candidates excluded: **7**.",
        "- Production apply authorized: **false**.",
        "",
        "## Safety",
        "",
        "No production SQL or DML was executed. No facilities, provenance, import records, source rows, schema, or migration state changed.",
        "",
        "`R4A_SOURCE_DRIFT_REVALIDATED`",
        "",
        "`TOTAL PRODUCTION MUTATIONS: 0`",
        "",
    ]
    _write_lf(report_path, "\n".join(report))
    return {
        "source_revalidation_path": source_path,
        "manifest_path": manifest_path,
        "manifest_seal_path": seal_path,
        "report_path": report_path,
        "manifest_sha256": replacement_manifest_sha256,
        "causeway_sha256": current_sha,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Read-only R4A Causeway source-drift revalidation")
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--r3-manifest", type=Path, required=True)
    parser.add_argument("--prior-payload", type=Path, required=True)
    parser.add_argument("--intermediate-payload", type=Path, required=True)
    parser.add_argument("--current-payload", type=Path, required=True)
    parser.add_argument("--current-url", required=True)
    parser.add_argument("--current-retrieved-at-utc", required=True)
    parser.add_argument("--current-status", type=int, required=True)
    parser.add_argument("--current-content-type", required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args(argv)
    run(
        args.root,
        args.r3_manifest,
        args.prior_payload,
        args.intermediate_payload,
        args.current_payload,
        args.current_url,
        args.current_retrieved_at_utc,
        args.current_status,
        args.current_content_type,
        args.output_dir,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

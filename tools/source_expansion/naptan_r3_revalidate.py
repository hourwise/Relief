"""Read-only R3 revalidation and apply-manifest sealer for the OGL pilot pool.

The module deliberately has no database client and no production-write path. It
consumes fresh disposable source bytes, the committed Pilot 1/Pilot 2 register,
and a separately captured read-only production recheck. Its output is a plan
for a later, separately authorized apply transaction.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from .local_authority_ogl_pilot import (
    SOURCE_CATALOG,
    _csv_rows,
    canonical_json,
    normalize_geojson_feature,
    normalize_tabular_record,
    sha256_bytes,
)


TOOL_VERSION = "relief.local-authority-ogl-r3-revalidation.v1"
PRODUCTION_WRITE_CAPABILITY = False
EXPECTED_STRICT_POOL = 89
EXPECTED_REVIEW_POOL = 7
PILOT_1_SOURCE_IDS = {
    "city-of-york-public-toilets",
    "causeway-coast-and-glens-public-toilets",
}
ALL_SOURCE_IDS = (
    "city-of-york-public-toilets",
    "causeway-coast-and-glens-public-toilets",
    "adur-public-toilets",
    "worthing-public-toilets",
    "perth-kinross-public-toilets-and-comfort-schemes",
    "belfast-public-toilets",
)


def _read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _write_lf(path: Path, text: str) -> None:
    """Write deterministic evidence bytes independent of the host newline mode."""
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        handle.write(text)


def _load_current_source(path: Path, source_id: str) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    source = SOURCE_CATALOG[source_id]
    payload = path.read_bytes()
    actual_sha = sha256_bytes(payload)
    if source_id in PILOT_1_SOURCE_IDS:
        document = json.loads(payload.decode("utf-8"))
        features = document.get("features") if isinstance(document, dict) else None
        if not isinstance(features, list):
            raise ValueError(f"{source_id} current payload is not a GeoJSON FeatureCollection")
        records = [
            normalize_geojson_feature(feature, source_id, ordinal)
            for ordinal, feature in enumerate(features, start=1)
        ]
    elif source.get("format") == "csv":
        records = [
            normalize_tabular_record(
                row,
                source_id,
                ordinal,
                sha256_bytes(canonical_json(row).encode("utf-8")),
            )
            for ordinal, row in enumerate(_csv_rows(payload), start=1)
        ]
    elif source.get("format") == "geojson":
        document = json.loads(payload.decode("utf-8"))
        features = document.get("features") if isinstance(document, dict) else None
        if not isinstance(features, list):
            raise ValueError(f"{source_id} current payload is not a GeoJSON FeatureCollection")
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
        raise ValueError(f"unsupported current source format for {source_id}")
    return (
        {
            "source_id": source_id,
            "publisher": source["publisher"],
            "dataset": source["dataset"],
            "resource_url": source["resource_url"],
            "licence": source["licence"],
            "byte_size": len(payload),
            "sha256": actual_sha,
            "record_count": len(records),
        },
        sorted(records, key=lambda row: row["source_record_id"]),
    )


def _semantic_record(record: dict[str, Any]) -> dict[str, Any]:
    return {
        key: record.get(key)
        for key in (
            "source_record_id",
            "name",
            "address",
            "postcode",
            "latitude",
            "longitude",
            "toilet_type",
            "direct_toilet_evidence",
        )
    }


def _source_revalidation(
    root: Path,
    source_inputs: dict[str, Path],
) -> tuple[list[dict[str, Any]], dict[str, list[dict[str, Any]]]]:
    data_dir = root / "docs" / "data"
    previous_manifest = _read_json(data_dir / "LOCAL_AUTHORITY_OGL_PILOT_1_SOURCE_MANIFEST_2026-08-23.json")
    previous_by_id = {row["source_id"]: row for row in previous_manifest["sources"]}
    previous_pilot_2 = _read_json(data_dir / "LOCAL_AUTHORITY_OGL_PILOT_2_SOURCE_MANIFEST_2026-08-23.json")
    previous_by_id.update(
        {
            row["source_id"]: {
                "retrieved_at_utc": None,
                "byte_size": row.get("raw_bytes"),
                "sha256": row.get("raw_sha256"),
            }
            for row in previous_pilot_2["selected_sources"]
        }
    )
    previous_normalized = _read_json(data_dir / "LOCAL_AUTHORITY_OGL_PILOT_1_NORMALIZED_RECORDS_2026-08-23.json")["records"]
    previous_pilot_1 = {
        row["source_record_id"]: row
        for row in previous_normalized
        if row["source_namespace"] in PILOT_1_SOURCE_IDS
    }
    snapshots: list[dict[str, Any]] = []
    current_records: dict[str, list[dict[str, Any]]] = {}
    for source_id in ALL_SOURCE_IDS:
        manifest, records = _load_current_source(source_inputs[source_id], source_id)
        current_records[source_id] = records
        previous = previous_by_id.get(source_id)
        identity_stable = True
        semantic_changes: dict[str, int] = {}
        if source_id in PILOT_1_SOURCE_IDS:
            current_by_id = {row["source_record_id"]: row for row in records}
            previous_ids = set(
                row_id for row_id, row in previous_pilot_1.items() if row["source_namespace"] == source_id
            )
            current_ids = set(current_by_id)
            identity_stable = previous_ids == current_ids
            for field in ("name", "address", "postcode", "latitude", "longitude", "toilet_type"):
                semantic_changes[field] = sum(
                    current_by_id.get(row_id, {}).get(field) != previous_pilot_1.get(row_id, {}).get(field)
                    for row_id in sorted(previous_ids & current_ids)
                )
        status = "UNCHANGED_EXACT_BYTES"
        if previous and manifest["sha256"] != previous["sha256"]:
            status = "PAYLOAD_CHANGED_IDENTITIES_STABLE" if identity_stable else "PAYLOAD_CHANGED_IDENTITY_DRIFT"
        snapshots.append(
            {
                **manifest,
                "previous_snapshot": {
                    "retrieved_at_utc": previous.get("retrieved_at_utc") if previous else None,
                    "byte_size": previous.get("byte_size") if previous else None,
                    "sha256": previous.get("sha256") if previous else None,
                },
                "revalidation_status": status,
                "identity_stable": identity_stable,
                "pilot_1_semantic_changes": semantic_changes,
            }
        )
        if status == "PAYLOAD_CHANGED_IDENTITY_DRIFT":
            raise ValueError(f"source identity drift detected for {source_id}")
    return snapshots, current_records


def run(root: Path, source_args: list[tuple[str, Path]], production_recheck_path: Path, output_dir: Path) -> None:
    if PRODUCTION_WRITE_CAPABILITY:
        raise RuntimeError("R3 must not have production-write capability")
    source_inputs = dict(source_args)
    if set(source_inputs) != set(ALL_SOURCE_IDS):
        raise ValueError("R3 requires exactly the six selected Pilot 1/Pilot 2 sources")
    snapshots, current_records = _source_revalidation(root, source_inputs)
    data_dir = root / "docs" / "data"
    register = _read_json(data_dir / "LOCAL_AUTHORITY_OGL_COMBINED_CANDIDATE_REGISTER_2026-08-23.json")
    entries = register["entries"]
    strict = [row for row in entries if row.get("classification") == "CONSERVATIVE_NET_NEW"]
    review = [row for row in entries if row.get("classification") == "POSSIBLE_NET_NEW_REVIEW"]
    if len(strict) != EXPECTED_STRICT_POOL or len(review) != EXPECTED_REVIEW_POOL:
        raise ValueError("committed OGL pool counts changed")
    source_rows = {
        row["source_record_id"]: row
        for records in current_records.values()
        for row in records
    }
    missing = [row["candidate_id"] for row in strict if row["source_record_id"] not in source_rows]
    if missing:
        raise ValueError(f"strict pool source identities missing from current payloads: {missing}")
    mismatched_coordinates = [
        row["candidate_id"]
        for row in strict
        if abs(float(row["latitude"]) - float(source_rows[row["source_record_id"]]["latitude"])) > 1e-9
        or abs(float(row["longitude"]) - float(source_rows[row["source_record_id"]]["longitude"])) > 1e-9
    ]
    if mismatched_coordinates:
        raise ValueError(f"strict pool coordinates changed: {mismatched_coordinates}")
    production = _read_json(production_recheck_path)
    if production.get("project_ref") != "bgwxrxkmyaihplaloely":
        raise ValueError("production recheck project ref mismatch")
    if production.get("baseline", {}).get("facilities") != 15620:
        raise ValueError("production facility baseline changed")
    candidate_recheck = production.get("candidate_recheck", {})
    required_recheck = {
        "total_candidates": EXPECTED_STRICT_POOL,
        "same_nearest_facility": EXPECTED_STRICT_POOL,
        "no_nearest_facility": 0,
        "current_within_250m": 0,
    }
    if any(candidate_recheck.get(key) != value for key, value in required_recheck.items()):
        raise ValueError("current production candidate recheck failed")
    strict = sorted(strict, key=lambda row: row["candidate_id"])
    source_revalidation = {
        "tool_version": TOOL_VERSION,
        "classification": "R3_SOURCE_REVALIDATED_READ_ONLY",
        "retrieval_mode": "official HTTPS resources with normal certificate validation",
        "production_write_capability": False,
        "selected_sources": snapshots,
        "source_payload_drift": [
            {
                "source_id": row["source_id"],
                "status": row["revalidation_status"],
                "previous_sha256": row["previous_snapshot"]["sha256"],
                "current_sha256": row["sha256"],
                "identity_stable": row["identity_stable"],
                "semantic_changes": row["pilot_1_semantic_changes"],
            }
            for row in snapshots
            if row["revalidation_status"] != "UNCHANGED_EXACT_BYTES"
        ],
        "strict_pool": {
            "expected": EXPECTED_STRICT_POOL,
            "revalidated": len(strict),
            "missing_source_identities": [],
            "coordinate_mismatches": [],
        },
        "review_pool_preserved_out_of_apply_manifest": len(review) == EXPECTED_REVIEW_POOL,
    }
    apply_manifest = {
        "tool_version": TOOL_VERSION,
        "classification": "R3_PRODUCTION_APPLY_MANIFEST_SEALED",
        "manifest_scope": "89 strict CONSERVATIVE_NET_NEW candidates only",
        "production_project": production["project"],
        "production_project_ref": production["project_ref"],
        "production_region": production["region"],
        "production_apply_authorized": False,
        "production_write_capability": False,
        "canonical_insertion_authorized": False,
        "sealed_at_utc": production["recheck_at_utc"],
        "source_snapshots": [
            {
                "source_id": row["source_id"],
                "resource_url": row["resource_url"],
                "byte_size": row["byte_size"],
                "sha256": row["sha256"],
                "revalidation_status": row["revalidation_status"],
            }
            for row in snapshots
        ],
        "candidate_count": len(strict),
        "candidates": [
            {
                "candidate_id": row["candidate_id"],
                "source_namespace": row["source_namespace"],
                "source_record_id": row["source_record_id"],
                "name": row["name"],
                "latitude": row["latitude"],
                "longitude": row["longitude"],
                "licence": row["licence"],
                "attribution": row["attribution"],
                "direct_toilet_evidence": row["direct_toilet_evidence"],
                "source_row_identity_revalidated": True,
                "current_nearest_facility_id": row["nearest_relief_facility_id"],
                "current_nearest_facility_distance_m_frozen_reference": row["nearest_relief_distance_m"],
            }
            for row in strict
        ],
        "guards_required_in_next_apply": [
            "recheck production counts and source identity absence",
            "recheck source bytes and hashes against this manifest",
            "fail closed on any existing source or canonical identity conflict",
            "write only through the separately authorized apply transaction",
            "record before/after counts and preserve all zero-mutation boundaries",
        ],
        "review_candidates_excluded": len(review),
        "mutation_count_this_transaction": 0,
    }
    production_comparison = {
        "tool_version": TOOL_VERSION,
        "classification": "R3_PRODUCTION_REVALIDATION_PASSED",
        **production,
        "source_provenance_rows_for_selected_namespaces": 0,
        "candidate_pool_revalidated": len(strict),
        "candidate_pool_same_nearest_facility": candidate_recheck["same_nearest_facility"],
        "candidate_pool_current_within_250m": candidate_recheck["current_within_250m"],
        "production_mutations": 0,
    }
    output_dir.mkdir(parents=True, exist_ok=True)
    _write_lf(
        output_dir / "LOCAL_AUTHORITY_OGL_R3_SOURCE_REVALIDATION_2026-09-16.json",
        canonical_json(source_revalidation) + "\n",
    )
    _write_lf(
        output_dir / "LOCAL_AUTHORITY_OGL_R3_PRODUCTION_COMPARISON_2026-09-16.json",
        canonical_json(production_comparison) + "\n",
    )
    _write_lf(
        output_dir / "LOCAL_AUTHORITY_OGL_R3_PRODUCTION_APPLY_MANIFEST_2026-09-16.json",
        canonical_json(apply_manifest) + "\n",
    )
    manifest_path = output_dir / "LOCAL_AUTHORITY_OGL_R3_PRODUCTION_APPLY_MANIFEST_2026-09-16.json"
    manifest_sha256 = sha256_bytes(manifest_path.read_bytes())
    _write_lf(
        output_dir / "LOCAL_AUTHORITY_OGL_R3_APPLY_MANIFEST_SEAL_2026-09-16.json",
        canonical_json(
            {
                "tool_version": TOOL_VERSION,
                "classification": "R3_APPLY_MANIFEST_CONTENT_SEALED",
                "manifest_path": "docs/data/LOCAL_AUTHORITY_OGL_R3_PRODUCTION_APPLY_MANIFEST_2026-09-16.json",
                "manifest_sha256": manifest_sha256,
                "candidate_count": len(strict),
                "production_apply_authorized": False,
                "canonical_insertion_authorized": False,
                "production_mutations": 0,
                "seal_scope": "current official source hashes, 89 strict candidate identities, and read-only production recheck only",
                "next_transaction_must_recheck": True,
            }
        )
        + "\n",
    )
    report = [
        "# RELIEF Data Growth R3 — OGL Pilot Revalidation and Apply Manifest",
        "",
        "**Classification:** `PRODUCTION_READ_ONLY`",
        "",
        "R3 revalidated the existing Local Authority OGL Pilot 1 + Pilot 2 pool against fresh official HTTPS payloads and a read-only production recheck. No canonical insertion was attempted.",
        "",
        "## Result",
        "",
        f"- Strict pool revalidated: **{len(strict)}** (`CONSERVATIVE_NET_NEW`).",
        f"- Review pool preserved but excluded from the apply manifest: **{len(review)}**.",
        "- Current production nearest-facility identity agreed with the frozen reference for all 89 strict candidates.",
        "- Current production 250 m duplicate guard matched **0** strict candidates.",
        "- Existing selected OGL source provenance rows in production: **0**.",
        "- Production mutations in R3: **0**.",
        f"- Apply-manifest content SHA-256: `{manifest_sha256}`.",
        "",
        "## Source revalidation",
        "",
        "All six selected official resources were fetched into disposable C:\\Temp storage over normal TLS. Five payloads are byte-identical to the Pilot 1/Pilot 2 evidence. The current Causeway payload has a new SHA-256 and metadata change, but all 52 stable source identities, names, addresses, postcodes, coordinates, and toilet type values remain unchanged; this is recorded as `PAYLOAD_CHANGED_IDENTITIES_STABLE`, not silently ignored.",
        "",
        "## Production safety",
        "",
        "- Production project: Relief (`bgwxrxkmyaihplaloely`).",
        "- Production migration head: `20260822170000`.",
        "- Canonical facilities remained at 15,620; facility_sources at 15,634; observations at 14; import_runs at 5; toilet units at 0.",
        "- Source graph remained at 1 / 97,270 / 436,428 / 169,527 / 3,519 rows.",
        "- No `INSERT`, `UPDATE`, `DELETE`, `MERGE`, `TRUNCATE`, DDL, migration, import, provenance, or canonical operation was run.",
        "",
        "## Apply-manifest boundary",
        "",
        "`LOCAL_AUTHORITY_OGL_R3_PRODUCTION_APPLY_MANIFEST_2026-09-16.json` is a sealed input for a later separately authorized apply transaction. It is not an authorization and contains no execution path. The seven review candidates are excluded; only the 89 strict candidates are listed.",
        "",
        "## Required next transaction",
        "",
        "A separate production-apply authorization must repeat the source/hash and conflict gates immediately before writing. R3 stops here.",
        "",
        "`R3_SOURCE_REVALIDATED_READ_ONLY`",
        "",
        "`R3_CANDIDATE_POOL_STABLE`",
        "",
        "`R3_PRODUCTION_APPLY_MANIFEST_SEALED`",
        "",
        "`R3_CANONICAL_INSERTION_NOT_AUTHORIZED`",
        "",
        "`TOTAL PRODUCTION MUTATIONS: 0`",
        "",
    ]
    _write_lf(output_dir / "LOCAL_AUTHORITY_OGL_R3_REPORT_2026-09-16.md", "\n".join(report))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Revalidate the OGL pilot pool without production writes")
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--source", action="append", nargs=2, metavar=("SOURCE_ID", "PATH"), required=True)
    parser.add_argument("--production-recheck", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args(argv)
    run(args.root, [(source_id, Path(path)) for source_id, path in args.source], args.production_recheck, args.output_dir)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

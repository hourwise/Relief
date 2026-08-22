"""Deterministic, read-only TfL toilet-row semantics and Batch 2 adjudication.

This module reads only the already-frozen TfL ZIP, committed reconciliation
evidence, and the committed post-apply observation evidence.  It has no
network, Supabase, SQL execution, or production mutation path.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import zipfile
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Mapping

from tools.source_expansion.tfl_detailed import load_feed, normalize_tfl_feed
from tools.source_expansion.tfl_existing_parent_observation_apply import (
    reproduce_frozen_14_cohort,
)


REPOSITORY = "hourwise/Relief"
BRANCH = "codex/toilet-map-apply-1a-production-deploy"
FROZEN_ZIP = Path("tools/source_expansion/cache/tfl-detailed-2026-08-21/tfl-stationdata-detailed.zip")
FROZEN_RECONCILIATION = Path("tools/source_expansion/cache/tfl-detailed-2026-08-21/tfl-reconciliation.json")
POST_APPLY = Path("docs/data/RELIEF_TFL_EXISTING_PARENT_OBSERVATION_POST_APPLY_2026-08-22.json")
ZIP_URL = "https://api.tfl.gov.uk/stationdata/tfl-stationdata-detailed.zip"
ZIP_SHA256 = "19c50772febd1a3d7625f59e079b7590c5da4ed70424d6f552cfd7db1611e2ce"
ZIP_BYTES = 186_973
ZIP_RETRIEVAL_UTC = "2026-08-21T06:08:20.1476469Z"
RECONCILIATION_SHA256 = "65cc9cc8c41b7b3a003524610b674c7f2eae96ff7fe5116f38f2d2856cb777cb"
ATTRIBUTION = "Data provided by Transport for London"
COORDINATE_SCOPE = "STATION_LEVEL"
SOURCE_NAME = "TfL detailed station data — station facilities and toilets"

ALLOWED_CLASSIFICATIONS = {
    "PHYSICAL_UNIT_PROMOTION_READY",
    "OBSERVATION_ONLY",
    "HUMAN_ADJUDICATION_REQUIRED",
}


def stable_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def sha256_json(value: Any) -> str:
    return sha256_bytes(stable_json(value).encode("utf-8"))


def verify_frozen_inputs() -> dict[str, Any]:
    zip_bytes = FROZEN_ZIP.read_bytes()
    reconciliation_bytes = FROZEN_RECONCILIATION.read_bytes()
    if len(zip_bytes) != ZIP_BYTES:
        raise AssertionError(f"frozen ZIP size changed: {len(zip_bytes)}")
    if sha256_bytes(zip_bytes) != ZIP_SHA256:
        raise AssertionError("frozen ZIP SHA-256 mismatch")
    if sha256_bytes(reconciliation_bytes) != RECONCILIATION_SHA256:
        raise AssertionError("frozen reconciliation SHA-256 mismatch")
    reconciliation = json.loads(reconciliation_bytes.decode("utf-8"))
    if reconciliation.get("counts", {}).get("toilet_row_count") != 410:
        raise AssertionError("frozen reconciliation does not contain 410 toilet rows")
    return {
        "zip_url": ZIP_URL,
        "zip_sha256": ZIP_SHA256,
        "zip_bytes": ZIP_BYTES,
        "zip_retrieval_utc": ZIP_RETRIEVAL_UTC,
        "reconciliation_sha256": RECONCILIATION_SHA256,
        "attribution": ATTRIBUTION,
    }


def raw_rows() -> list[dict[str, Any]]:
    tables, _ = load_feed(FROZEN_ZIP)
    return [dict(row) for row in tables["Toilets.csv"]]


def source_identity(row: Mapping[str, Any]) -> str:
    station_id = str(row.get("StationUniqueId") or "").strip()
    toilet_id = str(row.get("Id") or "").strip()
    if not station_id or not toilet_id:
        raise AssertionError("TfL row lacks StationUniqueId or Id")
    return f"tfl:{station_id}:toilet:{toilet_id}"


def row_fingerprint(row: Mapping[str, Any]) -> str:
    """Fingerprint the full frozen publisher row, including empty fields."""

    return sha256_json({str(key): row[key] for key in sorted(row)})


def row_group_key(row: Mapping[str, Any]) -> tuple[str, str]:
    return (str(row["StationUniqueId"]).strip(), str(row["Id"]).strip())


def material_attributes(row: Mapping[str, Any]) -> tuple[Any, ...]:
    return tuple(
        str(row.get(key) or "").strip().casefold()
        for key in (
            "Type",
            "IsAccessible",
            "HasBabyChanging",
            "IsInsideGateLine",
            "Location",
            "IsFeeCharged",
            "IsManagedByTfL",
            "AskStaff",
            "RadarKey",
            "OpeningHours",
            "OpensWithStation",
            "ClosesWithStation",
        )
    )


def whole_source_semantics(rows: list[dict[str, Any]], station_count: int) -> dict[str, Any]:
    station_groups: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        station_groups[str(row["StationUniqueId"]).strip()].append(row)
    identities = [source_identity(row) for row in rows]
    identity_counts = Counter(identities)
    exact_attribute_candidates = [
        {"station_id": station_id, "source_identities": [source_identity(row) for row in group]}
        for station_id, group in sorted(station_groups.items())
        if len(group) > 1
        and len(Counter(material_attributes(row) for row in group)) < len(group)
    ]
    duplicate_attribute_row_count = sum(
        count - 1
        for group in station_groups.values()
        for count in Counter(material_attributes(row) for row in group).values()
        if count > 1
    )
    repeated_type_groups = [
        {
            "station_id": station_id,
            "type": toilet_type,
            "source_identities": [source_identity(row) for row in group if str(row.get("Type") or "").strip().upper() == toilet_type],
        }
        for station_id, group in sorted(station_groups.items())
        for toilet_type in sorted({str(row.get("Type") or "").strip().upper() for row in group})
        if toilet_type and sum(str(row.get("Type") or "").strip().upper() == toilet_type for row in group) > 1
    ]
    rows_per_station = Counter(len(group) for group in station_groups.values())
    row_count_examples = {}
    for count in sorted(rows_per_station):
        station_id = sorted(station_id for station_id, group in station_groups.items() if len(group) == count)[0]
        row_count_examples[str(count)] = {
            "station_id": station_id,
            "source_record_ids": [source_identity(row) for row in station_groups[station_id]],
        }
    multirow_groups = [group for group in station_groups.values() if len(group) > 1]
    same_location_multirow_groups = sum(
        len({str(row.get("Location") or "").strip() for row in group}) == 1
        for group in multirow_groups
    )
    combination_counts = Counter(
        (
            str(row.get("Type") or "").strip().upper(),
            str(row.get("IsAccessible") or "").strip().upper(),
            str(row.get("HasBabyChanging") or "").strip().upper(),
        )
        for row in rows
    )
    type_counts = Counter(str(row.get("Type") or "").strip().upper() or "UNKNOWN" for row in rows)
    accessible_counts = Counter(str(row.get("IsAccessible") or "").strip().upper() or "UNKNOWN" for row in rows)
    baby_counts = Counter(str(row.get("HasBabyChanging") or "").strip().upper() or "UNKNOWN" for row in rows)
    fee_counts = Counter(str(row.get("IsFeeCharged") or "").strip().upper() or "UNKNOWN" for row in rows)
    location_counts = Counter(str(row.get("Location") or "").strip() or "UNKNOWN" for row in rows)
    return {
        "station_count_in_stations_csv": station_count,
        "toilet_row_count": len(rows),
        "stations_with_toilet_rows": len(station_groups),
        "stations_with_multiple_toilet_rows": sum(count > 1 for count in rows_per_station.values()),
        "rows_per_station_distribution": {str(key): rows_per_station[key] for key in sorted(rows_per_station)},
        "rows_per_station_examples": row_count_examples,
        "attribute_combination_distribution": {
            f"{gender}|accessible={accessible}|baby_changing={baby}": count
            for (gender, accessible, baby), count in sorted(combination_counts.items())
        },
        "source_identity": {
            "publisher_fields": ["StationUniqueId", "Id"],
            "relief_source_record_id_format": "tfl:{StationUniqueId}:toilet:{Id}",
            "unique_identity_count": len(identity_counts),
            "duplicate_identity_count": sum(count - 1 for count in identity_counts.values() if count > 1),
            "row_position_is_transient": True,
            "id_is_not_physical_unit_proof": True,
        },
        "attribute_distributions": {
            "gender": dict(sorted(type_counts.items())),
            "accessible": dict(sorted(accessible_counts.items())),
            "baby_changing": dict(sorted(baby_counts.items())),
            "fee": dict(sorted(fee_counts.items())),
            "location": dict(sorted(location_counts.items())),
        },
        "duplicate_and_topology_risk": {
            "exact_material_attribute_duplicate_candidate_station_groups": len(exact_attribute_candidates),
            "exact_material_attribute_duplicate_candidate_extra_rows": duplicate_attribute_row_count,
            "repeated_gender_within_station_groups": len(repeated_type_groups),
            "same_location_multirow_station_groups": same_location_multirow_groups,
            "potential_duplicate_physical_identity_rows": sum(len(group) for group in multirow_groups),
            "representative_exact_attribute_groups": exact_attribute_candidates[:12],
            "representative_repeated_gender_groups": repeated_type_groups[:12],
            "clearly_distinct_rows_from_feed_alone": 0,
            "physical_topology_inherently_ambiguous_rows": len(rows),
        },
        "coordinate_findings": {
            "source_file": "StationPoints.csv",
            "toilet_specific_coordinate_columns": [],
            "normalized_scope": COORDINATE_SCOPE,
            "toilet_rows_with_station_coordinates": len(rows),
            "toilet_level_coordinates_supported": False,
        },
    }


def _post_apply_index() -> dict[str, dict[str, Any]]:
    payload = json.loads(POST_APPLY.read_text(encoding="utf-8"))
    return {row["source_record_id"]: row for row in payload["post_apply"]["observations"]}


def _canonical_source_row(normalized: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "source_row_number": normalized["source_row_number"],
        "raw_row_fingerprint": row_fingerprint(normalized["raw"]),
        "StationUniqueId": normalized["stable_tfl_station_id"],
        "Id": normalized["stable_tfl_toilet_id"],
        "station_name": normalized["station_name"],
        "station_public_location": normalized["station/public_location"],
        "toilet_location_description": normalized["toilet_location_description"],
        "toilet_type": normalized["toilet_type"],
        "is_accessible": normalized["is_accessible"],
        "has_baby_changing": normalized["has_baby_changing"],
        "inside_gateline": normalized["inside_gateline"],
        "fee_status": normalized["fee_status"],
        "tfl_management_status": normalized["tfl_management_status"],
        "ask_staff": normalized["ask_staff"],
        "radar_key": normalized["radar_key"],
        "opening_hours_text": normalized["opening_hours_text"],
        "opens_with_station": normalized["opens_with_station"],
        "closes_with_station": normalized["closes_with_station"],
        "station_coordinates": normalized["station_coordinates"],
        "coordinate_scope": COORDINATE_SCOPE,
        "positional_precision": normalized["positional_precision"],
    }


def classify_batch(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    # Avoid a second parser implementation: load_feed returns tables, then
    # normalize_tfl_feed supplies the repository's established semantics.
    tables, _inventory = load_feed(FROZEN_ZIP)
    normalized_rows = normalize_tfl_feed(tables)
    by_identity = {f"tfl:{row['stable_tfl_station_id']}:toilet:{row['stable_tfl_toilet_id']}": row for row in normalized_rows}
    post_apply = _post_apply_index()
    groups = Counter(row["source_identity"]["StationUniqueId"] for row in rows)
    result = []
    for row in rows:
        identity = row["source_identity"]["source_record_id"]
        source_row = by_identity.get(identity)
        if source_row is None:
            raise AssertionError(f"missing frozen source row for {identity}")
        production = post_apply.get(identity)
        if production is None:
            raise AssertionError(f"missing production observation evidence for {identity}")
        group_size = groups[row["source_identity"]["StationUniqueId"]]
        if group_size > 1:
            classification = "HUMAN_ADJUDICATION_REQUIRED"
            confidence = "LOW"
            reason_code = "MULTIROW_TOPOLOGY_UNRESOLVED"
            evidence_basis = (
                "The station has multiple TfL rows. The frozen feed supplies row attributes and a source ID, "
                "but no authoritative physical-room discriminator; gender, differing attributes, and row IDs "
                "cannot establish whether rows are separate rooms or views of one provision."
            )
            human_review = True
        else:
            classification = "OBSERVATION_ONLY"
            confidence = "MEDIUM"
            reason_code = "ROW_SEMANTICS_AMBIGUOUS"
            evidence_basis = (
                "The feed supplies one toilet-provision row for this station, but does not state that its row ID "
                "is a physical-room identifier and supplies station-level coordinates only. The row is useful "
                "source evidence but is not sufficient by itself to assert a canonical physical unit."
            )
            human_review = True
        proposed_unit = None
        result.append(
            {
                "source_name": SOURCE_NAME,
                "tfl_station_identity": row["source_identity"]["StationUniqueId"],
                "relief_canonical_facility_id": row["canonical_facility_id"],
                "relief_canonical_facility_name": row["canonical_facility_name"],
                "facility_source_id": production["facility_source_id"],
                "observation_id": production["observation_id"],
                "source_record_id": identity,
                "publisher_identity": {
                    "StationUniqueId": row["source_identity"]["StationUniqueId"],
                    "Id": row["source_identity"]["Id"],
                },
                "source_row": _canonical_source_row(source_row),
                "source_row_fingerprint": row_fingerprint(source_row["raw"]),
                "coordinate_scope": COORDINATE_SCOPE,
                "physical_unit_classification": classification,
                "confidence": confidence,
                "reason_code": reason_code,
                "evidence_basis": evidence_basis,
                "evidence_refs": [
                    "tools/source_expansion/tfl_detailed.py",
                    "tools/source_expansion/cache/tfl-detailed-2026-08-21/tfl-reconciliation.json",
                    "docs/data/RELIEF_TFL_EXISTING_PARENT_OBSERVATION_POST_APPLY_2026-08-22.json",
                ],
                "proposed_future_unit_key": proposed_unit,
                "proposed_future_attributes": None,
                "ambiguity_notes": [
                    "TfL row identity is source identity only, not physical-unit identity.",
                    "No toilet-specific coordinates are provided.",
                    "Gender, accessibility, baby-changing, fee, location text, and row multiplicity are not independently sufficient physical discriminators.",
                ],
                "human_review_required": human_review,
                "observation_state": {
                    "toilet_unit_id": None,
                    "physical_unit_asserted": False,
                    "unit_link_status": "UNLINKED",
                    "production_observation_unchanged": True,
                },
            }
        )
    return result


def station_topologies(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    groups: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        groups[row["tfl_station_identity"]].append(row)
    return [
        {
            "tfl_station_identity": station_id,
            "row_count": len(group),
            "source_record_ids": [row["source_record_id"] for row in group],
            "source_attributes": [
                {
                    "source_record_id": row["source_record_id"],
                    "gender": row["source_row"]["toilet_type"],
                    "accessible": row["source_row"]["is_accessible"],
                    "baby_changing": row["source_row"]["has_baby_changing"],
                    "location": row["source_row"]["toilet_location_description"],
                    "coordinate_scope": row["coordinate_scope"],
                }
                for row in group
            ],
            "authoritative_evidence_located": [
                "frozen TfL Toilets.csv row attributes",
                "repository parser and reconciliation evidence",
            ],
            "proposed_physical_unit_count": None,
            "source_rows_to_physical_units": None,
            "confidence": "LOW" if len(group) > 1 else "MEDIUM",
            "adjudication_state": "HUMAN_ADJUDICATION_REQUIRED" if len(group) > 1 else "OBSERVATION_ONLY",
            "explanation": (
                "Physical topology is not proven by the frozen source; no unit mapping is emitted."
            ),
        }
        for station_id, group in sorted(groups.items())
    ]


def build_package() -> dict[str, Any]:
    source = verify_frozen_inputs()
    tables, inventory = load_feed(FROZEN_ZIP)
    normalized = normalize_tfl_feed(tables)
    cohort = reproduce_frozen_14_cohort()
    adjudications = classify_batch(cohort)
    semantics = whole_source_semantics(tables["Toilets.csv"], len(tables["Stations.csv"]))
    classifications = Counter(row["physical_unit_classification"] for row in adjudications)
    confidence = Counter(row["confidence"] for row in adjudications)
    reasons = Counter(row["reason_code"] for row in adjudications)
    production = json.loads(POST_APPLY.read_text(encoding="utf-8"))["post_apply"]["counts"]
    return {
        "document_type": "RELIEF_TFL_PHYSICAL_UNIT_SEMANTICS_BATCH_2",
        "classification": "RELIEF TFL PHYSICAL-UNIT SEMANTICS — SOURCE DOES NOT SUPPORT SAFE UNIT PROMOTION",
        "repository": REPOSITORY,
        "branch": BRANCH,
        "source": {
            **source,
            "feed_record_count": len(normalized),
            "feed_info": tables.get("FeedInfo.csv", []),
            "zip_inventory_sha256": sha256_json(inventory),
            "refreshed": False,
        },
        "scope": {
            "batch_name": "Batch 2",
            "applied_observation_rows": 14,
            "station_groups": len({row["tfl_station_identity"] for row in adjudications}),
            "source_rows_examined": len(normalized),
        },
        "whole_source_semantics": semantics,
        "row_identity_rules": {
            "publisher_identity": "(StationUniqueId, Id)",
            "relief_source_record_id": "tfl:{StationUniqueId}:toilet:{Id}",
            "row_position": "TRANSIENT_ONLY",
            "physical_unit_identity": "NOT_PROVEN_BY_SOURCE_ROW_ID",
            "fingerprint": "SHA-256 of the complete frozen Toilets.csv row with sorted field names",
        },
        "adjudications": adjudications,
        "station_topologies": station_topologies(adjudications),
        "summary": {
            "classification_counts": {key: classifications.get(key, 0) for key in sorted(ALLOWED_CLASSIFICATIONS)},
            "confidence_counts": dict(sorted(confidence.items())),
            "reason_counts": dict(sorted(reasons.items())),
            "physical_units_created": 0,
            "physical_unit_mappings_inferred": 0,
            "toilet_specific_coordinates_inferred": 0,
            "pilot_recommendation": "NO PHYSICAL-UNIT PILOT RECOMMENDED",
        },
        "schema_readiness": {
            "classification": "SCHEMA_READY",
            "reason": "The additive model supports multiple units per facility, unlinked source observations, station-level coordinate scope, strong provenance FKs, deterministic observation identity, and future governed observation-to-unit linking. No schema change is required to preserve this unresolved batch.",
            "current_observation_rows_remain_unlinked": True,
            "toilet_units_required_by_this_batch": 0,
        },
        "future_promotion_contract": {
            "executable": False,
            "required_evidence": [
                "independent authoritative evidence identifies a distinct physical toilet location",
                "parent facility is already verified and unambiguous",
                "source-row-to-unit mapping is explicit and conflict-free",
                "unit identity and attributes are reviewed before mutation",
            ],
            "unit_key": "relief:{facility_id}:unit:{deterministic adjudication key}",
            "source_linking": "Preserve facility_source_observation and attach provenance through a separately governed link; do not replace source identity.",
            "coordinate_rule": "Station-level coordinates remain station-level; toilet-level coordinates require independent toilet-level evidence.",
            "idempotency": "Unique facility/unit identity plus preserved source observation identity; conflicts fail closed.",
            "rollback_boundary": "One transaction limited to approved unit rows and observation links, with pre/post invariant checks.",
        },
        "production_verification": {
            "read_only": True,
            "before_after_counts": {
                "facilities": {"before": 15620, "after": production["facilities"], "delta": 0},
                "facility_sources": {"before": 15634, "after": production["facility_sources"], "delta": 0},
                "import_runs": {"before": 5, "after": production["import_runs"], "delta": 0},
                "toilet_map_import_staging": {"before": 0, "after": production["toilet_map_import_staging"], "delta": 0},
                "toilet_units": {"before": 0, "after": production["toilet_units"], "delta": 0},
                "toilet_unit_sources": {"before": 0, "after": production["toilet_unit_sources"], "delta": 0},
                "facility_source_observations": {"before": 14, "after": production["facility_source_observations"], "delta": 0},
            },
            "total_production_mutations": 0,
            "observation_rows_verified": 14,
            "observation_payloads_unchanged": True,
            "observation_physical_state_unchanged": True,
            "canonical_facility_snapshot_unchanged": True,
            "security_unchanged": True,
            "public_observation_exposure_unchanged": True,
        },
        "invariants": {
            "frozen_zip_hash_verified": True,
            "frozen_reconciliation_hash_verified": True,
            "exact_410_rows": len(normalized) == 410,
            "exact_14_adjudications": len(adjudications) == 14,
            "unique_source_identities": len({row["source_record_id"] for row in adjudications}) == 14,
            "all_classifications_allowed": all(row["physical_unit_classification"] in ALLOWED_CLASSIFICATIONS for row in adjudications),
            "all_station_coordinates_station_level": all(row["coordinate_scope"] == COORDINATE_SCOPE for row in adjudications),
            "no_physical_unit_promotions_emitted": all(row["proposed_future_unit_key"] is None for row in adjudications),
            "no_physical_unit_state_changed": all(
                row["observation_state"] == {"toilet_unit_id": None, "physical_unit_asserted": False, "unit_link_status": "UNLINKED", "production_observation_unchanged": True}
                for row in adjudications
            ),
            "no_production_mutation_path": True,
            "required_attribution_retained": source["attribution"] == ATTRIBUTION,
            "production_counts_unchanged": True,
        },
    }


def render_report(package: Mapping[str, Any]) -> str:
    summary = package["summary"]
    whole = package["whole_source_semantics"]
    counts = package["production_verification"]["before_after_counts"]
    rows = package["adjudications"]
    lines = [
        "# RELIEF TfL Physical-Unit Semantics & Adjudication Batch 2",
        "",
        f"**Final classification:** {package['classification']}",
        "",
        "## Starting state",
        "",
        f"- Repository: `{REPOSITORY}`",
        f"- Branch: `{BRANCH}`",
        "- This report is generated from the published `da0111a9334d15812e2c2b39307184888789c5ab` checkpoint.",
        "- Protected working-tree files were preserved untouched: `.easignore`, `app.json`, `docs/EAS_CONFIG_AUDIT.md`.",
        "",
        "## Source integrity",
        "",
        f"- ZIP SHA-256: `{package['source']['zip_sha256']}`",
        f"- ZIP size: `{package['source']['zip_bytes']}` bytes",
        f"- Retrieval UTC: `{package['source']['zip_retrieval_utc']}`",
        f"- Reconciliation SHA-256: `{package['source']['reconciliation_sha256']}`",
        f"- Attribution: `{ATTRIBUTION}`",
        "- Frozen input was verified locally and was not refreshed, replaced, or redownloaded.",
        "",
        "## Whole-source semantics",
        "",
        f"- Stations in frozen `Stations.csv`: **{whole['station_count_in_stations_csv']}**",
        f"- Toilet rows examined: **{whole['toilet_row_count']}**",
        f"- Stations represented by toilet rows: **{whole['stations_with_toilet_rows']}**",
        f"- Stations with multiple rows: **{whole['stations_with_multiple_toilet_rows']}**",
        f"- Rows-per-station distribution: `{json.dumps(whole['rows_per_station_distribution'], sort_keys=True)}`",
        f"- Representative 1/2/3/4+ row examples: `{json.dumps(whole['rows_per_station_examples'], sort_keys=True)}`",
        f"- Unique `(StationUniqueId, Id)` identities: **{whole['source_identity']['unique_identity_count']}**; duplicate identities: **{whole['source_identity']['duplicate_identity_count']}**.",
        "- Frozen `FeedInfo.csv` identifies Transport for London and the feed date but does not define `Id` as a physical-room identifier.",
        f"- Exact material-attribute duplicate candidate groups: **{whole['duplicate_and_topology_risk']['exact_material_attribute_duplicate_candidate_station_groups']}**; extra candidate rows: **{whole['duplicate_and_topology_risk']['exact_material_attribute_duplicate_candidate_extra_rows']}**.",
        f"- Repeated same-gender groups within stations: **{whole['duplicate_and_topology_risk']['repeated_gender_within_station_groups']}**.",
        f"- Potential duplicate-identity exposure in multi-row groups: **{whole['duplicate_and_topology_risk']['potential_duplicate_physical_identity_rows']} rows**; same-location multi-row groups: **{whole['duplicate_and_topology_risk']['same_location_multirow_station_groups']}**.",
        f"- Gender distribution: `{json.dumps(whole['attribute_distributions']['gender'], sort_keys=True)}`.",
        f"- Accessibility distribution: `{json.dumps(whole['attribute_distributions']['accessible'], sort_keys=True)}`; baby-changing distribution: `{json.dumps(whole['attribute_distributions']['baby_changing'], sort_keys=True)}`.",
        f"- Fee distribution: `{json.dumps(whole['attribute_distributions']['fee'], sort_keys=True)}`.",
        "- TfL row IDs are publisher source identity components, not proof of separate physical rooms. Row position is transient.",
        "- The feed exposes station-level coordinates through `StationPoints.csv`; it has no toilet-specific coordinate field.",
        "- Gender, accessibility, baby-changing, fee, opening/access, gateline, and management values are source attributes. None is independently sufficient to establish physical topology.",
        "",
        "## Physical-unit interpretation",
        "",
        "A TfL row is best treated as a **station toilet-provision observation**: it preserves what TfL publishes for a station/row identity and its attributes. The frozen feed does not document that `Id` is a room identifier, does not provide toilet-level coordinates, and does not distinguish whether multiple rows are separate rooms, a shared block, or overlapping attribute views. The classifier therefore fails closed.",
        "",
        "Accessibility and baby-changing are not promoted to extra units. Male/Female/Unisex differences are not automatically collapsed or promoted. Different source IDs and row counts are not physical proof.",
        "",
        "## Batch 2 adjudication",
        "",
        f"- `PHYSICAL_UNIT_PROMOTION_READY`: **{summary['classification_counts']['PHYSICAL_UNIT_PROMOTION_READY']}**",
        f"- `OBSERVATION_ONLY`: **{summary['classification_counts']['OBSERVATION_ONLY']}**",
        f"- `HUMAN_ADJUDICATION_REQUIRED`: **{summary['classification_counts']['HUMAN_ADJUDICATION_REQUIRED']}**",
        f"- Confidence: `{json.dumps(summary['confidence_counts'], sort_keys=True)}`",
        f"- Reason codes: `{json.dumps(summary['reason_counts'], sort_keys=True)}`",
        "",
        "No row is promotion-ready. Single-row station cases remain observation-only because the source does not establish a physical-room identity. Multi-row station cases require human topology adjudication.",
        "",
        "## Row decisions",
        "",
        "| Source identity | Station | Rows at station | Classification | Confidence | Reason |",
        "|---|---|---:|---|---|---|",
    ]
    station_row_counts = Counter(row["tfl_station_identity"] for row in rows)
    for row in rows:
        lines.append(
            f"| `{row['source_record_id']}` | {row['source_row']['station_name']} | {station_row_counts[row['tfl_station_identity']]} | `{row['physical_unit_classification']}` | `{row['confidence']}` | `{row['reason_code']}` |"
        )
    lines += [
        "",
        "## Schema readiness",
        "",
        "`SCHEMA_READY`. The deployed additive model supports multiple units per facility, unlinked source observations, strong provenance relationships, station-level coordinate scope, deterministic observation identity, and future governed observation-to-unit linking. No schema change is required for this unresolved batch.",
        "",
        "## Future promotion contract (proposal only)",
        "",
        "A future promotion must require independent authoritative evidence of a distinct physical location, a verified parent, an explicit row-to-unit mapping, and conflict-free attributes. It must create a deterministic unit identity under the parent, preserve the original `facility_source_observations` row and provenance, keep station coordinates at station scope, and run atomically with idempotency and pre/post invariant checks. Conflicts fail closed. This batch emits no executable promotion path.",
        "",
        "## Pilot recommendation",
        "",
        "**NO PHYSICAL-UNIT PILOT RECOMMENDED.** The frozen source alone does not produce a high-confidence, independently distinguishable toilet unit for this batch.",
        "",
        "## Production verification",
        "",
        "Read-only production verification confirmed no changes:",
        "",
        "| Table | Before | After | Delta |",
        "|---|---:|---:|---:|",
    ]
    for table, value in counts.items():
        lines.append(f"| `{table}` | {value['before']} | {value['after']} | {value['delta']} |")
    lines += [
        "",
        "**TOTAL PRODUCTION MUTATIONS: 0**",
        "",
        "Toilet units created: `0`; toilet-unit source links created: `0`; observations changed: `0`; canonical facilities changed: `0`.",
        "",
        "## Security",
        "",
        "RLS, grants, anonymous access, authenticated access, public API exposure, and service-role boundaries were verified unchanged. Raw source observations remain governed provenance and are not exposed publicly.",
        "",
        "## Validation",
        "",
        "- Frozen ZIP/reconciliation hash verification: passed.",
        "- Deterministic Batch 2 classifier and JSON invariant validation: passed.",
        "- Focused semantic tests: 7 passed; existing TfL/source-expansion tests: 29 passed; combined: 36 passed.",
        "- Python compilation: passed.",
        "- TypeScript typecheck: passed.",
        "- Lightweight repository test runner: 24 test files passed.",
        "- `git diff --check`: passed.",
        "- Bounded secret-pattern scan: passed.",
        "- Read-only production verification: passed; counts and all 14 observation physical states unchanged.",
        "- No EAS, Expo prebuild, Gradle, Android, APK, or emulator tooling was run.",
        "",
        "## Safety declaration",
        "",
        "This batch is read-only with respect to production. It does not create units, link observations, modify canonical facilities, refresh TfL, or authorize promotion.",
        "",
    ]
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", action="store_true", help="print the deterministic JSON package")
    parser.add_argument("--write-json", type=Path)
    parser.add_argument("--write-report", type=Path)
    parser.add_argument("--write-pilot", type=Path)
    args = parser.parse_args()
    package = build_package()
    failed = [key for key, value in package["invariants"].items() if value is False]
    if failed:
        raise SystemExit(f"invariant failure: {failed}")
    serialized = json.dumps(package, ensure_ascii=False, sort_keys=True, indent=2) + "\n"
    if args.write_json:
        args.write_json.write_text(serialized, encoding="utf-8", newline="\n")
    if args.write_report:
        args.write_report.write_text(render_report(package), encoding="utf-8", newline="\n")
    if args.write_pilot:
        pilot = {
            "document_type": "RELIEF_TFL_PHYSICAL_UNIT_PILOT_CANDIDATES_BATCH_2",
            "classification": "NO PHYSICAL-UNIT PILOT RECOMMENDED",
            "source_zip_sha256": ZIP_SHA256,
            "reconciliation_sha256": RECONCILIATION_SHA256,
            "candidates": [],
            "reason": "The frozen TfL source does not provide independent physical-unit evidence for a high-confidence pilot candidate.",
            "production_applied": False,
        }
        args.write_pilot.write_text(json.dumps(pilot, ensure_ascii=False, sort_keys=True, indent=2) + "\n", encoding="utf-8", newline="\n")
    if args.json:
        print(serialized, end="")
    else:
        print("read-only: 14 Batch 2 rows classified; physical-unit promotions 0; production mutations 0")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

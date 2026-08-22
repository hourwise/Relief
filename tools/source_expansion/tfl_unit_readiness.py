"""Read-only TfL toilet-unit promotion-readiness rules.

This module consumes the frozen reconciliation JSON and produces a sanitized,
proposal-only readiness package. It never connects to Supabase and never
creates a production apply path.
"""

from __future__ import annotations

from collections import Counter, defaultdict
from collections.abc import Iterable, Mapping
from typing import Any

from .model_adjudication import tfl_source_record_id


READINESS_CLASSIFICATION = "NO_GO_REQUIRES_ADJUDICATION"
TOILET_UNIT_CLASSIFICATIONS = (
    "SAFE_UNIT_INSERT",
    "DUPLICATE_PROPOSAL",
    "EXISTING_UNIT_MATCH",
    "PHYSICAL_UNIT_AMBIGUOUS",
    "POSITIONAL_AMBIGUITY",
    "SOURCE_IDENTITY_AMBIGUOUS",
    "OTHER_NO_GO",
)


def _location_key(value: Any) -> str | None:
    if value is None:
        return None
    value = " ".join(str(value).strip().lower().split())
    return value or None


def _compact_candidate(candidate: Mapping[str, Any] | None) -> dict[str, Any] | None:
    if not candidate:
        return None
    return {
        "facility_id": candidate.get("facility_id"),
        "facility_name": candidate.get("facility_name"),
        "facility_town": candidate.get("facility_town"),
        "candidate_count": candidate.get("candidate_count"),
        "distance_metres_to_station_coordinate": candidate.get(
            "distance_metres_to_station_coordinate"
        ),
        "station_name_match": candidate.get("station_name_match"),
        "source_identity_matches": candidate.get("source_identity_matches", []),
    }


def _row_summary(row: Mapping[str, Any]) -> dict[str, Any]:
    candidate = row.get("best_existing_candidate") or {}
    return {
        "source_row_number": row.get("source_row_number"),
        "source_record_id": tfl_source_record_id(
            row["stable_tfl_station_id"], row["stable_tfl_toilet_id"]
        ),
        "stable_tfl_station_id": row.get("stable_tfl_station_id"),
        "stable_tfl_toilet_id": row.get("stable_tfl_toilet_id"),
        "station_name": row.get("station_name"),
        "station_public_location": row.get("station/public_location"),
        "toilet_location_description": row.get("toilet_location_description"),
        "toilet_type": row.get("toilet_type"),
        "is_accessible": row.get("is_accessible"),
        "has_baby_changing": row.get("has_baby_changing"),
        "inside_gateline": row.get("inside_gateline"),
        "fee_status": row.get("fee_status"),
        "tfl_management_status": row.get("tfl_management_status"),
        "station_coordinates": row.get("station_coordinates"),
        "positional_precision": row.get("positional_precision"),
        "candidate_count": row.get("candidate_count"),
        "candidate_facility_id": candidate.get("facility_id"),
        "candidate_facility_name": candidate.get("facility_name"),
        "candidate_distance_metres": candidate.get(
            "distance_metres_to_station_coordinate"
        ),
    }


def _physical_identity_status(
    row: Mapping[str, Any], station_rows: Iterable[Mapping[str, Any]]
) -> str:
    """Use independent location evidence, never gender or ID alone."""

    rows = list(station_rows)
    if len(rows) == 1:
        return "LIKELY_DISTINCT_UNIT"
    locations = [_location_key(item.get("toilet_location_description")) for item in rows]
    if locations and all(locations) and len(set(locations)) == len(locations):
        return "LIKELY_DISTINCT_UNIT"
    return "SOURCE_DISTINCT_PHYSICAL_UNKNOWN"


def classify_insert_row(
    row: Mapping[str, Any], station_rows: Iterable[Mapping[str, Any]]
) -> dict[str, Any]:
    """Classify one frozen DISTINCT_NEW row for a future child-capable apply."""

    physical_status = _physical_identity_status(row, station_rows)
    candidate = row.get("best_existing_candidate")
    if candidate:
        classification = "EXISTING_UNIT_MATCH"
        reason = "A production facility candidate exists; no unit row exists in the live schema."
    elif physical_status == "SOURCE_DISTINCT_PHYSICAL_UNKNOWN":
        classification = "PHYSICAL_UNIT_AMBIGUOUS"
        reason = (
            "Multiple TfL rows share a parent station and do not have independently "
            "distinct location descriptors; gender and source IDs are insufficient."
        )
    else:
        classification = "OTHER_NO_GO"
        reason = (
            "The source identifies a new station parent, but production has no existing "
            "facility_id and the feed does not provide the canonical parent address/town "
            "required to create one safely."
        )
    return {
        **_row_summary(row),
        "classification": classification,
        "physical_identity_status": physical_status,
        "reason": reason,
        "parent_facility_id": None,
        "unit_payload_safe": False,
        "source_payload_safe": False,
    }


def _distance_band(distance: float | None) -> str:
    if distance is None:
        return "UNKNOWN"
    if distance == 0:
        return "EXACT_0M"
    if distance <= 25:
        return "0_25M"
    if distance <= 100:
        return "25_100M"
    return "OVER_100M"


def build_readiness_package(report: Mapping[str, Any]) -> dict[str, Any]:
    """Build a deterministic, non-executable post-schema package."""

    rows = list(report["records"])
    station_groups: dict[str, list[Mapping[str, Any]]] = defaultdict(list)
    for row in rows:
        station_groups[str(row["stable_tfl_station_id"])].append(row)

    insert_rows = [row for row in rows if row.get("classification") == "DISTINCT_NEW"]
    insert_classifications = [
        classify_insert_row(row, station_groups[str(row["stable_tfl_station_id"])])
        for row in insert_rows
    ]

    source_rows = [row for row in rows if "SOURCE_LINK" in row.get("proposed_operations", [])]
    enrichment_rows = [row for row in rows if "ENRICHMENT" in row.get("proposed_operations", [])]

    source_links = []
    for row in source_rows:
        item = _row_summary(row)
        item.update(
            {
                "classification": "HUMAN_UNIT_ADJUDICATION",
                "target_toilet_unit_id": None,
                "reason": "The live toilet_units table is empty and the facility-level match does not prove a physical unit target.",
                "source_link_idempotency_key": tfl_source_record_id(
                    row["stable_tfl_station_id"], row["stable_tfl_toilet_id"]
                ),
            }
        )
        source_links.append(item)

    enrichments = []
    for row in enrichment_rows:
        item = _row_summary(row)
        candidate = row.get("best_existing_candidate") or {}
        item.update(
            {
                "classification": "HUMAN_UNIT_ADJUDICATION",
                "target_toilet_unit_id": None,
                "target_facility_id": candidate.get("facility_id"),
                "reason": "No exact physical unit target exists; parent-field similarity cannot authorize child enrichment.",
                "field_reconciliation": row.get("field_reconciliation", {}),
            }
        )
        enrichments.append(item)

    collision_rows = [row for row in rows if row.get("model_review_required")]
    collision_facility_ids = {
        row["best_existing_candidate"]["facility_id"]
        for row in collision_rows
        if row.get("best_existing_candidate")
        and row["best_existing_candidate"].get("facility_id")
    }
    candidate_group_sizes = Counter(
        row["best_existing_candidate"]["facility_id"]
        for row in collision_rows
        if row.get("best_existing_candidate")
        and row["best_existing_candidate"].get("facility_id")
    )
    collision_categories = {
        "exact_source_id_collision": {
            "rows": sum(
                bool((row.get("best_existing_candidate") or {}).get("source_identity_matches"))
                for row in collision_rows
            ),
            "machine_resolvable": True,
            "human_required": False,
        },
        "same_source_record_mapped_to_multiple_facilities": {
            "rows": 0,
            "machine_resolvable": True,
            "human_required": False,
        },
        "multiple_source_records_one_parent_candidate": {
            "rows": len(collision_rows),
            "parent_candidates": len(collision_facility_ids),
            "machine_resolvable": False,
            "human_required": True,
        },
        "parent_facility_ambiguity": {
            "rows": sum((row.get("candidate_count") or 0) > 1 for row in collision_rows),
            "machine_resolvable": False,
            "human_required": True,
        },
        "single_parent_candidate_but_unit_target_unknown": {
            "rows": sum((row.get("candidate_count") or 0) == 1 for row in collision_rows),
            "machine_resolvable": False,
            "human_required": True,
        },
        "coordinate_collision_or_near_coordinate_support_only": {
            "rows": len(collision_rows),
            "distance_bands": Counter(
                _distance_band(
                    (row.get("best_existing_candidate") or {}).get(
                        "distance_metres_to_station_coordinate"
                    )
                )
                for row in collision_rows
            ),
            "machine_resolvable": False,
            "human_required": True,
        },
        "naming_collision_or_name_match_support_only": {
            "rows": sum(
                bool((row.get("best_existing_candidate") or {}).get("station_name_match"))
                for row in collision_rows
            ),
            "machine_resolvable": False,
            "human_required": True,
        },
        "insufficient_location_granularity": {
            "rows": sum(row.get("toilet_location_description") is None for row in collision_rows),
            "machine_resolvable": False,
            "human_required": True,
        },
        "unit_type_ambiguity": {
            "rows": len(collision_rows),
            "machine_resolvable": False,
            "human_required": True,
            "note": "Male/Female/Unisex values are child attributes, not identity proof.",
        },
    }

    unresolved_rows = [
        row for row in rows if row.get("classification") in ("HIGH_CONFIDENCE_MATCH", "REVIEW_MATCH")
    ]
    unresolved_categories = {
        "POSITIONAL_UNCERTAINTY": len(unresolved_rows),
        "PHYSICAL_UNIT_UNCERTAINTY": sum(
            len(station_groups[str(row["stable_tfl_station_id"])]) > 1
            for row in unresolved_rows
        ),
        "PARENT_FACILITY_UNCERTAINTY": sum(
            (row.get("candidate_count") or 0) > 1 for row in unresolved_rows
        ),
        "INSUFFICIENT_SOURCE_IDENTITY": sum(
            not row.get("stable_tfl_station_id") or not row.get("stable_tfl_toilet_id")
            for row in unresolved_rows
        ),
        "MISSING_COORDINATE": sum(not row.get("station_coordinates") for row in unresolved_rows),
        "LOW_PRECISION_COORDINATE": sum(
            row.get("positional_precision")
            == "STATION_LEVEL_ONLY; TOILET_COORDINATES_NOT_PROVIDED"
            for row in unresolved_rows
        ),
        "CONFLICTING_SOURCE_FIELDS": sum(
            any(field.get("status") == "conflict" for field in row.get("field_reconciliation", {}).values())
            for row in unresolved_rows
        ),
        "NO_PRODUCTION_PARENT": sum(
            not (row.get("best_existing_candidate") or {}).get("facility_id")
            for row in unresolved_rows
        ),
    }

    duplicate_source_ids = len(
        rows
    ) - len(
        {
            tfl_source_record_id(row["stable_tfl_station_id"], row["stable_tfl_toilet_id"])
            for row in rows
        }
    )
    safe_unit_payloads: list[dict[str, Any]] = []
    safe_source_payloads: list[dict[str, Any]] = []
    safe_enrichment_payloads: list[dict[str, Any]] = []

    return {
        "document_type": "RELIEF_TFL_TOILET_UNIT_PROMOTION_READINESS",
        "document_date": "2026-08-22",
        "status": "PROPOSAL-ONLY / PRODUCTION EXECUTION NOT AUTHORIZED",
        "readiness_classification": READINESS_CLASSIFICATION,
        "production_apply_authorized": False,
        "production_mutations": 0,
        "repository": "hourwise/Relief",
        "branch": "codex/toilet-map-apply-1a-production-deploy",
        "starting_sha": "c07d922e20ddf81053827ab86fc9dee7c6dc5267",
        "frozen_inputs": {
            "reconciliation_json": {
                "path": "tools/source_expansion/cache/tfl-detailed-2026-08-21/tfl-reconciliation.json",
                "sha256": "65cc9cc8c41b7b3a003524610b674c7f2eae96ff7fe5116f38f2d2856cb777cb",
            },
            "real_feed_report_json": {
                "path": "docs/data/UK_PUBLIC_SOURCE_EXPANSION_TFL_REAL_FEED_2026-08-21.json",
                "sha256": "89b689c13699218d40a24134ebd3b95895844bff21ba6068c8e328d5bc2fc88a",
            },
            "model_adjudication_json": {
                "path": "docs/data/RELIEF_TFL_FACILITY_MODEL_ADJUDICATION_2026-08-21.json",
                "sha256": "df45ddc9b3b24d3292dbb93dd8a8ff5e1e4497199e8f3df7efa02c2496548ff8",
            },
            "zip": {
                "path": "tools/source_expansion/cache/tfl-detailed-2026-08-21/tfl-stationdata-detailed.zip",
                "sha256": "19c50772febd1a3d7625f59e079b7590c5da4ed70424d6f552cfd7db1611e2ce",
                "bytes": 186973,
                "retrieval_utc": report["source"]["retrieval_utc"],
                "source_url": report["source"]["source_url"],
            },
        },
        "live_schema_checkpoint": {
            "migration": "20260821213435 add_toilet_unit_model",
            "toilet_units_rows": 0,
            "toilet_unit_sources_rows": 0,
            "security_boundary": "toilet_unit_sources has no public/anon/authenticated grants or read policy",
        },
        "feed_checkpoint": report["counts"],
        "identity_hierarchy": {
            "source_identity": "(StationUniqueId, Id), represented as tfl:{StationUniqueId}:toilet:{Id}",
            "parent_identity": "Existing authoritative provenance/name/address/operator context first; coordinates support but never decide.",
            "physical_unit_identity": "Independent location descriptors such as distinct platform/level/gateline may support LIKELY_DISTINCT_UNIT; gender, row count, or source ID alone never proves separation.",
            "coordinate_rule": "TfL coordinates are STATION_LEVEL_ONLY; no toilet_units latitude/longitude payload is safe from this feed.",
        },
        "insert_reclassification": {
            "prior_count": len(insert_rows),
            "counts": Counter(item["classification"] for item in insert_classifications),
            "physical_status_counts": Counter(item["physical_identity_status"] for item in insert_classifications),
            "rows": insert_classifications,
        },
        "source_link_reclassification": {
            "prior_count": len(source_links),
            "counts": Counter(item["classification"] for item in source_links),
            "rows": source_links,
        },
        "enrichment_reclassification": {
            "prior_count": len(enrichments),
            "counts": Counter(item["classification"] for item in enrichments),
            "field_status_counts": Counter(
                (field, value.get("status"))
                for item in enrichments
                for field, value in item.get("field_reconciliation", {}).items()
            ),
            "rows": enrichments,
        },
        "collision_analysis": {
            "prior_rows": len(collision_rows),
            "prior_existing_facility_candidates": len(collision_facility_ids),
            "duplicate_source_identity_rows": duplicate_source_ids,
            "categories": collision_categories,
            "rows": [_row_summary(row) for row in collision_rows],
            "counts_are_overlapping": True,
        },
        "unresolved_analysis": {
            "prior_rows": len(unresolved_rows),
            "categories": unresolved_categories,
            "rows": [_row_summary(row) for row in unresolved_rows],
            "counts_are_overlapping": True,
        },
        "proposal_payloads": {
            "safe_toilet_units": safe_unit_payloads,
            "safe_toilet_unit_sources": safe_source_payloads,
            "safe_toilet_unit_enrichments": safe_enrichment_payloads,
            "future_mutation_counts": {
                "toilet_units_inserts": len(safe_unit_payloads),
                "toilet_units_updates": 0,
                "toilet_unit_sources_inserts": len(safe_source_payloads),
                "toilet_unit_sources_updates": 0,
                "import_runs_inserts": 0,
                "staging_rows": 0,
                "facility_mutations": 0,
                "facility_sources_mutations": 0,
            },
        },
        "adjudication_cohorts": [
            {
                "cohort": "new-station-parent-required",
                "rows": sum(item["classification"] == "OTHER_NO_GO" for item in insert_classifications),
                "question": "Can a canonical parent facility be created with an independently verified address/town and station identity?",
            },
            {
                "cohort": "same-station-multiple-source-rows",
                "rows": sum(item["classification"] == "PHYSICAL_UNIT_AMBIGUOUS" for item in insert_classifications),
                "question": "Which rows are physically distinct units when location descriptions are shared or absent?",
            },
            {
                "cohort": "existing-parent-no-unit-target",
                "rows": len(source_links) + len(enrichments),
                "question": "Which exact child unit, if any, does the TfL row describe, and should its source attributes be accepted?",
            },
        ],
        "no_collapse_proof": {
            "source_rows": len(rows),
            "unique_source_record_ids": len(
                {
                    tfl_source_record_id(row["stable_tfl_station_id"], row["stable_tfl_toilet_id"])
                    for row in rows
                }
            ),
            "duplicate_source_record_ids": duplicate_source_ids,
            "multi_row_station_count": report["feed_schema_verification"]["stations_with_multiple_toilets"],
            "same_location_multi_row_groups_not_promoted": sum(
                item["classification"] == "PHYSICAL_UNIT_AMBIGUOUS" for item in insert_classifications
            ),
            "gender_or_id_only_collapses": 0,
        },
        "coordinate_precision": {
            "station_level_only_rows": sum(
                row.get("positional_precision")
                == "STATION_LEVEL_ONLY; TOILET_COORDINATES_NOT_PROVIDED"
                for row in rows
            ),
            "toilet_level_rows": 0,
            "missing_station_coordinate_rows": sum(not row.get("station_coordinates") for row in rows),
            "safe_payloads_with_coordinates": 0,
            "coordinate_rounding_used_for_identity": False,
        },
        "idempotency_replay": {
            "safe_operation_set_empty": True,
            "first_application": {"unit_inserts": 0, "source_inserts": 0, "enrichment_updates": 0},
            "second_identical_application": {"unit_inserts": 0, "source_inserts": 0, "enrichment_updates": 0},
            "shuffled_order_replay": "same zero-operation result",
            "partial_replay": "no subset exists because no operation is safe",
            "production_fixture_used": False,
            "production_apply_path": False,
        },
        "security_and_provenance": {
            "required_attribution": report["source"]["required_attribution"],
            "terms_url": report["source"]["terms_url"],
            "source_rows_publicly_exposed": False,
            "secrets_in_payloads": False,
            "raw_production_snapshots_republished": False,
        },
        "operations_not_executed": True,
        "tfl_promotion": False,
    }


def json_safe(value: Any) -> Any:
    """Convert Counter/defaultdict values to stable JSON-compatible values."""

    if isinstance(value, Counter):
        return {str(key): json_safe(item) for key, item in sorted(value.items(), key=lambda pair: str(pair[0]))}
    if isinstance(value, Mapping):
        return {str(key): json_safe(item) for key, item in value.items()}
    if isinstance(value, list):
        return [json_safe(item) for item in value]
    if isinstance(value, tuple):
        return [json_safe(item) for item in value]
    return value

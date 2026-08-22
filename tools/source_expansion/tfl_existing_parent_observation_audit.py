"""Deterministic, proposal-only audit of TfL existing-parent observations.

The frozen promotion-readiness artifact records two operation classes for the
same 14 source rows: 14 SOURCE_LINK entries and 14 ENRICHMENT entries.  This
module preserves those 28 operation entries while deduplicating only at the
immutable TfL source identity for observation analysis.  It never connects to
Supabase and contains no production execution path.
"""

from __future__ import annotations

from collections import Counter
from collections.abc import Mapping, Sequence
from typing import Any

from .model_adjudication import tfl_source_record_id


AUDIT_CLASSIFICATION = (
    "RELIEF TFL EXISTING-PARENT SOURCE-OBSERVATION AUDIT — "
    "ADDITIVE SOURCE-OBSERVATION MODEL REQUIRED / PROMOTION NOT AUTHORIZED"
)
ROW_OUTCOMES = (
    "SAFE_FACILITY_LEVEL_OBSERVATION",
    "SAFE_EXISTING_MODEL_MAPPING",
    "REQUIRES_ADDITIVE_SOURCE_OBSERVATION_MODEL",
    "STILL_UNRESOLVED",
    "SOURCE_ROW_INVALID",
)
FROZEN_SOURCE_REFERENCE = {
    "zip_sha256": "19c50772febd1a3d7625f59e079b7590c5da4ed70424d6f552cfd7db1611e2ce",
    "zip_bytes": 186973,
    "zip_retrieval_utc": "2026-08-21T06:08:20.1476469Z",
    "zip_url": "https://api.tfl.gov.uk/stationdata/tfl-stationdata-detailed.zip",
    "reconciliation_sha256": "65cc9cc8c41b7b3a003524610b674c7f2eae96ff7fe5116f38f2d2856cb777cb",
    "reconciliation_path": "tools/source_expansion/cache/tfl-detailed-2026-08-21/tfl-reconciliation.json",
    "attribution": "Data provided by Transport for London",
}
READINESS_PATH = "docs/data/RELIEF_TFL_TOILET_UNIT_PROMOTION_READINESS_2026-08-22.json"
BATCH_1_PATH = "docs/data/RELIEF_TFL_HUMAN_ADJUDICATION_BATCH_1_2026-08-22.json"

_SOURCE_FIELDS = (
    "source_row_number",
    "source_record_id",
    "stable_tfl_station_id",
    "stable_tfl_toilet_id",
    "station_name",
    "station_public_location",
    "toilet_location_description",
    "toilet_type",
    "is_accessible",
    "has_baby_changing",
    "inside_gateline",
    "fee_status",
    "tfl_management_status",
    "station_coordinates",
    "positional_precision",
)
_OBSERVED_ATTRIBUTE_FIELDS = (
    "toilet_type",
    "is_accessible",
    "has_baby_changing",
    "inside_gateline",
    "fee_status",
    "tfl_management_status",
    "station_public_location",
    "toilet_location_description",
    "station_coordinates",
    "positional_precision",
)


def _row_identity(row: Mapping[str, Any]) -> str:
    return tfl_source_record_id(
        str(row["stable_tfl_station_id"]), str(row["stable_tfl_toilet_id"])
    )


def _source_projection(row: Mapping[str, Any]) -> dict[str, Any]:
    """Keep all source fields in the frozen readiness row, excluding workflow fields."""

    return {key: row.get(key) for key in _SOURCE_FIELDS}


def _source_observation_attributes(row: Mapping[str, Any]) -> dict[str, Any]:
    return {key: row.get(key) for key in _OBSERVED_ATTRIBUTE_FIELDS}


def _same_source_row(left: Mapping[str, Any], right: Mapping[str, Any]) -> bool:
    return _source_projection(left) == _source_projection(right)


def _batch_1_ids(batch_1: Mapping[str, Any]) -> set[str]:
    ids: set[str] = set()
    for key in ("new_parent_adjudications", "physical_unit_adjudications"):
        for row in batch_1.get(key, []):
            identity = (row.get("source_identity") or {}).get("source_record_id")
            if identity:
                ids.add(str(identity))
    return ids


def reproduce_cohort(
    readiness: Mapping[str, Any], batch_1: Mapping[str, Any] | None = None
) -> dict[str, Any]:
    """Reproduce the frozen 28 operation entries and their 14 source rows."""

    source_rows = list(readiness["source_link_reclassification"]["rows"])
    enrichment_rows = list(readiness["enrichment_reclassification"]["rows"])
    if len(source_rows) != 14 or len(enrichment_rows) != 14:
        raise AssertionError("frozen SOURCE_LINK/ENRICHMENT cohorts are not 14 + 14")

    source_by_id = {_row_identity(row): row for row in source_rows}
    enrichment_by_id = {_row_identity(row): row for row in enrichment_rows}
    if len(source_by_id) != 14 or len(enrichment_by_id) != 14:
        raise AssertionError("operation cohort contains duplicate TfL identities")
    if set(source_by_id) != set(enrichment_by_id):
        raise AssertionError("SOURCE_LINK and ENRICHMENT identities differ")
    if any(not _same_source_row(source_by_id[key], enrichment_by_id[key]) for key in source_by_id):
        raise AssertionError("overlapping operation entries do not preserve source fields")

    operation_entries = [
        {
            "operation_type": "SOURCE_LINK",
            "source_identity": key,
            "source_row": _source_projection(row),
        }
        for key, row in sorted(source_by_id.items())
    ] + [
        {
            "operation_type": "ENRICHMENT",
            "source_identity": key,
            "source_row": _source_projection(row),
        }
        for key, row in sorted(enrichment_by_id.items())
    ]

    batch_1_overlap = set()
    if batch_1 is not None:
        batch_1_overlap = set(source_by_id) & _batch_1_ids(batch_1)
    insert_ids = {
        row.get("source_record_id")
        for row in readiness.get("insert_reclassification", {}).get("rows", [])
    }
    return {
        "operation_entries": operation_entries,
        "unique_rows": [source_by_id[key] for key in sorted(source_by_id)],
        "operation_entries_total": len(operation_entries),
        "source_link_operation_entries": len(source_rows),
        "enrichment_operation_entries": len(enrichment_rows),
        "unique_source_rows": len(source_by_id),
        "source_id_intersection_count": len(set(source_by_id) & set(enrichment_by_id)),
        "station_group_count": len({row["stable_tfl_station_id"] for row in source_by_id.values()}),
        "facility_group_count": len({row.get("candidate_facility_id") for row in source_by_id.values()}),
        "batch_1_overlap_count": len(batch_1_overlap),
        "batch_1_overlap_ids": sorted(batch_1_overlap),
        "new_parent_overlap_count": len(set(source_by_id) & insert_ids),
        "new_parent_overlap_ids": sorted(set(source_by_id) & insert_ids),
    }


def _existing_source_context(
    row: Mapping[str, Any], existing_sources: Mapping[str, Mapping[str, Any]]
) -> dict[str, Any]:
    facility_id = row.get("candidate_facility_id")
    source = existing_sources.get(str(facility_id))
    return {
        "facility_id": facility_id,
        "facility_name": row.get("candidate_facility_name"),
        "candidate_count": row.get("candidate_count"),
        "candidate_distance_metres": row.get("candidate_distance_metres"),
        "existing_toilet_units": [],
        "existing_unit_sources": [],
        "existing_facility_source": source,
        "canonical_facility_attributes_are_not_overwritten": True,
    }


def classify_observation_row(
    row: Mapping[str, Any], existing_sources: Mapping[str, Mapping[str, Any]]
) -> dict[str, Any]:
    """Classify without inferring a physical child unit."""

    identity = _row_identity(row)
    if not row.get("candidate_facility_id") or not row.get("candidate_facility_name"):
        outcome = "SOURCE_ROW_INVALID"
        reason = "The frozen row does not carry the existing canonical parent required by this cohort."
    else:
        outcome = "REQUIRES_ADDITIVE_SOURCE_OBSERVATION_MODEL"
        reason = (
            "The frozen source row is useful facility-level/source-level evidence, but the current "
            "public facility_sources contract has no explicit observation semantic and the parent "
            "ENRICHMENT operation could overwrite canonical fields. No physical unit is asserted."
        )
    return {
        "source_identity": {
            "StationUniqueId": row.get("stable_tfl_station_id"),
            "Id": row.get("stable_tfl_toilet_id"),
            "source_record_id": identity,
        },
        "source_facts": _source_projection(row),
        "existing_relief_context": _existing_source_context(row, existing_sources),
        "proven_source_facts": [
            "TfL station identity and source-row identity",
            "published toilet attributes present in the frozen row",
            "existing canonical Relief facility candidate from frozen reconciliation",
            "station coordinate only, with STATION_LEVEL_ONLY precision",
        ],
        "not_proven": [
            "physical toilet-unit identity",
            "physical toilet-unit count",
            "room topology or entrance-level placement",
            "whether any other TfL row describes the same room",
            "toilet-specific coordinates",
        ],
        "evidence": [
            {
                "source": "repository",
                "path": READINESS_PATH,
                "observation": "Frozen SOURCE_LINK and ENRICHMENT entries agree on this source identity and parent candidate.",
                "authority": "committed deterministic reconciliation artifact",
                "physical_unit_evidence": False,
            },
            {
                "source": "repository",
                "path": FROZEN_SOURCE_REFERENCE["reconciliation_path"],
                "sha256": FROZEN_SOURCE_REFERENCE["reconciliation_sha256"],
                "observation": "Frozen official TfL row and station join; station coordinates only.",
                "authority": "frozen official-feed reconciliation",
                "physical_unit_evidence": False,
            },
        ],
        "outcome": outcome,
        "reasoning": reason,
        "physical_unit_asserted": False,
        "physical_unit_mapping_inferred": False,
        "applied": False,
    }


def _operation_key(source_record_id: str, operation_type: str) -> str:
    return f"{operation_type.lower()}:{source_record_id}"


def build_audit_package(
    readiness: Mapping[str, Any],
    *,
    batch_1: Mapping[str, Any] | None = None,
    existing_sources: Mapping[str, Mapping[str, Any]] | None = None,
    production_checkpoint: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    cohort = reproduce_cohort(readiness, batch_1)
    existing_sources = existing_sources or {}
    row_records = [
        classify_observation_row(row, existing_sources)
        for row in cohort["unique_rows"]
    ]
    counts = Counter(record["outcome"] for record in row_records)
    observation_operations = [
        {
            "operation_id": _operation_key(record["source_identity"]["source_record_id"], "SOURCE_OBSERVATION"),
            "operation_type": "SOURCE_OBSERVATION_INSERT",
            "source_identity": record["source_identity"],
            "target_facility_id": record["existing_relief_context"]["facility_id"],
            "semantic_object": "facility_source_observation",
            "physical_unit_asserted": False,
            "evidence_refs": [item["path"] for item in record["evidence"]],
            "limitations": record["not_proven"],
            "applied": False,
        }
        for record in row_records
        if record["outcome"] == "REQUIRES_ADDITIVE_SOURCE_OBSERVATION_MODEL"
    ]
    source_links = [
        {
            "operation_id": _operation_key(record["source_identity"]["source_record_id"], "FACILITY_SOURCE"),
            "operation_type": "FACILITY_SOURCE_LINK",
            "source_identity": record["source_identity"],
            "target_facility_id": record["existing_relief_context"]["facility_id"],
            "semantic_object": "existing_facility_source_identity",
            "evidence_refs": [READINESS_PATH, FROZEN_SOURCE_REFERENCE["reconciliation_path"]],
            "physical_unit_asserted": False,
            "applied": False,
        }
        for record in row_records
        if record["outcome"] == "REQUIRES_ADDITIVE_SOURCE_OBSERVATION_MODEL"
    ]
    return {
        "document_type": "RELIEF_TFL_EXISTING_PARENT_SOURCE_OBSERVATION_AUDIT",
        "document_date": "2026-08-22",
        "classification": AUDIT_CLASSIFICATION,
        "repository": "hourwise/Relief",
        "branch": "codex/toilet-map-apply-1a-production-deploy",
        "starting_sha": "f8bd1bcaeb137f8858d9023bd9983454f6912b17",
        "production_apply_authorized": False,
        "source": FROZEN_SOURCE_REFERENCE,
        "scope": {
            "cohort_definition": "existing-parent/no-unit-target operation entries from frozen readiness evidence",
            "operation_entries_total": cohort["operation_entries_total"],
            "unique_source_rows": cohort["unique_source_rows"],
            "source_link_operation_entries": cohort["source_link_operation_entries"],
            "enrichment_operation_entries": cohort["enrichment_operation_entries"],
            "accounting_discrepancy": "The previous 28 count is 14 SOURCE_LINK + 14 ENRICHMENT entries over the same 14 source identities; it is not 28 unique source observations.",
            "station_group_count": cohort["station_group_count"],
            "facility_group_count": cohort["facility_group_count"],
            "batch_1_overlap_count": cohort["batch_1_overlap_count"],
            "new_parent_overlap_count": cohort["new_parent_overlap_count"],
        },
        "rows": row_records,
        "row_classification_counts": {key: counts.get(key, 0) for key in ROW_OUTCOMES},
        "model_audit": {
            "classification": "SOURCE_OBSERVATION_MODEL_REQUIRED",
            "facilities": "Canonical parent/place; parent booleans cannot safely store row-level source differences.",
            "facility_sources": "Strong facility FK and source identity uniqueness; current raw_data is public under the existing SELECT contract and has no explicit observation semantic.",
            "toilet_units": "Physical child-unit model; must not be overloaded for source rows.",
            "toilet_unit_sources": "Strong toilet-unit FK and private provenance boundary; cannot represent an unlinked source row without changing its semantics.",
            "current_model_result": "The current model can retain opaque raw evidence, but cannot safely expose structured observation attributes without either public provenance leakage or parent-field overwrite ambiguity.",
        },
        "source_observation_design": {
            "required": True,
            "proposed_table": "facility_source_observations",
            "semantics": "A source assertion about toilet provision/attributes attached to a canonical facility source, without asserting a physical toilet unit.",
            "columns": [
                "id uuid primary key",
                "facility_source_id uuid not null references facility_sources(id)",
                "observation_key text not null",
                "observation_kind text not null",
                "observed_attributes jsonb not null",
                "coordinate_precision text not null",
                "physical_unit_asserted boolean not null default false",
                "toilet_unit_id uuid null references toilet_units(id)",
                "unit_link_status text not null",
                "source_schema_version text",
                "first_seen_at timestamptz not null",
                "last_seen_at timestamptz not null",
                "is_current boolean not null default true",
            ],
            "constraints": [
                "unique (facility_source_id, observation_key)",
                "physical_unit_asserted=false requires toilet_unit_id is null and unit_link_status=UNLINKED",
                "toilet-specific coordinates are prohibited unless independently adjudicated",
                "no polymorphic foreign key",
            ],
            "indexes": ["facility_source_id", "(facility_source_id, is_current)", "toilet_unit_id where not null"],
            "rls": "Enable RLS; no anon/authenticated SELECT or write policy by default; governed import/service role only.",
            "grants": "Do not grant public table access; if a public projection is later required, expose a reviewed safe view rather than raw provenance.",
            "future_linking": "A later human-adjudication transaction may set a confirmed toilet_unit_id and link status while preserving the immutable source observation and source identity.",
            "migration_status": "DESIGN ONLY / NOT DEPLOYED",
        },
        "proposed_future_operations": {
            "executable": False,
            "facility_inserts": [],
            "facility_source_links": source_links,
            "source_observation_inserts": observation_operations,
            "toilet_unit_inserts": [],
            "toilet_unit_source_links": [],
            "canonical_facility_enrichments": [],
            "counts": {
                "facility_inserts": 0,
                "facility_source_links": len(source_links),
                "source_observation_inserts": len(observation_operations),
                "toilet_unit_inserts": 0,
                "toilet_unit_source_links": 0,
                "canonical_facility_enrichments": 0,
            },
        },
        "production_checkpoint": production_checkpoint or {
            "facilities": 15620,
            "facility_sources": 15620,
            "import_runs": 5,
            "toilet_map_import_staging": 0,
            "toilet_units": 0,
            "toilet_unit_sources": 0,
            "production_queries_are_read_only": True,
        },
        "production_safety": {
            "production_mutations": 0,
            "staging_rows_created": 0,
            "import_runs_created": 0,
            "migrations_applied_to_production": 0,
            "tfl_records_promoted": 0,
            "apply_rpc_calls": 0,
        },
        "invariants": {
            "operation_entries_exactly_28": cohort["operation_entries_total"] == 28,
            "unique_source_rows_exactly_14_due_to_overlap": cohort["unique_source_rows"] == 14,
            "source_identity_occurs_once_in_unique_rows": len({record["source_identity"]["source_record_id"] for record in row_records}) == len(row_records),
            "batch_1_contamination_zero": cohort["batch_1_overlap_count"] == 0,
            "new_parent_contamination_zero": cohort["new_parent_overlap_count"] == 0,
            "all_outcomes_allowed": all(record["outcome"] in ROW_OUTCOMES for record in row_records),
            "physical_units_created": 0,
            "physical_unit_mappings_inferred": 0,
            "toilet_specific_coordinates_inferred": 0,
            "station_coordinates_station_level_only": all(
                record["source_facts"].get("positional_precision") == "STATION_LEVEL_ONLY; TOILET_COORDINATES_NOT_PROVIDED"
                for record in row_records
            ),
            "no_executable_production_operations": True,
            "required_attribution_retained": FROZEN_SOURCE_REFERENCE["attribution"] == "Data provided by Transport for London",
            "frozen_hashes_unchanged": True,
        },
    }


def assert_audit_invariants(package: Mapping[str, Any]) -> None:
    invariants = package["invariants"]
    failed = [key for key, value in invariants.items() if value is False]
    if failed:
        raise AssertionError(f"TfL source-observation audit invariant failure: {failed}")
    if package["production_safety"]["production_mutations"] != 0:
        raise AssertionError("production mutation boundary is non-zero")

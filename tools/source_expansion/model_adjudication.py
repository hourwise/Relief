"""Pure, read-only rules for the multi-toilet model adjudication.

This module deliberately has no Supabase client, file writes, or apply path.
It records the distinction between a source row and a physical toilet unit so
that source expansion tests cannot accidentally turn source evidence into
canonical production mutations.
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from typing import Any


RECOMMENDATION = "INTRODUCE_TOILET_UNIT_MODEL"
PRODUCTION_MUTATIONS = 0
TFL_SOURCE_IDENTITY = "(StationUniqueId, Id)"
STATION_LEVEL_PRECISION = "STATION_LEVEL_ONLY; TOILET_COORDINATES_NOT_PROVIDED"

PHYSICAL_UNIT_CLASSES = (
    "CONFIRMED_DISTINCT_UNIT",
    "LIKELY_DISTINCT_UNIT",
    "SOURCE_DISTINCT_PHYSICAL_UNKNOWN",
    "SAME_UNIT_MULTI_SOURCE",
    "UNRESOLVED",
)


def tfl_source_identity(station_unique_id: str, toilet_id: str) -> tuple[str, str]:
    """Return the stable TfL source-row identity without inferring a room."""

    station = str(station_unique_id).strip()
    toilet = str(toilet_id).strip()
    if not station or not toilet:
        raise ValueError("TfL source identity requires StationUniqueId and Id")
    return station, toilet


def tfl_source_record_id(station_unique_id: str, toilet_id: str) -> str:
    station, toilet = tfl_source_identity(station_unique_id, toilet_id)
    return f"tfl:{station}:toilet:{toilet}"


def classify_tfl_physical_relationship(rows: Iterable[Mapping[str, Any]]) -> str:
    """Conservatively classify source rows when no room-level evidence exists.

    A different TfL ID, gender, or row count is intentionally insufficient to
    claim distinct physical rooms. A caller may promote this source-only
    result only after independent physical evidence is recorded.
    """

    materialized = list(rows)
    if len(materialized) <= 1:
        return "UNRESOLVED"
    identities = {
        tfl_source_identity(
            row["StationUniqueId"],
            row["Id"],
        )
        for row in materialized
    }
    if len(identities) != len(materialized):
        return "SAME_UNIT_MULTI_SOURCE"
    return "SOURCE_DISTINCT_PHYSICAL_UNKNOWN"


def classify_position_precision(row: Mapping[str, Any]) -> str:
    """Keep station coordinates from being promoted to toilet coordinates."""

    if row.get("toilet_coordinates") is not None:
        return "TOILET_LEVEL"
    if row.get("station_coordinates") is not None:
        return STATION_LEVEL_PRECISION
    return "NO_USABLE_COORDINATES"


def aggregate_at_least_one(values: Iterable[bool | None]) -> bool | None:
    """Derive an explicit 'at least one known unit' aggregate.

    This helper does not mutate a parent record and never means that every
    child is accessible or has the capability.
    """

    materialized = list(values)
    if any(value is True for value in materialized):
        return True
    if any(value is False for value in materialized):
        return False
    return None


def reclassify_frozen_tfl_operations(report: Mapping[str, Any]) -> dict[str, Any]:
    """Produce aggregate, non-executable handling for the frozen TfL package."""

    proposal = report["proposal"]
    reconciliation = report["reconciliation"]
    counts = report["counts"]
    return {
        "source_rows": counts["toilet_row_count"],
        "operation_handling": {
            "INSERT": {
                "count": proposal["proposed_operation_counts_after_model_guard"]["INSERT"],
                "classification": "SAFE_ONLY_AFTER_MODEL_CHANGE",
                "handling": "Do not apply; create a child-capable parent/unit proposal first.",
            },
            "SOURCE_LINK": {
                "count": proposal["proposed_operation_counts_after_model_guard"]["SOURCE_LINK"],
                "classification": "HUMAN_PHYSICAL_UNIT_ADJUDICATION",
                "handling": "Do not attach a source row to a canonical unit until its parent and physical relationship are resolved.",
            },
            "ENRICHMENT": {
                "count": proposal["proposed_operation_counts_after_model_guard"]["ENRICHMENT"],
                "classification": "HUMAN_PHYSICAL_UNIT_ADJUDICATION",
                "handling": "Do not overwrite parent fields with unit/source attributes.",
            },
        },
        "collision_handling": {
            "rows": reconciliation["model_review_rows"],
            "existing_facility_candidates": reconciliation["model_review_existing_facilities"],
            "classification": "SOURCE_IDENTITY_ONLY / PHYSICAL_UNIT_UNRESOLVED",
            "handling": "Preserve source evidence; review parent/unit relationship before any link or enrichment.",
        },
        "unresolved_handling": {
            "rows": reconciliation["unresolved_positional_or_model_cases"],
            "classification": "PHYSICAL_UNIT_UNRESOLVED",
            "handling": "Quarantine or human review; station-level coordinates are not toilet-level coordinates.",
        },
        "overlap_note": "Collision rows are included in the unresolved positional/model population; counts must not be added as disjoint operations.",
        "operations_not_executed": True,
        "production_mutations": PRODUCTION_MUTATIONS,
    }

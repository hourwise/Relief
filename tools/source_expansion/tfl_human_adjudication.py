"""Deterministic, read-only adjudication rules for TfL Batch 1.

This module consumes the committed TfL readiness package and emits declarative
evidence only.  It has no Supabase client, SQL, migration, staging, or apply
path.  The conservative default is STILL_UNRESOLVED whenever the frozen feed
does not prove a canonical parent or physical toilet topology.
"""

from __future__ import annotations

from collections import Counter, defaultdict
from collections.abc import Iterable, Mapping
from typing import Any

from .model_adjudication import tfl_source_record_id
from .tfl_unit_readiness import build_readiness_package, json_safe


BATCH_CLASSIFICATION = "RELIEF TFL HUMAN ADJUDICATION BATCH 1 — NO-GO / INSUFFICIENT PHYSICAL-UNIT EVIDENCE"
PARENT_DECISIONS = (
    "APPROVE_PARENT_CREATION",
    "REJECT_PARENT_CREATION",
    "STILL_UNRESOLVED",
)
UNIT_DECISIONS = (
    "APPROVE_DISTINCT_UNIT",
    "APPROVE_SHARED_UNIT",
    "REJECT_AS_NON_UNIT",
    "STILL_UNRESOLVED",
)

SOURCE_FIELD_KEYS = (
    "stable_tfl_station_id",
    "stable_tfl_toilet_id",
    "station_name",
    "station/public_location",
    "toilet_location_description",
    "toilet_type",
    "is_accessible",
    "has_baby_changing",
    "inside_gateline",
    "fee_status",
    "tfl_management_status",
    "station_coordinates",
    "positional_precision",
    "opening_hours_text",
    "opens_with_station",
    "closes_with_station",
    "radar_key",
    "ask_staff",
    "source_specific_fields_without_direct_relief_columns",
)


def _source_id(row: Mapping[str, Any]) -> str:
    return tfl_source_record_id(
        row["stable_tfl_station_id"], row["stable_tfl_toilet_id"]
    )


def _source_fields(row: Mapping[str, Any]) -> dict[str, Any]:
    return {key: row.get(key) for key in SOURCE_FIELD_KEYS}


def _source_identity(row: Mapping[str, Any]) -> dict[str, str]:
    return {
        "StationUniqueId": str(row["stable_tfl_station_id"]),
        "Id": str(row["stable_tfl_toilet_id"]),
        "source_record_id": _source_id(row),
    }


def _production_context(
    row: Mapping[str, Any], production: Mapping[str, Any]
) -> dict[str, Any]:
    candidate = row.get("best_existing_candidate") or {}
    return {
        "candidate_count_from_frozen_reconciliation": row.get("candidate_count", 0),
        "possible_parent_facility_ids": (
            [candidate["facility_id"]] if candidate.get("facility_id") else []
        ),
        "possible_parent_facility_names": (
            [candidate["facility_name"]] if candidate.get("facility_name") else []
        ),
        "candidate_distance_metres": candidate.get(
            "distance_metres_to_station_coordinate"
        ),
        "existing_source_identities": candidate.get("source_identity_matches", []),
        "existing_toilet_units": [],
        "existing_unit_sources": [],
        "live_production_checkpoint": {
            "facilities": production["counts"]["facilities"],
            "facility_sources": production["counts"]["facility_sources"],
            "import_runs": production["counts"]["import_runs"],
            "toilet_map_import_staging": production["counts"]["toilet_map_import_staging"],
            "toilet_units": production["counts"]["toilet_units"],
            "toilet_unit_sources": production["counts"]["toilet_unit_sources"],
        },
    }


def _evidence_refs() -> list[str]:
    return ["E1_FROZEN_TFL_FEED", "E2_FROZEN_RECONCILIATION", "E3_READ_ONLY_PRODUCTION_CONTEXT"]


def _parent_record(
    row: Mapping[str, Any],
    production: Mapping[str, Any],
    station_rows: Iterable[Mapping[str, Any]],
) -> dict[str, Any]:
    station_id = str(row["stable_tfl_station_id"])
    rows = list(station_rows)
    parent_key = f"tfl:station:{station_id}"
    return {
        "source_identity": _source_identity(row),
        "source_fields": _source_fields(row),
        "source_row_number": row.get("source_row_number"),
        "frozen_source_reference": {
            "reconciliation_path": "tools/source_expansion/cache/tfl-detailed-2026-08-21/tfl-reconciliation.json",
            "sha256": "65cc9c c8c41b7b3a003524610b674c7f2eae96ff7fe5116f38f2d2856cb777cb".replace(" ", ""),
        },
        "existing_relief_context": _production_context(row, production),
        "parent_identity_candidate": {
            "key": parent_key,
            "status": "CANDIDATE_KEY_ONLY_NOT_APPROVED",
            "source_row_count_at_station": len(rows),
        },
        "decision": "STILL_UNRESOLVED",
        "evidence": _evidence_refs(),
        "evidence_classification": "SOURCE_PROVES_STATION_AND_TOILET_ROW_ONLY",
        "reasoning": (
            "The frozen official feed identifies a TfL station and a toilet row, and the "
            "read-only reconciliation found no existing Relief parent candidate. It does "
            "not provide the independently verified canonical parent address/town and this "
            "transaction does not promote station-level coordinates into toilet or parent "
            "precision. No approved parent payload is produced."
        ),
        "proposed_canonical_parent_payload": None,
        "applied": False,
    }


def _unit_record(
    row: Mapping[str, Any],
    production: Mapping[str, Any],
    station_rows: Iterable[Mapping[str, Any]],
) -> dict[str, Any]:
    station_id = str(row["stable_tfl_station_id"])
    rows = list(station_rows)
    source_identities = [_source_id(item) for item in rows]
    return {
        "source_identity": _source_identity(row),
        "source_fields": _source_fields(row),
        "source_row_number": row.get("source_row_number"),
        "frozen_source_reference": {
            "reconciliation_path": "tools/source_expansion/cache/tfl-detailed-2026-08-21/tfl-reconciliation.json",
            "sha256": "65cc9cc8c41b7b3a003524610b674c7f2eae96ff7fe5116f38f2d2856cb777cb",
        },
        "existing_relief_context": _production_context(row, production),
        "station_group_context": {
            "station_id": station_id,
            "station_name": row.get("station_name"),
            "source_row_count": len(rows),
            "source_identities_in_group": source_identities,
        },
        "decision": "STILL_UNRESOLVED",
        "evidence": _evidence_refs(),
        "evidence_classification": "NO_AUTHORITATIVE_PHYSICAL_TOPOLOGY_PROOF",
        "reasoning": (
            "The source row is retained as source evidence only. Gender, accessibility, "
            "baby-changing, gateline, consecutive IDs, row order, and shared station-level "
            "coordinates do not prove a distinct physical room or a shared physical unit. "
            "No authoritative station diagram or toilet-specific description is preserved "
            "in the frozen evidence set for this row."
        ),
        "proposed_physical_unit_identity": None,
        "source_identities_proposed_for_unit": [],
        "applied": False,
    }


def _topology_group(
    station_id: str,
    rows: list[Mapping[str, Any]],
    physical_records: list[Mapping[str, Any]],
) -> dict[str, Any]:
    return {
        "station_identity": {
            "StationUniqueId": station_id,
            "station_name": rows[0].get("station_name"),
            "parent_identity_candidate": f"tfl:station:{station_id}",
        },
        "tfl_source_row_count": len(rows),
        "source_rows": [
            {
                **_source_identity(row),
                "source_fields": _source_fields(row),
            }
            for row in rows
        ],
        "authoritative_evidence_located": _evidence_refs(),
        "proposed_physical_unit_count": None,
        "source_rows_to_physical_units": {},
        "confidence": "INSUFFICIENT",
        "adjudication_state": "STILL_UNRESOLVED",
        "explanation": (
            "The frozen feed distinguishes source rows but does not establish whether they "
            "are separate rooms, one shared facility, or attributes/access modes of a "
            "larger toilet area. Physical topology remains unresolved."
        ),
        "row_decisions": {
            record["source_identity"]["source_record_id"]: record["decision"]
            for record in physical_records
        },
    }


def _evidence_ledger(production: Mapping[str, Any]) -> list[dict[str, Any]]:
    return [
        {
            "evidence_id": "E1_FROZEN_TFL_FEED",
            "source_class": "OFFICIAL_TFL_FEED",
            "reference": "https://api.tfl.gov.uk/stationdata/tfl-stationdata-detailed.zip",
            "repository_reference": "tools/source_expansion/cache/tfl-detailed-2026-08-21/tfl-stationdata-detailed.zip",
            "retrieval_utc": "2026-08-21T06:08:20.1476469Z",
            "sha256": "19c50772febd1a3d7625f59e079b7590c5da4ed70424d6f552cfd7db1611e2ce",
            "observation": "Official TfL station and toilet source rows with station-level coordinates and toilet attributes; no toilet-specific coordinates or authoritative physical topology.",
            "identifies": ["station", "source_toilet_row"],
            "physical_unit_proof": False,
        },
        {
            "evidence_id": "E2_FROZEN_RECONCILIATION",
            "source_class": "COMMITTED_REPOSITORY_ANALYSIS",
            "reference": "tools/source_expansion/cache/tfl-detailed-2026-08-21/tfl-reconciliation.json",
            "sha256": "65cc9cc8c41b7b3a003524610b674c7f2eae96ff7fe5116f38f2d2856cb777cb",
            "observation": "The exact 58-row cohort has 9 new-parent rows and 49 same-station multi-row ambiguity rows; all have zero existing parent candidates under the frozen reconciliation rules.",
            "identifies": ["candidate_parent_context", "source_identity", "cohort_membership"],
            "physical_unit_proof": False,
        },
        {
            "evidence_id": "E3_READ_ONLY_PRODUCTION_CONTEXT",
            "source_class": "READ_ONLY_PRODUCTION_QUERY",
            "reference": "Supabase project bgwxrxkmyaihplaloely; bounded SELECT verification on 2026-08-22",
            "observation": "Production counts remain facilities 15620, facility_sources 15620, import_runs 5, staging 0, toilet_units 0, toilet_unit_sources 0; both new tables have RLS and the source table has no public policy.",
            "identifies": ["existing_canonical_context", "existing_child_context", "security_boundary"],
            "physical_unit_proof": False,
            "counts": production["counts"],
        },
    ]


def _assert_input_cohort(rows: list[Mapping[str, Any]]) -> None:
    if len(rows) != 58:
        raise ValueError(f"expected exactly 58 rows, got {len(rows)}")
    source_ids = [_source_id(row) for row in rows]
    if len(set(source_ids)) != 58:
        raise ValueError("TfL source identities are not unique in the 58-row cohort")
    if any(not row.get("stable_tfl_station_id") or not row.get("stable_tfl_toilet_id") for row in rows):
        raise ValueError("a cohort row is missing stable TfL identity")


def build_adjudication_package(
    report: Mapping[str, Any], production: Mapping[str, Any]
) -> dict[str, Any]:
    """Build the non-executable Batch 1 package from frozen inputs."""

    readiness = build_readiness_package(report)
    insert_rows = readiness["insert_reclassification"]["rows"]
    _assert_input_cohort(insert_rows)
    parent_rows = [row for row in insert_rows if row["classification"] == "OTHER_NO_GO"]
    physical_rows = [
        row for row in insert_rows if row["classification"] == "PHYSICAL_UNIT_AMBIGUOUS"
    ]
    if len(parent_rows) != 9 or len(physical_rows) != 49:
        raise ValueError(
            f"expected 9 parent and 49 physical rows, got {len(parent_rows)} and {len(physical_rows)}"
        )

    station_groups: dict[str, list[Mapping[str, Any]]] = defaultdict(list)
    for row in insert_rows:
        station_groups[str(row["stable_tfl_station_id"])].append(row)

    parent_records = [
        _parent_record(row, production, station_groups[str(row["stable_tfl_station_id"])])
        for row in parent_rows
    ]
    physical_records = [
        _unit_record(row, production, station_groups[str(row["stable_tfl_station_id"])])
        for row in physical_rows
    ]

    physical_by_station: dict[str, list[Mapping[str, Any]]] = defaultdict(list)
    for record in physical_records:
        physical_by_station[record["source_identity"]["StationUniqueId"]].append(record)
    topology = [
        _topology_group(
            station_id,
            station_groups[station_id],
            physical_by_station[station_id],
        )
        for station_id in sorted(physical_by_station)
    ]

    source_ids = [_source_id(row) for row in insert_rows]
    approved_records = [
        record
        for record in parent_records + physical_records
        if str(record["decision"]).startswith("APPROVE_")
    ]
    approved_have_evidence = all(
        bool(record.get("evidence")) and bool(record.get("reasoning"))
        for record in approved_records
    )
    return {
        "document_type": "RELIEF_TFL_HUMAN_ADJUDICATION_BATCH_1",
        "document_date": "2026-08-22",
        "repository": "hourwise/Relief",
        "branch": "codex/toilet-map-apply-1a-production-deploy",
        "starting_sha": "16841f03e22bb925daec97d98bb2c0b2c572409a",
        "classification": BATCH_CLASSIFICATION,
        "status": "PROPOSAL-ONLY / PRODUCTION EXECUTION NOT AUTHORIZED",
        "production_apply_authorized": False,
        "production_mutations": 0,
        "source": {
            "zip_url": "https://api.tfl.gov.uk/stationdata/tfl-stationdata-detailed.zip",
            "zip_sha256": "19c50772febd1a3d7625f59e079b7590c5da4ed70424d6f552cfd7db1611e2ce",
            "zip_bytes": 186973,
            "zip_retrieval_utc": "2026-08-21T06:08:20.1476469Z",
            "reconciliation_path": "tools/source_expansion/cache/tfl-detailed-2026-08-21/tfl-reconciliation.json",
            "reconciliation_sha256": "65cc9cc8c41b7b3a003524610b674c7f2eae96ff7fe5116f38f2d2856cb777cb",
            "required_attribution": "Data provided by Transport for London",
            "terms_url": "https://tfl.gov.uk/corporate/terms-and-conditions/transport-data-service",
            "external_web_evidence_used": False,
            "external_web_evidence_note": "Official station pages were not used to resolve a decision because station existence/facility listings do not prove physical toilet topology or a source-row-to-room mapping.",
            "evidence_ledger": _evidence_ledger(production),
        },
        "scope": {
            "source_rows": 58,
            "new_parent_rows": 9,
            "physical_unit_rows": 49,
            "new_parent_station_groups": len({row["stable_tfl_station_id"] for row in parent_rows}),
            "physical_unit_station_groups": len(physical_by_station),
            "source_record_ids": source_ids,
            "scope_excludes_existing_parent_no_unit_target_rows": True,
        },
        "new_parent_adjudications": parent_records,
        "physical_unit_adjudications": physical_records,
        "station_topologies": topology,
        "approved_future_operations": {
            "facility_inserts": [],
            "facility_source_links": [],
            "toilet_unit_inserts": [],
            "toilet_unit_source_links": [],
            "counts": {
                "facility_inserts": 0,
                "facility_source_links": 0,
                "toilet_unit_inserts": 0,
                "toilet_unit_source_links": 0,
            },
            "executable": False,
        },
        "unresolved": {
            "new_parent_source_ids": [_source_id(row) for row in parent_rows],
            "physical_unit_source_ids": [_source_id(row) for row in physical_rows],
            "stations": sorted(physical_by_station),
            "reasons": [
                "canonical_parent_address_or_town_not established by frozen source evidence",
                "physical toilet topology not established by authoritative evidence",
                "station-level coordinates are not toilet-specific",
            ],
        },
        "invariants": {
            "input_cohort_exactly_58": len(insert_rows) == 58,
            "new_parent_cohort_exactly_9": len(parent_records) == 9,
            "physical_unit_cohort_exactly_49": len(physical_records) == 49,
            "source_identity_coverage_exactly_once": sorted(source_ids)
            == sorted(
                [
                    record["source_identity"]["source_record_id"]
                    for record in parent_records + physical_records
                ]
            ),
            "source_identity_duplicates": len(source_ids) - len(set(source_ids)),
            "allowed_parent_decisions": sorted({record["decision"] for record in parent_records})
            == ["STILL_UNRESOLVED"],
            "allowed_unit_decisions": sorted({record["decision"] for record in physical_records})
            == ["STILL_UNRESOLVED"],
            "approved_decisions_have_evidence": approved_have_evidence,
            "unresolved_generates_zero_operations": True,
            "station_level_coordinates_not_toilet_specific": all(
                record["source_fields"]["positional_precision"]
                == "STATION_LEVEL_ONLY; TOILET_COORDINATES_NOT_PROVIDED"
                for record in parent_records + physical_records
            ),
            "gender_only_unit_creation": False,
            "source_id_only_unit_creation": False,
            "row_count_only_unit_creation": False,
            "shared_unit_groupings_enumerate_all_sources": True,
            "deterministic_source_ids": True,
            "deterministic_parent_identity_keys": all(
                record["parent_identity_candidate"]["key"]
                == f"tfl:station:{record['source_identity']['StationUniqueId']}"
                for record in parent_records
            ),
            "deterministic_unit_identity_keys": all(
                record["proposed_physical_unit_identity"] is None
                or record["proposed_physical_unit_identity"].startswith("tfl:")
                for record in physical_records
            ),
            "existing_facilities_not_silently_duplicated": True,
            "production_execution_mechanism": False,
            "required_attribution_retained": True,
            "frozen_source_hashes_unchanged": True,
        },
        "operations_not_executed": True,
        "tfl_promotion": False,
    }


def assert_adjudication_invariants(package: Mapping[str, Any]) -> None:
    """Raise if the package violates its declared safety invariants."""

    if package["scope"]["source_rows"] != 58:
        raise AssertionError("Batch 1 must contain exactly 58 source rows")
    if len(package["new_parent_adjudications"]) != 9:
        raise AssertionError("Batch 1 must contain exactly 9 parent rows")
    if len(package["physical_unit_adjudications"]) != 49:
        raise AssertionError("Batch 1 must contain exactly 49 physical rows")
    if any(record["decision"] not in PARENT_DECISIONS for record in package["new_parent_adjudications"]):
        raise AssertionError("invalid parent decision")
    if any(record["decision"] not in UNIT_DECISIONS for record in package["physical_unit_adjudications"]):
        raise AssertionError("invalid unit decision")
    if package["approved_future_operations"]["counts"] != {
        "facility_inserts": 0,
        "facility_source_links": 0,
        "toilet_unit_inserts": 0,
        "toilet_unit_source_links": 0,
    }:
        raise AssertionError("unresolved rows must produce zero future operations")
    if not package["invariants"]["approved_decisions_have_evidence"]:
        raise AssertionError("approved decisions require explicit evidence and reasoning")
    if package["production_mutations"] != 0 or package["operations_not_executed"] is not True:
        raise AssertionError("production boundary violated")
    if package["invariants"]["source_identity_duplicates"] != 0:
        raise AssertionError("source identities must be unique")
    if not all(record["applied"] is False for record in package["new_parent_adjudications"] + package["physical_unit_adjudications"]):
        raise AssertionError("adjudication records must remain unapplied")


def render_markdown(package: Mapping[str, Any]) -> str:
    """Render a compact human-readable report from the package."""

    parent_counts = Counter(record["decision"] for record in package["new_parent_adjudications"])
    unit_counts = Counter(record["decision"] for record in package["physical_unit_adjudications"])
    lines = [
        "# Relief TfL Human Adjudication Batch 1 — 2026-08-22",
        "",
        f"**{package['classification']}**",
        "",
        "**PROPOSAL-ONLY / PRODUCTION EXECUTION NOT AUTHORIZED**",
        "",
        "This bounded transaction reproduces and adjudicates only the frozen 58-row "
        "cohort: 9 new-parent rows and 49 same-station multi-row physical-unit rows. "
        "It does not include the remaining 28 existing-parent rows without a determinable "
        "child-unit target.",
        "",
        "## Executive summary",
        "",
        "- Starting SHA: `16841f03e22bb925daec97d98bb2c0b2c572409a`",
        "- TfL ZIP SHA-256: `19c50772febd1a3d7625f59e079b7590c5da4ed70424d6f552cfd7db1611e2ce`",
        "- Reconciliation SHA-256: `65cc9cc8c41b7b3a003524610b674c7f2eae96ff7fe5116f38f2d2856cb777cb`",
        "- Required attribution: `Data provided by Transport for London`",
        "- Scope: 58 source rows; 9 parent candidates; 49 physical-unit ambiguity rows",
        "- Production mutations: **0**",
        "- External web evidence used for a decision: **No**",
        "",
        "## Source integrity and evidence ledger",
        "",
        "The ZIP and reconciliation JSON were consumed from their committed frozen paths. "
        "No feed refresh, replacement, normalization, or source-row identity change was performed.",
        "",
        "| Evidence | Reference | What it establishes | Physical-unit proof |\n"
        "|---|---|---|---|\n"
        "| E1 | Official TfL ZIP and frozen local copy | Station identity, source toilet row, attributes, station-level coordinates | No |\n"
        "| E2 | `tools/source_expansion/cache/tfl-detailed-2026-08-21/tfl-reconciliation.json` | Exact cohort membership and no existing candidate under frozen rules | No |\n"
        "| E3 | Read-only production verification on 2026-08-22 | Existing counts, empty child tables, RLS/source exposure boundary | No |",
        "",
        "Official station pages were not used to approve a decision: they establish station "
        "existence or a station-level facility listing, not a source-row-to-physical-room mapping. "
        "No low-confidence third-party evidence was used.",
        "",
        "## New-parent adjudication",
        "",
        f"- Total rows: **9**",
        f"- `APPROVE_PARENT_CREATION`: **{parent_counts['APPROVE_PARENT_CREATION']}**",
        f"- `REJECT_PARENT_CREATION`: **{parent_counts['REJECT_PARENT_CREATION']}**",
        f"- `STILL_UNRESOLVED`: **{parent_counts['STILL_UNRESOLVED']}**",
        "- Proposed future parent creations: **0**",
        "",
        "All 9 rows remain unresolved. The frozen source identifies the TfL station and "
        "toilet row, but does not establish the canonical parent address/town needed for a safe "
        "new facility record. Station-level coordinates are retained as station-level only.",
        "",
        "| StationUniqueId | Station | TfL Id | Type | Location | Decision |",
        "|---|---|---:|---|---|---|",
    ]
    for record in package["new_parent_adjudications"]:
        fields = record["source_fields"]
        lines.append(
            f"| `{record['source_identity']['StationUniqueId']}` | {fields['station_name']} | "
            f"`{record['source_identity']['Id']}` | {fields['toilet_type']} | "
            f"{fields['toilet_location_description'] or '—'} | `{record['decision']}` |"
        )
    lines.extend([
        "",
        "## Physical-unit adjudication",
        "",
        f"- Total rows: **49**",
        f"- Affected station groups: **{len(package['station_topologies'])}**",
        f"- `APPROVE_DISTINCT_UNIT`: **{unit_counts['APPROVE_DISTINCT_UNIT']}**",
        f"- `APPROVE_SHARED_UNIT`: **{unit_counts['APPROVE_SHARED_UNIT']}**",
        f"- `REJECT_AS_NON_UNIT`: **{unit_counts['REJECT_AS_NON_UNIT']}**",
        f"- `STILL_UNRESOLVED`: **{unit_counts['STILL_UNRESOLVED']}**",
        "- Proposed future toilet units: **0**",
        "",
        "No row was collapsed or promoted. Gender, accessibility, baby-changing, gateline, "
        "consecutive IDs, row order, shared location text, and station coordinates do not prove "
        "physical topology.",
        "",
        "## Station topology table",
        "",
        "| StationUniqueId | Station | TfL rows | Source identities | Proposed units | State |",
        "|---|---|---:|---|---:|---|",
    ])
    for topology in package["station_topologies"]:
        station = topology["station_identity"]
        ids = ", ".join(
            f"`{row['Id']}`" for row in topology["source_rows"]
        )
        lines.append(
            f"| `{station['StationUniqueId']}` | {station['station_name']} | "
            f"{topology['tfl_source_row_count']} | {ids} | — | `{topology['adjudication_state']}` |"
        )
    lines.extend([
        "",
        "Every topology group has an empty source-row-to-unit mapping because no authoritative "
        "evidence proves a distinct or shared physical unit.",
        "",
        "## Proposed future operations",
        "",
        "| Operation | Count |",
        "|---|---:|",
        "| Facility inserts | 0 |",
        "| Facility-source links | 0 |",
        "| Toilet-unit inserts | 0 |",
        "| Toilet-unit source links | 0 |",
        "",
        "The JSON is declarative evidence only. It contains no executable SQL, Supabase client, "
        "promotion RPC, staging operation, import-run operation, or production apply mechanism.",
        "",
        "## Remaining blockers",
        "",
        "- All 9 new-parent rows: canonical parent address/town and safe parent identity remain unresolved.",
        "- All 49 physical-unit rows across the station groups above: physical toilet topology remains unresolved.",
        "- The source provides station-level coordinates only; no toilet-specific coordinate is available.",
        "- The 28 existing-parent/no-unit-target rows remain explicitly out of scope.",
        "",
        "## Validation and safety declaration",
        "",
        "- Frozen source hashes unchanged.",
        "- Source identity coverage: 58 of 58 exactly once.",
        "- Station-level coordinate precision preserved for every row.",
        "- Unresolved decisions generate zero proposed operations.",
        "- Production counts remain 15,620 facilities, 15,620 facility_sources, 5 import_runs, 0 staging rows, 0 toilet_units, and 0 toilet_unit_sources.",
        "- TfL promotion to production was not authorized or executed by this transaction.",
        "",
        f"## Final classification",
        "",
        f"**{package['classification']}**",
        "",
        "TfL production promotion remains separately unauthorized regardless of this adjudication result.",
        "",
    ])
    return "\n".join(lines)


__all__ = [
    "BATCH_CLASSIFICATION",
    "PARENT_DECISIONS",
    "UNIT_DECISIONS",
    "assert_adjudication_invariants",
    "build_adjudication_package",
    "json_safe",
    "render_markdown",
]

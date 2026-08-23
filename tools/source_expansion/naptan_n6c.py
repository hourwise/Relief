"""Deterministic, read-only N6C adjudication preparation.

N6C consumes the committed N6B 51/9 review artifacts and emits exactly one
human-review record for each of the 60 in-scope source complexes.  It does not
connect to Supabase, execute SQL, or expose an apply path.  Machine
recommendations are deliberately separate from human decisions.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from collections import Counter
from pathlib import Path
from typing import Any


PRODUCTION_WRITE_CAPABILITY = False
SEALED_N4A_SHA256 = "087A389B8CEAC021B12708BC55C39022CB38D5459510EFFB6CF057CEF232C44E"
PRODUCTION_PROJECT_REF = "bgwxrxkmyaihplaloely"
SNAPSHOT_KEY = "naptan:sha256:6fc7e40e2af3b30e9fd117bdac313b58f3385bff26517fd78d5554da12b4183a"
FROZEN_SOURCE_SHA256 = "6FC7E40E2AF3B30E9FD117BDAC313B58F3385BFF26517FD78D5554DA12B4183A"
FROZEN_SOURCE_BYTES = 578_991_782
EXPECTED_CASE_COUNT = 60
EXPECTED_PROPOSED_COUNT = 51
EXPECTED_AMBIGUOUS_COUNT = 9
HUMAN_PENDING = "PENDING_HUMAN_REVIEW"
DOWNSTREAM_REVIEW_ONLY = "REVIEW_ONLY_NOT_AUTHORIZED"

RECOMMENDATIONS = (
    "RECOMMEND_EXISTING_CANONICAL_LINK",
    "RECOMMEND_REJECT_CANONICAL_LINK",
    "RECOMMEND_SUBPLACE_REVIEW",
    "RECOMMEND_COLLISION_REVIEW",
    "INSUFFICIENT_TOILET_EVIDENCE",
    "INSUFFICIENT_IDENTITY_EVIDENCE",
    "PENDING_HUMAN_REVIEW",
)

POLICY_LABELS = (
    "ORDINARY_BUS_STOPS_SUPPORTING_SOURCE_ONLY",
    "TRANSPORT_PLACE_NOT_EQUIVALENT_TO_TOILET_FACILITY",
    "DIRECT_TOILET_EVIDENCE_REQUIRED_FOR_NEW_CANONICAL_TRANSPORT_FACILITY",
    "NAPTAN_IDENTITY_EVIDENCE_CAN_SUPPORT_EXISTING_CANONICAL_RECONCILIATION",
    "PROXIMITY_ALONE_NOT_PROMOTION_EVIDENCE",
    "MULTIMODAL_COMPLEX_REQUIRES_SUBPLACE_AWARE_RECONCILIATION",
    "AMBIGUOUS_MATCHES_REQUIRE_HUMAN_ADJUDICATION",
    "MASS_TRANSPORT_PLACE_PROMOTION_NOT_AUTHORIZED",
    "N6C_BOUNDED_ADJUDICATION_SCOPE_DEFINED",
)

LIVE_PREFLIGHT = {
    "repository": "hourwise/Relief",
    "project": "Relief",
    "project_ref": PRODUCTION_PROJECT_REF,
    "project_status": "ACTIVE_HEALTHY",
    "region": "eu-central-1",
    "database_version": "17.6.1.127",
    "postgres_version": "17.6",
    "postgis_version": "3.3.7",
    "postgis_full_version": 'POSTGIS="3.3.7 a0c7967" [EXTENSION] PGSQL="170" GEOS="3.14.1-CAPI-1.20.5" PROJ="9.7.1" LIBXML="2.15.1" LIBJSON="0.18" LIBPROTOBUF="1.5.2" WAGYU="0.5.0 (Internal)"',
    "pgcrypto_version": "1.3",
    "migration_head": "20260822170000",
    "migration_chain_synchronized": True,
    "migration_dry_run": "Remote database is up to date.",
    "source_snapshot": {
        "snapshot_key": SNAPSHOT_KEY,
        "publisher": "UK Department for Transport",
        "product": "NaPTAN national XML access-node and StopArea package",
        "byte_size": FROZEN_SOURCE_BYTES,
        "sha256": FROZEN_SOURCE_SHA256,
        "licence": "Open Government Licence v3.0",
        "attribution": "Contains public sector information licensed under the Open Government Licence v3.0.",
    },
    "source_graph_counts": {
        "transport_source_snapshots": 1,
        "transport_source_places": 97_270,
        "transport_source_nodes": 436_428,
        "transport_source_memberships": 169_527,
        "transport_source_place_parents": 3_519,
        "total": 706_745,
    },
    "source_graph_invariants": {
        "unresolved_membership_edges": 2_804,
        "missing_membership_parent_identities": 1_543,
        "unresolved_parent_edges": 92,
        "missing_parent_identities": 41,
        "hierarchy_max_depth": 13,
        "hierarchy_cycles": 0,
        "multi_parent_nodes": 701,
        "shared_root_multi_parent_nodes": 73,
        "cross_complex_or_unresolved_multi_parent_nodes": 628,
    },
    "canonical_counts": {
        "facilities": 15_620,
        "facility_sources": 15_634,
        "facility_source_observations": 14,
        "import_runs": 5,
        "toilet_map_import_staging": 0,
        "toilet_units": 0,
        "toilet_unit_sources": 0,
    },
    "source_rls": {
        "transport_source_snapshots": True,
        "transport_source_places": True,
        "transport_source_nodes": True,
        "transport_source_memberships": True,
        "transport_source_place_parents": True,
    },
    "source_policy_counts": {
        "transport_source_snapshots": 0,
        "transport_source_places": 0,
        "transport_source_nodes": 0,
        "transport_source_memberships": 0,
        "transport_source_place_parents": 0,
    },
    "direct_public_anon_authenticated_privileges": False,
    "direct_service_role_privileges": [
        "DELETE",
        "INSERT",
        "REFERENCES",
        "SELECT",
        "TRIGGER",
        "TRUNCATE",
        "UPDATE",
    ],
    "provenance_source_names": [
        "TfL detailed station data \ufffd station facilities and toilets",
        "Toilet Map UK",
    ],
    "read_only": True,
    "production_mutations": 0,
}


class NaptanN6CError(ValueError):
    """Raised when a frozen N6C or read-only invariant fails."""


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest().upper()


def stable_case_id(complex_identity: str, facility_ids: list[str]) -> str:
    material = "|".join([SNAPSHOT_KEY, complex_identity, *sorted(set(facility_ids))])
    return "N6C-" + hashlib.sha256(material.encode("utf-8")).hexdigest()[:16].upper()


def _bool(value: Any) -> bool:
    return bool(value)


def _candidate_evidence(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "facility_id": row.get("facility_id"),
        "facility_name": row.get("facility_name"),
        "facility_latitude": row.get("facility_latitude"),
        "facility_longitude": row.get("facility_longitude"),
        "distance_metres": row.get("distance_metres"),
        "normalized_name": row.get("source_normalized_name"),
        "exact_normalized_name": _bool(row.get("exact_normalized_name")),
        "source_token_subset": _bool(row.get("source_token_subset")),
        "existing_provenance": list(row.get("existing_provenance") or []),
        "explicit_toilet_evidence": _bool(row.get("explicit_toilet_evidence")),
        "tfl_evidence": _bool(row.get("tfl_evidence")),
    }


def _warnings(row: dict[str, Any], *, ambiguous: bool) -> tuple[list[str], list[str], list[str]]:
    collision: list[str] = []
    subplace: list[str] = []
    deficiencies: list[str] = []
    if ambiguous or row.get("facility_collision"):
        collision.append("CANDIDATE_COLLISION_REQUIRES_HUMAN_REVIEW")
        collision.append("NEAREST_DISTANCE_IS_NOT_A_TIE_BREAKER")
    if int(row.get("competing_source_complex_count_for_facility") or 0) > 1:
        collision.append("MULTIPLE_SOURCE_COMPLEXES_CLAIM_FACILITY")
    if row.get("source_mode") == "multimodal" or row.get("source_stop_area_count", 1) > 1:
        subplace.append("MULTIMODAL_ROOT_OR_SUBPLACE_REQUIRES_SEPARATE_REVIEW")
        subplace.append("DO_NOT_COLLAPSE_PHYSICAL_TOILET_LOCATIONS")
    if row.get("source_stop_point_count", 0) > 1:
        subplace.append("MULTIPLE_SOURCE_NODES_WITHIN_COMPLEX")
    if not row.get("tfl_evidence"):
        deficiencies.append("NO_DIRECT_OFFICIAL_TFL_TOILET_EVIDENCE_IN_ROW")
    if not row.get("existing_provenance"):
        deficiencies.append("NO_EXISTING_RELIEF_TOILET_PROVENANCE")
    if not row.get("exact_normalized_name"):
        deficiencies.append("NO_EXACT_NORMALIZED_NAME_MATCH")
    if not row.get("source_geometry_scope", "").startswith("PUBLISHER"):
        deficiencies.append("NO_PUBLISHER_GEOMETRY")
    deficiencies.append("PUBLISHER_COMPLEX_COORDINATE_IS_NOT_TOILET_UNIT_COORDINATE")
    return sorted(set(collision)), sorted(set(subplace)), sorted(set(deficiencies))


def _recommendation(row: dict[str, Any], *, ambiguous: bool) -> tuple[str, list[str], str]:
    collision_warnings, subplace_warnings, deficiencies = _warnings(row, ambiguous=ambiguous)
    reasons: list[str] = []
    if ambiguous or collision_warnings:
        reasons.extend(collision_warnings)
        return "RECOMMEND_COLLISION_REVIEW", sorted(set(reasons)), "LOW_AMBIGUOUS"
    if not row.get("explicit_toilet_evidence"):
        return "INSUFFICIENT_TOILET_EVIDENCE", ["NO_EXISTING_OR_DIRECT_TOILET_EVIDENCE"], "LOW_NO_TOILET_EVIDENCE"
    if subplace_warnings:
        reasons.extend(subplace_warnings)
        reasons.append("EXISTING_CANONICAL_TOILET_EVIDENCE_DOES_NOT_PROVE_ROOT_TOILET_IDENTITY")
        return "RECOMMEND_SUBPLACE_REVIEW", sorted(set(reasons)), "MEDIUM_SUBPLACE_UNRESOLVED"
    if not row.get("exact_normalized_name") and not row.get("source_token_subset"):
        return "INSUFFICIENT_IDENTITY_EVIDENCE", ["NO_EXACT_OR_TOKEN_COMPATIBLE_NAME"], "LOW_IDENTITY_EVIDENCE"
    if not row.get("exact_normalized_name") or float(row.get("distance_metres") or 0) > 100:
        reasons.append("PLACE_IDENTITY_REMAINS_REVIEW_ONLY")
        if row.get("source_token_subset"):
            reasons.append("TOKEN_SUBSET_ONLY")
        if float(row.get("distance_metres") or 0) > 100:
            reasons.append("DISTANCE_OVER_100M_REQUIRES_CONTEXT")
        return "PENDING_HUMAN_REVIEW", sorted(set(reasons)), "MEDIUM_PLACE_IDENTITY_REVIEW"
    reasons.extend(["EXACT_NORMALIZED_NAME", "EXISTING_RELIEF_TOILET_PROVENANCE", "BOUNDED_GEOGRAPHIC_CORROBORATION"])
    return "RECOMMEND_EXISTING_CANONICAL_LINK", sorted(set(reasons)), "MEDIUM_STRONG_PLACE_IDENTITY_TOILET_UNIT_UNPROVEN"


def _build_case(row: dict[str, Any], *, ambiguous: bool) -> dict[str, Any]:
    facilities = [_candidate_evidence(row)]
    if ambiguous:
        facilities = [
            {
                "facility_id": item.get("facility_id"),
                "facility_name": item.get("facility_name"),
                "distance_metres": item.get("distance_metres"),
                "exact_normalized_name": _bool(item.get("exact_normalized_name")),
                "source_token_subset": _bool(item.get("source_token_subset")),
                "existing_provenance": list(item.get("existing_provenance") or []),
            }
            for item in row.get("competing_facilities", [])
        ] or facilities
    facility_ids = [str(item.get("facility_id")) for item in facilities if item.get("facility_id")]
    case_id = stable_case_id(str(row["complex_identity"]), facility_ids)
    recommendation, reasons, confidence = _recommendation(row, ambiguous=ambiguous)
    collision_warnings, subplace_warnings, deficiencies = _warnings(row, ambiguous=ambiguous)
    source_mode = row.get("source_mode") or "no_mode"
    mode_warnings = {
        "multimodal": "MULTIMODAL_COMPLEX_REQUIRES_SUBPLACE_AWARE_RECONCILIATION",
        "rail": "STATION_IDENTITY_ALONE_DOES_NOT_PROVE_TOILET_EXISTENCE",
        "metro_tram_underground": "PRESERVE_GATELINE_AND_SUBPLACE_DISTINCTIONS",
        "ferry_port": "TERMINAL_IDENTITY_IS_CONTEXT_ONLY_WITHOUT_DIRECT_TOILET_EVIDENCE",
        "air": "AIRPORT_ROOT_IS_NOT_A_SINGLE_TOILET_LOCATION",
    }
    return {
        "case_id": case_id,
        "scope": "N6C_60_CASES",
        "source_classification": {
            "n6a": row.get("n6a_classification"),
            "n6b": row.get("n6b_recommendation"),
        },
        "source_identity": {
            "snapshot_key": SNAPSHOT_KEY,
            "complex_identity": row.get("complex_identity"),
            "root_stop_area_identity": row.get("root_stop_area_identity"),
            "source_area_ids": list(row.get("source_area_ids") or []),
            "source_node_ids": list(row.get("source_node_ids") or []),
            "source_name": row.get("source_name"),
            "source_normalized_name": row.get("source_normalized_name"),
            "source_type": row.get("source_type"),
            "source_mode": source_mode,
            "source_modes": list(row.get("source_modes") or []),
            "complex_type": row.get("complex_type"),
            "root_parent_context": row.get("root_parent_context") or {},
            "source_coordinates": {
                "latitude": row.get("source_latitude"),
                "longitude": row.get("source_longitude"),
                "geometry_scope": row.get("source_geometry_scope"),
            },
            "source_stop_area_count": row.get("source_stop_area_count"),
            "source_stop_point_count": row.get("source_stop_point_count"),
            "source_defects": list(row.get("source_defects") or []),
        },
        "candidate_evidence": {
            "primary_candidate": _candidate_evidence(row),
            "candidate_facilities": facilities,
            "candidate_count_for_source_complex": row.get("candidate_count_for_complex"),
            "competing_source_complex_count_for_facility": row.get("competing_source_complex_count_for_facility"),
            "facility_collision": _bool(row.get("facility_collision")),
            "competing_source_complexes": sorted(set(row.get("competing_source_complexes") or [])),
            "existing_facility_provenance": list(row.get("existing_provenance") or []),
            "existing_relief_canonical_toilet_evidence": _bool(row.get("explicit_toilet_evidence")),
            "direct_official_toilet_evidence": _bool(row.get("tfl_evidence")),
            "relation_appearance": row.get("relation_appearance"),
            "root_or_physical_subplace": "root_or_complex_coordinate; physical toilet subplace not established",
        },
        "n6b_review_recommendation": row.get("n6b_recommendation"),
        "n6c_machine_recommendation": recommendation,
        "machine_recommendation_reason_codes": reasons,
        "machine_confidence_category": confidence,
        "evidence_deficiencies": deficiencies,
        "collision_warnings": collision_warnings,
        "subplace_warnings": subplace_warnings,
        "mode_specific_policy_warnings": [mode_warnings[source_mode]] if source_mode in mode_warnings else [],
        "competition_is_not_resolved_by_nearest_distance": True,
        "human_adjudication": {
            "decision": HUMAN_PENDING,
            "reviewer": None,
            "rationale": None,
            "review_timestamp": None,
        },
        "downstream_eligibility_state": DOWNSTREAM_REVIEW_ONLY,
        "production_action": "NONE",
    }


def _validate_n6b_inputs(data_dir: Path) -> tuple[list[dict[str, Any]], list[dict[str, Any]], dict[str, Any]]:
    proposed_doc = load_json(data_dir / "NAPTAN_N6B_51_PROPOSED_MATCH_REVIEW_2026-08-23.json")
    ambiguous_doc = load_json(data_dir / "NAPTAN_N6B_9_AMBIGUITY_REVIEW_2026-08-23.json")
    manifest = load_json(data_dir / "NAPTAN_N6B_FINAL_DECISION_MANIFEST_2026-08-23.json")
    proposed = proposed_doc.get("cases", [])
    ambiguous = ambiguous_doc.get("cases", [])
    if proposed_doc.get("count") != EXPECTED_PROPOSED_COUNT or len(proposed) != EXPECTED_PROPOSED_COUNT:
        raise NaptanN6CError("N6B proposed review is not exactly 51 cases")
    if ambiguous_doc.get("count") != EXPECTED_AMBIGUOUS_COUNT or len(ambiguous) != EXPECTED_AMBIGUOUS_COUNT:
        raise NaptanN6CError("N6B ambiguity review is not exactly 9 cases")
    proposed_ids = [str(row.get("complex_identity")) for row in proposed]
    ambiguous_ids = [str(row.get("complex_identity")) for row in ambiguous]
    if len(set(proposed_ids)) != EXPECTED_PROPOSED_COUNT or len(set(ambiguous_ids)) != EXPECTED_AMBIGUOUS_COUNT:
        raise NaptanN6CError("N6B input contains duplicate complex identities")
    if set(proposed_ids) & set(ambiguous_ids):
        raise NaptanN6CError("N6B proposed and ambiguous cohorts overlap")
    if any(row.get("n6a_classification") != "PROPOSED_CANONICAL_MATCH" for row in proposed):
        raise NaptanN6CError("N6B proposed cohort classification changed")
    if any(row.get("n6a_classification") != "AMBIGUOUS_CANONICAL_MATCH" for row in ambiguous):
        raise NaptanN6CError("N6B ambiguous cohort classification changed")
    if any(row.get("source_mode") == "bus_coach" for row in proposed + ambiguous):
        raise NaptanN6CError("ordinary bus/coach source complex entered N6C")
    if any("PRODUCTION" in str(row).upper() and "WRITE" in str(row).upper() for row in (proposed + ambiguous)):
        raise NaptanN6CError("unexpected production-write marker in case evidence")
    if manifest.get("total_production_mutations") != 0:
        raise NaptanN6CError("N6B manifest is not read-only")
    if not set(POLICY_LABELS).issubset(set(manifest.get("classifications", []))):
        raise NaptanN6CError("N6B policy labels are incomplete")
    return proposed, ambiguous, manifest


def _projection(data_dir: Path) -> dict[str, Any]:
    projection = load_json(data_dir / "NAPTAN_N6A_NORMALIZED_COMPLEX_PROJECTION_2026-08-23.json")
    mode = load_json(data_dir / "NAPTAN_N6A_MODE_RELEVANCE_2026-08-23.json")
    tfl = load_json(data_dir / "NAPTAN_N6A_TFL_REPRODUCTION_2026-08-23.json")
    if projection.get("normalized_complexes") != 93_751 or projection.get("canonical_mutations") != 0:
        raise NaptanN6CError("N6A normalized projection baseline changed")
    if mode.get("classification_totals", {}).get("PROPOSED_CANONICAL_MATCH") != 51:
        raise NaptanN6CError("N6A classification baseline changed")
    if tfl.get("actual_n3_counts") != tfl.get("expected_n3_counts"):
        raise NaptanN6CError("N6A TfL reproduction baseline changed")
    return {"projection": projection, "mode_relevance": mode, "tfl_reproduction": tfl}


def build_case_register(data_dir: Path, sealed_migration_path: Path | None = None) -> dict[str, Any]:
    if PRODUCTION_WRITE_CAPABILITY:
        raise NaptanN6CError("N6C production write capability must remain false")
    if sealed_migration_path and _sha256_file(sealed_migration_path) != SEALED_N4A_SHA256:
        raise NaptanN6CError("sealed N4A hash mismatch")
    proposed, ambiguous, _manifest = _validate_n6b_inputs(data_dir)
    baseline = _projection(data_dir)
    cases = [_build_case(row, ambiguous=False) for row in proposed]
    cases.extend(_build_case(row, ambiguous=True) for row in ambiguous)
    cases.sort(key=lambda item: item["case_id"])
    if len(cases) != EXPECTED_CASE_COUNT or len({case["case_id"] for case in cases}) != EXPECTED_CASE_COUNT:
        raise NaptanN6CError("N6C case register is not exactly 60 unique cases")
    return {
        "batch": "RELIEF_NAPTAN_N6C",
        "scope": {
            "proposed_existing_canonical_cases": EXPECTED_PROPOSED_COUNT,
            "ambiguous_collision_cases": EXPECTED_AMBIGUOUS_COUNT,
            "total_cases": EXPECTED_CASE_COUNT,
            "excluded_proposed_new_complexes": 4_163,
            "excluded_ordinary_bus_coach_complexes": 75_920,
        },
        "source_classification_preserved": True,
        "machine_recommendations_are_not_human_decisions": True,
        "production_write_capability": False,
        "source_graph_reference": {
            "snapshot_key": SNAPSHOT_KEY,
            "sha256": FROZEN_SOURCE_SHA256,
            "byte_size": FROZEN_SOURCE_BYTES,
            "source_graph_rows": 706_745,
            "normalized_complexes": 93_751,
        },
        "n6a_baseline": {
            "classification_totals": baseline["mode_relevance"]["classification_totals"],
            "normalized_projection": baseline["projection"],
            "tfl_reproduction": baseline["tfl_reproduction"],
        },
        "cases": cases,
    }


def _recommendation_summary(register: dict[str, Any]) -> dict[str, Any]:
    cases = register["cases"]
    source_counts = Counter(case["source_classification"]["n6a"] for case in cases)
    machine_counts = Counter(case["n6c_machine_recommendation"] for case in cases)
    human_counts = Counter(case["human_adjudication"]["decision"] for case in cases)
    mode_counts: dict[str, Counter[str]] = {}
    for case in cases:
        mode = case["source_identity"]["source_mode"]
        mode_counts.setdefault(mode, Counter())[case["n6c_machine_recommendation"]] += 1
    return {
        "scope": register["scope"],
        "source_classification_counts": dict(sorted(source_counts.items())),
        "machine_recommendation_counts": dict(sorted(machine_counts.items())),
        "human_decision_counts": dict(sorted(human_counts.items())),
        "machine_recommendations_are_not_human_decisions": True,
        "human_decisions_pending": len(cases),
        "downstream_eligibility": {DOWNSTREAM_REVIEW_ONLY: len(cases)},
        "by_mode": {mode: dict(sorted(counter.items())) for mode, counter in sorted(mode_counts.items())},
        "production_mutations": 0,
    }


def _collision_register(register: dict[str, Any]) -> dict[str, Any]:
    rows = []
    for case in register["cases"]:
        if case["source_classification"]["n6a"] != "AMBIGUOUS_CANONICAL_MATCH":
            continue
        rows.append({
            "case_id": case["case_id"],
            "complex_identity": case["source_identity"]["complex_identity"],
            "source_name": case["source_identity"]["source_name"],
            "competing_facilities": case["candidate_evidence"]["candidate_facilities"],
            "competing_source_complexes": case["candidate_evidence"]["competing_source_complexes"],
            "collision_warnings": case["collision_warnings"],
            "subplace_warnings": case["subplace_warnings"],
            "required_human_state": HUMAN_PENDING,
        })
    if len(rows) != EXPECTED_AMBIGUOUS_COUNT:
        raise NaptanN6CError("collision register is not exactly 9 cases")
    return {"count": len(rows), "nearest_distance_tie_breaker": False, "cases": rows, "production_mutations": 0}


def _human_queue(register: dict[str, Any]) -> dict[str, Any]:
    cases = []
    for case in register["cases"]:
        primary = case["candidate_evidence"]["primary_candidate"]
        cases.append({
            "case_id": case["case_id"],
            "source_complex": case["source_identity"]["complex_identity"],
            "source_name": case["source_identity"]["source_name"],
            "source_mode": case["source_identity"]["source_mode"],
            "candidate_facility_id": primary.get("facility_id"),
            "candidate_facility_name": primary.get("facility_name"),
            "distance_metres": primary.get("distance_metres"),
            "direct_official_toilet_evidence": case["candidate_evidence"]["direct_official_toilet_evidence"],
            "existing_relief_toilet_evidence": case["candidate_evidence"]["existing_relief_canonical_toilet_evidence"],
            "collision": bool(case["collision_warnings"]),
            "subplace_warning": bool(case["subplace_warnings"]),
            "machine_recommendation": case["n6c_machine_recommendation"],
            "machine_reason_codes": case["machine_recommendation_reason_codes"],
            "human_decision": HUMAN_PENDING,
            "human_reviewer": None,
            "human_rationale": None,
            "human_review_timestamp": None,
        })
    return {
        "count": len(cases),
        "human_decision_field": HUMAN_PENDING,
        "fake_reviewer_metadata": False,
        "cases": cases,
        "production_mutations": 0,
    }


def _production_immutability(baseline: dict[str, Any]) -> dict[str, Any]:
    return {
        "read_only": True,
        "production_write_capability": False,
        "source_graph_mutations": 0,
        "canonical_facility_inserts": 0,
        "canonical_facility_updates": 0,
        "facility_source_inserts": 0,
        "facility_source_observation_mutations": 0,
        "toilet_unit_mutations": 0,
        "tfl_observation_mutations": 0,
        "import_run_mutations": 0,
        "auth_mutations": 0,
        "schema_mutations": 0,
        "migration_ledger_mutations": 0,
        "total_production_mutations": 0,
        "before_after_counts_equal": True,
        "source_counts": baseline["source_graph_counts"],
        "canonical_counts": baseline["canonical_counts"],
    }


def emit_artifacts(data_dir: Path, output_dir: Path, *, starting_sha: str, remote_sha: str, sealed_migration_path: Path) -> list[Path]:
    register = build_case_register(data_dir, sealed_migration_path)
    projection = _projection(data_dir)
    n6b_source = load_json(data_dir / "NAPTAN_N6B_SOURCE_BASELINE_2026-08-23.json")
    n6b_tfl_policy = load_json(data_dir / "NAPTAN_N6B_TFL_PRODUCT_POLICY_2026-08-23.json")
    n6b_tfl_obs = load_json(data_dir / "NAPTAN_N6B_14_TFL_OBSERVATION_ASSESSMENT_2026-08-23.json")
    n6b_human_boundary = load_json(data_dir / "NAPTAN_N6B_HUMAN_ADJUDICATION_BOUNDARY_2026-08-23.json")
    n6b_hierarchy = load_json(data_dir / "NAPTAN_N6B_TOILET_EVIDENCE_HIERARCHY_2026-08-23.json")
    n6b_mode = load_json(data_dir / "NAPTAN_N6B_TRANSPORT_MODE_POLICY_2026-08-23.json")
    n6b_arch = load_json(data_dir / "NAPTAN_N6B_FACILITY_PLACE_ASSESSMENT_2026-08-23.json")
    n6b_manifest = load_json(data_dir / "NAPTAN_N6B_FINAL_DECISION_MANIFEST_2026-08-23.json")
    baseline = {
        "source_graph_counts": n6b_source["source_graph_counts"],
        "canonical_counts": LIVE_PREFLIGHT["canonical_counts"],
    }
    preflight = {
        **LIVE_PREFLIGHT,
        "branch": "codex/toilet-map-apply-1a-production-deploy",
        "starting_local_sha": starting_sha,
        "starting_remote_sha": remote_sha,
        "sealed_n4a_sha256": _sha256_file(sealed_migration_path),
        "n6b_source_graph_baseline_reproduced": {
            "transport_source_snapshots": n6b_source["source_graph_counts"]["snapshots"],
            "transport_source_places": n6b_source["source_graph_counts"]["places"],
            "transport_source_nodes": n6b_source["source_graph_counts"]["nodes"],
            "transport_source_memberships": n6b_source["source_graph_counts"]["memberships"],
            "transport_source_place_parents": n6b_source["source_graph_counts"]["parents"],
            "total": n6b_source["source_graph_counts"]["total"],
        } == LIVE_PREFLIGHT["source_graph_counts"],
        "n6a_baseline_preserved": True,
        "n6b_manifest_total_production_mutations": n6b_manifest["total_production_mutations"],
    }
    cases = register["cases"]
    proposed = [case for case in cases if case["source_classification"]["n6a"] == "PROPOSED_CANONICAL_MATCH"]
    ambiguous = [case for case in cases if case["source_classification"]["n6a"] == "AMBIGUOUS_CANONICAL_MATCH"]
    mode_summary = {}
    for mode in ("rail", "metro_tram_underground", "multimodal", "ferry_port", "air", "bus_coach", "taxi", "no_mode"):
        cohort = [case for case in cases if case["source_identity"]["source_mode"] == mode]
        mode_summary[mode] = {
            "n6c_cases": len(cohort),
            "n6c_machine_recommendations": dict(sorted(Counter(case["n6c_machine_recommendation"] for case in cohort).items())),
            "direct_official_toilet_evidence_cases": sum(case["candidate_evidence"]["direct_official_toilet_evidence"] for case in cohort),
            "existing_relief_toilet_evidence_cases": sum(case["candidate_evidence"]["existing_relief_canonical_toilet_evidence"] for case in cohort),
        }
    artifacts: dict[str, Any] = {
        "NAPTAN_N6C_PRODUCTION_PREFLIGHT_2026-08-23.json": preflight,
        "NAPTAN_N6C_CASE_REGISTER_60_2026-08-23.json": register,
        "NAPTAN_N6C_51_PROPOSED_MATCH_ADJUDICATION_2026-08-23.json": {"count": len(proposed), "cases": proposed, "production_mutations": 0},
        "NAPTAN_N6C_9_AMBIGUOUS_CASE_ADJUDICATION_2026-08-23.json": {"count": len(ambiguous), "cases": ambiguous, "production_mutations": 0},
        "NAPTAN_N6C_RECOMMENDATION_SUMMARY_2026-08-23.json": _recommendation_summary(register),
        "NAPTAN_N6C_COLLISION_AND_SUBPLACE_REGISTER_2026-08-23.json": _collision_register(register),
        "NAPTAN_N6C_TFL_CROSS_EVIDENCE_2026-08-23.json": {
            "frozen_reproduction": projection["tfl_reproduction"],
            "n6b_tfl_product_policy": n6b_tfl_policy,
            "n6b_existing_14_observation_assessment": n6b_tfl_obs,
            "n6c_decision": "TfL may supply direct toilet evidence and NaPTAN may supply identity context; neither makes a transport root one canonical toilet facility.",
            "production_mutations": 0,
        },
        "NAPTAN_N6C_HUMAN_REVIEW_QUEUE_2026-08-23.json": _human_queue(register),
        "NAPTAN_N6C_PRODUCTION_IMMUTABILITY_2026-08-23.json": _production_immutability(baseline),
        "NAPTAN_N6C_FINAL_DECISION_MANIFEST_2026-08-23.json": {
            "classifications": [
                "N6B_SOURCE_CLASSIFICATION_PRESERVED",
                "N6C_CASE_REGISTER_COMPLETE",
                "N6C_MACHINE_RECOMMENDATIONS_COMPLETE",
                "N6C_HUMAN_DECISIONS_PENDING",
                "N6C_PRODUCTION_READ_ONLY",
                "N6C_NO_CANONICAL_PROMOTION",
                "N6C_NO_NEW_TRANSPORT_PLACES",
                "N6C_NO_SOURCE_GRAPH_MUTATION",
                "N6C_BOUNDED_HUMAN_REVIEW_READY",
            ],
            "n6b_policy_labels_preserved": list(n6b_manifest["classifications"]),
            "source_graph_rows": 706_745,
            "case_count": len(cases),
            "proposed_count": len(proposed),
            "ambiguous_count": len(ambiguous),
            "machine_recommendations_are_not_human_decisions": True,
            "human_decision_default": HUMAN_PENDING,
            "production_write_capability": False,
            "total_production_mutations": 0,
        },
    }
    output_dir.mkdir(parents=True, exist_ok=True)
    paths: list[Path] = []
    for name, payload in artifacts.items():
        path = output_dir / name
        path.write_text(json.dumps(payload, indent=2, ensure_ascii=False, sort_keys=True) + "\n", encoding="utf-8")
        paths.append(path)
    report = output_dir / "NAPTAN_N6C_BOUNDED_HUMAN_ADJUDICATION_2026-08-23.md"
    report.write_text(markdown_report(register, preflight, mode_summary, n6b_hierarchy, n6b_mode, n6b_arch, n6b_human_boundary), encoding="utf-8")
    paths.append(report)
    return paths


def markdown_report(register: dict[str, Any], preflight: dict[str, Any], mode_summary: dict[str, Any], hierarchy: dict[str, Any], mode_policy: dict[str, Any], architecture: dict[str, Any], human_boundary: dict[str, Any]) -> str:
    summary = _recommendation_summary(register)
    tfl = register["n6a_baseline"]["tfl_reproduction"]["actual_n3_counts"]
    lines = [
        "# RELIEF NAPTAN N6C — Bounded Human Adjudication of 60 Cases",
        "",
        "## Scope and safety",
        "",
        "This is a read-only adjudication-preparation transaction. The case register is derived from the committed N6B 51 proposed existing-canonical cases and 9 ambiguous/collision cases. It does not represent human decisions or production authorization.",
        "",
        f"- Production project: `Relief` / `{preflight['project_ref']}` (`{preflight['project_status']}`), region `{preflight['region']}`.",
        f"- Starting checkpoint: `{preflight['starting_local_sha']}` local and `{preflight['starting_remote_sha']}` remote.",
        f"- Sealed N4A SHA-256: `{preflight['sealed_n4a_sha256']}`.",
        "- `PRODUCTION_WRITE_CAPABILITY = false`; no production DML, DDL, provenance, source-graph, canonical, or migration operation was executed.",
        "",
        "## N6A/N6B baseline preserved",
        "",
        "The authoritative N6A/N6B source classifications are unchanged: 51 `PROPOSED_CANONICAL_MATCH`, 9 `AMBIGUOUS_CANONICAL_MATCH`, 4,163 proposed-new analytical complexes, and 75,933 supporting/no-action outcomes. N6C excludes the proposed-new and supporting/no-action populations.",
        "",
        "The production source graph remains 1 snapshot, 97,270 places, 436,428 nodes, 169,527 memberships, and 3,519 parent edges: 706,745 rows. The normalized projection remains 93,751 complexes; N6C does not persist it.",
        "",
        "## Case register",
        "",
        f"Exactly {register['scope']['total_cases']} deterministic cases are registered: {register['scope']['proposed_existing_canonical_cases']} proposed existing-canonical cases and {register['scope']['ambiguous_collision_cases']} ambiguous/collision cases. Each has a stable case ID, frozen source classification, machine recommendation, evidence deficiencies, warnings, and a human decision initialized to `{HUMAN_PENDING}`.",
        "",
        f"Machine recommendation counts: `{json.dumps(summary['machine_recommendation_counts'], sort_keys=True)}`. These are review guidance only; no recommendation is a decision.",
        "",
        "The nine ambiguous cases retain all competing candidate/source relationships. Cockfosters, Wapping Wharf, Oakwood, Falkirk Grahamston, Dunoon Ferry Terminal, Canary Wharf, Hillingdon, and North Greenwich remain visible as collision/subplace cases. Nearest distance is explicitly prohibited as a tie-breaker.",
        "",
        "## Mode cohort view",
        "",
        "| Mode | N6C cases | Direct official toilet evidence | Existing Relief toilet evidence | Machine recommendations |",
        "|---|---:|---:|---:|---|",
    ]
    for mode in ("rail", "metro_tram_underground", "multimodal", "ferry_port", "air", "bus_coach", "taxi", "no_mode"):
        row = mode_summary[mode]
        lines.append(f"| {mode} | {row['n6c_cases']:,} | {row['direct_official_toilet_evidence_cases']:,} | {row['existing_relief_toilet_evidence_cases']:,} | `{json.dumps(row['n6c_machine_recommendations'], sort_keys=True)}` |")
    lines += [
        "",
        "Ordinary bus/coach stops remain outside N6C. The 4,163 proposed-new transport places are not a promotion backlog. NaPTAN identity is context and reconciliation evidence, not proof that a transport root is a toilet facility.",
        "",
        "## Evidence policy",
        "",
        "1. Direct official toilet evidence may support bounded review of an actual toilet facility or unit.",
        "2. Existing Relief canonical toilet evidence plus NaPTAN identity may support review of an existing facility relationship.",
        "3. Strong transport-place reconciliation alone remains supporting context.",
        "4. Proximity/context alone never supports canonical promotion.",
        "",
        "Rail, metro/Underground/tram, ferry/port, and air cases retain mode-specific warnings. Multimodal cases require subplace-aware review; a station, interchange, or terminal root is not collapsed into one physical toilet location.",
        "",
        "## TfL cross-evidence",
        "",
        f"The frozen 509-station reproduction remains exact: {tfl['HIGH_CONFIDENCE_COMPLEX_MATCH']} high-confidence complex, {tfl['HIGH_CONFIDENCE_SUBPLACE_MATCH']} high-confidence subplace, {tfl['MULTIMODAL_COMPLEX_MATCH']} multimodal, {tfl['AMBIGUOUS_COMPLEX']} ambiguous, and {tfl['NO_MATCH']} no-match; exact official identifier matches remain 0 and 28 N2 ambiguities remain resolved. Existing 14 TfL observations are unchanged.",
        "",
        "NaPTAN can supply station/complex identity context. TfL can supply direct toilet evidence. Neither source authorizes representing an entire complex as one toilet facility when multiple physical locations or units exist.",
        "",
        "## Facility versus place boundary",
        "",
        f"The current product boundary remains: {architecture.get('recommendation', 'retain the existing facility-only model for now')}. `facilities` should not be overloaded with 93,751 transport complexes. A separate place/transport entity would require a distinct product/schema authorization and is not implemented here.",
        "",
        "## Human adjudication boundary",
        "",
        "Human review is required for source-to-multiple-facility collisions, multiple source complexes claiming one facility, multimodal root/subplace uncertainty, generic or token-subset-only names, nearby-but-separate toilet locations, and conflicting authoritative evidence. No reviewer identity, timestamp, rationale, approval, or rejection has been fabricated.",
        "",
        "## N6C outputs and next boundary",
        "",
        "The JSON case register and human-review queue are the deterministic evidence. All 60 cases remain `PENDING_HUMAN_REVIEW` and `REVIEW_ONLY_NOT_AUTHORIZED`. The smallest next transaction is a separately authorized human adjudication review of these 60 cases; any production promotion would require another explicit authorization and must remain separate from this preparation batch.",
        "",
        "## Final classifications",
        "",
        "- `N6B_SOURCE_CLASSIFICATION_PRESERVED`",
        "- `N6C_CASE_REGISTER_COMPLETE`",
        "- `N6C_MACHINE_RECOMMENDATIONS_COMPLETE`",
        "- `N6C_HUMAN_DECISIONS_PENDING`",
        "- `N6C_PRODUCTION_READ_ONLY`",
        "- `N6C_NO_CANONICAL_PROMOTION`",
        "- `N6C_NO_NEW_TRANSPORT_PLACES`",
        "- `N6C_NO_SOURCE_GRAPH_MUTATION`",
        "- `N6C_BOUNDED_HUMAN_REVIEW_READY`",
        "",
        "`TOTAL PRODUCTION MUTATIONS: 0`",
    ]
    return "\n".join(lines) + "\n"


def main() -> None:
    parser = argparse.ArgumentParser(description="Emit deterministic read-only N6C adjudication evidence")
    parser.add_argument("--data-dir", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--sealed-migration", type=Path, required=True)
    parser.add_argument("--starting-sha", required=True)
    parser.add_argument("--remote-sha", required=True)
    args = parser.parse_args()
    paths = emit_artifacts(args.data_dir, args.output_dir, starting_sha=args.starting_sha, remote_sha=args.remote_sha, sealed_migration_path=args.sealed_migration)
    print(json.dumps({"production_write_capability": False, "case_count": EXPECTED_CASE_COUNT, "artifacts": [str(path) for path in paths]}, sort_keys=True))


if __name__ == "__main__":
    main()

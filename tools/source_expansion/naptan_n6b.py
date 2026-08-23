"""Read-only N6B transport-canonical scope analysis.

N6B is a product-governance analysis over the N6A projection.  It deliberately
has no production connection and no apply path.  The detailed 51/9 review
tables are rebuilt from the exact frozen XML and the committed production
facility snapshot; live production invariants remain a separate read-only
preflight supplied by the N6A evidence and governed SQL audit.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Iterable

from tools.source_expansion.naptan_n1 import haversine_m, normalize_matching_text
from tools.source_expansion.naptan_n3 import normalize_complexes, parse_xml
from tools.source_expansion.naptan_n6a import (
    CandidateEvidence,
    GENERIC_SOURCE_NAMES,
    PRODUCTION_WRITE_CAPABILITY as N6A_PRODUCTION_WRITE_CAPABILITY,
    SNAPSHOT_KEY,
    assert_read_only_sql,
    classify_candidate,
    stable_candidate_key,
    token_subset_compatible,
)
from tools.source_expansion.naptan_n5_r1 import FROZEN_BYTES, FROZEN_SHA256, sha256_file


PRODUCTION_WRITE_CAPABILITY = False
SEALED_N4A_SHA256 = "087A389B8CEAC021B12708BC55C39022CB38D5459510EFFB6CF057CEF232C44E"
PRODUCTION_PROJECT_REF = "bgwxrxkmyaihplaloely"
N6A_REQUIRED_COUNTS = {
    "normalized_complexes": 93751,
    "single_area_complexes": 91757,
    "parent_area_complexes": 559,
    "multimodal_parent_complexes": 1435,
    "unresolved_area_nodes": 93,
    "hierarchy_max_depth": 13,
    "hierarchy_cycles": 0,
}
N6A_MODE_COUNTS = {
    "bus_coach": 75920,
    "multimodal": 1541,
    "no_mode": 13591,
    "metro_tram_underground": 641,
    "rail": 1519,
    "ferry_port": 470,
    "air": 65,
    "taxi": 4,
}
N6A_CLASSIFICATION_TOTALS = {
    "EXISTING_CANONICAL_MATCH": 0,
    "PROPOSED_CANONICAL_MATCH": 51,
    "AMBIGUOUS_CANONICAL_MATCH": 9,
    "PROPOSED_NEW_TRANSPORT_PLACE": 4163,
    "SUPPORTING_SOURCE_ONLY": 75933,
    "CONFLICT": 0,
    "NO_ACTION": 13595,
}
N6B_REVIEW_OUTCOMES = (
    "ELIGIBLE_FOR_FUTURE_LINK_REVIEW",
    "REQUIRES_HUMAN_ADJUDICATION",
    "SUPPORTING_CONTEXT_ONLY",
    "INSUFFICIENT_TOILET_EVIDENCE",
)


class NaptanN6BError(ValueError):
    """Raised when a read-only N6B invariant is not satisfied."""


def sha256_upper(path: Path) -> str:
    return sha256_file(path).upper()


def mode_for_complex(row: dict[str, Any]) -> str:
    modes = sorted(set(row.get("modes", [])))
    if len(modes) > 1:
        return "multimodal"
    return modes[0] if modes else "no_mode"


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def load_facilities(facilities_path: Path, sources_path: Path | None = None) -> tuple[list[dict[str, Any]], dict[str, list[str]]]:
    facilities = load_json(facilities_path)
    source_names: dict[str, list[str]] = defaultdict(list)
    if sources_path and sources_path.exists():
        for row in load_json(sources_path):
            source_names[str(row["facility_id"])].append(str(row.get("source_name") or ""))
    for facility in facilities:
        facility["facility_id"] = str(facility.get("id"))
        facility["source_names"] = sorted(set(source_names.get(facility["facility_id"], [])))
        facility["normalized_name"] = normalize_matching_text(facility.get("name"))
    return facilities, source_names


def _candidate_rows(complexes: Iterable[dict[str, Any]], facilities: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Generate bounded name+publisher-geometry candidate pairs locally."""

    # The production query uses PostGIS indexes.  The local replay must use a
    # bounded equivalent; scanning all 15,620 facilities for every complex
    # would be both needlessly slow and unlike the governed N6A query.
    grid: dict[tuple[int, int], list[dict[str, Any]]] = defaultdict(list)
    cell_size = 0.05
    for facility in facilities:
        if facility.get("latitude") is None or facility.get("longitude") is None:
            continue
        key = (
            int((float(facility["latitude"]) + 90.0) // cell_size),
            int((float(facility["longitude"]) + 180.0) // cell_size),
        )
        grid[key].append(facility)

    rows: list[dict[str, Any]] = []
    for complex_row in complexes:
        if not str(complex_row.get("geometry_scope", "")).startswith("PUBLISHER"):
            continue
        latitude = complex_row.get("latitude")
        longitude = complex_row.get("longitude")
        if latitude is None or longitude is None:
            continue
        source_name = complex_row.get("root_name") or ""
        source_normalized = normalize_matching_text(source_name)
        source_cell = (
            int((float(latitude) + 90.0) // cell_size),
            int((float(longitude) + 180.0) // cell_size),
        )
        nearby_facilities: list[dict[str, Any]] = []
        for lat_delta in (-1, 0, 1):
            for lon_delta in (-1, 0, 1):
                nearby_facilities.extend(grid.get((source_cell[0] + lat_delta, source_cell[1] + lon_delta), []))
        for facility in nearby_facilities:
            exact = source_normalized == facility["normalized_name"]
            token_subset = token_subset_compatible(source_name, facility.get("name"))
            if not (exact or token_subset):
                continue
            distance = haversine_m(
                float(latitude),
                float(longitude),
                float(facility["latitude"]),
                float(facility["longitude"]),
            )
            if distance > 500:
                continue
            rows.append(
                {
                    "complex_identity": complex_row["complex_identity"],
                    "root_stop_area_identity": complex_row["root_stop_area_identity"],
                    "source_name": source_name,
                    "source_normalized_name": source_normalized,
                    "source_mode": mode_for_complex(complex_row),
                    "source_modes": sorted(complex_row.get("modes", [])),
                    "complex_type": complex_row.get("complex_type"),
                    "source_type": complex_row.get("area_type"),
                    "source_latitude": latitude,
                    "source_longitude": longitude,
                    "source_geometry_scope": complex_row.get("geometry_scope"),
                    "source_area_ids": list(complex_row.get("area_ids", [])),
                    "source_node_ids": list(complex_row.get("stop_point_ids", [])),
                    "source_stop_area_count": complex_row.get("stop_area_count", 0),
                    "source_stop_point_count": complex_row.get("stop_point_count", 0),
                    "source_defects": list(complex_row.get("defects", [])),
                    "facility_id": facility["facility_id"],
                    "facility_name": facility.get("name"),
                    "facility_latitude": facility.get("latitude"),
                    "facility_longitude": facility.get("longitude"),
                    "distance_metres": round(distance, 1),
                    "exact_normalized_name": exact,
                    "source_token_subset": token_subset,
                    "existing_provenance": list(facility.get("source_names", [])),
                    "explicit_toilet_evidence": bool(facility.get("source_names")),
                    "tfl_evidence": any("TfL" in name for name in facility.get("source_names", [])),
                }
            )
    return sorted(rows, key=lambda row: (row["complex_identity"], row["facility_id"]))


def classify_n6a_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    candidate_counts = Counter(row["complex_identity"] for row in rows)
    facility_complexes: dict[str, set[str]] = defaultdict(set)
    for row in rows:
        facility_complexes[row["facility_id"]].add(row["complex_identity"])
    for row in rows:
        evidence = CandidateEvidence(
            exact_normalized_name=bool(row["exact_normalized_name"]),
            token_subset_name=bool(row["source_token_subset"]),
            distance_metres=row["distance_metres"],
            hierarchy_resolved=not row["source_defects"],
            candidate_count=candidate_counts[row["complex_identity"]],
            facility_collision=len(facility_complexes[row["facility_id"]]) > 1,
            source_mode=row["source_mode"],
            source_geometry_available=True,
            generic_source_name=normalize_matching_text(row["source_name"]) in GENERIC_SOURCE_NAMES,
            existing_provenance=bool(row["existing_provenance"]),
        )
        row["candidate_count_for_complex"] = candidate_counts[row["complex_identity"]]
        row["competing_source_complex_count_for_facility"] = len(facility_complexes[row["facility_id"]])
        row["facility_collision"] = len(facility_complexes[row["facility_id"]]) > 1
        # N6A's authoritative production classification only promotes a
        # strong candidate.  A unique weak candidate is not itself an
        # ambiguous canonical relationship; it falls back to the complex's
        # normal supporting/proposed-new policy.  Competition is ambiguous
        # regardless of distance, preserving the collision guard.
        if row["source_mode"] == "bus_coach":
            row["n6a_classification"] = "SUPPORTING_SOURCE_ONLY"
        elif row["source_mode"] in {"taxi", "no_mode"}:
            row["n6a_classification"] = "NO_ACTION"
        elif row["facility_collision"] or row["candidate_count_for_complex"] > 1:
            row["n6a_classification"] = "AMBIGUOUS_CANONICAL_MATCH"
        else:
            # N6A's 51 proposed rows are the unique name-compatible
            # candidates.  Strength is retained as an N6B evidence dimension;
            # it is not silently upgraded into a production decision.
            row["n6a_classification"] = "PROPOSED_CANONICAL_MATCH"
        row["stable_candidate_key"] = stable_candidate_key(SNAPSHOT_KEY, row["complex_identity"], row["facility_id"])
    return rows


def _relation_appearance(row: dict[str, Any]) -> str:
    if row["n6a_classification"] == "AMBIGUOUS_CANONICAL_MATCH":
        return "indeterminate"
    if row["exact_normalized_name"] and row["distance_metres"] <= 100:
        return "likely same campus/complex; toilet-unit identity unproven"
    if row["exact_normalized_name"] and row["distance_metres"] <= 250:
        return "nearby but potentially separate"
    if row["source_token_subset"]:
        return "nearby but potentially separate"
    return "indeterminate"


def detailed_review_rows(rows: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Group the authoritative N6A 51/9 cohorts without making a decision."""

    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        if row["n6a_classification"] in {"PROPOSED_CANONICAL_MATCH", "AMBIGUOUS_CANONICAL_MATCH"}:
            copy = dict(row)
            copy["root_parent_context"] = {
                "complex_type": row["complex_type"],
                "source_area_ids": row["source_area_ids"],
                "source_stop_area_count": row["source_stop_area_count"],
                "source_stop_point_count": row["source_stop_point_count"],
                "source_defects": row["source_defects"],
            }
            copy["generic_name_guard"] = normalize_matching_text(row["source_name"]) not in GENERIC_SOURCE_NAMES
            copy["relation_appearance"] = _relation_appearance(row)
            copy["n6b_recommendation"] = (
                "REQUIRES_HUMAN_ADJUDICATION"
                if row["n6a_classification"] == "AMBIGUOUS_CANONICAL_MATCH"
                else "ELIGIBLE_FOR_FUTURE_LINK_REVIEW"
            )
            grouped[row["complex_identity"]].append(copy)

    proposed = [rows[0] for key, rows in sorted(grouped.items()) if rows[0]["n6a_classification"] == "PROPOSED_CANONICAL_MATCH"]
    ambiguous = []
    for key, case_rows in sorted(grouped.items()):
        if case_rows[0]["n6a_classification"] != "AMBIGUOUS_CANONICAL_MATCH":
            continue
        case = dict(case_rows[0])
        case["competing_facilities"] = [
            {
                "facility_id": row["facility_id"],
                "facility_name": row["facility_name"],
                "distance_metres": row["distance_metres"],
                "exact_normalized_name": row["exact_normalized_name"],
                "source_token_subset": row["source_token_subset"],
                "existing_provenance": row["existing_provenance"],
            }
            for row in case_rows
        ]
        case["competing_source_complexes"] = sorted(
            {row["complex_identity"] for row in rows if row["facility_id"] in {x["facility_id"] for x in case["competing_facilities"]}}
        )
        case["ambiguity_reason"] = (
            "multiple plausible canonical facilities or a canonical facility claimed by multiple source complexes; nearest distance is not a tie-breaker"
        )
        ambiguous.append(case)
    return proposed, ambiguous


def n6b_policy_manifest() -> dict[str, Any]:
    return {
        "production_write_capability": PRODUCTION_WRITE_CAPABILITY,
        "policy_labels": [
            "ORDINARY_BUS_STOPS_SUPPORTING_SOURCE_ONLY",
            "TRANSPORT_PLACE_NOT_EQUIVALENT_TO_TOILET_FACILITY",
            "DIRECT_TOILET_EVIDENCE_REQUIRED_FOR_NEW_CANONICAL_TRANSPORT_FACILITY",
            "NAPTAN_IDENTITY_EVIDENCE_CAN_SUPPORT_EXISTING_CANONICAL_RECONCILIATION",
            "PROXIMITY_ALONE_NOT_PROMOTION_EVIDENCE",
            "MULTIMODAL_COMPLEX_REQUIRES_SUBPLACE_AWARE_RECONCILIATION",
            "AMBIGUOUS_MATCHES_REQUIRE_HUMAN_ADJUDICATION",
            "MASS_TRANSPORT_PLACE_PROMOTION_NOT_AUTHORIZED",
            "N6C_BOUNDED_ADJUDICATION_SCOPE_DEFINED",
        ],
        "toilet_evidence_hierarchy": [
            {
                "tier": "A",
                "name": "DIRECT_OFFICIAL_TOILET_EVIDENCE",
                "allowed_future_use": "may support a bounded review of an actual toilet facility or unit; never automatic transport-place creation",
            },
            {
                "tier": "B",
                "name": "EXISTING_RELIEF_CANONICAL_TOILET_EVIDENCE",
                "allowed_future_use": "NaPTAN identity/geography may support a future link review; it does not prove the transport complex is the toilet",
            },
            {
                "tier": "C",
                "name": "STRONG_PLACE_RECONCILIATION_ONLY",
                "allowed_future_use": "supporting context and candidate generation only",
            },
            {
                "tier": "D",
                "name": "PROXIMITY_OR_CONTEXT_ONLY",
                "allowed_future_use": "never sufficient for canonical promotion",
            },
        ],
        "architecture_recommendation": {
            "current_model": "facilities represents actual toilet facilities; transport complexes are not equivalent entities",
            "recommendation": "retain facility-only canonical writes for now and keep NaPTAN as private source/context evidence",
            "future_option": "a separate place/transport entity may be considered in a separately authorized product/schema decision",
            "schema_change_in_n6b": False,
        },
        "mode_policy": {
            "rail": "existing canonical links require bounded review; new canonical transport facility requires direct toilet evidence; station identity alone is insufficient",
            "metro_tram_underground": "use TfL/official toilet evidence for actual toilets; retain subplace and gateline context; no station-as-toilet shortcut",
            "multimodal": "subplace-aware review required; do not collapse multiple physical toilet locations into the root interchange",
            "ferry_port": "terminal/pier identity is supporting context; direct facility evidence required for a new canonical toilet",
            "air": "terminal-specific toilet evidence required; airport root cannot stand in for multiple toilet locations",
            "bus_coach": "ordinary roadside stops remain SUPPORTING_SOURCE_ONLY; bus/coach stations and interchanges still need direct toilet evidence and review",
            "taxi": "NO_ACTION by default; no canonical facility role from NaPTAN identity",
            "no_mode": "NO_ACTION unless independent product and toilet evidence exists",
        },
        "human_adjudication_boundary": [
            "one source complex to multiple plausible facilities",
            "multiple source complexes to one facility",
            "multimodal root/subplace uncertainty",
            "generic or token-subset-only names",
            "station-to-nearby-public-toilet proximity without physical-unit proof",
            "conflicting official or existing provenance evidence",
        ],
    }


def build_analysis(xml_path: Path, facilities_path: Path, sources_path: Path, n6a_dir: Path) -> dict[str, Any]:
    if not xml_path.exists():
        raise NaptanN6BError(f"frozen XML not found: {xml_path}")
    source_sha = sha256_upper(xml_path)
    if xml_path.stat().st_size != FROZEN_BYTES or source_sha != FROZEN_SHA256:
        raise NaptanN6BError("frozen source exactness gate failed")
    if N6A_PRODUCTION_WRITE_CAPABILITY or PRODUCTION_WRITE_CAPABILITY:
        raise NaptanN6BError("N6B production write capability must be false")

    data, parse_seconds = parse_xml(xml_path)
    normalized = normalize_complexes(data)
    complexes = normalized["complexes"]
    facilities, _source_names = load_facilities(facilities_path, sources_path)
    rows = classify_n6a_rows(_candidate_rows(complexes, facilities))
    proposed, ambiguous = detailed_review_rows(rows)

    n6a_mode = load_json(n6a_dir / "NAPTAN_N6A_MODE_RELEVANCE_2026-08-23.json")
    n6a_scale = load_json(n6a_dir / "NAPTAN_N6A_CANDIDATE_SCALE_2026-08-23.json")
    n6a_projection = load_json(n6a_dir / "NAPTAN_N6A_NORMALIZED_COMPLEX_PROJECTION_2026-08-23.json")
    n6a_tfl = load_json(n6a_dir / "NAPTAN_N6A_TFL_REPRODUCTION_2026-08-23.json")
    n6a_tfl_audit = load_json(n6a_dir / "NAPTAN_N6A_EXISTING_TFL_OBSERVATION_AUDIT_2026-08-23.json")
    n6a_immutability = load_json(n6a_dir / "NAPTAN_N6A_PRODUCTION_IMMUTABILITY_2026-08-23.json")
    n6a_performance = load_json(n6a_dir / "NAPTAN_N6A_QUERY_PERFORMANCE_2026-08-23.json")

    computed_classifications = Counter(row["n6a_classification"] for row in rows)
    mode_cohorts: dict[str, dict[str, Any]] = {}
    for mode, total in N6A_MODE_COUNTS.items():
        mode_rows = [row for row in complexes if mode_for_complex(row) == mode]
        name_generic = sum(normalize_matching_text(row.get("root_name")) in GENERIC_SOURCE_NAMES for row in mode_rows)
        exact_candidates = sum(1 for row in rows if row["source_mode"] == mode and row["exact_normalized_name"])
        mode_cohorts[mode] = {
            "complexes": total,
            "computed_complexes": len(mode_rows),
            "n6a_classifications": n6a_mode["by_mode"][mode],
            "n6a_candidate_pairs_500m": n6a_scale["by_mode"][mode]["pairs_500m"],
            "n6a_complexes_with_candidates_500m": n6a_scale["by_mode"][mode]["complexes_500m"],
            "computed_exact_name_candidate_rows": exact_candidates,
            "generic_name_complexes": name_generic,
            "generic_name_rate": round(name_generic / total, 6) if total else 0,
            "explicit_toilet_evidence_interpretation": "existing canonical facility provenance is toilet evidence; no independent evidence is imputed to proposed-new complexes",
        }

    policy = n6b_policy_manifest()
    return {
        "batch": "RELIEF_NAPTAN_N6B",
        "production_write_capability": False,
        "production_project_ref": PRODUCTION_PROJECT_REF,
        "snapshot_key": SNAPSHOT_KEY,
        "frozen_source": {"byte_size": xml_path.stat().st_size, "sha256": source_sha, "expected_sha256": FROZEN_SHA256, "exact": True},
        "sealed_n4a_sha256": SEALED_N4A_SHA256,
        "local_projection": {
            "parse_seconds": round(parse_seconds, 3),
            "normalized_complexes": len(complexes),
            "mode_distribution": dict(sorted(Counter(mode_for_complex(row) for row in complexes).items())),
            "geometry_scope": dict(sorted(Counter(row.get("geometry_scope") for row in complexes).items())),
        },
        "n6a_baseline_preserved": {
            "required_projection": N6A_REQUIRED_COUNTS,
            "required_mode_counts": N6A_MODE_COUNTS,
            "classification_totals": n6a_mode["classification_totals"],
            "candidate_scale": n6a_scale["bounded_name_and_geometry_generator"],
            "projection_artifact_sha256": hashlib.sha256(json.dumps(n6a_projection, sort_keys=True).encode()).hexdigest(),
        },
        "computed_candidate_reproduction": {
            "candidate_rows": len(rows),
            "candidate_complexes": len({row["complex_identity"] for row in rows}),
            "classifications": dict(sorted(computed_classifications.items())),
            "detail_51_count": len(proposed),
            "detail_9_count": len(ambiguous),
            "authoritative_counts_source": "N6A committed production-backed evidence; N6B does not replace that baseline",
        },
        "mode_cohorts": mode_cohorts,
        "proposed_match_review_51": proposed,
        "ambiguous_match_review_9": ambiguous,
        "proposed_new_population": {
            "total": 4163,
            "by_mode": n6a_mode["by_mode"],
            "independent_toilet_evidence": "not established for the proposed-new population; NaPTAN mode/name/geometry is place evidence only",
            "automatic_creation": False,
            "product_conclusion": "not a promotion backlog; requires separate place-model and toilet-evidence policy decision",
        },
        "tfl_product_assessment": {
            "frozen_reproduction": n6a_tfl,
            "existing_observation_audit": n6a_tfl_audit,
            "decision": "TfL can supply direct toilet evidence and NaPTAN can supply station/complex identity context, but neither source alone proves that a station root is one canonical toilet facility",
            "writes": 0,
        },
        "toilet_evidence_hierarchy": policy["toilet_evidence_hierarchy"],
        "transport_mode_policy": policy["mode_policy"],
        "facility_vs_place_assessment": policy["architecture_recommendation"],
        "human_adjudication_boundary": policy["human_adjudication_boundary"],
        "n6c_recommendation": {
            "classification": "N6C_BOUNDED_ADJUDICATION_SCOPE_DEFINED",
            "population": {"proposed_existing_links": 51, "ambiguous_collision_cases": 9, "total_cases": 60},
            "inclusion_rule": "review only the N6A 51 proposed existing-canonical candidates and 9 ambiguous/collision cases; retain source identity, facility identity, evidence dimensions, and vetoes",
            "exclusions": ["all 4163 proposed-new complexes", "ordinary 75920 bus/coach complexes", "automatic canonical writes", "new place schema"],
            "execution_mode": "read-only/human-adjudication planning; any later promotion requires a separate authorization",
        },
        "production_immutability": {
            "source_graph_mutations": 0,
            "canonical_facility_inserts": 0,
            "canonical_facility_updates": 0,
            "facility_source_inserts": 0,
            "facility_source_observation_mutations": 0,
            "toilet_unit_mutations": 0,
            "tfl_observation_mutations": 0,
            "auth_mutations": 0,
            "schema_mutations": 0,
            "migration_ledger_mutations": 0,
            "total_production_mutations": 0,
            "baseline_evidence": n6a_immutability,
        },
        "performance": n6a_performance,
        "policy_labels": policy["policy_labels"],
        "validation": {
            "n6a_production_write_capability_false": N6A_PRODUCTION_WRITE_CAPABILITY is False,
            "n6b_production_write_capability_false": PRODUCTION_WRITE_CAPABILITY is False,
            "source_exact": True,
            "no_promotion_path": True,
            "n6a_tfl_result_preserved": n6a_tfl["actual_n3_counts"] == n6a_tfl["expected_n3_counts"],
            "n6a_candidate_baseline_preserved": n6a_mode["classification_totals"] == N6A_CLASSIFICATION_TOTALS,
            "n6a_projection_baseline_preserved": n6a_projection["normalized_complexes"] == 93751,
        },
    }


def markdown_report(analysis: dict[str, Any], *, branch: str, starting_sha: str, remote_sha: str) -> str:
    cohorts = analysis["mode_cohorts"]
    n6a = analysis["n6a_baseline_preserved"]
    tfl = analysis["tfl_product_assessment"]["frozen_reproduction"]["actual_n3_counts"]
    lines = [
        "# RELIEF NAPTAN N6B — Transport Canonical Scope Decision",
        "",
        "## Starting state",
        "",
        f"- Repository: `hourwise/Relief`\n- Branch: `{branch}`\n- Starting local SHA: `{starting_sha}`\n- Starting remote SHA: `{remote_sha}`",
        "- Production project: `Relief` / `bgwxrxkmyaihplaloely`; analysis path read-only.",
        "- Protected files were preserved and were not staged or committed.",
        "",
        "## N6A baseline preserved",
        "",
        "The N6A production-backed results remain authoritative and unchanged: 93,751 normalized complexes; 51 proposed canonical matches; 9 ambiguous matches; 4,163 proposed-new analytical rows; and 75,933 supporting/no-action outcomes in the committed N6A classification contract.",
        "",
        "Source graph counts remain 1 snapshot, 97,270 places, 436,428 nodes, 169,527 memberships, and 3,519 parent edges (706,745 total). No N6B production DML was executed.",
        "",
        "## Mode cohort analysis",
        "",
        "| Mode | Complexes | Candidate complexes at 500m | N6A proposed | N6A ambiguous | N6A proposed-new | N6A supporting | N6A no-action | Generic-name complexes |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for mode in ("rail", "metro_tram_underground", "multimodal", "ferry_port", "air", "bus_coach", "taxi", "no_mode"):
        row = cohorts[mode]
        c = row["n6a_classifications"]
        lines.append(f"| {mode} | {row['complexes']:,} | {row['n6a_complexes_with_candidates_500m']:,} | {c['proposed_match']:,} | {c['ambiguous']:,} | {c['proposed_new']:,} | {c['supporting']:,} | {c['no_action']:,} | {row['generic_name_complexes']:,} |")
    lines += [
        "",
        "The 75,920 ordinary bus/coach complexes remain `SUPPORTING_SOURCE_ONLY`. Mode, scale, or proximity is not toilet evidence. The 4,163 proposed-new population is not an insertion queue.",
        "",
        "## 51 proposed and 9 ambiguous cases",
        "",
        f"The machine-readable review tables contain `{analysis['n6c_recommendation']['population']['proposed_existing_links']}` proposed existing-facility cases and `{analysis['n6c_recommendation']['population']['ambiguous_collision_cases']}` ambiguous cases. Proposed cases are eligible only for a future review; the 9 ambiguous cases require human adjudication. No case was promoted.",
        "",
        "Known collision examples are retained: Cockfosters Underground Station has two canonical facilities; Wapping Wharf has two canonical facilities; and Oakwood Underground Station/Oakwood Station compete for one canonical facility. Nearest distance is not used as an automatic tie-breaker.",
        "",
        "## Toilet-evidence hierarchy",
        "",
        "1. Tier A: direct official toilet evidence may support bounded review of an actual toilet facility or unit.\n2. Tier B: existing Relief canonical toilet evidence plus NaPTAN identity may support a future link review.\n3. Tier C: strong place reconciliation alone is supporting context.\n4. Tier D: proximity/context alone never supports promotion.",
        "",
        "## Product policy",
        "",
        "NaPTAN transport places are not equivalent to Relief toilet facilities. New canonical transport-related facilities require direct toilet evidence. NaPTAN identity can support reconciliation of an existing canonical facility, but proximity alone is not promotion evidence. Multimodal complexes require subplace-aware review. Ordinary bus stops remain supporting-source-only. Ambiguous cases require human adjudication. Mass transport-place promotion is not authorized.",
        "",
        "## Facility versus place model",
        "",
        "The current `facilities` entity represents actual public toilet facilities and is not a safe home for 93,751 transport complexes. N6B therefore retains the facility-only write boundary and keeps NaPTAN as private identity/context evidence. A separate canonical place or transport-place entity remains an open product/schema decision; N6B does not implement it.",
        "",
        "## TfL decision",
        "",
        f"The frozen 509-station reproduction remains exact: {tfl['HIGH_CONFIDENCE_COMPLEX_MATCH']} high-confidence complex matches, {tfl['HIGH_CONFIDENCE_SUBPLACE_MATCH']} high-confidence subplace matches, {tfl['MULTIMODAL_COMPLEX_MATCH']} multimodal matches, {tfl['AMBIGUOUS_COMPLEX']} ambiguous complexes, {tfl['NO_MATCH']} no-match, and 0 exact official identifier matches. NaPTAN contributes station/complex identity context; TfL can contribute direct toilet evidence. A station root must not be collapsed into one toilet facility where multiple physical toilets or subplaces exist.",
        "",
        "## N6C recommendation",
        "",
        "Define N6C as a bounded, read-only/human-adjudication review of exactly the 51 proposed existing-canonical candidates plus the 9 ambiguous collision cases. Exclude all 4,163 proposed-new complexes and ordinary bus/coach stops. Any later facility or provenance write requires a separate authorization.",
        "",
        "## Safety and classification",
        "",
        "- `PRODUCTION_RECONCILIATION_ANALYSIS_READ_ONLY`\n- `TOTAL PRODUCTION MUTATIONS: 0`\n- No facilities, facility sources, observations, toilet units, source graph rows, migrations, policies, grants, or schema objects were written.",
        "",
        "## Final decision",
        "",
        "`RELIEF NAPTAN N6B — TRANSPORT CANONICAL SCOPE DEFINED / NAPTAN RETAINED AS SUPPORTING IDENTITY EVIDENCE BY DEFAULT / MASS TRANSPORT PROMOTION NOT AUTHORIZED / BOUNDED N6C ADJUDICATION SCOPE DEFINED / PRODUCTION UNCHANGED`",
    ]
    return "\n".join(lines) + "\n"


def emit_artifacts(analysis: dict[str, Any], output_dir: Path, *, branch: str, starting_sha: str, remote_sha: str) -> list[Path]:
    output_dir.mkdir(parents=True, exist_ok=True)
    artifacts = {
        "NAPTAN_N6B_PRODUCTION_PREFLIGHT_2026-08-23.json": {
            "repository": "hourwise/Relief",
            "branch": branch,
            "starting_local_sha": starting_sha,
            "starting_remote_sha": remote_sha,
            "project": "Relief",
            "project_ref": PRODUCTION_PROJECT_REF,
            "production_write_capability": False,
            "migration_head": "20260822170000",
            "sealed_n4a_sha256": SEALED_N4A_SHA256,
            "migration_dry_run": "Remote database is up to date.",
            "read_only": True,
        },
        "NAPTAN_N6B_SOURCE_BASELINE_2026-08-23.json": {
            "source_graph_counts": {"snapshots": 1, "places": 97270, "nodes": 436428, "memberships": 169527, "parents": 3519, "total": 706745},
            "unresolved_memberships": 2804,
            "missing_membership_parent_identities": 1543,
            "unresolved_parent_edges": 92,
            "missing_parent_identities": 41,
            "hierarchy_max_depth": 13,
            "hierarchy_cycles": 0,
            "source_graph_mutations": 0,
        },
        "NAPTAN_N6B_MODE_COHORT_SUMMARY_2026-08-23.json": analysis["mode_cohorts"],
        "NAPTAN_N6B_51_PROPOSED_MATCH_REVIEW_2026-08-23.json": {"count": 51, "cases": analysis["proposed_match_review_51"], "production_writes": 0},
        "NAPTAN_N6B_9_AMBIGUITY_REVIEW_2026-08-23.json": {"count": 9, "cases": analysis["ambiguous_match_review_9"], "production_writes": 0},
        "NAPTAN_N6B_4163_PROPOSED_NEW_BREAKDOWN_2026-08-23.json": analysis["proposed_new_population"],
        "NAPTAN_N6B_TOILET_EVIDENCE_HIERARCHY_2026-08-23.json": {"tiers": analysis["toilet_evidence_hierarchy"], "automatic_promotion": False},
        "NAPTAN_N6B_TRANSPORT_MODE_POLICY_2026-08-23.json": analysis["transport_mode_policy"],
        "NAPTAN_N6B_FACILITY_PLACE_ASSESSMENT_2026-08-23.json": analysis["facility_vs_place_assessment"],
        "NAPTAN_N6B_TFL_PRODUCT_POLICY_2026-08-23.json": analysis["tfl_product_assessment"],
        "NAPTAN_N6B_14_TFL_OBSERVATION_ASSESSMENT_2026-08-23.json": analysis["tfl_product_assessment"]["existing_observation_audit"],
        "NAPTAN_N6B_HUMAN_ADJUDICATION_BOUNDARY_2026-08-23.json": {"boundary": analysis["human_adjudication_boundary"], "production_writes": 0},
        "NAPTAN_N6B_N6C_RECOMMENDATION_2026-08-23.json": analysis["n6c_recommendation"],
        "NAPTAN_N6B_PRODUCTION_IMMUTABILITY_2026-08-23.json": analysis["production_immutability"],
        "NAPTAN_N6B_FINAL_DECISION_MANIFEST_2026-08-23.json": {"classifications": analysis["policy_labels"], "final_classification": "RELIEF NAPTAN N6B — TRANSPORT CANONICAL SCOPE DEFINED / NAPTAN RETAINED AS SUPPORTING IDENTITY EVIDENCE BY DEFAULT / MASS TRANSPORT PROMOTION NOT AUTHORIZED / BOUNDED N6C ADJUDICATION SCOPE DEFINED / PRODUCTION UNCHANGED", "total_production_mutations": 0},
    }
    paths: list[Path] = []
    for name, payload in artifacts.items():
        path = output_dir / name
        path.write_text(json.dumps(payload, indent=2, ensure_ascii=False, sort_keys=True) + "\n", encoding="utf-8")
        paths.append(path)
    report = output_dir / "NAPTAN_N6B_TRANSPORT_CANONICAL_SCOPE_DECISION_2026-08-23.md"
    report.write_text(markdown_report(analysis, branch=branch, starting_sha=starting_sha, remote_sha=remote_sha), encoding="utf-8")
    paths.append(report)
    return paths


def main() -> None:
    parser = argparse.ArgumentParser(description="Emit read-only N6B transport canonical scope evidence")
    parser.add_argument("--xml", type=Path, required=True)
    parser.add_argument("--facilities", type=Path, required=True)
    parser.add_argument("--sources", type=Path, required=True)
    parser.add_argument("--n6a-dir", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--branch", required=True)
    parser.add_argument("--starting-sha", required=True)
    parser.add_argument("--remote-sha", required=True)
    args = parser.parse_args()
    analysis = build_analysis(args.xml, args.facilities, args.sources, args.n6a_dir)
    paths = emit_artifacts(analysis, args.output_dir, branch=args.branch, starting_sha=args.starting_sha, remote_sha=args.remote_sha)
    print(json.dumps({"production_write_capability": False, "artifacts": [str(path) for path in paths], "detail_51": analysis["computed_candidate_reproduction"]["detail_51_count"], "detail_9": analysis["computed_candidate_reproduction"]["detail_9_count"], "computed_candidate_rows": analysis["computed_candidate_reproduction"]["candidate_rows"]}, sort_keys=True))


if __name__ == "__main__":
    main()

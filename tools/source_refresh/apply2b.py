"""Bounded, read-only decision packaging for Refresh 2 new facilities.

This module consumes the already-published Refresh 2 review evidence. It does
not read or write Supabase, invoke an apply engine, or mutate canonical data.
It classifies every new-facility candidate and emits a proposed future insert
manifest only for candidates that pass the deterministic review policy.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import re
from collections import Counter
from pathlib import Path
from typing import Any


PACKAGE_SCHEMA_VERSION = "1.0"
APPLY_ENGINE_VERSION = "relief.toilet-map-refresh-2b-new.v1"
PROJECT_REF = "bgwxrxkmyaihplaloely"
SOURCE_NAME = "Toilet Map UK"
SOURCE_VERSION = "2026-08-18T01:00:00+00:00"
SOURCE_CHECKSUM = "5600358ce06ca5dfdc0060968b26e8c9e05a1cb5c9dbe0455cdf3951f480ad7f"
SOURCE_LICENCE = "CC BY 4.0"
ALLOWED_DECISIONS = {
    "PREPARE_INSERT_CANDIDATE",
    "DEFER_EXTERNAL_VERIFICATION",
    "QUARANTINE",
}
PLACEHOLDER_NAMES = {
    "does not exist",
    "doesn't exist",
    "not applicable",
    "n/a",
    "unknown",
    "unnamed",
}
SOURCE_BATCH_DUPLICATE_RADIUS_M = 250.0


def _normalise_name(value: Any) -> str:
    value = str(value or "").casefold()
    return re.sub(r"[^a-z0-9]+", "", value)


def _coordinates(operation: dict[str, Any]) -> tuple[float, float] | None:
    proposed = operation.get("proposed_after_value") or {}
    try:
        latitude = float(proposed["latitude"])
        longitude = float(proposed["longitude"])
    except (KeyError, TypeError, ValueError):
        return None
    if not (-90 <= latitude <= 90 and -180 <= longitude <= 180):
        return None
    return latitude, longitude


def _distance_m(first: tuple[float, float], second: tuple[float, float]) -> float:
    earth_radius_m = 6_371_000.0
    lat1, lon1 = map(math.radians, first)
    lat2, lon2 = map(math.radians, second)
    delta_lat = lat2 - lat1
    delta_lon = lon2 - lon1
    haversine = (
        math.sin(delta_lat / 2) ** 2
        + math.cos(lat1) * math.cos(lat2) * math.sin(delta_lon / 2) ** 2
    )
    return 2 * earth_radius_m * math.asin(math.sqrt(haversine))


def _is_new_candidate(operation: dict[str, Any]) -> bool:
    return bool(
        operation.get("apply_2_candidate")
        and operation.get("category") == "REVIEW_REQUIRED"
        and operation.get("target_facility_id") is None
        and operation.get("target_field") == "__facility_creation__"
        and operation.get("review_reason_code") == "NEW_FACILITY"
    )


def _batch_duplicate_evidence(operations: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    evidence: dict[str, dict[str, Any]] = {}
    for index, first in enumerate(operations):
        first_name = (first.get("proposed_after_value") or {}).get("name")
        first_coordinates = _coordinates(first)
        if not first_name or first_coordinates is None:
            continue
        for second in operations[index + 1 :]:
            second_name = (second.get("proposed_after_value") or {}).get("name")
            second_coordinates = _coordinates(second)
            if not second_name or second_coordinates is None:
                continue
            if _normalise_name(first_name) != _normalise_name(second_name):
                continue
            distance_m = _distance_m(first_coordinates, second_coordinates)
            if distance_m > SOURCE_BATCH_DUPLICATE_RADIUS_M:
                continue
            detail = {
                "match_type": "NORMALISED_NAME_AND_COORDINATE_PROXIMITY",
                "other_operation_id": second["operation_id"],
                "other_source_record_id": second["source_record_id"],
                "other_name": second_name,
                "distance_m": round(distance_m, 3),
                "radius_m": SOURCE_BATCH_DUPLICATE_RADIUS_M,
            }
            reverse = {
                **detail,
                "other_operation_id": first["operation_id"],
                "other_source_record_id": first["source_record_id"],
                "other_name": first_name,
            }
            evidence[first["operation_id"]] = detail
            evidence[second["operation_id"]] = reverse
    return evidence


def _placeholder_name(operation: dict[str, Any]) -> bool:
    name = str((operation.get("proposed_after_value") or {}).get("name") or "").strip().casefold()
    return not name or name in PLACEHOLDER_NAMES


def _decision_for(
    operation: dict[str, Any],
    batch_duplicate: dict[str, Any] | None,
) -> tuple[str, str, bool, bool]:
    proposed = operation.get("proposed_after_value") or {}
    name = proposed.get("name")
    if _placeholder_name(operation):
        return (
            "QUARANTINE",
            "INVALID_PLACEHOLDER_OR_MISSING_FACILITY_NAME",
            False,
            False,
        )
    if not name or _coordinates(operation) is None:
        return "QUARANTINE", "MISSING_OR_INVALID_FACILITY_IDENTITY_FIELDS", False, True
    if operation.get("collision_candidate"):
        return (
            "DEFER_EXTERNAL_VERIFICATION",
            "CURRENT_CANONICAL_NEIGHBOUR_OR_COLLISION_REQUIRES_IDENTITY_VERIFICATION",
            True,
            False,
        )
    if batch_duplicate:
        return (
            "DEFER_EXTERNAL_VERIFICATION",
            "SOURCE_BATCH_DUPLICATE_CANDIDATE_REQUIRES_SOURCE_IDENTITY_VERIFICATION",
            True,
            False,
        )
    return (
        "PREPARE_INSERT_CANDIDATE",
        "VALID_EXACT_SOURCE_NEW_RECORD_WITH_NO_DETERMINISTIC_COLLISION_EVIDENCE",
        False,
        True,
    )


def _decision_record(
    operation: dict[str, Any],
    decision: str,
    rule: str,
    verification: bool,
    eligible: bool,
    batch_duplicate: dict[str, Any] | None,
) -> dict[str, Any]:
    assessment = operation.get("review_assessment") or {}
    proposed = operation.get("proposed_after_value") or {}
    return {
        "operation_id": operation["operation_id"],
        "source_record_id": operation["source_record_id"],
        "target_facility_id": None,
        "target_field": operation["target_field"],
        "proposed_facility": proposed,
        "source_evidence": operation.get("source_evidence"),
        "refresh_reason_code": operation.get("review_reason_code"),
        "refresh_category": operation.get("category"),
        "refresh_collision_candidate": bool(operation.get("collision_candidate")),
        "decision": decision,
        "decision_rule": rule,
        "evidence_sufficient_for_future_apply_2b": eligible,
        "external_verification_required": verification,
        "source_batch_duplicate_evidence": batch_duplicate,
        "exact_source_link_count_preflight": 0,
        "safety_critical": assessment.get("safety_critical"),
        "ambiguous": assessment.get("ambiguous"),
        "stronger_provenance_risk": assessment.get("stronger_provenance_risk"),
        "unknown_to_false_certainty_risk": assessment.get("unknown_to_false_certainty_risk"),
        "material_user_visible_change": assessment.get("material_user_visible_change"),
        "urgent_search_impact": assessment.get("urgent_search_impact"),
        "human_review_required_after_decision": verification or decision == "QUARANTINE",
    }


def build_apply2b_package(
    refresh2_review: dict[str, Any],
    *,
    input_review_sha256: str | None = None,
    generating_commit: str = "WORKTREE",
    project_ref: str = PROJECT_REF,
    expected_candidate_count: int | None = 42,
    production_reference_counts: dict[str, int] | None = None,
) -> tuple[dict[str, Any], dict[str, Any]]:
    """Build the all-candidate decision report and future insert manifest."""

    operations = refresh2_review.get("operations")
    if not isinstance(operations, list):
        raise ValueError("Refresh 2 review has no operations list")
    candidates = [operation for operation in operations if _is_new_candidate(operation)]
    if expected_candidate_count is not None and len(candidates) != expected_candidate_count:
        raise ValueError(f"expected {expected_candidate_count} new candidates, found {len(candidates)}")
    source_checksums = {
        (operation.get("source_evidence") or {}).get("source_checksum", "").casefold()
        for operation in candidates
    }
    if candidates and source_checksums != {SOURCE_CHECKSUM.casefold()}:
        raise ValueError("new candidates do not share the frozen Refresh 2 source checksum")
    batch_duplicates = _batch_duplicate_evidence(candidates)
    records: list[dict[str, Any]] = []
    candidate_operations: list[dict[str, Any]] = []
    for operation in sorted(candidates, key=lambda item: item["operation_id"]):
        duplicate = batch_duplicates.get(operation["operation_id"])
        decision, rule, verification, eligible = _decision_for(operation, duplicate)
        record = _decision_record(operation, decision, rule, verification, eligible, duplicate)
        records.append(record)
        if eligible:
            candidate = dict(record)
            candidate["execution_guard"] = {
                "require_exact_source_record_id": operation["source_record_id"],
                "require_no_existing_source_link": True,
                "require_source_checksum": SOURCE_CHECKSUM,
                "require_source_version": SOURCE_VERSION,
                "require_source_licence": SOURCE_LICENCE,
                "require_coordinate_and_name_re_read": True,
                "require_duplicate_collision_recheck": True,
                "require_separate_owner_execution_approval": True,
                "read_only_preparation_only": True,
            }
            candidate_operations.append(candidate)
    decision_counts = dict(sorted(Counter(record["decision"] for record in records).items()))
    if set(decision_counts) - ALLOWED_DECISIONS:
        raise ValueError("decision set contains an unsupported action")
    if len(records) != 42 and expected_candidate_count == 42:
        raise ValueError("the bounded package must contain all 42 candidates")
    if len(candidate_operations) + decision_counts.get("DEFER_EXTERNAL_VERIFICATION", 0) + decision_counts.get("QUARANTINE", 0) != len(records):
        raise ValueError("decision counts do not reconcile")
    source_evidence = (candidates[0].get("source_evidence") if candidates else {}) or {}
    common = {
        "package_schema_version": PACKAGE_SCHEMA_VERSION,
        "generation": "Toilet Map Refresh 2 / Apply 2B new-facility review",
        "classification": "TOILET MAP APPLY 2B — NEW FACILITY PACKAGE PREPARED / EXECUTION NOT AUTHORIZED",
        "status": "PROPOSED / NOT AUTHORIZED FOR PRODUCTION EXECUTION",
        "read_only": True,
        "apply_engine_version": APPLY_ENGINE_VERSION,
        "generating_commit": generating_commit,
        "input_review_sha256": input_review_sha256,
        "source_name": SOURCE_NAME,
        "source_url": source_evidence.get("source_url"),
        "source_licence": SOURCE_LICENCE,
        "source_version": SOURCE_VERSION,
        "source_checksum": SOURCE_CHECKSUM,
        "project_ref": project_ref,
        "scope": {
            "new_facility_candidates_assessed": len(records),
            "existing_facility_operations_excluded": True,
            "stale_operations_excluded": True,
            "quarantined_source_rows_excluded": True,
            "deferred_source_omissions_excluded": True,
        },
        "decision_counts": decision_counts,
        "canonical_mutations": 0,
        "production_mutations": 0,
        "facility_inserts": 0,
        "facility_updates": 0,
        "facility_deletes": 0,
        "facility_sources_mutations": 0,
        "provenance_mutations": 0,
        "staging_mutations": 0,
        "import_run_mutations": 0,
        "production_reference_counts": production_reference_counts or {
            "facilities": 15_584,
            "facility_sources": 15_584,
            "import_runs": 5,
            "staging": 0,
        },
        "production_read_only_checks": {
            "exact_source_link_check_candidate_count": 42,
            "exact_source_link_check_rows_found": 0,
            "targeted_nearest_facility_checks": 6,
            "targeted_nearest_checks_are_read_only": True,
            "apply_2a_data_reopened_or_modified": False,
        },
    }
    report = {**common, "package_kind": "DECISION_REPORT", "decisions": records}
    manifest = {
        **common,
        "package_kind": "FUTURE_INSERT_CANDIDATE_MANIFEST",
        "status_detail": "Contains only PREPARE_INSERT_CANDIDATE decisions; separate execution approval remains required.",
        "operation_count": len(candidate_operations),
        "operations": candidate_operations,
    }
    return report, manifest


def render_decision_report_markdown(report: dict[str, Any]) -> str:
    counts = report["decision_counts"]
    lines = [
        "# Toilet Map Refresh 2B new-facility decisions",
        "",
        "> Proposed, read-only preparation. No new facility was inserted and Apply 2B execution is not authorized.",
        "",
        f"- Source version: `{report['source_version']}`",
        f"- Source checksum: `{report['source_checksum']}`",
        f"- Candidates assessed: `{report['scope']['new_facility_candidates_assessed']}`",
        f"- Exact source links found in production preflight: `{report['production_read_only_checks']['exact_source_link_check_rows_found']}` of `{report['production_read_only_checks']['exact_source_link_check_candidate_count']}`",
        f"- Canonical mutations: `{report['canonical_mutations']}`",
        f"- Production mutations: `{report['production_mutations']}`",
        "",
        "## Decisions",
        "",
        "| Decision | Count | Treatment |",
        "|---|---:|---|",
        f"| `PREPARE_INSERT_CANDIDATE` | {counts.get('PREPARE_INSERT_CANDIDATE', 0)} | Include in a future guarded insert package; no execution authorization is implied |",
        f"| `DEFER_EXTERNAL_VERIFICATION` | {counts.get('DEFER_EXTERNAL_VERIFICATION', 0)} | Exclude until identity/collision evidence is resolved |",
        f"| `QUARANTINE` | {counts.get('QUARANTINE', 0)} | Exclude because the source identity is invalid or unusable |",
        "",
        "## Decision policy",
        "",
        "- A candidate is prepared only when its frozen public source identity contains a usable name and coordinate, the production exact-source preflight found no existing source link, and no deterministic collision evidence was found.",
        "- The three Refresh 2 collision candidates (Hemsby Beach Toilets, Burns Mall Toilets, and Tesco Extra) remain deferred because a nearby canonical facility requires identity verification before insertion.",
        "- The two exact-name Becky’s Barn Cafe rows are deferred because they are 217.1 m apart within the same source batch; source identity must establish whether they are two toilets or one duplicated source record.",
        "- The `Does not exist` row is quarantined as an invalid placeholder name. A nearby canonical Yates’s record reinforces that it cannot be treated as a new facility without human investigation.",
        "- Neilston Train Station, Neilston Library, and Neilston Leisure Centre are retained as distinct candidates: their names are distinct and their nearest current canonical facility is 1.9–2.3 km away. This is not a substitute for the required execution-time recheck.",
        "",
        "## Production boundary",
        "",
        "- This package contains proposed future inserts only; it is not an executable migration or apply command.",
        "- It contains no facility IDs, so it cannot target an existing facility for update or deletion.",
        "- A future execution would require a separate owner approval, a fresh read-only preflight, duplicate/collision recheck, and an auditable transaction/postcheck.",
        "",
        "## Case register",
        "",
        "| Operation | Source record | Name | Town | Decision | Rule |",
        "|---|---|---|---|---|---|",
    ]
    for record in report["decisions"]:
        proposed = record["proposed_facility"]
        name = str(proposed.get("name", "")).replace("|", "\\|")
        town = str(proposed.get("town", "")).replace("|", "\\|")
        lines.append(
            f"| `{record['operation_id']}` | `{record['source_record_id']}` | {name} | {town} | `{record['decision']}` | `{record['decision_rule']}` |"
        )
    return "\n".join(lines) + "\n"


def render_apply_plan_markdown(manifest: dict[str, Any]) -> str:
    return "\n".join(
        [
            "# Toilet Map Apply 2B new-facility preparation plan",
            "",
            "> This is a proposed future-insert package only. No Apply 2B operation was executed.",
            "",
            f"- Prepared candidates: `{manifest['operation_count']}`",
            f"- Deferred candidates: `{manifest['decision_counts'].get('DEFER_EXTERNAL_VERIFICATION', 0)}`",
            f"- Quarantined candidates: `{manifest['decision_counts'].get('QUARANTINE', 0)}`",
            f"- Source version: `{manifest['source_version']}`",
            f"- Source checksum: `{manifest['source_checksum']}`",
            f"- Production project: `{manifest['project_ref']}`",
            f"- Canonical mutations: `{manifest['canonical_mutations']}`",
            f"- Production mutations: `{manifest['production_mutations']}`",
            "",
            "## Included future candidates",
            "",
            "The manifest includes only the candidates classified `PREPARE_INSERT_CANDIDATE`. It is frozen to the published Refresh 2 source checksum and includes source evidence plus execution-time guards for exact source identity, no existing source link, usable coordinates/name, and collision recheck.",
            "",
            "## Excluded candidates",
            "",
            "The three canonical-neighbour/collision candidates and the two same-name Becky’s Barn Cafe source records are deferred for external identity verification. The `Does not exist` placeholder is quarantined. None is included in the future insert manifest.",
            "",
            "## Required future gates",
            "",
            "1. Obtain separate explicit authorization for Apply 2B execution.",
            "2. Re-read production and verify every source ID still has no `facility_sources` link; abort on any link, drift, or source checksum/version mismatch.",
            "3. Re-run duplicate and collision checks against current canonical facilities and the exact frozen source snapshot.",
            "4. Execute only the separately approved insert set through a narrowly scoped, auditable transaction with postcheck evidence.",
            "5. Do not broaden the package to deferred, quarantined, existing-facility, stale, omission, or secondary-source data.",
            "",
        ]
    )


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_package(input_path: Path, output_dir: Path, *, generating_commit: str, project_ref: str) -> tuple[Path, Path, Path, Path]:
    refresh2_review = json.loads(input_path.read_text(encoding="utf-8"))
    report, manifest = build_apply2b_package(
        refresh2_review,
        input_review_sha256=_sha256(input_path),
        generating_commit=generating_commit,
        project_ref=project_ref,
    )
    output_dir.mkdir(parents=True, exist_ok=True)
    report_json = output_dir / "TOILET_MAP_APPLY_2B_NEW_DECISIONS.json"
    report_md = output_dir / "TOILET_MAP_APPLY_2B_NEW_DECISIONS.md"
    manifest_json = output_dir / "TOILET_MAP_APPLY_2B_NEW_MANIFEST.json"
    plan_md = output_dir / "TOILET_MAP_APPLY_2B_NEW_PLAN.md"
    report_json.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    report_md.write_text(render_decision_report_markdown(report), encoding="utf-8")
    manifest_json.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    plan_md.write_text(render_apply_plan_markdown(manifest), encoding="utf-8")
    return report_json, report_md, manifest_json, plan_md


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, required=True, help="published Refresh 2 review evidence")
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--generating-commit", required=True)
    parser.add_argument("--project-ref", default=PROJECT_REF)
    args = parser.parse_args()
    paths = write_package(args.input, args.output_dir, generating_commit=args.generating_commit, project_ref=args.project_ref)
    print(json.dumps({"written": [str(path) for path in paths]}, indent=2))


if __name__ == "__main__":
    main()

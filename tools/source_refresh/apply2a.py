"""Bounded, read-only decision packaging for Refresh 2 existing facilities.

This module consumes the already-published Refresh 2 Apply 2 manifest. It does
not read or write Supabase, invoke an apply engine, or mutate canonical data.
Its only output is a decision record for the existing-facility subset and a
proposed future execution manifest containing decisions that passed policy.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from collections import Counter
from pathlib import Path
from typing import Any


PACKAGE_SCHEMA_VERSION = "1.0"
APPLY_ENGINE_VERSION = "relief.toilet-map-refresh-2a-existing.v1"
PROJECT_REF = "bgwxrxkmyaihplaloely"
ALLOWED_DECISIONS = {
    "APPLY_SOURCE",
    "KEEP_CANONICAL",
    "DEFER_EXTERNAL_VERIFICATION",
    "PROTECTED",
    "QUARANTINE",
}


def _is_existing_candidate(operation: dict[str, Any]) -> bool:
    """Return whether an operation is in the bounded 2A existing scope."""

    return bool(
        operation.get("apply_2_candidate")
        and operation.get("target_facility_id")
        and operation.get("target_field")
        and not str(operation["target_field"]).startswith("__")
    )


def _decision_for(operation: dict[str, Any]) -> tuple[str, str, bool, bool]:
    """Apply the conservative, deterministic 2A decision policy."""

    reason = operation.get("review_reason_code")
    field = operation.get("target_field")

    if reason == "SAFE_BOOLEAN_ENRICHMENT":
        if operation.get("category") != "SAFE_CANDIDATE":
            raise ValueError("safe boolean operation has an unexpected category")
        if operation.get("before_value") is not None:
            raise ValueError("safe boolean operation must enrich an unknown value")
        if not isinstance(operation.get("proposed_after_value"), bool):
            raise ValueError("safe boolean operation must have an explicit boolean")
        if not operation.get("source_record_id") or operation.get("current_provenance"):
            raise ValueError("safe boolean operation lacks exact identity or is protected")
        return "APPLY_SOURCE", "EXACT_SOURCE_ID_EXPLICIT_BOOLEAN_CANONICAL_UNKNOWN", False, True

    if reason == "SOURCE_CANONICAL_CONFLICT":
        if operation.get("before_value") is None:
            raise ValueError("source conflict must have an accepted canonical value")
        if operation.get("current_provenance"):
            return "PROTECTED", "CURRENT_CANONICAL_HAS_EXISTING_SOURCE_PROVENANCE", False, False
        return "KEEP_CANONICAL", "CONFLICT_WITH_CURRENT_CANONICAL_NO_INDEPENDENT_CORROBORATION", False, False

    if reason == "UNSUPPORTED_ENRICHMENT" and field == "open_hours":
        return "DEFER_EXTERNAL_VERIFICATION", "MATERIAL_OPEN_HOURS_ENRICHMENT_NEEDS_INDEPENDENT_VERIFICATION", True, False

    raise ValueError(f"unexpected in-scope operation: {operation.get('operation_id')}")


def _decision_record(operation: dict[str, Any], decision: str, rule: str, verification: bool, eligible: bool) -> dict[str, Any]:
    assessment = operation.get("review_assessment") or {}
    return {
        "operation_id": operation["operation_id"],
        "target_facility_id": operation["target_facility_id"],
        "source_record_id": operation["source_record_id"],
        "target_field": operation["target_field"],
        "before_value": operation.get("before_value"),
        "proposed_after_value": operation.get("proposed_after_value"),
        "source_evidence": operation.get("source_evidence"),
        "current_provenance": operation.get("current_provenance"),
        "refresh_reason_code": operation.get("review_reason_code"),
        "refresh_category": operation.get("category"),
        "decision": decision,
        "decision_rule": rule,
        "evidence_sufficient_for_future_apply_2a": eligible,
        "external_verification_required": verification,
        "safety_critical": assessment.get("safety_critical"),
        "ambiguous": assessment.get("ambiguous"),
        "stronger_provenance_risk": assessment.get("stronger_provenance_risk"),
        "unknown_to_false_certainty_risk": assessment.get("unknown_to_false_certainty_risk"),
        "material_user_visible_change": assessment.get("material_user_visible_change"),
        "urgent_search_impact": assessment.get("urgent_search_impact"),
        "human_review_required_after_decision": decision in {"DEFER_EXTERNAL_VERIFICATION", "QUARANTINE"},
    }


def build_apply2a_package(
    refresh2_manifest: dict[str, Any],
    *,
    input_manifest_sha256: str | None = None,
    generating_commit: str = "WORKTREE",
    project_ref: str = PROJECT_REF,
    expected_existing_count: int | None = 132,
) -> tuple[dict[str, Any], dict[str, Any]]:
    """Build the decision report and future execution manifest.

    The first return value contains all in-scope existing operations and their
    final decisions. The second contains only future APPLY_SOURCE operations.
    Neither represents an executed mutation.
    """

    operations = refresh2_manifest.get("operations")
    if not isinstance(operations, list):
        raise ValueError("Refresh 2 manifest has no operations list")

    existing = [operation for operation in operations if _is_existing_candidate(operation)]
    if expected_existing_count is not None and len(existing) != expected_existing_count:
        raise ValueError(f"expected {expected_existing_count} existing operations, found {len(existing)}")

    records: list[dict[str, Any]] = []
    candidate_operations: list[dict[str, Any]] = []
    for operation in sorted(existing, key=lambda item: item["operation_id"]):
        decision, rule, verification, eligible = _decision_for(operation)
        record = _decision_record(operation, decision, rule, verification, eligible)
        records.append(record)
        if eligible:
            candidate = dict(record)
            candidate["execution_guard"] = {
                "require_exact_source_record_id": operation["source_record_id"],
                "require_exact_target_facility_id": operation["target_facility_id"],
                "require_current_canonical_value": operation.get("before_value"),
                "require_source_checksum": operation.get("source_evidence", {}).get("source_checksum"),
                "require_re_read_only_preflight": True,
            }
            candidate_operations.append(candidate)

    decision_counts = dict(sorted(Counter(record["decision"] for record in records).items()))
    review_count = sum(record["refresh_category"] == "REVIEW_REQUIRED" for record in records)
    if expected_existing_count is not None and review_count != 110:
        raise ValueError(f"expected 110 remaining review cases, found {review_count}")
    if set(decision_counts) - ALLOWED_DECISIONS:
        raise ValueError("decision set contains an unsupported action")

    source_evidence = next((record["source_evidence"] for record in records if record.get("source_evidence")), {})
    common = {
        "package_schema_version": PACKAGE_SCHEMA_VERSION,
        "generation": "Toilet Map Refresh 2 / Apply 2A existing-facility decisions",
        "status": "PROPOSED / NOT AUTHORIZED FOR PRODUCTION EXECUTION",
        "read_only": True,
        "apply_engine_version": APPLY_ENGINE_VERSION,
        "generating_commit": generating_commit,
        "input_manifest_sha256": input_manifest_sha256,
        "source_checksum": source_evidence.get("source_checksum"),
        "source_version": source_evidence.get("source_version"),
        "project_ref": project_ref,
        "scope": {
            "existing_facility_operations": len(records),
            "remaining_review_cases": review_count,
            "new_facility_operations_excluded": True,
            "stale_operations_excluded": True,
            "quarantined_operations_excluded": True,
            "deferred_omission_operations_excluded": True,
        },
        "decision_counts": decision_counts,
        "canonical_mutations": 0,
        "production_mutations": 0,
    }

    decision_report = {**common, "package_kind": "DECISION_REPORT", "decisions": records}
    apply_manifest = {
        **common,
        "package_kind": "EXECUTION_CANDIDATE_MANIFEST",
        "status_detail": "Contains only APPLY_SOURCE decisions; separate execution approval remains required.",
        "operation_count": len(candidate_operations),
        "operations": candidate_operations,
    }
    return decision_report, apply_manifest


def render_decision_report_markdown(report: dict[str, Any]) -> str:
    counts = report["decision_counts"]
    lines = [
        "# Toilet Map Refresh 2A existing-facility decisions",
        "",
        "> Proposed, read-only preparation. Apply 2A is not authorized and was not executed.",
        "",
        f"- Source version: `{report.get('source_version')}`",
        f"- Source checksum: `{report.get('source_checksum')}`",
        f"- Existing-facility operations assessed: `{report['scope']['existing_facility_operations']}`",
        f"- Remaining review cases assessed: `{report['scope']['remaining_review_cases']}`",
        f"- Canonical mutations: `{report['canonical_mutations']}`",
        f"- Production mutations: `{report['production_mutations']}`",
        "",
        "## Decisions",
        "",
        "| Decision | Count | Treatment |",
        "|---|---:|---|",
        f"| `APPLY_SOURCE` | {counts.get('APPLY_SOURCE', 0)} | Eligible for a future guarded Apply 2A preflight |",
        f"| `KEEP_CANONICAL` | {counts.get('KEEP_CANONICAL', 0)} | Preserve the current accepted canonical value |",
        f"| `PROTECTED` | {counts.get('PROTECTED', 0)} | Preserve because current provenance is present |",
        f"| `DEFER_EXTERNAL_VERIFICATION` | {counts.get('DEFER_EXTERNAL_VERIFICATION', 0)} | Exclude until independent current-hours evidence exists |",
        f"| `QUARANTINE` | {counts.get('QUARANTINE', 0)} | No execution candidate; none in this bounded set |",
        "",
        "## Decision policy",
        "",
        "- The 22 `SAFE_BOOLEAN_ENRICHMENT` records are `APPLY_SOURCE` only because they have an exact source record ID, an explicit boolean, an unknown canonical value, and no current field provenance.",
        "- The 98 unprotected `SOURCE_CANONICAL_CONFLICT` records are `KEEP_CANONICAL`. An exact source link alone does not establish that a fresh source value should overwrite an accepted non-null canonical value.",
        "- The 2 source conflicts with existing Toilet Map provenance are `PROTECTED`; the package does not weaken or replace that provenance.",
        "- The 10 `open_hours` enrichments are `DEFER_EXTERNAL_VERIFICATION`. Hours are material and affect urgent search behaviour; the source snapshot alone is not independent current verification.",
        "",
        "## Case register",
        "",
        "| Operation | Facility | Field | Before | Proposed source value | Decision |",
        "|---|---|---|---|---|---|",
    ]
    for record in report["decisions"]:
        before = json.dumps(record.get("before_value"), ensure_ascii=False, separators=(",", ":"))
        after = json.dumps(record.get("proposed_after_value"), ensure_ascii=False, separators=(",", ":"))
        lines.append(
            f"| `{record['operation_id']}` | `{record['target_facility_id']}` | `{record['target_field']}` | `{before}` | `{after}` | `{record['decision']}` |"
        )
    return "\n".join(lines) + "\n"


def render_apply_plan_markdown(manifest: dict[str, Any]) -> str:
    return "\n".join(
        [
            "# Toilet Map Apply 2A existing-facility preparation plan",
            "",
            "> This is a proposed execution package only. No Apply 2A operation was executed.",
            "",
            f"- Candidate operations: `{manifest['operation_count']}`",
            f"- Source version: `{manifest.get('source_version')}`",
            f"- Source checksum: `{manifest.get('source_checksum')}`",
            f"- Production project: `{manifest.get('project_ref')}`",
            f"- Canonical mutations: `{manifest['canonical_mutations']}`",
            f"- Production mutations: `{manifest['production_mutations']}`",
            "",
            "## Included future candidates",
            "",
            "Only the 22 deterministic `APPLY_SOURCE` boolean enrichments are included. Each candidate has an exact target facility, exact source record, expected current canonical value, source checksum, and a required read-only preflight guard.",
            "",
            "## Excluded decisions",
            "",
            "The 98 `KEEP_CANONICAL`, 2 `PROTECTED`, and 10 `DEFER_EXTERNAL_VERIFICATION` decisions are not execution candidates. New facilities, stale candidates, quarantined rows, and deferred source omissions are outside this package and remain excluded.",
            "",
            "## Required future gates",
            "",
            "1. Obtain a separate explicit authorization for Apply 2A execution.",
            "2. Re-read production and verify every target facility, source link, canonical value, provenance value, source version, and checksum.",
            "3. Abort on any target drift, provenance drift, source drift, duplicate/collision signal, or failed guard.",
            "4. Execute only through the separately approved apply path with auditable transaction and postcheck evidence.",
            "",
        ]
    )


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_package(input_path: Path, output_dir: Path, *, generating_commit: str, project_ref: str) -> tuple[Path, Path, Path, Path]:
    refresh2_manifest = json.loads(input_path.read_text(encoding="utf-8"))
    report, manifest = build_apply2a_package(
        refresh2_manifest,
        input_manifest_sha256=_sha256(input_path),
        generating_commit=generating_commit,
        project_ref=project_ref,
    )
    output_dir.mkdir(parents=True, exist_ok=True)
    report_json = output_dir / "TOILET_MAP_APPLY_2A_EXISTING_DECISIONS.json"
    report_md = output_dir / "TOILET_MAP_APPLY_2A_EXISTING_DECISIONS.md"
    manifest_json = output_dir / "TOILET_MAP_APPLY_2A_EXISTING_MANIFEST.json"
    plan_md = output_dir / "TOILET_MAP_APPLY_2A_EXISTING_PLAN.md"
    report_json.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    report_md.write_text(render_decision_report_markdown(report), encoding="utf-8")
    manifest_json.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    plan_md.write_text(render_apply_plan_markdown(manifest), encoding="utf-8")
    return report_json, report_md, manifest_json, plan_md


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, required=True, help="published Refresh 2 Apply 2 manifest")
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--generating-commit", required=True)
    parser.add_argument("--project-ref", default=PROJECT_REF)
    args = parser.parse_args()
    paths = write_package(args.input, args.output_dir, generating_commit=args.generating_commit, project_ref=args.project_ref)
    print(json.dumps({"written": [str(path) for path in paths]}, indent=2))


if __name__ == "__main__":
    main()

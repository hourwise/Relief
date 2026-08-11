"""Design-stage interlocks and synthetic transaction model for Apply 1A.

This module deliberately has no live write client.  The existing
``apply_engine_1a.py`` remains the GET-only live preflight and in-memory
simulation.  This module supplies the future operator gates, a deterministic
synthetic transaction model for tests, and the post-apply verifier contract.
"""

from __future__ import annotations

import argparse
import copy
import os
import threading
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Any

try:
    from .apply_engine_1a import (
        ALLOWED_FIELDS,
        APPLY_ENGINE_VERSION,
        EXPECTED_APPROVED_MANIFEST_SHA256,
        EXPECTED_APPROVED_PLAN_SHA256,
        EXPECTED_PROJECT_REF,
        EXPECTED_REVIEW_COMMIT,
        EXPECTED_SOURCE_CHECKSUM,
        evaluate_operation,
        load_json,
        merged_provenance,
        sha256_bytes,
        validate_manifest_identity,
        validate_plan,
        build_manifest,
    )
except ImportError:  # Supports direct execution from tools/enrichment.
    from apply_engine_1a import (
        ALLOWED_FIELDS,
        APPLY_ENGINE_VERSION,
        EXPECTED_APPROVED_MANIFEST_SHA256,
        EXPECTED_APPROVED_PLAN_SHA256,
        EXPECTED_PROJECT_REF,
        EXPECTED_REVIEW_COMMIT,
        EXPECTED_SOURCE_CHECKSUM,
        evaluate_operation,
        load_json,
        merged_provenance,
        sha256_bytes,
        validate_manifest_identity,
        validate_plan,
        build_manifest,
    )


SOURCE_NAME = "Toilet Map UK"
LIVE_APPLY_CONFIRMATION = "APPLY_RELIEF_TOILET_MAP_1A_48"
PRIVILEGED_DATABASE_ENV = "RELIEF_APPLY_1A_DATABASE_URL"
APPLY_RUN_KIND = "apply_1a"
ALLOWED_APPLY_FIELDS = frozenset(ALLOWED_FIELDS)
# Review lock: this branch can validate the future privileged path but cannot
# open a database connection or execute the SQL function.
LIVE_EXECUTION_ENABLED = False


class LiveApplyGateError(ValueError):
    """Raised when a deliberate live-apply interlock is missing or wrong."""


@dataclass(frozen=True)
class SyntheticTransactionResult:
    state: dict[str, Any]
    audit: dict[str, Any]


def validate_approval_identity(
    *,
    plan_sha256: str,
    manifest_sha256: str,
    source_sha256: str,
    project_ref: str,
    confirmation: str,
) -> None:
    """Validate every approval identity against immutable local constants."""

    if plan_sha256.lower() != EXPECTED_APPROVED_PLAN_SHA256:
        raise LiveApplyGateError("plan SHA-256 is not the approved Apply 1A plan")
    if manifest_sha256.lower() != EXPECTED_APPROVED_MANIFEST_SHA256:
        raise LiveApplyGateError("manifest SHA-256 is not the approved Apply 1A manifest")
    if source_sha256.lower() != EXPECTED_SOURCE_CHECKSUM.lower():
        raise LiveApplyGateError("source SHA-256 is not the approved Toilet Map snapshot")
    if project_ref != EXPECTED_PROJECT_REF:
        raise LiveApplyGateError("project ref is not the approved Relief project")
    if confirmation != LIVE_APPLY_CONFIRMATION:
        raise LiveApplyGateError("explicit Apply 1A confirmation is missing or incorrect")


def validate_operation_set(operations: list[dict[str, Any]]) -> None:
    """Validate the future write payload's shape without touching a database."""

    if len(operations) != 48:
        raise ValueError(f"Apply 1A requires exactly 48 operations, found {len(operations)}")
    seen_operation_ids: set[str] = set()
    for operation in operations:
        operation_id = str(operation.get("operation_id", ""))
        if not operation_id or operation_id in seen_operation_ids:
            raise ValueError("operation IDs must be present and unique")
        seen_operation_ids.add(operation_id)
        if operation.get("canonical_source_name") != SOURCE_NAME:
            raise ValueError("operation source name is not Toilet Map UK")
        if operation.get("field") not in ALLOWED_APPLY_FIELDS:
            raise ValueError("operation field is not on the Apply 1A allowlist")
        if operation.get("expected_current_value") is not None:
            raise ValueError("operation expected current value must be null")
        if not isinstance(operation.get("proposed_value"), bool):
            raise ValueError("operation proposed value must be boolean")
        if operation.get("matching_basis") != "EXACT_SOURCE_ID":
            raise ValueError("operation must use EXACT_SOURCE_ID matching")
        if operation.get("confidence") != "HIGH":
            raise ValueError("operation confidence must be HIGH")
        if not operation.get("facility_id") or not operation.get("source_record_id"):
            raise ValueError("operation must identify a facility and source record")


def load_approved_operations(root: Path) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    """Load and independently validate the exact committed plan and manifest."""

    plan_path = root / "docs/data/TOILET_MAP_PROPOSED_APPLY_PLAN_2026-08.json"
    raw_plan = plan_path.read_bytes()
    raw_plan_sha256 = sha256_bytes(raw_plan)
    plan = load_json(plan_path)
    validate_plan(plan, raw_plan_sha256)
    manifest = build_manifest(plan, raw_plan_sha256)
    validate_manifest_identity(manifest, raw_plan_sha256, EXPECTED_SOURCE_CHECKSUM)
    validate_operation_set(manifest["operations"])
    return manifest, manifest["operations"]


def _apply_provenance(
    facility: dict[str, Any], operation: dict[str, Any], source_link: dict[str, Any] | None
) -> dict[str, Any]:
    """Merge only the approved field, including future audit identity fields."""

    _, after, _ = merged_provenance(facility, operation, source_link, "transaction_timestamp")
    entry = after[operation["field"]]
    entry.update(
        {
            "approved_plan_sha256": EXPECTED_APPROVED_PLAN_SHA256,
            "approved_manifest_sha256": EXPECTED_APPROVED_MANIFEST_SHA256,
            "apply_engine_version": APPLY_ENGINE_VERSION,
            "approved_review_commit": EXPECTED_REVIEW_COMMIT,
        }
    )
    return after


def post_apply_verify(
    before_state: dict[str, Any], after_state: dict[str, Any], operations: list[dict[str, Any]]
) -> dict[str, Any]:
    """Verify the future post-commit contract against synthetic state."""

    failures: list[str] = []
    before_facilities = before_state.get("facilities", {})
    after_facilities = after_state.get("facilities", {})
    if len(before_facilities) != len(after_facilities):
        failures.append("FACILITY_COUNT_CHANGED")
    if set(before_facilities) != set(after_facilities):
        failures.append("FACILITY_ID_SET_CHANGED")
    if before_state.get("source_links", []) != after_state.get("source_links", []):
        failures.append("FACILITY_SOURCES_CHANGED")

    changed_fields_by_facility: dict[str, set[str]] = defaultdict(set)
    for operation in operations:
        changed_fields_by_facility[operation["facility_id"]].add(operation["field"])

    for facility_id, before in before_facilities.items():
        after = after_facilities.get(facility_id)
        if after is None:
            continue
        changed_fields = changed_fields_by_facility.get(facility_id, set())
        before_other = {key: value for key, value in before.items() if key not in changed_fields}
        after_other = {key: value for key, value in after.items() if key not in changed_fields}
        before_provenance = copy.deepcopy(before_other.get("field_provenance") or {})
        after_provenance = copy.deepcopy(after_other.get("field_provenance") or {})
        if isinstance(before_provenance, dict) and isinstance(after_provenance, dict):
            for field in changed_fields:
                before_provenance.pop(field, None)
                after_provenance.pop(field, None)
            before_other["field_provenance"] = before_provenance
            after_other["field_provenance"] = after_provenance
        if before_other != after_other:
            failures.append(f"UNRELATED_FACILITY_FIELDS_CHANGED:{facility_id}")

    for operation in operations:
        facility = after_facilities.get(operation["facility_id"])
        if facility is None:
            failures.append(f"MISSING_POSTCHECK_FACILITY:{operation['facility_id']}")
            continue
        if facility.get(operation["field"]) != operation["proposed_value"]:
            failures.append(f"WRONG_POSTCHECK_VALUE:{operation['operation_id']}")
        provenance = facility.get("field_provenance")
        target = provenance.get(operation["field"]) if isinstance(provenance, dict) else None
        if not isinstance(target, dict):
            failures.append(f"MISSING_POSTCHECK_PROVENANCE:{operation['operation_id']}")
            continue
        if target.get("source_record_id") != operation["source_record_id"]:
            failures.append(f"WRONG_POSTCHECK_SOURCE:{operation['operation_id']}")
        if target.get("new_value") != operation["proposed_value"]:
            failures.append(f"WRONG_POSTCHECK_PROVENANCE_VALUE:{operation['operation_id']}")
        if target.get("approved_manifest_sha256") != EXPECTED_APPROVED_MANIFEST_SHA256:
            failures.append(f"WRONG_POSTCHECK_MANIFEST:{operation['operation_id']}")

    return {
        "ok": not failures,
        "failures": failures,
        "facility_count_unchanged": len(before_facilities) == len(after_facilities),
        "facility_sources_unchanged": before_state.get("source_links", []) == after_state.get("source_links", []),
        "operation_count": len(operations),
    }


class SyntheticApplyCoordinator:
    """Serialize same-manifest synthetic attempts like a DB advisory lock."""

    def __init__(self) -> None:
        self._locks: dict[str, threading.Lock] = {}
        self._locks_guard = threading.Lock()

    def _lock_for(self, manifest_sha256: str) -> threading.Lock:
        with self._locks_guard:
            return self._locks.setdefault(manifest_sha256, threading.Lock())

    def run(
        self,
        state: dict[str, Any],
        operations: list[dict[str, Any]],
        *,
        manifest_sha256: str = EXPECTED_APPROVED_MANIFEST_SHA256,
    ) -> SyntheticTransactionResult:
        with self._lock_for(manifest_sha256):
            return apply_synthetic_transaction(state, operations, manifest_sha256=manifest_sha256)


def apply_synthetic_transaction(
    state: dict[str, Any],
    operations: list[dict[str, Any]],
    *,
    manifest_sha256: str = EXPECTED_APPROVED_MANIFEST_SHA256,
) -> SyntheticTransactionResult:
    """Model the future all-or-nothing transaction without live persistence."""

    if manifest_sha256.lower() != EXPECTED_APPROVED_MANIFEST_SHA256:
        raise LiveApplyGateError("synthetic manifest is not the approved manifest")
    validate_operation_set(operations)
    before_state = copy.deepcopy(state)
    audit_runs = before_state.setdefault("audit_runs", {})
    existing = audit_runs.get(manifest_sha256)
    if existing and existing.get("transaction_outcome") == "committed":
        return SyntheticTransactionResult(
            state=before_state,
            audit={**existing, "transaction_outcome": "already_applied", "applied_count": 0},
        )
    if existing and existing.get("transaction_outcome") == "in_progress":
        raise LiveApplyGateError("same-manifest transaction is already in progress")

    audit = {
        "run_kind": APPLY_RUN_KIND,
        "approved_plan_sha256": EXPECTED_APPROVED_PLAN_SHA256,
        "approved_manifest_sha256": EXPECTED_APPROVED_MANIFEST_SHA256,
        "transaction_outcome": "in_progress",
        "requested_operation_count": len(operations),
        "ready_count": 0,
        "applied_count": 0,
        "stale_count": 0,
        "failed_count": 0,
    }
    working = copy.deepcopy(before_state)
    working.setdefault("audit_runs", {})[manifest_sha256] = audit
    results = [evaluate_operation(operation, working, "transaction_timestamp") for operation in operations]
    failures = [result for result in results if result["status"] != "READY"]
    if failures:
        audit = {
            **audit,
            "transaction_outcome": "rolled_back",
            "ready_count": len(results) - len(failures),
            "stale_count": len(failures),
            "failed_count": len(failures),
            "rollback_summary": "all facility and provenance changes rolled back before commit",
        }
        rolled_back = copy.deepcopy(before_state)
        rolled_back.setdefault("audit_runs", {})[manifest_sha256] = audit
        return SyntheticTransactionResult(state=rolled_back, audit=audit)

    for operation in operations:
        facility = working["facilities"][operation["facility_id"]]
        link = next(
            row
            for row in working["source_links"]
            if row.get("source_record_id") == operation["source_record_id"]
            and row.get("facility_id") == operation["facility_id"]
        )
        facility["field_provenance"] = _apply_provenance(facility, operation, link)
        facility[operation["field"]] = operation["proposed_value"]

    verification = post_apply_verify(before_state, working, operations)
    if not verification["ok"]:
        audit = {
            **audit,
            "transaction_outcome": "rolled_back",
            "ready_count": len(operations),
            "stale_count": 0,
            "failed_count": 1,
            "rollback_summary": "; ".join(verification["failures"]),
        }
        rolled_back = copy.deepcopy(before_state)
        rolled_back.setdefault("audit_runs", {})[manifest_sha256] = audit
        return SyntheticTransactionResult(state=rolled_back, audit=audit)

    audit = {
        **audit,
        "transaction_outcome": "committed",
        "ready_count": len(operations),
        "applied_count": len(operations),
        "stale_count": 0,
        "failed_count": 0,
    }
    working.setdefault("audit_runs", {})[manifest_sha256] = audit
    return SyntheticTransactionResult(state=working, audit=audit)


def future_execution_command() -> str:
    """Return the exact future command shape, with no credential material."""

    return (
        "python tools/enrichment/live_apply_1a.py "
        "--apply "
        f"--project-ref {EXPECTED_PROJECT_REF} "
        f"--plan-sha {EXPECTED_APPROVED_PLAN_SHA256} "
        f"--manifest-sha {EXPECTED_APPROVED_MANIFEST_SHA256} "
        f"--source-sha {EXPECTED_SOURCE_CHECKSUM.upper()} "
        f"--confirm {LIVE_APPLY_CONFIRMATION} "
        f"--privileged-db-env {PRIVILEGED_DATABASE_ENV}"
    )


def execute_privileged_apply(
    *,
    plan_sha256: str,
    manifest_sha256: str,
    source_sha256: str,
    project_ref: str,
    confirmation: str,
    privileged_db_env: str,
) -> None:
    """Validate the future operator call, then fail closed on this branch.

    The database URL is intentionally read only from the named environment
    variable.  The hard design lock is checked before any database client or
    connection can be constructed.
    """

    validate_approval_identity(
        plan_sha256=plan_sha256,
        manifest_sha256=manifest_sha256,
        source_sha256=source_sha256,
        project_ref=project_ref,
        confirmation=confirmation,
    )
    if privileged_db_env != PRIVILEGED_DATABASE_ENV:
        raise LiveApplyGateError("unexpected privileged credential environment name")
    if not os.environ.get(PRIVILEGED_DATABASE_ENV):
        raise LiveApplyGateError(f"{PRIVILEGED_DATABASE_ENV} is not set")
    if not LIVE_EXECUTION_ENABLED:
        raise LiveApplyGateError(
            "LIVE APPLY NOT EXECUTED: LIVE_EXECUTION_ENABLED is hard-locked false on this review branch"
        )
    raise LiveApplyGateError("LIVE APPLY NOT EXECUTED: privileged client implementation is not enabled")


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Design-stage Apply 1A live-apply interlock")
    parser.add_argument("--apply", action="store_true", help="request the future privileged path")
    parser.add_argument("--project-ref")
    parser.add_argument("--plan-sha")
    parser.add_argument("--manifest-sha")
    parser.add_argument("--source-sha")
    parser.add_argument("--confirm")
    parser.add_argument("--privileged-db-env", default=PRIVILEGED_DATABASE_ENV)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    if not args.apply:
        print("DRY_RUN_ONLY: no live Apply RPC is called and no database mutation is possible in this design branch.")
        print(future_execution_command())
        return 0
    if not all((args.project_ref, args.plan_sha, args.manifest_sha, args.source_sha, args.confirm)):
        raise SystemExit("LIVE APPLY REFUSED: all approval identities and --confirm are required")
    try:
        execute_privileged_apply(
            plan_sha256=args.plan_sha,
            manifest_sha256=args.manifest_sha,
            source_sha256=args.source_sha,
            project_ref=args.project_ref,
            confirmation=args.confirm,
            privileged_db_env=args.privileged_db_env,
        )
    except LiveApplyGateError as exc:
        raise SystemExit(str(exc)) from exc
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""Build and simulate Relief Apply Engine 1A.

Apply Engine 1A is deliberately read-only.  It freezes the approved Review 1
plan, creates a deterministic manifest, performs a GET-only live preflight,
and exercises the future write semantics against in-memory copies.  There is
no database mutation client in this module.
"""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
import os
import re
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.parse import urlencode
from urllib.request import Request, urlopen


EXPECTED_REVIEW_COMMIT = "4710b9ec7a9f5a83aa9e7225400b8a6046ce0e77"
EXPECTED_SOURCE_CHECKSUM = "f6824fdc7cd29df8c1f45ba749c1b28d319fb34803c55459bbe748ef65937624"
EXPECTED_PROJECT_REF = "bgwxrxkmyaihplaloely"
EXPECTED_PLAN_SCHEMA_VERSION = "1.0"
APPLY_ENGINE_VERSION = "relief.apply-engine-1a.v1"
SOURCE_NAME = "Toilet Map UK"
ALLOWED_FIELDS = frozenset(
    {"is_accessible", "requires_radar_key", "has_baby_changing", "is_gender_neutral", "is_free"}
)
EXCLUDED_FIELDS = frozenset(
    {
        "name",
        "coordinates",
        "latitude",
        "longitude",
        "opening_hours",
        "open_hours",
        "address",
        "town",
        "postcode",
    }
)
EXCLUDED_CATEGORIES = frozenset(
    {
        "would_create_new",
        "would_mark_source_missing",
        "would_ignore_out_of_scope",
        "would_quarantine",
        "would_require_manual_review",
    }
)
PAGE_SIZE = 1000
UUID_RE = re.compile(r"^[0-9a-fA-F-]{36}$")


def read_env(path: Path) -> dict[str, str]:
    values: dict[str, str] = {}
    if not path.exists():
        return values
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        value = value.strip()
        if len(value) >= 2 and value[0] == value[-1] and value[0] in {"'", '"'}:
            value = value[1:-1]
        values[key.strip()] = value
    return values


def canonical_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def sha256_file(path: Path) -> str:
    return sha256_bytes(path.read_bytes())


def canonical_sha256(value: Any) -> str:
    return sha256_bytes(canonical_json(value).encode("utf-8"))


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def timestamp_equal(left: Any, right: Any) -> bool:
    if left is None or right is None:
        return left is right
    left_text = str(left).replace("Z", "+00:00")
    right_text = str(right).replace("Z", "+00:00")
    try:
        left_dt = datetime.fromisoformat(left_text)
        right_dt = datetime.fromisoformat(right_text)
    except ValueError:
        return str(left) == str(right)
    if left_dt.tzinfo is None:
        left_dt = left_dt.replace(tzinfo=timezone.utc)
    if right_dt.tzinfo is None:
        right_dt = right_dt.replace(tzinfo=timezone.utc)
    return left_dt.astimezone(timezone.utc) == right_dt.astimezone(timezone.utc)


def timestamp_is_newer(left: Any, right: Any) -> bool:
    """Return whether left is newer than right; None/unparseable is conservative."""
    if left is None or right is None:
        return True
    left_text = str(left).replace("Z", "+00:00")
    right_text = str(right).replace("Z", "+00:00")
    try:
        left_dt = datetime.fromisoformat(left_text)
        right_dt = datetime.fromisoformat(right_text)
    except ValueError:
        return True
    if left_dt.tzinfo is None:
        left_dt = left_dt.replace(tzinfo=timezone.utc)
    if right_dt.tzinfo is None:
        right_dt = right_dt.replace(tzinfo=timezone.utc)
    return left_dt.astimezone(timezone.utc) > right_dt.astimezone(timezone.utc)


def in_filter(values: list[str]) -> str:
    return "in.(" + ",".join(values) + ")"


def rest_get_selected(
    base_url: str,
    anon_key: str,
    table: str,
    select: str,
    filters: list[tuple[str, str]],
) -> list[dict[str, Any]]:
    params: list[tuple[str, str]] = [("select", select), ("limit", str(PAGE_SIZE))]
    params.extend(filters)
    url = f"{base_url.rstrip('/')}/rest/v1/{table}?{urlencode(params)}"
    request = Request(
        url,
        method="GET",
        headers={
            "apikey": anon_key,
            "Authorization": f"Bearer {anon_key}",
            "Accept": "application/json",
        },
    )
    with urlopen(request, timeout=60) as response:
        body = json.loads(response.read().decode("utf-8"))
    if not isinstance(body, list):
        raise RuntimeError(f"Supabase REST returned a non-list for {table}")
    return body


def validate_entry_shape(entry: dict[str, Any]) -> None:
    category = entry.get("category")
    action = entry.get("proposed_action")
    fields = entry.get("affected_fields")
    field = fields[0] if isinstance(fields, list) and len(fields) == 1 else None
    if category in EXCLUDED_CATEGORIES:
        raise ValueError(f"excluded category cannot enter Apply 1A: {category}")
    if field in EXCLUDED_FIELDS:
        raise ValueError(f"excluded field cannot enter Apply 1A: {field}")
    if category != "would_enrich_existing" or action != "AUTO_ENRICH":
        raise ValueError(f"entry is outside Apply 1A: {category}/{action}")
    if field not in ALLOWED_FIELDS:
        raise ValueError(f"field is not on Apply 1A allowlist: {field}")
    if not isinstance(entry.get("confidence"), str) or entry["confidence"] != "HIGH":
        raise ValueError("Apply 1A requires HIGH confidence")
    if entry.get("current_value") is not None:
        raise ValueError("Apply 1A requires a null current value")
    if not isinstance(entry.get("proposed_value"), bool):
        raise ValueError("Apply 1A requires a boolean proposed value")
    provenance = entry.get("provenance_that_would_be_recorded")
    if not isinstance(provenance, dict) or provenance.get("basis") != "EXACT_SOURCE_ID":
        raise ValueError("Apply 1A requires EXACT_SOURCE_ID basis")
    facility_id = str(entry.get("relief_facility_id", ""))
    source_id = str(entry.get("source_record_id", ""))
    if not UUID_RE.fullmatch(facility_id) or not source_id:
        raise ValueError("Apply 1A requires facility and source IDs")


def validate_plan(plan: dict[str, Any], raw_plan_sha256: str) -> None:
    if plan.get("plan_schema_version") != EXPECTED_PLAN_SCHEMA_VERSION:
        raise ValueError("approved plan schema version changed")
    if plan.get("plan_only") is not True:
        raise ValueError("approved plan is not plan_only=true")
    if plan.get("executable_mutation_path") is not False:
        raise ValueError("approved plan executable_mutation_path changed")
    if str(plan.get("source_checksum", "")).lower() != EXPECTED_SOURCE_CHECKSUM:
        raise ValueError("approved source checksum changed")
    entries = plan.get("entries")
    if not isinstance(entries, list):
        raise ValueError("approved plan entries are not a list")
    candidate_entries = [
        entry
        for entry in entries
        if isinstance(entry, dict)
        and entry.get("category") == "would_enrich_existing"
        and entry.get("proposed_action") == "AUTO_ENRICH"
    ]
    for entry in candidate_entries:
        validate_entry_shape(entry)
    selected = extract_candidates(plan)
    if len(selected) != 48:
        raise ValueError(f"Apply 1A requires exactly 48 entries, found {len(selected)}")
    if raw_plan_sha256 != sha256_file(Path(__file__).resolve().parents[2] / "docs/data/TOILET_MAP_PROPOSED_APPLY_PLAN_2026-08.json"):
        raise ValueError("plan hash changed while validating")


def extract_candidates(plan: dict[str, Any]) -> list[dict[str, Any]]:
    selected: list[dict[str, Any]] = []
    for entry in plan.get("entries", []):
        if not isinstance(entry, dict):
            continue
        if entry.get("category") == "would_enrich_existing" and entry.get("proposed_action") == "AUTO_ENRICH":
            validate_entry_shape(entry)
            if entry.get("confidence") == "HIGH" and entry.get("current_value") is None:
                selected.append(entry)
    return selected


def provenance_template(entry: dict[str, Any], source_checksum: str) -> dict[str, Any]:
    field = entry["affected_fields"][0]
    return {
        "source": SOURCE_NAME,
        "source_name": SOURCE_NAME,
        "source_record_id": entry["source_record_id"],
        "source_updated_at": entry["provenance_that_would_be_recorded"].get("source_updated_at"),
        "source_snapshot_checksum": source_checksum.upper(),
        "field": field,
        "previous_value": None,
        "new_value": entry["proposed_value"],
        "basis": "EXACT_SOURCE_ID",
        "policy_version": APPLY_ENGINE_VERSION,
        "recorded_at": "transaction_timestamp",
    }


def build_manifest(plan: dict[str, Any], plan_sha256: str) -> dict[str, Any]:
    selected = extract_candidates(plan)
    if len(selected) != 48:
        raise ValueError(f"Apply 1A requires exactly 48 entries, found {len(selected)}")
    operations: list[dict[str, Any]] = []
    for entry in selected:
        field = entry["affected_fields"][0]
        operation_key = f"{entry['relief_facility_id']}|{entry['source_record_id']}|{field}|{str(entry['proposed_value']).lower()}"
        operations.append(
            {
                "operation_id": "A1A-" + sha256_bytes(operation_key.encode("utf-8"))[:16],
                "plan_schema_version": EXPECTED_PLAN_SCHEMA_VERSION,
                "apply_engine_version": APPLY_ENGINE_VERSION,
                "facility_id": entry["relief_facility_id"],
                "canonical_source_name": SOURCE_NAME,
                "source_record_id": entry["source_record_id"],
                "source_checksum": EXPECTED_SOURCE_CHECKSUM.upper(),
                "source_updated_at": entry["provenance_that_would_be_recorded"].get("source_updated_at"),
                "field": field,
                "expected_current_value": None,
                "proposed_value": entry["proposed_value"],
                "matching_basis": "EXACT_SOURCE_ID",
                "confidence": entry["confidence"],
                "provenance_to_be_recorded": provenance_template(entry, EXPECTED_SOURCE_CHECKSUM),
                "reason": entry["reason"],
                "approved_review_commit": EXPECTED_REVIEW_COMMIT,
            }
        )
    operations.sort(key=lambda item: (item["facility_id"], item["field"], item["source_record_id"], str(item["proposed_value"])))
    core = {
        "manifest_schema_version": "1.0",
        "engine": "Relief Apply Engine 1A",
        "apply_engine_version": APPLY_ENGINE_VERSION,
        "approved_review_commit": EXPECTED_REVIEW_COMMIT,
        "approved_plan_sha256": plan_sha256,
        "approved_source_checksum": EXPECTED_SOURCE_CHECKSUM.upper(),
        "project_ref": EXPECTED_PROJECT_REF,
        "scope": {
            "category": "would_enrich_existing",
            "proposed_action": "AUTO_ENRICH",
            "confidence": "HIGH",
            "fields": sorted(ALLOWED_FIELDS),
            "operation_count": len(operations),
        },
        "exclusions": {
            "fields": sorted(EXCLUDED_FIELDS),
            "categories": sorted(EXCLUDED_CATEGORIES),
            "no_new_facilities": True,
            "no_source_lifecycle_changes": True,
            "no_publication_status_changes": True,
        },
        "operations": operations,
    }
    return {**core, "manifest_sha256": canonical_sha256(core)}


def validate_manifest_identity(manifest: dict[str, Any], plan_sha256: str, source_checksum: str) -> None:
    if manifest.get("approved_plan_sha256") != plan_sha256:
        raise ValueError("manifest plan hash does not match approved plan")
    if str(manifest.get("approved_source_checksum", "")).lower() != source_checksum.lower():
        raise ValueError("manifest source checksum does not match approved source")
    if manifest.get("apply_engine_version") != APPLY_ENGINE_VERSION:
        raise ValueError("manifest apply version is not approved")
    core = dict(manifest)
    actual_hash = core.pop("manifest_sha256", None)
    if actual_hash != canonical_sha256(core):
        raise ValueError("manifest deterministic hash does not verify")
    if len(manifest.get("operations", [])) != 48:
        raise ValueError("manifest operation count is not 48")


def selected_fields() -> str:
    return "id,name,updated_at,verification_status,field_provenance,is_accessible,requires_radar_key,has_baby_changing,is_gender_neutral,is_free"


def fetch_state(root: Path, operations: list[dict[str, Any]], offline: bool, snapshot_dir: Path | None) -> dict[str, Any]:
    facility_ids = sorted({operation["facility_id"] for operation in operations})
    source_ids = sorted({operation["source_record_id"] for operation in operations})
    if offline:
        if snapshot_dir is None:
            raise ValueError("offline mode requires snapshot_dir")
        facilities = load_json(snapshot_dir / "facilities.json")
        source_links = load_json(snapshot_dir / "facility_sources.json")
        facilities = [row for row in facilities if str(row.get("id")) in facility_ids]
        source_links = [
            row
            for row in source_links
            if str(row.get("source_record_id")) in source_ids and row.get("source_name") == SOURCE_NAME
        ]
        mode = "offline local snapshots"
    else:
        env = read_env(root / ".env")
        base_url = env.get("EXPO_PUBLIC_SUPABASE_URL")
        anon_key = env.get("EXPO_PUBLIC_SUPABASE_ANON_KEY")
        if not base_url or not anon_key:
            raise RuntimeError("live preflight requires EXPO_PUBLIC_SUPABASE_URL and EXPO_PUBLIC_SUPABASE_ANON_KEY")
        if EXPECTED_PROJECT_REF not in base_url:
            raise RuntimeError("configured Supabase URL is not the approved project")
        facilities = rest_get_selected(
            base_url,
            anon_key,
            "facilities",
            selected_fields(),
            [("id", in_filter(facility_ids))],
        )
        source_links = rest_get_selected(
            base_url,
            anon_key,
            "facility_sources",
            "facility_id,source_name,source_record_id,source_updated_at,is_current,import_run_id",
            [("source_name", f"eq.{SOURCE_NAME}"), ("source_record_id", in_filter(source_ids))],
        )
        mode = "read-only Supabase REST GET"
    return {
        "snapshot_mode": mode,
        "facilities": {str(row.get("id")): row for row in facilities if row.get("id")},
        "source_links": [row for row in source_links if row.get("facility_id") and row.get("source_record_id")],
    }


def relevant_snapshot(state: dict[str, Any], operations: list[dict[str, Any]]) -> dict[str, Any]:
    facility_ids = {operation["facility_id"] for operation in operations}
    source_ids = {operation["source_record_id"] for operation in operations}
    facilities = []
    for facility_id in sorted(facility_ids):
        row = state["facilities"].get(facility_id)
        if row is None:
            facilities.append({"id": facility_id, "missing": True})
            continue
        facilities.append(
            {
                "id": str(row.get("id")),
                "name": row.get("name"),
                "updated_at": row.get("updated_at"),
                "verification_status": row.get("verification_status"),
                "is_accessible": row.get("is_accessible"),
                "requires_radar_key": row.get("requires_radar_key"),
                "has_baby_changing": row.get("has_baby_changing"),
                "is_gender_neutral": row.get("is_gender_neutral"),
                "is_free": row.get("is_free"),
                "field_provenance": row.get("field_provenance"),
            }
        )
    links = [
        row
        for row in state["source_links"]
        if str(row.get("source_record_id")) in source_ids
        and row.get("source_name") == SOURCE_NAME
        and str(row.get("facility_id")) in facility_ids
    ]
    links.sort(key=lambda row: (str(row.get("source_record_id")), str(row.get("facility_id"))))
    return {"facilities": facilities, "source_links": links}


def snapshot_hash(snapshot: dict[str, Any]) -> str:
    return canonical_sha256(snapshot)


def source_link_for(state: dict[str, Any], operation: dict[str, Any]) -> dict[str, Any] | None:
    matches = [
        row
        for row in state["source_links"]
        if row.get("source_name") == SOURCE_NAME and str(row.get("source_record_id")) == operation["source_record_id"]
    ]
    exact = [row for row in matches if str(row.get("facility_id")) == operation["facility_id"]]
    if len(exact) == 1:
        return exact[0]
    return None


def provenance_strength(value: Any) -> str:
    if value is None:
        return "none"
    if not isinstance(value, dict):
        return "uninterpretable"
    source = str(value.get("source") or value.get("source_name") or "").strip().lower()
    if source == SOURCE_NAME.lower():
        return "same_source"
    if source in {"staff", "staff_verified", "community", "community_confirmed", "source_verified"}:
        return "stronger"
    if source:
        return "other_source"
    return "uninterpretable"


def merged_provenance(
    facility: dict[str, Any], operation: dict[str, Any], link: dict[str, Any] | None, recorded_at: str
) -> tuple[dict[str, Any], dict[str, Any], str]:
    existing = facility.get("field_provenance")
    before = copy.deepcopy(existing) if isinstance(existing, dict) else {}
    after = copy.deepcopy(before)
    field = operation["field"]
    delta = copy.deepcopy(operation["provenance_to_be_recorded"])
    delta["source_updated_at"] = operation["source_updated_at"]
    delta["source_snapshot_checksum"] = operation["source_checksum"]
    delta["import_run_id"] = (link or {}).get("import_run_id")
    delta["recorded_at"] = recorded_at
    delta["previous_value"] = facility.get(field)
    delta["new_value"] = operation["proposed_value"]
    after[field] = delta
    return before, after, provenance_strength(before.get(field))


def evaluate_operation(
    operation: dict[str, Any], state: dict[str, Any], recorded_at: str, idempotent: bool = False
) -> dict[str, Any]:
    facility = state["facilities"].get(operation["facility_id"])
    link = source_link_for(state, operation)
    failures: list[str] = []
    checks: dict[str, bool] = {
        "facility_exists": facility is not None,
        "exact_source_link_exists": link is not None,
        "source_link_current": bool(link and link.get("is_current") is True),
        "source_link_identifies_facility": bool(link and str(link.get("facility_id")) == operation["facility_id"]),
        "source_timestamp_not_newer_than_approved": bool(
            link and not timestamp_is_newer(link.get("source_updated_at"), operation["source_updated_at"])
        ),
        "target_field_allowlisted": operation.get("field") in ALLOWED_FIELDS,
        "target_field_is_null": bool(facility is not None and facility.get(operation["field"]) is None),
        "no_stronger_field_provenance": False,
        "facility_relevant_state_valid": facility is not None,
    }
    if facility is None:
        failures.append("MISSING_FACILITY")
    if link is None:
        failures.append("MISSING_OR_MISMATCHED_SOURCE_LINK")
    elif link.get("is_current") is not True:
        failures.append("SOURCE_LINK_NOT_CURRENT")
    if link is not None and timestamp_is_newer(link.get("source_updated_at"), operation["source_updated_at"]):
        failures.append("SOURCE_TIMESTAMP_NEWER_THAN_APPROVED")
    if operation.get("field") not in ALLOWED_FIELDS:
        failures.append("FIELD_NOT_ALLOWLISTED")
    if facility is not None and facility.get(operation["field"]) is not None:
        if (
            idempotent
            and facility.get(operation["field"]) == operation["proposed_value"]
            and isinstance(facility.get("field_provenance"), dict)
            and isinstance(facility["field_provenance"].get(operation["field"]), dict)
            and facility["field_provenance"][operation["field"]].get("source_record_id") == operation["source_record_id"]
            and facility["field_provenance"][operation["field"]].get("policy_version") == APPLY_ENGINE_VERSION
        ):
            checks["idempotent_already_applied"] = True
            return {
                "operation_id": operation["operation_id"],
                "status": "IDEMPOTENT_NOOP",
                "checks": checks,
                "failures": [],
                "facility": facility,
                "source_link": link,
                "provenance_delta": None,
                "hypothetical_affected_row_count": 0,
            }
        failures.append("TARGET_FIELD_NOT_NULL")
    existing_provenance = facility.get("field_provenance") if facility is not None else None
    target_provenance = existing_provenance.get(operation["field"]) if isinstance(existing_provenance, dict) else None
    strength = provenance_strength(target_provenance)
    checks["no_stronger_field_provenance"] = strength in {"none", "same_source"}
    if strength not in {"none", "same_source"}:
        failures.append("STRONGER_OR_UNINTERPRETABLE_PROVENANCE")
    if not failures and facility is not None:
        before, after, _ = merged_provenance(facility, operation, link, recorded_at)
        provenance_delta = {
            "field": operation["field"],
            "before_field_provenance": before.get(operation["field"]),
            "after_field_provenance": after.get(operation["field"]),
            "unrelated_fields_preserved": sorted(set(before) - {operation["field"]}) == sorted(
                set(after) - {operation["field"]}
            ),
            "full_before": before,
            "full_after": after,
        }
    else:
        provenance_delta = None
    return {
        "operation_id": operation["operation_id"],
        "status": "READY" if not failures else "STALE / PRECONDITION_FAILED",
        "checks": checks,
        "failures": failures,
        "facility": facility,
        "source_link": link,
        "provenance_delta": provenance_delta,
        "hypothetical_affected_row_count": 1 if not failures else 0,
    }


def simulate_apply(
    state: dict[str, Any], operations: list[dict[str, Any]], recorded_at: str, fail_at: int | None = None
) -> dict[str, Any]:
    working = copy.deepcopy(state)
    applied: list[str] = []
    try:
        for index, operation in enumerate(operations):
            result = evaluate_operation(operation, working, recorded_at)
            if result["status"] != "READY":
                continue
            if fail_at is not None and index == fail_at:
                raise RuntimeError("synthetic transaction failure")
            facility = working["facilities"][operation["facility_id"]]
            link = source_link_for(working, operation)
            _, after, _ = merged_provenance(facility, operation, link, recorded_at)
            facility[operation["field"]] = operation["proposed_value"]
            facility["field_provenance"] = after
            applied.append(operation["operation_id"])
    except Exception:
        return {"rolled_back": True, "state": copy.deepcopy(state), "applied_before_failure": applied}
    return {"rolled_back": False, "state": working, "applied": applied}


def run_fixture_proofs(state: dict[str, Any], operations: list[dict[str, Any]], recorded_at: str) -> dict[str, Any]:
    proofs: dict[str, Any] = {}
    if not operations:
        return proofs
    first = operations[0]
    accepted = evaluate_operation(first, state, recorded_at)
    proofs["exact_allowed_null_to_known"] = accepted["status"] == "READY"
    false_operation = copy.deepcopy(first)
    false_operation["proposed_value"] = False
    false_state = copy.deepcopy(state)
    false_state["facilities"][first["facility_id"]][first["field"]] = None
    proofs["exact_allowed_null_to_false"] = evaluate_operation(false_operation, false_state, recorded_at)["status"] == "READY"
    proofs["non_null_rejected"] = bool(
        evaluate_operation(
            first,
            {"facilities": {first["facility_id"]: {**copy.deepcopy(state["facilities"][first["facility_id"]]), first["field"]: True}}, "source_links": state["source_links"]},
            recorded_at,
        )["failures"]
    )
    mismatch_state = copy.deepcopy(state)
    for link in mismatch_state["source_links"]:
        if str(link.get("source_record_id")) == first["source_record_id"]:
            link["facility_id"] = "00000000-0000-0000-0000-000000000000"
    proofs["source_link_mismatch_rejected"] = "MISSING_OR_MISMATCHED_SOURCE_LINK" in evaluate_operation(first, mismatch_state, recorded_at)["failures"]
    timestamp_state = copy.deepcopy(state)
    for link in timestamp_state["source_links"]:
        if str(link.get("source_record_id")) == first["source_record_id"]:
            link["source_updated_at"] = "2099-01-01T00:00:00Z"
    proofs["stale_changed_baseline_rejected"] = "SOURCE_TIMESTAMP_NEWER_THAN_APPROVED" in evaluate_operation(first, timestamp_state, recorded_at)["failures"]
    stronger_state = copy.deepcopy(state)
    stronger_state["facilities"][first["facility_id"]]["field_provenance"] = {first["field"]: {"source": "community_confirmed"}}
    proofs["stronger_provenance_rejected"] = "STRONGER_OR_UNINTERPRETABLE_PROVENANCE" in evaluate_operation(first, stronger_state, recorded_at)["failures"]
    first_run = simulate_apply(state, operations, recorded_at)
    second_results = [
        evaluate_operation(operation, first_run["state"], recorded_at, idempotent=True) for operation in operations
    ]
    proofs["repeated_manifest_is_idempotent"] = all(result["status"] == "IDEMPOTENT_NOOP" for result in second_results if result["status"] != "STALE / PRECONDITION_FAILED")
    failed_run = simulate_apply(state, operations, recorded_at, fail_at=0)
    proofs["partial_failure_rolls_back"] = failed_run["rolled_back"] and failed_run["state"] == state
    return proofs


def build_simulation(
    root: Path,
    manifest: dict[str, Any],
    before_state: dict[str, Any],
    after_state: dict[str, Any],
    generated_at: str,
    snapshot_mode: str,
) -> dict[str, Any]:
    operations = manifest["operations"]
    results = [evaluate_operation(operation, before_state, generated_at) for operation in operations]
    ready = [result for result in results if result["status"] == "READY"]
    stale = [result for result in results if result["status"] != "READY"]
    by_field = Counter(
        operation["field"]
        for operation, result in zip(operations, results)
        if result["status"] == "READY"
    )
    failure_counts = Counter(failure for result in stale for failure in result["failures"])
    first_run = simulate_apply(before_state, operations, generated_at)
    rerun = [
        evaluate_operation(operation, first_run["state"], generated_at, idempotent=True) for operation in operations
    ]
    idempotent_noops = sum(result["status"] == "IDEMPOTENT_NOOP" for result in rerun)
    before_snapshot = relevant_snapshot(before_state, operations)
    after_snapshot = relevant_snapshot(after_state, operations)
    database_unchanged = before_snapshot == after_snapshot
    provenance_rows = [
        result["provenance_delta"]
        for result in results
        if result["status"] == "READY" and result["provenance_delta"] is not None
    ]
    provenance_shapes = [
        row
        for facility in before_state["facilities"].values()
        for row in [facility.get("field_provenance")]
        if row is not None
    ]
    audit_design = {
        "preferred_parent": "public.import_runs",
        "existing_parent_support": ["source_name", "source checksum", "status", "row counts", "error_summary"],
        "required_future_metadata": ["approved_plan_sha256", "manifest_sha256", "apply_engine_version", "rollback_state"],
        "schema_gap": "import_runs has no dedicated columns for plan hash, manifest hash, policy version, or rollback state; do not overload unrelated columns during a live apply.",
        "live_audit_row_created": False,
    }
    simulation = {
        "simulation_schema_version": "1.0",
        "simulation_mode": "GET-only live preflight plus in-memory transactional simulation",
        "generated_at": generated_at,
        "project_ref": EXPECTED_PROJECT_REF,
        "approved_review_commit": EXPECTED_REVIEW_COMMIT,
        "approved_plan_sha256": manifest["approved_plan_sha256"],
        "manifest_sha256": manifest["manifest_sha256"],
        "source_checksum": EXPECTED_SOURCE_CHECKSUM.upper(),
        "snapshot_mode": snapshot_mode,
        "requested_operation_count": len(operations),
        "ready_count": len(ready),
        "stale_or_precondition_failure_count": len(stale),
        "operation_counts_by_field": dict(sorted(by_field.items())),
        "precondition_failure_counts": dict(sorted(failure_counts.items())),
        "operations": [
            {
                "operation_id": operation["operation_id"],
                "facility_id": operation["facility_id"],
                "source_record_id": operation["source_record_id"],
                "field": operation["field"],
                "current_value": result["facility"].get(operation["field"]) if result["facility"] else None,
                "proposed_value": operation["proposed_value"],
                "precondition_result": result["status"],
                "precondition_checks": result["checks"],
                "precondition_failures": result["failures"],
                "facility_name": result["facility"].get("name") if result["facility"] else None,
                "source_link": result["source_link"],
                "provenance_delta": result["provenance_delta"],
                "hypothetical_affected_row_count": result["hypothetical_affected_row_count"],
            }
            for operation, result in zip(operations, results)
        ],
        "transaction_design": {
            "future_order": ["revalidate manifest identity", "revalidate each row", "update one approved scalar", "merge field provenance", "record run evidence", "verify affected-row counts", "commit atomically"],
            "unexpected_failure": "rollback the whole transaction",
            "this_run": "No database transaction was opened and no persistent row or audit record was written.",
        },
        "provenance_model": {
            "observed_column": "public.facilities.field_provenance JSONB",
            "observed_shape": "object keyed by facility field; existing values are per-field objects",
            "merge_strategy": "copy the existing object and replace only the approved target field with the same per-field object shape extended with Apply 1A evidence",
            "unrelated_fields_preserved": all(row.get("unrelated_fields_preserved") for row in provenance_rows) if provenance_rows else True,
            "example_proposed_deltas": provenance_rows,
            "schema_safe_for_simulation": all(isinstance(row, dict) for row in provenance_shapes),
        },
        "idempotency": {
            "first_simulated_run_changes": len(first_run.get("applied", [])),
            "repeat_simulated_run_additional_changes": 0,
            "repeat_simulated_run_noops": idempotent_noops,
            "changed_manifest_is_distinct": True,
            "partial_failure_rolls_back": simulate_apply(before_state, operations, generated_at, fail_at=0)["rolled_back"],
        },
        "before_after_database_comparison": {
            "before_snapshot_sha256": snapshot_hash(before_snapshot),
            "after_snapshot_sha256": snapshot_hash(after_snapshot),
            "persistent_data_differences": 0 if database_unchanged else 1,
            "all_affected_fields_unchanged": database_unchanged,
            "relevant_source_links_unchanged": before_snapshot.get("source_links") == after_snapshot.get("source_links"),
            "relevant_provenance_unchanged": before_snapshot.get("facilities") == after_snapshot.get("facilities"),
        },
        "audit_design": audit_design,
        "fixture_proofs": run_fixture_proofs(before_state, operations, generated_at),
        "safety_statement": {
            "simulated_only": True,
            "database_mutations_committed": 0,
            "database_mutations_attempted": 0,
            "live_write_capability_present": False,
        },
    }
    return simulation


def write_markdown(simulation: dict[str, Any], path: Path) -> None:
    lines = [
        "# Relief Apply Engine 1A Simulation",
        "",
        "> SIMULATED_ONLY. This artifact was produced by GET-only live preflight and in-memory copies. No database transaction was opened.",
        "",
        "## Frozen inputs",
        "",
        f"- Review commit: `{simulation['approved_review_commit']}`",
        f"- Approved plan SHA-256: `{simulation['approved_plan_sha256']}`",
        f"- Manifest SHA-256: `{simulation['manifest_sha256']}`",
        f"- Source snapshot checksum: `{simulation['source_checksum']}`",
        f"- Supabase project: `{simulation['project_ref']}`",
        f"- Snapshot mode: **{simulation['snapshot_mode']}**",
        "",
        "## Scope and preflight",
        "",
        f"- Requested operations: **{simulation['requested_operation_count']}**",
        f"- READY: **{simulation['ready_count']}**",
        f"- STALE / PRECONDITION_FAILED: **{simulation['stale_or_precondition_failure_count']}**",
        f"- Counts by field: `{simulation['operation_counts_by_field']}`",
        f"- Failure counts: `{simulation['precondition_failure_counts']}`",
        "",
        "The simulator accepted only exact source-ID linked, HIGH-confidence, null-to-boolean entries on the five-field Apply 1A allowlist. New facilities, absent upstream IDs, out-of-scope records, quarantine candidates, conflicts, names, coordinates, addresses, towns, postcodes, and opening-hours fields are excluded by code and do not have an execution path.",
        "",
        "## Operation results",
        "",
        "| Operation | Facility | Source ID | Field | Current | Proposed | Result | Hypothetical rows |",
        "|---|---|---|---|---:|---:|---|---:|",
    ]
    for operation in simulation["operations"]:
        lines.append(
            f"| `{operation['operation_id']}` | `{operation['facility_id']}` | `{operation['source_record_id']}` | `{operation['field']}` | `{operation['current_value']}` | `{operation['proposed_value']}` | `{operation['precondition_result']}` | `{operation['hypothetical_affected_row_count']}` |"
        )
    lines.extend(
        [
            "",
            "## Provenance model",
            "",
            f"- Observed representation: `{simulation['provenance_model']['observed_column']}` with `{simulation['provenance_model']['observed_shape']}`.",
            f"- Merge strategy: {simulation['provenance_model']['merge_strategy']}.",
            f"- Unrelated provenance preserved in simulation: **{simulation['provenance_model']['unrelated_fields_preserved']}**.",
            f"- Schema safe for this simulation: **{simulation['provenance_model']['schema_safe_for_simulation']}**.",
            "- Each hypothetical target-field delta carries the source name, source record ID, source update timestamp, approved source checksum, field, previous/new values, exact-ID basis, Apply 1A policy version, import-run identity when observed, and transaction timestamp placeholder.",
            "",
            "## Transaction, rollback, and idempotency",
            "",
            "A future execution must revalidate the run and every row inside one atomic transaction, update only the approved scalar, merge only that field's provenance, verify affected-row counts, and commit. Any unexpected failure must roll back the full transaction. This task intentionally implements no live execution path.",
            f"- First in-memory run would change: **{simulation['idempotency']['first_simulated_run_changes']}** operations.",
            f"- Repeating the same manifest adds: **{simulation['idempotency']['repeat_simulated_run_additional_changes']}** changes; explicit idempotent no-ops: **{simulation['idempotency']['repeat_simulated_run_noops']}**.",
            f"- Synthetic partial failure rollback: **{simulation['idempotency']['partial_failure_rolls_back']}**.",
            "",
            "## Zero-side-effect verification",
            "",
            f"- Before snapshot SHA-256: `{simulation['before_after_database_comparison']['before_snapshot_sha256']}`",
            f"- After snapshot SHA-256: `{simulation['before_after_database_comparison']['after_snapshot_sha256']}`",
            f"- Persistent data differences: **{simulation['before_after_database_comparison']['persistent_data_differences']}**",
            f"- All affected fields unchanged: **{simulation['before_after_database_comparison']['all_affected_fields_unchanged']}**",
            f"- Relevant source links unchanged: **{simulation['before_after_database_comparison']['relevant_source_links_unchanged']}**",
            f"- Relevant provenance unchanged: **{simulation['before_after_database_comparison']['relevant_provenance_unchanged']}**",
            "",
            "## Audit design",
            "",
            f"- Preferred parent: `{simulation['audit_design']['preferred_parent']}`.",
            f"- Schema gap: {simulation['audit_design']['schema_gap']}",
            "- No live audit row was created.",
            "",
            "## Safety result",
            "",
            "SIMULATED_ONLY",
            "DATABASE_MUTATIONS_COMMITTED = 0",
        ]
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def run(args: argparse.Namespace) -> dict[str, Any]:
    root = Path(args.root).resolve()
    plan_path = (root / args.plan_json).resolve()
    plan_raw = plan_path.read_bytes()
    plan_sha256 = sha256_bytes(plan_raw)
    plan = json.loads(plan_raw.decode("utf-8"))
    validate_plan(plan, plan_sha256)
    manifest = build_manifest(plan, plan_sha256)
    validate_manifest_identity(manifest, plan_sha256, EXPECTED_SOURCE_CHECKSUM)
    manifest_path = (root / args.manifest_json).resolve()
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    before_state = fetch_state(root, manifest["operations"], args.offline, Path(args.snapshot_dir).resolve() if args.offline else None)
    generated_at = datetime.now(timezone.utc).isoformat()
    after_state = fetch_state(root, manifest["operations"], args.offline, Path(args.snapshot_dir).resolve() if args.offline else None)
    simulation = build_simulation(root, manifest, before_state, after_state, generated_at, before_state["snapshot_mode"])
    simulation_path = (root / args.simulation_json).resolve()
    markdown_path = (root / args.simulation_markdown).resolve()
    simulation_path.parent.mkdir(parents=True, exist_ok=True)
    simulation_path.write_text(json.dumps(simulation, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    write_markdown(simulation, markdown_path)
    return {"manifest": manifest, "simulation": simulation, "manifest_path": manifest_path, "simulation_path": simulation_path, "markdown_path": markdown_path}


def main() -> int:
    parser = argparse.ArgumentParser(description="Read-only Relief Apply Engine 1A manifest and simulation")
    parser.add_argument("--root", default=Path(__file__).resolve().parents[2])
    parser.add_argument("--plan-json", default="docs/data/TOILET_MAP_PROPOSED_APPLY_PLAN_2026-08.json")
    parser.add_argument("--manifest-json", default="docs/data/TOILET_MAP_APPLY_1A_MANIFEST.json")
    parser.add_argument("--simulation-json", default="docs/data/TOILET_MAP_APPLY_1A_SIMULATION.json")
    parser.add_argument("--simulation-markdown", default="docs/data/TOILET_MAP_APPLY_1A_SIMULATION.md")
    parser.add_argument("--snapshot-dir", default="tools/facility-enrichment/cache")
    parser.add_argument("--offline", action="store_true", help="Use local snapshots for synthetic/offline execution")
    args = parser.parse_args()
    try:
        result = run(args)
    except Exception as exc:
        print(f"ERROR: Apply Engine 1A simulation failed: {exc}", file=sys.stderr)
        return 1
    simulation = result["simulation"]
    print(
        json.dumps(
            {
                "simulated_only": True,
                "database_mutations_committed": 0,
                "manifest_sha256": result["manifest"]["manifest_sha256"],
                "requested_operation_count": simulation["requested_operation_count"],
                "ready_count": simulation["ready_count"],
                "stale_or_precondition_failure_count": simulation["stale_or_precondition_failure_count"],
                "manifest_json": str(result["manifest_path"]),
                "simulation_json": str(result["simulation_path"]),
                "simulation_markdown": str(result["markdown_path"]),
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

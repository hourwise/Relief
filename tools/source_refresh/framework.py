"""Source registry, immutable snapshots, and deterministic review diffs.

This module deliberately has no Supabase client and no canonical write path.
It can fetch/read data only through a caller that supplies bytes (the existing
Toilet Map downloader remains the fetch boundary), then writes local evidence.
"""

from __future__ import annotations

import csv
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


REQUIRED_REGISTRY_FIELDS = (
    "source_id",
    "source_name",
    "publisher",
    "source_url",
    "licence_identifier",
    "licence_url",
    "required_attribution",
    "parser_normalizer_version",
    "current_status",
)

RUNTIME_RECORD_FIELDS = (
    "retrieved_at",
    "source_file_or_api_version",
    "checksum",
    "source_record_identifier",
    "last_seen_at",
    "current_status",
)


def canonical_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def load_registry(path: Path) -> dict[str, dict[str, Any]]:
    data = json.loads(path.read_text(encoding="utf-8"))
    entries = data.get("sources", []) if isinstance(data, dict) else data
    if not isinstance(entries, list):
        raise ValueError("source registry must contain a sources list")
    result: dict[str, dict[str, Any]] = {}
    for entry in entries:
        if not isinstance(entry, dict):
            raise ValueError("source registry entries must be objects")
        missing = [field for field in REQUIRED_REGISTRY_FIELDS if field not in entry]
        if missing:
            raise ValueError(f"source registry entry is missing fields: {', '.join(missing)}")
        source_id = str(entry["source_id"]).strip()
        if not source_id or source_id in result:
            raise ValueError("source registry source_id values must be non-empty and unique")
        result[source_id] = entry
    return result


def validate_source_definition(entry: dict[str, Any]) -> None:
    """Reject incomplete entries before a snapshot can be treated as usable."""
    for field in REQUIRED_REGISTRY_FIELDS:
        if field not in entry:
            raise ValueError(f"source entry missing required field: {field}")
    if entry["current_status"] not in {"CURRENT_SOURCE_READY", "TEMPLATE_PENDING_SOURCE_CONFIRMATION"}:
        raise ValueError(f"source is not in an allowed preparation state: {entry['current_status']}")
    if entry["current_status"] == "CURRENT_SOURCE_READY":
        for field in ("source_url", "licence_identifier", "licence_url", "required_attribution"):
            if not str(entry.get(field) or "").strip():
                raise ValueError(f"ready source is missing verified {field}")


def read_records(path: Path) -> list[dict[str, Any]]:
    if path.suffix.lower() == ".json":
        data = json.loads(path.read_text(encoding="utf-8"))
        if isinstance(data, dict):
            data = data.get("records", data.get("data", []))
        if not isinstance(data, list) or not all(isinstance(row, dict) for row in data):
            raise ValueError("JSON candidate must be a list of objects or contain records/data")
        return data
    with path.open("r", newline="", encoding="utf-8-sig") as handle:
        return [dict(row) for row in csv.DictReader(handle)]


def snapshot_bytes(
    payload: bytes,
    source_id: str,
    snapshot_root: Path,
    *,
    retrieved_at: str | None = None,
    source_file_or_api_version: str | None = None,
    parser_normalizer_version: str,
) -> dict[str, Any]:
    """Write a content-addressed raw snapshot and its metadata once."""
    retrieved = retrieved_at or datetime.now(timezone.utc).isoformat()
    checksum = sha256_bytes(payload)
    directory = snapshot_root / source_id
    directory.mkdir(parents=True, exist_ok=True)
    raw_path = directory / f"{checksum}.raw"
    metadata_path = directory / f"{checksum}.json"
    if raw_path.exists() and raw_path.read_bytes() != payload:
        raise ValueError("content-addressed snapshot collision")
    if not raw_path.exists():
        raw_path.write_bytes(payload)
    metadata = {
        "source_id": source_id,
        "retrieved_at": retrieved,
        "last_seen_at": retrieved,
        "source_file_or_api_version": source_file_or_api_version,
        "checksum": checksum,
        "parser_normalizer_version": parser_normalizer_version,
        "current_status": "CURRENT",
        "immutable": True,
        "raw_snapshot": raw_path.name,
    }
    if metadata_path.exists():
        existing = json.loads(metadata_path.read_text(encoding="utf-8"))
        if existing != metadata:
            raise ValueError("snapshot metadata already exists with different provenance")
    else:
        metadata_path.write_text(canonical_json(metadata) + "\n", encoding="utf-8")
    return metadata


def diff_records(
    previous: list[dict[str, Any]],
    current: list[dict[str, Any]],
    *,
    record_id_field: str = "id",
) -> dict[str, Any]:
    """Compare source records without mutating either input or canonical data."""
    previous_by_id: dict[str, dict[str, Any]] = {}
    current_by_id: dict[str, dict[str, Any]] = {}
    duplicate_ids: list[str] = []
    for label, rows, destination in (("previous", previous, previous_by_id), ("current", current, current_by_id)):
        for row in rows:
            record_id = str(row.get(record_id_field, "")).strip()
            if not record_id:
                continue
            if record_id in destination:
                duplicate_ids.append(f"{label}:{record_id}")
            destination[record_id] = row
    new_ids = sorted(set(current_by_id) - set(previous_by_id))
    missing_ids = sorted(set(previous_by_id) - set(current_by_id))
    changed_ids = sorted(
        record_id
        for record_id in set(current_by_id) & set(previous_by_id)
        if canonical_json(current_by_id[record_id]) != canonical_json(previous_by_id[record_id])
    )
    unchanged_ids = sorted(
        record_id
        for record_id in set(current_by_id) & set(previous_by_id)
        if record_id not in changed_ids
    )
    return {
        "new": new_ids,
        "missing_or_stale": missing_ids,
        "changed": changed_ids,
        "unchanged": unchanged_ids,
        "duplicate_ids": sorted(set(duplicate_ids)),
        "record_status": {
            **{record_id: "NEW" for record_id in new_ids},
            **{record_id: "STALE_OR_MISSING" for record_id in missing_ids},
            **{record_id: "CHANGED" for record_id in changed_ids},
            **{record_id: "CURRENT" for record_id in unchanged_ids},
        },
        "canonical_mutations": 0,
        "review_required": bool(missing_ids or changed_ids or duplicate_ids),
    }

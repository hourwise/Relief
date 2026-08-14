#!/usr/bin/env python3
"""Create a local source snapshot and review-only deterministic diff."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from .framework import (
    canonical_json,
    diff_records,
    load_registry,
    read_records,
    snapshot_bytes,
    validate_source_definition,
)


REPOSITORY_ROOT = Path(__file__).resolve().parents[2]


def main() -> int:
    parser = argparse.ArgumentParser(description="Read-only source refresh snapshot/diff")
    parser.add_argument("--registry", default=str(REPOSITORY_ROOT / "tools/source_refresh/source_registry.json"))
    parser.add_argument("--source-id", required=True)
    parser.add_argument("--input", required=True, help="Locally fetched candidate CSV or JSON")
    parser.add_argument("--previous", help="Previous local CSV or JSON snapshot for comparison")
    parser.add_argument("--snapshot-root", default=str(REPOSITORY_ROOT / "tools/source_refresh/snapshots"))
    parser.add_argument("--output", default=str(REPOSITORY_ROOT / "tools/source_refresh/output/review.json"))
    parser.add_argument("--record-id-field", default="id")
    parser.add_argument("--source-file-or-api-version")
    parser.add_argument("--retrieved-at")
    parser.add_argument("--parser-normalizer-version", default="source-refresh-framework-v1")
    args = parser.parse_args()

    registry = load_registry(Path(args.registry))
    if args.source_id not in registry:
        raise SystemExit(f"unknown source id: {args.source_id}")
    source = registry[args.source_id]
    validate_source_definition(source)
    input_path = Path(args.input)
    payload = input_path.read_bytes()
    metadata = snapshot_bytes(
        payload,
        args.source_id,
        Path(args.snapshot_root),
        retrieved_at=args.retrieved_at,
        source_file_or_api_version=args.source_file_or_api_version,
        parser_normalizer_version=args.parser_normalizer_version,
    )
    current = read_records(input_path)
    previous = read_records(Path(args.previous)) if args.previous else []
    report = {
        "source": source,
        "snapshot": metadata,
        "candidate_record_count": len(current),
        "previous_record_count": len(previous),
        "diff": diff_records(previous, current, record_id_field=args.record_id_field),
        "pipeline": [
            "DOWNLOAD/FETCH (existing source-specific downloader)",
            "IMMUTABLE_RAW_SNAPSHOT",
            "NORMALIZE",
            "DETERMINISTIC_MATCH",
            "PROPOSED_CHANGES",
            "PROVENANCE_COMPARISON",
            "REVIEW",
            "BOUNDED_APPLY (not implemented by this command)",
        ],
        "review_only": True,
        "canonical_mutations": 0,
    }
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"review_only": True, "canonical_mutations": 0, "output": str(output), "diff": report["diff"]}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

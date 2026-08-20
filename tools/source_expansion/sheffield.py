"""Build the frozen, read-only Sheffield adjudication package."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from tools.source_refresh.framework import canonical_json


PACKAGE_VERSION = "relief.uk-public-source-expansion.sheffield-adjudication.v1"


def build_sheffield_package(review: dict[str, Any], nearby_ids: list[str], no_nearby_ids: list[str]) -> dict[str, Any]:
    nearby = set(nearby_ids)
    no_nearby = set(no_nearby_ids)
    records = review.get("records", [])
    operations = []
    for record in records:
        source_record_id = str(record["source_record_id"])
        if source_record_id not in nearby and source_record_id not in no_nearby:
            raise ValueError(f"Sheffield record is missing an adjudication bucket: {source_record_id}")
        operations.append({
            "operation_id": f"sheffield:{source_record_id}",
            "source_record_id": source_record_id,
            "decision": "DEFER_EXTERNAL_VERIFICATION",
            "reason_code": "MISSING_SOURCE_NAME",
            "nearby_existing_facility_within_100m": source_record_id in nearby,
            "proposed_action": "NONE",
            "safety_note": "A UPRN and coordinate do not establish a facility display name or an exact canonical identity; do not insert, link, or enrich.",
        })
    if len(operations) != 41 or len(nearby) != 18 or len(no_nearby) != 23:
        raise ValueError("unexpected Sheffield package population")
    return {
        "package_version": PACKAGE_VERSION,
        "classification": "SHEFFIELD — ADJUDICATED / NO SUPPORTABLE OPERATIONS / EXTERNAL VERIFICATION REQUIRED",
        "source": {
            "source_id": review["source"]["source_id"],
            "source_name": review["source"]["source_name"],
            "publisher": review["source"]["publisher"],
            "source_url": review["source"]["source_url"],
            "licence": review["source"]["licence_identifier"],
            "snapshot_sha256": review["source"]["raw_checksum"],
            "retrieved_at": review["source"]["retrieved_at"],
            "service_fields": ["objectid", "uprn", "blpu_state"],
            "source_state_counts": {"2": 41},
        },
        "decision_summary": {
            "source_rows": 41,
            "nearby_existing_facility_within_100m": 18,
            "no_nearby_existing_facility_within_100m": 23,
            "multiple_nearby_facilities": 0,
            "exact_source_links": 0,
            "missing_source_names": 41,
            "INSERT": 0,
            "SOURCE_LINK": 0,
            "ENRICHMENT": 0,
            "DEFER_EXTERNAL_VERIFICATION": 41,
        },
        "operations": operations,
        "production_boundary": {
            "canonical_mutations": 0,
            "production_mutations": 0,
            "facility_inserts": 0,
            "facility_updates": 0,
            "facility_deletes": 0,
            "facility_source_mutations": 0,
            "provenance_mutations": 0,
            "import_run_mutations": 0,
            "staging_mutations": 0,
        },
        "next_required_evidence": "An authoritative name-bearing source or council/OS/UPRN lookup with reuse rights and a stable facility identity.",
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Freeze Sheffield read-only adjudication")
    parser.add_argument("--review", required=True)
    parser.add_argument("--nearby-ids", required=True)
    parser.add_argument("--no-nearby-ids", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args(argv)
    review = json.loads(Path(args.review).read_text(encoding="utf-8"))
    nearby = json.loads(Path(args.nearby_ids).read_text(encoding="utf-8"))
    no_nearby = json.loads(Path(args.no_nearby_ids).read_text(encoding="utf-8"))
    package = build_sheffield_package(review, nearby, no_nearby)
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(canonical_json(package) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

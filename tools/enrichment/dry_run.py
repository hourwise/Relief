#!/usr/bin/env python3
"""Run the non-mutating Toilet Map reconciliation dry run.

The only network operation in this command is HTTP GET against the configured
Supabase REST tables. There is no POST/PATCH/DELETE path and no SQL client.
The source file is read locally and reports are written locally.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from pipeline import SOURCE_NAME, ToiletMapAdapter, reconcile

DEFAULT_DATA_URL = "https://www.toiletmap.org.uk/dataset"
DEFAULT_DOWNLOAD_URL = "https://p02w6qqjlqmja4sk.public.blob.vercel-storage.com/exports/toilets-2026-08-11T00%3A00%3A40.710Z-APHGhV8gen3MznZyQPYdAigXG8eRY7.csv?download=1"
DEFAULT_SOURCE_UPDATED_AT = "2026-08-11T01:00:00+00:00"
PAGE_SIZE = 1000


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


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def rest_get_rows(base_url: str, anon_key: str, table: str, select: str, snapshot_dir: Path, offline: bool) -> list[dict[str, Any]]:
    snapshot_path = snapshot_dir / f"{table}.json"
    if offline:
        return json.loads(snapshot_path.read_text(encoding="utf-8"))
    rows: list[dict[str, Any]] = []
    offset = 0
    while True:
        params = urlencode({"select": select, "order": "id.asc", "limit": PAGE_SIZE, "offset": offset})
        url = f"{base_url.rstrip('/')}/rest/v1/{table}?{params}"
        request = Request(
            url,
            method="GET",
            headers={
                "apikey": anon_key,
                "Authorization": f"Bearer {anon_key}",
                "Accept": "application/json",
                "Prefer": "count=exact",
            },
        )
        with urlopen(request, timeout=60) as response:
            page = json.loads(response.read().decode("utf-8"))
        if not isinstance(page, list):
            raise RuntimeError(f"Supabase REST returned a non-list for {table}")
        rows.extend(page)
        if len(page) < PAGE_SIZE:
            break
        offset += PAGE_SIZE
    snapshot_dir.mkdir(parents=True, exist_ok=True)
    snapshot_path.write_text(json.dumps(rows, ensure_ascii=False), encoding="utf-8")
    return rows


def discover_input(root: Path) -> Path:
    candidates = sorted((root / "tools" / "facility-enrichment" / "cache").glob("toilet-map-uk-*.csv"), key=lambda item: item.stat().st_mtime, reverse=True)
    if not candidates:
        raise FileNotFoundError("No cached Toilet Map CSV found; download the official dataset into tools/facility-enrichment/cache first.")
    return candidates[0]


def write_markdown(report: dict[str, Any], path: Path) -> None:
    summary = report["summary"]
    source = report["source"]
    input_data = report["input"]
    lines = [
        "# Toilet Map UK Reconciliation Dry Run - 2026-08",
        "",
        "> Read-only report. No Supabase inserts, updates, deletes, migrations, or deployments were performed.",
        "",
        "## Source",
        "",
        f"- Canonical source: {source['canonical_name']}",
        f"- Official dataset page: {source['data_url']}",
        f"- Download URL used: {source['download_url']}",
        f"- Source-declared update timestamp: {source['source_declared_update_timestamp']}",
        f"- Retrieved at: {source['retrieval_timestamp']}",
        f"- Licence: {source['licence']}",
        f"- Input checksum: `{source['input_sha256']}`",
        f"- Input bytes: {source['input_bytes']:,}",
        "",
        "## Baseline and input",
        "",
        f"- Relief facilities at baseline: **{summary['relief_baseline_facility_count']:,}**",
        f"- Toilet Map records in current input: **{summary['current_toilet_map_input_record_count']:,}**",
        f"- Active / removed-or-inactive / unknown status: **{summary['current_toilet_map_active_records']:,} / {summary['current_toilet_map_removed_or_inactive_records']:,} / {summary['current_toilet_map_unknown_status_records']:,}**",
        f"- Existing Toilet Map-linked facilities in baseline: **{report['baseline'].get('toilet_map_linked_facilities', 'not recorded'):,}**",
        f"- Facilities with non-empty field provenance: **{report['baseline'].get('records_with_field_provenance', 'not recorded'):,}**",
        "",
        "## Reconciliation result",
        "",
        "| Measure | Count |",
        "|---|---:|",
        f"| Exact source-ID matches | {summary['exact_source_id_matches']:,} |",
        f"| High-confidence inferred matches | {summary['high_confidence_inferred_matches']:,} |",
        f"| Ambiguous candidates | {summary['ambiguous_candidates']:,} |",
        f"| Likely-new facilities | {summary['likely_new_facilities']:,} |",
        f"| Existing linked records unchanged | {summary['unchanged_linked_records']:,} |",
        f"| Existing linked records changed | {summary['changed_linked_records']:,} |",
        f"| Upstream removed/inactive records | {summary['upstream_removed_inactive_records']:,} |",
        f"| Previously linked records absent upstream | {summary['previously_linked_relief_records_absent_upstream']:,} |",
        f"| Invalid source records | {summary['invalid_source_records']:,} |",
        f"| Source-quality warning records | {summary['source_quality_warning_records']:,} |",
        f"| Potential duplicate-risk clusters | {summary['potential_duplicate_clusters']:,} |",
        "",
        "## Field enrichment opportunities",
        "",
    ]
    if report["field_enrichment_opportunities"]:
        lines.extend(f"- `{field}` could supply a previously unknown Relief value for **{count:,}** matched records." for field, count in sorted(report["field_enrichment_opportunities"].items(), key=lambda item: (-item[1], item[0])))
    else:
        lines.append("- None measured.")
    lines.extend(["", "## Field conflicts", ""])
    if report["field_conflicts"]:
        lines.extend(f"- `{field}` disagrees with the current Relief value on **{count:,}** matched records." for field, count in sorted(report["field_conflicts"].items(), key=lambda item: (-item[1], item[0])))
    else:
        lines.append("- None measured.")
    lines.extend([
        "",
        "## Matching rules",
        "",
        "- Existing `facility_sources` source ID linkage is authoritative.",
        "- High-confidence inference requires a close name match plus a conservative 60m/150m geographic threshold and no close competitor.",
        "- Ambiguous candidates are reported, never automatically merged.",
        "- Missing upstream values remain unknown; they do not clear or become false in Relief.",
        "- A source record missing from the current snapshot is reported for policy review; it is not deleted or unpublished.",
        "",
        "## Representative review samples",
        "",
    ])
    for label in ("likely_new", "changed", "ambiguous", "upstream_removed_or_inactive", "previously_linked_absent_upstream", "invalid_or_source_quality", "field_conflicts"):
        examples = report["examples"].get(label, [])
        lines.append(f"- **{label}:** {len(examples)} sample(s) in the machine-readable report." if examples else f"- **{label}:** none available in this run.")
    lines.extend([
        "",
        "## Safety boundary",
        "",
        "This command uses only HTTP GET for the configured Supabase REST reads and local file writes for snapshots/reports. The existing live importer remains a separate, explicit path and was not invoked.",
        "",
        f"Machine-readable report: `{report.get('report_json_path', 'report.json')}`",
    ])
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def run(args: argparse.Namespace) -> dict[str, Any]:
    root = Path(args.root).resolve()
    input_path = Path(args.input).resolve() if args.input else discover_input(root)
    baseline_path = Path(args.baseline).resolve()
    snapshot_dir = Path(args.snapshot_dir).resolve()
    report_json_path = Path(args.report_json).resolve()
    report_markdown_path = Path(args.report_markdown).resolve()
    input_hash = sha256(input_path)
    env = read_env(root / ".env")
    base_url = env.get("EXPO_PUBLIC_SUPABASE_URL")
    anon_key = env.get("EXPO_PUBLIC_SUPABASE_ANON_KEY")
    if not args.offline and (not base_url or not anon_key):
        raise RuntimeError("Read-only REST snapshot requires EXPO_PUBLIC_SUPABASE_URL and EXPO_PUBLIC_SUPABASE_ANON_KEY in .env")
    if not baseline_path.exists():
        raise FileNotFoundError(f"Baseline report not found: {baseline_path}")
    baseline = json.loads(baseline_path.read_text(encoding="utf-8"))
    adapter = ToiletMapAdapter()
    candidates = adapter.read(input_path)
    facilities = rest_get_rows(base_url or "", anon_key or "", "facilities", "id,name,address,town,postcode,latitude,longitude,open_hours,is_free,is_accessible,requires_radar_key,has_baby_changing,is_gender_neutral,is_family_friendly,has_staff_nearby,field_provenance,publication_status,verification_status", snapshot_dir, args.offline)
    source_links = rest_get_rows(base_url or "", anon_key or "", "facility_sources", "id,facility_id,source_name,source_record_id,source_url,source_licence,source_updated_at,is_current", snapshot_dir, args.offline)
    generated_at = datetime.now(timezone.utc).isoformat()
    source_metadata = {
        "canonical_name": SOURCE_NAME,
        "data_url": DEFAULT_DATA_URL,
        "download_url": args.download_url,
        "source_declared_update_timestamp": args.source_updated_at,
        "retrieval_timestamp": args.retrieved_at or generated_at,
        "licence": "CC BY 4.0",
        "attribution": "Contains data from the Toilet Map © 2025 – CC BY 4.0 (Creative Commons Attribution 4.0 International)",
        "input_sha256": input_hash,
        "input_bytes": input_path.stat().st_size,
    }
    input_metadata = {
        "generated_at": generated_at,
        "input_path": str(input_path),
        "snapshot_mode": "offline local snapshots" if args.offline else "read-only Supabase REST GET",
        "facility_snapshot_count": len(facilities),
        "facility_source_snapshot_count": len(source_links),
    }
    report = reconcile(candidates, facilities, source_links, baseline, source_metadata, input_metadata)
    report["report_json_path"] = report_json_path.relative_to(root).as_posix() if report_json_path.is_relative_to(root) else str(report_json_path)
    report["report_markdown_path"] = report_markdown_path.relative_to(root).as_posix() if report_markdown_path.is_relative_to(root) else str(report_markdown_path)
    report_json_path.parent.mkdir(parents=True, exist_ok=True)
    report_json_path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    write_markdown(report, report_markdown_path)
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description="Read-only Toilet Map UK reconciliation dry run")
    parser.add_argument("--root", default=Path(__file__).resolve().parents[2])
    parser.add_argument("--input")
    parser.add_argument("--baseline", default="docs/data/DEVELOPMENT_BASELINE_2026-08-11.json")
    parser.add_argument("--snapshot-dir", default="tools/facility-enrichment/cache")
    parser.add_argument("--report-json", default="tools/facility-enrichment/output/toilet-map-reconciliation.json")
    parser.add_argument("--report-markdown", default="tools/facility-enrichment/output/toilet-map-reconciliation.md")
    parser.add_argument("--source-updated-at", default=DEFAULT_SOURCE_UPDATED_AT)
    parser.add_argument("--retrieved-at")
    parser.add_argument("--download-url", default=DEFAULT_DOWNLOAD_URL)
    parser.add_argument("--offline", action="store_true", help="Use local facility/source snapshots instead of REST GETs")
    args = parser.parse_args()
    try:
        report = run(args)
    except Exception as exc:  # CLI boundary: provide a concise failure and non-zero status.
        print(f"ERROR: dry run failed: {exc}", file=sys.stderr)
        return 1
    print(json.dumps({"read_only": report["read_only"], "summary": report["summary"], "report_json": report["report_json_path"], "report_markdown": report["report_markdown_path"]}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

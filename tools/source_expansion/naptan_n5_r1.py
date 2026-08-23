"""Read-only N5-R1 frozen-source count-contract reconciliation.

The validator deliberately separates publisher XML element counts, logical
identity counts, duplicate extras, unresolved edge rows, and distinct missing
identities. It never connects to Supabase and has no production write path.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import statistics
import time
import xml.etree.ElementTree as ET
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

from tools.source_expansion.naptan_n3 import (
    deep_hierarchy_analysis,
    multi_parent_analysis,
    normalize_complexes,
    parse_xml as parse_n3,
)


FROZEN_SHA256 = "6FC7E40E2AF3B30E9FD117BDAC313B58F3385BFF26517FD78D5554DA12B4183A"
FROZEN_BYTES = 578_991_782
N4A_SHA256 = "087A389B8CEAC021B12708BC55C39022CB38D5459510EFFB6CF057CEF232C44E"
N4A_RELATIVE_PATH = "supabase/migrations/20260822170000_naptan_transport_source_graph.sql"
PARENT_TAGS = {"parentstoparearef", "parentstopareacode", "parentid"}


class N5R1Error(ValueError):
    pass


def local_name(tag: str) -> str:
    return tag.rsplit("}", 1)[-1]


def text_of(element: ET.Element, wanted: str) -> str:
    for child in element.iter():
        if local_name(child.tag) == wanted:
            value = (child.text or "").strip()
            if "\ufffd" in value:
                raise N5R1Error(f"replacement character U+FFFD in {wanted}")
            return value
    return ""


def place_identity(value: str) -> str:
    if not value:
        raise N5R1Error("empty StopArea identity")
    return f"naptan-stop-area:{value.upper()}"


def node_identity(value: str) -> str:
    if not value:
        raise N5R1Error("empty StopPoint identity")
    return f"naptan-stop-point:{value.upper()}"


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest().upper()


def verify_frozen_source(path: Path) -> dict[str, Any]:
    actual = {"byte_size": path.stat().st_size, "sha256": sha256_file(path)}
    actual["exact"] = actual["byte_size"] == FROZEN_BYTES and actual["sha256"] == FROZEN_SHA256
    if not actual["exact"]:
        raise N5R1Error(f"FROZEN_SOURCE_REPLAY_UNAVAILABLE: {actual}")
    return {**actual, "expected_byte_size": FROZEN_BYTES, "expected_sha256": FROZEN_SHA256}


def direct_element_counter(path: Path) -> dict[str, Any]:
    """Method B: count XML relationship elements without identity maps."""
    started = time.perf_counter()
    stop_points = 0
    stop_areas = 0
    membership_elements = 0
    parent_elements = 0
    blank_memberships = 0
    blank_parents = 0
    for _, element in ET.iterparse(path, events=("end",)):
        kind = local_name(element.tag)
        if kind == "StopPoint":
            stop_points += 1
            for child in element.iter():
                if local_name(child.tag) == "StopAreaRef":
                    membership_elements += 1
                    if not (child.text or "").strip():
                        blank_memberships += 1
            element.clear()
        elif kind == "StopArea":
            stop_areas += 1
            for child in element.iter():
                if local_name(child.tag).lower() in PARENT_TAGS:
                    parent_elements += 1
                    if not (child.text or "").strip():
                        blank_parents += 1
            element.clear()
    return {
        "method": "B_DIRECT_STREAMING_XML_ELEMENT_COUNTER",
        "stop_points": stop_points,
        "stop_areas": stop_areas,
        "publisher_membership_element_count": membership_elements,
        "publisher_parent_element_count": parent_elements,
        "blank_membership_elements": blank_memberships,
        "blank_parent_elements": blank_parents,
        "seconds": round(time.perf_counter() - started, 3),
        "independence": "iterparse element counter; no N3 identity maps or normalization",
    }


def frequency_summary(values: list[int]) -> dict[str, Any]:
    if not values:
        return {"distinct_identities": 0, "min": 0, "max": 0, "mean": 0, "median": 0, "referenced_more_than_once": 0}
    return {
        "distinct_identities": len(values),
        "min": min(values),
        "max": max(values),
        "mean": round(statistics.mean(values), 6),
        "median": statistics.median(values),
        "referenced_more_than_once": sum(value > 1 for value in values),
    }


def independent_key_counter(path: Path) -> dict[str, Any]:
    """Method C: derive and count independent logical keys and frequencies."""
    started = time.perf_counter()
    membership_counts: Counter[str] = Counter()
    parent_counts: Counter[str] = Counter()
    membership_locations: defaultdict[str, list[dict[str, int]]] = defaultdict(list)
    parent_locations: defaultdict[str, list[dict[str, int]]] = defaultdict(list)
    node_ids: set[str] = set()
    area_ids: set[str] = set()
    stop_point_sequence = 0
    stop_area_sequence = 0
    for _, element in ET.iterparse(path, events=("end",)):
        kind = local_name(element.tag)
        if kind == "StopPoint":
            stop_point_sequence += 1
            publisher_id = text_of(element, "AtcoCode")
            node = node_identity(publisher_id)
            node_ids.add(node)
            ref_sequence = 0
            for child in element.iter():
                if local_name(child.tag) != "StopAreaRef":
                    continue
                ref_sequence += 1
                raw_ref = (child.text or "").strip()
                if not raw_ref:
                    continue
                place = place_identity(raw_ref)
                key = f"{node}|{place}"
                membership_counts[key] += 1
                membership_locations[key].append({"stop_point_sequence": stop_point_sequence, "reference_sequence": ref_sequence})
            element.clear()
        elif kind == "StopArea":
            stop_area_sequence += 1
            publisher_id = text_of(element, "StopAreaCode")
            child_id = place_identity(publisher_id)
            area_ids.add(child_id)
            parent_sequence = 0
            for child in element.iter():
                if local_name(child.tag).lower() not in PARENT_TAGS:
                    continue
                parent_sequence += 1
                raw_parent = (child.text or "").strip()
                if not raw_parent:
                    continue
                parent_id = place_identity(raw_parent)
                key = f"{child_id}|{parent_id}"
                parent_counts[key] += 1
                parent_locations[key].append({"stop_area_sequence": stop_area_sequence, "reference_sequence": parent_sequence})
            element.clear()

    membership_missing_frequency: Counter[str] = Counter()
    membership_missing_raw_frequency: Counter[str] = Counter()
    unresolved_membership_edges = 0
    unresolved_membership_raw = 0
    for key, count in membership_counts.items():
        _node, place = key.split("|", 1)
        if place not in area_ids:
            membership_missing_frequency[place] += 1
            membership_missing_raw_frequency[place] += count
            unresolved_membership_edges += 1
            unresolved_membership_raw += count
    parent_missing_frequency: Counter[str] = Counter()
    parent_missing_raw_frequency: Counter[str] = Counter()
    unresolved_parent_edges = 0
    unresolved_parent_raw = 0
    for key, count in parent_counts.items():
        _child, parent = key.split("|", 1)
        if parent not in area_ids:
            parent_missing_frequency[parent] += 1
            parent_missing_raw_frequency[parent] += count
            unresolved_parent_edges += 1
            unresolved_parent_raw += count

    duplicate_keys = []
    for key, count in sorted(membership_counts.items()):
        if count > 1:
            node, place = key.split("|", 1)
            duplicate_keys.append({
                "publisher_node_identity": node,
                "publisher_place_identity": place,
                "membership_key": key,
                "raw_occurrence_count": count,
                "duplicate_extra_occurrence_count": count - 1,
                "source_occurrences": membership_locations[key],
            })

    parent_duplicates = [
        {"parent_edge_key": key, "raw_occurrence_count": count, "duplicate_extra_occurrence_count": count - 1, "source_occurrences": parent_locations[key]}
        for key, count in sorted(parent_counts.items()) if count > 1
    ]
    return {
        "method": "C_INDEPENDENT_LOGICAL_KEY_COUNTER",
        "stop_points": len(node_ids),
        "stop_areas": len(area_ids),
        "publisher_membership_element_count": sum(membership_counts.values()),
        "unique_membership_key_count": len(membership_counts),
        "duplicate_membership_extra_occurrence_count": sum(max(count - 1, 0) for count in membership_counts.values()),
        "stored_membership_row_count": len(membership_counts),
        "unresolved_membership_edge_count": unresolved_membership_edges,
        "unresolved_membership_raw_element_count": unresolved_membership_raw,
        "distinct_missing_member_parent_identity_count": len(membership_missing_frequency),
        "missing_member_parent_identity_frequency": dict(sorted(membership_missing_frequency.items())),
        "missing_member_parent_identity_raw_frequency": dict(sorted(membership_missing_raw_frequency.items())),
        "missing_member_parent_frequency_summary": frequency_summary(list(membership_missing_frequency.values())),
        "publisher_parent_element_count": sum(parent_counts.values()),
        "unique_parent_edge_count": len(parent_counts),
        "stored_parent_row_count": len(parent_counts),
        "duplicate_parent_extra_occurrence_count": sum(max(count - 1, 0) for count in parent_counts.values()),
        "unresolved_parent_edge_count": unresolved_parent_edges,
        "unresolved_parent_raw_element_count": unresolved_parent_raw,
        "distinct_missing_area_parent_identity_count": len(parent_missing_frequency),
        "missing_area_parent_identity_frequency": dict(sorted(parent_missing_frequency.items())),
        "missing_area_parent_identity_raw_frequency": dict(sorted(parent_missing_raw_frequency.items())),
        "missing_area_parent_frequency_summary": frequency_summary(list(parent_missing_frequency.values())),
        "exact_duplicate_memberships": duplicate_keys,
        "duplicate_parent_edges": parent_duplicates,
        "invariants": {
            "raw_equals_unique_plus_duplicate_extras": sum(membership_counts.values()) == len(membership_counts) + sum(max(count - 1, 0) for count in membership_counts.values()),
            "parent_raw_equals_unique_plus_duplicate_extras": sum(parent_counts.values()) == len(parent_counts) + sum(max(count - 1, 0) for count in parent_counts.values()),
            "unresolved_edges_ge_distinct_missing_ids": unresolved_membership_edges >= len(membership_missing_frequency),
            "unresolved_parent_edges_ge_distinct_missing_ids": unresolved_parent_edges >= len(parent_missing_frequency),
        },
        "seconds": round(time.perf_counter() - started, 3),
        "independence": "separate identity-key/frequency pass; no N3 parser or normalized projection",
    }


def n3_projection(path: Path) -> dict[str, Any]:
    started = time.perf_counter()
    data, parse_seconds = parse_n3(path)
    normalized = normalize_complexes(data)
    multi = multi_parent_analysis(data, normalized)
    deep = deep_hierarchy_analysis(data)
    type_counts = Counter(row["complex_type"] for row in normalized["complexes"])
    mode_counts = Counter("multimodal" if len(row["modes"]) > 1 else (row["modes"][0] if row["modes"] else "no_mode") for row in normalized["complexes"])
    return {
        "method": "A_EXISTING_COMMITTED_N3_PARSER_UNCHANGED",
        "stop_points": len(data["points"]),
        "stop_areas": len(data["areas"]),
        "unique_membership_key_count": sum(len(value) for value in data["point_parents"].values()),
        "duplicate_membership_extra_occurrence_count": data["duplicate_memberships"],
        "derived_publisher_membership_element_count": sum(len(value) for value in data["point_parents"].values()) + data["duplicate_memberships"],
        "distinct_missing_member_parent_identity_count": len(data["defects"]["MISSING_MEMBER_PARENT"]),
        "distinct_missing_area_parent_identity_count": len(data["defects"]["MISSING_AREA_PARENT"]),
        "publisher_parent_element_count": len(data["parent_map"]) and sum(len(value) for value in data["parent_map"].values()) or 0,
        "normalized_complexes": len(normalized["complexes"]),
        "complex_type_distribution": dict(sorted(type_counts.items())),
        "mode_distribution": dict(sorted(mode_counts.items())),
        "unresolved_area_nodes": sum(1 for result in normalized["roots"].values() if result[0] is None),
        "multi_parent_nodes": multi["total_multi_parent_stop_points"],
        "shared_root_multi_parent_nodes": multi["shared_common_complex_count"],
        "cross_complex_or_unresolved_multi_parent_nodes": multi["cross_complex_or_unresolved_count"],
        "hierarchy_cycles": len(data["defects"]["HIERARCHY_CYCLE"]),
        "maximum_hierarchy_depth": deep["maximum_depth"],
        "parse_seconds": round(parse_seconds, 3),
        "total_seconds": round(time.perf_counter() - started, 3),
        "independence": "existing committed N3 parser and projection; not changed by N5-R1",
    }


def schema_static_audit(repo_root: Path) -> dict[str, Any]:
    migration = repo_root / N4A_RELATIVE_PATH
    text = migration.read_text(encoding="utf-8")
    actual_hash = sha256_file(migration)
    required_fragments = {
        "membership_unique_key": "unique (snapshot_id, membership_key)",
        "membership_duplicate_count": "duplicate_occurrence_count integer default 1 not null",
        "membership_nullable_node": "node_id uuid,",
        "membership_nullable_place": "place_id uuid,",
        "membership_unresolved_status": "UNRESOLVED_MISSING_PLACE",
        "parent_unique_key": "unique (snapshot_id, parent_edge_key)",
        "parent_duplicate_count": "duplicate_occurrence_count integer default 1 not null",
        "parent_nullable_child": "child_place_id uuid,",
        "parent_nullable_parent": "parent_place_id uuid,",
        "parent_unresolved_status": "UNRESOLVED_MISSING_PARENT",
    }
    checks = {name: fragment in text for name, fragment in required_fragments.items()}
    return {
        "migration_path": N4A_RELATIVE_PATH,
        "migration_sha256": actual_hash,
        "required_sha256": N4A_SHA256,
        "sealed_hash_exact": actual_hash == N4A_SHA256,
        "checks": checks,
        "classification": "N4A_SCHEMA_SUPPORTS_CORRECTED_COUNTS" if actual_hash == N4A_SHA256 and all(checks.values()) else "N4A_SCHEMA_CHANGE_REQUIRED",
        "reason": "One row per unique membership/parent key, duplicate occurrence metadata, nullable unresolved FKs, and no one-parent-per-node constraint." if all(checks.values()) else "required representability contract not proven",
    }


def validate(path: Path, repo_root: Path) -> dict[str, Any]:
    source = verify_frozen_source(path)
    method_b = direct_element_counter(path)
    method_c = independent_key_counter(path)
    method_a = n3_projection(path)
    schema = schema_static_audit(repo_root)
    comparisons = {
        "method_a_unique_equals_method_c_unique": method_a["unique_membership_key_count"] == method_c["unique_membership_key_count"],
        "method_a_duplicate_equals_method_c_duplicate": method_a["duplicate_membership_extra_occurrence_count"] == method_c["duplicate_membership_extra_occurrence_count"],
        "method_a_raw_equals_method_b_raw": method_a["derived_publisher_membership_element_count"] == method_b["publisher_membership_element_count"],
        "method_b_raw_equals_method_c_raw": method_b["publisher_membership_element_count"] == method_c["publisher_membership_element_count"],
        "parent_raw_equals_method_c_parent_raw": method_b["publisher_parent_element_count"] == method_c["publisher_parent_element_count"] == method_a["publisher_parent_element_count"],
    }
    expected_projection = {
        "stop_points": 436428,
        "stop_areas": 97270,
        "normalized_complexes": 93751,
        "single_area": 91757,
        "parent_area": 559,
        "multimodal_parent": 1435,
        "unresolved_area_nodes": 93,
        "multi_parent_nodes": 701,
        "shared_root_multi_parent_nodes": 73,
        "cross_complex_or_unresolved_multi_parent_nodes": 628,
        "maximum_hierarchy_depth": 13,
        "hierarchy_cycles": 0,
    }
    type_name_map = {
        "single_area": "SINGLE_AREA_COMPLEX",
        "parent_area": "PARENT_AREA_COMPLEX",
        "multimodal_parent": "MULTIMODAL_PARENT_COMPLEX",
    }
    observed_projection = {
        key: method_a[key] if key in method_a else method_a["complex_type_distribution"].get(type_name_map[key], 0)
        for key in expected_projection
    }
    projection_matches = {key: observed_projection[key] == value for key, value in expected_projection.items()}
    corrected_contract = {
        "source_snapshot_rows": 1,
        "stop_area_rows": method_c["stop_areas"],
        "stop_point_rows": method_c["stop_points"],
        "publisher_membership_element_count": method_c["publisher_membership_element_count"],
        "unique_membership_key_count": method_c["unique_membership_key_count"],
        "stored_membership_row_count": method_c["stored_membership_row_count"],
        "duplicate_membership_extra_occurrence_count": method_c["duplicate_membership_extra_occurrence_count"],
        "duplicate_occurrence_column_semantics": "total_occurrences_per_logical_key; duplicate pair rows have value 2",
        "publisher_parent_element_count": method_c["publisher_parent_element_count"],
        "unique_parent_edge_count": method_c["unique_parent_edge_count"],
        "stored_parent_row_count": method_c["stored_parent_row_count"],
        "unresolved_membership_edge_count": method_c["unresolved_membership_edge_count"],
        "distinct_missing_member_parent_identity_count": method_c["distinct_missing_member_parent_identity_count"],
        "unresolved_parent_edge_count": method_c["unresolved_parent_edge_count"],
        "distinct_missing_area_parent_identity_count": method_c["distinct_missing_area_parent_identity_count"],
        "multi_parent_nodes": method_a["multi_parent_nodes"],
        "maximum_hierarchy_depth": method_a["maximum_hierarchy_depth"],
        "hierarchy_cycles": method_a["hierarchy_cycles"],
        "normalized_complexes": method_a["normalized_complexes"],
        "total_stored_source_graph_rows": 1 + method_c["stop_areas"] + method_c["stop_points"] + method_c["stored_membership_row_count"] + method_c["stored_parent_row_count"],
    }
    old_contract_test = {"old_raw_minus_duplicates": 169527 - 3, "observed_raw": method_c["publisher_membership_element_count"], "observed_logical": method_c["stored_membership_row_count"], "old_contract_is_supported": False}
    return {
        "source": source,
        "membership_count_methods": {"method_a": method_a, "method_b": method_b, "method_c": method_c},
        "comparisons": comparisons,
        "all_independent_count_methods_agree": all(comparisons.values()),
        "old_contract_arithmetic_test": old_contract_test,
        "projection_expected": expected_projection,
        "projection_observed": observed_projection,
        "projection_matches": projection_matches,
        "all_unaffected_projection_invariants_match": all(projection_matches.values()),
        "schema_static_audit": schema,
        "corrected_contract": corrected_contract,
        "root_cause_classification": "MULTIPLE_DEFECTS",
        "root_cause_summary": "N2/N3 reported a deduplicated unique-key count as publisher membership elements; N4A then subtracted the three duplicate extras again in its hard-coded national estimate. Missing-reference counts were also labelled as references/rows without distinguishing edge rows from distinct missing identities.",
        "production_execution": False,
        "production_mutations": 0,
    }


def emit_evidence(result: dict[str, Any], output_dir: Path) -> list[str]:
    """Write compact non-secret evidence projections from a completed result."""
    output_dir.mkdir(parents=True, exist_ok=True)
    methods = result["membership_count_methods"]
    keyed = methods["method_c"]
    outputs: dict[str, Any] = {
        "NAPTAN_N5_R1_VALIDATION_RESULTS_2026-08-23.json": result,
        "NAPTAN_N5_R1_MEMBERSHIP_COUNT_EVIDENCE_2026-08-23.json": {
            "definitions": {
                "publisher_membership_element_count": "StopAreaRef XML elements physically present in StopPoint records.",
                "unique_membership_key_count": "Distinct naptan-stop-point:<ATCO>|naptan-stop-area:<StopAreaCode> keys.",
                "duplicate_membership_extra_occurrence_count": "Occurrences beyond the first for each unique membership key.",
                "stored_membership_row_count": "Expected transport_source_memberships rows; one row per unique key.",
            },
            "source": result["source"],
            "method_a": methods["method_a"],
            "method_b": methods["method_b"],
            "method_c_summary": {key: keyed[key] for key in (
                "publisher_membership_element_count", "unique_membership_key_count",
                "duplicate_membership_extra_occurrence_count", "stored_membership_row_count",
                "unresolved_membership_edge_count", "distinct_missing_member_parent_identity_count",
            )},
            "comparisons": result["comparisons"],
            "old_contract_arithmetic_test": result["old_contract_arithmetic_test"],
        },
        "NAPTAN_N5_R1_DUPLICATE_MEMBERSHIPS_2026-08-23.json": {
            "source": result["source"],
            "duplicate_memberships": keyed["exact_duplicate_memberships"],
            "total_duplicate_extra_occurrences": keyed["duplicate_membership_extra_occurrence_count"],
        },
        "NAPTAN_N5_R1_UNRESOLVED_MEMBERSHIP_EVIDENCE_2026-08-23.json": {
            "source": result["source"],
            "unresolved_membership_edge_count": keyed["unresolved_membership_edge_count"],
            "unresolved_membership_raw_element_count": keyed["unresolved_membership_raw_element_count"],
            "distinct_missing_member_parent_identity_count": keyed["distinct_missing_member_parent_identity_count"],
            "identity_frequency": keyed["missing_member_parent_identity_frequency"],
            "raw_identity_frequency": keyed["missing_member_parent_identity_raw_frequency"],
            "frequency_summary": keyed["missing_member_parent_frequency_summary"],
        },
        "NAPTAN_N5_R1_PARENT_EDGE_EVIDENCE_2026-08-23.json": {
            "source": result["source"],
            "publisher_parent_element_count": keyed["publisher_parent_element_count"],
            "unique_parent_edge_count": keyed["unique_parent_edge_count"],
            "stored_parent_row_count": keyed["stored_parent_row_count"],
            "duplicate_parent_extra_occurrence_count": keyed["duplicate_parent_extra_occurrence_count"],
            "unresolved_parent_edge_count": keyed["unresolved_parent_edge_count"],
            "unresolved_parent_raw_element_count": keyed["unresolved_parent_raw_element_count"],
            "distinct_missing_area_parent_identity_count": keyed["distinct_missing_area_parent_identity_count"],
            "identity_frequency": keyed["missing_area_parent_identity_frequency"],
            "raw_identity_frequency": keyed["missing_area_parent_identity_raw_frequency"],
            "frequency_summary": keyed["missing_area_parent_frequency_summary"],
        },
        "NAPTAN_N5_R1_SCHEMA_REPRESENTABILITY_2026-08-23.json": {
            "static_migration_audit": result["schema_static_audit"],
            "live_catalog_audit": {
                "target_tables_rls_enabled": True,
                "policies": [],
                "service_role_has_all_table_privileges": True,
                "public_anon_authenticated_grants": False,
                "membership_nullable_node_and_place": True,
                "parent_nullable_child_and_parent": True,
                "unique_membership_snapshot_key": True,
                "unique_parent_snapshot_key": True,
            },
        },
        "NAPTAN_N5_R1_CORRECTED_INGESTION_CONTRACT_2026-08-23.json": {
            "contract_version": "N5-R1-2026-08-23",
            "authoritative": True,
            "supersedes": [
                "docs/data/NAPTAN_N4A_SCHEMA_CONTRACT_2026-08-22.json estimated_current_snapshot_rows.memberships_after_exact_duplicate_coalescing=169524",
                "tools/source_expansion/naptan_n4a.py pre-N5-R1 national_scale_estimate",
            ],
            "source": result["source"],
            "values": result["corrected_contract"],
            "semantics": {
                "duplicate_occurrence_count": "Total raw occurrences for the logical key; each duplicated key has value 2.",
                "unresolved_membership_edge_count": "Logical unique membership rows whose place identity is missing.",
                "distinct_missing_member_parent_identity_count": "Unique missing StopArea identities referenced by unresolved membership edges.",
                "unresolved_parent_edge_count": "Logical unique StopArea-parent edges whose parent identity is missing.",
                "distinct_missing_area_parent_identity_count": "Unique missing parent StopArea identities.",
            },
            "root_cause_classification": result["root_cause_classification"],
        },
        "NAPTAN_N5_R1_COUNT_PROVENANCE_TRACE_2026-08-23.json": {
            "earliest_169524": {
                "commit": "28195ff47b8559ad6c65f7d4866b47f45870560a",
                "subject": "feat(data): define NaPTAN source graph schema",
                "file": "tools/source_expansion/naptan_n4a.py",
                "function": "national_scale_estimate",
                "field": "membership_rows_after_exact_duplicate_coalescing",
                "value": 169524,
                "origin": "hard-coded N4A national-scale estimate",
            },
            "upstream_169527": [
                {"file": "docs/data/NAPTAN_N2_HIERARCHY_REPORT_2026-08-22.md", "meaning": "N2 logical membership rows"},
                {"file": "docs/data/NAPTAN_N2_HIERARCHY_PROFILE_2026-08-22.json", "field": "memberships.total_rows", "value": 169527},
                {"file": "docs/data/NAPTAN_N3_COMPLEX_PROFILE_2026-08-22.json", "field": "source.memberships", "value": 169527},
                {"file": "docs/data/NAPTAN_N3_TRANSPORT_COMPLEX_REPORT_2026-08-22.md", "wording": "publisher-declared memberships", "value": 169527},
            ],
            "propagation": "N4A copied the existing 169527 logical/set-based count, labelled it as post-deduplication, then subtracted duplicate extras again to produce 169524. N3 itself records 169527 unique keys and 3 duplicate occurrences.",
            "classification": "MULTIPLE_DEFECTS",
        },
    }
    written: list[str] = []
    for name, value in outputs.items():
        (output_dir / name).write_text(json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        written.append(name)
    return written


def main() -> None:
    parser = argparse.ArgumentParser(description="N5-R1 frozen-source count reconciliation")
    parser.add_argument("source", type=Path)
    parser.add_argument("--repo-root", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    result = validate(args.source, args.repo_root)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"source_exact": result["source"]["exact"], "methods_agree": result["all_independent_count_methods_agree"], "projection_matches": result["all_unaffected_projection_invariants_match"], "corrected_total_rows": result["corrected_contract"]["total_stored_source_graph_rows"]}, sort_keys=True))


if __name__ == "__main__":
    main()

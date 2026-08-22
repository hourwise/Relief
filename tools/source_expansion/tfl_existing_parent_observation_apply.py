"""Bounded planner for the frozen 14-row TfL observation apply.

This module is deliberately narrow and dry-run-only.  It reads the committed
existing-parent audit and readiness evidence, proves the 14-row cohort, and
builds declarative source-link/observation operations.  It has no Supabase
client, no SQL executor, and no production mutation path.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any, Mapping

try:
    from .tfl_existing_parent_observation_audit import reproduce_cohort
except ImportError:  # Support the explicitly documented direct dry-run entrypoint.
    from tools.source_expansion.tfl_existing_parent_observation_audit import reproduce_cohort


REPOSITORY = "hourwise/Relief"
BRANCH = "codex/toilet-map-apply-1a-production-deploy"
AUDIT_PATH = Path("docs/data/RELIEF_TFL_EXISTING_PARENT_SOURCE_OBSERVATION_AUDIT_2026-08-22.json")
READINESS_PATH = Path("docs/data/RELIEF_TFL_TOILET_UNIT_PROMOTION_READINESS_2026-08-22.json")
BATCH_1_PATH = Path("docs/data/RELIEF_TFL_HUMAN_ADJUDICATION_BATCH_1_2026-08-22.json")

SOURCE_ID = "tfl_detailed_station_data"
SOURCE_NAME = "TfL detailed station data — station facilities and toilets"
SOURCE_URL = "https://api.tfl.gov.uk/stationdata/tfl-stationdata-detailed.zip"
SOURCE_LICENCE = "TfL Transport Data Service terms, based on OGL 2.0 with TfL amendments"
SOURCE_LICENCE_URL = "https://tfl.gov.uk/corporate/terms-and-conditions/transport-data-service"
SOURCE_ATTRIBUTION = "Data provided by Transport for London"
SOURCE_TERMS_ATTRIBUTION = "Powered by TfL Open Data"
SOURCE_OS_ATTRIBUTION = (
    "Contains OS data © Crown copyright and database rights 2016 and Geomni UK "
    "Map data © and database rights [2019]"
)
ZIP_SHA256 = "19c50772febd1a3d7625f59e079b7590c5da4ed70424d6f552cfd7db1611e2ce"
ZIP_BYTES = 186973
ZIP_RETRIEVAL_UTC = "2026-08-21T06:08:20.1476469Z"
RECONCILIATION_SHA256 = "65cc9cc8c41b7b3a003524610b674c7f2eae96ff7fe5116f38f2d2856cb777cb"
OBSERVATION_KIND = "TOILET_PROVISION"
COORDINATE_SCOPE = "STATION_LEVEL"


def _read_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        value = json.load(handle)
    if not isinstance(value, dict):
        raise AssertionError(f"expected JSON object: {path}")
    return value


def _stable_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def _sha256_json(value: Any) -> str:
    return hashlib.sha256(_stable_json(value).encode("utf-8")).hexdigest()


def _source_row_projection(row: Mapping[str, Any]) -> dict[str, Any]:
    fields = (
        "source_row_number",
        "source_record_id",
        "stable_tfl_station_id",
        "stable_tfl_toilet_id",
        "station_name",
        "station_public_location",
        "toilet_location_description",
        "toilet_type",
        "is_accessible",
        "has_baby_changing",
        "inside_gateline",
        "fee_status",
        "tfl_management_status",
        "station_coordinates",
        "positional_precision",
    )
    return {key: row.get(key) for key in fields}


def _batch_1_ids(batch_1: Mapping[str, Any]) -> set[str]:
    identifiers: set[str] = set()
    for key in ("new_parent_adjudications", "physical_unit_adjudications"):
        for row in batch_1.get(key, []):
            identity = (row.get("source_identity") or {}).get("source_record_id")
            if identity:
                identifiers.add(str(identity))
    return identifiers


def _expected_source_metadata() -> dict[str, Any]:
    return {
        "source_id": SOURCE_ID,
        "source_name": SOURCE_NAME,
        "source_url": SOURCE_URL,
        "licence_identifier": SOURCE_LICENCE,
        "licence_url": SOURCE_LICENCE_URL,
        "attribution": SOURCE_ATTRIBUTION,
        "transport_data_terms_attribution": SOURCE_TERMS_ATTRIBUTION,
        "os_derived_data_attribution": SOURCE_OS_ATTRIBUTION,
        "frozen_source": {
            "zip_sha256": ZIP_SHA256,
            "zip_bytes": ZIP_BYTES,
            "zip_retrieval_utc": ZIP_RETRIEVAL_UTC,
            "zip_url": SOURCE_URL,
            "reconciliation_sha256": RECONCILIATION_SHA256,
        },
    }


def reproduce_frozen_14_cohort(
    audit: Mapping[str, Any] | None = None,
    readiness: Mapping[str, Any] | None = None,
    batch_1: Mapping[str, Any] | None = None,
) -> list[dict[str, Any]]:
    """Reproduce and validate the exact 14 unique source observations."""

    audit = audit or _read_json(AUDIT_PATH)
    readiness = readiness or _read_json(READINESS_PATH)
    batch_1 = batch_1 or _read_json(BATCH_1_PATH)
    cohort = reproduce_cohort(readiness, batch_1)

    if cohort["operation_entries_total"] != 28:
        raise AssertionError("frozen operation entry count is not 28")
    if cohort["source_link_operation_entries"] != 14 or cohort["enrichment_operation_entries"] != 14:
        raise AssertionError("frozen operation classes are not 14 + 14")
    if cohort["unique_source_rows"] != 14 or cohort["station_group_count"] != 14:
        raise AssertionError("frozen unique cohort is not 14 rows across 14 stations")
    if cohort["batch_1_overlap_count"] != 0 or cohort["new_parent_overlap_count"] != 0:
        raise AssertionError("cohort overlaps excluded TfL rows")

    audit_rows = {row["source_identity"]["source_record_id"]: row for row in audit.get("rows", [])}
    readiness_rows = {row["source_record_id"]: row for row in cohort["unique_rows"]}
    if len(audit_rows) != 14 or set(audit_rows) != set(readiness_rows):
        raise AssertionError("stored audit and reproduced readiness identities differ")
    if audit.get("scope", {}).get("batch_1_overlap_count") != 0:
        raise AssertionError("stored audit reports Batch 1 contamination")
    if audit.get("scope", {}).get("new_parent_overlap_count") != 0:
        raise AssertionError("stored audit reports new-parent contamination")
    if set(audit.get("unresolved", {}).get("new_parent_source_ids", [])) & set(audit_rows):
        raise AssertionError("new-parent source identity contaminated the 14-row cohort")
    if set(audit.get("unresolved", {}).get("physical_unit_source_ids", [])) & set(audit_rows):
        raise AssertionError("physical-unit source identity contaminated the 14-row cohort")
    if set(audit_rows) & _batch_1_ids(batch_1):
        raise AssertionError("Batch 1 source identity contaminated the 14-row cohort")

    rows: list[dict[str, Any]] = []
    for source_record_id in sorted(readiness_rows):
        source_row = readiness_rows[source_record_id]
        audited = audit_rows[source_record_id]
        if audited.get("outcome") != "REQUIRES_ADDITIVE_SOURCE_OBSERVATION_MODEL":
            raise AssertionError(f"unexpected audit outcome for {source_record_id}")
        if audited.get("physical_unit_asserted") is not False:
            raise AssertionError(f"physical assertion present for {source_record_id}")
        if audited.get("physical_unit_mapping_inferred") is not False:
            raise AssertionError(f"physical mapping inferred for {source_record_id}")
        if audited.get("source_facts") != _source_row_projection(source_row):
            raise AssertionError(f"stored audit source facts differ for {source_record_id}")
        context = audited.get("existing_relief_context") or {}
        facility_id = context.get("facility_id")
        if not facility_id or not context.get("facility_name"):
            raise AssertionError(f"missing canonical parent for {source_record_id}")
        rows.append(
            {
                "source_identity": {
                    "StationUniqueId": source_row["stable_tfl_station_id"],
                    "Id": source_row["stable_tfl_toilet_id"],
                    "source_record_id": source_record_id,
                },
                "canonical_facility_id": facility_id,
                "canonical_facility_name": context["facility_name"],
                "source_facts": _source_row_projection(source_row),
                "evidence_refs": [
                    str(AUDIT_PATH).replace("\\", "/"),
                    "tools/source_expansion/cache/tfl-detailed-2026-08-21/tfl-reconciliation.json",
                ],
            }
        )
    if len(rows) != 14:
        raise AssertionError("reproduced cohort is not exactly 14 rows")
    if len({row["source_identity"]["source_record_id"] for row in rows}) != 14:
        raise AssertionError("reproduced source identities are not unique")
    if len({row["canonical_facility_id"] for row in rows}) != 14:
        raise AssertionError("reproduced canonical facilities are not unique")
    return rows


def observed_attributes(row: Mapping[str, Any]) -> dict[str, Any]:
    """Build a lossless source-evidence payload without adding canonical claims."""

    source_facts = row["source_facts"]
    coordinates = source_facts.get("station_coordinates")
    if coordinates is not None and source_facts.get("positional_precision") != (
        "STATION_LEVEL_ONLY; TOILET_COORDINATES_NOT_PROVIDED"
    ):
        raise AssertionError("non-station coordinate precision in frozen source facts")
    return {
        "source_identity": row["source_identity"],
        "source_facts": source_facts,
        "coordinate_scope": COORDINATE_SCOPE,
        "physical_unit_asserted": False,
        "unit_link_status": "UNLINKED",
        "provenance": _expected_source_metadata(),
    }


def build_apply_plan(rows: list[dict[str, Any]]) -> dict[str, Any]:
    """Build a declarative plan; production state is filled by read-only preflight."""

    operations = []
    for row in rows:
        source_record_id = row["source_identity"]["source_record_id"]
        attrs = observed_attributes(row)
        operations.append(
            {
                "source_identity": row["source_identity"],
                "canonical_facility_id": row["canonical_facility_id"],
                "canonical_facility_name": row["canonical_facility_name"],
                "facility_source_id": None,
                "source_name": SOURCE_NAME,
                "source_record_id": source_record_id,
                "source_link_action": "PENDING_PREFLIGHT",
                "observation_key": source_record_id,
                "observed_attributes": attrs,
                "observed_attributes_sha256": _sha256_json(attrs),
                "observation_action": "PENDING_PREFLIGHT",
                "coordinate_scope": COORDINATE_SCOPE,
                "physical_unit_asserted": False,
                "unit_link_status": "UNLINKED",
                "toilet_unit_id": None,
                "evidence_refs": row["evidence_refs"],
            }
        )
    return {
        "document_type": "RELIEF_TFL_EXISTING_PARENT_OBSERVATION_APPLY_PLAN",
        "classification": "GOVERNED / DECLARATIVE PLAN / PHYSICAL-UNIT PROMOTION NOT AUTHORIZED",
        "repository": REPOSITORY,
        "branch": BRANCH,
        "source": _expected_source_metadata(),
        "scope": {
            "prior_operation_entries": 28,
            "unique_source_observations": 14,
            "station_groups": 14,
            "canonical_facility_groups": 14,
            "batch_1_contamination": 0,
            "new_parent_contamination": 0,
        },
        "import_run_decision": {
            "classification": "IMPORT_RUN_NOT_REQUIRED",
            "reason": "facility_source_observations has no import_runs relationship; existing import_runs apply_1a governance is specific to Toilet Map UK and cannot represent this TfL apply.",
            "create_count": 0,
        },
        "operations": operations,
        "operation_counts": {
            "facility_inserts": 0,
            "facility_source_inserts_maximum": 14,
            "source_observation_inserts": 14,
            "canonical_facility_updates": 0,
            "toilet_unit_inserts": 0,
            "toilet_unit_source_links": 0,
            "import_runs": 0,
        },
        "production_apply": {
            "executable": False,
            "production_mutations_before_apply": 0,
            "physical_unit_promotion_authorized": False,
        },
    }


def load_plan() -> dict[str, Any]:
    return build_apply_plan(reproduce_frozen_14_cohort())


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", action="store_true", help="print the deterministic dry-run plan")
    parser.add_argument("--apply", action="store_true", help="always rejected: this module has no production apply path")
    args = parser.parse_args()
    if args.apply:
        raise SystemExit("refusing --apply: use the separately governed production transaction, not this planner")
    plan = load_plan()
    if args.json:
        print(json.dumps(plan, ensure_ascii=False, sort_keys=True, indent=2))
    else:
        print("dry-run: 14 TfL source observations; facility inserts 0; physical units 0; import runs 0")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

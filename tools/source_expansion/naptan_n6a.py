"""Read-only N6A reconciliation contracts.

N6A consumes the already-ingested NaPTAN source graph and produces local
candidate-analysis artifacts.  This module deliberately has no production
connection or apply path.  Production queries used by the N6A transaction are
executed through the governed read-only Supabase SQL channel and are checked
with :func:`assert_read_only_sql` before execution.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import unicodedata
from dataclasses import dataclass
from typing import Any

PRODUCTION_WRITE_CAPABILITY = False
SNAPSHOT_KEY = "naptan:sha256:6fc7e40e2af3b30e9fd117bdac313b58f3385bff26517fd78d5554da12b4183a"

OUTCOMES = (
    "EXISTING_CANONICAL_MATCH",
    "PROPOSED_CANONICAL_MATCH",
    "AMBIGUOUS_CANONICAL_MATCH",
    "PROPOSED_NEW_TRANSPORT_PLACE",
    "SUPPORTING_SOURCE_ONLY",
    "CONFLICT",
    "NO_ACTION",
)

GENERIC_SOURCE_NAMES = frozenset(
    {
        "central",
        "central station",
        "church",
        "high street",
        "hospital",
        "station",
    }
)

_MUTATION_WORDS = re.compile(
    r"\b(?:insert|update|delete|merge|upsert|alter|create|drop|truncate|grant|revoke|vacuum|refresh|copy|call|do)\b",
    re.IGNORECASE,
)


class NaptanN6AError(ValueError):
    """Raised when the read-only N6A contract is violated."""


def normalize_matching_text(value: str | None) -> str:
    """Apply the committed conservative external-label normalizer."""

    if value is None:
        return ""
    value = unicodedata.normalize("NFKC", value).strip().casefold()
    value = re.sub(r"[\u2010-\u2015\-_/&,.'’]", " ", value)
    return re.sub(r"\s+", " ", value)


def token_subset_compatible(source_name: str, canonical_name: str) -> bool:
    """Allow a source label with a canonical suffix, never a one-token guess."""

    source = normalize_matching_text(source_name)
    canonical = normalize_matching_text(canonical_name)
    if not source or not canonical:
        return False
    if source == canonical:
        return True
    source_tokens = set(source.split())
    canonical_tokens = set(canonical.split())
    return len(source_tokens) >= 2 and source_tokens <= canonical_tokens


def stable_candidate_key(snapshot_key: str, complex_identity: str, facility_id: str) -> str:
    """Return a stable, semantic candidate identity."""

    if not snapshot_key or not complex_identity or not facility_id:
        raise NaptanN6AError("candidate key components must be non-empty")
    return f"{snapshot_key}|{complex_identity}|{facility_id}"


def candidate_key_digest(snapshot_key: str, complex_identity: str, facility_id: str) -> str:
    """Return a short deterministic digest for compact local indexes."""

    return hashlib.sha256(stable_candidate_key(snapshot_key, complex_identity, facility_id).encode("utf-8")).hexdigest()


def assert_read_only_sql(sql: str) -> None:
    """Fail closed for SQL that could mutate production or session state."""

    if not isinstance(sql, str) or not sql.strip():
        raise NaptanN6AError("SQL must be a non-empty string")
    without_comments = re.sub(r"--[^\n]*|/\*.*?\*/", " ", sql, flags=re.DOTALL)
    if _MUTATION_WORDS.search(without_comments):
        raise NaptanN6AError("N6A accepts read-only SQL only")
    if ";" in without_comments.rstrip().rstrip(";"):
        raise NaptanN6AError("N6A accepts one read-only statement only")


def distance_band(distance_metres: float | None) -> str:
    if distance_metres is None:
        return "UNAVAILABLE"
    for limit in (25, 50, 100, 250, 500, 1000, 5000):
        if distance_metres <= limit:
            return f"<={limit}m"
    return ">5000m"


@dataclass(frozen=True)
class CandidateEvidence:
    official_identifier: bool = False
    existing_provenance: bool = False
    exact_normalized_name: bool = False
    token_subset_name: bool = False
    distance_metres: float | None = None
    hierarchy_resolved: bool = True
    candidate_count: int = 1
    facility_collision: bool = False
    source_mode: str = "no_mode"
    source_geometry_available: bool = False
    generic_source_name: bool = False
    conflicting_identifier: bool = False


def evidence_score(evidence: CandidateEvidence) -> dict[str, Any]:
    """Return decomposable evidence, never an opaque probability."""

    dimensions = {
        "official_identifier": 100 if evidence.official_identifier else 0,
        "existing_provenance": 25 if evidence.existing_provenance else 0,
        "exact_normalized_name": 40 if evidence.exact_normalized_name else 0,
        "token_subset_name": 25 if evidence.token_subset_name else 0,
        "distance_band": distance_band(evidence.distance_metres),
        "distance_points": (
            30
            if evidence.distance_metres is not None and evidence.distance_metres <= 25
            else 25
            if evidence.distance_metres is not None and evidence.distance_metres <= 50
            else 20
            if evidence.distance_metres is not None and evidence.distance_metres <= 100
            else 10
            if evidence.distance_metres is not None and evidence.distance_metres <= 250
            else 5
            if evidence.distance_metres is not None and evidence.distance_metres <= 500
            else 0
        ),
        "hierarchy_resolved": 10 if evidence.hierarchy_resolved else 0,
        "competing_candidate_penalty": 20 if evidence.candidate_count > 1 else 0,
    }
    dimensions["total_points"] = sum(value for value in dimensions.values() if isinstance(value, int))
    return dimensions


def classify_candidate(
    evidence: CandidateEvidence,
    *,
    has_candidate: bool,
) -> str:
    """Apply the conservative N6A planning classification contract."""

    if evidence.conflicting_identifier:
        return "CONFLICT"
    if evidence.official_identifier:
        return "EXISTING_CANONICAL_MATCH"
    if evidence.source_mode == "bus_coach":
        return "SUPPORTING_SOURCE_ONLY"
    if evidence.source_mode in {"no_mode", "taxi"}:
        return "NO_ACTION"
    if not has_candidate:
        return "PROPOSED_NEW_TRANSPORT_PLACE" if evidence.source_geometry_available else "SUPPORTING_SOURCE_ONLY"
    if evidence.candidate_count > 1 or evidence.facility_collision:
        return "AMBIGUOUS_CANONICAL_MATCH"
    distance = evidence.distance_metres
    strong_name_and_distance = (
        distance is not None
        and ((evidence.exact_normalized_name and distance <= 250) or (evidence.token_subset_name and distance <= 100))
    )
    if strong_name_and_distance and not evidence.generic_source_name and evidence.hierarchy_resolved:
        return "PROPOSED_CANONICAL_MATCH"
    return "AMBIGUOUS_CANONICAL_MATCH"


def emit_contract() -> dict[str, Any]:
    """Return the machine-readable local N6A contract."""

    return {
        "production_write_capability": PRODUCTION_WRITE_CAPABILITY,
        "snapshot_key": SNAPSHOT_KEY,
        "outcomes": list(OUTCOMES),
        "name_normalization": "NFKC + casefold + committed punctuation normalization + whitespace collapse",
        "candidate_generation": {
            "primary_unit": "deterministic normalized transport complex",
            "name_evidence": ["exact normalized name", "source token subset with at least two source tokens"],
            "geography_bands_metres": [25, 50, 100, 250, 500, 1000, 5000],
            "proximity_only_veto": True,
            "production_persistence": False,
        },
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Emit the read-only N6A reconciliation contract")
    parser.add_argument("--emit-contract", action="store_true", help="print the contract JSON")
    args = parser.parse_args()
    if not args.emit_contract:
        parser.error("N6A has no apply mode; use --emit-contract")
    print(json.dumps(emit_contract(), indent=2, sort_keys=True))


if __name__ == "__main__":
    main()

"""Repeatable, local-only source snapshot and diff primitives."""

from .framework import (
    REQUIRED_REGISTRY_FIELDS,
    diff_records,
    load_registry,
    read_records,
    sha256_bytes,
    snapshot_bytes,
    validate_source_definition,
)

__all__ = [
    "REQUIRED_REGISTRY_FIELDS",
    "diff_records",
    "load_registry",
    "read_records",
    "sha256_bytes",
    "snapshot_bytes",
    "validate_source_definition",
]

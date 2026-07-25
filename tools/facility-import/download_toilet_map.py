#!/usr/bin/env python3
"""Download the Toilet Map UK dataset."""

import hashlib
import sys
from pathlib import Path

import httpx

TOILET_MAP_URL = "https://toiletmap.org.uk/export/toilets.geojson"
TOILET_MAP_LICENCE = "OGL-3.0"
TOILET_MAP_SOURCE_NAME = "Toilet Map UK"


def download(output_path: Path) -> tuple[Path, str]:
    """Download the GeoJSON dataset. Returns (path, sha256 checksum)."""
    print(f"Downloading from {TOILET_MAP_URL} ...")
    with httpx.Client(follow_redirects=True, timeout=120) as client:
        resp = client.get(TOILET_MAP_URL)
        resp.raise_for_status()

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_bytes(resp.content)

    checksum = hashlib.sha256(resp.content).hexdigest()
    print(f"Saved {len(resp.content):,} bytes to {output_path}")
    print(f"SHA-256: {checksum}")
    return output_path, checksum


if __name__ == "__main__":
    out = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("data/toilet_map_uk.geojson")
    download(out)

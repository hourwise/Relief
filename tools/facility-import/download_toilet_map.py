#!/usr/bin/env python3
"""Download the Toilet Map UK dataset (CSV format)."""

import hashlib
import json
import re
import sys
from pathlib import Path

import httpx

DATASET_PAGE = "https://www.toiletmap.org.uk/dataset"
TOILET_MAP_SOURCE_NAME = "Toilet Map UK"
TOILET_MAP_LICENCE = "CC-BY-4.0"


def download(output_path: Path) -> tuple[Path, str]:
    """Download the CSV dataset. Returns (path, sha256 checksum)."""
    print(f"Fetching dataset page: {DATASET_PAGE}")
    with httpx.Client(follow_redirects=True, timeout=30) as client:
        page_resp = client.get(DATASET_PAGE)
        page_resp.raise_for_status()

    match = re.search(
        r'<script id="__NEXT_DATA__" type="application/json">(.*?)</script>',
        page_resp.text,
    )
    if not match:
        raise RuntimeError("Could not find __NEXT_DATA__ on dataset page")

    data = json.loads(match.group(1))
    files = data["props"]["pageProps"].get("fileListing", [])

    csv_url = None
    for f in files:
        if f.get("type") == "csv":
            csv_url = f["downloadUrl"]
            break

    if not csv_url:
        raise RuntimeError("No CSV download found on dataset page")

    print(f"Found CSV URL: {csv_url[:80]}...")
    print("Downloading CSV dataset...")

    with httpx.Client(follow_redirects=True, timeout=120) as client:
        resp = client.get(csv_url)
        resp.raise_for_status()

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_bytes(resp.content)

    checksum = hashlib.sha256(resp.content).hexdigest()
    print(f"Saved {len(resp.content):,} bytes to {output_path}")
    print(f"SHA-256: {checksum}")
    return output_path, checksum


if __name__ == "__main__":
    out = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("data/toilet_map_uk.csv")
    download(out)

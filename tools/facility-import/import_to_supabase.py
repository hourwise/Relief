#!/usr/bin/env python3
"""
Import normalised facility CSV into Supabase.

Usage:
  python import_to_supabase.py --file normalised.csv --dry-run
  python import_to_supabase.py --file normalised.csv
  python import_to_supabase.py --file normalised.csv --liverpool-only
"""

import argparse
import csv
import hashlib
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

import psycopg2
from dotenv import load_dotenv

load_dotenv()

DB_URL = os.getenv("SUPABASE_DB_URL")
SOURCE_NAME = "Toilet Map UK"
SOURCE_LICENCE = "OGL-3.0"
BATCH_SIZE = 500

# Liverpool bounding box (rough)
LIVERPOOL_LAT_MIN = 53.3
LIVERPOOL_LAT_MAX = 53.5
LIVERPOOL_LNG_MIN = -3.0
LIVERPOOL_LNG_MAX = -2.8


def get_connection():
    if not DB_URL:
        print("ERROR: SUPABASE_DB_URL not set. See .env.example")
        sys.exit(1)
    return psycopg2.connect(DB_URL)


def compute_checksum(file_path: Path) -> str:
    return hashlib.sha256(file_path.read_bytes()).hexdigest()


def validate_row(row: dict, row_num: int) -> list[str]:
    errors = []
    if not row.get("source_record_id"):
        errors.append("missing source_record_id")
    try:
        lat = float(row["latitude"])
        lng = float(row["longitude"])
    except (ValueError, TypeError, KeyError):
        errors.append("invalid latitude/longitude")
        return errors
    if not (49.0 <= lat <= 61.0 and -9.0 <= lng <= 2.0):
        errors.append(f"coordinates outside UK: {lat},{lng}")
    return errors


def run_import(args):
    file_path = Path(args.file)
    if not file_path.exists():
        print(f"ERROR: File not found: {file_path}")
        sys.exit(1)

    checksum = compute_checksum(file_path)
    dry_run = args.dry_run
    liverpool_only = args.liverpool_only

    print(f"File: {file_path}")
    print(f"Checksum: {checksum}")
    print(f"Dry run: {dry_run}")
    print(f"Liverpool only: {liverpool_only}")

    # Read all rows
    with open(file_path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        all_rows = list(reader)

    print(f"Rows read: {len(all_rows)}")

    # Filter to Liverpool if requested
    if liverpool_only:
        filtered = []
        for row in all_rows:
            try:
                lat = float(row["latitude"])
                lng = float(row["longitude"])
                if (LIVERPOOL_LAT_MIN <= lat <= LIVERPOOL_LAT_MAX and
                        LIVERPOOL_LNG_MIN <= lng <= LIVERPOOL_LNG_MAX):
                    filtered.append(row)
            except (ValueError, TypeError):
                continue
        all_rows = filtered
        print(f"Rows after Liverpool filter: {len(all_rows)}")

    # Validate
    valid_rows = []
    quarantined = []
    for i, row in enumerate(all_rows):
        errors = validate_row(row, i)
        if errors:
            quarantined.append((row, errors))
        else:
            valid_rows.append(row)

    print(f"Valid: {len(valid_rows)}")
    print(f"Quarantined: {len(quarantined)}")
    if quarantined and args.show_quarantined:
        for row, errs in quarantined[:10]:
            print(f"  Row {row.get('source_record_id', '?')}: {errs}")

    if dry_run:
        print("\n=== DRY RUN — no database changes ===")
        print(f"Would insert/update: {len(valid_rows)} facilities")
        print(f"Would quarantine: {len(quarantined)} rows")
        # Show sample
        for row in valid_rows[:5]:
            print(f"  {row.get('name', '?')} ({row.get('postcode', '?')})")
        if len(valid_rows) > 5:
            print(f"  ... and {len(valid_rows) - 5} more")
        return

    # === LIVE IMPORT ===
    conn = get_connection()
    conn.autocommit = False
    cur = conn.cursor()

    try:
        # 1. Create import_runs record
        cur.execute(
            """INSERT INTO import_runs
               (source_name, source_file_name, source_checksum, status, rows_received, rows_valid, rows_quarantined)
               VALUES (%s, %s, %s, 'started', %s, %s, %s)
               RETURNING id""",
            (SOURCE_NAME, file_path.name, checksum, len(all_rows), len(valid_rows), len(quarantined)),
        )
        run_id = cur.fetchone()[0]
        print(f"Import run ID: {run_id}")

        # 2. Clear staging table for this run
        cur.execute("DELETE FROM toilet_map_import_staging WHERE import_run_id = %s", (run_id,))

        # 3. Load valid rows into staging
        staging_inserts = 0
        for row in valid_rows:
            opening_hours = None
            if row.get("opening_hours"):
                try:
                    import json
                    opening_hours = json.dumps(json.loads(row["opening_hours"]))
                except Exception:
                    opening_hours = row["opening_hours"]

            raw_data = None
            if row.get("raw_data"):
                try:
                    import json
                    raw_data = row["raw_data"]
                except Exception:
                    raw_data = "{}"

            cur.execute(
                """INSERT INTO toilet_map_import_staging
                   (import_run_id, source_record_id, name, latitude, longitude,
                    address, postcode, town, is_accessible, has_baby_changing,
                    requires_radar_key, is_free, opening_hours, source_updated_at, raw_data)
                   VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s::jsonb, %s, %s::jsonb)""",
                (
                    run_id,
                    row["source_record_id"],
                    row.get("name"),
                    float(row["latitude"]),
                    float(row["longitude"]),
                    row.get("address", ""),
                    row.get("postcode", ""),
                    row.get("town", ""),
                    row.get("is_accessible"),
                    row.get("has_baby_changing"),
                    row.get("requires_radar_key"),
                    row.get("is_free"),
                    opening_hours,
                    row.get("source_updated_at"),
                    raw_data,
                ),
            )
            staging_inserts += 1

        print(f"Staged: {staging_inserts} rows")

        # 4. Upsert from staging into facilities + facility_sources
        inserted = 0
        updated = 0
        unchanged = 0

        cur.execute(
            """SELECT source_record_id, name, latitude, longitude, address, postcode, town,
                      is_accessible, has_baby_changing, requires_radar_key, is_free,
                      opening_hours, source_updated_at, raw_data
               FROM toilet_map_import_staging
               WHERE import_run_id = %s""",
            (run_id,),
        )

        staging_rows = cur.fetchall()
        col_names = [desc[0] for desc in cur.description]

        for staging_row in staging_rows:
            row_dict = dict(zip(col_names, staging_row))
            source_record_id = row_dict["source_record_id"]

            # Check if facility_sources already has this source record
            cur.execute(
                """SELECT fs.facility_id, f.id
                   FROM facility_sources fs
                   JOIN facilities f ON f.id = fs.facility_id
                   WHERE fs.source_name = %s AND fs.source_record_id = %s AND fs.is_current = true""",
                (SOURCE_NAME, source_record_id),
            )
            existing = cur.fetchone()

            if existing:
                facility_id = existing[0]
                # Update facility if source is newer
                cur.execute(
                    """UPDATE facilities SET
                         name = %s, address = %s, postcode = %s, town = %s,
                         is_accessible = %s, has_baby_changing = %s,
                         requires_radar_key = %s, is_free = %s,
                         open_hours = %s::jsonb,
                         publication_status = 'published',
                         verification_status = 'source_imported'
                       WHERE id = %s
                       AND (updated_at < %s OR updated_at IS NULL)""",
                    (
                        row_dict["name"],
                        row_dict["address"],
                        row_dict["postcode"],
                        row_dict["town"],
                        row_dict["is_accessible"],
                        row_dict["has_baby_changing"],
                        row_dict["requires_radar_key"],
                        row_dict["is_free"],
                        row_dict["opening_hours"],
                        facility_id,
                        row_dict["source_updated_at"] or datetime.now(timezone.utc).isoformat(),
                    ),
                )
                if cur.rowcount > 0:
                    updated += 1
                else:
                    unchanged += 1

                # Update facility_sources last_seen_at
                cur.execute(
                    """UPDATE facility_sources SET last_seen_at = NOW()
                       WHERE source_name = %s AND source_record_id = %s""",
                    (SOURCE_NAME, source_record_id),
                )
            else:
                # New facility
                cur.execute(
                    """INSERT INTO facilities
                       (name, address, latitude, longitude, postcode, town,
                        is_accessible, has_baby_changing, requires_radar_key, is_free,
                        open_hours, publication_status, verification_status, is_verified)
                       VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s::jsonb,
                               'published', 'source_imported', false)
                       RETURNING id""",
                    (
                        row_dict["name"],
                        row_dict["address"],
                        row_dict["latitude"],
                        row_dict["longitude"],
                        row_dict["postcode"],
                        row_dict["town"],
                        row_dict["is_accessible"],
                        row_dict["has_baby_changing"],
                        row_dict["requires_radar_key"],
                        row_dict["is_free"],
                        row_dict["opening_hours"],
                    ),
                )
                facility_id = cur.fetchone()[0]
                inserted += 1

                # Create facility_source record
                cur.execute(
                    """INSERT INTO facility_sources
                       (facility_id, import_run_id, source_name, source_record_id,
                        source_licence, source_updated_at, raw_data)
                       VALUES (%s, %s, %s, %s, %s, %s, %s::jsonb)""",
                    (
                        facility_id,
                        run_id,
                        SOURCE_NAME,
                        source_record_id,
                        SOURCE_LICENCE,
                        row_dict["source_updated_at"],
                        row_dict["raw_data"],
                    ),
                )

        # 5. Mark old source records as stale
        cur.execute(
            """UPDATE facility_sources SET is_current = false
               WHERE source_name = %s
               AND last_seen_at < NOW() - INTERVAL '7 days'
               AND is_current = true""",
            (SOURCE_NAME,),
        )
        marked_stale = cur.rowcount

        # Also mark facilities that weren't seen in this import as stale
        cur.execute(
            """UPDATE facilities SET verification_status = 'stale'
               WHERE verification_status = 'source_imported'
               AND id NOT IN (
                   SELECT DISTINCT facility_id FROM facility_sources
                   WHERE source_name = %s AND is_current = true
               )""",
            (SOURCE_NAME,),
        )
        facilities_marked_stale = cur.rowcount

        # 6. Complete import_runs record
        cur.execute(
            """UPDATE import_runs SET
               status = 'completed',
               completed_at = NOW(),
               rows_inserted = %s,
               rows_updated = %s,
               rows_unchanged = %s,
               rows_marked_stale = %s
               WHERE id = %s""",
            (inserted, updated, unchanged, marked_stale + facilities_marked_stale, run_id),
        )

        conn.commit()

        print(f"\n=== Import complete ===")
        print(f"Inserted:  {inserted}")
        print(f"Updated:   {updated}")
        print(f"Unchanged: {unchanged}")
        print(f"Stale:     {marked_stale + facilities_marked_stale}")
        print(f"Quarantined: {len(quarantined)}")

    except Exception as e:
        conn.rollback()
        # Mark run as failed
        try:
            cur.execute(
                "UPDATE import_runs SET status = 'failed', error_summary = %s, completed_at = NOW() WHERE id = %s",
                (str(e), run_id),
            )
            conn.commit()
        except Exception:
            pass
        print(f"ERROR: Import failed: {e}")
        sys.exit(1)
    finally:
        cur.close()
        conn.close()


def main():
    parser = argparse.ArgumentParser(description="Import normalised facility CSV into Supabase")
    parser.add_argument("--file", required=True, help="Path to normalised CSV file")
    parser.add_argument("--dry-run", action="store_true", help="Validate only, no database changes")
    parser.add_argument("--liverpool-only", action="store_true", help="Filter to Liverpool bounding box")
    parser.add_argument("--show-quarantined", action="store_true", help="Show quarantined row details")
    args = parser.parse_args()
    run_import(args)


if __name__ == "__main__":
    main()

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
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

import psycopg2
import psycopg2.extras
from dotenv import load_dotenv

load_dotenv()

DB_URL = os.getenv("SUPABASE_DB_URL")
SOURCE_NAME = "Toilet Map UK"
SOURCE_LICENCE = "CC-BY-4.0"
BATCH_SIZE = 500

LIVERPOOL_LAT_MIN = 53.3
LIVERPOOL_LAT_MAX = 53.5
LIVERPOOL_LNG_MIN = -3.0
LIVERPOOL_LNG_MAX = -2.8


def get_connection():
    if not DB_URL:
        print("ERROR: SUPABASE_DB_URL not set. See .env")
        sys.exit(1)
    return psycopg2.connect(DB_URL)


def compute_checksum(file_path: Path) -> str:
    return hashlib.sha256(file_path.read_bytes()).hexdigest()


def nullable_bool(val):
    if val is None or str(val).strip() == "":
        return None
    s = str(val).strip().lower()
    if s in ("true", "1", "yes"):
        return True
    if s in ("false", "0", "no"):
        return False
    return None


def nullable_str(val):
    if val is None or str(val).strip() == "":
        return None
    return str(val).strip()


def safe_json(val):
    """Ensure val is a valid JSON string for JSONB columns."""
    if val is None:
        return None
    if isinstance(val, (list, dict)):
        return json.dumps(val)
    if isinstance(val, str) and val.strip():
        try:
            json.loads(val)
            return val
        except (json.JSONDecodeError, TypeError):
            return None
    return None


def validate_row(row, row_num):
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


def prepare_row(row):
    """Convert a CSV row dict into a tuple for staging insert."""
    opening_hours_str = None
    if row.get("opening_hours"):
        try:
            opening_hours_str = json.dumps(json.loads(row["opening_hours"]))
        except Exception:
            opening_hours_str = row["opening_hours"]

    raw_data_str = row.get("raw_data") or "{}"

    return (
        row["source_record_id"],
        nullable_str(row.get("name")),
        float(row["latitude"]),
        float(row["longitude"]),
        nullable_str(row.get("address")),
        nullable_str(row.get("postcode")),
        nullable_str(row.get("town")),
        nullable_bool(row.get("is_accessible")),
        nullable_bool(row.get("has_baby_changing")),
        nullable_bool(row.get("requires_radar_key")),
        nullable_bool(row.get("is_free")),
        opening_hours_str,
        nullable_str(row.get("source_updated_at")),
        raw_data_str,
    )


STAGING_COLS = (
    "source_record_id", "name", "latitude", "longitude",
    "address", "postcode", "town", "is_accessible", "has_baby_changing",
    "requires_radar_key", "is_free", "opening_hours", "source_updated_at", "raw_data",
)


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

    with open(file_path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        all_rows = list(reader)

    print(f"Rows read: {len(all_rows)}")

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
        print("\n=== DRY RUN - no database changes ===")
        print(f"Would insert/update: {len(valid_rows)} facilities")
        print(f"Would quarantine: {len(quarantined)} rows")
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

        # 2. Load valid rows into staging using batch insert
        staging_tuples = [prepare_row(row) for row in valid_rows]

        insert_query = f"""
            INSERT INTO toilet_map_import_staging
               (import_run_id, {', '.join(STAGING_COLS)})
               VALUES %s
        """
        staging_args = [(run_id,) + t for t in staging_tuples]
        psycopg2.extras.execute_values(cur, insert_query, staging_args, page_size=BATCH_SIZE)
        print(f"Staged: {len(staging_tuples)} rows")

        # 3. Read staging rows back
        cur.execute(
            f"""SELECT source_record_id, name, latitude, longitude, address, postcode, town,
                       is_accessible, has_baby_changing, requires_radar_key, is_free,
                       opening_hours, source_updated_at, raw_data
                FROM toilet_map_import_staging
                WHERE import_run_id = %s""",
            (run_id,),
        )
        staging_rows = cur.fetchall()
        col_names = [desc[0] for desc in cur.description]

        # 4. Find which source_record_ids already exist
        source_ids = [dict(zip(col_names, r))["source_record_id"] for r in staging_rows]
        cur.execute(
            """SELECT source_record_id, facility_id FROM facility_sources
               WHERE source_name = %s AND source_record_id = ANY(%s) AND is_current = true""",
            (SOURCE_NAME, source_ids),
        )
        existing_map = dict(cur.fetchall())  # source_record_id -> facility_id

        # Separate into new vs existing
        new_rows = []
        update_rows = []
        for staging_row in staging_rows:
            row_dict = dict(zip(col_names, staging_row))
            oh = row_dict["opening_hours"]
            if isinstance(oh, (list, dict)):
                oh = json.dumps(oh)
            row_dict["opening_hours"] = oh

            rd = row_dict["raw_data"]
            if isinstance(rd, (list, dict)):
                rd = json.dumps(rd)
            row_dict["raw_data"] = rd

            if row_dict["source_record_id"] in existing_map:
                row_dict["_facility_id"] = existing_map[row_dict["source_record_id"]]
                update_rows.append(row_dict)
            else:
                new_rows.append(row_dict)

        print(f"New facilities: {len(new_rows)}, Existing to update: {len(update_rows)}")

        # 5. Batch INSERT new facilities
        inserted = 0
        if new_rows:
            # Build batch inserts with source_record_id in VALUES so we can map back
            insert_template = """(%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s::jsonb, 'published', 'source_imported', false)"""

            new_source_to_facility = {}
            for i in range(0, len(new_rows), BATCH_SIZE):
                batch = new_rows[i:i + BATCH_SIZE]
                facility_values = []
                for r in batch:
                    facility_values.append((
                        r["name"] or "Unnamed Toilet",
                        r["address"] or "",
                        r["latitude"],
                        r["longitude"],
                        r["postcode"] or "",
                        r["town"] or "",
                        r["is_accessible"],
                        r["has_baby_changing"],
                        r["requires_radar_key"],
                        r["is_free"],
                        safe_json(r["opening_hours"]),
                    ))

                facility_insert_query = """
                    INSERT INTO facilities
                       (name, address, latitude, longitude, postcode, town,
                        is_accessible, has_baby_changing, requires_radar_key, is_free,
                        open_hours, publication_status, verification_status, is_verified)
                    VALUES %s
                    RETURNING id, name
                """
                psycopg2.extras.execute_values(
                    cur, facility_insert_query, facility_values,
                    page_size=BATCH_SIZE,
                    template=insert_template,
                )
                returned = cur.fetchall()
                for (fid, fname) in returned:
                    for r in batch:
                        if (r["name"] or "Unnamed Toilet") == fname and r["source_record_id"] not in new_source_to_facility:
                            new_source_to_facility[r["source_record_id"]] = fid
                            break

            inserted = len(new_source_to_facility)
            print(f"Inserted {inserted} facilities, mapped {len(new_source_to_facility)} source IDs")

            # Batch INSERT facility_sources for new facilities
            source_values = []
            now_iso = datetime.now(timezone.utc).isoformat()
            for r in new_rows:
                fid = new_source_to_facility.get(r["source_record_id"])
                if fid:
                    source_values.append((
                        fid,
                        run_id,
                        SOURCE_NAME,
                        r["source_record_id"],
                        SOURCE_LICENCE,
                        r["source_updated_at"] or now_iso,
                        safe_json(r["raw_data"]),
                    ))

            source_insert_query = """
                INSERT INTO facility_sources
                   (facility_id, import_run_id, source_name, source_record_id,
                    source_licence, source_updated_at, raw_data)
                VALUES %s
            """
            psycopg2.extras.execute_values(
                cur, source_insert_query, source_values,
                page_size=BATCH_SIZE,
                template="(%s, %s, %s, %s, %s, %s, %s::jsonb)",
            )

        # 6. Batch UPDATE existing facilities
        updated = 0
        unchanged = 0
        if update_rows:
            now_iso = datetime.now(timezone.utc).isoformat()
            for r in update_rows:
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
                        r["name"],
                        r["address"],
                        r["postcode"],
                        r["town"],
                        r["is_accessible"],
                        r["has_baby_changing"],
                        r["requires_radar_key"],
                        r["is_free"],
                        safe_json(r["opening_hours"]),
                        r["_facility_id"],
                        r["source_updated_at"] or now_iso,
                    ),
                )
                if cur.rowcount > 0:
                    updated += 1
                else:
                    unchanged += 1

            # Update facility_sources last_seen_at for existing
            existing_source_ids = [r["source_record_id"] for r in update_rows]
            cur.execute(
                """UPDATE facility_sources SET last_seen_at = NOW()
                   WHERE source_name = %s AND source_record_id = ANY(%s)""",
                (SOURCE_NAME, existing_source_ids),
            )

        # 7. Mark stale source records
        cur.execute(
            """UPDATE facility_sources SET is_current = false
               WHERE source_name = %s
               AND last_seen_at < NOW() - INTERVAL '7 days'
               AND is_current = true""",
            (SOURCE_NAME,),
        )
        marked_stale = cur.rowcount

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

        # 8. Complete import_runs record
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

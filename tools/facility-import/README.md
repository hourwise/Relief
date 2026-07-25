# Relief — Facility Importer

Staged ETL pipeline for importing UK public toilet data from the [Toilet Map UK](https://toiletmap.org.uk) dataset.

## Quick Start

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Configure database connection
cp .env.example .env
# Edit .env with your Supabase DB connection string

# 3. Download the dataset
python download_toilet_map.py data/toilet_map_uk.geojson

# 4. Normalise to CSV
python normalise_toilet_map.py data/toilet_map_uk.geojson data/normalised.csv

# 5. Dry-run (validate only, no DB changes)
python import_to_supabase.py --file data/normalised.csv --dry-run --liverpool-only

# 6. Live import (Liverpool only)
python import_to_supabase.py --file data/normalised.csv --liverpool-only

# 7. Full UK import (after Liverpool is verified)
python import_to_supabase.py --file data/normalised.csv
```

## How It Works

```
download → normalise → staging table → validate → upsert facilities → record stats
```

1. **Download** — Fetches the Toilet Map UK GeoJSON export
2. **Normalise** — Converts source fields to Relief fields, preserves unknowns as null
3. **Staging** — Loads normalised rows into `toilet_map_import_staging`
4. **Validate** — Rejects rows with missing IDs, invalid coordinates, or out-of-UK locations
5. **Upsert** — Creates new facilities or updates existing ones (matched by `source_name` + `source_record_id`)
6. **Provenance** — Records source attribution in `facility_sources`
7. **Stale detection** — Marks source records not seen in 7+ days as stale

## Key Properties

- **Idempotent** — Running the same import twice does not create duplicates
- **Safe** — Invalid records are quarantined, not silently inserted
- **Traceable** — Every import run is recorded in `import_runs` with checksums and counts
- **Attributed** — Each facility's source is tracked in `facility_sources`
- **Unknown-safe** — Missing boolean values are stored as `null`, not `false`

## Configuration

| Variable | Purpose |
|----------|---------|
| `SUPABASE_DB_URL` | PostgreSQL Direct connection string from Supabase Dashboard > Settings > Database > Connection string > URI (port 5432). Falls back to Session Pooler if IPv6 is unavailable. Do NOT use Transaction Pooler (port 6543). |
| `SUPABASE_SERVICE_ROLE_KEY` | Reserved for future use; currently all writes go through PostgreSQL |

**Important:** `SUPABASE_DB_URL` is a server-side secret. It must never appear in Expo client code or be prefixed with `EXPO_PUBLIC_`.

## Database Tables Used

| Table | Purpose |
|-------|---------|
| `toilet_map_import_staging` | Temporary staging area for normalised source rows |
| `facilities` | Core facility table (upserted from staging) |
| `facility_sources` | Source attribution and deduplication tracking |
| `import_runs` | Import execution log with counts and checksums |

## Important Notes

- The `toilet_map_import_staging` table is `UNLOGGED` for performance — it is truncated before each import run
- Imported records use `publication_status = 'published'` and `verification_status = 'source_imported'`
- Imported records are NOT marked as Relief-verified (`is_verified = false`)
- The service role key is never exposed to the Expo application
- This tool runs server-side only

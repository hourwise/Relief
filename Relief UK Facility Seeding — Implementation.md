# Relief UK Facility Seeding — Implementation Instructions

You are working in the `hourwise/Relief` repository.

Your task is to create a safe, repeatable UK public-toilet data import system for Relief.

Follow these instructions exactly. Do not redesign unrelated parts of the application.

## Main objective

Build a data importer that:

1. Tests with Liverpool data first.
2. Imports the Toilet Map UK dataset as the primary source.
3. Keeps source attribution and licensing information.
4. Does not falsely claim imported toilets are verified by Relief.
5. Can later import the complete UK dataset safely.
6. Can be run repeatedly without creating duplicates.
7. Does not overwrite Relief community corrections or reviews.

Do not import the whole UK until the Liverpool test has passed.

---

# Phase 1 — Inspect the current implementation

Before changing code:

1. Read:

   * `AGENTS.md`
   * `README.md`
   * `docs/CURRENT_STATE.md`
   * `docs/FEATURE_MATRIX.md`
   * `docs/PROPOSED_DATA_MODEL.md`
   * `docs/DECISIONS_NEEDED.md`
   * all Supabase migration files
   * `src/services/facilities.ts`
   * `src/types/index.ts`

2. Confirm the real `facilities` table columns from the migrations.

3. Check whether the remote development Supabase database matches the local migrations.

4. Do not assume PostGIS, indexes, policies, functions or migrations are working until verified.

5. Record any schema mismatch before continuing.

---

# Phase 2 — Fix the facility trust model

The current `is_verified` boolean is not enough.

Imported facilities must be visible in the app, but they must not be described as verified by Relief.

Create a new migration that adds these fields to `facilities`:

```sql
publication_status TEXT NOT NULL DEFAULT 'hidden'
  CHECK (publication_status IN (
    'published',
    'hidden',
    'under_review',
    'removed'
  ));

verification_status TEXT NOT NULL DEFAULT 'source_imported'
  CHECK (verification_status IN (
    'source_imported',
    'source_verified',
    'community_confirmed',
    'staff_verified',
    'disputed',
    'stale'
  ));

last_community_confirmed_at TIMESTAMPTZ;
last_staff_verified_at TIMESTAMPTZ;
```

Keep `is_verified` temporarily if existing code still depends on it, but treat it as a legacy field.

Do not mark imported records as Relief verified.

Imported records should normally use:

```text
publication_status = published
verification_status = source_imported
is_verified = false
```

Update facility-reading code so public facilities are selected using:

```text
publication_status = published
```

Do not require imported facilities to have:

```text
is_verified = true
```

Update Row Level Security so anonymous users can read published facilities but cannot write directly to the live `facilities` table.

---

# Phase 3 — Stop treating unknown data as false

Imported data frequently does not say whether a feature exists.

Unknown must not be stored as false.

Review these facility fields:

* `is_free`
* `is_accessible`
* `is_disabled_access`
* `has_baby_changing`
* `has_family_room`
* `is_gender_neutral`
* `is_single_occupancy`
* `is_24h`
* `has_wheelchair_access`
* `requires_radar_key`
* `has_adult_changing_place`
* `has_lift`
* `has_grab_rails`
* other imported amenity fields

Where practical, change imported-data boolean columns to nullable booleans:

```text
true = source says yes
false = source says no
null = source does not say
```

Do not use database defaults that turn missing source information into `true` or `false`.

In particular, missing fee information must not automatically mean the toilet is free.

Update TypeScript types to support `boolean | null` where the database allows unknown values.

Update the UI so it can display:

* Yes
* No
* Unknown
* Limited, where supported

Do not display unknown data as a confirmed negative.

---

# Phase 4 — Add source provenance tables

Create an `import_runs` table.

Suggested structure:

```sql
CREATE TABLE import_runs (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  source_name TEXT NOT NULL,
  source_file_name TEXT,
  source_checksum TEXT,
  status TEXT NOT NULL DEFAULT 'started',
  started_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  completed_at TIMESTAMPTZ,
  rows_received INTEGER NOT NULL DEFAULT 0,
  rows_valid INTEGER NOT NULL DEFAULT 0,
  rows_inserted INTEGER NOT NULL DEFAULT 0,
  rows_updated INTEGER NOT NULL DEFAULT 0,
  rows_unchanged INTEGER NOT NULL DEFAULT 0,
  rows_quarantined INTEGER NOT NULL DEFAULT 0,
  rows_marked_stale INTEGER NOT NULL DEFAULT 0,
  error_summary TEXT
);
```

Create a `facility_sources` table.

Suggested structure:

```sql
CREATE TABLE facility_sources (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  facility_id UUID REFERENCES facilities(id) ON DELETE CASCADE,
  import_run_id UUID REFERENCES import_runs(id),
  source_name TEXT NOT NULL,
  source_record_id TEXT NOT NULL,
  source_url TEXT,
  source_licence TEXT NOT NULL,
  source_updated_at TIMESTAMPTZ,
  first_seen_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  last_seen_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  is_current BOOLEAN NOT NULL DEFAULT true,
  raw_data JSONB,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  UNIQUE (source_name, source_record_id)
);
```

The unique source identity must be:

```text
source_name + source_record_id
```

Do not use rounded latitude and longitude as the main unique identifier.

Two toilets may legitimately exist very close together.

---

# Phase 5 — Add a staging table

Create a staging table for Toilet Map imports.

The staging table should contain normalised source fields, for example:

```sql
CREATE UNLOGGED TABLE toilet_map_import_staging (
  source_record_id TEXT NOT NULL,
  name TEXT,
  latitude DOUBLE PRECISION,
  longitude DOUBLE PRECISION,
  address TEXT,
  postcode TEXT,
  town TEXT,
  is_accessible BOOLEAN,
  has_baby_changing BOOLEAN,
  requires_radar_key BOOLEAN,
  is_free BOOLEAN,
  opening_hours JSONB,
  source_updated_at TIMESTAMPTZ,
  raw_data JSONB
);
```

Adjust field names to match the real Toilet Map dataset.

Do not insert downloaded source records straight into `facilities`.

The required flow is:

```text
download
→ normalise
→ staging table
→ validate
→ upsert source records
→ create or update facilities
→ record import statistics
```

Invalid records must be quarantined or rejected, not silently inserted.

Reject records with:

* missing source record ID;
* invalid latitude;
* invalid longitude;
* coordinates outside the expected UK area;
* clearly unusable names and addresses;
* malformed source values.

Keep the raw source row in `raw_data` where practical.

---

# Phase 6 — Create the importer

Create this directory:

```text
tools/facility-import/
```

Add:

```text
tools/facility-import/
  README.md
  requirements.txt
  download_toilet_map.py
  normalise_toilet_map.py
  import_to_supabase.py
```

Use Python for the importer.

The importer must:

1. Download or accept a local Toilet Map CSV/JSON file.
2. Calculate a checksum for the source file.
3. Create an `import_runs` record.
4. Convert source fields into Relief fields.
5. Preserve unknown values as null.
6. Load the normalised records into the staging table.
7. Validate coordinates and required values.
8. Upsert using `source_name` and `source_record_id`.
9. Avoid duplicate facilities.
10. Update `last_seen_at`.
11. Mark missing old source records as potentially stale rather than deleting them.
12. Complete the `import_runs` record with counts.
13. Return a non-zero exit code if the import fails.
14. Never expose the Supabase service role key to the Expo application.

Configuration must come from server-side environment variables.

For example:

```env
SUPABASE_DB_URL=
SUPABASE_SERVICE_ROLE_KEY=
```

Do not commit real secrets.

Add a safe `.env.example`.

---

# Phase 7 — Use safe bulk loading

Do not create one enormous SQL file containing thousands of individual `INSERT` statements.

Prefer one of these:

1. PostgreSQL `COPY` into the staging table.
2. Supabase server-side batch upserts.
3. Batches of approximately 500–1,000 records if direct bulk loading is unavailable.

The process must be restartable.

Running the same import file twice must not create duplicate facilities or duplicate source rows.

Add a dry-run mode:

```bash
python import_to_supabase.py --file normalised.csv --dry-run
```

Dry-run must:

* parse the file;
* validate records;
* report proposed inserts and updates;
* make no database changes.

---

# Phase 8 — Add PostGIS nearest-facility support

Check whether PostGIS is enabled.

If it is not enabled, add a migration to enable it.

Add a geography point generated from longitude and latitude:

```sql
ALTER TABLE facilities
ADD COLUMN IF NOT EXISTS location geography(Point, 4326)
GENERATED ALWAYS AS (
  ST_SetSRID(
    ST_MakePoint(longitude, latitude),
    4326
  )::geography
) STORED;
```

Add a spatial index:

```sql
CREATE INDEX IF NOT EXISTS facilities_location_gix
ON facilities
USING GIST (location);
```

Create a database function for nearby facilities.

The function must:

* accept latitude;
* accept longitude;
* accept radius in metres;
* return only published facilities;
* calculate real distance using PostGIS;
* order by distance;
* support a sensible result limit.

Update `fetchClosestFacility()` so it uses the PostGIS function.

Do not determine the nearest toilet by:

* ordering by rating first;
* downloading only 20 rows;
* using simple Euclidean latitude/longitude calculations.

Keep existing code working until the new database function is tested.

---

# Phase 9 — Liverpool-only test import

Before importing the UK:

1. Filter the source dataset to Liverpool or a small Merseyside test area.
2. Import approximately 50–200 facilities.
3. Do not use fake facility records if real source records are available.
4. Confirm the following:

   * records appear on the map;
   * records appear in nearby searches;
   * postcode and town searches work;
   * nearest-facility search returns the nearest toilet;
   * unknown accessibility values display as unknown;
   * imported facilities say they are source imported;
   * imported facilities do not say they are Relief verified;
   * source attribution is visible;
   * duplicate imports do not create duplicates;
   * anonymous users can read published facilities;
   * anonymous users cannot write facilities;
   * authenticated users cannot insert directly into live facilities;
   * community submissions still use the moderation queue.

Add tests for the importer where practical.

At minimum, test:

* valid row;
* missing source ID;
* invalid coordinate;
* unknown boolean value;
* repeated import;
* changed source record;
* missing record becoming stale;
* two nearby but genuinely separate toilets.

---

# Phase 10 — Update the Relief interface

On imported facility details, display a source label such as:

```text
Source: Toilet Map
Not yet confirmed by the Relief community
```

Where licence attribution is required, include the correct attribution in an appropriate app information or attribution screen.

Do not display:

```text
Verified by Relief
```

unless:

```text
verification_status = community_confirmed
```

or:

```text
verification_status = staff_verified
```

If a user confirms a facility, update the community confirmation timestamp.

Do not overwrite the original source information.

Community corrections must be stored separately and reviewed before replacing canonical data.

---

# Phase 11 — Full UK import

Only proceed after the Liverpool import passes all checks.

For the complete UK import:

1. Download a fresh Toilet Map dataset.
2. Record its filename, checksum and retrieval date.
3. Run dry-run.
4. Review rejected and duplicate candidates.
5. Run the real import.
6. Confirm row counts.
7. Verify map performance.
8. Verify nearby-query performance.
9. Verify indexes are being used.
10. Confirm no community data was overwritten.
11. Confirm required attribution is present.

Do not divide the import council by council unless a source-specific council adapter is being added.

The national Toilet Map dataset should be the main seed.

Council datasets and OpenStreetMap should be later enrichment sources.

---

# Phase 12 — Sources that must not be used incorrectly

Do not use Google Places to create Relief’s permanent toilet database.

Google Maps may be used to display the map, but Google Places data must not be permanently copied into Relief unless its terms explicitly permit that exact storage.

Do not begin with OpenStreetMap Overpass requests for the entire UK.

OpenStreetMap may be added later as a separate source adapter.

If OSM is added:

* preserve OSM source IDs;
* preserve ODbL attribution;
* keep OSM-derived data identifiable;
* do not silently mix OSM data with proprietary Relief community data;
* document the licensing consequences.

---

# Phase 13 — Documentation

Update:

* `README.md`
* `docs/CURRENT_STATE.md`
* `docs/FEATURE_MATRIX.md`
* `docs/PROPOSED_DATA_MODEL.md`
* `docs/DECISIONS_NEEDED.md`
* the new importer README

Update D04 to state:

```text
Primary source: Toilet Map UK dataset.
Initial validation area: Liverpool.
Import method: staged, repeatable ETL.
Secondary sources: OSM and reviewed council open data.
Verification: imported records are not Relief verified until confirmed.
```

Use the repository’s approved status vocabulary.

Do not describe the national import as complete until it has run successfully and been tested in the application.

---

# Required implementation order

Complete work in this order:

1. Inspect and report schema mismatches.
2. Add trust and provenance migrations.
3. Add staging and import-run tables.
4. Build importer with dry-run support.
5. Add PostGIS nearest-facility function.
6. Update app queries and TypeScript types.
7. Import Liverpool test data.
8. Run tests and document results.
9. Fix discovered problems.
10. Import the full UK dataset.
11. Update project documentation.

Do not skip directly to Step 10.

---

# Completion report

When finished, report:

1. Files created.
2. Files changed.
3. Migrations added.
4. Exact importer command.
5. Liverpool rows received.
6. Liverpool rows inserted.
7. Rows updated.
8. Rows rejected.
9. Duplicate candidates.
10. Tests run.
11. Test results.
12. Remaining risks.
13. Whether full UK import was performed.
14. Evidence that repeated imports do not create duplicates.
15. Evidence that anonymous users cannot write live facility data.

Do not claim success without showing the relevant evidence.

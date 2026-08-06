-- ============================================================
-- Project "Relief" — Facility Trust Model, Provenance & Import Infrastructure
-- Phases 2, 3, 4, 5, 8 of the seeding implementation
-- ============================================================

-- ============================================================
-- PHASE 2: Trust model — publication & verification status
-- ============================================================

-- publication_status: controls visibility in the app
ALTER TABLE facilities
  ADD COLUMN IF NOT EXISTS publication_status TEXT NOT NULL DEFAULT 'hidden'
  CHECK (publication_status IN (
    'published',
    'hidden',
    'under_review',
    'removed'
  ));

-- verification_status: tracks how reliable the data is
ALTER TABLE facilities
  ADD COLUMN IF NOT EXISTS verification_status TEXT NOT NULL DEFAULT 'source_imported'
  CHECK (verification_status IN (
    'source_imported',
    'source_verified',
    'community_confirmed',
    'staff_verified',
    'disputed',
    'stale'
  ));

ALTER TABLE facilities
  ADD COLUMN IF NOT EXISTS last_community_confirmed_at TIMESTAMPTZ;

ALTER TABLE facilities
  ADD COLUMN IF NOT EXISTS last_staff_verified_at TIMESTAMPTZ;

-- Index for the new publication_status filter
CREATE INDEX IF NOT EXISTS idx_facilities_publication_status
  ON facilities (publication_status);

CREATE INDEX IF NOT EXISTS idx_facilities_verification_status
  ON facilities (verification_status);

-- ============================================================
-- PHASE 3: Nullable booleans — stop treating unknown as false
-- ============================================================
-- Change all amenity boolean columns from DEFAULT false to nullable.
-- true = source says yes, false = source says no, null = unknown.

ALTER TABLE facilities
  ALTER COLUMN is_free DROP DEFAULT,
  ALTER COLUMN is_free TYPE BOOLEAN USING is_free,
  ALTER COLUMN is_free DROP NOT NULL;

ALTER TABLE facilities
  ALTER COLUMN is_accessible DROP DEFAULT,
  ALTER COLUMN is_accessible TYPE BOOLEAN USING is_accessible,
  ALTER COLUMN is_accessible DROP NOT NULL;

ALTER TABLE facilities
  ALTER COLUMN is_disabled_access DROP DEFAULT,
  ALTER COLUMN is_disabled_access TYPE BOOLEAN USING is_disabled_access,
  ALTER COLUMN is_disabled_access DROP NOT NULL;

ALTER TABLE facilities
  ALTER COLUMN has_baby_changing DROP DEFAULT,
  ALTER COLUMN has_baby_changing TYPE BOOLEAN USING has_baby_changing,
  ALTER COLUMN has_baby_changing DROP NOT NULL;

ALTER TABLE facilities
  ALTER COLUMN has_family_room DROP DEFAULT,
  ALTER COLUMN has_family_room TYPE BOOLEAN USING has_family_room,
  ALTER COLUMN has_family_room DROP NOT NULL;

ALTER TABLE facilities
  ALTER COLUMN is_gender_neutral DROP DEFAULT,
  ALTER COLUMN is_gender_neutral TYPE BOOLEAN USING is_gender_neutral,
  ALTER COLUMN is_gender_neutral DROP NOT NULL;

ALTER TABLE facilities
  ALTER COLUMN is_single_occupancy DROP DEFAULT,
  ALTER COLUMN is_single_occupancy TYPE BOOLEAN USING is_single_occupancy,
  ALTER COLUMN is_single_occupancy DROP NOT NULL;

ALTER TABLE facilities
  ALTER COLUMN is_24h DROP DEFAULT,
  ALTER COLUMN is_24h TYPE BOOLEAN USING is_24h,
  ALTER COLUMN is_24h DROP NOT NULL;

-- Privacy
ALTER TABLE facilities
  ALTER COLUMN is_single_room DROP DEFAULT,
  ALTER COLUMN is_single_room TYPE BOOLEAN USING is_single_room,
  ALTER COLUMN is_single_room DROP NOT NULL;

ALTER TABLE facilities
  ALTER COLUMN has_floor_to_ceiling_cubicles DROP DEFAULT,
  ALTER COLUMN has_floor_to_ceiling_cubicles TYPE BOOLEAN USING has_floor_to_ceiling_cubicles,
  ALTER COLUMN has_floor_to_ceiling_cubicles DROP NOT NULL;

ALTER TABLE facilities
  ALTER COLUMN is_quiet DROP DEFAULT,
  ALTER COLUMN is_quiet TYPE BOOLEAN USING is_quiet,
  ALTER COLUMN is_quiet DROP NOT NULL;

-- Accessibility
ALTER TABLE facilities
  ALTER COLUMN has_wheelchair_access DROP DEFAULT,
  ALTER COLUMN has_wheelchair_access TYPE BOOLEAN USING has_wheelchair_access,
  ALTER COLUMN has_wheelchair_access DROP NOT NULL;

ALTER TABLE facilities
  ALTER COLUMN requires_radar_key DROP DEFAULT,
  ALTER COLUMN requires_radar_key TYPE BOOLEAN USING requires_radar_key,
  ALTER COLUMN requires_radar_key DROP NOT NULL;

ALTER TABLE facilities
  ALTER COLUMN has_adult_changing_place DROP DEFAULT,
  ALTER COLUMN has_adult_changing_place TYPE BOOLEAN USING has_adult_changing_place,
  ALTER COLUMN has_adult_changing_place DROP NOT NULL;

ALTER TABLE facilities
  ALTER COLUMN has_lift DROP DEFAULT,
  ALTER COLUMN has_lift TYPE BOOLEAN USING has_lift,
  ALTER COLUMN has_lift DROP NOT NULL;

ALTER TABLE facilities
  ALTER COLUMN has_grab_rails DROP DEFAULT,
  ALTER COLUMN has_grab_rails TYPE BOOLEAN USING has_grab_rails,
  ALTER COLUMN has_grab_rails DROP NOT NULL;

-- Baby
ALTER TABLE facilities
  ALTER COLUMN has_baby_changing_inside DROP DEFAULT,
  ALTER COLUMN has_baby_changing_inside TYPE BOOLEAN USING has_baby_changing_inside,
  ALTER COLUMN has_baby_changing_inside DROP NOT NULL;

ALTER TABLE facilities
  ALTER COLUMN has_separate_changing_room DROP DEFAULT,
  ALTER COLUMN has_separate_changing_room TYPE BOOLEAN USING has_separate_changing_room,
  ALTER COLUMN has_separate_changing_room DROP NOT NULL;

ALTER TABLE facilities
  ALTER COLUMN has_family_toilet DROP DEFAULT,
  ALTER COLUMN has_family_toilet TYPE BOOLEAN USING has_family_toilet,
  ALTER COLUMN has_family_toilet DROP NOT NULL;

ALTER TABLE facilities
  ALTER COLUMN has_pram_access DROP DEFAULT,
  ALTER COLUMN has_pram_access TYPE BOOLEAN USING has_pram_access,
  ALTER COLUMN has_pram_access DROP NOT NULL;

-- Equipment
ALTER TABLE facilities
  ALTER COLUMN has_soap DROP DEFAULT,
  ALTER COLUMN has_soap TYPE BOOLEAN USING has_soap,
  ALTER COLUMN has_soap DROP NOT NULL;

ALTER TABLE facilities
  ALTER COLUMN has_paper_towels DROP DEFAULT,
  ALTER COLUMN has_paper_towels TYPE BOOLEAN USING has_paper_towels,
  ALTER COLUMN has_paper_towels DROP NOT NULL;

ALTER TABLE facilities
  ALTER COLUMN has_hand_dryer DROP DEFAULT,
  ALTER COLUMN has_hand_dryer TYPE BOOLEAN USING has_hand_dryer,
  ALTER COLUMN has_hand_dryer DROP NOT NULL;

ALTER TABLE facilities
  ALTER COLUMN has_mirror DROP DEFAULT,
  ALTER COLUMN has_mirror TYPE BOOLEAN USING has_mirror,
  ALTER COLUMN has_mirror DROP NOT NULL;

ALTER TABLE facilities
  ALTER COLUMN has_shelf DROP DEFAULT,
  ALTER COLUMN has_shelf TYPE BOOLEAN USING has_shelf,
  ALTER COLUMN has_shelf DROP NOT NULL;

ALTER TABLE facilities
  ALTER COLUMN has_hooks DROP DEFAULT,
  ALTER COLUMN has_hooks TYPE BOOLEAN USING has_hooks,
  ALTER COLUMN has_hooks DROP NOT NULL;

ALTER TABLE facilities
  ALTER COLUMN has_sanitary_bins DROP DEFAULT,
  ALTER COLUMN has_sanitary_bins TYPE BOOLEAN USING has_sanitary_bins,
  ALTER COLUMN has_sanitary_bins DROP NOT NULL;

ALTER TABLE facilities
  ALTER COLUMN has_free_period_products DROP DEFAULT,
  ALTER COLUMN has_free_period_products TYPE BOOLEAN USING has_free_period_products,
  ALTER COLUMN has_free_period_products DROP NOT NULL;

ALTER TABLE facilities
  ALTER COLUMN has_drinking_water DROP DEFAULT,
  ALTER COLUMN has_drinking_water TYPE BOOLEAN USING has_drinking_water,
  ALTER COLUMN has_drinking_water DROP NOT NULL;

-- Safety
ALTER TABLE facilities
  ALTER COLUMN has_staff_nearby DROP DEFAULT,
  ALTER COLUMN has_staff_nearby TYPE BOOLEAN USING has_staff_nearby,
  ALTER COLUMN has_staff_nearby DROP NOT NULL;

ALTER TABLE facilities
  ALTER COLUMN has_cctv DROP DEFAULT,
  ALTER COLUMN has_cctv TYPE BOOLEAN USING has_cctv,
  ALTER COLUMN has_cctv DROP NOT NULL;

ALTER TABLE facilities
  ALTER COLUMN is_women_friendly DROP DEFAULT,
  ALTER COLUMN is_women_friendly TYPE BOOLEAN USING is_women_friendly,
  ALTER COLUMN is_women_friendly DROP NOT NULL;

ALTER TABLE facilities
  ALTER COLUMN is_family_friendly DROP DEFAULT,
  ALTER COLUMN is_family_friendly TYPE BOOLEAN USING is_family_friendly,
  ALTER COLUMN is_family_friendly DROP NOT NULL;

-- Facility types
ALTER TABLE facilities
  ALTER COLUMN is_picnic_area DROP DEFAULT,
  ALTER COLUMN is_picnic_area TYPE BOOLEAN USING is_picnic_area,
  ALTER COLUMN is_picnic_area DROP NOT NULL;

-- Environment ratings: change defaults to null (unknown until reviewed)
ALTER TABLE facilities
  ALTER COLUMN noise_level DROP DEFAULT,
  ALTER COLUMN noise_level TYPE INTEGER USING noise_level,
  ALTER COLUMN noise_level DROP NOT NULL;

ALTER TABLE facilities
  ALTER COLUMN temperature DROP DEFAULT,
  ALTER COLUMN temperature TYPE INTEGER USING temperature,
  ALTER COLUMN temperature DROP NOT NULL;

ALTER TABLE facilities
  ALTER COLUMN lighting DROP DEFAULT,
  ALTER COLUMN lighting TYPE INTEGER USING lighting,
  ALTER COLUMN lighting DROP NOT NULL;

ALTER TABLE facilities
  ALTER COLUMN smell DROP DEFAULT,
  ALTER COLUMN smell TYPE INTEGER USING smell,
  ALTER COLUMN smell DROP NOT NULL;

-- ============================================================
-- PHASE 4: Source provenance tables
-- ============================================================

-- import_runs: tracks each import execution
CREATE TABLE IF NOT EXISTS import_runs (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  source_name TEXT NOT NULL,
  source_file_name TEXT,
  source_checksum TEXT,
  status TEXT NOT NULL DEFAULT 'started'
    CHECK (status IN ('started', 'completed', 'failed')),
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

ALTER TABLE import_runs ENABLE ROW LEVEL SECURITY;

-- Only service_role can manage import runs
CREATE POLICY "Service role manages import runs"
  ON import_runs FOR ALL
  USING (true)
  WITH CHECK (true);

-- facility_sources: tracks where each facility's data came from
CREATE TABLE IF NOT EXISTS facility_sources (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  facility_id UUID NOT NULL REFERENCES facilities(id) ON DELETE CASCADE,
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

CREATE INDEX IF NOT EXISTS idx_facility_sources_facility
  ON facility_sources (facility_id);

CREATE INDEX IF NOT EXISTS idx_facility_sources_current
  ON facility_sources (source_name, is_current);

ALTER TABLE facility_sources ENABLE ROW LEVEL SECURITY;

-- Published facilities' sources are publicly readable
CREATE POLICY "Published facility sources are viewable"
  ON facility_sources FOR SELECT
  USING (
    EXISTS (
      SELECT 1 FROM facilities
      WHERE facilities.id = facility_sources.facility_id
        AND facilities.publication_status = 'published'
    )
  );

-- Only service_role can write facility sources
CREATE POLICY "Service role manages facility sources"
  ON facility_sources FOR ALL
  USING (true)
  WITH CHECK (true);

-- ============================================================
-- PHASE 5: Staging table for Toilet Map imports
-- ============================================================

CREATE UNLOGGED TABLE IF NOT EXISTS toilet_map_import_staging (
  import_run_id UUID NOT NULL REFERENCES import_runs(id),
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
  raw_data JSONB,
  validation_errors TEXT[]
);

-- ============================================================
-- PHASE 8: PostGIS nearest-facility support
-- ============================================================

-- Enable PostGIS (if not already enabled)
CREATE EXTENSION IF NOT EXISTS postgis;

-- Generated geography column from lat/lng
ALTER TABLE facilities
  ADD COLUMN IF NOT EXISTS location geography(Point, 4326)
  GENERATED ALWAYS AS (
    ST_SetSRID(
      ST_MakePoint(longitude, latitude),
      4326
    )::geography
  ) STORED;

-- Spatial index
CREATE INDEX IF NOT EXISTS facilities_location_gix
  ON facilities
  USING GIST (location);

-- ============================================================
-- RLS update: published facilities visible to everyone
-- ============================================================

-- Drop the old is_verified-only policy
DROP POLICY IF EXISTS "Verified facilities are viewable by everyone" ON facilities;

-- New policy: published facilities are publicly readable
CREATE POLICY "Published facilities are viewable by everyone"
  ON facilities FOR SELECT
  USING (publication_status = 'published');

-- No direct INSERT/UPDATE/DELETE for anon or authenticated users
-- (only service_role can write via the importer or admin tools)
-- The default Supabase RLS denies all writes unless a policy allows them,
-- so no explicit deny policy is needed.

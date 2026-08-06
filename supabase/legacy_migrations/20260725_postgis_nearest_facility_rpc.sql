-- ============================================================
-- Project "Relief" — PostGIS Nearest-Facility RPC
-- ============================================================
-- Adds find_nearest_facilities() for accurate server-side
-- nearest-facility lookup used by "Need One Now".
--
-- Prerequisites (already applied by prior migrations):
--   CREATE EXTENSION IF NOT EXISTS postgis;
--   facilities.location geography(Point, 4326) generated column
--   facilities_location_gix GiST index
--   idx_facilities_publication_status index
-- ============================================================

-- Drop prior version if re-running during development
DROP FUNCTION IF EXISTS find_nearest_facilities(
  double precision, double precision, integer, integer
);

CREATE OR REPLACE FUNCTION find_nearest_facilities(
  user_latitude  double precision,
  user_longitude double precision,
  search_radius_metres integer DEFAULT 5000,
  result_limit        integer DEFAULT 1
)
RETURNS TABLE (
  facility_id     uuid,
  name            text,
  address         text,
  latitude        double precision,
  longitude       double precision,
  postcode        text,
  town            text,
  country         text,
  photos          text[],
  open_hours      jsonb,
  is_free         boolean,
  price_note      text,
  access_notes    text,
  last_verified_at timestamptz,
  is_accessible   boolean,
  is_disabled_access boolean,
  has_baby_changing  boolean,
  has_family_room    boolean,
  is_gender_neutral  boolean,
  is_single_occupancy boolean,
  is_24h           boolean,
  is_single_room   boolean,
  has_floor_to_ceiling_cubicles boolean,
  is_quiet         boolean,
  has_wheelchair_access boolean,
  requires_radar_key   boolean,
  has_adult_changing_place boolean,
  has_lift          boolean,
  has_grab_rails    boolean,
  has_baby_changing_inside boolean,
  has_separate_changing_room boolean,
  has_family_toilet boolean,
  has_pram_access   boolean,
  has_soap          boolean,
  has_paper_towels  boolean,
  has_hand_dryer    boolean,
  has_mirror        boolean,
  has_shelf         boolean,
  has_hooks         boolean,
  has_sanitary_bins boolean,
  has_free_period_products boolean,
  has_drinking_water boolean,
  noise_level       integer,
  temperature       integer,
  lighting          integer,
  smell             integer,
  has_staff_nearby  boolean,
  has_cctv          boolean,
  is_women_friendly boolean,
  is_family_friendly boolean,
  is_water_refill_station boolean,
  is_shower_facility     boolean,
  is_breastfeeding_room  boolean,
  is_rest_area           boolean,
  is_changing_place      boolean,
  is_ev_charging         boolean,
  is_picnic_area         boolean,
  overall_score     double precision,
  cleanliness_rating double precision,
  privacy_rating    double precision,
  accessibility_rating double precision,
  safety_rating     double precision,
  noise_rating      double precision,
  environment_rating double precision,
  publication_status text,
  verification_status text,
  last_community_confirmed_at timestamptz,
  last_staff_verified_at timestamptz,
  created_at        timestamptz,
  updated_at        timestamptz,
  created_by        uuid,
  is_verified       boolean,
  field_provenance  jsonb,
  distance_metres   double precision
)
LANGUAGE plpgsql
STABLE
SECURITY INVOKER
SET search_path = public
AS $$
BEGIN
  -- ── Input validation ──────────────────────────────────────
  IF user_latitude IS NULL OR user_latitude < -90 OR user_latitude > 90 THEN
    RAISE EXCEPTION 'Invalid latitude: %. Must be between -90 and 90.', user_latitude;
  END IF;

  IF user_longitude IS NULL OR user_longitude < -180 OR user_longitude > 180 THEN
    RAISE EXCEPTION 'Invalid longitude: %. Must be between -180 and 180.', user_longitude;
  END IF;

  IF search_radius_metres IS NULL OR search_radius_metres <= 0 THEN
    RAISE EXCEPTION 'Invalid search_radius_metres: %. Must be positive.', search_radius_metres;
  END IF;

  IF result_limit IS NULL OR result_limit <= 0 THEN
    RAISE EXCEPTION 'Invalid result_limit: %. Must be positive.', result_limit;
  END IF;

  -- ── Query ─────────────────────────────────────────────────
  RETURN QUERY
  SELECT
    f.id,
    f.name,
    f.address,
    f.latitude,
    f.longitude,
    f.postcode,
    f.town,
    f.country,
    f.photos,
    f.open_hours,
    f.is_free,
    f.price_note,
    f.access_notes,
    f.last_verified_at,
    f.is_accessible,
    f.is_disabled_access,
    f.has_baby_changing,
    f.has_family_room,
    f.is_gender_neutral,
    f.is_single_occupancy,
    f.is_24h,
    f.is_single_room,
    f.has_floor_to_ceiling_cubicles,
    f.is_quiet,
    f.has_wheelchair_access,
    f.requires_radar_key,
    f.has_adult_changing_place,
    f.has_lift,
    f.has_grab_rails,
    f.has_baby_changing_inside,
    f.has_separate_changing_room,
    f.has_family_toilet,
    f.has_pram_access,
    f.has_soap,
    f.has_paper_towels,
    f.has_hand_dryer,
    f.has_mirror,
    f.has_shelf,
    f.has_hooks,
    f.has_sanitary_bins,
    f.has_free_period_products,
    f.has_drinking_water,
    f.noise_level,
    f.temperature,
    f.lighting,
    f.smell,
    f.has_staff_nearby,
    f.has_cctv,
    f.is_women_friendly,
    f.is_family_friendly,
    f.is_water_refill_station,
    f.is_shower_facility,
    f.is_breastfeeding_room,
    f.is_rest_area,
    f.is_changing_place,
    f.is_ev_charging,
    f.is_picnic_area,
    f.overall_score,
    f.cleanliness_rating,
    f.privacy_rating,
    f.accessibility_rating,
    f.safety_rating,
    f.noise_rating,
    f.environment_rating,
    f.publication_status,
    f.verification_status,
    f.last_community_confirmed_at,
    f.last_staff_verified_at,
    f.created_at,
    f.updated_at,
    f.created_by,
    f.is_verified,
    f.field_provenance,
    ST_Distance(
      f.location,
      ST_SetSRID(ST_MakePoint(user_longitude, user_latitude), 4326)::geography
    ) AS distance_metres
  FROM facilities f
  WHERE f.publication_status = 'published'
    AND ST_DWithin(
          f.location,
          ST_SetSRID(ST_MakePoint(user_longitude, user_latitude), 4326)::geography,
          search_radius_metres
        )
  ORDER BY
    distance_metres ASC,
    f.name ASC           -- stable tiebreaker
  LIMIT result_limit;
END;
$$;

-- ============================================================
-- GRANT EXECUTE
-- ============================================================
-- Allow both anon (unauthenticated "Need One Now") and
-- authenticated users to call this function.
-- RLS on the facilities table still applies via SECURITY INVOKER.

GRANT EXECUTE ON FUNCTION find_nearest_facilities(
  double precision, double precision, integer, integer
) TO anon;

GRANT EXECUTE ON FUNCTION find_nearest_facilities(
  double precision, double precision, integer, integer
) TO authenticated;

-- ============================================================
-- VERIFICATION QUERIES (run manually in Supabase SQL Editor)
-- ============================================================

-- 1. Confirm PostGIS is enabled
-- SELECT PostGIS_Version();

-- 2. Confirm location column exists and is populated
-- SELECT count(*) AS total,
--        count(location) AS has_location
-- FROM facilities
-- WHERE publication_status = 'published';

-- 3. Confirm GiST index exists
-- SELECT indexname, indexdef
-- FROM pg_indexes
-- WHERE tablename = 'facilities' AND indexname = 'facilities_location_gix';

-- 4. Test nearest to Liverpool city centre (53.4084, -2.9916)
-- SELECT facility_id, name, distance_metres
-- FROM find_nearest_facilities(53.4084, -2.9916, 5000, 3);

-- 5. EXPLAIN ANALYSE to confirm index usage
-- EXPLAIN ANALYSE
-- SELECT f.id, f.name,
--   ST_Distance(f.location,
--     ST_SetSRID(ST_MakePoint(-2.9916, 53.4084), 4326)::geography
--   ) AS distance_metres
-- FROM facilities f
-- WHERE f.publication_status = 'published'
--   AND ST_DWithin(f.location,
--     ST_SetSRID(ST_MakePoint(-2.9916, 53.4084), 4326)::geography,
--     5000
--   )
-- ORDER BY distance_metres ASC
-- LIMIT 1;

-- 6. Test input validation (should raise exception)
-- SELECT * FROM find_nearest_facilities(999, -2.9916, 5000, 1);
-- SELECT * FROM find_nearest_facilities(53.4084, -2.9916, -1, 1);

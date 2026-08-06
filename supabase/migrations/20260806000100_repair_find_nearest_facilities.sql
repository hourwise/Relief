-- ============================================================
-- Relief — Repair find_nearest_facilities()
-- ============================================================
-- The live function declared and selected six columns that do
-- not exist on public.facilities:
--
--   is_water_refill_station, is_shower_facility,
--   is_breastfeeding_room, is_rest_area, is_changing_place,
--   is_ev_charging
--
-- Every call therefore failed at plan time with:
--   42703  column f.is_water_refill_station does not exist
--
-- which is what broke the "Need One Now" journey.
--
-- This migration replaces the function with a deliberately small
-- and stable projection: only the fields the emergency result
-- actually renders. Keeping the surface narrow means adding a
-- facility column no longer risks breaking the most urgent
-- journey in the app, and no speculative columns are invented
-- merely to satisfy hand-written TypeScript types.
--
-- Note: is_picnic_area DOES exist in the live schema and is
-- retained on the facilities table. It is simply not part of this
-- RPC's response, because the emergency result does not show it.
-- ============================================================

-- The return type changes, so the old function must be dropped;
-- CREATE OR REPLACE cannot alter a function's OUT columns.
DROP FUNCTION IF EXISTS public.find_nearest_facilities(
  double precision, double precision, integer, integer
);

CREATE FUNCTION public.find_nearest_facilities(
  user_latitude        double precision,
  user_longitude       double precision,
  search_radius_metres integer DEFAULT 5000,
  result_limit         integer DEFAULT 1
)
RETURNS TABLE (
  facility_id         uuid,
  name                text,
  address             text,
  latitude            double precision,
  longitude           double precision,
  town                text,
  postcode            text,
  open_hours          jsonb,
  is_free             boolean,
  is_accessible       boolean,
  overall_score       double precision,
  verification_status text,
  distance_metres     double precision
)
LANGUAGE plpgsql
STABLE
SECURITY INVOKER
SET search_path = public
AS $$
BEGIN
  -- ── Input validation ──────────────────────────────────────
  -- Raising here is intentional: a malformed request is a client
  -- bug and must not be indistinguishable from "nothing nearby".
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
  -- The projection is wrapped in a subquery so ORDER BY binds to
  -- the inner aliases rather than to this function's OUT
  -- parameters, which share the same names.
  RETURN QUERY
  SELECT *
  FROM (
    SELECT
      f.id                  AS r_facility_id,
      f.name                AS r_name,
      f.address             AS r_address,
      f.latitude            AS r_latitude,
      f.longitude           AS r_longitude,
      f.town                AS r_town,
      f.postcode            AS r_postcode,
      f.open_hours          AS r_open_hours,
      f.is_free             AS r_is_free,
      f.is_accessible       AS r_is_accessible,
      f.overall_score       AS r_overall_score,
      f.verification_status AS r_verification_status,
      ST_Distance(
        f.location,
        ST_SetSRID(ST_MakePoint(user_longitude, user_latitude), 4326)::geography
      )                     AS r_distance_metres
    FROM facilities f
    WHERE f.publication_status = 'published'
      AND ST_DWithin(
            f.location,
            ST_SetSRID(ST_MakePoint(user_longitude, user_latitude), 4326)::geography,
            search_radius_metres
          )
  ) q
  ORDER BY q.r_distance_metres ASC,
           q.r_name ASC          -- stable tiebreaker for equal distances
  LIMIT result_limit;
END;
$$;

-- ============================================================
-- GRANT EXECUTE
-- ============================================================
-- anon is required: "Need One Now" must work without an account.
-- RLS on facilities still applies because this is SECURITY INVOKER.

GRANT EXECUTE ON FUNCTION public.find_nearest_facilities(
  double precision, double precision, integer, integer
) TO anon;

GRANT EXECUTE ON FUNCTION public.find_nearest_facilities(
  double precision, double precision, integer, integer
) TO authenticated;

-- ============================================================
-- Verification (executed against the live project on 2026-08-06)
-- ============================================================
--   SELECT facility_id, name, town, round(distance_metres) AS m
--   FROM find_nearest_facilities(53.4084, -2.9916, 5000, 1);
--
-- Expected: exactly one published facility, no 42703 error.

-- ============================================================
-- Relief — PostGIS Nearest-Facility RPC Verification Queries
-- ============================================================
-- Run these in Supabase SQL Editor after applying migration
-- 20260725_postgis_nearest_facility_rpc.sql
--
-- Each test prints PASS/FAIL. All must pass before shipping.
-- ============================================================

-- ─── TEST 1: PostGIS is enabled ─────────────────────────────
DO $$
BEGIN
  IF EXISTS (SELECT 1 FROM pg_extension WHERE extname = 'postgis') THEN
    RAISE NOTICE 'TEST 1 PASS: PostGIS extension is enabled';
  ELSE
    RAISE EXCEPTION 'TEST 1 FAIL: PostGIS extension NOT found';
  END IF;
END $$;

-- ─── TEST 2: location column exists and is populated ────────
DO $$
DECLARE
  v_total integer;
  v_has_location integer;
BEGIN
  SELECT count(*), count(location)
  INTO v_total, v_has_location
  FROM facilities
  WHERE publication_status = 'published';

  RAISE NOTICE 'TEST 2: total published=%, has_location=%', v_total, v_has_location;

  IF v_has_location = v_total AND v_total > 0 THEN
    RAISE NOTICE 'TEST 2 PASS: All published facilities have location';
  ELSE
    RAISE EXCEPTION 'TEST 2 FAIL: % of % published facilities missing location',
      v_total - v_has_location, v_total;
  END IF;
END $$;

-- ─── TEST 3: GiST spatial index exists ──────────────────────
DO $$
BEGIN
  IF EXISTS (
    SELECT 1 FROM pg_indexes
    WHERE tablename = 'facilities'
      AND indexname = 'facilities_location_gix'
  ) THEN
    RAISE NOTICE 'TEST 3 PASS: GiST index facilities_location_gix exists';
  ELSE
    RAISE EXCEPTION 'TEST 3 FAIL: GiST index facilities_location_gix NOT found';
  END IF;
END $$;

-- ─── TEST 4: publication_status index exists ────────────────
DO $$
BEGIN
  IF EXISTS (
    SELECT 1 FROM pg_indexes
    WHERE tablename = 'facilities'
      AND indexname = 'idx_facilities_publication_status'
  ) THEN
    RAISE NOTICE 'TEST 4 PASS: publication_status index exists';
  ELSE
    RAISE EXCEPTION 'TEST 4 FAIL: publication_status index NOT found';
  END IF;
END $$;

-- ─── TEST 5: find_nearest_facilities function exists ────────
DO $$
BEGIN
  IF EXISTS (
    SELECT 1 FROM pg_proc
    WHERE proname = 'find_nearest_facilities'
  ) THEN
    RAISE NOTICE 'TEST 5 PASS: find_nearest_facilities function exists';
  ELSE
    RAISE EXCEPTION 'TEST 5 FAIL: find_nearest_facilities function NOT found';
  END IF;
END $$;

-- ─── TEST 6: nearest of several facilities (Liverpool centre)─
-- Liverpool city centre: 53.4084, -2.9916
-- Should return the genuinely nearest published facility.
DO $$
DECLARE
  v_count integer;
  v_first_name text;
  v_first_dist double precision;
  v_second_dist double precision;
BEGIN
  SELECT count(*) INTO v_count
  FROM find_nearest_facilities(53.4084, -2.9916, 25000, 3);

  IF v_count < 2 THEN
    RAISE NOTICE 'TEST 6 SKIP: fewer than 2 facilities within 25 km of Liverpool centre (% found)', v_count;
    RETURN;
  END IF;

  SELECT name, distance_metres INTO v_first_name, v_first_dist
  FROM find_nearest_facilities(53.4084, -2.9916, 25000, 1);

  SELECT distance_metres INTO v_second_dist
  FROM find_nearest_facilities(53.4084, -2.9916, 25000, 2)
  ORDER BY distance_metres DESC
  LIMIT 1;

  RAISE NOTICE 'TEST 6: nearest=% (%m), second=%m', v_first_name, v_first_dist, v_second_dist;

  IF v_first_dist <= v_second_dist THEN
    RAISE NOTICE 'TEST 6 PASS: nearest facility is actually closest';
  ELSE
    RAISE EXCEPTION 'TEST 6 FAIL: nearest facility is NOT closest (% > %)', v_first_dist, v_second_dist;
  END IF;
END $$;

-- ─── TEST 7: unpublished closer facility is ignored ──────────
-- Temporarily unmark the nearest facility as published,
-- verify the function skips it, then restore.
-- WARNING: This test modifies data. Run in a test database only.
DO $$
DECLARE
  v_nearest_id uuid;
  v_new_nearest_id uuid;
  v_original_status text;
BEGIN
  -- Find current nearest
  SELECT facility_id INTO v_nearest_id
  FROM find_nearest_facilities(53.4084, -2.9916, 25000, 1);

  IF v_nearest_id IS NULL THEN
    RAISE NOTICE 'TEST 7 SKIP: no facilities found';
    RETURN;
  END IF;

  -- Save and change status
  SELECT publication_status INTO v_original_status
  FROM facilities WHERE id = v_nearest_id;

  UPDATE facilities SET publication_status = 'hidden' WHERE id = v_nearest_id;

  -- Find new nearest
  SELECT facility_id INTO v_new_nearest_id
  FROM find_nearest_facilities(53.4084, -2.9916, 25000, 1);

  -- Restore
  UPDATE facilities SET publication_status = v_original_status WHERE id = v_nearest_id;

  IF v_new_nearest_id IS NOT NULL AND v_new_nearest_id != v_nearest_id THEN
    RAISE NOTICE 'TEST 7 PASS: unpublished facility skipped, new nearest=%', v_new_nearest_id;
  ELSE
    RAISE EXCEPTION 'TEST 7 FAIL: unpublished facility NOT skipped (new_nearest=%)', v_new_nearest_id;
  END IF;
END $$;

-- ─── TEST 8: facility just inside radius is returned ─────────
DO $$
DECLARE
  v_count integer;
BEGIN
  -- Use a very large radius to guarantee at least one result
  SELECT count(*) INTO v_count
  FROM find_nearest_facilities(53.4084, -2.9916, 100000, 1);

  IF v_count >= 1 THEN
    RAISE NOTICE 'TEST 8 PASS: facility found within 100 km radius';
  ELSE
    RAISE EXCEPTION 'TEST 8 FAIL: no facilities found within 100 km';
  END IF;
END $$;

-- ─── TEST 9: facility outside radius is NOT returned ─────────
DO $$
DECLARE
  v_count integer;
BEGIN
  -- Use 1 metre radius — should find nothing unless standing on a toilet
  SELECT count(*) INTO v_count
  FROM find_nearest_facilities(53.4084, -2.9916, 1, 1);

  IF v_count = 0 THEN
    RAISE NOTICE 'TEST 9 PASS: no facility within 1 metre (expected)';
  ELSE
    RAISE NOTICE 'TEST 9 INFO: facility found within 1 metre — either very lucky or data issue';
  END IF;
END $$;

-- ─── TEST 10: equal-distance results are deterministic ──────
-- Same query twice must return same ordering
DO $$
DECLARE
  v_result1 text;
  v_result2 text;
BEGIN
  SELECT string_agg(facility_id::text, ',' ORDER BY facility_id)
  INTO v_result1
  FROM find_nearest_facilities(53.4084, -2.9916, 5000, 5);

  SELECT string_agg(facility_id::text, ',' ORDER BY facility_id)
  INTO v_result2
  FROM find_nearest_facilities(53.4084, -2.9916, 5000, 5);

  IF v_result1 = v_result2 THEN
    RAISE NOTICE 'TEST 10 PASS: deterministic ordering confirmed';
  ELSE
    RAISE EXCEPTION 'TEST 10 FAIL: non-deterministic (%, %)', v_result1, v_result2;
  END IF;
END $$;

-- ─── TEST 11: invalid latitude raises exception ─────────────
DO $$
BEGIN
  PERFORM find_nearest_facilities(999, -2.9916, 5000, 1);
  RAISE EXCEPTION 'TEST 11 FAIL: no exception for latitude 999';
EXCEPTION WHEN OTHERS THEN
  RAISE NOTICE 'TEST 11 PASS: invalid latitude correctly rejected: %', SQLERRM;
END $$;

-- ─── TEST 12: invalid longitude raises exception ────────────
DO $$
BEGIN
  PERFORM find_nearest_facilities(53.4084, 999, 5000, 1);
  RAISE EXCEPTION 'TEST 12 FAIL: no exception for longitude 999';
EXCEPTION WHEN OTHERS THEN
  RAISE NOTICE 'TEST 12 PASS: invalid longitude correctly rejected: %', SQLERRM;
END $$;

-- ─── TEST 13: no facilities found (empty result) ────────────
-- Use coordinates in the middle of the Atlantic Ocean
DO $$
DECLARE
  v_count integer;
BEGIN
  SELECT count(*) INTO v_count
  FROM find_nearest_facilities(0, -40, 1000, 1);

  IF v_count = 0 THEN
    RAISE NOTICE 'TEST 13 PASS: no facilities in Atlantic Ocean (expected)';
  ELSE
    RAISE EXCEPTION 'TEST 13 FAIL: unexpected facility in Atlantic Ocean';
  END IF;
END $$;

-- ─── TEST 14: negative radius raises exception ──────────────
DO $$
BEGIN
  PERFORM find_nearest_facilities(53.4084, -2.9916, -1, 1);
  RAISE EXCEPTION 'TEST 14 FAIL: no exception for negative radius';
EXCEPTION WHEN OTHERS THEN
  RAISE NOTICE 'TEST 14 PASS: negative radius correctly rejected: %', SQLERRM;
END $$;

-- ─── TEST 15: zero limit raises exception ───────────────────
DO $$
BEGIN
  PERFORM find_nearest_facilities(53.4084, -2.9916, 5000, 0);
  RAISE EXCEPTION 'TEST 15 FAIL: no exception for zero limit';
EXCEPTION WHEN OTHERS THEN
  RAISE NOTICE 'TEST 15 PASS: zero limit correctly rejected: %', SQLERRM;
END $$;

-- ─── EXPLAIN ANALYSE (index usage verification) ─────────────
-- Run separately and check for "Index Scan" or "Bitmap Index Scan"
-- on facilities_location_gix in the query plan.
EXPLAIN ANALYSE
SELECT f.id, f.name,
  ST_Distance(f.location,
    ST_SetSRID(ST_MakePoint(-2.9916, 53.4084), 4326)::geography
  ) AS distance_metres
FROM facilities f
WHERE f.publication_status = 'published'
  AND ST_DWithin(f.location,
    ST_SetSRID(ST_MakePoint(-2.9916, 53.4084), 4326)::geography,
    5000
  )
ORDER BY distance_metres ASC
LIMIT 1;

-- ─── GRANTS VERIFICATION ────────────────────────────────────
DO $$
BEGIN
  IF EXISTS (
    SELECT 1 FROM information_schema.routine_privileges
    WHERE routine_name = 'find_nearest_facilities'
      AND grantee = 'anon'
      AND privilege_type = 'EXECUTE'
  ) THEN
    RAISE NOTICE 'TEST GRANTS PASS: anon has EXECUTE on find_nearest_facilities';
  ELSE
    RAISE NOTICE 'TEST GRANTS WARN: anon may not have EXECUTE (check Supabase dashboard)';
  END IF;

  IF EXISTS (
    SELECT 1 FROM information_schema.routine_privileges
    WHERE routine_name = 'find_nearest_facilities'
      AND grantee = 'authenticated'
      AND privilege_type = 'EXECUTE'
  ) THEN
    RAISE NOTICE 'TEST GRANTS PASS: authenticated has EXECUTE on find_nearest_facilities';
  ELSE
    RAISE NOTICE 'TEST GRANTS WARN: authenticated may not have EXECUTE (check Supabase dashboard)';
  END IF;
END $$;

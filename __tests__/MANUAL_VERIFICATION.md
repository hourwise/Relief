# Relief — PostGIS Nearest-Facility Manual Verification Guide

**Migration:** `supabase/migrations/20260725_postgis_nearest_facility_rpc.sql`  
**Date:** 2026-07-25  
**Status:** Requires manual execution and verification before marking VERIFIED

---

## Prerequisites

1. Apply the migration in Supabase SQL Editor:
   ```
   Contents of: supabase/migrations/20260725_postgis_nearest_facility_rpc.sql
   ```
2. Confirm no errors in the SQL Editor output.

---

## Test 1 — Liverpool City Centre (dense area)

**Position:** 53.4084, -2.9916 (Liverpool ONE shopping centre)

```sql
SELECT facility_id, name, distance_metres
FROM find_nearest_facilities(53.4084, -2.9916, 5000, 5);
```

**Expected:** 1–5 published facilities returned, ordered by distance ascending.  
**Record:**
| Field | Value |
|-------|-------|
| Returned facility name | |
| distance_metres | |
| Search radius used | 5000 |
| How verified closest | |

---

## Test 2 — Two closely spaced facilities

**Position:** 53.4100, -2.9850 (near Liverpool Cathedral — multiple facilities nearby)

```sql
-- Get 2 nearest
SELECT facility_id, name, distance_metres
FROM find_nearest_facilities(53.4100, -2.9850, 5000, 2);

-- Verify order by checking raw distances
SELECT f.id, f.name,
  ST_Distance(f.location,
    ST_SetSRID(ST_MakePoint(-2.9850, 53.4100), 4326)::geography
  ) AS manual_distance
FROM facilities f
WHERE f.publication_status = 'published'
ORDER BY manual_distance ASC
LIMIT 5;
```

**Expected:** RPC results match manual query order.  
**Record:**
| Field | Value |
|-------|-------|
| RPC #1 name | |
| RPC #1 distance | |
| RPC #2 name | |
| RPC #2 distance | |
| Manual query matches? | |

---

## Test 3 — Radius expansion (remote area)

**Position:** 54.9, -2.5 (rural Northumberland — few facilities)

```sql
-- Step 1: 5 km radius
SELECT count(*) AS found_5km
FROM find_nearest_facilities(54.9, -2.5, 5000, 1);

-- Step 2: 10 km radius
SELECT count(*) AS found_10km
FROM find_nearest_facilities(54.9, -2.5, 10000, 1);

-- Step 3: 25 km radius
SELECT facility_id, name, distance_metres
FROM find_nearest_facilities(54.9, -2.5, 25000, 3);
```

**Expected:** 5 km may return 0; 10 km may return 0; 25 km should find facilities.  
**Record:**
| Radius | Found |
|--------|-------|
| 5 km | |
| 10 km | |
| 25 km | |
| Nearest name | |
| Nearest distance | |

---

## Test 4 — EXPLAIN ANALYSE (index usage)

```sql
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
```

**Expected:** Query plan shows index scan on `facilities_location_gix` (GiST). Look for:
- `Index Scan using facilities_location_gix` or
- `Bitmap Index Scan on facilities_location_gix`

**NOT expected:** Sequential Scan on `facilities` (means index not used).

**Record:**
| Metric | Value |
|--------|-------|
| Index used? | |
| Execution time | |
| Rows examined | |

---

## Test 5 — Input validation

```sql
-- Should raise exception
SELECT * FROM find_nearest_facilities(999, -2.9916, 5000, 1);
-- Expected: EXCEPTION Invalid latitude

SELECT * FROM find_nearest_facilities(53.4084, -999, 5000, 1);
-- Expected: EXCEPTION Invalid longitude

SELECT * FROM find_nearest_facilities(53.4084, -2.9916, -1, 1);
-- Expected: EXCEPTION Invalid radius

SELECT * FROM find_nearest_facilities(53.4084, -2.9916, 5000, 0);
-- Expected: EXCEPTION Invalid limit
```

**Record:** All 4 exceptions raised? Y/N

---

## Test 6 — RLS verification

```sql
-- As anon (disable role in SQL Editor or use incognito Supabase client)
-- Should work:
SELECT * FROM find_nearest_facilities(53.4084, -2.9916, 5000, 1);

-- As authenticated user:
-- Should also work:
SELECT * FROM find_nearest_facilities(53.4084, -2.9916, 5000, 1);
```

**Record:** Both roles can execute? Y/N

---

## Test 7 — App integration (Android)

1. Build and run the Android app
2. Tap "Need One Now" button
3. Verify the map zooms to a real facility
4. Verify the facility name is shown on the emergency card
5. Verify walking time is shown (should be reasonable, e.g. 5–30 minutes)
6. Tap "Get Directions" — Google Maps should open with walking directions
7. Check console logs for any errors

**Record:**
| Check | Pass |
|-------|------|
| Map zooms to facility | |
| Facility name shown | |
| Walking time shown | |
| Get Directions opens Google Maps | |
| No console errors | |

---

## Completion Checklist

- [ ] Migration applied successfully
- [ ] All SQL verification tests pass (`__tests__/postgis_nearest_facility_verification.sql`)
- [ ] Manual Test 1 (Liverpool centre) passed
- [ ] Manual Test 2 (closely spaced) passed
- [ ] Manual Test 3 (radius expansion) passed
- [ ] Manual Test 4 (EXPLAIN ANALYSE shows index) passed
- [ ] Manual Test 5 (input validation) passed
- [ ] Manual Test 6 (RLS grants) passed
- [ ] Manual Test 7 (Android app integration) passed
- [ ] Client unit tests pass
- [ ] No paid Google API enabled (Google Maps deep links only, no Routes/Directions API)
- [ ] No UI redesign performed

// ============================================================
// Project "Relief" — Facilities Service
// ============================================================
// Every read returns a discriminated result. A failed query must
// never be reported to the UI as "no facilities found": an empty
// map and a broken backend look identical to the user but mean
// completely different things, and only one of them is worth
// retrying.
// ============================================================

import { supabase } from './supabase';
import {
  filterColumnMap,
  mapNearestFacilityRow,
  type NearestFacilityRow,
} from '../utils/facilityQuery';
import type { Facility, FacilityFilters, NearestFacilityResult } from '../types';

// Re-exported so callers keep a single import site for facility reads.
export { filterColumnMap, mapNearestFacilityRow };

const VIEWPORT_LIMIT = 500;
const SEARCH_LIMIT = 20;

/** A read that either succeeded or failed for a stated reason. */
export type QueryResult<T> =
  | { ok: true; data: T }
  | { ok: false; error: string };

export interface FacilityPage {
  facilities: Facility[];
  count: number;
  /** True when the viewport holds more facilities than were returned. */
  truncated: boolean;
}

export interface ViewportBounds {
  minLatitude: number;
  maxLatitude: number;
  minLongitude: number;
  maxLongitude: number;
}

// eslint-disable-next-line @typescript-eslint/no-explicit-any
function applyFilters(query: any, filters: Partial<FacilityFilters>): any {
  let q = query;
  for (const { column, value } of filterColumnMap(filters)) {
    q = q.eq(column, value);
  }
  if (filters.min_rating && filters.min_rating > 0) {
    q = q.gte('overall_score', filters.min_rating);
  }
  return q;
}

function describeError(error: { message?: string; code?: string } | null): string {
  if (!error) return 'Unknown error';
  if (error.code === '42703' || error.code === '42883') {
    // Schema/RPC drift — worth naming explicitly so it is not mistaken for a
    // network problem during triage.
    return 'The facility service is out of date. Please update the app.';
  }
  return error.message || 'Could not reach the facility service.';
}

/**
 * Facilities inside a map viewport bounding box.
 */
export async function fetchViewportFacilities(
  bounds: ViewportBounds,
  filters?: Partial<FacilityFilters>,
): Promise<QueryResult<FacilityPage>> {
  let query = supabase
    .from('facilities')
    .select('*', { count: 'exact' })
    .gte('latitude', bounds.minLatitude)
    .lte('latitude', bounds.maxLatitude)
    .gte('longitude', bounds.minLongitude)
    .lte('longitude', bounds.maxLongitude)
    .eq('publication_status', 'published')
    .order('name')
    .limit(VIEWPORT_LIMIT);

  if (filters) query = applyFilters(query, filters);

  const { data, error, count } = await query;

  if (error) {
    console.error('fetchViewportFacilities failed:', error);
    return { ok: false, error: describeError(error) };
  }

  const facilities = (data ?? []) as unknown as Facility[];
  return {
    ok: true,
    data: {
      facilities,
      count: count ?? facilities.length,
      truncated: facilities.length >= VIEWPORT_LIMIT,
    },
  };
}

/**
 * Facilities within a rough radius of a point.
 *
 * The bounding box is an approximation used to bound the query cheaply; true
 * distances are computed from the returned coordinates.
 */
export async function fetchNearbyFacilities(
  latitude: number,
  longitude: number,
  radiusKm = 10,
  filters?: Partial<FacilityFilters>,
): Promise<QueryResult<FacilityPage>> {
  const latDelta = radiusKm / 111;
  const cosLat = Math.cos((latitude * Math.PI) / 180);
  // Guard against the poles, where the longitude delta explodes.
  const lngDelta = radiusKm / (111 * Math.max(Math.abs(cosLat), 0.01));

  return fetchViewportFacilities(
    {
      minLatitude: latitude - latDelta,
      maxLatitude: latitude + latDelta,
      minLongitude: longitude - lngDelta,
      maxLongitude: longitude + lngDelta,
    },
    filters,
  );
}

/**
 * A single facility by ID.
 */
export async function fetchFacilityById(
  id: string,
): Promise<QueryResult<Facility | null>> {
  const { data, error } = await supabase
    .from('facilities')
    .select('*')
    .eq('id', id)
    .maybeSingle();

  if (error) {
    console.error('fetchFacilityById failed:', error);
    return { ok: false, error: describeError(error) };
  }

  // `null` here means "no such published facility", which is a real answer
  // rather than a failure.
  return { ok: true, data: (data as unknown as Facility) ?? null };
}

/**
 * Search published facilities by town or postcode.
 */
export async function searchFacilities(
  term: string,
): Promise<QueryResult<Facility[]>> {
  const trimmed = term.trim();
  if (!trimmed) return { ok: true, data: [] };

  // Escape PostgREST's `or` filter metacharacters so a search for "a,b" or
  // "50%" cannot alter the filter structure.
  const escaped = trimmed.replace(/[,()*\\]/g, (match) => `\\${match}`);
  const pattern = `%${escaped}%`;

  const { data, error } = await supabase
    .from('facilities')
    .select('*')
    .or(`town.ilike.${pattern},postcode.ilike.${pattern}`)
    .eq('publication_status', 'published')
    .order('overall_score', { ascending: false, nullsFirst: false })
    .limit(SEARCH_LIMIT);

  if (error) {
    console.error('searchFacilities failed:', error);
    return { ok: false, error: describeError(error) };
  }

  return { ok: true, data: (data ?? []) as unknown as Facility[] };
}

/**
 * The closest published facility, via the PostGIS RPC.
 *
 * Radius widens 5 km → 10 km → 25 km only when a search genuinely found
 * nothing. An RPC *error* aborts immediately: retrying a broken function at a
 * wider radius just fails three times and then reports "nothing nearby",
 * which is exactly the misdiagnosis this journey must not make.
 */
export async function fetchClosestFacility(
  latitude: number,
  longitude: number,
): Promise<QueryResult<NearestFacilityResult | null>> {
  const radii = [5000, 10000, 25000];

  for (const radius of radii) {
    const { data, error } = await supabase.rpc('find_nearest_facilities', {
      user_latitude: latitude,
      user_longitude: longitude,
      search_radius_metres: radius,
      result_limit: 1,
    });

    if (error) {
      console.error(`find_nearest_facilities failed at ${radius}m:`, error);
      return { ok: false, error: describeError(error) };
    }

    const rows = (data ?? []) as NearestFacilityRow[];
    if (rows.length > 0) {
      const facility = mapNearestFacilityRow(rows[0]);
      if (!facility) {
        return {
          ok: false,
          error: 'The nearest facility could not be read. Please try again.',
        };
      }
      return {
        ok: true,
        data: { facility, distance_metres: facility.distance_metres },
      };
    }
  }

  // Searched every radius successfully and genuinely found nothing.
  return { ok: true, data: null };
}

export { estimateWalkingTime } from '../utils/walkingTime';

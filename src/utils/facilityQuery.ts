// ============================================================
// Project "Relief" — Pure query mapping
// ============================================================
// Filter-to-column mapping and RPC row mapping live here, apart
// from the Supabase client, so they can be tested directly
// without a React Native runtime. These two functions are where
// schema drift previously turned into runtime failure, so they
// are the ones that most need tests.
// ============================================================

import {
  FILTERABLE_BOOLEAN_COLUMNS,
  type FacilityFilters,
  type FilterableBooleanColumn,
  type NearestFacility,
} from '../types';

export interface FilterColumn {
  column: FilterableBooleanColumn;
  value: boolean;
}

/**
 * Turn active filters into column equality checks.
 *
 * Only columns in FILTERABLE_BOOLEAN_COLUMNS are ever emitted, and that list is
 * compile-time checked against the generated schema. A filter naming a column
 * the database does not have cannot reach PostgREST.
 *
 * `open_now` is deliberately not emitted: it is derived client-side from
 * `open_hours` (jsonb), not a single equality check. `min_rating` is a range
 * comparison and is applied separately.
 */
export function filterColumnMap(
  filters: Partial<FacilityFilters>,
): FilterColumn[] {
  const applied: FilterColumn[] = [];
  for (const column of FILTERABLE_BOOLEAN_COLUMNS) {
    const value = filters[column];
    // Only an explicit true/false filters. `undefined` means "don't care": a
    // facility whose information is unknown must not be excluded by it.
    if (value !== undefined) applied.push({ column, value });
  }
  return applied;
}

/** One row as returned by the repaired find_nearest_facilities(). */
export interface NearestFacilityRow {
  facility_id: string | null;
  name: string | null;
  address: string | null;
  latitude: number | null;
  longitude: number | null;
  town: string | null;
  postcode: string | null;
  open_hours: unknown;
  is_free: boolean | null;
  is_accessible: boolean | null;
  overall_score: number | null;
  verification_status: string | null;
  distance_metres: number | null;
}

/**
 * Map one nearest-facility row.
 *
 * Returns null when the row cannot be used: without an id, coordinates and a
 * distance there is nothing to show on a map or route to, and inventing
 * defaults for those would put a pin in the wrong place.
 *
 * Missing *descriptive* fields are tolerated — the UK import has facilities
 * with no address or postcode, and those are still worth showing.
 */
export function mapNearestFacilityRow(
  row: NearestFacilityRow,
): NearestFacility | null {
  if (
    !row.facility_id ||
    row.latitude == null ||
    row.longitude == null ||
    row.distance_metres == null
  ) {
    return null;
  }

  return {
    facility_id: row.facility_id,
    name: row.name ?? 'Unnamed facility',
    address: row.address,
    latitude: row.latitude,
    longitude: row.longitude,
    town: row.town,
    postcode: row.postcode,
    open_hours: (row.open_hours as NearestFacility['open_hours']) ?? null,
    is_free: row.is_free,
    is_accessible: row.is_accessible,
    overall_score: row.overall_score,
    verification_status: (row.verification_status ??
      'source_imported') as NearestFacility['verification_status'],
    distance_metres: row.distance_metres,
  };
}

// ============================================================
// Project "Relief" — Facilities Service
// ============================================================

import { supabase } from './supabase';
import type { Facility, FacilityFilters, NearestFacilityResult } from '../types';

const VIEWPORT_LIMIT = 500;

// eslint-disable-next-line @typescript-eslint/no-explicit-any
function applyFilters(query: any, filters: Partial<FacilityFilters>): any {
  const filterMap: [string, boolean | number | undefined][] = [
    ['is_free', filters.is_free],
    ['is_accessible', filters.is_accessible],
    ['is_disabled_access', filters.is_disabled_access],
    ['has_baby_changing', filters.has_baby_changing],
    ['has_family_room', filters.has_family_room],
    ['is_gender_neutral', filters.is_gender_neutral],
    ['is_single_occupancy', filters.is_single_occupancy],
    ['is_24h', filters.is_24h],
    ['is_single_room', filters.is_single_room],
    ['has_floor_to_ceiling_cubicles', filters.has_floor_to_ceiling_cubicles],
    ['is_quiet', filters.is_quiet],
    ['has_wheelchair_access', filters.has_wheelchair_access],
    ['requires_radar_key', filters.requires_radar_key],
    ['has_adult_changing_place', filters.has_adult_changing_place],
    ['has_lift', filters.has_lift],
    ['has_grab_rails', filters.has_grab_rails],
    ['has_baby_changing_inside', filters.has_baby_changing_inside],
    ['has_separate_changing_room', filters.has_separate_changing_room],
    ['has_family_toilet', filters.has_family_toilet],
    ['has_pram_access', filters.has_pram_access],
    ['has_soap', filters.has_soap],
    ['has_paper_towels', filters.has_paper_towels],
    ['has_hand_dryer', filters.has_hand_dryer],
    ['has_mirror', filters.has_mirror],
    ['has_shelf', filters.has_shelf],
    ['has_hooks', filters.has_hooks],
    ['has_sanitary_bins', filters.has_sanitary_bins],
    ['has_free_period_products', filters.has_free_period_products],
    ['has_drinking_water', filters.has_drinking_water],
    ['has_staff_nearby', filters.has_staff_nearby],
    ['has_cctv', filters.has_cctv],
    ['is_women_friendly', filters.is_women_friendly],
    ['is_family_friendly', filters.is_family_friendly],
    ['is_water_refill_station', filters.is_water_refill_station],
    ['is_shower_facility', filters.is_shower_facility],
    ['is_breastfeeding_room', filters.is_breastfeeding_room],
    ['is_rest_area', filters.is_rest_area],
    ['is_changing_place', filters.is_changing_place],
    ['is_ev_charging', filters.is_ev_charging],
    ['is_picnic_area', filters.is_picnic_area],
  ];

  let q = query;
  for (const [col, val] of filterMap) {
    if (val !== undefined) {
      q = q.eq(col, val);
    }
  }
  if (filters.min_rating && filters.min_rating > 0) {
    q = q.gte('overall_score', filters.min_rating);
  }
  return q;
}

/**
 * Fetch facilities within a map viewport bounding box.
 * Used by MapScreen for bounded, debounced queries.
 */
export async function fetchViewportFacilities(
  bounds: {
    minLatitude: number;
    maxLatitude: number;
    minLongitude: number;
    maxLongitude: number;
  },
  filters?: Partial<FacilityFilters>,
): Promise<{ facilities: Facility[]; count: number }> {
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

  if (filters) {
    query = applyFilters(query, filters);
  }

  const { data, error, count } = await query;

  if (error) {
    console.error('Error fetching viewport facilities:', error);
    return { facilities: [], count: 0 };
  }

  return {
    facilities: (data as unknown as Facility[]) || [],
    count: count || 0,
  };
}

/**
 * Fetch nearby facilities — kept for emergency/closest-facility use.
 */
export async function fetchNearbyFacilities(
  latitude: number,
  longitude: number,
  radiusKm: number = 10,
  filters?: Partial<FacilityFilters>,
): Promise<{ facilities: Facility[]; count: number }> {
  const latDelta = radiusKm / 111;
  const lngDelta = radiusKm / (111 * Math.cos((latitude * Math.PI) / 180));

  let query = supabase
    .from('facilities')
    .select('*', { count: 'exact' })
    .gte('latitude', latitude - latDelta)
    .lte('latitude', latitude + latDelta)
    .gte('longitude', longitude - lngDelta)
    .lte('longitude', longitude + lngDelta)
    .eq('publication_status', 'published')
    .order('name')
    .limit(VIEWPORT_LIMIT);

  if (filters) {
    query = applyFilters(query, filters);
  }

  const { data, error, count } = await query;

  if (error) {
    console.error('Error fetching nearby facilities:', error);
    return { facilities: [], count: 0 };
  }

  return {
    facilities: (data as unknown as Facility[]) || [],
    count: count || 0,
  };
}

/**
 * Fetch a single facility by ID.
 */
export async function fetchFacilityById(
  id: string,
): Promise<Facility | null> {
  const { data, error } = await supabase
    .from('facilities')
    .select('*')
    .eq('id', id)
    .single();

  if (error) {
    console.error('Error fetching facility:', error);
    return null;
  }

  return data as unknown as Facility;
}

/**
 * Search facilities by town or postcode.
 */
export async function searchFacilities(
  query: string,
): Promise<Facility[]> {
  const searchTerm = `%${query}%`;

  const { data, error } = await supabase
    .from('facilities')
    .select('*')
    .or(`town.ilike.${searchTerm},postcode.ilike.${searchTerm}`)
    .eq('publication_status', 'published')
    .order('overall_score', { ascending: false })
    .limit(20);

  if (error) {
    console.error('Error searching facilities:', error);
    return [];
  }

  return data as unknown as Facility[];
}

/**
 * Get the closest facility to a given location using PostGIS RPC.
 * Uses controlled radius expansion: 5 km → 10 km → 25 km.
 */
export async function fetchClosestFacility(
  latitude: number,
  longitude: number,
): Promise<NearestFacilityResult | null> {
  const radii = [5000, 10000, 25000];

  for (const radius of radii) {
    const { data, error } = await supabase.rpc('find_nearest_facilities', {
      user_latitude: latitude,
      user_longitude: longitude,
      search_radius_metres: radius,
      result_limit: 1,
    });

    if (error) {
      console.error(
        `Error finding nearest facility (radius ${radius}m):`,
        error.message || error,
      );
      // Continue to wider radius on transient errors
      continue;
    }

    if (data && data.length > 0) {
      const row = data[0];
      const facility: Facility = {
        id: row.facility_id,
        name: row.name,
        address: row.address,
        latitude: row.latitude,
        longitude: row.longitude,
        postcode: row.postcode,
        town: row.town,
        country: row.country,
        photos: row.photos ?? [],
        open_hours: row.open_hours,
        is_free: row.is_free,
        price_note: row.price_note,
        access_notes: row.access_notes ?? '',
        last_verified_at: row.last_verified_at,
        is_accessible: row.is_accessible,
        is_disabled_access: row.is_disabled_access,
        has_baby_changing: row.has_baby_changing,
        has_family_room: row.has_family_room,
        is_gender_neutral: row.is_gender_neutral,
        is_single_occupancy: row.is_single_occupancy,
        is_24h: row.is_24h,
        is_single_room: row.is_single_room,
        has_floor_to_ceiling_cubicles: row.has_floor_to_ceiling_cubicles,
        is_quiet: row.is_quiet,
        has_wheelchair_access: row.has_wheelchair_access,
        requires_radar_key: row.requires_radar_key,
        has_adult_changing_place: row.has_adult_changing_place,
        has_lift: row.has_lift,
        has_grab_rails: row.has_grab_rails,
        has_baby_changing_inside: row.has_baby_changing_inside,
        has_separate_changing_room: row.has_separate_changing_room,
        has_family_toilet: row.has_family_toilet,
        has_pram_access: row.has_pram_access,
        has_soap: row.has_soap,
        has_paper_towels: row.has_paper_towels,
        has_hand_dryer: row.has_hand_dryer,
        has_mirror: row.has_mirror,
        has_shelf: row.has_shelf,
        has_hooks: row.has_hooks,
        has_sanitary_bins: row.has_sanitary_bins,
        has_free_period_products: row.has_free_period_products,
        has_drinking_water: row.has_drinking_water,
        noise_level: row.noise_level,
        temperature: row.temperature,
        lighting: row.lighting,
        smell: row.smell,
        has_staff_nearby: row.has_staff_nearby,
        has_cctv: row.has_cctv,
        is_women_friendly: row.is_women_friendly,
        is_family_friendly: row.is_family_friendly,
        is_water_refill_station: row.is_water_refill_station,
        is_shower_facility: row.is_shower_facility,
        is_breastfeeding_room: row.is_breastfeeding_room,
        is_rest_area: row.is_rest_area,
        is_changing_place: row.is_changing_place,
        is_ev_charging: row.is_ev_charging,
        is_picnic_area: row.is_picnic_area,
        overall_score: row.overall_score ?? 0,
        cleanliness_rating: row.cleanliness_rating,
        privacy_rating: row.privacy_rating,
        accessibility_rating: row.accessibility_rating,
        safety_rating: row.safety_rating,
        noise_rating: row.noise_rating,
        environment_rating: row.environment_rating,
        publication_status: row.publication_status,
        verification_status: row.verification_status,
        last_community_confirmed_at: row.last_community_confirmed_at,
        last_staff_verified_at: row.last_staff_verified_at,
        created_at: row.created_at,
        updated_at: row.updated_at,
        created_by: row.created_by,
        is_verified: row.is_verified ?? false,
      };

      return {
        facility,
        distance_metres: row.distance_metres,
      };
    }
  }

  // No facility found within any radius
  return null;
}

/**
 * Calculate approximate walking time in minutes (assuming 5 km/h).
 *
 * Accepts either:
 *   - distanceMetres (number) — from PostGIS RPC distance_metres
 *   - (fromLat, fromLng, toLat, toLng) — legacy coordinate-based Haversine
 */
export function estimateWalkingTime(
  distanceMetresOrFromLat: number,
  fromLng?: number,
  toLat?: number,
  toLng?: number,
): number {
  let metres: number;

  if (fromLng !== undefined && toLat !== undefined && toLng !== undefined) {
    // Legacy 4-arg Haversine path
    const fromLat = distanceMetresOrFromLat;
    const R = 6371;
    const dLat = ((toLat - fromLat) * Math.PI) / 180;
    const dLng = ((toLng - fromLng) * Math.PI) / 180;
    const a =
      Math.sin(dLat / 2) * Math.sin(dLat / 2) +
      Math.cos((fromLat * Math.PI) / 180) *
        Math.cos((toLat * Math.PI) / 180) *
        Math.sin(dLng / 2) *
        Math.sin(dLng / 2);
    const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));
    metres = R * c * 1000;
  } else {
    // Single-arg: distance in metres from PostGIS
    metres = distanceMetresOrFromLat;
  }

  const walkingMinutes = Math.round((metres / 1000 / 5) * 60);
  return Math.max(1, walkingMinutes);
}
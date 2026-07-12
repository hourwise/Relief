// ============================================================
// Project "Relief" — Facilities Service
// ============================================================

import { supabase } from './supabase';
import type { Facility, FacilityFilters } from '../types';

const FACILITIES_PER_PAGE = 20;

/**
 * Fetch nearby facilities within a bounding box, ordered by distance.
 */
export async function fetchNearbyFacilities(
  latitude: number,
  longitude: number,
  radiusKm: number = 10,
  filters?: Partial<FacilityFilters>,
  page: number = 0,
): Promise<{ facilities: Facility[]; count: number }> {
  // Approximate degree-to-km conversion
  const latDelta = radiusKm / 111;
  const lngDelta = radiusKm / (111 * Math.cos((latitude * Math.PI) / 180));

  let query = supabase
    .from('facilities')
    .select('*', { count: 'exact' })
    .gte('latitude', latitude - latDelta)
    .lte('latitude', latitude + latDelta)
    .gte('longitude', longitude - lngDelta)
    .lte('longitude', longitude + lngDelta)
    .eq('is_verified', true)
    .order('overall_score', { ascending: false })
    .range(page * FACILITIES_PER_PAGE, (page + 1) * FACILITIES_PER_PAGE - 1);

  // Apply filters (basic + advanced)
  if (filters) {
    // Basic filters
    if (filters.is_free !== undefined) {
      query = query.eq('is_free', filters.is_free);
    }
    if (filters.is_accessible !== undefined) {
      query = query.eq('is_accessible', filters.is_accessible);
    }
    if (filters.is_disabled_access !== undefined) {
      query = query.eq('is_disabled_access', filters.is_disabled_access);
    }
    if (filters.has_baby_changing !== undefined) {
      query = query.eq('has_baby_changing', filters.has_baby_changing);
    }
    if (filters.has_family_room !== undefined) {
      query = query.eq('has_family_room', filters.has_family_room);
    }
    if (filters.is_gender_neutral !== undefined) {
      query = query.eq('is_gender_neutral', filters.is_gender_neutral);
    }
    if (filters.is_single_occupancy !== undefined) {
      query = query.eq('is_single_occupancy', filters.is_single_occupancy);
    }
    if (filters.is_24h !== undefined) {
      query = query.eq('is_24h', filters.is_24h);
    }
    if (filters.min_rating && filters.min_rating > 0) {
      query = query.gte('overall_score', filters.min_rating);
    }

    // Phase 3 — Advanced Privacy filters
    if (filters.is_single_room !== undefined) {
      query = query.eq('is_single_room', filters.is_single_room);
    }
    if (filters.has_floor_to_ceiling_cubicles !== undefined) {
      query = query.eq('has_floor_to_ceiling_cubicles', filters.has_floor_to_ceiling_cubicles);
    }
    if (filters.is_quiet !== undefined) {
      query = query.eq('is_quiet', filters.is_quiet);
    }

    // Phase 3 — Advanced Accessibility filters
    if (filters.has_wheelchair_access !== undefined) {
      query = query.eq('has_wheelchair_access', filters.has_wheelchair_access);
    }
    if (filters.requires_radar_key !== undefined) {
      query = query.eq('requires_radar_key', filters.requires_radar_key);
    }
    if (filters.has_adult_changing_place !== undefined) {
      query = query.eq('has_adult_changing_place', filters.has_adult_changing_place);
    }
    if (filters.has_lift !== undefined) {
      query = query.eq('has_lift', filters.has_lift);
    }
    if (filters.has_grab_rails !== undefined) {
      query = query.eq('has_grab_rails', filters.has_grab_rails);
    }

    // Phase 3 — Baby facilities
    if (filters.has_baby_changing_inside !== undefined) {
      query = query.eq('has_baby_changing_inside', filters.has_baby_changing_inside);
    }
    if (filters.has_separate_changing_room !== undefined) {
      query = query.eq('has_separate_changing_room', filters.has_separate_changing_room);
    }
    if (filters.has_family_toilet !== undefined) {
      query = query.eq('has_family_toilet', filters.has_family_toilet);
    }
    if (filters.has_pram_access !== undefined) {
      query = query.eq('has_pram_access', filters.has_pram_access);
    }

    // Phase 3 — Equipment
    if (filters.has_soap !== undefined) {
      query = query.eq('has_soap', filters.has_soap);
    }
    if (filters.has_paper_towels !== undefined) {
      query = query.eq('has_paper_towels', filters.has_paper_towels);
    }
    if (filters.has_hand_dryer !== undefined) {
      query = query.eq('has_hand_dryer', filters.has_hand_dryer);
    }
    if (filters.has_mirror !== undefined) {
      query = query.eq('has_mirror', filters.has_mirror);
    }
    if (filters.has_shelf !== undefined) {
      query = query.eq('has_shelf', filters.has_shelf);
    }
    if (filters.has_hooks !== undefined) {
      query = query.eq('has_hooks', filters.has_hooks);
    }
    if (filters.has_sanitary_bins !== undefined) {
      query = query.eq('has_sanitary_bins', filters.has_sanitary_bins);
    }
    if (filters.has_free_period_products !== undefined) {
      query = query.eq('has_free_period_products', filters.has_free_period_products);
    }
    if (filters.has_drinking_water !== undefined) {
      query = query.eq('has_drinking_water', filters.has_drinking_water);
    }

    // Phase 3 — Safety
    if (filters.has_staff_nearby !== undefined) {
      query = query.eq('has_staff_nearby', filters.has_staff_nearby);
    }

    // Facility Types
    if (filters.is_water_refill_station !== undefined) {
      query = query.eq('is_water_refill_station', filters.is_water_refill_station);
    }
    if (filters.is_shower_facility !== undefined) {
      query = query.eq('is_shower_facility', filters.is_shower_facility);
    }
    if (filters.is_breastfeeding_room !== undefined) {
      query = query.eq('is_breastfeeding_room', filters.is_breastfeeding_room);
    }
    if (filters.is_rest_area !== undefined) {
      query = query.eq('is_rest_area', filters.is_rest_area);
    }
    if (filters.is_changing_place !== undefined) {
      query = query.eq('is_changing_place', filters.is_changing_place);
    }
    if (filters.is_ev_charging !== undefined) {
      query = query.eq('is_ev_charging', filters.is_ev_charging);
    }
    if (filters.is_picnic_area !== undefined) {
      query = query.eq('is_picnic_area', filters.is_picnic_area);
    }
    if (filters.has_cctv !== undefined) {
      query = query.eq('has_cctv', filters.has_cctv);
    }
    if (filters.is_women_friendly !== undefined) {
      query = query.eq('is_women_friendly', filters.is_women_friendly);
    }
    if (filters.is_family_friendly !== undefined) {
      query = query.eq('is_family_friendly', filters.is_family_friendly);
    }
  }

  const { data, error, count } = await query;

  if (error) {
    console.error('Error fetching facilities:', error);
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
    .eq('is_verified', true)
    .order('overall_score', { ascending: false })
    .limit(20);

  if (error) {
    console.error('Error searching facilities:', error);
    return [];
  }

  return data as unknown as Facility[];
}

/**
 * Get the closest facility to a given location (for emergency mode).
 */
export async function fetchClosestFacility(
  latitude: number,
  longitude: number,
): Promise<Facility | null> {
  const { facilities } = await fetchNearbyFacilities(
    latitude,
    longitude,
    5, // 5km radius
    undefined,
    0,
  );

  if (facilities.length === 0) return null;

  // Sort by approximate distance (simple Euclidean)
  const sorted = facilities.sort((a, b) => {
    const distA = Math.sqrt(
      Math.pow(a.latitude - latitude, 2) +
        Math.pow(a.longitude - longitude, 2),
    );
    const distB = Math.sqrt(
      Math.pow(b.latitude - latitude, 2) +
        Math.pow(b.longitude - longitude, 2),
    );
    return distA - distB;
  });

  return sorted[0];
}

/**
 * Calculate approximate walking time in minutes (assuming 5 km/h pace).
 */
export function estimateWalkingTime(
  fromLat: number,
  fromLng: number,
  toLat: number,
  toLng: number,
): number {
  const R = 6371; // Earth's radius in km
  const dLat = ((toLat - fromLat) * Math.PI) / 180;
  const dLng = ((toLng - fromLng) * Math.PI) / 180;
  const a =
    Math.sin(dLat / 2) * Math.sin(dLat / 2) +
    Math.cos((fromLat * Math.PI) / 180) *
      Math.cos((toLat * Math.PI) / 180) *
      Math.sin(dLng / 2) *
      Math.sin(dLng / 2);
  const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));
  const distanceKm = R * c;

  // Walking speed ~5 km/h
  const walkingMinutes = Math.round((distanceKm / 5) * 60);
  return Math.max(1, walkingMinutes);
}
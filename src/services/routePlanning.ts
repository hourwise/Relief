// ============================================================
// Project "Relief" — Route Planning Service (4.2)
// Finds facilities along a route with comfort stops
// every 60-90 minutes (e.g. Liverpool → London)
// ============================================================

import { supabase } from './supabase';
import type { Facility } from '../types';

export interface RouteStop {
  facility: Facility;
  distanceFromStartKm: number;
  estimatedArrivalMinutes: number;
  stopDurationMinutes: number;
}

export interface RoutePlan {
  from: string;
  to: string;
  totalDistanceKm: number;
  estimatedDrivingMinutes: number;
  comfortStops: RouteStop[];
}

/**
 * Geocode a location string (town/postcode) to coordinates.
 * Uses the facilities table as a lookup source.
 */
async function geocodeLocation(query: string): Promise<{ lat: number; lng: number } | null> {
  const { data, error } = await supabase
    .from('facilities')
    .select('latitude, longitude')
    .or(`town.ilike.%${query}%,postcode.ilike.%${query}%`)
    .eq('is_verified', true)
    .limit(1);

  if (error || !data || data.length === 0) return null;

  return { lat: data[0].latitude, lng: data[0].longitude };
}

/**
 * Calculate distance between two coordinates using Haversine formula.
 */
function haversineDistance(
  lat1: number, lng1: number,
  lat2: number, lng2: number,
): number {
  const R = 6371; // Earth's radius in km
  const dLat = ((lat2 - lat1) * Math.PI) / 180;
  const dLng = ((lng2 - lng1) * Math.PI) / 180;
  const a =
    Math.sin(dLat / 2) * Math.sin(dLat / 2) +
    Math.cos((lat1 * Math.PI) / 180) *
      Math.cos((lat2 * Math.PI) / 180) *
      Math.sin(dLng / 2) *
      Math.sin(dLng / 2);
  const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));
  return R * c;
}

/**
 * Estimate driving time in minutes (assuming ~80 km/h average).
 */
function estimateDrivingTime(distanceKm: number): number {
  return Math.round((distanceKm / 80) * 60);
}

/**
 * Interpolate a point along a line between two coordinates.
 */
function interpolatePoint(
  lat1: number, lng1: number,
  lat2: number, lng2: number,
  fraction: number,
): { lat: number; lng: number } {
  return {
    lat: lat1 + (lat2 - lat1) * fraction,
    lng: lng1 + (lng2 - lng1) * fraction,
  };
}

/**
 * Plan a route with comfort stops every 60-90 minutes.
 * Finds suitable facilities near the route path.
 */
export async function planRoute(
  fromQuery: string,
  toQuery: string,
  comfortStopIntervalMinutes: number = 75, // Default: every 75 mins
  searchRadiusKm: number = 5, // Search within 5km of route
): Promise<RoutePlan | { error: string }> {
  // Geocode start and end points
  const fromCoords = await geocodeLocation(fromQuery);
  const toCoords = await geocodeLocation(toQuery);

  if (!fromCoords) {
    return { error: `Could not find location: "${fromQuery}"` };
  }
  if (!toCoords) {
    return { error: `Could not find location: "${toQuery}"` };
  }

  const totalDistanceKm = haversineDistance(
    fromCoords.lat, fromCoords.lng,
    toCoords.lat, toCoords.lng,
  );

  const totalDrivingMinutes = estimateDrivingTime(totalDistanceKm);

  // Calculate how many comfort stops we need
  const numberOfStops = Math.max(
    0,
    Math.floor(totalDrivingMinutes / comfortStopIntervalMinutes),
  );

  const comfortStops: RouteStop[] = [];

  for (let i = 1; i <= numberOfStops; i++) {
    // Find a point along the route at this stop interval
    const fraction = i / (numberOfStops + 1);
    const point = interpolatePoint(
      fromCoords.lat, fromCoords.lng,
      toCoords.lat, toCoords.lng,
      fraction,
    );

    // Search for facilities near this point
    const latDelta = searchRadiusKm / 111;
    const lngDelta = searchRadiusKm / (111 * Math.cos((point.lat * Math.PI) / 180));

    const { data, error } = await supabase
      .from('facilities')
      .select('*')
      .gte('latitude', point.lat - latDelta)
      .lte('latitude', point.lat + latDelta)
      .gte('longitude', point.lng - lngDelta)
      .lte('longitude', point.lng + lngDelta)
      .eq('is_verified', true)
      .order('overall_score', { ascending: false })
      .limit(3);

    if (error || !data || data.length === 0) continue;

    // Pick the highest-rated facility
    const facility = data[0] as unknown as Facility;
    const distanceFromStart = haversineDistance(
      fromCoords.lat, fromCoords.lng,
      facility.latitude, facility.longitude,
    );

    comfortStops.push({
      facility,
      distanceFromStartKm: Math.round(distanceFromStart * 10) / 10,
      estimatedArrivalMinutes: estimateDrivingTime(distanceFromStart),
      stopDurationMinutes: 15, // Suggested 15 min stop
    });
  }

  return {
    from: fromQuery,
    to: toQuery,
    totalDistanceKm: Math.round(totalDistanceKm * 10) / 10,
    estimatedDrivingMinutes: totalDrivingMinutes,
    comfortStops,
  };
}

/**
 * Get a human-readable summary of the route.
 */
export function formatRouteSummary(plan: RoutePlan): string {
  const hours = Math.floor(plan.estimatedDrivingMinutes / 60);
  const mins = plan.estimatedDrivingMinutes % 60;
  const timeStr = hours > 0 ? `${hours}h ${mins}m` : `${mins}m`;

  let summary = `${plan.from} → ${plan.to}\n`;
  summary += `Total: ${plan.totalDistanceKm} km (${timeStr} driving)\n`;
  summary += `Comfort stops: ${plan.comfortStops.length}\n\n`;

  plan.comfortStops.forEach((stop, i) => {
    const arrivalHours = Math.floor(stop.estimatedArrivalMinutes / 60);
    const arrivalMins = stop.estimatedArrivalMinutes % 60;
    summary += `Stop ${i + 1}: ${stop.facility.name}\n`;
    summary += `  📍 ${stop.facility.address}\n`;
    summary += `  ⏱ Arrive ~${arrivalHours}h ${arrivalMins}m | ★ ${stop.facility.overall_score.toFixed(1)}\n`;
  });

  return summary;
}
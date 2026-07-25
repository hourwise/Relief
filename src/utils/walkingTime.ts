/**
 * Calculate an approximate walking time at 5 km/h.
 * Coordinate input is straight-line only and must never be presented as a route.
 */
export function estimateWalkingTime(
  distanceMetresOrFromLat: number,
  fromLng?: number,
  toLat?: number,
  toLng?: number,
): number {
  let metres: number;
  if (fromLng !== undefined && toLat !== undefined && toLng !== undefined) {
    const fromLat = distanceMetresOrFromLat;
    const earthRadiusKm = 6371;
    const dLat = ((toLat - fromLat) * Math.PI) / 180;
    const dLng = ((toLng - fromLng) * Math.PI) / 180;
    const a = Math.sin(dLat / 2) ** 2 + Math.cos((fromLat * Math.PI) / 180) * Math.cos((toLat * Math.PI) / 180) * Math.sin(dLng / 2) ** 2;
    metres = earthRadiusKm * 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a)) * 1000;
  } else {
    metres = distanceMetresOrFromLat;
  }
  return Math.max(1, Math.round((metres / 1000 / 5) * 60));
}

// ============================================================
// Relief — Facility submission coordinate contract
// ============================================================

export interface FacilityCoordinates {
  latitude: number;
  longitude: number;
}

type CoordinateInput = {
  latitude?: number | null;
  longitude?: number | null;
} | null | undefined;

/**
 * A community submission must carry an explicitly selected real-world point.
 * The exact 0,0 pair is rejected as the known placeholder state for Relief's
 * UK-focused product, even though it is technically inside global bounds.
 */
export function isValidFacilityCoordinates(
  coordinates: CoordinateInput,
): coordinates is FacilityCoordinates {
  if (!coordinates) return false;

  const { latitude, longitude } = coordinates;
  if (!Number.isFinite(latitude) || !Number.isFinite(longitude)) return false;
  if (latitude < -90 || latitude > 90) return false;
  if (longitude < -180 || longitude > 180) return false;
  if (latitude === 0 && longitude === 0) return false;

  return true;
}

/**
 * Return only coordinates that are safe to pass to the moderation queue.
 * Returning null makes the fail-closed boundary explicit and easy to test.
 */
export function getFacilitySubmissionCoordinates(
  coordinates: CoordinateInput,
): FacilityCoordinates | null {
  return isValidFacilityCoordinates(coordinates)
    ? { latitude: coordinates.latitude, longitude: coordinates.longitude }
    : null;
}

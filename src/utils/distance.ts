// ============================================================
// Project "Relief" — Distance calculation and formatting
// ============================================================
// The UK build presents metres and kilometres. Miles must not
// appear anywhere in the distance UI.
// ============================================================

const EARTH_RADIUS_METRES = 6371000;

/**
 * Great-circle distance in metres.
 *
 * Straight-line only. This is honest for "how far away is it" but must never
 * be presented as a route distance — the walk is always at least this long.
 * Server-side nearest lookups use PostGIS instead; this is for ordering and
 * labelling facilities the client already holds.
 */
export function distanceMetres(
  fromLatitude: number,
  fromLongitude: number,
  toLatitude: number,
  toLongitude: number,
): number {
  const toRadians = (degrees: number) => (degrees * Math.PI) / 180;

  const dLat = toRadians(toLatitude - fromLatitude);
  const dLng = toRadians(toLongitude - fromLongitude);

  const a =
    Math.sin(dLat / 2) ** 2 +
    Math.cos(toRadians(fromLatitude)) *
      Math.cos(toRadians(toLatitude)) *
      Math.sin(dLng / 2) ** 2;

  return EARTH_RADIUS_METRES * 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));
}

/**
 * Format a distance for display in the UK build.
 *
 * Under 1 km reads in metres rounded to 10 m, because single-metre precision
 * implies an accuracy neither GPS nor a straight line can support. At and
 * above 1 km it reads in kilometres to one decimal place.
 */
export function formatDistance(metres: number | null | undefined): string | null {
  if (metres == null || !Number.isFinite(metres) || metres < 0) return null;

  if (metres < 1000) {
    const rounded = Math.round(metres / 10) * 10;
    // Never claim "0 m away" for a facility that is merely very close.
    return `${Math.max(rounded, 10)} m`;
  }

  return `${(metres / 1000).toFixed(1)} km`;
}

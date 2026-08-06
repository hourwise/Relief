// ============================================================
// Project "Relief" — Facility list ordering
// ============================================================

import type { Facility } from '../types';

export type SortMode = 'distance' | 'rating';

/**
 * A facility paired with its distance from the user.
 *
 * `distanceMetres` is null when the user's location is unknown — the list must
 * still render and still be sortable by rating in that case.
 */
export interface RankedFacility {
  facility: Facility;
  distanceMetres: number | null;
}

/**
 * Sort facilities for display.
 *
 * Unknown values always sort last, never first and never as zero. An unrated
 * facility is not a zero-star facility, and a facility whose distance we
 * cannot compute must not masquerade as the nearest one.
 *
 * Ordering is total and stable: ties fall back to name, so the same data always
 * renders in the same order.
 */
export function sortFacilities(
  items: readonly RankedFacility[],
  mode: SortMode,
): RankedFacility[] {
  const byName = (a: RankedFacility, b: RankedFacility) =>
    a.facility.name.localeCompare(b.facility.name);

  return [...items].sort((a, b) => {
    if (mode === 'distance') {
      const aDistance = a.distanceMetres;
      const bDistance = b.distanceMetres;
      if (aDistance == null && bDistance == null) return byName(a, b);
      if (aDistance == null) return 1;
      if (bDistance == null) return -1;
      if (aDistance !== bDistance) return aDistance - bDistance;
      return byName(a, b);
    }

    // Rating: treat null and 0 as "unrated" and sink both. The imported UK
    // dataset carries overall_score = 0 for facilities with no community
    // ratings yet, so 0 means "no rating", not "rated zero".
    const aScore = a.facility.overall_score ?? 0;
    const bScore = b.facility.overall_score ?? 0;
    const aRated = aScore > 0;
    const bRated = bScore > 0;
    if (!aRated && !bRated) return byName(a, b);
    if (!aRated) return 1;
    if (!bRated) return -1;
    if (aScore !== bScore) return bScore - aScore;
    return byName(a, b);
  });
}

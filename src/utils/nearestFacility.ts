import { getOpenStatus, type OpenStatus } from './openingHours';
import type { NearestFacility } from '../types';

/** Availability priority for the urgent journey. */
const AVAILABILITY_PRIORITY: Record<OpenStatus, number> = {
  open: 0,
  unknown: 1,
  closed: 2,
};

/**
 * Rank candidates open -> unknown -> closed, then by distance within each
 * class. The RPC remains responsible only for the spatial candidate set.
 */
export function rankNearestFacilities(
  facilities: readonly NearestFacility[],
): NearestFacility[] {
  return facilities
    .map((facility, index) => ({
      facility,
      index,
      status: getOpenStatus(facility),
    }))
    .sort((a, b) => {
      const availability =
        AVAILABILITY_PRIORITY[a.status] - AVAILABILITY_PRIORITY[b.status];
      if (availability !== 0) return availability;

      const distance = a.facility.distance_metres - b.facility.distance_metres;
      return distance !== 0 ? distance : a.index - b.index;
    })
    .map(({ facility }) => facility);
}

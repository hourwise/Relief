// ============================================================
// Project "Relief" — Opening Hours Utilities
// ============================================================

import type { Facility } from '../types';

export type OpenStatus = 'open' | 'closed' | 'unknown';

const DAY_NAMES = [
  'sunday', 'monday', 'tuesday', 'wednesday',
  'thursday', 'friday', 'saturday',
] as const;

function parseTime(time: string): number | null {
  const parts = time.split(':');
  if (parts.length !== 2) return null;
  const h = parseInt(parts[0], 10);
  const m = parseInt(parts[1], 10);
  if (isNaN(h) || isNaN(m) || h < 0 || h > 23 || m < 0 || m > 59) return null;
  return h * 60 + m;
}

/**
 * Determine whether a facility is open, closed, or unknown right now.
 *
 * Handles overnight hours: if close <= open the interval crosses midnight
 * (e.g. open 22:00, close 06:00 means open from 22:00 tonight until 06:00
 * tomorrow morning).
 *
 * Returns 'unknown' when hours data is missing or today's entry is null.
 */
export function getOpenStatus(facility: Facility): OpenStatus {
  if (facility.is_24h) return 'open';
  if (!facility.open_hours) return 'unknown';

  const today = DAY_NAMES[new Date().getDay()];
  const todayHours = facility.open_hours[today];

  if (!todayHours) return 'unknown';

  const openMinutes = parseTime(todayHours.open);
  const closeMinutes = parseTime(todayHours.close);
  if (openMinutes === null || closeMinutes === null) return 'unknown';

  const now = new Date();
  const nowMinutes = now.getHours() * 60 + now.getMinutes();

  if (closeMinutes <= openMinutes) {
    // Overnight: open from openMinutes tonight through midnight and into
    // the next morning until closeMinutes.
    return nowMinutes >= openMinutes || nowMinutes <= closeMinutes
      ? 'open'
      : 'closed';
  }

  // Normal same-day window
  return nowMinutes >= openMinutes && nowMinutes <= closeMinutes
    ? 'open'
    : 'closed';
}

/**
 * Legacy boolean helper — returns true only for 'open'.
 * Prefer getOpenStatus() for UI that can show all three states.
 */
export function isOpenNow(facility: Facility): boolean {
  return getOpenStatus(facility) === 'open';
}

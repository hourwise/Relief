// ============================================================
// Project "Relief" — Opening Hours Utilities
// ============================================================

import type { OpenHours } from '../types';

export type OpenStatus = 'open' | 'closed' | 'unknown';

/** The minimum shape needed to judge opening status. */
export interface OpeningHoursSource {
  is_24h?: boolean | null;
  open_hours: OpenHours | null;
}

const DAY_NAMES = [
  'sunday',
  'monday',
  'tuesday',
  'wednesday',
  'thursday',
  'friday',
  'saturday',
] as const;

function parseTime(time: string): number | null {
  const parts = time.split(':');
  if (parts.length !== 2) return null;
  const h = parseInt(parts[0], 10);
  const m = parseInt(parts[1], 10);
  if (isNaN(h) || isNaN(m) || h < 0 || h > 23 || m < 0 || m > 59) {
    return null;
  }
  return h * 60 + m;
}

function isHoursEntry(
  value: unknown,
): value is { open: string; close: string } {
  return (
    typeof value === 'object' &&
    value !== null &&
    typeof (value as { open?: unknown }).open === 'string' &&
    typeof (value as { close?: unknown }).close === 'string'
  );
}

function getWindowStatus(
  entry: { open: string; close: string } | null | undefined,
  nowMinutes: number,
): OpenStatus {
  if (!entry) return 'unknown';

  const openMinutes = parseTime(entry.open);
  const closeMinutes = parseTime(entry.close);
  if (openMinutes === null || closeMinutes === null) return 'unknown';

  if (closeMinutes <= openMinutes) {
    // Overnight: open from openMinutes tonight through midnight and into the
    // next morning until closeMinutes. Equal values retain the existing
    // all-day interpretation used by the app.
    return nowMinutes >= openMinutes || nowMinutes <= closeMinutes
      ? 'open'
      : 'closed';
  }

  return nowMinutes >= openMinutes && nowMinutes <= closeMinutes
    ? 'open'
    : 'closed';
}

/**
 * Determine whether a facility is open, closed, or unknown right now.
 * Missing, null, and malformed hours stay unknown. Overnight schedules from
 * the previous day are also considered during the early-morning carry-over.
 */
export function getOpenStatus(facility: OpeningHoursSource): OpenStatus {
  if (facility.is_24h) return 'open';
  if (!facility.open_hours) return 'unknown';

  const now = new Date();
  const dayIndex = now.getDay();
  const today = DAY_NAMES[dayIndex];
  const previousDay = DAY_NAMES[(dayIndex + DAY_NAMES.length - 1) % DAY_NAMES.length];
  const nowMinutes = now.getHours() * 60 + now.getMinutes();
  const todayEntry = facility.open_hours[today];
  const previousEntry = facility.open_hours[previousDay];

  // Only an overnight previous-day entry may carry into today.
  if (isHoursEntry(previousEntry)) {
    const previousOpen = parseTime(previousEntry.open);
    const previousClose = parseTime(previousEntry.close);
    if (
      previousOpen !== null &&
      previousClose !== null &&
      previousClose <= previousOpen &&
      nowMinutes <= previousClose
    ) {
      return 'open';
    }
  }

  return isHoursEntry(todayEntry)
    ? getWindowStatus(todayEntry, nowMinutes)
    : 'unknown';
}

/** Legacy boolean helper — returns true only for confirmed open. */
export function isOpenNow(facility: OpeningHoursSource): boolean {
  return getOpenStatus(facility) === 'open';
}

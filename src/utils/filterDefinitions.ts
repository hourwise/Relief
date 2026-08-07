// ============================================================
// Project "Relief" — Filter definitions
// ============================================================
// One source of truth for which filters exist, what they are
// called, and how they map to the database. The Filters screen
// renders from this, and the query layer reads the same keys, so
// the UI and the query cannot drift apart.
//
// WHY SO FEW FILTERS ARE EXPOSED
// ------------------------------
// The schema carries far more amenity columns than appear here.
// Most are not populated yet: the UK import filled only a handful
// of fields, so a switch for (say) "Grab rails" would look like it
// worked while always returning nothing — indistinguishable, to a
// user, from a broken service.
//
// Counts below are published facilities with the column true,
// measured against the live database on 2026-08-07 (15,584
// published rows). Only columns with meaningful coverage are
// offered. The rest stay in the schema for future ingestion and
// community contributions; see HIDDEN_UNTIL_POPULATED.
// ============================================================

import {
  type FacilityFilters,
  type FilterableBooleanColumn,
} from '../types';

export interface BooleanFilterDefinition {
  key: FilterableBooleanColumn;
  label: string;
  description?: string;
  /** Published facilities with this column true on 2026-08-07. */
  liveCount: number;
}

/**
 * Boolean filters offered to users, in display order.
 *
 * `satisfies` keeps every key checked against the generated schema, so a
 * filter for a column the database does not have is a compile error.
 */
export const EXPOSED_BOOLEAN_FILTERS = [
  {
    key: 'is_24h',
    label: 'Open 24 hours',
    description: 'Always open, no closing time.',
    liveCount: 984,
  },
  {
    key: 'is_accessible',
    label: 'Accessible',
    description: 'Recorded as an accessible facility.',
    liveCount: 6374,
  },
  {
    key: 'requires_radar_key',
    label: 'RADAR Key',
    description: 'Opened with a National Key Scheme RADAR key.',
    liveCount: 2453,
  },
  {
    key: 'has_baby_changing',
    label: 'Baby changing',
    description: 'Baby-changing facilities recorded.',
    liveCount: 4889,
  },
  {
    key: 'is_gender_neutral',
    label: 'Gender-neutral',
    description: 'Recorded as gender-neutral.',
    liveCount: 1766,
  },
  {
    key: 'is_family_friendly',
    label: 'Family friendly',
    description: 'Suitable for families with children.',
    liveCount: 291,
  },
  {
    key: 'has_staff_nearby',
    label: 'Staff nearby',
    description: 'Staff are usually on site.',
    liveCount: 829,
  },
] as const satisfies readonly BooleanFilterDefinition[];

export type ExposedFilterKey = (typeof EXPOSED_BOOLEAN_FILTERS)[number]['key'];

export const EXPOSED_FILTER_KEYS: readonly ExposedFilterKey[] =
  EXPOSED_BOOLEAN_FILTERS.map((f) => f.key);

/**
 * Real columns deliberately NOT offered, because zero published facilities
 * have them set. Kept here rather than deleted so the reason is recorded and
 * so a test can assert they stay hidden until the data arrives.
 *
 * Every one of these measured 0 on 2026-08-07.
 */
export const HIDDEN_UNTIL_POPULATED: readonly FilterableBooleanColumn[] = [
  'is_disabled_access',
  'is_single_room',
  'has_floor_to_ceiling_cubicles',
  'is_quiet',
  'is_single_occupancy',
  'has_wheelchair_access',
  'has_adult_changing_place',
  'has_lift',
  'has_grab_rails',
  'has_baby_changing_inside',
  'has_separate_changing_room',
  'has_family_room',
  'has_family_toilet',
  'has_pram_access',
  'has_soap',
  'has_paper_towels',
  'has_hand_dryer',
  'has_mirror',
  'has_shelf',
  'has_hooks',
  'has_sanitary_bins',
  'has_free_period_products',
  'has_drinking_water',
  'has_cctv',
  'is_women_friendly',
  'is_picnic_area',
] as const satisfies readonly FilterableBooleanColumn[];

// --- Cost ---

/**
 * Cost is tri-state rather than a switch, because `is_free = false` is a real
 * request ("show me paid facilities", 3,221 of them) and not the absence of a
 * filter. A plain on/off toggle cannot express it.
 */
export type CostOption = 'any' | 'free' | 'paid';

export const COST_OPTIONS: readonly { value: CostOption; label: string }[] = [
  { value: 'any', label: 'Any' },
  { value: 'free', label: 'Free' },
  { value: 'paid', label: 'Paid' },
];

/** The `is_free` value a cost choice implies, or undefined for "don't care". */
export function costOptionToIsFree(option: CostOption): boolean | undefined {
  if (option === 'free') return true;
  if (option === 'paid') return false;
  return undefined;
}

/** Read the current cost choice back out of a filter set. */
export function costOptionFromFilters(
  filters: Partial<FacilityFilters>,
): CostOption {
  if (filters.is_free === true) return 'free';
  if (filters.is_free === false) return 'paid';
  return 'any';
}

/** Apply a cost choice, removing the key entirely for "any". */
export function applyCostOption(
  filters: Partial<FacilityFilters>,
  option: CostOption,
): Partial<FacilityFilters> {
  const next = { ...filters };
  const isFree = costOptionToIsFree(option);
  if (isFree === undefined) delete next.is_free;
  else next.is_free = isFree;
  return next;
}

/**
 * Count the filters a user has actually applied.
 *
 * An explicit `false` counts: "Paid" is a filter. Counting only `true` made
 * the Filters button read "Filters" while a paid-only filter was active.
 * `min_rating` is not counted because it is not offered — no published
 * facility has a rating yet.
 */
export function countActiveFilters(filters: Partial<FacilityFilters>): number {
  // Cost is counted separately because it is tri-state; the rest are switches.
  let count = filters.is_free !== undefined ? 1 : 0;
  if (filters.open_now === true) count += 1;
  for (const key of EXPOSED_FILTER_KEYS) {
    if (filters[key] === true) count += 1;
  }
  return count;
}

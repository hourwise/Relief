// ============================================================
// Relief — exposed filters vs. real data
// ============================================================
// The Filters screen must be truthful about the current dataset.
// Offering a switch that always returns nothing is, to a user,
// indistinguishable from a broken service — so these tests pin
// which filters are offered and why.
//
// Coverage figures were measured against the live database on
// 2026-08-07 across 15,584 published facilities.
// ============================================================

import {
  applyCostOption,
  costOptionFromFilters,
  costOptionToIsFree,
  countActiveFilters,
  COST_OPTIONS,
  EXPOSED_BOOLEAN_FILTERS,
  EXPOSED_FILTER_KEYS,
  HIDDEN_UNTIL_POPULATED,
} from '../src/utils/filterDefinitions';
import { FILTERABLE_BOOLEAN_COLUMNS } from '../src/types';
import { filterColumnMap } from '../src/utils/facilityQuery';
import {
  assertDeepEqual,
  assertEqual,
  assertTrue,
  section,
} from './helpers/harness';

const REAL_COLUMNS = FILTERABLE_BOOLEAN_COLUMNS as readonly string[];

section('every exposed filter maps to a real database column');

for (const filter of EXPOSED_BOOLEAN_FILTERS) {
  assertTrue(
    `${filter.key} is a real facilities column`,
    REAL_COLUMNS.includes(filter.key),
  );
  assertTrue(`${filter.key} has a label`, filter.label.length > 0);
  // The whole point: an offered filter must be able to return something.
  assertTrue(`${filter.key} has live data (${filter.liveCount})`, filter.liveCount > 0);
  assertDeepEqual(
    `${filter.key} is emitted as a column equality filter`,
    filterColumnMap({ [filter.key]: true }),
    [{ column: filter.key, value: true }],
  );
}

assertEqual('seven boolean filters are offered', EXPOSED_BOOLEAN_FILTERS.length, 7);

section('zero-data filters are hidden, not deleted');

// These columns exist and are kept in the schema for future ingestion, but no
// published facility sets them, so they must not be offered.
for (const column of HIDDEN_UNTIL_POPULATED) {
  assertTrue(`${column} is still a real column`, REAL_COLUMNS.includes(column));
  assertEqual(
    `${column} is not offered as a filter`,
    (EXPOSED_FILTER_KEYS as readonly string[]).includes(column),
    false,
  );
}

// Named explicitly, because these are the ones the device test found returning
// empty results while looking like they worked.
const MUST_STAY_HIDDEN = [
  'is_single_room',
  'has_floor_to_ceiling_cubicles',
  'is_quiet',
  'has_wheelchair_access',
  'has_adult_changing_place',
  'has_lift',
  'has_grab_rails',
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
  'is_picnic_area',
];

for (const column of MUST_STAY_HIDDEN) {
  assertEqual(
    `${column} is not exposed`,
    (EXPOSED_FILTER_KEYS as readonly string[]).includes(column),
    false,
  );
  assertTrue(
    `${column} is recorded as hidden-until-populated`,
    (HIDDEN_UNTIL_POPULATED as readonly string[]).includes(column),
  );
}

// Every real column is accounted for: either offered or explicitly hidden.
// This is what stops a new column silently appearing in neither list.
for (const column of REAL_COLUMNS) {
  const offered = (EXPOSED_FILTER_KEYS as readonly string[]).includes(column);
  const hidden = (HIDDEN_UNTIL_POPULATED as readonly string[]).includes(column);
  // is_free is handled by the tri-state cost control, not a switch.
  const isCost = column === 'is_free';
  assertTrue(
    `${column} is either offered, hidden or cost-controlled`,
    offered || hidden || isCost,
  );
}

section('cost is tri-state: Free and Paid are both real requests');

assertEqual('three cost options', COST_OPTIONS.length, 3);
assertEqual('Any means no constraint', costOptionToIsFree('any'), undefined);
assertEqual('Free means is_free = true', costOptionToIsFree('free'), true);
assertEqual('Paid means is_free = false', costOptionToIsFree('paid'), false);

assertDeepEqual(
  'Free emits is_free = true',
  filterColumnMap(applyCostOption({}, 'free')),
  [{ column: 'is_free', value: true }],
);
assertDeepEqual(
  'Paid emits is_free = false',
  filterColumnMap(applyCostOption({}, 'paid')),
  [{ column: 'is_free', value: false }],
);
assertDeepEqual(
  'Any emits no cost filter at all',
  filterColumnMap(applyCostOption({ is_free: true }, 'any')),
  [],
);

assertEqual('Free reads back as free', costOptionFromFilters({ is_free: true }), 'free');
assertEqual('Paid reads back as paid', costOptionFromFilters({ is_free: false }), 'paid');
assertEqual('absent reads back as any', costOptionFromFilters({}), 'any');

// Switching cost must not disturb other filters.
assertDeepEqual(
  'changing cost preserves other filters',
  applyCostOption({ is_accessible: true, is_free: true }, 'paid'),
  { is_accessible: true, is_free: false },
);

section('open_now stays client-derived');

// open_hours is jsonb evaluated against the current time; it is not a column
// equality check and must never be sent to PostgREST as one.
assertDeepEqual(
  'open_now is not emitted as a column filter',
  filterColumnMap({ open_now: true }),
  [],
);
assertDeepEqual(
  'open_now alongside a real filter emits only the real one',
  filterColumnMap({ open_now: true, is_accessible: true }),
  [{ column: 'is_accessible', value: true }],
);
assertEqual(
  'open_now is not in the boolean filter list',
  (EXPOSED_FILTER_KEYS as readonly string[]).includes('open_now'),
  false,
);

section('rating is not offered while no facility is rated');

// 0 of 15,584 published facilities have overall_score > 0, so every threshold
// above "Any" returned an empty list.
assertDeepEqual('min_rating is not a column filter', filterColumnMap({ min_rating: 4 }), []);
assertEqual('min_rating does not count as an active filter', countActiveFilters({ min_rating: 4 }), 0);

section('active filter count');

assertEqual('nothing set counts zero', countActiveFilters({}), 0);
assertEqual('Free counts', countActiveFilters({ is_free: true }), 1);
// Regression: counting only `true` left the button reading "Filters" while a
// paid-only filter was applied.
assertEqual('Paid counts too', countActiveFilters({ is_free: false }), 1);
assertEqual('open_now counts', countActiveFilters({ open_now: true }), 1);
assertEqual(
  'combined filters count together',
  countActiveFilters({ is_free: false, is_accessible: true, open_now: true }),
  3,
);
assertEqual(
  'hidden columns do not inflate the count',
  countActiveFilters({ has_soap: true, is_accessible: true } as never),
  1,
);

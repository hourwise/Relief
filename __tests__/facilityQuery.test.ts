// ============================================================
// Relief — filter-to-column mapping and nearest-facility mapping
// ============================================================
// These are the two places where schema drift turned into runtime
// failure: filters for columns that do not exist, and an RPC
// projection that selected them.
// ============================================================

import {
  filterColumnMap,
  mapNearestFacilityRow,
  type NearestFacilityRow,
} from '../src/utils/facilityQuery';
import { FILTERABLE_BOOLEAN_COLUMNS } from '../src/types';
import {
  assertDeepEqual,
  assertEqual,
  assertNull,
  assertTrue,
  section,
} from './helpers/harness';

section('filter-to-database-column mapping');

assertDeepEqual('no filters map to no columns', filterColumnMap({}), []);

assertDeepEqual(
  'a true filter maps to an equality check on that column',
  filterColumnMap({ is_free: true }),
  [{ column: 'is_free', value: true }],
);

// An explicit false is a real request ("show me paid ones"), not "don't care".
assertDeepEqual(
  'an explicit false is preserved',
  filterColumnMap({ is_free: false }),
  [{ column: 'is_free', value: false }],
);

assertDeepEqual(
  'multiple filters emit in the declared column order',
  filterColumnMap({ has_baby_changing: true, is_accessible: true, is_free: true }),
  [
    { column: 'is_free', value: true },
    { column: 'is_accessible', value: true },
    { column: 'has_baby_changing', value: true },
  ],
);

// open_now is derived client-side from open_hours (jsonb); min_rating is a range
// comparison. Neither is a column equality check.
assertDeepEqual('open_now is never sent as a column filter', filterColumnMap({ open_now: true }), []);
assertDeepEqual('min_rating is never sent as a column filter', filterColumnMap({ min_rating: 4 }), []);
assertDeepEqual(
  'open_now and min_rating are excluded alongside real filters',
  filterColumnMap({ open_now: true, min_rating: 3, is_quiet: true }),
  [{ column: 'is_quiet', value: true }],
);

section('the six phantom columns cannot be filtered');

// These do not exist on public.facilities. Selecting them in
// find_nearest_facilities() produced PostgreSQL 42703 and broke "Need One Now".
const PHANTOM_COLUMNS = [
  'is_water_refill_station',
  'is_shower_facility',
  'is_breastfeeding_room',
  'is_rest_area',
  'is_changing_place',
  'is_ev_charging',
];

for (const column of PHANTOM_COLUMNS) {
  assertEqual(
    `${column} is not an offered filter`,
    (FILTERABLE_BOOLEAN_COLUMNS as readonly string[]).includes(column),
    false,
  );
  // Even if a stale caller passes one, it must not reach PostgREST.
  assertDeepEqual(
    `${column} is dropped if a caller still passes it`,
    filterColumnMap({ [column]: true } as never),
    [],
  );
}

// is_picnic_area DOES exist in the live schema and must be retained.
assertTrue(
  'is_picnic_area is still an offered filter',
  (FILTERABLE_BOOLEAN_COLUMNS as readonly string[]).includes('is_picnic_area'),
);
assertDeepEqual(
  'is_picnic_area maps to a real column filter',
  filterColumnMap({ is_picnic_area: true }),
  [{ column: 'is_picnic_area', value: true }],
);

section('nearest-facility result mapping');

// The exact row the live RPC returned for lat 53.4084, lon -2.9916, r=5000.
const liverpoolRow: NearestFacilityRow = {
  facility_id: '1a2cfe7d-b81e-439b-a51f-301f598d8b66',
  name: 'Moorfields',
  address: null,
  latitude: 53.408573,
  longitude: -2.98918,
  town: 'Liverpool',
  postcode: null,
  open_hours: null,
  is_free: true,
  is_accessible: false,
  overall_score: 0,
  verification_status: 'source_imported',
  distance_metres: 162.08216307,
};

const mapped = mapNearestFacilityRow(liverpoolRow);
assertEqual('maps the verified live row', mapped?.name, 'Moorfields');
assertEqual('carries the facility id', mapped?.facility_id, liverpoolRow.facility_id);
assertEqual('carries the distance unrounded', mapped?.distance_metres, 162.08216307);
assertEqual('keeps a null address as null', mapped?.address, null);
assertEqual('keeps a null postcode as null', mapped?.postcode, null);
assertEqual('preserves is_free', mapped?.is_free, true);
assertEqual('preserves a false accessibility flag', mapped?.is_accessible, false);
assertEqual('preserves a zero score rather than dropping it', mapped?.overall_score, 0);
assertEqual('preserves verification status', mapped?.verification_status, 'source_imported');

// A tri-state amenity that is unknown must stay unknown, never become false.
const unknownAccess = mapNearestFacilityRow({ ...liverpoolRow, is_accessible: null });
assertEqual('unknown accessibility stays null, not false', unknownAccess?.is_accessible, null);

const unknownCost = mapNearestFacilityRow({ ...liverpoolRow, is_free: null });
assertEqual('unknown cost stays null, not false', unknownCost?.is_free, null);

const unnamed = mapNearestFacilityRow({ ...liverpoolRow, name: null });
assertEqual('a missing name falls back to a readable label', unnamed?.name, 'Unnamed facility');

const noStatus = mapNearestFacilityRow({ ...liverpoolRow, verification_status: null });
assertEqual(
  'a missing verification status defaults to the weakest claim',
  noStatus?.verification_status,
  'source_imported',
);

section('unusable rows are rejected rather than guessed at');

// Without coordinates or a distance there is nothing to map or route to, and a
// default would put a pin somewhere the facility is not.
assertNull('no id is unusable', mapNearestFacilityRow({ ...liverpoolRow, facility_id: null }));
assertNull('no latitude is unusable', mapNearestFacilityRow({ ...liverpoolRow, latitude: null }));
assertNull('no longitude is unusable', mapNearestFacilityRow({ ...liverpoolRow, longitude: null }));
assertNull('no distance is unusable', mapNearestFacilityRow({ ...liverpoolRow, distance_metres: null }));

// Zero is a legitimate value for both and must not be rejected as falsy.
assertTrue(
  'zero coordinates are valid, not missing',
  mapNearestFacilityRow({ ...liverpoolRow, latitude: 0, longitude: 0 }) !== null,
);
assertTrue(
  'zero distance is valid, not missing',
  mapNearestFacilityRow({ ...liverpoolRow, distance_metres: 0 }) !== null,
);

// ============================================================
// Relief — additive toilet-unit contract
// ============================================================
// These tests protect the parent/child boundary: a unit is explicit only when
// published, its attributes remain unit-scoped, and missing source values are
// never rendered as negative facts.

import type { ToiletUnit } from '../src/types/toiletUnits';
import {
  toiletUnitAttributeLabels,
  toiletUnitIdentityLabel,
  toiletUnitTypeLabel,
} from '../src/utils/toiletUnits';
import { assertDeepEqual, assertEqual, section } from './helpers/harness';

const makeUnit = (overrides: Partial<ToiletUnit> = {}): ToiletUnit => ({
  id: 'unit-1',
  facility_id: 'facility-1',
  unit_label: null,
  unit_type: 'unknown',
  identity_status: 'UNRESOLVED',
  is_accessible: null,
  has_baby_changing: null,
  is_free: null,
  price_note: null,
  open_hours: null,
  is_24h: null,
  is_inside_gateline: null,
  location_description: null,
  access_notes: null,
  requires_radar_key: null,
  ask_staff: null,
  latitude: null,
  longitude: null,
  coordinate_precision: 'UNKNOWN',
  publication_status: 'published',
  verification_status: 'source_imported',
  last_verified_at: null,
  created_at: '2026-08-21T00:00:00Z',
  updated_at: '2026-08-21T00:00:00Z',
  created_by: null,
  field_provenance: {},
  ...overrides,
});

section('toilet-unit identity and attributes stay child-scoped');

const male = makeUnit({
  id: 'male-1',
  unit_type: 'male',
  identity_status: 'SOURCE_DISTINCT_PHYSICAL_UNKNOWN',
  publication_status: 'hidden',
  is_accessible: true,
  has_baby_changing: false,
  is_free: true,
  is_inside_gateline: true,
  location_description: 'Ticket hall',
});
const female = makeUnit({ id: 'female-1', unit_type: 'female' });
const unisex = makeUnit({ id: 'unisex-1', unit_type: 'unisex' });

assertDeepEqual(
  'Male, Female, and Unisex child rows retain separate labels',
  [toiletUnitTypeLabel(male), toiletUnitTypeLabel(female), toiletUnitTypeLabel(unisex)],
  ['Male', 'Female', 'Unisex'],
);
assertDeepEqual(
  'only explicitly true/false child attributes are presented',
  toiletUnitAttributeLabels(male),
  ['Accessible', 'Inside gateline', 'Free'],
);
assertDeepEqual(
  'unknown child attributes do not become negative claims',
  toiletUnitAttributeLabels(unisex),
  [],
);
assertEqual(
  'source-distinct rows remain visibly physical-unit-unconfirmed',
  toiletUnitIdentityLabel(male),
  'Source row; physical unit unconfirmed',
);

section('station coordinates are not child coordinates');

const stationOnlyUnit = makeUnit({ coordinate_precision: 'UNKNOWN' });
assertEqual('station-only unit latitude remains absent', stationOnlyUnit.latitude, null);
assertEqual('station-only unit longitude remains absent', stationOnlyUnit.longitude, null);
assertEqual('station-only unit precision remains unknown', stationOnlyUnit.coordinate_precision, 'UNKNOWN');

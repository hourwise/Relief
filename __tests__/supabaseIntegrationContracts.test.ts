import {
  buildCorrectionInsert,
  buildFacilitySubmissionInsert,
  buildFavouriteInsert,
  buildFindNearestFacilitiesArgs,
  buildOwnedFacilityFilter,
  buildTemporaryReportInsert,
} from '../src/services/integrationContracts';
import { SUPABASE_AUTH_OPTIONS } from '../src/services/supabaseAuthConfig';
import { describeSupabaseError } from '../src/utils/supabaseErrors';
import { assertDeepEqual, assertEqual, assertTrue, section } from './helpers/harness';

section('session restoration contract');

assertTrue('sessions use persistent storage', SUPABASE_AUTH_OPTIONS.persistSession);
assertTrue('token refresh is enabled', SUPABASE_AUTH_OPTIONS.autoRefreshToken);
assertEqual('URL detection is disabled for native auth', SUPABASE_AUTH_OPTIONS.detectSessionInUrl, false);

section('RPC request shape');

assertDeepEqual(
  'nearest RPC receives the generated argument names',
  buildFindNearestFacilitiesArgs(53.4084, -2.9916, 25000, 25),
  {
    user_latitude: 53.4084,
    user_longitude: -2.9916,
    search_radius_metres: 25000,
    result_limit: 25,
  },
);

section('authenticated write request shapes');

assertDeepEqual(
  'favourite insert carries the authenticated user id',
  buildFavouriteInsert('user-1', 'facility-1'),
  { user_id: 'user-1', facility_id: 'facility-1' },
);
assertDeepEqual(
  'favourite removal is scoped to the authenticated user and facility',
  buildOwnedFacilityFilter('user-1', 'facility-1'),
  { user_id: 'user-1', facility_id: 'facility-1' },
);

assertDeepEqual(
  'temporary report insert carries expiry and pending state',
  buildTemporaryReportInsert('user-1', 'facility-1', 'out_of_order', 'Closed', '2026-08-12T20:00:00.000Z'),
  {
    facility_id: 'facility-1',
    user_id: 'user-1',
    type: 'out_of_order',
    notes: 'Closed',
    expires_at: '2026-08-12T20:00:00.000Z',
    is_expired: false,
  },
);

assertDeepEqual(
  'correction insert carries the authenticated user id and pending status',
  buildCorrectionInsert('user-1', 'facility-1', 'name', 'Old', 'New', 'Sign changed'),
  {
    facility_id: 'facility-1',
    user_id: 'user-1',
    field: 'name',
    old_value: 'Old',
    new_value: 'New',
    notes: 'Sign changed',
    status: 'pending',
  },
);

const submission = {
  name: 'Example facility',
  address: '1 Example Street',
  latitude: 53.4,
  longitude: -2.9,
  postcode: 'L1 1AA',
  town: 'Liverpool',
  country: 'United Kingdom',
  access_notes: '',
  is_free: true,
  price_note: '',
  open_hours: null,
  photos: [],
  is_accessible: false,
  is_disabled_access: false,
  has_baby_changing: false,
  has_family_room: false,
  is_gender_neutral: false,
  is_single_occupancy: false,
  is_24h: false,
  notes: '',
  access_codes: '',
  submission_notes: '',
};
assertDeepEqual(
  'facility submission insert adds only authenticated ownership and pending state',
  buildFacilitySubmissionInsert('user-1', submission),
  { ...submission, user_id: 'user-1', status: 'pending' },
);

section('failed-RLS and offline error handling');

assertEqual(
  'RLS denial is safe and actionable',
  describeSupabaseError({ code: '42501', message: 'new row violates row-level security policy' }, 'Fallback'),
  'This action is not available for your account right now.',
);
assertEqual(
  'offline errors do not leak backend details',
  describeSupabaseError({ message: 'fetch failed: java.net.UnknownHostException: supabase.co' }, 'Fallback'),
  'No connection. Check your internet and try again.',
);
assertEqual(
  'schema drift is distinguished from a generic failure',
  describeSupabaseError({ code: '42703' }, 'Fallback'),
  'The facility service is out of date. Please update the app.',
);

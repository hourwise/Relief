// ============================================================
// Project "Relief" — Core Type Definitions
// ============================================================
// Facility and filter types are DERIVED from the generated
// Supabase types (src/types/database.types.ts) rather than
// hand-maintained. Hand-written copies previously drifted from
// the live schema and invented six columns that do not exist,
// which is what broke find_nearest_facilities() at runtime.
// Deriving them means the compiler now rejects any reference to
// a column the database does not have.
// ============================================================

import type { Tables } from './database.types';

export type { Database, Json } from './database.types';

type FacilityRow = Tables<'facilities'>;

// --- Facility ---

export type PublicationStatus =
  | 'published'
  | 'hidden'
  | 'under_review'
  | 'removed';

export type VerificationStatus =
  | 'source_imported'
  | 'source_verified'
  | 'community_confirmed'
  | 'staff_verified'
  | 'disputed'
  | 'stale';

export interface OpenHours {
  [day: string]: { open: string; close: string } | null;
}

/**
 * A published facility as the client consumes it.
 *
 * `location` (PostGIS geography) and `field_provenance` are omitted: they are
 * server-side concerns the UI never reads. Status columns are narrowed from
 * `string` to their real domains, and `open_hours` from `Json` to `OpenHours`.
 *
 * Every other field — including its nullability — comes straight from the
 * live schema. Amenity booleans are genuinely tri-state: true = yes,
 * false = no, null = unknown. Null must never be rendered as "no".
 */
export interface Facility
  extends Omit<
    FacilityRow,
    | 'location'
    | 'field_provenance'
    | 'open_hours'
    | 'publication_status'
    | 'verification_status'
  > {
  open_hours: OpenHours | null;
  publication_status: PublicationStatus;
  verification_status: VerificationStatus;
}

// --- Filters ---

/**
 * The boolean columns that actually exist on `facilities`, computed from the
 * generated row type. This is the gate that keeps phantom filters out.
 */
type BooleanFacilityColumn = {
  [K in keyof FacilityRow]-?: NonNullable<FacilityRow[K]> extends boolean
    ? K
    : never;
}[keyof FacilityRow];

/**
 * Boolean columns exposed as user-facing filters, in the order they are
 * offered. `satisfies` makes this list unforgeable: adding a column the
 * database does not have is a compile error, not a runtime 42703.
 *
 * Deliberately absent, because the live schema has no such columns:
 *   is_water_refill_station, is_shower_facility, is_breastfeeding_room,
 *   is_rest_area, is_changing_place, is_ev_charging
 *
 * `is_picnic_area` IS present in the live schema and is retained.
 *
 * `is_verified` is a real boolean column but is intentionally not a filter —
 * it is legacy, superseded by `verification_status`.
 */
export const FILTERABLE_BOOLEAN_COLUMNS = [
  // Cost and core access
  'is_free',
  'is_accessible',
  'is_disabled_access',
  'is_24h',
  // Privacy
  'is_single_room',
  'has_floor_to_ceiling_cubicles',
  'is_quiet',
  'is_gender_neutral',
  'is_single_occupancy',
  // Accessibility
  'has_wheelchair_access',
  'requires_radar_key',
  'has_adult_changing_place',
  'has_lift',
  'has_grab_rails',
  // Baby and family
  'has_baby_changing',
  'has_baby_changing_inside',
  'has_separate_changing_room',
  'has_family_room',
  'has_family_toilet',
  'has_pram_access',
  // Equipment
  'has_soap',
  'has_paper_towels',
  'has_hand_dryer',
  'has_mirror',
  'has_shelf',
  'has_hooks',
  'has_sanitary_bins',
  'has_free_period_products',
  'has_drinking_water',
  // Safety and setting
  'has_staff_nearby',
  'has_cctv',
  'is_women_friendly',
  'is_family_friendly',
  'is_picnic_area',
] as const satisfies readonly BooleanFacilityColumn[];

export type FilterableBooleanColumn =
  (typeof FILTERABLE_BOOLEAN_COLUMNS)[number];

/**
 * `open_now` and `min_rating` are not plain column equality checks:
 * `open_now` is evaluated client-side from `open_hours`, and `min_rating`
 * maps to `overall_score >= n`.
 */
export type FacilityFilters = Record<FilterableBooleanColumn, boolean> & {
  open_now: boolean;
  min_rating: number;
};

// --- Nearest facility (from the PostGIS RPC) ---

/**
 * The repaired find_nearest_facilities() response.
 *
 * Deliberately narrow: only what the emergency result renders. It is NOT a
 * `Facility`. Widening this back to a full facility row is what coupled the
 * most urgent journey in the app to every column on the table.
 */
export interface NearestFacility {
  facility_id: string;
  name: string;
  address: string | null;
  latitude: number;
  longitude: number;
  town: string | null;
  postcode: string | null;
  open_hours: OpenHours | null;
  is_free: boolean | null;
  is_accessible: boolean | null;
  overall_score: number | null;
  verification_status: VerificationStatus;
  distance_metres: number;
}

export interface NearestFacilityResult {
  facility: NearestFacility;
  distance_metres: number;
}

// --- User ---
export interface UserProfile {
  id: string;
  email: string;
  display_name: string | null;
  avatar_url: string | null;
  created_at: string;
  has_lifetime_access: boolean;
  subscription_tier: 'free' | 'plus' | null;
  subscription_expires_at: string | null;
}

// --- Report ---
export interface FacilityReport {
  id: string;
  facility_id: string;
  user_id: string;
  type: 'temporary' | 'permanent';
  reason:
    | 'out_of_order'
    | 'no_water'
    | 'cleaning'
    | 'busy'
    | 'closed_permanently'
    | 'refurbishment';
  notes: string;
  expires_at: string | null;
  created_at: string;
}

// --- Badge ---
export type BadgeType =
  | 'explorer'
  | 'community_hero'
  | 'accessibility_champion'
  | 'family_helper';

export interface UserBadge {
  id: string;
  user_id: string;
  badge: BadgeType;
  awarded_at: string;
}

// --- Saved Profile ---
export type SavedProfileMode =
  | 'ibs'
  | 'family'
  | 'accessibility'
  | 'pregnancy'
  | 'neurodivergent'
  | 'elderly';

export interface SavedProfile {
  id: string;
  user_id: string;
  mode: SavedProfileMode;
  name: string;
  preferences: ProfilePreferences;
  created_at: string;
}

export interface ProfilePreferences {
  requires_accessible: boolean;
  requires_baby_changing: boolean;
  requires_family_room: boolean;
  requires_gender_neutral: boolean;
  requires_single_occupancy: boolean;
  requires_quiet: boolean;
  requires_radar_key: boolean;
  requires_adult_changing: boolean;
  min_rating: number;
}

// --- Favourite ---
export interface Favourite {
  id: string;
  user_id: string;
  facility_id: string;
  created_at: string;
}

// --- Navigation ---

/**
 * `Main` is reachable without a session. `Auth` is a modal presented only when
 * an account-dependent action is attempted, never as a gate on discovery.
 */
export type RootStackParamList = {
  Main: undefined;
  Auth: { reason?: string } | undefined;
  AboutRelief: undefined;
};

export type AuthStackParamList = {
  Login: { reason?: string } | undefined;
  Register: undefined;
};

export type MainTabParamList = {
  Find: undefined;
  Favourites: undefined;
  Profile: undefined;
};

/**
 * The Find tab's stack. `FindHome` hosts the shared Map/List experience.
 */
export type FindStackParamList = {
  FindHome: undefined;
  FacilityDetail: { facilityId: string };
  AddFacility: undefined;
  ReportFacility: { facilityId: string };
  CorrectInfo: { facilityId: string };
  AdvancedFilters: undefined;
};

export type ProfileStackParamList = {
  ProfileMain: undefined;
};

// ============================================================
// Project "Relief" — Core Type Definitions
// ============================================================

// --- Facility ---
export interface Facility {
  id: string;
  name: string;
  address: string | null;
  latitude: number;
  longitude: number;
  postcode: string | null;
  town: string | null;
  country: string;

  // Details
  photos: string[];
  open_hours: OpenHours | null;
  is_free: boolean | null;
  price_note?: string;
  access_notes: string;
  last_verified_at: string | null;

  // Amenities — nullable: true=yes, false=no, null=unknown
  is_accessible: boolean | null;
  is_disabled_access: boolean | null;
  has_baby_changing: boolean | null;
  has_family_room: boolean | null;
  is_gender_neutral: boolean | null;
  is_single_occupancy: boolean | null;
  is_24h: boolean | null;

  // Privacy
  is_single_room: boolean | null;
  has_floor_to_ceiling_cubicles: boolean | null;
  is_quiet: boolean | null;

  // Accessibility
  has_wheelchair_access: boolean | null;
  requires_radar_key: boolean | null;
  has_adult_changing_place: boolean | null;
  has_lift: boolean | null;
  has_grab_rails: boolean | null;

  // Baby
  has_baby_changing_inside: boolean | null;
  has_separate_changing_room: boolean | null;
  has_family_toilet: boolean | null;
  has_pram_access: boolean | null;

  // Equipment
  has_soap: boolean | null;
  has_paper_towels: boolean | null;
  has_hand_dryer: boolean | null;
  has_mirror: boolean | null;
  has_shelf: boolean | null;
  has_hooks: boolean | null;
  has_sanitary_bins: boolean | null;
  has_free_period_products: boolean | null;
  has_drinking_water: boolean | null;

  // Environment
  noise_level: number | null;
  temperature: number | null;
  lighting: number | null;
  smell: number | null;

  // Safety
  has_staff_nearby: boolean | null;
  has_cctv: boolean | null;
  is_women_friendly: boolean | null;
  is_family_friendly: boolean | null;

  // Facility Types
  is_water_refill_station: boolean | null;
  is_shower_facility: boolean | null;
  is_breastfeeding_room: boolean | null;
  is_rest_area: boolean | null;
  is_changing_place: boolean | null;
  is_ev_charging: boolean | null;
  is_picnic_area: boolean | null;

  // Ratings
  overall_score: number;
  cleanliness_rating: number | null;
  privacy_rating: number | null;
  accessibility_rating: number | null;
  safety_rating: number | null;
  noise_rating: number | null;
  environment_rating: number | null;

  // Trust model
  publication_status: 'published' | 'hidden' | 'under_review' | 'removed';
  verification_status:
    | 'source_imported'
    | 'source_verified'
    | 'community_confirmed'
    | 'staff_verified'
    | 'disputed'
    | 'stale';
  last_community_confirmed_at: string | null;
  last_staff_verified_at: string | null;

  // Metadata
  created_at: string;
  updated_at: string;
  created_by: string | null;
  is_verified: boolean; // legacy field, kept for backward compat
}

export interface OpenHours {
  [day: string]: { open: string; close: string } | null;
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
export type RootStackParamList = {
  Auth: undefined;
  Main: undefined;
  Paywall: undefined;
  AIRecommendations: undefined;
  PredictiveSuggestions: undefined;
};

export type AuthStackParamList = {
  Login: undefined;
  Register: undefined;
};

export type MainTabParamList = {
  Map: undefined;
  List: undefined;
  Favourites: undefined;
  Profile: undefined;
};

export type MapStackParamList = {
  MapView: undefined;
  FacilityDetail: { facilityId: string };
  AddFacility: undefined;
  ReportFacility: { facilityId: string };
  CorrectInfo: { facilityId: string };
  AdvancedFilters: undefined;
};

export type ProfileStackParamList = {
  ProfileMain: undefined;
  MySubmissions: undefined;
  MyBadges: undefined;
  SavedProfiles: undefined;
  RoutePlanning: undefined;
  OfflineMaps: undefined;
  NotificationAlerts: undefined;
  LocationSharing: undefined;
  AIRecommendations: undefined;
  PredictiveSuggestions: undefined;
};

// --- Filters ---
export interface FacilityFilters {
  open_now: boolean;
  is_free: boolean;
  is_accessible: boolean;
  is_disabled_access: boolean;
  has_baby_changing: boolean;
  has_family_room: boolean;
  is_gender_neutral: boolean;
  is_single_occupancy: boolean;
  is_24h: boolean;
  min_rating: number;
  // Advanced
  is_single_room: boolean;
  has_floor_to_ceiling_cubicles: boolean;
  is_quiet: boolean;
  has_wheelchair_access: boolean;
  requires_radar_key: boolean;
  has_adult_changing_place: boolean;
  has_lift: boolean;
  has_grab_rails: boolean;
  has_baby_changing_inside: boolean;
  has_separate_changing_room: boolean;
  has_family_toilet: boolean;
  has_pram_access: boolean;
  has_soap: boolean;
  has_paper_towels: boolean;
  has_hand_dryer: boolean;
  has_mirror: boolean;
  has_shelf: boolean;
  has_hooks: boolean;
  has_sanitary_bins: boolean;
  has_free_period_products: boolean;
  has_drinking_water: boolean;
  has_staff_nearby: boolean;
  has_cctv: boolean;
  is_women_friendly: boolean;
  is_family_friendly: boolean;
  // Facility Types
  is_water_refill_station: boolean;
  is_shower_facility: boolean;
  is_breastfeeding_room: boolean;
  is_rest_area: boolean;
  is_changing_place: boolean;
  is_ev_charging: boolean;
  is_picnic_area: boolean;
}

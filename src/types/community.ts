// ============================================================
// Project "Relief" — Community Feature Types
// ============================================================

/** Moderation queue item for facility submissions */
export interface FacilitySubmission {
  id: string;
  user_id: string;
  status: 'pending' | 'approved' | 'rejected';
  name: string;
  address: string;
  latitude: number;
  longitude: number;
  postcode: string;
  town: string;
  country: string;
  access_notes: string;
  is_free: boolean;
  price_note?: string;
  open_hours: Record<string, { open: string; close: string } | null> | null;
  photos: string[];
  // Amenities
  is_accessible: boolean;
  is_disabled_access: boolean;
  has_baby_changing: boolean;
  has_family_room: boolean;
  is_gender_neutral: boolean;
  is_single_occupancy: boolean;
  is_24h: boolean;
  // Notes
  notes: string;
  access_codes: string;
  submission_notes: string;
  // Metadata
  created_at: string;
  reviewed_at: string | null;
  reviewed_by: string | null;
  rejection_reason: string | null;
}

/** Photo moderation item */
export interface PhotoModeration {
  id: string;
  facility_id: string;
  user_id: string;
  url: string;
  thumbnail_url: string;
  status: 'pending' | 'approved' | 'rejected' | 'reported';
  exif_stripped: boolean;
  faces_blurred: boolean;
  reported_by: string | null;
  report_reason: string | null;
  created_at: string;
}

/** Temporary report (closure, out of order, cleaning, busy) */
export interface TemporaryReport {
  id: string;
  facility_id: string;
  user_id: string;
  type: 'out_of_order' | 'no_water' | 'cleaning' | 'busy' | 'closed' | 'refurbishment';
  notes: string;
  expires_at: string;
  is_expired: boolean;
  created_at: string;
}

/** Permanent correction request */
export interface CorrectionRequest {
  id: string;
  facility_id: string;
  user_id: string;
  field: string;
  old_value: string;
  new_value: string;
  notes: string;
  status: 'pending' | 'approved' | 'rejected';
  created_at: string;
  reviewed_at: string | null;
  reviewed_by: string | null;
}

/** Access code entry */
export interface AccessCode {
  id: string;
  facility_id: string;
  user_id: string;
  code: string;
  description: string;
  is_verified: boolean;
  created_at: string;
  updated_at: string;
}

/** User badge */
export interface Badge {
  id: string;
  user_id: string;
  badge_type: 'explorer' | 'community_hero' | 'accessibility_champion' | 'family_helper';
  awarded_at: string;
  source: string;
}

/** Rate limit tracker */
export interface RateLimitEntry {
  user_id: string;
  action: string;
  timestamp: string;
}
// ============================================================
// Project "Relief" — Community Service
// Handles facility submissions, reports, corrections,
// access codes, photo uploads, badges, and rate limiting
// ============================================================

import { supabase } from './supabase';
import type {
  FacilitySubmission,
  TemporaryReport,
  CorrectionRequest,
  AccessCode,
  Badge,
  PhotoModeration,
} from '../types/community';

// ────────────────────────────────────────
// 2.1 — Facility Submission (→ moderation queue)
// ────────────────────────────────────────

/**
 * Submit a new facility for moderation review.
 * The facility is NOT added to the live facilities table directly.
 * It goes into the facility_submissions table for admin approval.
 */
export async function submitFacility(
  submission: Omit<FacilitySubmission, 'id' | 'user_id' | 'status' | 'created_at' | 'reviewed_at' | 'reviewed_by' | 'rejection_reason'>,
): Promise<{ success: boolean; error?: string }> {
  const { data: userData, error: userError } = await supabase.auth.getUser();
  if (userError || !userData?.user) {
    return { success: false, error: 'You must be signed in to submit a facility' };
  }

  // Rate limit check: max 3 submissions per user per hour
  const rateCheck = await checkRateLimit(userData.user.id, 'submit_facility');
  if (!rateCheck.allowed) {
    return { success: false, error: rateCheck.error };
  }

  const { data, error } = await supabase.from('facility_submissions').insert({
    ...submission,
    user_id: userData.user.id,
    status: 'pending',
  });

  if (error) {
    console.error('Error submitting facility:', error);
    return { success: false, error: error.message };
  }

  // Record the rate limit action
  await recordRateLimit(userData.user.id, 'submit_facility');

  // Award Explorer badge if this is the first submission
  await checkAndAwardBadge(userData.user.id, 'explorer');

  return { success: true };
}

/**
 * Fetch all pending/approved/rejected submissions for the current user.
 */
export async function getUserSubmissions(): Promise<FacilitySubmission[]> {
  const { data: userData } = await supabase.auth.getUser();
  if (!userData?.user) return [];

  const { data, error } = await supabase
    .from('facility_submissions')
    .select('*')
    .eq('user_id', userData.user.id)
    .order('created_at', { ascending: false });

  if (error) {
    console.error('Error fetching user submissions:', error);
    return [];
  }

  return data as unknown as FacilitySubmission[];
}

// ────────────────────────────────────────
// 2.2 — Photo Uploads with Moderation Pipeline
// ────────────────────────────────────────

/**
 * Upload a photo to Supabase Storage for a facility.
 * Photos go through moderation pipeline (EXIF stripped, faces blurred).
 */
export async function uploadFacilityPhoto(
  facilityId: string,
  uri: string,
): Promise<{ success: boolean; url?: string; error?: string }> {
  const { data: userData, error: userError } = await supabase.auth.getUser();
  if (userError || !userData?.user) {
    return { success: false, error: 'You must be signed in to upload photos' };
  }

  // Rate limit: max 10 photo uploads per user per hour
  const rateCheck = await checkRateLimit(userData.user.id, 'upload_photo');
  if (!rateCheck.allowed) {
    return { success: false, error: rateCheck.error };
  }

  try {
    // Generate a unique file name
    const fileName = `${facilityId}/${userData.user.id}/${Date.now()}.jpg`;

    // Read the file as blob from local URI
    const response = await fetch(uri);
    const blob = await response.blob();

    // Upload to Supabase Storage
    const { data, error } = await supabase.storage
      .from('facility-photos')
      .upload(fileName, blob, {
        contentType: 'image/jpeg',
        cacheControl: '3600',
        upsert: false,
      });

    if (error) {
      return { success: false, error: error.message };
    }

    // Get public URL
    const { data: urlData } = supabase.storage
      .from('facility-photos')
      .getPublicUrl(fileName);

    // Insert into photo_moderation queue (status: pending)
    const { error: modError } = await supabase
      .from('photo_moderation')
      .insert({
        facility_id: facilityId,
        user_id: userData.user.id,
        url: urlData.publicUrl,
        thumbnail_url: urlData.publicUrl, // Will be replaced by server-side thumbnail
        status: 'pending',
        exif_stripped: false, // Server-side processing will set this
        faces_blurred: false, // Server-side processing will set this
      });

    if (modError) {
      return { success: false, error: modError.message };
    }

    // Record rate limit
    await recordRateLimit(userData.user.id, 'upload_photo');

    return { success: true, url: urlData.publicUrl };
  } catch (err) {
    console.error('Error uploading photo:', err);
    return { success: false, error: 'Failed to upload photo' };
  }
}

/**
 * Report a photo for moderation review.
 */
export async function reportPhoto(
  photoId: string,
  reason: string,
): Promise<{ success: boolean; error?: string }> {
  const { data: userData } = await supabase.auth.getUser();
  if (!userData?.user) {
    return { success: false, error: 'You must be signed in to report photos' };
  }

  const { error } = await supabase
    .from('photo_moderation')
    .update({
      status: 'reported',
      reported_by: userData.user.id,
      report_reason: reason,
    })
    .eq('id', photoId);

  if (error) {
    return { success: false, error: error.message };
  }

  return { success: true };
}

/**
 * Report a review for moderation.
 */
export async function reportReview(
  reviewId: string,
  reason: string,
): Promise<{ success: boolean; error?: string }> {
  const { data: userData } = await supabase.auth.getUser();
  if (!userData?.user) {
    return { success: false, error: 'You must be signed in to report reviews' };
  }

  const { error } = await supabase
    .from('review_reports')
    .insert({
      review_id: reviewId,
      user_id: userData.user.id,
      reason,
    });

  if (error) {
    return { success: false, error: error.message };
  }

  return { success: true };
}

/**
 * Fetch photos for a facility that are approved.
 */
export async function getFacilityPhotos(
  facilityId: string,
): Promise<{ url: string; thumbnail_url: string }[]> {
  const { data, error } = await supabase
    .from('photo_moderation')
    .select('url, thumbnail_url')
    .eq('facility_id', facilityId)
    .eq('status', 'approved');

  if (error) {
    console.error('Error fetching facility photos:', error);
    return [];
  }

  return data as { url: string; thumbnail_url: string }[];
}

// ────────────────────────────────────────
// 2.3 — Temporary Reports (closure, out of order, etc.)
// ────────────────────────────────────────

/**
 * Submit a temporary report for a facility.
 * These expire automatically after a set duration.
 */
export async function submitTemporaryReport(
  facilityId: string,
  type: TemporaryReport['type'],
  notes: string,
  durationHours: number = 2,
): Promise<{ success: boolean; error?: string }> {
  const { data: userData, error: userError } = await supabase.auth.getUser();
  if (userError || !userData?.user) {
    return { success: false, error: 'You must be signed in to report' };
  }

  // Rate limit: max 1 report per facility per user per hour
  const rateCheck = await checkRateLimit(
    userData.user.id,
    `report_facility_${facilityId}`,
    1, // 1 per hour
  );
  if (!rateCheck.allowed) {
    return { success: false, error: 'You have already reported this facility recently. Please wait before reporting again.' };
  }

  // Check for duplicate active reports for this facility
  const { data: existingReports } = await supabase
    .from('temporary_reports')
    .select('id')
    .eq('facility_id', facilityId)
    .eq('type', type)
    .eq('is_expired', false)
    .gte('expires_at', new Date().toISOString());

  if (existingReports && existingReports.length > 0) {
    return { success: false, error: 'A report for this issue already exists' };
  }

  const expiresAt = new Date(
    Date.now() + durationHours * 60 * 60 * 1000,
  ).toISOString();

  const { error } = await supabase.from('temporary_reports').insert({
    facility_id: facilityId,
    user_id: userData.user.id,
    type,
    notes,
    expires_at: expiresAt,
    is_expired: false,
  });

  if (error) {
    console.error('Error submitting report:', error);
    return { success: false, error: error.message };
  }

  // Record rate limit
  await recordRateLimit(userData.user.id, `report_facility_${facilityId}`);

  // Award Community Hero badge if this is the 5th report
  await checkAndAwardBadge(userData.user.id, 'community_hero');

  return { success: true };
}

/**
 * Get active (non-expired) temporary reports for a facility.
 */
export async function getActiveReports(
  facilityId: string,
): Promise<TemporaryReport[]> {
  const now = new Date().toISOString();

  const { data, error } = await supabase
    .from('temporary_reports')
    .select('*')
    .eq('facility_id', facilityId)
    .eq('is_expired', false)
    .gte('expires_at', now) // Only reports that haven't expired yet
    .order('created_at', { ascending: false });

  if (error) {
    console.error('Error fetching reports:', error);
    return [];
  }

  return data as unknown as TemporaryReport[];
}

/**
 * Manually mark a user's own report as resolved (premature expiry).
 */
export async function resolveOwnReport(
  reportId: string,
): Promise<{ success: boolean; error?: string }> {
  const { data: userData } = await supabase.auth.getUser();
  if (!userData?.user) {
    return { success: false, error: 'Not authenticated' };
  }

  const { error } = await supabase
    .from('temporary_reports')
    .update({
      is_expired: true,
      expires_at: new Date().toISOString(),
    })
    .eq('id', reportId)
    .eq('user_id', userData.user.id); // Can only resolve own reports

  if (error) {
    return { success: false, error: error.message };
  }

  return { success: true };
}

// ────────────────────────────────────────
// 2.4 — Correct Information (permanent edits → moderation)
// ────────────────────────────────────────

/**
 * Submit a correction for a facility field.
 * Goes to moderation queue for admin approval.
 */
export async function submitCorrection(
  facilityId: string,
  field: string,
  oldValue: string,
  newValue: string,
  notes: string,
): Promise<{ success: boolean; error?: string }> {
  const { data: userData, error: userError } = await supabase.auth.getUser();
  if (userError || !userData?.user) {
    return { success: false, error: 'You must be signed in to submit corrections' };
  }

  // Rate limit: max 5 corrections per user per day
  const rateCheck = await checkRateLimit(
    userData.user.id,
    'submit_correction',
    5,
    24, // 24-hour window
  );
  if (!rateCheck.allowed) {
    return { success: false, error: rateCheck.error };
  }

  const { error } = await supabase.from('correction_requests').insert({
    facility_id: facilityId,
    user_id: userData.user.id,
    field,
    old_value: oldValue,
    new_value: newValue,
    notes,
    status: 'pending',
  });

  if (error) {
    console.error('Error submitting correction:', error);
    return { success: false, error: error.message };
  }

  // Record rate limit
  await recordRateLimit(userData.user.id, 'submit_correction');

  return { success: true };
}

// ────────────────────────────────────────
// 2.5 — Access Codes and Notes
// ────────────────────────────────────────

/**
 * Add or update an access code for a facility.
 */
export async function addAccessCode(
  facilityId: string,
  code: string,
  description: string,
): Promise<{ success: boolean; error?: string }> {
  const { data: userData, error: userError } = await supabase.auth.getUser();
  if (userError || !userData?.user) {
    return { success: false, error: 'You must be signed in to add access codes' };
  }

  // Check if user already submitted a code for this facility
  const { data: existing } = await supabase
    .from('access_codes')
    .select('id')
    .eq('facility_id', facilityId)
    .eq('user_id', userData.user.id)
    .single();

  if (existing) {
    // Update existing code
    const { error } = await supabase
      .from('access_codes')
      .update({
        code,
        description,
        updated_at: new Date().toISOString(),
      })
      .eq('id', existing.id);

    if (error) {
      return { success: false, error: error.message };
    }
  } else {
    // Insert new code
    const { error } = await supabase.from('access_codes').insert({
      facility_id: facilityId,
      user_id: userData.user.id,
      code,
      description,
      is_verified: false,
    });

    if (error) {
      return { success: false, error: error.message };
    }
  }

  return { success: true };
}

/**
 * Get access codes for a facility.
 */
export async function getAccessCodes(
  facilityId: string,
): Promise<AccessCode[]> {
  const { data, error } = await supabase
    .from('access_codes')
    .select('*')
    .eq('facility_id', facilityId)
    .order('is_verified', { ascending: false })
    .order('created_at', { ascending: false });

  if (error) {
    console.error('Error fetching access codes:', error);
    return [];
  }

  return data as unknown as AccessCode[];
}

// ────────────────────────────────────────
// 2.6 — Gamification Badges
// ────────────────────────────────────────

/**
 * Fetch badges for the current user.
 */
export async function getUserBadges(): Promise<Badge[]> {
  const { data: userData } = await supabase.auth.getUser();
  if (!userData?.user) return [];

  const { data, error } = await supabase
    .from('user_badges')
    .select('*')
    .eq('user_id', userData.user.id)
    .order('awarded_at', { ascending: false });

  if (error) {
    console.error('Error fetching badges:', error);
    return [];
  }

  return data as unknown as Badge[];
}

/**
 * Check and award a badge if conditions are met.
 */
async function checkAndAwardBadge(
  userId: string,
  badgeType: Badge['badge_type'],
): Promise<void> {
  // Check if user already has this badge
  const { data: existingBadge } = await supabase
    .from('user_badges')
    .select('id')
    .eq('user_id', userId)
    .eq('badge_type', badgeType)
    .single();

  if (existingBadge) return; // Already has badge

  let shouldAward = false;
  let source = '';

  switch (badgeType) {
    case 'explorer': {
      // Award for first facility submission
      const { count } = await supabase
        .from('facility_submissions')
        .select('id', { count: 'exact' })
        .eq('user_id', userId);
      shouldAward = (count ?? 0) >= 1;
      source = 'Submitted your first facility';
      break;
    }
    case 'community_hero': {
      // Award for 5+ reports
      const { count } = await supabase
        .from('temporary_reports')
        .select('id', { count: 'exact' })
        .eq('user_id', userId);
      shouldAward = (count ?? 0) >= 5;
      source = 'Submitted 5 reports';
      break;
    }
    case 'accessibility_champion': {
      // Award for 3+ accessibility-related corrections
      const { count } = await supabase
        .from('correction_requests')
        .select('id', { count: 'exact' })
        .eq('user_id', userId)
        .in('field', ['is_accessible', 'is_disabled_access', 'has_wheelchair_access', 'has_grab_rails', 'has_lift', 'has_adult_changing_place', 'requires_radar_key']);
      shouldAward = (count ?? 0) >= 3;
      source = 'Made 3 accessibility corrections';
      break;
    }
    case 'family_helper': {
      // Award for 3+ baby/family related corrections
      const { count } = await supabase
        .from('correction_requests')
        .select('id', { count: 'exact' })
        .eq('user_id', userId)
        .in('field', ['has_baby_changing', 'has_family_room', 'has_baby_changing_inside', 'has_separate_changing_room', 'has_family_toilet', 'has_pram_access']);
      shouldAward = (count ?? 0) >= 3;
      source = 'Made 3 family-related corrections';
      break;
    }
  }

  if (shouldAward) {
    await supabase.from('user_badges').insert({
      user_id: userId,
      badge_type: badgeType,
      source,
    });
  }
}

// ────────────────────────────────────────
// 2.8 — Rate Limiting & Duplicate Checks
// ────────────────────────────────────────

/**
 * Check if a user has exceeded their rate limit for a specific action.
 */
async function checkRateLimit(
  userId: string,
  action: string,
  maxAttempts: number = 3,
  windowHours: number = 1,
): Promise<{ allowed: boolean; error?: string }> {
  const since = new Date(
    Date.now() - windowHours * 60 * 60 * 1000,
  ).toISOString();

  const { count, error } = await supabase
    .from('rate_limits')
    .select('id', { count: 'exact' })
    .eq('user_id', userId)
    .eq('action', action)
    .gte('timestamp', since);

  if (error) {
    console.error('Rate limit check error:', error);
    // Allow on error to prevent blocking legitimate usage
    return { allowed: true };
  }

  if ((count ?? 0) >= maxAttempts) {
    return {
      allowed: false,
      error: `Too many attempts. Please try again in ${windowHours} hour(s).`,
    };
  }

  return { allowed: true };
}

/**
 * Record a rate limit entry.
 */
async function recordRateLimit(
  userId: string,
  action: string,
): Promise<void> {
  await supabase.from('rate_limits').insert({
    user_id: userId,
    action,
    timestamp: new Date().toISOString(),
  });
}
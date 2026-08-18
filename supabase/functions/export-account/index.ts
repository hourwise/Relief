import { serve } from 'https://deno.land/std@0.168.0/http/server.ts';
import { createClient } from 'https://esm.sh/@supabase/supabase-js@2';
import { isRecentlyAuthenticated } from '../delete-account/contract.ts';
import { parseExportRequestBody } from './contract.ts';

const EXPORT_VERSION = 1;

type Row = Record<string, unknown>;

const OPTIONAL_EMPTY_READ_LABELS = new Set([
  'moderator_read_failed',
  'verification_history_read_failed',
]);

type FacilityReference = {
  id: string;
  name: string;
  address: string | null;
  town: string;
  postcode: string | null;
  publication_status: string;
};

function jsonResponse(body: Record<string, unknown>, status: number): Response {
  return new Response(JSON.stringify(body), {
    status,
    headers: {
      'Content-Type': 'application/json',
      'Access-Control-Allow-Headers': 'authorization, x-client-info, apikey, content-type',
      'Access-Control-Allow-Methods': 'POST, OPTIONS',
      'Access-Control-Allow-Origin': '*',
    },
  });
}

function bearerToken(request: Request): string | null {
  const value = request.headers.get('authorization') ?? '';
  const match = value.match(/^Bearer\s+(.+)$/i);
  return match?.[1] ?? null;
}

async function readRows<T extends Row>(
  query: any,
  label: string,
  onOptionalUnavailable?: () => void,
): Promise<T[]> {
  const { data, error } = await query;
  if (error) {
    if (OPTIONAL_EMPTY_READ_LABELS.has(label)) {
      onOptionalUnavailable?.();
      console.warn(JSON.stringify({ outcome: 'optional_export_section_unavailable', section: label }));
      return [];
    }
    throw new Error(label);
  }
  return (data ?? []) as T[];
}

function stringValue(value: unknown): string | null {
  return typeof value === 'string' && value.length > 0 ? value : null;
}

function displayNameFromMetadata(metadata: Record<string, unknown>): string | null {
  for (const key of ['full_name', 'name']) {
    const value = metadata[key];
    if (typeof value === 'string' && value.trim()) return value.trim();
  }
  return null;
}

function facilityIds(rows: Row[]): string[] {
  return [...new Set(rows.map((row) => stringValue(row.facility_id)).filter((id): id is string => id !== null))];
}

function addFacility<T extends Row>(row: T, facilities: Map<string, FacilityReference>): T & { facility: FacilityReference | null } {
  const facilityId = stringValue(row.facility_id);
  return { ...row, facility: facilityId ? facilities.get(facilityId) ?? null : null };
}

function withoutUserId(row: Row): Row {
  const { user_id: _userId, ...safe } = row;
  return safe;
}

function safeFacilitySubmission(row: Row): Row {
  const { user_id: _userId, photos, ...safe } = row;
  return { ...safe, photo_count: Array.isArray(photos) ? photos.length : null };
}

function safeSubscription(row: Row): Row {
  return {
    tier: row.tier,
    is_active: row.is_active,
    lifetime_purchase_at: row.lifetime_purchase_at,
    plus_monthly_purchase_at: row.plus_monthly_purchase_at,
    plus_yearly_purchase_at: row.plus_yearly_purchase_at,
    current_period_start: row.current_period_start,
    current_period_end: row.current_period_end,
    will_renew: row.will_renew,
    is_grace_period: row.is_grace_period,
    cancellation_at: row.cancellation_at,
    cancelled_at: row.cancelled_at,
    refunded_at: row.refunded_at,
    created_at: row.created_at,
    updated_at: row.updated_at,
  };
}

async function buildExport(admin: any, user: { id: string; email?: string | null; created_at?: string; email_confirmed_at?: string | null; user_metadata?: Record<string, unknown> | null }): Promise<Row> {
  const userId = user.id;
  const unavailableSections = new Set<string>();
  const [
    profiles,
    favourites,
    savedProfiles,
    facilitySubmissions,
    facilityReports,
    temporaryReports,
    corrections,
    accessCodes,
    reviewReports,
    photos,
    photoReports,
    badges,
    moderators,
    verificationHistory,
    subscriptions,
    subscriptionEvents,
    reviewedSubmissions,
    reviewedCorrections,
    createdFacilities,
  ] = await Promise.all([
    readRows(admin.from('user_profiles').select('email,display_name,avatar_url,created_at,has_lifetime_access,subscription_tier,subscription_expires_at').eq('id', userId).limit(1), 'profile_read_failed'),
    readRows(admin.from('favourites').select('id,facility_id,created_at').eq('user_id', userId), 'favourites_read_failed'),
    readRows(admin.from('saved_profiles').select('id,mode,name,preferences,created_at').eq('user_id', userId), 'saved_profiles_read_failed'),
    readRows(admin.from('facility_submissions').select('id,user_id,status,name,address,latitude,longitude,postcode,town,country,access_notes,is_free,price_note,open_hours,photos,is_accessible,is_disabled_access,has_baby_changing,has_family_room,is_gender_neutral,is_single_occupancy,is_24h,notes,access_codes,submission_notes,created_at,reviewed_at,rejection_reason').eq('user_id', userId), 'facility_submissions_read_failed'),
    readRows(admin.from('facility_reports').select('id,facility_id,type,reason,notes,expires_at,created_at').eq('user_id', userId), 'facility_reports_read_failed'),
    readRows(admin.from('temporary_reports').select('id,facility_id,type,notes,expires_at,is_expired,created_at').eq('user_id', userId), 'temporary_reports_read_failed'),
    readRows(admin.from('correction_requests').select('id,facility_id,field,old_value,new_value,notes,status,created_at,reviewed_at,rejection_reason').eq('user_id', userId), 'corrections_read_failed'),
    readRows(admin.from('access_codes').select('id,facility_id,code,description,is_verified,created_at,updated_at').eq('user_id', userId), 'access_codes_read_failed'),
    readRows(admin.from('review_reports').select('id,reason,created_at').eq('user_id', userId), 'review_reports_read_failed'),
    readRows(admin.from('photo_moderation').select('id,facility_id,status,exif_stripped,faces_blurred,report_reason,created_at').eq('user_id', userId), 'photo_moderation_read_failed'),
    readRows(admin.from('photo_moderation').select('status,created_at').eq('reported_by', userId), 'photo_reports_read_failed'),
    readRows(admin.from('user_badges').select('id,badge_type,awarded_at,source').eq('user_id', userId), 'badges_read_failed'),
    readRows(admin.from('relief_moderators').select('active,created_at,updated_at').eq('user_id', userId).limit(1), 'moderator_read_failed', () => unavailableSections.add('moderation_activity')),
    readRows(admin.from('access_code_verification_history').select('action,created_at').eq('moderator_id', userId), 'verification_history_read_failed', () => unavailableSections.add('moderation_activity')),
    readRows(admin.from('user_subscriptions').select('tier,is_active,lifetime_purchase_at,plus_monthly_purchase_at,plus_yearly_purchase_at,current_period_start,current_period_end,will_renew,is_grace_period,cancellation_at,cancelled_at,refunded_at,created_at,updated_at').eq('user_id', userId).limit(1), 'subscription_read_failed'),
    readRows(admin.from('subscription_events').select('event_type,tier,previous_tier,created_at').eq('user_id', userId).order('created_at', { ascending: true }), 'subscription_events_read_failed'),
    readRows(admin.from('facility_submissions').select('status,reviewed_at').eq('reviewed_by', userId), 'reviewed_submissions_read_failed'),
    readRows(admin.from('correction_requests').select('status,reviewed_at').eq('reviewed_by', userId), 'reviewed_corrections_read_failed'),
    readRows(admin.from('facilities').select('id,name,address,town,postcode,created_at').eq('created_by', userId), 'canonical_attribution_read_failed'),
  ]);

  const relatedIds = facilityIds([
    ...favourites,
    ...facilityReports,
    ...temporaryReports,
    ...corrections,
    ...accessCodes,
    ...photos,
  ]);
  const relatedFacilities = relatedIds.length === 0
    ? []
    : await readRows<FacilityReference>(
        admin.from('facilities').select('id,name,address,town,postcode,publication_status').in('id', relatedIds),
        'facility_context_read_failed',
      );
  const facilityMap = new Map(relatedFacilities.map((facility) => [facility.id, facility]));
  const metadata = user.user_metadata ?? {};
  const profile = profiles[0] ? withoutUserId(profiles[0]) : null;
  const moderator = moderators[0];
  const moderationUnavailable = unavailableSections.has('moderation_activity');

  return {
    export_version: EXPORT_VERSION,
    generated_at: new Date().toISOString(),
    account: {
      id: userId,
      email: user.email ?? null,
      created_at: user.created_at ?? null,
      email_confirmed_at: user.email_confirmed_at ?? null,
      display_name: displayNameFromMetadata(metadata) ?? stringValue(profiles[0]?.display_name),
    },
    profile,
    favourites: favourites.map((row) => addFacility(withoutUserId(row), facilityMap)),
    saved_profiles: savedProfiles.map(withoutUserId),
    contributions: {
      facility_submissions: facilitySubmissions.map(safeFacilitySubmission),
      reports: facilityReports.map((row) => addFacility(row, facilityMap)),
      temporary_reports: temporaryReports.map((row) => addFacility(row, facilityMap)),
      corrections: corrections.map((row) => addFacility(row, facilityMap)),
      access_codes: accessCodes.map((row) => addFacility(row, facilityMap)),
      photo_moderation: photos.map((row) => addFacility(row, facilityMap)),
      review_reports: reviewReports.map(withoutUserId),
    },
    badges: badges.map(withoutUserId),
    subscriptions: {
      current: subscriptions[0] ? safeSubscription(subscriptions[0]) : null,
      events: subscriptionEvents.map((row) => ({
        event_type: row.event_type,
        tier: row.tier,
        previous_tier: row.previous_tier,
        created_at: row.created_at,
      })),
      provider_payloads: 'excluded',
    },
    moderation_activity: {
      role: moderationUnavailable ? null : moderator?.active === true ? 'moderator' : 'none',
      availability: moderationUnavailable ? 'partial' : 'complete',
      limitation: moderationUnavailable ? 'Some internal moderation activity is not currently included in this export.' : null,
      review_actions: [
        ...reviewedSubmissions.map((row) => ({ kind: 'facility_submission', outcome: row.status, occurred_at: row.reviewed_at })),
        ...reviewedCorrections.map((row) => ({ kind: 'correction_request', outcome: row.status, occurred_at: row.reviewed_at })),
      ],
      verification_actions: verificationHistory.map((row) => ({ action: row.action, occurred_at: row.created_at })),
      photo_reports: photoReports.map((row) => ({ outcome: row.status, occurred_at: row.created_at })),
    },
    canonical_attribution: createdFacilities.map((row) => ({
      id: row.id,
      name: row.name,
      address: row.address,
      town: row.town,
      postcode: row.postcode,
      associated_as: 'creator',
      created_at: row.created_at,
    })),
    excluded: [
      'passwords_and_authentication_tokens',
      'raw_auth_metadata_and_provider_secrets',
      'rate_limits_and_internal_security_controls',
      'reviewer_and_reporter_identity_references',
      'other_users_contribution_content',
      'canonical_import_and_field_provenance_internals',
      'photo_storage_urls_and_storage_objects',
      'raw_revenuecat_webhook_payloads',
    ],
  };
}

serve(async (request) => {
  const requestId = crypto.randomUUID();
  if (request.method === 'OPTIONS') return jsonResponse({}, 204);
  if (request.method !== 'POST') return jsonResponse({ ok: false, code: 'METHOD_NOT_ALLOWED', request_id: requestId }, 405);

  const token = bearerToken(request);
  if (!token) return jsonResponse({ ok: false, code: 'AUTHENTICATION_REQUIRED', request_id: requestId }, 401);

  const supabaseUrl = Deno.env.get('SUPABASE_URL') ?? '';
  const supabaseAnonKey = Deno.env.get('SUPABASE_ANON_KEY') ?? '';
  const supabaseServiceRoleKey = Deno.env.get('SUPABASE_SERVICE_ROLE_KEY') ?? '';
  if (!supabaseUrl || !supabaseAnonKey || !supabaseServiceRoleKey) {
    console.error(JSON.stringify({ request_id: requestId, outcome: 'misconfigured' }));
    return jsonResponse({ ok: false, code: 'EXPORT_BACKEND_MISCONFIGURED', request_id: requestId }, 503);
  }

  let body: unknown;
  try {
    body = await request.json();
  } catch {
    return jsonResponse({ ok: false, code: 'INVALID_REQUEST', request_id: requestId }, 400);
  }
  if (!parseExportRequestBody(body).ok) {
    return jsonResponse({ ok: false, code: 'INVALID_REQUEST', error: 'The export request contains unsupported fields.', request_id: requestId }, 400);
  }

  const authClient = createClient(supabaseUrl, supabaseAnonKey, { auth: { autoRefreshToken: false, persistSession: false } });
  const { data: authData, error: authError } = await authClient.auth.getUser(token);
  if (authError || !authData.user) return jsonResponse({ ok: false, code: 'AUTHENTICATION_REQUIRED', request_id: requestId }, 401);
  if (!isRecentlyAuthenticated(authData.user.last_sign_in_at)) {
    return jsonResponse({ ok: false, code: 'RECENT_AUTHENTICATION_REQUIRED', request_id: requestId }, 401);
  }

  const admin = createClient(supabaseUrl, supabaseServiceRoleKey, { auth: { autoRefreshToken: false, persistSession: false } });
  try {
    const exportPayload = await buildExport(admin, authData.user);
    return jsonResponse({ ok: true, export: exportPayload, request_id: requestId }, 200);
  } catch {
    console.error(JSON.stringify({ request_id: requestId, outcome: 'export_generation_failed' }));
    return jsonResponse({ ok: false, code: 'EXPORT_GENERATION_FAILED', retryable: true, request_id: requestId }, 502);
  }
});

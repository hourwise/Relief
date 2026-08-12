// ============================================================
// Relief - typed Supabase integration contracts
// ============================================================
// Keep request construction separate from the network client. These builders
// are used by the services and can be tested locally without production
// credentials, users, or database writes.

import type { TablesInsert, Functions } from '../types/database.types';
import type { FacilitySubmission, TemporaryReport } from '../types/community';

export type FindNearestFacilitiesArgs = Functions<'find_nearest_facilities'>['Args'];

export function buildFindNearestFacilitiesArgs(
  latitude: number,
  longitude: number,
  searchRadiusMetres: number,
  resultLimit: number,
): FindNearestFacilitiesArgs {
  return {
    user_latitude: latitude,
    user_longitude: longitude,
    search_radius_metres: searchRadiusMetres,
    result_limit: resultLimit,
  };
}

export function buildFavouriteInsert(
  userId: string,
  facilityId: string,
): TablesInsert<'favourites'> {
  return { user_id: userId, facility_id: facilityId };
}

export function buildOwnedFacilityFilter(userId: string, facilityId: string) {
  return { user_id: userId, facility_id: facilityId } as const;
}

export function buildTemporaryReportInsert(
  userId: string,
  facilityId: string,
  type: TemporaryReport['type'],
  notes: string,
  expiresAt: string,
): TablesInsert<'temporary_reports'> {
  return {
    facility_id: facilityId,
    user_id: userId,
    type,
    notes,
    expires_at: expiresAt,
    is_expired: false,
  };
}

export function buildCorrectionInsert(
  userId: string,
  facilityId: string,
  field: string,
  oldValue: string,
  newValue: string,
  notes: string,
): TablesInsert<'correction_requests'> {
  return {
    facility_id: facilityId,
    user_id: userId,
    field,
    old_value: oldValue,
    new_value: newValue,
    notes,
    status: 'pending',
  };
}

type FacilitySubmissionInput = Omit<
  FacilitySubmission,
  'id' | 'user_id' | 'status' | 'created_at' | 'reviewed_at' | 'reviewed_by' | 'rejection_reason'
>;

export function buildFacilitySubmissionInsert(
  userId: string,
  submission: FacilitySubmissionInput,
): TablesInsert<'facility_submissions'> {
  return {
    ...submission,
    user_id: userId,
    status: 'pending',
  };
}

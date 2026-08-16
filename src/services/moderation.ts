import { describeSupabaseError } from '../utils/supabaseErrors';
import type {
  AccessCode,
  CorrectionRequest,
  FacilitySubmission,
} from '../types/community';
import { supabase } from './supabase';

export type ModerationDecision = 'approved' | 'rejected';
export type AccessCodeModerationDecision = 'verify' | 'revoke';

type ModerationRpcResult<T> = {
  data: T | null;
  error: { code?: string; message?: string } | null;
};

type ModerationRpcClient = {
  rpc: (
    name: string,
    args: Record<string, unknown>,
  ) => Promise<ModerationRpcResult<unknown>>;
};

// The generated production types intentionally do not include this source-only
// migration until it is separately deployed. Keep the adapter local and typed
// at this boundary rather than weakening the application-wide Supabase client.
const moderationRpc = supabase as unknown as ModerationRpcClient;

function failure(error: ModerationRpcResult<unknown>['error']) {
  return {
    success: false as const,
    error: describeSupabaseError(error, 'This moderation action could not be completed.'),
  };
}

export async function listModerationFacilitySubmissions(): Promise<FacilitySubmission[]> {
  const result = await moderationRpc.rpc('list_moderation_facility_submissions', {});
  if (result.error || !Array.isArray(result.data)) return [];
  return result.data as FacilitySubmission[];
}

export async function moderateFacilitySubmission(
  submissionId: string,
  decision: ModerationDecision,
  rejectionReason?: string,
): Promise<{ success: boolean; submission?: FacilitySubmission; error?: string }> {
  const result = await moderationRpc.rpc('moderate_facility_submission', {
    p_submission_id: submissionId,
    p_decision: decision,
    p_rejection_reason: rejectionReason ?? null,
  });
  if (result.error || !result.data) return failure(result.error);
  return { success: true, submission: result.data as FacilitySubmission };
}

export async function listModerationCorrectionRequests(): Promise<CorrectionRequest[]> {
  const result = await moderationRpc.rpc('list_moderation_correction_requests', {});
  if (result.error || !Array.isArray(result.data)) return [];
  return result.data as CorrectionRequest[];
}

export async function moderateCorrectionRequest(
  correctionId: string,
  decision: ModerationDecision,
  rejectionReason?: string,
): Promise<{ success: boolean; correction?: CorrectionRequest; error?: string }> {
  const result = await moderationRpc.rpc('moderate_correction_request', {
    p_correction_id: correctionId,
    p_decision: decision,
    p_rejection_reason: rejectionReason ?? null,
  });
  if (result.error || !result.data) return failure(result.error);
  return { success: true, correction: result.data as CorrectionRequest };
}

export async function listModerationAccessCodes(): Promise<AccessCode[]> {
  const result = await moderationRpc.rpc('list_moderation_access_codes', {});
  if (result.error || !Array.isArray(result.data)) return [];
  return result.data as AccessCode[];
}

export async function moderateAccessCode(
  accessCodeId: string,
  decision: AccessCodeModerationDecision,
): Promise<{ success: boolean; accessCode?: AccessCode; error?: string }> {
  const result = await moderationRpc.rpc('moderate_access_code', {
    p_access_code_id: accessCodeId,
    p_decision: decision,
  });
  if (result.error || !result.data) return failure(result.error);
  return { success: true, accessCode: result.data as AccessCode };
}

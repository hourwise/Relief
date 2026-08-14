import { RELIEF_TEST_MODE } from '../utils/env';

export const ACCOUNT_DELETION_CONFIRMATION = 'DELETE MY ACCOUNT' as const;
export const ACCOUNT_DELETION_FUNCTION = 'delete-account' as const;

export type AccountDeletionErrorCode =
  | 'INVALID_CONFIRMATION'
  | 'INVALID_REQUEST'
  | 'AUTHENTICATION_REQUIRED'
  | 'RECENT_AUTHENTICATION_REQUIRED'
  | 'DELETION_BACKEND_MISCONFIGURED'
  | 'SUBSCRIPTION_RETENTION_UNRESOLVED'
  | 'STORAGE_CLEANUP_FAILED'
  | 'DATA_CLEANUP_FAILED'
  | 'AUTH_DELETE_FAILED'
  | 'DELETION_REQUEST_FAILED';

export type AccountDeletionResult =
  | { success: true; simulated: boolean; message: string; requestId?: string }
  | { success: false; code: AccountDeletionErrorCode; error: string; partial?: boolean; retryable?: boolean };

type DeletionResponse = {
  ok: boolean;
  status?: 'deleted';
  code?: AccountDeletionErrorCode;
  error?: string;
  partial?: boolean;
  retryable?: boolean;
  request_id?: string;
};

export type AccountDeletionInvoker = (confirmation: string) => Promise<AccountDeletionResult>;

export function getAccountDeletionErrorMessage(
  result: Extract<AccountDeletionResult, { success: false }>,
): string {
  switch (result.code) {
    case 'SUBSCRIPTION_RETENTION_UNRESOLVED':
      return 'Automated deletion cannot currently complete because this account has subscription or payment history that needs additional handling. No account data was deleted. Relief support and data-rights contact details are not configured in this build yet.';
    case 'RECENT_AUTHENTICATION_REQUIRED':
      return 'For your security, please sign in again and then retry account deletion.';
    case 'STORAGE_CLEANUP_FAILED':
      return 'Relief could not confirm file cleanup, so your account was not reported as deleted. Please try again later.';
    case 'DATA_CLEANUP_FAILED':
      return 'Relief could not complete the account-data cleanup, so your account was not reported as deleted. Please try again later.';
    case 'AUTH_DELETE_FAILED':
      return 'Relief cleaned the account data but could not remove the sign-in account. Please try again later.';
    case 'DELETION_BACKEND_MISCONFIGURED':
    case 'DELETION_REQUEST_FAILED':
      return 'The account deletion service is temporarily unavailable. Your account was not reported as deleted. Please try again later.';
    default:
      return result.error;
  }
}

async function invokeProductionDeletion(confirmation: string): Promise<AccountDeletionResult> {
  const { supabase } = await import('./supabase');
  const { data, error } = await supabase.functions.invoke<DeletionResponse>(ACCOUNT_DELETION_FUNCTION, {
    body: { confirmation },
  });

  if (error || !data) {
    return {
      success: false,
      code: 'DELETION_REQUEST_FAILED',
      error: 'The account deletion service could not be reached. Please try again later.',
      retryable: true,
    };
  }

  if (!data.ok) {
    return {
      success: false,
      code: data.code ?? 'DELETION_REQUEST_FAILED',
      error: data.error ?? 'Account deletion could not be completed.',
      partial: data.partial,
      retryable: data.retryable,
    };
  }

  // Remove the local session after the server has deleted the Auth user. This
  // is local cleanup only; Auth deletion is performed by the Edge Function.
  await supabase.auth.signOut({ scope: 'local' });
  return {
    success: true,
    simulated: false,
    message: 'Your Relief account and governed user-linked data have been deleted. Canonical facility and provenance records may remain.',
    requestId: data.request_id,
  };
}

export function createAccountDeletionAdapter(
  testMode: boolean = RELIEF_TEST_MODE,
  invoke: AccountDeletionInvoker = invokeProductionDeletion,
): AccountDeletionInvoker {
  return async (confirmation: string): Promise<AccountDeletionResult> => {
    if (confirmation.trim().toUpperCase() !== ACCOUNT_DELETION_CONFIRMATION) {
      return {
        success: false,
        code: 'INVALID_CONFIRMATION',
        error: `Type ${ACCOUNT_DELETION_CONFIRMATION} to confirm this request.`,
      };
    }

    if (testMode) {
      return {
        success: true,
        simulated: true,
        message: 'Test mode: the deletion request was simulated. No account or data was deleted.',
      };
    }

    return invoke(ACCOUNT_DELETION_CONFIRMATION);
  };
}

export const requestAccountDeletion = createAccountDeletionAdapter();

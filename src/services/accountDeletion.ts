import { RELIEF_TEST_MODE } from '../utils/env';

export const ACCOUNT_DELETION_CONFIRMATION = 'DELETE MY ACCOUNT' as const;
export const ACCOUNT_DELETION_FUNCTION = 'delete-account' as const;

export type AccountDeletionErrorCode =
  | 'INVALID_CONFIRMATION'
  | 'INVALID_REQUEST'
  | 'AUTHENTICATION_REQUIRED'
  | 'RECENT_AUTHENTICATION_REQUIRED'
  | 'DELETION_BACKEND_MISCONFIGURED'
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
    message: 'Your account and current Relief data have been deleted.',
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

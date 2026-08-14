import { RELIEF_TEST_MODE } from '../utils/env';

export const ACCOUNT_DELETION_NOT_CONFIGURED = 'ACCOUNT_DELETION_NOT_CONFIGURED' as const;

export type AccountDeletionResult =
  | { success: true; simulated: boolean; message: string }
  | { success: false; code: typeof ACCOUNT_DELETION_NOT_CONFIGURED | 'INVALID_CONFIRMATION'; error: string };

/**
 * Account deletion is intentionally an adapter. The production adapter does
 * not delete Auth users or data until retention and legal contracts are
 * approved. The test adapter exercises the complete UI without a real write.
 */
export function createAccountDeletionAdapter(testMode: boolean = RELIEF_TEST_MODE) {
  return async (confirmation: string): Promise<AccountDeletionResult> => {
  if (confirmation.trim().toUpperCase() !== 'DELETE MY ACCOUNT') {
    return {
      success: false,
      code: 'INVALID_CONFIRMATION',
      error: 'Type DELETE MY ACCOUNT to confirm this request.',
    };
  }

  if (testMode) {
    return {
      success: true,
      simulated: true,
      message: 'Test mode: the deletion request was simulated. No account or data was deleted.',
    };
  }

  return {
    success: false,
    code: ACCOUNT_DELETION_NOT_CONFIGURED,
    error: 'Account deletion is not available in this build. Please contact Relief support for help with your account.',
  };
  };
}

export const requestAccountDeletion = createAccountDeletionAdapter();

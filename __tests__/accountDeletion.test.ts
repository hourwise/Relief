import {
  DELETE_ACCOUNT_CONFIRMATION,
  isRecentlyAuthenticated,
  parseDeletionRequestBody,
} from '../supabase/functions/delete-account/contract';
import { createAccountDeletionAdapter } from '../src/services/accountDeletion';
import { assertEqual, assertTrue, section } from './helpers/harness';

section('account deletion security contract');

assertTrue(
  'deletion request accepts the exact confirmation object',
  parseDeletionRequestBody({ confirmation: DELETE_ACCOUNT_CONFIRMATION }).ok,
);
assertEqual(
  'arbitrary target user field is rejected',
  parseDeletionRequestBody({ confirmation: DELETE_ACCOUNT_CONFIRMATION, user_id: 'another-user' }).ok,
  false,
);
assertEqual(
  'arbitrary target_user_id field is rejected',
  parseDeletionRequestBody({ confirmation: DELETE_ACCOUNT_CONFIRMATION, target_user_id: 'another-user' }).ok,
  false,
);
assertEqual(
  'anonymous or stale authentication is rejected by the recent-auth gate',
  isRecentlyAuthenticated(null, Date.now()),
  false,
);
assertTrue(
  'recent authentication is accepted within the bounded window',
  isRecentlyAuthenticated(new Date(Date.now() - 60_000).toISOString(), Date.now()),
);
async function runAdapterAssertion(): Promise<void> {
  let invokedConfirmation = '';
  const adapter = createAccountDeletionAdapter(false, async (confirmation) => {
    invokedConfirmation = confirmation;
    return { success: true, simulated: false, message: 'deleted' };
  });
  const result = await adapter(DELETE_ACCOUNT_CONFIRMATION);
  assertTrue('production adapter delegates the typed confirmation to the backend', result.success && invokedConfirmation === DELETE_ACCOUNT_CONFIRMATION);
}

runAdapterAssertion().catch((error) => {
  console.error(error);
  process.exitCode = 1;
});

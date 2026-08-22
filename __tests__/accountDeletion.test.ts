import {
  DELETE_ACCOUNT_CONFIRMATION,
  isRecentlyAuthenticated,
  parseDeletionRequestBody,
  SUBSCRIPTION_RETENTION_UNRESOLVED,
  subscriptionGuardStatus,
} from '../supabase/functions/delete-account/contract';
// Node typings are intentionally not part of the mobile app dependency graph.
// @ts-expect-error -- the test runner executes this under Node via tsx.
import { readFileSync } from 'node:fs';
import { createAccountDeletionAdapter, getAccountDeletionErrorMessage } from '../src/services/accountDeletion';
import { assertEqual, assertTrue, section } from './helpers/harness';

section('account deletion security contract');

const deletionMigration = readFileSync(
  new URL('../supabase/migrations/20260814135046_account_deletion_cleanup_contract.sql', import.meta.url),
  'utf8',
);
const deletionEdgeFunction = readFileSync(
  new URL('../supabase/functions/delete-account/index.ts', import.meta.url),
  'utf8',
);

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
  'zero subscription rows allow the deletion path',
  subscriptionGuardStatus({ blocked: false, subscription_history_present: false }),
  'allow',
);
assertEqual(
  'user subscription row blocks deletion',
  subscriptionGuardStatus({ blocked: true, code: SUBSCRIPTION_RETENTION_UNRESOLVED }),
  'blocked',
);
assertEqual(
  'subscription event row blocks deletion',
  subscriptionGuardStatus({ blocked: true, code: SUBSCRIPTION_RETENTION_UNRESOLVED }),
  'blocked',
);
assertEqual(
  'blocked subscription guard cannot proceed to later deletion phases',
  subscriptionGuardStatus({ blocked: true, code: SUBSCRIPTION_RETENTION_UNRESOLVED }) === 'allow',
  false,
);
assertEqual(
  'guard failure cannot proceed to later deletion phases',
  subscriptionGuardStatus(null, new Error('guard failed')) === 'allow',
  false,
);
assertTrue(
  'subscription guard precedes every account cleanup operation',
  deletionMigration.indexOf('subscription_guard := public.check_my_account_deletion_subscription_guard()') <
    deletionMigration.indexOf('update public.correction_requests'),
);
assertTrue(
  'reviewer identity cleanup preserves another user\'s facility submission',
  deletionMigration.includes('update public.facility_submissions') &&
    deletionMigration.includes('set reviewed_by = null') &&
    deletionMigration.includes('where reviewed_by = actor') &&
    deletionMigration.indexOf('update public.facility_submissions') <
      deletionMigration.indexOf('delete from public.facility_submissions'),
);
assertTrue(
  'correction reviewer identity is anonymised before owned-row deletion',
  deletionMigration.includes('update public.correction_requests') &&
    deletionMigration.indexOf('update public.correction_requests') <
      deletionMigration.indexOf('delete from public.correction_requests'),
);
assertTrue(
  'reporter and canonical attribution references are anonymised',
  deletionMigration.includes('update public.photo_moderation') &&
    deletionMigration.includes('set reported_by = null') &&
    deletionMigration.includes('update public.facilities') &&
    deletionMigration.includes('set created_by = null'),
);
assertTrue(
  'Auth deletion occurs only after the governed database cleanup',
  deletionEdgeFunction.indexOf('await userClient.rpc(\'delete_my_account_data\')') <
    deletionEdgeFunction.indexOf('await admin.auth.admin.deleteUser(userId)'),
);
assertEqual(
  'the deployed deletion path never accepts a target user id',
  deletionEdgeFunction.includes('target_user_id') || deletionEdgeFunction.includes('user_id'),
  false,
);
assertTrue(
  'subscription history receives a dedicated user-facing explanation',
  getAccountDeletionErrorMessage({
    success: false,
    code: 'SUBSCRIPTION_RETENTION_UNRESOLVED',
    error: 'internal guard message',
  }).includes('subscription or payment history'),
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

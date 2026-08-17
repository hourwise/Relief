// Node typings are intentionally not part of the mobile app dependency graph.
// @ts-expect-error -- the test runner executes this under Node via tsx.
import { readFileSync } from 'node:fs';
import {
  buildTestDataExport,
  createDataExportAdapter,
  formatDataExport,
  getDataExportErrorMessage,
} from '../src/services/dataExport';
import { isRecentlyAuthenticated } from '../supabase/functions/delete-account/contract';
import { parseExportRequestBody } from '../supabase/functions/export-account/contract';
import { assertEqual, assertTrue, section } from './helpers/harness';

const exportFunction = readFileSync(
  new URL('../supabase/functions/export-account/index.ts', import.meta.url),
  'utf8',
);
const profileScreen = readFileSync(new URL('../src/screens/ProfileScreen.tsx', import.meta.url), 'utf8');

section('governed data export request boundary');
assertTrue('empty export request is accepted', parseExportRequestBody({}).ok);
assertEqual('null export request is rejected', parseExportRequestBody(null).ok, false);
assertEqual('array export request is rejected', parseExportRequestBody([]).ok, false);
assertEqual('user_id cannot select an account', parseExportRequestBody({ user_id: 'other-user' }).ok, false);
assertEqual('target_user_id cannot select an account', parseExportRequestBody({ target_user_id: 'other-user' }).ok, false);
assertEqual('email cannot select an account', parseExportRequestBody({ email: 'other@example.test' }).ok, false);

section('test adapter is synthetic and stable');
const synthetic = buildTestDataExport();
assertEqual('export version is explicit', synthetic.export_version, 1);
assertEqual('synthetic account is clearly non-production', synthetic.account.email, 'example.user@invalid.test');
assertEqual('raw provider payloads are explicitly excluded', synthetic.subscriptions.provider_payloads, 'excluded');
assertTrue('synthetic export has stable empty sections', synthetic.favourites.length === 0 && synthetic.contributions.access_codes.length === 0);
assertEqual('formatted export is valid JSON', JSON.parse(formatDataExport(synthetic)).export_version, 1);

void (async () => {
  const simulatedResult = await createDataExportAdapter(true)();
  assertTrue('test adapter reports simulation', simulatedResult.success && simulatedResult.simulated);
  if (simulatedResult.success) assertEqual('test adapter uses the synthetic account', simulatedResult.payload.account.id, 'relief-test-account');

  let productionInvokeCalled = false;
  const productionResult = await createDataExportAdapter(false, async () => {
    productionInvokeCalled = true;
    return { success: false, code: 'EXPORT_GENERATION_FAILED', error: 'test failure' };
  })();
  assertTrue('production adapter delegates to its server invoker', productionInvokeCalled);
  assertEqual('production failure is not reported as success', productionResult.success, false);
  if (!productionResult.success) assertTrue('export failure message is safe', !getDataExportErrorMessage(productionResult).includes('test failure'));

  section('server export privacy boundary');
  assertTrue('server derives export identity from verified user', exportFunction.includes('buildExport(admin, authData.user)') && exportFunction.includes('const userId = user.id'));
  assertTrue('server does not accept target user fields', !exportFunction.includes('target_user_id'));
  assertTrue('server uses explicit column selections', !exportFunction.includes(".select('*')"));
  assertTrue('raw RevenueCat payloads are never selected', !exportFunction.includes('raw_revenuecat_json'));
  assertTrue('rate-limit rows are not queried', !exportFunction.includes("from('rate_limits')"));
  assertTrue('server export has no mutation calls', !exportFunction.includes('.insert(') && !exportFunction.includes('.update(') && !exportFunction.includes('.delete('));
  assertTrue('reviewer identities are not returned in the payload mapping', !exportFunction.includes('reviewed_by:') && !exportFunction.includes('reported_by:') && !exportFunction.includes('moderator_id:'));
  assertTrue('canonical provenance is not selected', !exportFunction.includes(".select('field_provenance") && !exportFunction.includes('field_provenance,'));
  assertTrue('profile exposes the user-facing export entry', profileScreen.includes('Download my data') && profileScreen.includes('requestDataExport'));

  section('authentication boundary');
  const now = Date.now();
  assertEqual('missing recent authentication is rejected by the shared helper', isRecentlyAuthenticated(null, now), false);
  assertEqual('stale recent authentication is rejected by the shared helper', isRecentlyAuthenticated(new Date(now - 16 * 60 * 1000).toISOString(), now), false);
  assertEqual('recent authentication is accepted by the shared helper', isRecentlyAuthenticated(new Date(now - 60_000).toISOString(), now), true);
})().catch((error) => {
  console.error(error);
  process.exitCode = 1;
});

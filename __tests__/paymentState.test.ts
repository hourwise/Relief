import { assertDeepEqual, assertEqual, assertTrue, section } from './helpers/harness';
import { resolvePaymentState } from '../src/utils/paymentState';

section('explicit payment and QA entitlement state');

const free = resolvePaymentState({
  reliefTestMode: false,
  paymentsEnabled: false,
  qaPremiumOverride: false,
  revenueCatConfigured: false,
});
assertEqual('missing configuration defaults to free', free.entitlementSource, 'FREE');
assertEqual('free state cannot purchase', free.canPurchase, false);
assertEqual('free state cannot restore', free.canRestore, false);

const testModeWithoutOverride = resolvePaymentState({
  reliefTestMode: true,
  paymentsEnabled: false,
  qaPremiumOverride: false,
  revenueCatConfigured: false,
});
assertEqual('test mode alone does not grant premium', testModeWithoutOverride.entitlementSource, 'FREE');
assertEqual('test mode alone cannot purchase', testModeWithoutOverride.canPurchase, false);

const qa = resolvePaymentState({
  reliefTestMode: true,
  paymentsEnabled: false,
  qaPremiumOverride: true,
  revenueCatConfigured: false,
});
assertEqual('explicit test state uses QA authority', qa.entitlementSource, 'QA_OVERRIDE');
assertTrue('explicit test state activates QA premium', qa.qaPremiumActive);
assertEqual('QA state cannot purchase', qa.canPurchase, false);
assertEqual('QA state cannot restore', qa.canRestore, false);

const overrideOutsideTest = resolvePaymentState({
  reliefTestMode: false,
  paymentsEnabled: false,
  qaPremiumOverride: true,
  revenueCatConfigured: false,
});
assertEqual('QA override outside test mode fails closed', overrideOutsideTest.entitlementSource, 'FREE');
assertEqual('QA override outside test mode cannot purchase', overrideOutsideTest.canPurchase, false);

const ambiguous = resolvePaymentState({
  reliefTestMode: true,
  paymentsEnabled: true,
  qaPremiumOverride: true,
  revenueCatConfigured: true,
});
assertDeepEqual(
  'test mode remains the sole authority when flags conflict',
  {
    source: ambiguous.entitlementSource,
    qa: ambiguous.qaPremiumActive,
    billing: ambiguous.realPaymentsActive,
    purchase: ambiguous.canPurchase,
  },
  { source: 'QA_OVERRIDE', qa: true, billing: false, purchase: false },
);

const real = resolvePaymentState({
  reliefTestMode: false,
  paymentsEnabled: true,
  qaPremiumOverride: false,
  revenueCatConfigured: true,
});
assertEqual('configured real billing is the RevenueCat authority', real.entitlementSource, 'REVENUECAT');
assertTrue('configured real billing can purchase', real.canPurchase);
assertTrue('configured real billing can restore', real.canRestore);

const missingRevenueCat = resolvePaymentState({
  reliefTestMode: false,
  paymentsEnabled: true,
  qaPremiumOverride: false,
  revenueCatConfigured: false,
});
assertEqual('enabled billing without RevenueCat config fails closed', missingRevenueCat.entitlementSource, 'FREE');
assertEqual('enabled billing without RevenueCat cannot purchase', missingRevenueCat.canPurchase, false);

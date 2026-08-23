// ============================================================
// Relief — explicit payment and QA entitlement state
// ============================================================

export type EntitlementSource = 'FREE' | 'QA_OVERRIDE' | 'REVENUECAT';

export interface PaymentStateInput {
  reliefTestMode: boolean;
  paymentsEnabled: boolean;
  qaPremiumOverride: boolean;
  revenueCatConfigured: boolean;
}

export interface PaymentState {
  entitlementSource: EntitlementSource;
  qaPremiumActive: boolean;
  realPaymentsActive: boolean;
  canPurchase: boolean;
  canRestore: boolean;
  statusMessage: string;
}

/**
 * Resolve payment authority once, with safe defaults.
 *
 * Test mode has explicit QA authority and never calls real billing. Real
 * billing requires test mode to be off, the feature switch to be on, and
 * RevenueCat configuration to be present. Missing configuration is free and
 * unavailable rather than an implicit payment enablement.
 */
export function resolvePaymentState(input: PaymentStateInput): PaymentState {
  const qaPremiumActive = input.reliefTestMode && input.qaPremiumOverride;
  if (qaPremiumActive) {
    return {
      entitlementSource: 'QA_OVERRIDE',
      qaPremiumActive: true,
      realPaymentsActive: false,
      canPurchase: false,
      canRestore: false,
      statusMessage: 'QA premium access is enabled for this test build. Purchases and restores are disabled.',
    };
  }

  const realPaymentsActive =
    !input.reliefTestMode && input.paymentsEnabled && input.revenueCatConfigured;
  if (realPaymentsActive) {
    return {
      entitlementSource: 'REVENUECAT',
      qaPremiumActive: false,
      realPaymentsActive: true,
      canPurchase: true,
      canRestore: true,
      statusMessage: 'Purchases are processed securely through Google Play or the App Store.',
    };
  }

  return {
    entitlementSource: 'FREE',
    qaPremiumActive: false,
    realPaymentsActive: false,
    canPurchase: false,
    canRestore: false,
    statusMessage: input.paymentsEnabled
      ? 'Purchases are unavailable because billing is not configured for this build.'
      : 'Purchases are disabled in this build.',
  };
}

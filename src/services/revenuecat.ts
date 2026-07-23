// ============================================================
// Project "Relief" — RevenueCat Service (4.15 / 4.16 / 4.17)
// Client-side RevenueCat integration for purchase management
// Server-side entitlement verification via Supabase Edge Function
// ============================================================

import Purchases, {
  PurchasesOffering,
  PurchasesPackage,
  CustomerInfo,
  PURCHASES_ERROR_CODE,
} from 'react-native-purchases';
import type { PurchasesEntitlementInfo } from 'react-native-purchases';
import { supabase } from './supabase';
import { getCurrentUser } from './auth';

// RevenueCat API keys — configure in .env
const REVENUECAT_API_KEY_IOS = process.env.EXPO_PUBLIC_REVENUECAT_API_KEY_IOS || '';
const REVENUECAT_API_KEY_ANDROID = process.env.EXPO_PUBLIC_REVENUECAT_API_KEY_ANDROID || '';

export type SubscriptionTier = 'free' | 'basic' | 'plus';

export interface EntitlementInfo {
  tier: SubscriptionTier;
  isActive: boolean;
  isLifetime: boolean;
  expiresAt: string | null;
  willRenew: boolean;
  isGracePeriod: boolean;
}

// ============================================================
// Initialise RevenueCat SDK
// ============================================================
export async function initRevenueCat(): Promise<void> {
  const user = await getCurrentUser();
  const appUserId = user?.id || undefined;

  try {
    if (REVENUECAT_API_KEY_IOS) {
      await Purchases.configure({
        apiKey: REVENUECAT_API_KEY_IOS,
        appUserID: appUserId,
      });
    } else if (REVENUECAT_API_KEY_ANDROID) {
      await Purchases.configure({
        apiKey: REVENUECAT_API_KEY_ANDROID,
        appUserID: appUserId,
      });
    } else {
      console.warn('[RevenueCat] No API keys configured. Using mock mode.');
    }
  } catch (error) {
    console.error('[RevenueCat] Initialisation failed:', error);
  }
}

// ============================================================
// Identify user after login (syncs RevenueCat user ID)
// ============================================================
export async function identifyUser(userId: string): Promise<void> {
  try {
    await Purchases.logIn(userId);
  } catch (error) {
    console.error('[RevenueCat] Login failed:', error);
  }
}

// ============================================================
// Logout (reset RevenueCat anonymous ID)
// ============================================================
export async function resetUser(): Promise<void> {
  try {
    await Purchases.logOut();
  } catch (error) {
    console.error('[RevenueCat] Logout failed:', error);
  }
}

// ============================================================
// Get current offerings
// ============================================================
export async function getOfferings(): Promise<PurchasesOffering | null> {
  try {
    const offerings = await Purchases.getOfferings();
    return offerings.current || null;
  } catch (error) {
    console.error('[RevenueCat] Failed to get offerings:', error);
    return null;
  }
}

// ============================================================
// Purchase a package
// ============================================================
export async function purchasePackage(
  pack: PurchasesPackage,
): Promise<{ success: boolean; customerInfo?: CustomerInfo; error?: string }> {
  try {
    const { customerInfo } = await Purchases.purchasePackage(pack);
    return { success: true, customerInfo };
  } catch (error: any) {
    if (error.code === PURCHASES_ERROR_CODE.PURCHASE_CANCELLED_ERROR) {
      return { success: false, error: 'Purchase cancelled' };
    }
    console.error('[RevenueCat] Purchase failed:', error);
    return { success: false, error: error.message || 'Purchase failed' };
  }
}

// ============================================================
// 4.16 — Restore purchases
// ============================================================
export async function restorePurchases(): Promise<{
  success: boolean;
  customerInfo?: CustomerInfo;
  error?: string;
}> {
  try {
    const customerInfo = await Purchases.restorePurchases();
    return { success: true, customerInfo };
  } catch (error: any) {
    console.error('[RevenueCat] Restore failed:', error);
    return { success: false, error: error.message || 'Restore failed' };
  }
}

// ============================================================
// Get current customer info (entitlements)
// ============================================================
export async function getCustomerInfo(): Promise<CustomerInfo | null> {
  try {
    const customerInfo = await Purchases.getCustomerInfo();
    return customerInfo;
  } catch (error) {
    console.error('[RevenueCat] Failed to get customer info:', error);
    return null;
  }
}

// ============================================================
// Get entitlements from customer info
// ============================================================
export function getEntitlements(customerInfo: CustomerInfo): {
  basic: EntitlementInfo;
  plus: EntitlementInfo;
} {
  const entitlements = customerInfo.entitlements.active;

  const getEntitlementInfo = (entitlementId: string): EntitlementInfo => {
    const entitlement: PurchasesEntitlementInfo | undefined = entitlements[entitlementId];
    if (!entitlement) {
      return {
        tier: entitlementId as SubscriptionTier,
        isActive: false,
        isLifetime: false,
        expiresAt: null,
        willRenew: false,
        isGracePeriod: false,
      };
    }

    return {
      tier: entitlementId as SubscriptionTier,
      isActive: entitlement.isActive,
      isLifetime: !entitlement.expirationDate,
      expiresAt: entitlement.expirationDate,
      willRenew: entitlement.willRenew,
      isGracePeriod: false,
    };
  };

  return {
    basic: getEntitlementInfo('basic'),
    plus: getEntitlementInfo('plus'),
  };
}

// ============================================================
// Determine user's highest tier from entitlements
// ============================================================
export function getHighestTier(entitlements: {
  basic: EntitlementInfo;
  plus: EntitlementInfo;
}): SubscriptionTier {
  if (entitlements.plus.isActive) return 'plus';
  if (entitlements.basic.isActive) return 'basic';
  return 'free';
}

// ============================================================
// Fetch entitlement from Supabase (server-side verified)
// Used as fallback/cache verification
// ============================================================
export async function getServerSideEntitlement(): Promise<{
  tier: SubscriptionTier;
  isActive: boolean;
  expiresAt: string | null;
  error?: string;
}> {
  try {
    const { data: userData } = await supabase.auth.getUser();
    if (!userData?.user) {
      return { tier: 'free', isActive: false, expiresAt: null };
    }

    const { data, error } = await supabase
      .from('user_subscriptions')
      .select('tier, is_active, current_period_end')
      .eq('user_id', userData.user.id)
      .single();

    if (error || !data) {
      return { tier: 'free', isActive: false, expiresAt: null };
    }

    return {
      tier: data.tier as SubscriptionTier,
      isActive: data.is_active,
      expiresAt: data.current_period_end,
    };
  } catch (error) {
    console.error('[RevenueCat] Server-side entitlement fetch failed:', error);
    return { tier: 'free', isActive: false, expiresAt: null };
  }
}

// ============================================================
// Get subscription events (for display in settings)
// ============================================================
export async function getSubscriptionEvents(): Promise<any[]> {
  try {
    const { data: userData } = await supabase.auth.getUser();
    if (!userData?.user) return [];

    const { data, error } = await supabase
      .from('subscription_events')
      .select('*')
      .eq('user_id', userData.user.id)
      .order('created_at', { ascending: false })
      .limit(20);

    if (error) return [];
    return data || [];
  } catch (error) {
    return [];
  }
}
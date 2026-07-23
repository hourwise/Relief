// ============================================================
// Project "Relief" — Subscription Context (4.19)
// Caches entitlements locally for graceful offline use
// ============================================================

import React, { createContext, useContext, useState, useEffect, useCallback, useRef } from 'react';
import AsyncStorage from '@react-native-async-storage/async-storage';
import type { SubscriptionTier, EntitlementInfo } from '../services/revenuecat';
import {
  initRevenueCat,
  identifyUser,
  resetUser,
  getCustomerInfo,
  getEntitlements,
  getHighestTier,
  getServerSideEntitlement,
  restorePurchases as rcRestorePurchases,
  purchasePackage,
} from '../services/revenuecat';
import { getCurrentUser, onAuthStateChange } from '../services/auth';
import type { PurchasesPackage, CustomerInfo } from 'react-native-purchases';

// ============================================================
// Constants
// ============================================================
const CACHE_KEY = '@relief/entitlement_cache';
const CACHE_TTL_MS = 24 * 60 * 60 * 1000; // 24 hours cache expiry

// ============================================================
// Types
// ============================================================
interface CachedEntitlement {
  tier: SubscriptionTier;
  isActive: boolean;
  expiresAt: string | null;
  cachedAt: string;
}

interface SubscriptionState {
  tier: SubscriptionTier;
  isActive: boolean;
  isBasicAccess: boolean;
  isPlusSubscriber: boolean;
  isLifetime: boolean;
  expiresAt: string | null;
  willRenew: boolean;
  isGracePeriod: boolean;
  loading: boolean;
  initialised: boolean;
  lastRefreshAt: Date | null;
}

interface SubscriptionContextValue extends SubscriptionState {
  refreshEntitlements: () => Promise<void>;
  purchase: (pack: PurchasesPackage) => Promise<{ success: boolean; error?: string }>;
  restore: () => Promise<{ success: boolean; error?: string }>;
  signOutAndReset: () => Promise<void>;
  isFeatureLocked: (feature: PremiumFeature) => boolean;
}

export type PremiumFeature =
  | 'route_planning'
  | 'offline_maps'
  | 'saved_profiles'
  | 'ai_recommendations'
  | 'travel_support'
  | 'europe_expansion'
  | 'smart_alerts';

// Feature → tier mapping
const FEATURE_TIER_MAP: Record<PremiumFeature, SubscriptionTier> = {
  route_planning: 'plus',
  offline_maps: 'plus',
  saved_profiles: 'plus',
  ai_recommendations: 'plus',
  travel_support: 'plus',
  europe_expansion: 'plus',
  smart_alerts: 'plus',
};

// ============================================================
// Default state
// ============================================================
const defaultState: SubscriptionState = {
  tier: 'free',
  isActive: false,
  isBasicAccess: false,
  isPlusSubscriber: false,
  isLifetime: false,
  expiresAt: null,
  willRenew: false,
  isGracePeriod: false,
  loading: true,
  initialised: false,
  lastRefreshAt: null,
};

// ============================================================
// Context
// ============================================================
const SubscriptionContext = createContext<SubscriptionContextValue>({
  ...defaultState,
  refreshEntitlements: async () => {},
  purchase: async () => ({ success: false }),
  restore: async () => ({ success: false }),
  signOutAndReset: async () => {},
  isFeatureLocked: () => true,
});

export const useSubscription = () => useContext(SubscriptionContext);

// ============================================================
// Cache helpers (4.19 — graceful offline use)
// ============================================================
async function cacheEntitlement(state: SubscriptionState): Promise<void> {
  try {
    const cache: CachedEntitlement = {
      tier: state.tier,
      isActive: state.isActive,
      expiresAt: state.expiresAt,
      cachedAt: new Date().toISOString(),
    };
    await AsyncStorage.setItem(CACHE_KEY, JSON.stringify(cache));
  } catch (error) {
    console.warn('[SubscriptionCache] Failed to cache:', error);
  }
}

async function getCachedEntitlement(): Promise<CachedEntitlement | null> {
  try {
    const cached = await AsyncStorage.getItem(CACHE_KEY);
    if (!cached) return null;

    const parsed: CachedEntitlement = JSON.parse(cached);
    const age = Date.now() - new Date(parsed.cachedAt).getTime();

    // Only use cache if within TTL
    if (age > CACHE_TTL_MS) {
      await AsyncStorage.removeItem(CACHE_KEY);
      return null;
    }

    return parsed;
  } catch (error) {
    return null;
  }
}

async function clearCachedEntitlement(): Promise<void> {
  try {
    await AsyncStorage.removeItem(CACHE_KEY);
  } catch (error) {
    console.warn('[SubscriptionCache] Failed to clear:', error);
  }
}

// ============================================================
// Subscription Provider
// ============================================================
export const SubscriptionProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [state, setState] = useState<SubscriptionState>(defaultState);
  const initialisedRef = useRef(false);

  // Build state from entitlements
  const buildState = useCallback((tier: SubscriptionTier, isActive: boolean, customerInfo?: CustomerInfo): SubscriptionState => {
    let isLifetime = false;
    let willRenew = false;
    let isGracePeriod = false;
    let expiresAt: string | null = null;

    if (customerInfo) {
      const entitlements = getEntitlements(customerInfo);
      const activeEntitlement = entitlements[tier === 'plus' ? 'plus' : 'basic'];
      if (activeEntitlement) {
        isLifetime = activeEntitlement.isLifetime;
        willRenew = activeEntitlement.willRenew;
        isGracePeriod = activeEntitlement.isGracePeriod;
        expiresAt = activeEntitlement.expiresAt;
      }
    }

    return {
      tier,
      isActive,
      isBasicAccess: tier === 'basic' && isActive,
      isPlusSubscriber: tier === 'plus' && isActive,
      isLifetime,
      expiresAt,
      willRenew,
      isGracePeriod,
      loading: false,
      initialised: true,
      lastRefreshAt: new Date(),
    };
  }, []);

  // Refresh entitlements (from RevenueCat SDK + Supabase fallback)
  const refreshEntitlements = useCallback(async () => {
    setState(prev => ({ ...prev, loading: true }));

    try {
      // Try RevenueCat SDK first
      const customerInfo = await getCustomerInfo();
      if (customerInfo) {
        const entitlements = getEntitlements(customerInfo);
        const tier = getHighestTier(entitlements);
        const isActive = tier !== 'free';
        const newState = buildState(tier, isActive, customerInfo);
        setState(newState);
        await cacheEntitlement(newState);
        return;
      }

      // Fallback: Supabase server-side
      const serverSide = await getServerSideEntitlement();
      if (serverSide) {
        const newState = buildState(serverSide.tier, serverSide.isActive);
        setState(newState);
        await cacheEntitlement(newState);
        return;
      }

      // Last resort: cached data (4.19 — graceful offline)
      const cached = await getCachedEntitlement();
      if (cached) {
        const newState = buildState(cached.tier, cached.isActive);
        setState(newState);
        return;
      }

      // Default: free tier
      const newState = buildState('free', false);
      setState(newState);
    } catch (error) {
      console.error('[SubscriptionContext] Refresh failed:', error);

      // Use cache on error (offline fallback)
      const cached = await getCachedEntitlement();
      if (cached) {
        const newState = buildState(cached.tier, cached.isActive);
        setState(newState);
      } else {
        setState(prev => ({ ...prev, loading: false }));
      }
    }
  }, [buildState]);

  // Purchase
  const purchase = useCallback(async (pack: PurchasesPackage) => {
    const result = await purchasePackage(pack);
    if (result.success) {
      await refreshEntitlements();
    }
    return result;
  }, [refreshEntitlements]);

  // Restore (4.16)
  const restore = useCallback(async () => {
    const result = await rcRestorePurchases();
    if (result.success) {
      await refreshEntitlements();
    }
    return result;
  }, [refreshEntitlements]);

  // Sign out and reset
  const signOutAndReset = useCallback(async () => {
    try {
      await resetUser();
      await clearCachedEntitlement();
      setState({ ...defaultState, loading: false });
    } catch (error) {
      console.error('[SubscriptionContext] Sign out reset failed:', error);
    }
  }, []);

  // Check if a feature is locked behind a paywall
  const isFeatureLocked = useCallback((feature: PremiumFeature): boolean => {
    const requiredTier = FEATURE_TIER_MAP[feature];

    // 'free' features are never locked
    if (requiredTier === 'free') return false;

    // Basic features: basic tier or above
    if (requiredTier === 'basic') {
      return !state.isBasicAccess && !state.isPlusSubscriber;
    }

    // Plus features: only plus tier
    if (requiredTier === 'plus') {
      return !state.isPlusSubscriber;
    }

    return true;
  }, [state]);

  // Initialise on mount
  useEffect(() => {
    if (initialisedRef.current) return;
    initialisedRef.current = true;

    const init = async () => {
      await initRevenueCat();
      await refreshEntitlements();
    };

    init();
  }, [refreshEntitlements]);

  // Listen for auth changes to re-sync
  useEffect(() => {
    const subscription = onAuthStateChange(async (session) => {
      if (session?.user) {
        await identifyUser(session.user.id);
        await refreshEntitlements();
      } else {
        await signOutAndReset();
      }
    });

    return () => {
      subscription?.subscription.unsubscribe();
    };
  }, [refreshEntitlements, signOutAndReset]);

  const value: SubscriptionContextValue = {
    ...state,
    refreshEntitlements,
    purchase,
    restore,
    signOutAndReset,
    isFeatureLocked,
  };

  return (
    <SubscriptionContext.Provider value={value}>
      {children}
    </SubscriptionContext.Provider>
  );
};
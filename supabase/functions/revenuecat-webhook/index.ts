// ============================================================
// Project "Relief" — RevenueCat Webhook Edge Function (4.15)
// Server-side entitlement verification via RevenueCat
// Handles: purchases, renewals, cancellations, refunds, expiry
// ============================================================

import { serve } from 'https://deno.land/std@0.168.0/http/server.ts';
import { createClient } from 'https://esm.sh/@supabase/supabase-js@2';

interface RevenueCatEvent {
  event: {
    type: string;
    app_user_id: string;
    product_id: string;
    entitlement_id: string;
    period_type: string;
    purchased_at_ms: number;
    expiration_at_ms: number | null;
    environment: string;
    store: string;
    cancellation_reason: string | null;
    is_trial_conversion: boolean;
    offer_code: string | null;
    original_app_user_id: string;
    event_timestamp_ms: number;
    id: string;
  };
}

interface SyncResult {
  synced: boolean;
  event_type: string;
  user_id: string | null;
  tier: string;
  error?: string;
}

function mapProductToTier(productId: string, entitlementId: string): string {
  // Map RevenueCat product/entitlement IDs to our tiers
  const lowerProduct = productId?.toLowerCase() || '';
  const lowerEntitlement = entitlementId?.toLowerCase() || '';

  if (lowerEntitlement.includes('basic') || lowerProduct.includes('basic_access') || lowerProduct.includes('basic')) {
    return 'basic';
  }
  if (lowerEntitlement.includes('plus') || lowerProduct.includes('plus_subscription') || lowerProduct.includes('plus_monthly') || lowerProduct.includes('plus_yearly')) {
    return 'plus';
  }
  return 'free';
}

function mapEventType(revenuecatType: string): string {
  const eventMap: Record<string, string> = {
    'INITIAL_PURCHASE': 'purchase_initial',
    'NON_RENEWING_PURCHASE': 'lifetime_purchase',
    'RENEWAL': 'purchase_renewal',
    'CANCELLATION': 'cancellation',
    'UNCANCELLATION': 'cancellation', // They un-cancelled
    'EXPIRATION': 'expiration',
    'BILLING_ISSUE': 'grace_period_start',
    'SUBSCRIBER_ALIAS': 'tier_change',
    'TRANSFER': 'tier_change',
    'REFUND': 'refund',
  };
  return eventMap[revenuecatType] || 'purchase_initial';
}

serve(async (req) => {
  try {
    // Parse the RevenueCat webhook payload
    const payload: RevenueCatEvent = await req.json();
    const event = payload.event;

    if (!event || !event.app_user_id) {
      return new Response(
        JSON.stringify({ error: 'Invalid payload: missing event or app_user_id' }),
        { headers: { 'Content-Type': 'application/json' }, status: 400 },
      );
    }

    // Create Supabase client with service role key
    const supabaseUrl = Deno.env.get('SUPABASE_URL') ?? '';
    const supabaseServiceKey = Deno.env.get('SUPABASE_SERVICE_ROLE_KEY') ?? '';
    const webhookSecret = Deno.env.get('REVENUECAT_WEBHOOK_SECRET') ?? '';

    if (!supabaseUrl || !supabaseServiceKey) {
      throw new Error('Missing Supabase environment variables');
    }

    // Verify webhook secret if configured
    const authHeader = req.headers.get('authorization') || '';
    if (webhookSecret && authHeader !== `Bearer ${webhookSecret}`) {
      return new Response(
        JSON.stringify({ error: 'Unauthorized' }),
        { headers: { 'Content-Type': 'application/json' }, status: 401 },
      );
    }

    const supabase = createClient(supabaseUrl, supabaseServiceKey, {
      auth: { autoRefreshToken: false, persistSession: false },
    });

    // Find the user by their RevenueCat app_user_id
    // app_user_id is our Supabase user UUID
    const userId = event.app_user_id;
    const tier = mapProductToTier(event.product_id, event.entitlement_id);
    const eventType = mapEventType(event.type);

    console.log(`Processing ${event.type} → ${eventType} for user ${userId}, tier: ${tier}`);

    // Calculate subscription dates
    const purchasedAt = event.purchased_at_ms
      ? new Date(event.purchased_at_ms).toISOString()
      : null;
    const expiresAt = event.expiration_at_ms
      ? new Date(event.expiration_at_ms).toISOString()
      : null;

    // Determine if active: active unless expired/cancelled/refunded
    const isActive = ![
      'EXPIRATION',
      'CANCELLATION',
      'REFUND',
    ].includes(event.type);

    const isGracePeriod = event.type === 'BILLING_ISSUE';
    const willRenew = event.type !== 'CANCELLATION' && event.type !== 'EXPIRATION';

    const cancellationAt = event.type === 'CANCELLATION' && event.cancellation_reason
      ? new Date(event.event_timestamp_ms).toISOString()
      : null;

    const cancelledAt = event.type === 'CANCELLATION'
      ? new Date(event.event_timestamp_ms).toISOString()
      : null;

    const refundedAt = event.type === 'REFUND'
      ? new Date(event.event_timestamp_ms).toISOString()
      : null;

    // Call the database function to sync subscription
    const { error } = await supabase.rpc('sync_subscription_from_revenuecat', {
      p_user_id: userId,
      p_tier: tier,
      p_is_active: isActive,
      p_lifetime_purchase_at: tier === 'basic' ? purchasedAt : null,
      p_current_period_start: purchasedAt,
      p_current_period_end: expiresAt,
      p_will_renew: willRenew,
      p_is_grace_period: isGracePeriod,
      p_cancellation_at: cancellationAt,
      p_cancelled_at: cancelledAt,
      p_refunded_at: refundedAt,
      p_raw_json: payload,
      p_event_type: eventType,
      p_previous_tier: null,
    });

    if (error) {
      console.error('Error syncing subscription:', error);
      const result: SyncResult = {
        synced: false,
        event_type: eventType,
        user_id: userId,
        tier,
        error: error.message,
      };
      return new Response(JSON.stringify(result), {
        headers: { 'Content-Type': 'application/json' },
        status: 500,
      });
    }

    const result: SyncResult = {
      synced: true,
      event_type: eventType,
      user_id: userId,
      tier,
    };

    return new Response(JSON.stringify(result), {
      headers: { 'Content-Type': 'application/json' },
      status: 200,
    });
  } catch (error) {
    console.error('RevenueCat webhook error:', error);
    return new Response(
      JSON.stringify({ error: 'Webhook processing failed', details: (error as Error).message }),
      { headers: { 'Content-Type': 'application/json' }, status: 500 },
    );
  }
});
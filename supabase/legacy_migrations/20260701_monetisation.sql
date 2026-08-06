-- ============================================================
-- Project "Relief" — Monetisation Migration (Phase 4.13-4.19)
-- Tables: user_subscriptions, subscription_events
-- ============================================================

-- ────────────────────────────────────────
-- 4.13 / 4.14 — User Subscriptions
-- Tracks Basic Access (lifetime) and Plus (recurring)
-- RevenueCat as source of truth, this table caches locally
-- ────────────────────────────────────────
CREATE TABLE IF NOT EXISTS user_subscriptions (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
  revenuecat_id TEXT UNIQUE, -- RevenueCat App User ID
  tier TEXT NOT NULL DEFAULT 'free' CHECK (tier IN ('free', 'basic', 'plus')),
  is_active BOOLEAN NOT NULL DEFAULT false,
  -- Basic Access (lifetime)
  lifetime_purchase_at TIMESTAMPTZ,
  -- Plus (recurring)
  plus_monthly_purchase_at TIMESTAMPTZ,
  plus_yearly_purchase_at TIMESTAMPTZ,
  current_period_start TIMESTAMPTZ,
  current_period_end TIMESTAMPTZ,
  will_renew BOOLEAN NOT NULL DEFAULT true,
  -- Management
  is_grace_period BOOLEAN NOT NULL DEFAULT false,
  cancellation_at TIMESTAMPTZ,
  cancelled_at TIMESTAMPTZ,
  refunded_at TIMESTAMPTZ,
  -- Metadata
  raw_revenuecat_json JSONB, -- Full RevenueCat response cached
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE UNIQUE INDEX IF NOT EXISTS idx_user_subscriptions_user ON user_subscriptions(user_id);
CREATE INDEX IF NOT EXISTS idx_user_subscriptions_tier ON user_subscriptions(tier);
CREATE INDEX IF NOT EXISTS idx_user_subscriptions_active ON user_subscriptions(is_active);

ALTER TABLE user_subscriptions ENABLE ROW LEVEL SECURITY;

-- Users can read their own subscription
CREATE POLICY "Users can read own subscription"
  ON user_subscriptions FOR SELECT
  TO authenticated
  USING (auth.uid() = user_id);

-- Only server-side (service_role) can insert/update/delete
CREATE POLICY "Service role manages subscriptions"
  ON user_subscriptions FOR ALL
  TO service_role
  USING (true)
  WITH CHECK (true);

-- ────────────────────────────────────────
-- 4.17 — Subscription Events Log
-- Audit trail for refunds, cancellations, expiry
-- ────────────────────────────────────────
CREATE TABLE IF NOT EXISTS subscription_events (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
  event_type TEXT NOT NULL CHECK (event_type IN (
    'purchase_initial',
    'purchase_renewal',
    'cancellation',
    'expiration',
    'refund',
    'restore',
    'grace_period_start',
    'grace_period_end',
    'tier_change',
    'lifetime_purchase'
  )),
  tier TEXT NOT NULL,
  previous_tier TEXT,
  details JSONB,
  revenuecat_event_id TEXT,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_subscription_events_user ON subscription_events(user_id);
CREATE INDEX IF NOT EXISTS idx_subscription_events_type ON subscription_events(event_type);

ALTER TABLE subscription_events ENABLE ROW LEVEL SECURITY;

-- Users can read own events
CREATE POLICY "Users can read own events"
  ON subscription_events FOR SELECT
  TO authenticated
  USING (auth.uid() = user_id);

-- Only server-side can insert
CREATE POLICY "Service role manages events"
  ON subscription_events FOR INSERT
  TO service_role
  WITH CHECK (true);

-- ────────────────────────────────────────
-- Function to sync RevenueCat data to user_subscriptions
-- Called by the Edge Function webhook
-- ────────────────────────────────────────
CREATE OR REPLACE FUNCTION sync_subscription_from_revenuecat(
  p_user_id UUID,
  p_tier TEXT,
  p_is_active BOOLEAN,
  p_lifetime_purchase_at TIMESTAMPTZ,
  p_current_period_start TIMESTAMPTZ,
  p_current_period_end TIMESTAMPTZ,
  p_will_renew BOOLEAN,
  p_is_grace_period BOOLEAN,
  p_cancellation_at TIMESTAMPTZ,
  p_cancelled_at TIMESTAMPTZ,
  p_refunded_at TIMESTAMPTZ,
  p_raw_json JSONB,
  p_event_type TEXT,
  p_previous_tier TEXT DEFAULT NULL
) RETURNS void AS $$
BEGIN
  -- Upsert the subscription record
  INSERT INTO user_subscriptions (
    user_id,
    tier,
    is_active,
    lifetime_purchase_at,
    current_period_start,
    current_period_end,
    will_renew,
    is_grace_period,
    cancellation_at,
    cancelled_at,
    refunded_at,
    raw_revenuecat_json,
    updated_at
  ) VALUES (
    p_user_id,
    p_tier,
    p_is_active,
    p_lifetime_purchase_at,
    p_current_period_start,
    p_current_period_end,
    p_will_renew,
    p_is_grace_period,
    p_cancellation_at,
    p_cancelled_at,
    p_refunded_at,
    p_raw_json,
    now()
  )
  ON CONFLICT (user_id) DO UPDATE SET
    tier = EXCLUDED.tier,
    is_active = EXCLUDED.is_active,
    lifetime_purchase_at = EXCLUDED.lifetime_purchase_at,
    current_period_start = EXCLUDED.current_period_start,
    current_period_end = EXCLUDED.current_period_end,
    will_renew = EXCLUDED.will_renew,
    is_grace_period = EXCLUDED.is_grace_period,
    cancellation_at = EXCLUDED.cancellation_at,
    cancelled_at = EXCLUDED.cancelled_at,
    refunded_at = EXCLUDED.refunded_at,
    raw_revenuecat_json = EXCLUDED.raw_revenuecat_json,
    updated_at = now();

  -- Log the event
  INSERT INTO subscription_events (
    user_id,
    event_type,
    tier,
    previous_tier,
    details,
    revenuecat_event_id
  ) VALUES (
    p_user_id,
    p_event_type,
    p_tier,
    p_previous_tier,
    p_raw_json,
    p_raw_json->>'event_id'
  );
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Grant execute to service_role
REVOKE ALL ON FUNCTION sync_subscription_from_revenuecat(UUID, TEXT, BOOLEAN, TIMESTAMPTZ, TIMESTAMPTZ, TIMESTAMPTZ, BOOLEAN, BOOLEAN, TIMESTAMPTZ, TIMESTAMPTZ, TIMESTAMPTZ, JSONB, TEXT, TEXT) FROM PUBLIC;
GRANT EXECUTE ON FUNCTION sync_subscription_from_revenuecat(UUID, TEXT, BOOLEAN, TIMESTAMPTZ, TIMESTAMPTZ, TIMESTAMPTZ, BOOLEAN, BOOLEAN, TIMESTAMPTZ, TIMESTAMPTZ, TIMESTAMPTZ, JSONB, TEXT, TEXT) TO service_role;
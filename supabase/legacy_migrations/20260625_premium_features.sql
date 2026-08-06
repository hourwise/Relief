-- ============================================================
-- Project "Relief" — Premium Features Migration (Phase 4)
-- Tables: saved_profiles, favourites
-- ============================================================

-- ────────────────────────────────────────
-- 4.1 — Saved Profiles (preference presets)
-- ────────────────────────────────────────
CREATE TABLE IF NOT EXISTS saved_profiles (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
  mode TEXT NOT NULL CHECK (mode IN ('ibs', 'family', 'accessibility', 'pregnancy', 'neurodivergent', 'elderly')),
  name TEXT NOT NULL,
  preferences JSONB NOT NULL DEFAULT '{}'::jsonb,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_saved_profiles_user ON saved_profiles(user_id);

ALTER TABLE saved_profiles ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can manage own profiles"
  ON saved_profiles FOR ALL
  TO authenticated
  USING (auth.uid() = user_id)
  WITH CHECK (auth.uid() = user_id);

-- ────────────────────────────────────────
-- 4.3 — Favourites (facilities, chains, routes)
-- ────────────────────────────────────────
-- Note: The base 'favourites' table already exists in a prior migration.
-- This ensures it's created if not present.
CREATE TABLE IF NOT EXISTS favourites (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
  facility_id UUID NOT NULL REFERENCES facilities(id) ON DELETE CASCADE,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  UNIQUE(user_id, facility_id)
);

CREATE INDEX IF NOT EXISTS idx_favourites_user ON favourites(user_id);
CREATE INDEX IF NOT EXISTS idx_favourites_facility ON favourites(facility_id);

ALTER TABLE favourites ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can manage own favourites"
  ON favourites FOR ALL
  TO authenticated
  USING (auth.uid() = user_id)
  WITH CHECK (auth.uid() = user_id);
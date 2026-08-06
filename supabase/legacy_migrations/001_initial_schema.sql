-- ============================================================
-- Project "Relief" — Initial Database Schema
-- ============================================================

-- ============================================================
-- FACILITIES TABLE
-- ============================================================
CREATE TABLE facilities (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  name TEXT NOT NULL,
  address TEXT NOT NULL,
  latitude DOUBLE PRECISION NOT NULL,
  longitude DOUBLE PRECISION NOT NULL,
  postcode TEXT NOT NULL,
  town TEXT NOT NULL,
  country TEXT NOT NULL DEFAULT 'GB',

  -- Details
  photos TEXT[] DEFAULT '{}',
  open_hours JSONB,
  is_free BOOLEAN DEFAULT true,
  price_note TEXT,
  access_notes TEXT DEFAULT '',
  last_verified_at TIMESTAMPTZ,

  -- Amenities (Phase 1)
  is_accessible BOOLEAN DEFAULT false,
  is_disabled_access BOOLEAN DEFAULT false,
  has_baby_changing BOOLEAN DEFAULT false,
  has_family_room BOOLEAN DEFAULT false,
  is_gender_neutral BOOLEAN DEFAULT false,
  is_single_occupancy BOOLEAN DEFAULT false,
  is_24h BOOLEAN DEFAULT false,

  -- Privacy (Phase 3)
  is_single_room BOOLEAN DEFAULT false,
  has_floor_to_ceiling_cubicles BOOLEAN DEFAULT false,
  is_quiet BOOLEAN DEFAULT false,

  -- Accessibility (Phase 3)
  has_wheelchair_access BOOLEAN DEFAULT false,
  requires_radar_key BOOLEAN DEFAULT false,
  has_adult_changing_place BOOLEAN DEFAULT false,
  has_lift BOOLEAN DEFAULT false,
  has_grab_rails BOOLEAN DEFAULT false,

  -- Baby Facilities (Phase 3)
  has_baby_changing_inside BOOLEAN DEFAULT false,
  has_separate_changing_room BOOLEAN DEFAULT false,
  has_family_toilet BOOLEAN DEFAULT false,
  has_pram_access BOOLEAN DEFAULT false,

  -- Equipment (Phase 3)
  has_soap BOOLEAN DEFAULT false,
  has_paper_towels BOOLEAN DEFAULT false,
  has_hand_dryer BOOLEAN DEFAULT false,
  has_mirror BOOLEAN DEFAULT false,
  has_shelf BOOLEAN DEFAULT false,
  has_hooks BOOLEAN DEFAULT false,
  has_sanitary_bins BOOLEAN DEFAULT false,
  has_free_period_products BOOLEAN DEFAULT false,
  has_drinking_water BOOLEAN DEFAULT false,

  -- Environment (Phase 3)
  noise_level INTEGER DEFAULT 3 CHECK (noise_level >= 1 AND noise_level <= 5),
  temperature INTEGER DEFAULT 3 CHECK (temperature >= 1 AND temperature <= 5),
  lighting INTEGER DEFAULT 3 CHECK (lighting >= 1 AND lighting <= 5),
  smell INTEGER DEFAULT 3 CHECK (smell >= 1 AND smell <= 5),

  -- Safety (Phase 3)
  has_staff_nearby BOOLEAN DEFAULT false,
  has_cctv BOOLEAN DEFAULT false,
  is_women_friendly BOOLEAN DEFAULT false,
  is_family_friendly BOOLEAN DEFAULT false,

  -- Extra (Requested)
  is_picnic_area BOOLEAN DEFAULT false,

  -- Ratings
  overall_score DOUBLE PRECISION DEFAULT 0,
  cleanliness_rating DOUBLE PRECISION DEFAULT 0,
  privacy_rating DOUBLE PRECISION DEFAULT 0,
  accessibility_rating DOUBLE PRECISION DEFAULT 0,
  safety_rating DOUBLE PRECISION DEFAULT 0,
  noise_rating DOUBLE PRECISION DEFAULT 0,
  environment_rating DOUBLE PRECISION DEFAULT 0,

  -- Metadata
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW(),
  created_by UUID REFERENCES auth.users(id) ON DELETE SET NULL,
  is_verified BOOLEAN DEFAULT false
);

-- Indexes for spatial queries
CREATE INDEX idx_facilities_location ON facilities (latitude, longitude);
CREATE INDEX idx_facilities_town ON facilities (town);
CREATE INDEX idx_facilities_postcode ON facilities (postcode);
CREATE INDEX idx_facilities_country ON facilities (country);
CREATE INDEX idx_facilities_is_verified ON facilities (is_verified);
CREATE INDEX idx_facilities_overall_score ON facilities (overall_score DESC);
CREATE INDEX idx_facilities_created_at ON facilities (created_at DESC);

-- ============================================================
-- USER PROFILES TABLE
-- ============================================================
CREATE TABLE user_profiles (
  id UUID PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
  email TEXT,
  display_name TEXT,
  avatar_url TEXT,
  created_at TIMESTAMPTZ DEFAULT NOW(),
  has_lifetime_access BOOLEAN DEFAULT false,
  subscription_tier TEXT CHECK (subscription_tier IN ('free', 'plus')) DEFAULT 'free',
  subscription_expires_at TIMESTAMPTZ
);

-- ============================================================
-- FACILITY REPORTS TABLE
-- ============================================================
CREATE TABLE facility_reports (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  facility_id UUID NOT NULL REFERENCES facilities(id) ON DELETE CASCADE,
  user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
  type TEXT NOT NULL CHECK (type IN ('temporary', 'permanent')),
  reason TEXT NOT NULL CHECK (reason IN (
    'out_of_order', 'no_water', 'cleaning', 'busy',
    'closed_permanently', 'refurbishment'
  )),
  notes TEXT DEFAULT '',
  expires_at TIMESTAMPTZ,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_reports_facility ON facility_reports (facility_id);
CREATE INDEX idx_reports_expires ON facility_reports (expires_at);

-- ============================================================
-- USER BADGES TABLE
-- ============================================================
CREATE TABLE user_badges (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
  badge_type TEXT NOT NULL CHECK (badge_type IN (
    'explorer', 'community_hero', 'accessibility_champion', 'family_helper'
  )),
  awarded_at TIMESTAMPTZ DEFAULT NOW(),
  UNIQUE(user_id, badge_type)
);

-- ============================================================
-- SAVED PROFILES TABLE
-- ============================================================
CREATE TABLE saved_profiles (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
  mode TEXT NOT NULL CHECK (mode IN (
    'ibs', 'family', 'accessibility', 'pregnancy', 'neurodivergent', 'elderly'
  )),
  name TEXT NOT NULL,
  preferences JSONB NOT NULL DEFAULT '{}',
  created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_saved_profiles_user ON saved_profiles (user_id);

-- ============================================================
-- FAVOURITES TABLE
-- ============================================================
CREATE TABLE favourites (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
  facility_id UUID NOT NULL REFERENCES facilities(id) ON DELETE CASCADE,
  created_at TIMESTAMPTZ DEFAULT NOW(),
  UNIQUE(user_id, facility_id)
);

CREATE INDEX idx_favourites_user ON favourites (user_id);

-- ============================================================
-- ROW LEVEL SECURITY
-- ============================================================

-- Facilities: public read (verified only), admin insert
ALTER TABLE facilities ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Verified facilities are viewable by everyone"
  ON facilities FOR SELECT
  USING (is_verified = true);

-- User profiles: users can read/update their own
ALTER TABLE user_profiles ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can view their own profile"
  ON user_profiles FOR SELECT
  USING (id = auth.uid());

CREATE POLICY "Users can update their own profile"
  ON user_profiles FOR UPDATE
  USING (id = auth.uid());

-- Reports: public read, authenticated create
ALTER TABLE facility_reports ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Reports are viewable by everyone"
  ON facility_reports FOR SELECT
  USING (true);

CREATE POLICY "Authenticated users can create reports"
  ON facility_reports FOR INSERT
  TO authenticated
  WITH CHECK (user_id = auth.uid());

-- Badges: public read, system insert
ALTER TABLE user_badges ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Badges are viewable by everyone"
  ON user_badges FOR SELECT
  USING (true);

-- Favourites: user only
ALTER TABLE favourites ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users manage their own favourites"
  ON favourites FOR ALL
  USING (user_id = auth.uid());

-- Saved profiles: user only
ALTER TABLE saved_profiles ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users manage their own saved profiles"
  ON saved_profiles FOR ALL
  USING (user_id = auth.uid());

-- ============================================================
-- TRIGGERS
-- ============================================================

-- Auto-create profile on user signup
CREATE OR REPLACE FUNCTION handle_new_user()
RETURNS TRIGGER AS $$
BEGIN
  INSERT INTO public.user_profiles (id, email, display_name)
  VALUES (
    NEW.id,
    NEW.email,
    COALESCE(NEW.raw_user_meta_data->>'full_name', NEW.email)
  );
  RETURN NEW;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

CREATE TRIGGER on_auth_user_created
  AFTER INSERT ON auth.users
  FOR EACH ROW
  EXECUTE FUNCTION handle_new_user();

-- Auto-update updated_at on facilities
CREATE OR REPLACE FUNCTION update_updated_at()
RETURNS TRIGGER AS $$
BEGIN
  NEW.updated_at = NOW();
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER facilities_updated_at
  BEFORE UPDATE ON facilities
  FOR EACH ROW
  EXECUTE FUNCTION update_updated_at();

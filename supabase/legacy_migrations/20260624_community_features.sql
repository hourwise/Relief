-- ============================================================
-- Project "Relief" — Community Features Migration
-- Phase 2: Facility submissions, photo moderation,
-- temporary reports, corrections, access codes, badges, rate limits
-- ============================================================

-- ────────────────────────────────────────
-- 2.1 — Facility Submissions (moderation queue)
-- ────────────────────────────────────────
CREATE TABLE IF NOT EXISTS facility_submissions (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
  status TEXT NOT NULL DEFAULT 'pending' CHECK (status IN ('pending', 'approved', 'rejected')),
  name TEXT NOT NULL,
  address TEXT NOT NULL,
  latitude DOUBLE PRECISION NOT NULL,
  longitude DOUBLE PRECISION NOT NULL,
  postcode TEXT NOT NULL,
  town TEXT NOT NULL,
  country TEXT NOT NULL DEFAULT 'United Kingdom',
  access_notes TEXT DEFAULT '',
  is_free BOOLEAN DEFAULT true,
  price_note TEXT DEFAULT '',
  open_hours JSONB DEFAULT NULL,
  photos JSONB DEFAULT '[]'::jsonb,
  -- Amenities
  is_accessible BOOLEAN DEFAULT false,
  is_disabled_access BOOLEAN DEFAULT false,
  has_baby_changing BOOLEAN DEFAULT false,
  has_family_room BOOLEAN DEFAULT false,
  is_gender_neutral BOOLEAN DEFAULT false,
  is_single_occupancy BOOLEAN DEFAULT false,
  is_24h BOOLEAN DEFAULT false,
  -- Notes
  notes TEXT DEFAULT '',
  access_codes TEXT DEFAULT '',
  submission_notes TEXT DEFAULT '',
  -- Metadata
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  reviewed_at TIMESTAMPTZ DEFAULT NULL,
  reviewed_by UUID REFERENCES auth.users(id) DEFAULT NULL,
  rejection_reason TEXT DEFAULT NULL
);

-- Index for moderation queue queries
CREATE INDEX IF NOT EXISTS idx_facility_submissions_status ON facility_submissions(status);
CREATE INDEX IF NOT EXISTS idx_facility_submissions_user ON facility_submissions(user_id);
CREATE INDEX IF NOT EXISTS idx_facility_submissions_created ON facility_submissions(created_at DESC);

-- RLS: Users can only see their own submissions
ALTER TABLE facility_submissions ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can insert their own submissions"
  ON facility_submissions FOR INSERT
  TO authenticated
  WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can view their own submissions"
  ON facility_submissions FOR SELECT
  TO authenticated
  USING (auth.uid() = user_id);

CREATE POLICY "Admins can view all submissions"
  ON facility_submissions FOR SELECT
  TO service_role
  USING (true);

CREATE POLICY "Admins can update submissions"
  ON facility_submissions FOR UPDATE
  TO service_role
  USING (true);

-- ────────────────────────────────────────
-- 2.2 — Photo Moderation Queue
-- ────────────────────────────────────────
CREATE TABLE IF NOT EXISTS photo_moderation (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  facility_id UUID NOT NULL REFERENCES facilities(id) ON DELETE CASCADE,
  user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
  url TEXT NOT NULL,
  thumbnail_url TEXT NOT NULL,
  status TEXT NOT NULL DEFAULT 'pending' CHECK (status IN ('pending', 'approved', 'rejected', 'reported')),
  exif_stripped BOOLEAN DEFAULT false,
  faces_blurred BOOLEAN DEFAULT false,
  reported_by UUID REFERENCES auth.users(id) DEFAULT NULL,
  report_reason TEXT DEFAULT NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_photo_moderation_status ON photo_moderation(status);
CREATE INDEX IF NOT EXISTS idx_photo_moderation_facility ON photo_moderation(facility_id);

ALTER TABLE photo_moderation ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can insert their own photos"
  ON photo_moderation FOR INSERT
  TO authenticated
  WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Anyone can view approved photos"
  ON photo_moderation FOR SELECT
  TO authenticated, anon
  USING (status = 'approved');

CREATE POLICY "Users can view their own pending photos"
  ON photo_moderation FOR SELECT
  TO authenticated
  USING (auth.uid() = user_id);

CREATE POLICY "Users can report photos"
  ON photo_moderation FOR UPDATE
  TO authenticated
  USING (true)
  WITH CHECK (status = 'reported');

-- ────────────────────────────────────────
-- 2.2 — Review Reports
-- ────────────────────────────────────────
CREATE TABLE IF NOT EXISTS review_reports (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  review_id UUID NOT NULL,
  user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
  reason TEXT NOT NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

ALTER TABLE review_reports ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can report reviews"
  ON review_reports FOR INSERT
  TO authenticated
  WITH CHECK (auth.uid() = user_id);

-- ────────────────────────────────────────
-- 2.3 — Temporary Reports (with expiry)
-- ────────────────────────────────────────
CREATE TABLE IF NOT EXISTS temporary_reports (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  facility_id UUID NOT NULL REFERENCES facilities(id) ON DELETE CASCADE,
  user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
  type TEXT NOT NULL CHECK (type IN ('out_of_order', 'no_water', 'cleaning', 'busy', 'closed', 'refurbishment')),
  notes TEXT DEFAULT '',
  expires_at TIMESTAMPTZ NOT NULL,
  is_expired BOOLEAN DEFAULT false,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_temporary_reports_facility ON temporary_reports(facility_id);
CREATE INDEX IF NOT EXISTS idx_temporary_reports_expires ON temporary_reports(expires_at);
CREATE INDEX IF NOT EXISTS idx_temporary_reports_active ON temporary_reports(facility_id, is_expired, expires_at);

ALTER TABLE temporary_reports ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Anyone can view active reports"
  ON temporary_reports FOR SELECT
  TO authenticated, anon
  USING (is_expired = false AND expires_at > now());

CREATE POLICY "Users can insert reports"
  ON temporary_reports FOR INSERT
  TO authenticated
  WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can resolve their own reports"
  ON temporary_reports FOR UPDATE
  TO authenticated
  USING (auth.uid() = user_id)
  WITH CHECK (is_expired = true);

-- ────────────────────────────────────────
-- 2.4 — Correction Requests (moderation queue)
-- ────────────────────────────────────────
CREATE TABLE IF NOT EXISTS correction_requests (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  facility_id UUID NOT NULL REFERENCES facilities(id) ON DELETE CASCADE,
  user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
  field TEXT NOT NULL,
  old_value TEXT NOT NULL DEFAULT '',
  new_value TEXT NOT NULL,
  notes TEXT DEFAULT '',
  status TEXT NOT NULL DEFAULT 'pending' CHECK (status IN ('pending', 'approved', 'rejected')),
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  reviewed_at TIMESTAMPTZ DEFAULT NULL,
  reviewed_by UUID REFERENCES auth.users(id) DEFAULT NULL
);

CREATE INDEX IF NOT EXISTS idx_correction_requests_status ON correction_requests(status);
CREATE INDEX IF NOT EXISTS idx_correction_requests_facility ON correction_requests(facility_id);

ALTER TABLE correction_requests ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can insert corrections"
  ON correction_requests FOR INSERT
  TO authenticated
  WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can view their own corrections"
  ON correction_requests FOR SELECT
  TO authenticated
  USING (auth.uid() = user_id);

-- ────────────────────────────────────────
-- 2.5 — Access Codes
-- ────────────────────────────────────────
CREATE TABLE IF NOT EXISTS access_codes (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  facility_id UUID NOT NULL REFERENCES facilities(id) ON DELETE CASCADE,
  user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
  code TEXT NOT NULL,
  description TEXT DEFAULT '',
  is_verified BOOLEAN DEFAULT false,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_access_codes_facility ON access_codes(facility_id);

ALTER TABLE access_codes ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Anyone can view access codes"
  ON access_codes FOR SELECT
  TO authenticated, anon
  USING (true);

CREATE POLICY "Users can insert access codes"
  ON access_codes FOR INSERT
  TO authenticated
  WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can update their own access codes"
  ON access_codes FOR UPDATE
  TO authenticated
  USING (auth.uid() = user_id);

-- ────────────────────────────────────────
-- 2.8 — Rate Limiting
-- ────────────────────────────────────────
CREATE TABLE IF NOT EXISTS rate_limits (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
  action TEXT NOT NULL,
  timestamp TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_rate_limits_lookup ON rate_limits(user_id, action, timestamp DESC);

ALTER TABLE rate_limits ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Service role manages rate limits"
  ON rate_limits FOR ALL
  TO service_role
  USING (true);

-- Allow the authenticated user to insert their own rate limit entries
CREATE POLICY "Users can insert their own rate limits"
  ON rate_limits FOR INSERT
  TO authenticated
  WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can read their own rate limits"
  ON rate_limits FOR SELECT
  TO authenticated
  USING (auth.uid() = user_id);

-- ────────────────────────────────────────
-- 2.7 — Report Expiry Automation (cron trigger)
-- This function is called by a Supabase cron job or Edge Function
-- to mark expired temporary reports.
-- ────────────────────────────────────────
CREATE OR REPLACE FUNCTION expire_temporary_reports()
RETURNS void
LANGUAGE plpgsql
SECURITY DEFINER
AS $$
BEGIN
  UPDATE temporary_reports
  SET is_expired = true
  WHERE is_expired = false
    AND expires_at < now();
END;
$$;

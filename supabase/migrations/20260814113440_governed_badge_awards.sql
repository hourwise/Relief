-- Relief Backend Batch 1: governed badge awards.
--
-- This migration is intentionally forward-only and has not been deployed.
-- It does not alter Apply 1A objects or create Storage resources.

ALTER TABLE public.user_badges
  ADD COLUMN IF NOT EXISTS source text NOT NULL DEFAULT '';

COMMENT ON COLUMN public.user_badges.source IS
  'Server-derived explanation for the badge award; never client-controlled.';

CREATE SCHEMA IF NOT EXISTS private;

REVOKE ALL ON SCHEMA private FROM PUBLIC, anon, authenticated, service_role;

CREATE OR REPLACE FUNCTION private.award_eligible_badges()
RETURNS trigger
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = pg_catalog, public
AS $$
DECLARE
  contributor_id uuid := NEW.user_id;
BEGIN
  -- This is a trigger-only function. It accepts no user or badge arguments;
  -- the contributor is taken from the row that passed the table's own RLS.
  IF contributor_id IS NULL THEN
    RETURN NEW;
  END IF;

  -- Serialize evaluation for one contributor. The unique constraint below
  -- makes the inserts idempotent as well as protecting against retries.
  PERFORM pg_advisory_xact_lock(
    pg_catalog.hashtextextended('relief.badges.' || contributor_id::text, 0)
  );

  -- Existing product condition: first facility submission.
  IF EXISTS (
    SELECT 1
    FROM public.facility_submissions
    WHERE user_id = contributor_id
  ) THEN
    INSERT INTO public.user_badges (user_id, badge_type, source)
    VALUES (contributor_id, 'explorer', 'Submitted your first facility')
    ON CONFLICT (user_id, badge_type) DO NOTHING;
  END IF;

  -- Existing product condition: five temporary reports.
  IF (
    SELECT count(*)
    FROM public.temporary_reports
    WHERE user_id = contributor_id
  ) >= 5 THEN
    INSERT INTO public.user_badges (user_id, badge_type, source)
    VALUES (contributor_id, 'community_hero', 'Submitted 5 reports')
    ON CONFLICT (user_id, badge_type) DO NOTHING;
  END IF;

  -- Existing product condition: three accessibility-related corrections.
  IF (
    SELECT count(*)
    FROM public.correction_requests
    WHERE user_id = contributor_id
      AND field IN (
        'is_accessible', 'is_disabled_access', 'has_wheelchair_access',
        'has_grab_rails', 'has_lift', 'has_adult_changing_place',
        'requires_radar_key'
      )
  ) >= 3 THEN
    INSERT INTO public.user_badges (user_id, badge_type, source)
    VALUES (contributor_id, 'accessibility_champion', 'Made 3 accessibility corrections')
    ON CONFLICT (user_id, badge_type) DO NOTHING;
  END IF;

  -- Existing product condition: three baby/family-related corrections.
  IF (
    SELECT count(*)
    FROM public.correction_requests
    WHERE user_id = contributor_id
      AND field IN (
        'has_baby_changing', 'has_family_room', 'has_baby_changing_inside',
        'has_separate_changing_room', 'has_family_toilet', 'has_pram_access'
      )
  ) >= 3 THEN
    INSERT INTO public.user_badges (user_id, badge_type, source)
    VALUES (contributor_id, 'family_helper', 'Made 3 family-related corrections')
    ON CONFLICT (user_id, badge_type) DO NOTHING;
  END IF;

  RETURN NEW;
END;
$$;

-- No client role can call the trigger function directly. The trigger owner
-- retains execution for the database-owned event path.
REVOKE ALL ON FUNCTION private.award_eligible_badges() FROM PUBLIC, anon, authenticated, service_role;
GRANT EXECUTE ON FUNCTION private.award_eligible_badges() TO postgres;

DROP TRIGGER IF EXISTS governed_badges_after_facility_submission
  ON public.facility_submissions;
CREATE TRIGGER governed_badges_after_facility_submission
  AFTER INSERT ON public.facility_submissions
  FOR EACH ROW
  EXECUTE FUNCTION private.award_eligible_badges();

DROP TRIGGER IF EXISTS governed_badges_after_temporary_report
  ON public.temporary_reports;
CREATE TRIGGER governed_badges_after_temporary_report
  AFTER INSERT ON public.temporary_reports
  FOR EACH ROW
  EXECUTE FUNCTION private.award_eligible_badges();

DROP TRIGGER IF EXISTS governed_badges_after_correction
  ON public.correction_requests;
CREATE TRIGGER governed_badges_after_correction
  AFTER INSERT ON public.correction_requests
  FOR EACH ROW
  EXECUTE FUNCTION private.award_eligible_badges();

-- Preserve public badge reads while removing direct write privileges from the
-- client roles. RLS remains enabled and the existing public SELECT policy is
-- unchanged.
REVOKE INSERT, UPDATE, DELETE, TRUNCATE, REFERENCES, TRIGGER
  ON public.user_badges FROM anon, authenticated;
GRANT SELECT ON public.user_badges TO anon, authenticated;

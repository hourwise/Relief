-- Disposable PostgreSQL regression assertions for
-- 20260814113440_governed_badge_awards.sql.
-- Run only after applying the migration to a local/disposable database.

DO $$
DECLARE
  function_definition text;
  trigger_count integer;
BEGIN
  SELECT pg_get_functiondef('private.award_eligible_badges()'::regprocedure)
    INTO function_definition;

  IF function_definition NOT LIKE '%SECURITY DEFINER%' THEN
    RAISE EXCEPTION 'badge function must be SECURITY DEFINER';
  END IF;
  IF function_definition NOT LIKE '%SET search_path = pg_catalog, public%' THEN
    RAISE EXCEPTION 'badge function search_path is not hardened';
  END IF;
  IF function_definition NOT LIKE '%ON CONFLICT (user_id, badge_type) DO NOTHING%' THEN
    RAISE EXCEPTION 'badge awards are not idempotent';
  END IF;
  IF function_definition LIKE '%p_user_id%' OR function_definition LIKE '%p_badge_type%' THEN
    RAISE EXCEPTION 'badge function must not accept caller-controlled identity or badge type';
  END IF;

  SELECT count(*)
    INTO trigger_count
    FROM pg_trigger
   WHERE tgname IN (
     'governed_badges_after_facility_submission',
     'governed_badges_after_temporary_report',
     'governed_badges_after_correction'
   )
     AND NOT tgisinternal;
  IF trigger_count <> 3 THEN
    RAISE EXCEPTION 'expected three governed badge triggers, found %', trigger_count;
  END IF;

  IF has_table_privilege('authenticated', 'public.user_badges', 'INSERT') THEN
    RAISE EXCEPTION 'authenticated must not be able to insert badges';
  END IF;
  IF has_function_privilege('authenticated', 'private.award_eligible_badges()', 'EXECUTE') THEN
    RAISE EXCEPTION 'authenticated must not execute the badge trigger function';
  END IF;
END
$$;

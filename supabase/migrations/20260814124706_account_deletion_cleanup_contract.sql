-- Relief account deletion: source-only contract for a separately approved
-- deployment. This function removes the authenticated user's current public
-- application rows, but it deliberately does not delete auth.users. The
-- trusted Edge Function performs Storage API cleanup first and Auth admin
-- deletion last.

create or replace function public.delete_my_account_data()
returns jsonb
language plpgsql
security definer
set search_path = ''
as $$
declare
  actor uuid := (select auth.uid());
  cleared_reviewed_by_references integer := 0;
  cleared_reported_by_references integer := 0;
  cleared_created_by_references integer := 0;
  affected_rows integer := 0;
  deleted_access_codes integer := 0;
  deleted_corrections integer := 0;
  deleted_facility_reports integer := 0;
  deleted_submissions integer := 0;
  deleted_favourites integer := 0;
  deleted_photo_moderation integer := 0;
  deleted_rate_limits integer := 0;
  deleted_review_reports integer := 0;
  deleted_saved_profiles integer := 0;
  deleted_subscription_events integer := 0;
  deleted_temporary_reports integer := 0;
  deleted_badges integer := 0;
  deleted_user_subscriptions integer := 0;
  deleted_user_profile integer := 0;
begin
  if actor is null then
    raise exception using
      errcode = '28000',
      message = 'Authenticated user required';
  end if;

  -- Preserve moderation/history rows while removing the deleted user's
  -- reviewer/reporter identity. These nullable references otherwise block
  -- deletion of auth.users because their foreign keys are NO ACTION.
  update public.correction_requests
     set reviewed_by = null
   where reviewed_by = actor;
  get diagnostics cleared_reviewed_by_references = row_count;

  update public.facility_submissions
     set reviewed_by = null
   where reviewed_by = actor;
  get diagnostics affected_rows = row_count;
  cleared_reviewed_by_references := cleared_reviewed_by_references + affected_rows;

  update public.photo_moderation
     set reported_by = null
   where reported_by = actor;
  get diagnostics cleared_reported_by_references = row_count;

  -- Keep canonical facilities, but remove the deleted user's attribution.
  update public.facilities
     set created_by = null
   where created_by = actor;
  get diagnostics cleared_created_by_references = row_count;

  -- Delete all current user-owned application data explicitly. The explicit
  -- deletes make the operation deterministic and returnable before the Auth
  -- admin deletion. Every statement is part of this function's transaction.
  delete from public.access_codes where user_id = actor;
  get diagnostics deleted_access_codes = row_count;

  delete from public.correction_requests where user_id = actor;
  get diagnostics deleted_corrections = row_count;

  delete from public.facility_reports where user_id = actor;
  get diagnostics deleted_facility_reports = row_count;

  delete from public.facility_submissions where user_id = actor;
  get diagnostics deleted_submissions = row_count;

  delete from public.favourites where user_id = actor;
  get diagnostics deleted_favourites = row_count;

  delete from public.photo_moderation where user_id = actor;
  get diagnostics deleted_photo_moderation = row_count;

  delete from public.rate_limits where user_id = actor;
  get diagnostics deleted_rate_limits = row_count;

  delete from public.review_reports where user_id = actor;
  get diagnostics deleted_review_reports = row_count;

  delete from public.saved_profiles where user_id = actor;
  get diagnostics deleted_saved_profiles = row_count;

  delete from public.subscription_events where user_id = actor;
  get diagnostics deleted_subscription_events = row_count;

  delete from public.temporary_reports where user_id = actor;
  get diagnostics deleted_temporary_reports = row_count;

  delete from public.user_badges where user_id = actor;
  get diagnostics deleted_badges = row_count;

  delete from public.user_subscriptions where user_id = actor;
  get diagnostics deleted_user_subscriptions = row_count;

  delete from public.user_profiles where id = actor;
  get diagnostics deleted_user_profile = row_count;

  return pg_catalog.jsonb_build_object(
    'contract_version', '20260814.1',
    'data_cleanup_completed', true,
    'auth_user_deleted', false,
    'cleared_reviewed_by_references', cleared_reviewed_by_references,
    'cleared_reported_by_references', cleared_reported_by_references,
    'cleared_created_by_references', cleared_created_by_references,
    'deleted_access_codes', deleted_access_codes,
    'deleted_corrections', deleted_corrections,
    'deleted_facility_reports', deleted_facility_reports,
    'deleted_submissions', deleted_submissions,
    'deleted_favourites', deleted_favourites,
    'deleted_photo_moderation', deleted_photo_moderation,
    'deleted_rate_limits', deleted_rate_limits,
    'deleted_review_reports', deleted_review_reports,
    'deleted_saved_profiles', deleted_saved_profiles,
    'deleted_subscription_events', deleted_subscription_events,
    'deleted_temporary_reports', deleted_temporary_reports,
    'deleted_badges', deleted_badges,
    'deleted_user_subscriptions', deleted_user_subscriptions,
    'deleted_user_profile', deleted_user_profile
  );
end;
$$;

revoke all on function public.delete_my_account_data() from public;
revoke execute on function public.delete_my_account_data() from anon;
grant execute on function public.delete_my_account_data() to authenticated;

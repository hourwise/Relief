begin;

-- Community-contract hardening only.  No canonical facility, badge, import,
-- subscription, or account-deletion objects are changed here.

-- Facility submissions: clients may create pending submissions using only the
-- contribution fields.  Moderation state and reviewer fields stay schema/
-- service controlled, with RLS providing a second boundary.
revoke insert, update, delete, truncate, trigger
  on table public.facility_submissions
  from anon, authenticated;
revoke insert (
  id, user_id, status, name, address, latitude, longitude, postcode, town,
  country, access_notes, is_free, price_note, open_hours, photos,
  is_accessible, is_disabled_access, has_baby_changing, has_family_room,
  is_gender_neutral, is_single_occupancy, is_24h, notes, access_codes,
  submission_notes, created_at, reviewed_at, reviewed_by, rejection_reason
), update (
  id, user_id, status, name, address, latitude, longitude, postcode, town,
  country, access_notes, is_free, price_note, open_hours, photos,
  is_accessible, is_disabled_access, has_baby_changing, has_family_room,
  is_gender_neutral, is_single_occupancy, is_24h, notes, access_codes,
  submission_notes, created_at, reviewed_at, reviewed_by, rejection_reason
)
  on table public.facility_submissions
  from anon, authenticated;
grant insert (
  user_id, name, address, latitude, longitude, postcode, town, country,
  access_notes, is_free, price_note, open_hours, photos, is_accessible,
  is_disabled_access, has_baby_changing, has_family_room, is_gender_neutral,
  is_single_occupancy, is_24h, notes, access_codes, submission_notes
)
  on table public.facility_submissions
  to authenticated;

drop policy if exists "Users can insert their own submissions"
  on public.facility_submissions;
create policy "Users can insert their own pending submissions"
  on public.facility_submissions
  for insert
  to authenticated
  with check (
    (select auth.uid()) = user_id
    and status = 'pending'
    and reviewed_at is null
    and reviewed_by is null
    and rejection_reason is null
  );

-- Corrections use the same pending-only, owner-derived boundary.
revoke insert, update, delete, truncate, trigger
  on table public.correction_requests
  from anon, authenticated;
revoke insert (
  id, facility_id, user_id, field, old_value, new_value, notes, status,
  created_at, reviewed_at, reviewed_by
), update (
  id, facility_id, user_id, field, old_value, new_value, notes, status,
  created_at, reviewed_at, reviewed_by
)
  on table public.correction_requests
  from anon, authenticated;
grant insert (facility_id, user_id, field, old_value, new_value, notes)
  on table public.correction_requests
  to authenticated;

drop policy if exists "Users can insert corrections"
  on public.correction_requests;
create policy "Users can insert their own pending corrections"
  on public.correction_requests
  for insert
  to authenticated
  with check (
    (select auth.uid()) = user_id
    and status = 'pending'
    and reviewed_at is null
    and reviewed_by is null
  );

-- Temporary reports: remove general client UPDATE privileges.  Resolution is
-- a single-purpose owner RPC so user_id, facility_id, type, notes and expiry
-- ownership cannot be reassigned through a table update.
revoke insert, update, delete, truncate, trigger
  on table public.temporary_reports
  from anon, authenticated;
revoke insert (
  id, facility_id, user_id, type, notes, expires_at, is_expired, created_at
), update (
  id, facility_id, user_id, type, notes, expires_at, is_expired, created_at
)
  on table public.temporary_reports
  from anon, authenticated;
grant insert (facility_id, user_id, type, notes, expires_at)
  on table public.temporary_reports
  to authenticated;

drop policy if exists "Users can resolve their own reports"
  on public.temporary_reports;

create or replace function public.resolve_own_temporary_report(
  p_report_id uuid
)
returns boolean
language plpgsql
security definer
set search_path = pg_catalog, public
as $function$
declare
  actor uuid := auth.uid();
begin
  if actor is null or p_report_id is null then
    return false;
  end if;

  update public.temporary_reports
  set is_expired = true,
      expires_at = pg_catalog.now()
  where id = p_report_id
    and user_id = actor
    and is_expired is distinct from true;

  if found then
    return true;
  end if;

  -- Idempotent for the same owner; another user's report remains false.
  return exists (
    select 1
    from public.temporary_reports
    where id = p_report_id
      and user_id = actor
      and is_expired = true
  );
end;
$function$;

revoke all on function public.resolve_own_temporary_report(uuid)
  from public, anon, authenticated, service_role;
grant execute on function public.resolve_own_temporary_report(uuid)
  to authenticated;

-- Access codes remain an authenticated community feature, but writes use a
-- narrow owner-derived RPC.  Direct table writes are removed so is_verified
-- cannot be client-controlled.
revoke insert, update, delete, truncate, trigger
  on table public.access_codes
  from anon, authenticated;
revoke insert (
  id, facility_id, user_id, code, description, is_verified, created_at,
  updated_at
), update (
  id, facility_id, user_id, code, description, is_verified, created_at,
  updated_at
)
  on table public.access_codes
  from anon, authenticated;

drop policy if exists "Users can insert access codes"
  on public.access_codes;
drop policy if exists "Users can update their own access codes"
  on public.access_codes;

create or replace function public.upsert_own_access_code(
  p_facility_id uuid,
  p_code text,
  p_description text default ''
)
returns uuid
language plpgsql
security definer
set search_path = pg_catalog, public
as $function$
declare
  actor uuid := auth.uid();
  existing_id uuid;
begin
  if actor is null then
    raise exception 'not authenticated' using errcode = '28000';
  end if;
  if p_facility_id is null or p_code is null or btrim(p_code) = '' then
    raise exception 'facility and access code are required' using errcode = '22023';
  end if;

  select id
    into existing_id
  from public.access_codes
  where facility_id = p_facility_id
    and user_id = actor
  order by created_at asc
  limit 1;

  if existing_id is not null then
    update public.access_codes
    set code = p_code,
        description = coalesce(p_description, ''),
        updated_at = pg_catalog.now()
    where id = existing_id
      and user_id = actor;
    return existing_id;
  end if;

  insert into public.access_codes (
    facility_id, user_id, code, description, is_verified
  ) values (
    p_facility_id, actor, p_code, coalesce(p_description, ''), false
  ) returning id into existing_id;

  return existing_id;
end;
$function$;

revoke all on function public.upsert_own_access_code(uuid, text, text)
  from public, anon, authenticated, service_role;
grant execute on function public.upsert_own_access_code(uuid, text, text)
  to authenticated;

commit;

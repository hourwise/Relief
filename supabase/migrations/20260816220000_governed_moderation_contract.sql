-- Relief governed moderation contract.
--
-- SOURCE-ONLY / PRODUCTION-GATED. Do not apply this migration without a
-- separate production approval that names the moderator operators and the
-- canonical-application policy.
--
-- This contract deliberately records moderation decisions without mutating
-- public.facilities. A future canonical-application migration must establish
-- provenance, duplicate detection, field validation, and rollback semantics
-- before any approved contribution can become canonical data.

begin;

create table if not exists public.relief_moderators (
  id uuid primary key default gen_random_uuid(),
  user_id uuid unique references auth.users(id) on delete set null,
  active boolean not null default true,
  created_at timestamptz not null default pg_catalog.now(),
  updated_at timestamptz not null default pg_catalog.now()
);

alter table public.relief_moderators enable row level security;
revoke all on table public.relief_moderators
  from public, anon, authenticated, service_role;

-- correction_requests currently has no rejection-reason field. Add the
-- narrow audit field locally so a rejected correction retains its rationale.
-- This remains absent from production until this source-only migration is
-- separately reviewed and deployed.
alter table public.correction_requests
  add column if not exists rejection_reason text;

create table if not exists public.access_code_verification_history (
  id uuid primary key default gen_random_uuid(),
  access_code_id uuid not null references public.access_codes(id) on delete cascade,
  moderator_id uuid references auth.users(id) on delete set null,
  action text not null check (action in ('verified', 'revoked')),
  created_at timestamptz not null default pg_catalog.now()
);

alter table public.access_code_verification_history enable row level security;
revoke all on table public.access_code_verification_history
  from public, anon, authenticated, service_role;

create index if not exists access_code_verification_history_code_created_idx
  on public.access_code_verification_history (access_code_id, created_at desc);

-- This private helper is the only place where moderator membership is read.
-- Membership is database state; auth user metadata, request payloads, hidden
-- routes and local flags are never consulted.
create or replace function private.relief_require_moderator()
returns uuid
language plpgsql
stable
security definer
set search_path = pg_catalog, public
as $function$
declare
  actor uuid := auth.uid();
begin
  if actor is null then
    raise exception 'Moderator authorization required' using errcode = '42501';
  end if;

  if not exists (
    select 1
    from public.relief_moderators
    where user_id = actor
      and active = true
  ) then
    raise exception 'Moderator authorization required' using errcode = '42501';
  end if;

  return actor;
end;
$function$;

revoke all on function private.relief_require_moderator()
  from public, anon, authenticated, service_role;

create or replace function public.list_moderation_facility_submissions()
returns setof public.facility_submissions
language plpgsql
security definer
set search_path = pg_catalog, public
as $function$
begin
  perform private.relief_require_moderator();

  return query
  select s.*
  from public.facility_submissions s
  where s.status = 'pending'
  order by s.created_at asc, s.id asc;
end;
$function$;

create or replace function public.moderate_facility_submission(
  p_submission_id uuid,
  p_decision text,
  p_rejection_reason text default null
)
returns public.facility_submissions
language plpgsql
security definer
set search_path = pg_catalog, public
as $function$
declare
  actor uuid := private.relief_require_moderator();
  current_submission public.facility_submissions;
begin
  if p_submission_id is null then
    raise exception 'Submission id is required' using errcode = '22023';
  end if;

  if p_decision not in ('approved', 'rejected') then
    raise exception 'Facility decision must be approved or rejected' using errcode = '22023';
  end if;

  if p_decision = 'rejected'
     and nullif(pg_catalog.btrim(coalesce(p_rejection_reason, '')), '') is null then
    raise exception 'A rejection reason is required' using errcode = '22023';
  end if;

  select s.*
    into current_submission
  from public.facility_submissions s
  where s.id = p_submission_id
  for update;

  if not found then
    raise exception 'Facility submission was not found' using errcode = 'P0002';
  end if;

  if current_submission.status <> 'pending' then
    raise exception 'Facility submission has already been reviewed' using errcode = '55000';
  end if;

  -- Approval is intentionally a moderation result only. No facilities row is
  -- inserted or updated by this function.
  update public.facility_submissions
     set status = p_decision,
         reviewed_at = pg_catalog.now(),
         reviewed_by = actor,
         rejection_reason = case
           when p_decision = 'rejected'
             then nullif(pg_catalog.btrim(p_rejection_reason), '')
           else null
         end
   where id = p_submission_id;

  select s.*
    into current_submission
  from public.facility_submissions s
  where s.id = p_submission_id;

  return current_submission;
end;
$function$;

create or replace function public.list_moderation_correction_requests()
returns setof public.correction_requests
language plpgsql
security definer
set search_path = pg_catalog, public
as $function$
begin
  perform private.relief_require_moderator();

  return query
  select c.*
  from public.correction_requests c
  where c.status = 'pending'
  order by c.created_at asc, c.id asc;
end;
$function$;

create or replace function public.moderate_correction_request(
  p_correction_id uuid,
  p_decision text,
  p_rejection_reason text default null
)
returns public.correction_requests
language plpgsql
security definer
set search_path = pg_catalog, public
as $function$
declare
  actor uuid := private.relief_require_moderator();
  current_correction public.correction_requests;
begin
  if p_correction_id is null then
    raise exception 'Correction id is required' using errcode = '22023';
  end if;

  if p_decision not in ('approved', 'rejected') then
    raise exception 'Correction decision must be approved or rejected' using errcode = '22023';
  end if;

  if p_decision = 'rejected'
     and nullif(pg_catalog.btrim(coalesce(p_rejection_reason, '')), '') is null then
    raise exception 'A rejection reason is required' using errcode = '22023';
  end if;

  select c.*
    into current_correction
  from public.correction_requests c
  where c.id = p_correction_id
  for update;

  if not found then
    raise exception 'Correction request was not found' using errcode = 'P0002';
  end if;

  if current_correction.status <> 'pending' then
    raise exception 'Correction request has already been reviewed' using errcode = '55000';
  end if;

  -- Corrections are reviewed records only. No arbitrary canonical column is
  -- interpreted or updated by this function.
  update public.correction_requests
     set status = p_decision,
         reviewed_at = pg_catalog.now(),
         reviewed_by = actor,
         rejection_reason = case
           when p_decision = 'rejected'
             then nullif(pg_catalog.btrim(p_rejection_reason), '')
           else null
         end
   where id = p_correction_id;

  select c.*
    into current_correction
  from public.correction_requests c
  where c.id = p_correction_id;

  return current_correction;
end;
$function$;

create or replace function public.list_moderation_access_codes()
returns setof public.access_codes
language plpgsql
security definer
set search_path = pg_catalog, public
as $function$
begin
  perform private.relief_require_moderator();

  return query
  select a.*
  from public.access_codes a
  where a.is_verified is distinct from true
  order by a.created_at asc, a.id asc;
end;
$function$;

create or replace function public.moderate_access_code(
  p_access_code_id uuid,
  p_decision text
)
returns public.access_codes
language plpgsql
security definer
set search_path = pg_catalog, public
as $function$
declare
  actor uuid := private.relief_require_moderator();
  current_code public.access_codes;
  next_verified boolean;
begin
  if p_access_code_id is null then
    raise exception 'Access-code id is required' using errcode = '22023';
  end if;

  if p_decision not in ('verify', 'revoke') then
    raise exception 'Access-code decision must be verify or revoke' using errcode = '22023';
  end if;

  next_verified := p_decision = 'verify';

  select a.*
    into current_code
  from public.access_codes a
  where a.id = p_access_code_id
  for update;

  if not found then
    raise exception 'Access code was not found' using errcode = 'P0002';
  end if;

  -- Replaying the same decision is safe and does not manufacture history.
  if current_code.is_verified is not distinct from next_verified then
    return current_code;
  end if;

  update public.access_codes
     set is_verified = next_verified,
         updated_at = pg_catalog.now()
   where id = p_access_code_id;

  insert into public.access_code_verification_history (
    access_code_id, moderator_id, action
  ) values (
    p_access_code_id, actor,
    case when next_verified then 'verified' else 'revoked' end
  );

  select a.*
    into current_code
  from public.access_codes a
  where a.id = p_access_code_id;

  return current_code;
end;
$function$;

-- The public RPCs are callable by the authenticated role only so an ordinary
-- user receives a server-side authorization failure; the function itself
-- remains the authority. No anon or service-role execute path is created.
revoke all on function public.list_moderation_facility_submissions()
  from public, anon, authenticated, service_role;
revoke all on function public.moderate_facility_submission(uuid, text, text)
  from public, anon, authenticated, service_role;
revoke all on function public.list_moderation_correction_requests()
  from public, anon, authenticated, service_role;
revoke all on function public.moderate_correction_request(uuid, text, text)
  from public, anon, authenticated, service_role;
revoke all on function public.list_moderation_access_codes()
  from public, anon, authenticated, service_role;
revoke all on function public.moderate_access_code(uuid, text)
  from public, anon, authenticated, service_role;

grant execute on function public.list_moderation_facility_submissions()
  to authenticated;
grant execute on function public.moderate_facility_submission(uuid, text, text)
  to authenticated;
grant execute on function public.list_moderation_correction_requests()
  to authenticated;
grant execute on function public.moderate_correction_request(uuid, text, text)
  to authenticated;
grant execute on function public.list_moderation_access_codes()
  to authenticated;
grant execute on function public.moderate_access_code(uuid, text)
  to authenticated;

commit;

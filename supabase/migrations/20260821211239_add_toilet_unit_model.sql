-- Relief — additive multi-toilet facility model
-- PROPOSED / NOT DEPLOYED IN THIS BATCH.
--
-- This migration creates optional child/source capability only. It does not
-- backfill existing facilities, create synthetic units, create import runs,
-- write staging rows, or promote any TfL INSERT/SOURCE_LINK/ENRICHMENT.
-- Existing facilities remain valid with zero explicit toilet_units.

create table public.toilet_units (
  id uuid default gen_random_uuid() not null,
  facility_id uuid not null,
  unit_label text,
  unit_type text default 'unknown'::text not null,
  identity_status text default 'UNRESOLVED'::text not null,
  is_accessible boolean,
  has_baby_changing boolean,
  is_free boolean,
  price_note text,
  open_hours jsonb,
  is_24h boolean,
  is_inside_gateline boolean,
  location_description text,
  access_notes text,
  requires_radar_key boolean,
  ask_staff boolean,
  latitude double precision,
  longitude double precision,
  coordinate_precision text default 'UNKNOWN'::text not null,
  publication_status text default 'hidden'::text not null,
  verification_status text default 'source_imported'::text not null,
  last_verified_at timestamp with time zone,
  created_at timestamp with time zone default now() not null,
  updated_at timestamp with time zone default now() not null,
  created_by uuid,
  field_provenance jsonb default '{}'::jsonb not null,
  constraint toilet_units_pkey primary key (id),
  constraint toilet_units_unit_type_check check (unit_type = any (array[
    'male'::text, 'female'::text, 'unisex'::text, 'other'::text, 'unknown'::text
  ])),
  constraint toilet_units_identity_status_check check (identity_status = any (array[
    'CONFIRMED_DISTINCT_UNIT'::text,
    'LIKELY_DISTINCT_UNIT'::text,
    'SOURCE_DISTINCT_PHYSICAL_UNKNOWN'::text,
    'SAME_UNIT_MULTI_SOURCE'::text,
    'UNRESOLVED'::text
  ])),
  constraint toilet_units_coordinate_precision_check check (
    (coordinate_precision = 'UNKNOWN'::text and latitude is null and longitude is null)
    or
    (coordinate_precision = 'TOILET_LEVEL'::text and latitude is not null and longitude is not null)
  ),
  constraint toilet_units_latitude_check check (latitude is null or (latitude >= (-90)::double precision and latitude <= (90)::double precision)),
  constraint toilet_units_longitude_check check (longitude is null or (longitude >= (-180)::double precision and longitude <= (180)::double precision)),
  constraint toilet_units_publication_status_check check (publication_status = any (array[
    'published'::text, 'hidden'::text, 'under_review'::text, 'removed'::text
  ])),
  constraint toilet_units_published_identity_check check (
    publication_status <> 'published'::text
    or identity_status = any (array[
      'CONFIRMED_DISTINCT_UNIT'::text,
      'LIKELY_DISTINCT_UNIT'::text,
      'SAME_UNIT_MULTI_SOURCE'::text
    ])
  ),
  constraint toilet_units_verification_status_check check (verification_status = any (array[
    'source_imported'::text,
    'source_verified'::text,
    'community_confirmed'::text,
    'staff_verified'::text,
    'disputed'::text,
    'stale'::text
  ])),
  constraint toilet_units_facility_id_fkey foreign key (facility_id)
    references public.facilities(id) on delete cascade
);

comment on table public.toilet_units is
  'Optional explicit toilet/provision units under a facility. Zero rows means unit detail is unknown, not exactly one toilet.';
comment on column public.toilet_units.identity_status is
  'Physical-unit adjudication status; a source row identity is not automatically a physical-unit identity.';
comment on column public.toilet_units.coordinate_precision is
  'Child coordinates are absent unless independently supported at toilet level. Parent station coordinates are not copied here.';

create table public.toilet_unit_sources (
  id uuid default gen_random_uuid() not null,
  toilet_unit_id uuid not null,
  import_run_id uuid,
  source_name text not null,
  source_record_id text not null,
  source_url text,
  source_licence text not null,
  source_updated_at timestamp with time zone,
  first_seen_at timestamp with time zone default now() not null,
  last_seen_at timestamp with time zone default now() not null,
  is_current boolean default true not null,
  raw_data jsonb,
  created_at timestamp with time zone default now() not null,
  updated_at timestamp with time zone default now() not null,
  constraint toilet_unit_sources_pkey primary key (id),
  constraint toilet_unit_sources_source_name_source_record_id_key unique (source_name, source_record_id),
  constraint toilet_unit_sources_toilet_unit_id_fkey foreign key (toilet_unit_id)
    references public.toilet_units(id) on delete cascade,
  constraint toilet_unit_sources_import_run_id_fkey foreign key (import_run_id)
    references public.import_runs(id)
);

comment on table public.toilet_unit_sources is
  'Provider assertions attached to an adjudicated toilet unit. Unresolved source rows remain source evidence until a unit relationship is known.';
comment on column public.toilet_unit_sources.source_record_id is
  'Provider-stable identity; for TfL use tfl:{StationUniqueId}:toilet:{Id}.';

create index idx_toilet_units_facility
  on public.toilet_units using btree (facility_id);

create index idx_toilet_units_published_facility
  on public.toilet_units using btree (facility_id, publication_status)
  where publication_status = 'published'::text;

create index idx_toilet_units_accessibility
  on public.toilet_units using btree (facility_id, is_accessible)
  where is_accessible is true;

create index idx_toilet_units_baby_changing
  on public.toilet_units using btree (facility_id, has_baby_changing)
  where has_baby_changing is true;

create index idx_toilet_unit_sources_unit
  on public.toilet_unit_sources using btree (toilet_unit_id);

create index idx_toilet_unit_sources_current
  on public.toilet_unit_sources using btree (source_name, is_current);

create trigger set_toilet_units_updated_at
  before update on public.toilet_units
  for each row execute function public.update_updated_at();

create trigger set_toilet_unit_sources_updated_at
  before update on public.toilet_unit_sources
  for each row execute function public.update_updated_at();

alter table public.toilet_units enable row level security;
alter table public.toilet_unit_sources enable row level security;

create policy "Published toilet units are viewable"
  on public.toilet_units for select
  to anon, authenticated
  using (
    publication_status = 'published'::text
    and exists (
      select 1
      from public.facilities f
      where f.id = toilet_units.facility_id
        and f.publication_status = 'published'::text
    )
  );

create policy "Published toilet unit sources are viewable"
  on public.toilet_unit_sources for select
  to anon, authenticated
  using (
    exists (
      select 1
      from public.toilet_units tu
      join public.facilities f on f.id = tu.facility_id
      where tu.id = toilet_unit_sources.toilet_unit_id
        and tu.publication_status = 'published'::text
        and f.publication_status = 'published'::text
    )
  );

-- New public-schema tables are not assumed to be Data API exposed. Grant only
-- public reads; RLS above still controls which rows are visible. Source/unit
-- writes are reserved for the governed import boundary.
grant select on table public.toilet_units, public.toilet_unit_sources to anon, authenticated;
grant all on table public.toilet_units, public.toilet_unit_sources to service_role;

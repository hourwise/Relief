-- Relief — facility-level source observations
--
-- ADDITIVE / LOCAL-VALIDATION ONLY for the TfL source-observation model.
-- This migration does not backfill facility_sources, create observations,
-- create toilet units, alter canonical facilities, or provide an apply path.
-- Production deployment is not authorized by this transaction.

create table public.facility_source_observations (
  id uuid default gen_random_uuid() not null,
  facility_source_id uuid not null,
  observation_key text not null,
  observation_kind text default 'TOILET_PROVISION'::text not null,
  observed_attributes jsonb default '{}'::jsonb not null,
  coordinate_scope text default 'NONE'::text not null,
  physical_unit_asserted boolean default false not null,
  toilet_unit_id uuid,
  unit_link_status text default 'UNLINKED'::text not null,
  source_schema_version text,
  first_seen_at timestamp with time zone default now() not null,
  last_seen_at timestamp with time zone default now() not null,
  is_current boolean default true not null,
  created_at timestamp with time zone default now() not null,
  updated_at timestamp with time zone default now() not null,
  constraint facility_source_observations_pkey primary key (id),
  constraint facility_source_observations_identity_key
    unique (facility_source_id, observation_key),
  constraint facility_source_observations_facility_source_id_fkey
    foreign key (facility_source_id)
    references public.facility_sources(id)
    on delete cascade,
  constraint facility_source_observations_toilet_unit_id_fkey
    foreign key (toilet_unit_id)
    references public.toilet_units(id)
    on delete restrict,
  constraint facility_source_observations_observation_key_check
    check (length(btrim(observation_key)) > 0),
  constraint facility_source_observations_observation_kind_check
    check (length(btrim(observation_kind)) > 0),
  constraint facility_source_observations_coordinate_scope_check
    check (coordinate_scope = any (array[
      'NONE'::text,
      'FACILITY_LEVEL'::text,
      'STATION_LEVEL'::text,
      'TOILET_LEVEL'::text
    ])),
  constraint facility_source_observations_unit_link_status_check
    check (unit_link_status = any (array[
      'UNLINKED'::text,
      'UNRESOLVED'::text,
      'CONFIRMED_DISTINCT_UNIT'::text,
      'SAME_UNIT_MULTI_SOURCE'::text
    ])),
  constraint facility_source_observations_physical_semantics_check
    check (
      (
        physical_unit_asserted = false
        and toilet_unit_id is null
        and unit_link_status = 'UNLINKED'::text
      )
      or
      (
        physical_unit_asserted = true
        and toilet_unit_id is not null
        and unit_link_status = any (array[
          'CONFIRMED_DISTINCT_UNIT'::text,
          'SAME_UNIT_MULTI_SOURCE'::text
        ])
      )
    ),
  constraint facility_source_observations_coordinate_semantics_check
    check (
      coordinate_scope <> 'TOILET_LEVEL'::text
      or (
        physical_unit_asserted = true
        and toilet_unit_id is not null
      )
    )
);

comment on table public.facility_source_observations is
  'Structured source evidence attached to facility provenance. An observation is not a physical toilet unit unless a separately governed adjudication establishes and records that relationship.';
comment on column public.facility_source_observations.observation_key is
  'Deterministic source-observation identity within one facility_sources row; for TfL use tfl:{StationUniqueId}:toilet:{Id}.';
comment on column public.facility_source_observations.observed_attributes is
  'Source-specific attributes retained as evidence; these values do not overwrite canonical facilities fields.';
comment on column public.facility_source_observations.coordinate_scope is
  'Semantic scope of coordinates in observed_attributes. TfL station coordinates use STATION_LEVEL, never TOILET_LEVEL.';
comment on column public.facility_source_observations.physical_unit_asserted is
  'False for an unadjudicated source observation. It may become true only together with a governed toilet_unit link and an allowed unit_link_status.';
comment on column public.facility_source_observations.toilet_unit_id is
  'Optional future link to an independently adjudicated physical unit; source identity and observed evidence remain unchanged.';

create index idx_facility_source_observations_source
  on public.facility_source_observations using btree (facility_source_id);

create index idx_facility_source_observations_current
  on public.facility_source_observations using btree (facility_source_id, is_current);

create index idx_facility_source_observations_unit
  on public.facility_source_observations using btree (toilet_unit_id)
  where toilet_unit_id is not null;

create trigger set_facility_source_observations_updated_at
  before update on public.facility_source_observations
  for each row execute function public.update_updated_at();

alter table public.facility_source_observations enable row level security;

-- This is governed provenance, not a public application data contract. With
-- no policies and no Data API grants, anon/authenticated cannot read or write.
revoke all on table public.facility_source_observations from public, anon, authenticated;
grant all on table public.facility_source_observations to service_role;

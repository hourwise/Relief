-- Relief — NaPTAN N4A transport source graph schema
-- CANDIDATE / NOT DEPLOYED / NO DATA INGESTION
--
-- This migration preserves publisher-scoped snapshot facts only. It does not
-- insert NaPTAN rows, create canonical facilities, create source links,
-- create observations, or expose a public API. N3 normalized complexes remain
-- a deterministic projection over these facts; they are not DfT facts and do
-- not receive a table in this migration.

create table public.transport_source_snapshots (
  id uuid default gen_random_uuid() not null,
  source_namespace text not null,
  product_name text not null,
  source_snapshot_key text not null,
  source_url text not null,
  source_checksum_sha256 text not null,
  source_byte_size bigint not null,
  retrieved_at timestamp with time zone not null,
  source_published_at timestamp with time zone,
  source_revision text,
  licence text not null,
  attribution text not null,
  parser_version text not null,
  source_schema_version text,
  ingestion_state text default 'CAPTURED'::text not null,
  row_counts jsonb default '{}'::jsonb not null,
  error_summary text,
  created_at timestamp with time zone default now() not null,
  updated_at timestamp with time zone default now() not null,
  constraint transport_source_snapshots_pkey primary key (id),
  constraint transport_source_snapshots_snapshot_key_key unique (source_snapshot_key),
  constraint transport_source_snapshots_namespace_checksum_key unique (source_namespace, source_checksum_sha256),
  constraint transport_source_snapshots_namespace_check check (length(btrim(source_namespace)) > 0),
  constraint transport_source_snapshots_product_check check (length(btrim(product_name)) > 0),
  constraint transport_source_snapshots_snapshot_key_check check (length(btrim(source_snapshot_key)) > 0),
  constraint transport_source_snapshots_url_check check (length(btrim(source_url)) > 0),
  constraint transport_source_snapshots_checksum_check check (source_checksum_sha256 ~ '^[0-9a-fA-F]{64}$'::text),
  constraint transport_source_snapshots_size_check check (source_byte_size >= 0),
  constraint transport_source_snapshots_licence_check check (length(btrim(licence)) > 0),
  constraint transport_source_snapshots_attribution_check check (length(btrim(attribution)) > 0),
  constraint transport_source_snapshots_parser_check check (length(btrim(parser_version)) > 0),
  constraint transport_source_snapshots_state_check check (ingestion_state = any (array[
    'CAPTURED'::text,
    'VALIDATING'::text,
    'VALIDATED'::text,
    'INGESTED'::text,
    'FAILED'::text,
    'SUPERSEDED'::text
  ])),
  constraint transport_source_snapshots_counts_object_check check (jsonb_typeof(row_counts) = 'object'::text)
);

comment on table public.transport_source_snapshots is
  'Immutable source-capture identity and governed lifecycle metadata. One exact source checksum is one replayable snapshot; this is not the Toilet Map import_runs contract.';
comment on column public.transport_source_snapshots.source_snapshot_key is
  'Relief-derived idempotency key, normally <source_namespace>:sha256:<source_checksum_sha256>; it is not a publisher identity.';
comment on column public.transport_source_snapshots.ingestion_state is
  'Lifecycle of the governed source snapshot. Historical snapshots are retained; a newer snapshot does not overwrite prior source facts.';

create table public.transport_source_places (
  id uuid default gen_random_uuid() not null,
  snapshot_id uuid not null,
  publisher_identity text not null,
  publisher_id text not null,
  place_kind text default 'STOP_AREA'::text not null,
  display_name text not null,
  normalized_name text default ''::text not null,
  source_type text,
  administrative_area_code text,
  source_status text,
  source_modification text,
  publisher_latitude double precision,
  publisher_longitude double precision,
  publisher_location public.geography(Point,4326) generated always as (
    case
      when publisher_latitude is not null and publisher_longitude is not null
      then public.st_setsrid(public.st_makepoint(publisher_longitude, publisher_latitude), 4326)::public.geography
      else null::public.geography
    end
  ) stored,
  coordinate_scope text default 'NONE'::text not null,
  source_attributes jsonb default '{}'::jsonb not null,
  created_at timestamp with time zone default now() not null,
  updated_at timestamp with time zone default now() not null,
  constraint transport_source_places_pkey primary key (id),
  constraint transport_source_places_snapshot_id_id_key unique (snapshot_id, id),
  constraint transport_source_places_identity_key unique (snapshot_id, publisher_identity),
  constraint transport_source_places_snapshot_id_fkey foreign key (snapshot_id)
    references public.transport_source_snapshots(id) on delete restrict,
  constraint transport_source_places_identity_check check (length(btrim(publisher_identity)) > 0),
  constraint transport_source_places_publisher_id_check check (length(btrim(publisher_id)) > 0),
  constraint transport_source_places_kind_check check (place_kind = any (array['STOP_AREA'::text])),
  constraint transport_source_places_coordinate_scope_check check (coordinate_scope = any (array[
    'NONE'::text,
    'STOP_AREA_LEVEL'::text
  ])),
  constraint transport_source_places_coordinate_pair_check check (
    (coordinate_scope = 'NONE'::text and publisher_latitude is null and publisher_longitude is null)
    or
    (coordinate_scope = 'STOP_AREA_LEVEL'::text and publisher_latitude is not null and publisher_longitude is not null)
  ),
  constraint transport_source_places_latitude_check check (publisher_latitude is null or publisher_latitude between -90 and 90),
  constraint transport_source_places_longitude_check check (publisher_longitude is null or publisher_longitude between -180 and 180),
  constraint transport_source_places_attributes_object_check check (jsonb_typeof(source_attributes) = 'object'::text)
);

comment on table public.transport_source_places is
  'Snapshot-scoped publisher StopArea facts. A place row is not a normalized Relief transport complex or canonical facility.';
comment on column public.transport_source_places.publisher_identity is
  'Stable publisher identity, for NaPTAN normally naptan-stop-area:<StopAreaCode>; uniqueness is scoped to one exact snapshot.';
comment on column public.transport_source_places.coordinate_scope is
  'Publisher geometry only. Relief-derived child/member centroids are not stored as publisher coordinates in this table.';

create table public.transport_source_nodes (
  id uuid default gen_random_uuid() not null,
  snapshot_id uuid not null,
  publisher_identity text not null,
  publisher_id text not null,
  source_stop_type text default ''::text not null,
  normalized_mode text,
  display_name text default ''::text not null,
  normalized_name text default ''::text not null,
  source_status text,
  source_modification text,
  publisher_latitude double precision,
  publisher_longitude double precision,
  publisher_location public.geography(Point,4326) generated always as (
    case
      when publisher_latitude is not null and publisher_longitude is not null
      then public.st_setsrid(public.st_makepoint(publisher_longitude, publisher_latitude), 4326)::public.geography
      else null::public.geography
    end
  ) stored,
  coordinate_scope text default 'NONE'::text not null,
  source_attributes jsonb default '{}'::jsonb not null,
  created_at timestamp with time zone default now() not null,
  updated_at timestamp with time zone default now() not null,
  constraint transport_source_nodes_pkey primary key (id),
  constraint transport_source_nodes_snapshot_id_id_key unique (snapshot_id, id),
  constraint transport_source_nodes_identity_key unique (snapshot_id, publisher_identity),
  constraint transport_source_nodes_snapshot_id_fkey foreign key (snapshot_id)
    references public.transport_source_snapshots(id) on delete restrict,
  constraint transport_source_nodes_identity_check check (length(btrim(publisher_identity)) > 0),
  constraint transport_source_nodes_publisher_id_check check (length(btrim(publisher_id)) > 0),
  constraint transport_source_nodes_coordinate_scope_check check (coordinate_scope = any (array[
    'NONE'::text,
    'TRANSPORT_STOP_LEVEL'::text
  ])),
  constraint transport_source_nodes_coordinate_pair_check check (
    (coordinate_scope = 'NONE'::text and publisher_latitude is null and publisher_longitude is null)
    or
    (coordinate_scope = 'TRANSPORT_STOP_LEVEL'::text and publisher_latitude is not null and publisher_longitude is not null)
  ),
  constraint transport_source_nodes_latitude_check check (publisher_latitude is null or publisher_latitude between -90 and 90),
  constraint transport_source_nodes_longitude_check check (publisher_longitude is null or publisher_longitude between -180 and 180),
  constraint transport_source_nodes_attributes_object_check check (jsonb_typeof(source_attributes) = 'object'::text)
);

comment on table public.transport_source_nodes is
  'Snapshot-scoped publisher StopPoint/access-node facts. Nodes remain source evidence and are not Relief facilities.';
comment on column public.transport_source_nodes.normalized_mode is
  'Relief-derived mode classification from structured source StopType; source_stop_type remains the publisher value.';
comment on column public.transport_source_nodes.coordinate_scope is
  'Publisher transport-node geometry only; it is never toilet geometry.';

create table public.transport_source_memberships (
  id uuid default gen_random_uuid() not null,
  snapshot_id uuid not null,
  node_id uuid,
  place_id uuid,
  publisher_node_identity text not null,
  publisher_place_identity text not null,
  membership_key text not null,
  resolution_status text default 'RESOLVED'::text not null,
  duplicate_occurrence_count integer default 1 not null,
  source_attributes jsonb default '{}'::jsonb not null,
  created_at timestamp with time zone default now() not null,
  updated_at timestamp with time zone default now() not null,
  constraint transport_source_memberships_pkey primary key (id),
  constraint transport_source_memberships_snapshot_key unique (snapshot_id, membership_key),
  constraint transport_source_memberships_snapshot_id_fkey foreign key (snapshot_id)
    references public.transport_source_snapshots(id) on delete restrict,
  constraint transport_source_memberships_node_fkey foreign key (snapshot_id, node_id)
    references public.transport_source_nodes(snapshot_id, id) on delete restrict,
  constraint transport_source_memberships_place_fkey foreign key (snapshot_id, place_id)
    references public.transport_source_places(snapshot_id, id) on delete restrict,
  constraint transport_source_memberships_node_identity_check check (length(btrim(publisher_node_identity)) > 0),
  constraint transport_source_memberships_place_identity_check check (length(btrim(publisher_place_identity)) > 0),
  constraint transport_source_memberships_key_check check (length(btrim(membership_key)) > 0),
  constraint transport_source_memberships_resolution_check check (resolution_status = any (array[
    'RESOLVED'::text,
    'UNRESOLVED_MISSING_NODE'::text,
    'UNRESOLVED_MISSING_PLACE'::text,
    'INVALID'::text
  ])),
  constraint transport_source_memberships_resolution_consistency_check check (
    (resolution_status = 'RESOLVED'::text and node_id is not null and place_id is not null)
    or
    (resolution_status = 'UNRESOLVED_MISSING_NODE'::text and node_id is null)
    or
    (resolution_status = 'UNRESOLVED_MISSING_PLACE'::text and place_id is null)
    or
    (resolution_status = 'INVALID'::text)
  ),
  constraint transport_source_memberships_duplicate_count_check check (duplicate_occurrence_count > 0),
  constraint transport_source_memberships_attributes_object_check check (jsonb_typeof(source_attributes) = 'object'::text)
);

comment on table public.transport_source_memberships is
  'Every publisher-declared StopPoint-to-StopArea membership, including multi-parent membership. Exact duplicate elements are coalesced with duplicate_occurrence_count.';
comment on column public.transport_source_memberships.membership_key is
  'Deterministic source key derived from publisher node and place identities; row order is never part of identity.';
comment on column public.transport_source_memberships.place_id is
  'Nullable only for unresolved publisher references; a missing StopArea is never fabricated to satisfy the FK.';

create table public.transport_source_place_parents (
  id uuid default gen_random_uuid() not null,
  snapshot_id uuid not null,
  child_place_id uuid,
  parent_place_id uuid,
  publisher_child_identity text not null,
  publisher_parent_identity text not null,
  parent_edge_key text not null,
  resolution_status text default 'RESOLVED'::text not null,
  duplicate_occurrence_count integer default 1 not null,
  source_attributes jsonb default '{}'::jsonb not null,
  created_at timestamp with time zone default now() not null,
  updated_at timestamp with time zone default now() not null,
  constraint transport_source_place_parents_pkey primary key (id),
  constraint transport_source_place_parents_snapshot_key unique (snapshot_id, parent_edge_key),
  constraint transport_source_place_parents_snapshot_id_fkey foreign key (snapshot_id)
    references public.transport_source_snapshots(id) on delete restrict,
  constraint transport_source_place_parents_child_fkey foreign key (snapshot_id, child_place_id)
    references public.transport_source_places(snapshot_id, id) on delete restrict,
  constraint transport_source_place_parents_parent_fkey foreign key (snapshot_id, parent_place_id)
    references public.transport_source_places(snapshot_id, id) on delete restrict,
  constraint transport_source_place_parents_child_identity_check check (length(btrim(publisher_child_identity)) > 0),
  constraint transport_source_place_parents_parent_identity_check check (length(btrim(publisher_parent_identity)) > 0),
  constraint transport_source_place_parents_key_check check (length(btrim(parent_edge_key)) > 0),
  constraint transport_source_place_parents_resolution_check check (resolution_status = any (array[
    'RESOLVED'::text,
    'UNRESOLVED_MISSING_CHILD'::text,
    'UNRESOLVED_MISSING_PARENT'::text,
    'INVALID'::text
  ])),
  constraint transport_source_place_parents_resolution_consistency_check check (
    (resolution_status = 'RESOLVED'::text and child_place_id is not null and parent_place_id is not null)
    or
    (resolution_status = 'UNRESOLVED_MISSING_CHILD'::text and child_place_id is null)
    or
    (resolution_status = 'UNRESOLVED_MISSING_PARENT'::text and parent_place_id is null)
    or
    (resolution_status = 'INVALID'::text)
  ),
  constraint transport_source_place_parents_duplicate_count_check check (duplicate_occurrence_count > 0),
  constraint transport_source_place_parents_attributes_object_check check (jsonb_typeof(source_attributes) = 'object'::text)
);

comment on table public.transport_source_place_parents is
  'Publisher StopArea parent edges. Parent chains are preserved without a depth limit; cycles are rejected/quarantined by the governed graph validator before a snapshot is marked VALIDATED.';
comment on column public.transport_source_place_parents.parent_place_id is
  'Nullable for unresolved parent references; no placeholder parent row is created.';

create index idx_transport_source_snapshots_namespace_state
  on public.transport_source_snapshots using btree (source_namespace, ingestion_state, retrieved_at desc);
create index idx_transport_source_places_snapshot_name
  on public.transport_source_places using btree (snapshot_id, normalized_name);
create index idx_transport_source_places_status
  on public.transport_source_places using btree (snapshot_id, source_status);
create index idx_transport_source_places_location
  on public.transport_source_places using gist (publisher_location)
  where publisher_location is not null;
create index idx_transport_source_nodes_snapshot_type
  on public.transport_source_nodes using btree (snapshot_id, source_stop_type);
create index idx_transport_source_nodes_mode
  on public.transport_source_nodes using btree (snapshot_id, normalized_mode);
create index idx_transport_source_nodes_status
  on public.transport_source_nodes using btree (snapshot_id, source_status);
create index idx_transport_source_nodes_location
  on public.transport_source_nodes using gist (publisher_location)
  where publisher_location is not null;
create index idx_transport_source_memberships_place
  on public.transport_source_memberships using btree (snapshot_id, place_id);
create index idx_transport_source_memberships_node
  on public.transport_source_memberships using btree (snapshot_id, node_id);
create index idx_transport_source_memberships_unresolved
  on public.transport_source_memberships using btree (snapshot_id, resolution_status)
  where resolution_status <> 'RESOLVED'::text;
create index idx_transport_source_place_parents_child
  on public.transport_source_place_parents using btree (snapshot_id, child_place_id);
create index idx_transport_source_place_parents_parent
  on public.transport_source_place_parents using btree (snapshot_id, parent_place_id);
create index idx_transport_source_place_parents_unresolved
  on public.transport_source_place_parents using btree (snapshot_id, resolution_status)
  where resolution_status <> 'RESOLVED'::text;

create trigger set_transport_source_snapshots_updated_at
  before update on public.transport_source_snapshots
  for each row execute function public.update_updated_at();
create trigger set_transport_source_places_updated_at
  before update on public.transport_source_places
  for each row execute function public.update_updated_at();
create trigger set_transport_source_nodes_updated_at
  before update on public.transport_source_nodes
  for each row execute function public.update_updated_at();
create trigger set_transport_source_memberships_updated_at
  before update on public.transport_source_memberships
  for each row execute function public.update_updated_at();
create trigger set_transport_source_place_parents_updated_at
  before update on public.transport_source_place_parents
  for each row execute function public.update_updated_at();

alter table public.transport_source_snapshots enable row level security;
alter table public.transport_source_places enable row level security;
alter table public.transport_source_nodes enable row level security;
alter table public.transport_source_memberships enable row level security;
alter table public.transport_source_place_parents enable row level security;

revoke all on table public.transport_source_snapshots, public.transport_source_places,
  public.transport_source_nodes, public.transport_source_memberships,
  public.transport_source_place_parents from public, anon, authenticated;
grant all on table public.transport_source_snapshots, public.transport_source_places,
  public.transport_source_nodes, public.transport_source_memberships,
  public.transport_source_place_parents to service_role;

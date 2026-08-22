\set ON_ERROR_STOP on

-- N4B disposable-only live assertions. This file must never be pointed at
-- production. It uses synthetic fixtures and leaves no committed source data.

begin;

do $$
declare
  missing_tables text[];
  missing_indexes text[];
  table_name text;
begin
  select array_agg(expected order by expected)
  into missing_tables
  from unnest(array[
    'transport_source_snapshots',
    'transport_source_places',
    'transport_source_nodes',
    'transport_source_memberships',
    'transport_source_place_parents'
  ]) as expected
  where not exists (
    select 1
    from pg_catalog.pg_class c
    join pg_catalog.pg_namespace n on n.oid = c.relnamespace
    where n.nspname = 'public' and c.relname = expected and c.relkind = 'r'
  );
  if missing_tables is not null then
    raise exception 'missing N4A tables: %', missing_tables;
  end if;

  if not exists (select 1 from pg_catalog.pg_extension where extname = 'postgis') then
    raise exception 'PostGIS extension is not installed';
  end if;

  select array_agg(expected order by expected)
  into missing_indexes
  from unnest(array[
    'idx_transport_source_snapshots_namespace_state',
    'idx_transport_source_places_snapshot_name',
    'idx_transport_source_places_status',
    'idx_transport_source_places_location',
    'idx_transport_source_nodes_snapshot_type',
    'idx_transport_source_nodes_mode',
    'idx_transport_source_nodes_status',
    'idx_transport_source_nodes_location',
    'idx_transport_source_memberships_place',
    'idx_transport_source_memberships_node',
    'idx_transport_source_memberships_unresolved',
    'idx_transport_source_place_parents_child',
    'idx_transport_source_place_parents_parent',
    'idx_transport_source_place_parents_unresolved'
  ]) as expected
  where not exists (
    select 1 from pg_catalog.pg_indexes i
    where i.schemaname = 'public' and i.indexname = expected
  );
  if missing_indexes is not null then
    raise exception 'missing N4A indexes: %', missing_indexes;
  end if;

  for table_name in select unnest(array[
    'transport_source_snapshots',
    'transport_source_places',
    'transport_source_nodes',
    'transport_source_memberships',
    'transport_source_place_parents'
  ]) loop
    if not (select c.relrowsecurity from pg_catalog.pg_class c
            join pg_catalog.pg_namespace n on n.oid = c.relnamespace
            where n.nspname = 'public' and c.relname = table_name) then
      raise exception 'RLS is not enabled on %', table_name;
    end if;
    if has_table_privilege('anon', format('public.%I', table_name), 'SELECT') then
      raise exception 'anon unexpectedly has SELECT on %', table_name;
    end if;
    if has_table_privilege('authenticated', format('public.%I', table_name), 'SELECT') then
      raise exception 'authenticated unexpectedly has SELECT on %', table_name;
    end if;
    if not has_table_privilege('service_role', format('public.%I', table_name), 'SELECT') then
      raise exception 'service_role lacks SELECT on %', table_name;
    end if;
  end loop;

  if not exists (select 1 from pg_proc where pronamespace = 'public'::regnamespace and proname = 'update_updated_at') then
    raise exception 'shared update_updated_at() function is missing';
  end if;
  if (select count(*) from pg_catalog.pg_trigger t
      join pg_catalog.pg_class c on c.oid = t.tgrelid
      join pg_catalog.pg_namespace n on n.oid = c.relnamespace
      where n.nspname = 'public'
        and t.tgname like 'set_transport_source_%_updated_at'
        and not t.tgisinternal) <> 5 then
    raise exception 'expected five transport updated_at triggers';
  end if;
  if exists (
    select 1
    from pg_catalog.pg_constraint con
    join pg_catalog.pg_class c on c.oid = con.conrelid
    join pg_catalog.pg_namespace n on n.oid = c.relnamespace
    join pg_catalog.pg_class f on f.oid = con.confrelid
    join pg_catalog.pg_namespace fn on fn.oid = f.relnamespace
    where n.nspname = 'public'
      and c.relname like 'transport_source_%'
      and fn.nspname = 'public'
      and f.relname = 'facilities'
  ) then
    raise exception 'N4A source graph unexpectedly references canonical facilities';
  end if;
  if exists (
    select 1 from pg_catalog.pg_class c
    join pg_catalog.pg_namespace n on n.oid = c.relnamespace
    where n.nspname = 'public' and c.relname = 'transport_source_complexes'
  ) then
    raise exception 'derived normalized complexes were persisted';
  end if;
end;
$$;

create temporary table n4b_counts (
  object_name text primary key,
  row_count bigint not null
) on commit drop;

insert into public.transport_source_snapshots (
  source_namespace, product_name, source_snapshot_key, source_url,
  source_checksum_sha256, source_byte_size, retrieved_at, licence,
  attribution, parser_version, row_counts
) values (
  'naptan', 'n4b-fixture-a',
  'naptan:sha256:aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa',
  'https://example.invalid/naptan-fixture-a',
  'aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa',
  123, now(), 'synthetic-test', 'synthetic-test', 'n4b-ci-1', '{"fixture": "A"}'
)
returning id as snapshot_a_id \gset

-- Snapshot identity uniqueness and malformed identity checks.
do $$
begin
  begin
    insert into public.transport_source_snapshots (
      source_namespace, product_name, source_snapshot_key, source_url,
      source_checksum_sha256, source_byte_size, retrieved_at, licence,
      attribution, parser_version
    ) values (
      'naptan', 'duplicate',
      'naptan:sha256:aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa',
      'https://example.invalid/duplicate',
      'aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa',
      0, now(), 'test', 'test', 'n4b-ci-duplicate'
    );
    raise exception 'duplicate snapshot identity was accepted';
  exception when unique_violation then
    null;
  end;
  begin
    insert into public.transport_source_snapshots (
      source_namespace, product_name, source_snapshot_key, source_url,
      source_checksum_sha256, source_byte_size, retrieved_at, licence,
      attribution, parser_version
    ) values (
      'naptan', 'malformed', 'naptan:sha256:not-a-sha',
      'https://example.invalid/malformed',
      'not-a-sha', 0, now(), 'test', 'test', 'n4b-ci-malformed'
    );
    raise exception 'malformed snapshot identity was accepted';
  exception when check_violation then
    null;
  end;
end;
$$;

insert into public.transport_source_places (
  snapshot_id, publisher_identity, publisher_id, display_name,
  normalized_name, publisher_latitude, publisher_longitude, coordinate_scope,
  source_attributes
)
select
  :'snapshot_a_id'::uuid,
  'naptan-stop-area:DEEP' || i,
  'DEEP' || i,
  'Deep ' || i,
  lower('deep ' || i),
  case when i = 0 then 51.5000 else null end,
  case when i = 0 then -0.1200 else null end,
  case when i = 0 then 'STOP_AREA_LEVEL' else 'NONE' end,
  jsonb_build_object('fixture', 'A', 'depth', i)
from generate_series(0, 12) as series(i);

insert into public.transport_source_places (
  snapshot_id, publisher_identity, publisher_id, display_name,
  normalized_name, coordinate_scope, source_attributes
) values
  (:'snapshot_a_id'::uuid, 'naptan-stop-area:ROOT2', 'ROOT2', 'Root 2', 'root 2', 'NONE', '{"fixture":"A"}'),
  (:'snapshot_a_id'::uuid, 'naptan-stop-area:ALT', 'ALT', 'Alternate Parent', 'alternate parent', 'NONE', '{"fixture":"A"}'),
  (:'snapshot_a_id'::uuid, 'naptan-stop-area:CHILD', 'CHILD', 'Child', 'child', 'NONE', '{"fixture":"A"}');

insert into public.transport_source_place_parents (
  snapshot_id, child_place_id, parent_place_id, publisher_child_identity,
  publisher_parent_identity, parent_edge_key, source_attributes
)
select
  :'snapshot_a_id'::uuid,
  child.id,
  parent.id,
  child.publisher_identity,
  parent.publisher_identity,
  child.publisher_identity || '|' || parent.publisher_identity,
  '{"fixture":"A"}'
from generate_series(1, 12) as series(i)
join public.transport_source_places child
  on child.snapshot_id = :'snapshot_a_id'::uuid
 and child.publisher_identity = 'naptan-stop-area:DEEP' || i
join public.transport_source_places parent
  on parent.snapshot_id = :'snapshot_a_id'::uuid
 and parent.publisher_identity = 'naptan-stop-area:DEEP' || (i - 1);

insert into public.transport_source_place_parents (
  snapshot_id, child_place_id, parent_place_id, publisher_child_identity,
  publisher_parent_identity, parent_edge_key, source_attributes
)
select
  :'snapshot_a_id'::uuid, child.id, parent.id, child.publisher_identity,
  parent.publisher_identity, child.publisher_identity || '|' || parent.publisher_identity,
  '{"fixture":"A"}'
from public.transport_source_places child
join public.transport_source_places parent
  on parent.snapshot_id = child.snapshot_id
where child.snapshot_id = :'snapshot_a_id'::uuid
  and child.publisher_identity = 'naptan-stop-area:ALT'
  and parent.publisher_identity = 'naptan-stop-area:DEEP0';

insert into public.transport_source_place_parents (
  snapshot_id, child_place_id, parent_place_id, publisher_child_identity,
  publisher_parent_identity, parent_edge_key, source_attributes
)
select
  :'snapshot_a_id'::uuid, child.id, parent.id, child.publisher_identity,
  parent.publisher_identity, child.publisher_identity || '|' || parent.publisher_identity,
  '{"fixture":"A"}'
from public.transport_source_places child
join public.transport_source_places parent
  on parent.snapshot_id = child.snapshot_id
where child.snapshot_id = :'snapshot_a_id'::uuid
  and child.publisher_identity = 'naptan-stop-area:CHILD'
  and parent.publisher_identity in ('naptan-stop-area:DEEP0', 'naptan-stop-area:ALT');

insert into public.transport_source_place_parents (
  snapshot_id, child_place_id, parent_place_id, publisher_child_identity,
  publisher_parent_identity, parent_edge_key, resolution_status, source_attributes
) values (
  :'snapshot_a_id'::uuid,
  (select id from public.transport_source_places where snapshot_id = :'snapshot_a_id'::uuid and publisher_identity = 'naptan-stop-area:DEEP0'),
  null,
  'naptan-stop-area:DEEP0', 'naptan-stop-area:MISSING_PARENT',
  'naptan-stop-area:DEEP0|naptan-stop-area:MISSING_PARENT',
  'UNRESOLVED_MISSING_PARENT', '{"fixture":"A"}'
);

insert into public.transport_source_nodes (
  snapshot_id, publisher_identity, publisher_id, source_stop_type,
  normalized_mode, display_name, publisher_latitude, publisher_longitude,
  coordinate_scope, source_attributes
) values
  (:'snapshot_a_id'::uuid, 'naptan-stop-point:TEST123', 'TEST123', 'MKD', 'BUS', 'Test 123', 51.5001, -0.1201, 'TRANSPORT_STOP_LEVEL', '{"fixture":"A"}'),
  (:'snapshot_a_id'::uuid, 'naptan-stop-point:NODE_REMOVED', 'NODE_REMOVED', 'BCT', 'BUS', 'Removed in B', null, null, 'NONE', '{"fixture":"A"}'),
  (:'snapshot_a_id'::uuid, 'naptan-stop-point:NODE_CROSS', 'NODE_CROSS', 'MET', 'METRO', 'Cross root', null, null, 'NONE', '{"fixture":"A"}');

insert into public.transport_source_memberships (
  snapshot_id, node_id, place_id, publisher_node_identity,
  publisher_place_identity, membership_key, duplicate_occurrence_count,
  source_attributes
)
select
  :'snapshot_a_id'::uuid, n.id, p.id, n.publisher_identity, p.publisher_identity,
  n.publisher_identity || '|' || p.publisher_identity, 1, '{"fixture":"A"}'
from public.transport_source_nodes n
cross join public.transport_source_places p
where n.snapshot_id = :'snapshot_a_id'::uuid
  and p.snapshot_id = :'snapshot_a_id'::uuid
  and n.publisher_identity = 'naptan-stop-point:TEST123'
  and p.publisher_identity in ('naptan-stop-area:DEEP0', 'naptan-stop-area:ALT');

insert into public.transport_source_memberships (
  snapshot_id, node_id, place_id, publisher_node_identity,
  publisher_place_identity, membership_key, duplicate_occurrence_count,
  source_attributes
)
select
  :'snapshot_a_id'::uuid, n.id, p.id, n.publisher_identity, p.publisher_identity,
  n.publisher_identity || '|' || p.publisher_identity, 1, '{"fixture":"A"}'
from public.transport_source_nodes n
cross join public.transport_source_places p
where n.snapshot_id = :'snapshot_a_id'::uuid
  and p.snapshot_id = :'snapshot_a_id'::uuid
  and n.publisher_identity = 'naptan-stop-point:NODE_CROSS'
  and p.publisher_identity in ('naptan-stop-area:DEEP0', 'naptan-stop-area:ROOT2');

insert into public.transport_source_memberships (
  snapshot_id, node_id, place_id, publisher_node_identity,
  publisher_place_identity, membership_key, duplicate_occurrence_count,
  source_attributes
)
select
  :'snapshot_a_id'::uuid, n.id, p.id, n.publisher_identity, p.publisher_identity,
  n.publisher_identity || '|' || p.publisher_identity, 2, '{"fixture":"A","duplicate_elements":2}'
from public.transport_source_nodes n
cross join public.transport_source_places p
where n.snapshot_id = :'snapshot_a_id'::uuid
  and p.snapshot_id = :'snapshot_a_id'::uuid
  and n.publisher_identity = 'naptan-stop-point:TEST123'
  and p.publisher_identity = 'naptan-stop-area:DEEP0'
on conflict (snapshot_id, membership_key) do update
set duplicate_occurrence_count = excluded.duplicate_occurrence_count;

insert into public.transport_source_memberships (
  snapshot_id, node_id, place_id, publisher_node_identity,
  publisher_place_identity, membership_key, resolution_status, source_attributes
) values (
  :'snapshot_a_id'::uuid,
  (select id from public.transport_source_nodes where snapshot_id = :'snapshot_a_id'::uuid and publisher_identity = 'naptan-stop-point:TEST123'),
  null,
  'naptan-stop-point:TEST123', 'naptan-stop-area:MISSING_AREA',
  'naptan-stop-point:TEST123|naptan-stop-area:MISSING_AREA',
  'UNRESOLVED_MISSING_PLACE', '{"fixture":"A"}'
);

insert into n4b_counts
select 'snapshots', count(*) from public.transport_source_snapshots where id = :'snapshot_a_id'::uuid
union all select 'places', count(*) from public.transport_source_places where snapshot_id = :'snapshot_a_id'::uuid
union all select 'nodes', count(*) from public.transport_source_nodes where snapshot_id = :'snapshot_a_id'::uuid
union all select 'memberships', count(*) from public.transport_source_memberships where snapshot_id = :'snapshot_a_id'::uuid
union all select 'parents', count(*) from public.transport_source_place_parents where snapshot_id = :'snapshot_a_id'::uuid;

do $$
begin
  if (select count(*) from public.transport_source_memberships where snapshot_id = :'snapshot_a_id'::uuid and duplicate_occurrence_count = 2) <> 1 then
    raise exception 'duplicate occurrence count was not preserved';
  end if;
  if (select count(*) from public.transport_source_memberships where snapshot_id = :'snapshot_a_id'::uuid and resolution_status = 'UNRESOLVED_MISSING_PLACE') <> 1 then
    raise exception 'unresolved membership was not retained';
  end if;
  if (select count(*) from public.transport_source_place_parents where snapshot_id = :'snapshot_a_id'::uuid and resolution_status = 'UNRESOLVED_MISSING_PARENT') <> 1 then
    raise exception 'unresolved parent edge was not retained';
  end if;
  if (select st_x(publisher_location::geometry) from public.transport_source_places where snapshot_id = :'snapshot_a_id'::uuid and publisher_identity = 'naptan-stop-area:DEEP0') <> -0.1200 then
    raise exception 'publisher longitude was not represented by PostGIS';
  end if;
  if (select st_y(publisher_location::geometry) from public.transport_source_places where snapshot_id = :'snapshot_a_id'::uuid and publisher_identity = 'naptan-stop-area:DEEP0') <> 51.5000 then
    raise exception 'publisher latitude was not represented by PostGIS';
  end if;
end;
$$;

-- Invalid coordinates, duplicate identities, and cross-snapshot composite FKs.
do $$
declare
  snapshot_b_id uuid;
  node_b_id uuid;
  place_a_id uuid;
begin
  begin
    insert into public.transport_source_places (
      snapshot_id, publisher_identity, publisher_id, display_name,
      publisher_latitude, publisher_longitude, coordinate_scope
    ) values (:'snapshot_a_id'::uuid, 'naptan-stop-area:BAD', 'BAD', 'Bad', 91, 0, 'STOP_AREA_LEVEL');
    raise exception 'invalid latitude was accepted';
  exception when check_violation then null;
  end;

  begin
    insert into public.transport_source_places (
      snapshot_id, publisher_identity, publisher_id, display_name,
      coordinate_scope
    ) values (:'snapshot_a_id'::uuid, 'naptan-stop-area:DEEP0', 'DEEP0-DUP', 'Duplicate', 'NONE');
    raise exception 'duplicate StopArea identity was accepted';
  exception when unique_violation then null;
  end;

  insert into public.transport_source_snapshots (
    source_namespace, product_name, source_snapshot_key, source_url,
    source_checksum_sha256, source_byte_size, retrieved_at, licence,
    attribution, parser_version
  ) values (
    'naptan', 'n4b-fixture-b',
    'naptan:sha256:bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb',
    'https://example.invalid/naptan-fixture-b',
    'bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb',
    456, now(), 'synthetic-test', 'synthetic-test', 'n4b-ci-1'
  ) returning id into snapshot_b_id;

  insert into public.transport_source_places (
    snapshot_id, publisher_identity, publisher_id, display_name,
    normalized_name, publisher_latitude, publisher_longitude, coordinate_scope
  ) values
    (snapshot_b_id, 'naptan-stop-area:DEEP0', 'DEEP0', 'Deep 0 renamed', 'deep 0 renamed', 51.6000, -0.1300, 'STOP_AREA_LEVEL'),
    (snapshot_b_id, 'naptan-stop-area:NEW', 'NEW', 'New place', 'new place', 'NONE');

  insert into public.transport_source_nodes (
    snapshot_id, publisher_identity, publisher_id, source_stop_type,
    normalized_mode, display_name, coordinate_scope
  ) values
    (snapshot_b_id, 'naptan-stop-point:TEST123', 'TEST123', 'MKD', 'BUS', 'Test 123', 'NONE'),
    (snapshot_b_id, 'naptan-stop-point:NODE_NEW', 'NODE_NEW', 'MKD', 'BUS', 'New node', 'NONE');

  select id into node_b_id from public.transport_source_nodes
  where snapshot_id = snapshot_b_id and publisher_identity = 'naptan-stop-point:TEST123';
  select id into place_a_id from public.transport_source_places
  where snapshot_id = :'snapshot_a_id'::uuid and publisher_identity = 'naptan-stop-area:DEEP0';

  begin
    insert into public.transport_source_memberships (
      snapshot_id, node_id, place_id, publisher_node_identity,
      publisher_place_identity, membership_key
    ) values (
      :'snapshot_a_id'::uuid, node_b_id, place_a_id,
      'naptan-stop-point:TEST123', 'naptan-stop-area:DEEP0',
      'naptan-stop-point:TEST123|naptan-stop-area:CROSS_SNAPSHOT'
    );
    raise exception 'cross-snapshot membership FK was accepted';
  exception when foreign_key_violation then null;
  end;

  insert into public.transport_source_place_parents (
    snapshot_id, child_place_id, parent_place_id, publisher_child_identity,
    publisher_parent_identity, parent_edge_key, resolution_status
  ) values (
    snapshot_b_id,
    (select id from public.transport_source_places where snapshot_id = snapshot_b_id and publisher_identity = 'naptan-stop-area:NEW'),
    (select id from public.transport_source_places where snapshot_id = snapshot_b_id and publisher_identity = 'naptan-stop-area:DEEP0'),
    'naptan-stop-area:NEW', 'naptan-stop-area:DEEP0',
    'naptan-stop-area:NEW|naptan-stop-area:DEEP0', 'RESOLVED'
  );

  if (select count(*) from public.transport_source_places where snapshot_id = :'snapshot_a_id'::uuid and publisher_identity = 'naptan-stop-area:DEEP0') <> 1 then
    raise exception 'Snapshot A history was overwritten';
  end if;
  if (select count(*) from public.transport_source_places where snapshot_id = snapshot_b_id and publisher_identity = 'naptan-stop-area:NEW') <> 1 then
    raise exception 'Snapshot B new place was not stored';
  end if;
end;
$$;

-- SQL-layer identical replay: replaying existing logical rows with conflict
-- coalescing must add no rows and must leave duplicate evidence unchanged.
insert into public.transport_source_places (
  id, snapshot_id, publisher_identity, publisher_id, place_kind,
  display_name, normalized_name, source_type, administrative_area_code,
  source_status, source_modification, publisher_latitude, publisher_longitude,
  coordinate_scope, source_attributes, created_at, updated_at
)
select id, snapshot_id, publisher_identity, publisher_id, place_kind,
  display_name, normalized_name, source_type, administrative_area_code,
  source_status, source_modification, publisher_latitude, publisher_longitude,
  coordinate_scope, source_attributes, created_at, updated_at
from public.transport_source_places
where snapshot_id = :'snapshot_a_id'::uuid
on conflict (snapshot_id, publisher_identity) do nothing;

insert into public.transport_source_nodes (
  id, snapshot_id, publisher_identity, publisher_id, source_stop_type,
  normalized_mode, display_name, normalized_name, source_status,
  source_modification, publisher_latitude, publisher_longitude,
  coordinate_scope, source_attributes, created_at, updated_at
)
select id, snapshot_id, publisher_identity, publisher_id, source_stop_type,
  normalized_mode, display_name, normalized_name, source_status,
  source_modification, publisher_latitude, publisher_longitude,
  coordinate_scope, source_attributes, created_at, updated_at
from public.transport_source_nodes
where snapshot_id = :'snapshot_a_id'::uuid
on conflict (snapshot_id, publisher_identity) do nothing;

insert into public.transport_source_memberships (
  id, snapshot_id, node_id, place_id, publisher_node_identity,
  publisher_place_identity, membership_key, resolution_status,
  duplicate_occurrence_count, source_attributes, created_at, updated_at
)
select id, snapshot_id, node_id, place_id, publisher_node_identity,
  publisher_place_identity, membership_key, resolution_status,
  duplicate_occurrence_count, source_attributes, created_at, updated_at
from public.transport_source_memberships
where snapshot_id = :'snapshot_a_id'::uuid
on conflict (snapshot_id, membership_key) do nothing;

insert into public.transport_source_place_parents (
  id, snapshot_id, child_place_id, parent_place_id,
  publisher_child_identity, publisher_parent_identity, parent_edge_key,
  resolution_status, duplicate_occurrence_count, source_attributes,
  created_at, updated_at
)
select id, snapshot_id, child_place_id, parent_place_id,
  publisher_child_identity, publisher_parent_identity, parent_edge_key,
  resolution_status, duplicate_occurrence_count, source_attributes,
  created_at, updated_at
from public.transport_source_place_parents
where snapshot_id = :'snapshot_a_id'::uuid
on conflict (snapshot_id, parent_edge_key) do nothing;

do $$
declare
  before_count bigint;
  after_count bigint;
begin
  select row_count into before_count from n4b_counts where object_name = 'places';
  select count(*) into after_count from public.transport_source_places where snapshot_id = :'snapshot_a_id'::uuid;
  if before_count <> after_count then raise exception 'place replay was not idempotent'; end if;
  select row_count into before_count from n4b_counts where object_name = 'nodes';
  select count(*) into after_count from public.transport_source_nodes where snapshot_id = :'snapshot_a_id'::uuid;
  if before_count <> after_count then raise exception 'node replay was not idempotent'; end if;
  select row_count into before_count from n4b_counts where object_name = 'memberships';
  select count(*) into after_count from public.transport_source_memberships where snapshot_id = :'snapshot_a_id'::uuid;
  if before_count <> after_count then raise exception 'membership replay was not idempotent'; end if;
  select row_count into before_count from n4b_counts where object_name = 'parents';
  select count(*) into after_count from public.transport_source_place_parents where snapshot_id = :'snapshot_a_id'::uuid;
  if before_count <> after_count then raise exception 'parent replay was not idempotent'; end if;
end;
$$;

-- Trigger behaviour must update updated_at on an existing row.
do $$
declare
  before_updated timestamptz;
  after_updated timestamptz;
begin
  select updated_at into before_updated
  from public.transport_source_nodes
  where snapshot_id = :'snapshot_a_id'::uuid
    and publisher_identity = 'naptan-stop-point:TEST123';
  perform pg_sleep(0.05);
  update public.transport_source_nodes
  set display_name = 'Test 123 updated'
  where snapshot_id = :'snapshot_a_id'::uuid
    and publisher_identity = 'naptan-stop-point:TEST123';
  select updated_at into after_updated
  from public.transport_source_nodes
  where snapshot_id = :'snapshot_a_id'::uuid
    and publisher_identity = 'naptan-stop-point:TEST123';
  if after_updated <= before_updated then raise exception 'update_updated_at trigger did not advance timestamp'; end if;
end;
$$;

commit;

select 'N4B_LIVE_SQL_ASSERTIONS_PASSED' as result;

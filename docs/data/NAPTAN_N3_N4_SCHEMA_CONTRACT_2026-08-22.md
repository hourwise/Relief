# NaPTAN N4 Schema Contract

Status: implementation-ready design with open operational questions. No SQL migration is created or applied by N3.

## Minimum source-neutral model

### `transport_source_places`

One row per source-level normalized complex or preserved subplace. Required concepts: source namespace, publisher place identity, role (`COMPLEX_ROOT`/`SUBPLACE`), publisher display name, normalized comparison name, aliases, source type/area type, observed modes, lifecycle/status, publisher geometry, geometry scope, source revision metadata, provenance and reconciliation state. Unique `(source_namespace, publisher_place_identity)`.

### `transport_source_nodes`

One row per publisher StopPoint/access node. Required concepts: source namespace, publisher node identity (`naptan:<ATCOCode>`), StopType, name, mode, lifecycle, source coordinates and coordinate scope, revision metadata and provenance. Unique `(source_namespace, publisher_node_identity)`.

### `transport_source_memberships`

Strong foreign keys from a source node to a source place, with membership kind, source revision, validity and provenance. Unique `(source_place_id, source_node_id, source_revision)` or an equivalent current/history contract. Every publisher-declared membership is retained, including multi-parent membership.

### `transport_source_place_parents`

Because N2/N3 observed nested StopArea parents up to depth 13, parent edges deserve a separate strong-FK table rather than a lossy JSON field. It stores child place, parent place, source revision, validity and provenance. Cycles are rejected by governed validation before publish; PostgreSQL row checks cannot prove arbitrary graph acyclicity.

## Canonical and security boundaries

The first migration should not require a canonical `facilities.id` link. A later governed reconciliation relation can be additive and auditable; it must not be a nullable-polymorphic foreign key. Source transport evidence is privileged provenance by default: RLS enabled, no anon/authenticated/public grants or policies, service-role/governed ingestion only. No public map/search query is required for N4.

## Constraints and indexes

Use UUIDs only for internal row identity. Enforce non-empty publisher identities, source namespace checks, uniqueness at publisher identity scope, valid geometry scope values, and revision consistency. Index source namespace/identity, place role, parent/child edges, node identity, current status, normalized name and reconciliation state. Add spatial indexes only if a governed read path demonstrates need.

## Lifecycle and deletion

Do not delete source identities when upstream marks a node or area inactive/deleted. Retain revision/status history or a current-state row with source revision. A future current-view query may exclude inactive nodes without erasing evidence.

## Open questions before N4

1. Whether source revision history is append-only or current-state plus audit rows.
2. Whether a transport source registry already exists that should own namespaces.
3. Whether canonical links are needed in the first migration or should remain a separate reconciliation table.
4. Whether any public product feature needs published transport place summaries; none is authorized by N3.

N4 is therefore `N4_SCHEMA_CONTRACT_READY_WITH_OPEN_QUESTIONS`, not a deployment authorization.

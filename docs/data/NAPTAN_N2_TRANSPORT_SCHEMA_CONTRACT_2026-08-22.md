# NaPTAN N2 transport hierarchy schema contract

**Design only — no migration and no production ingestion.**

## Recommended additive objects

`transport_source_places` should preserve a publisher-defined transport-place identity such as `naptan-stop-area:<StopAreaCode>`, source name, type, administrative area, source geometry, coordinate scope, status, revision, and provenance.

`transport_source_nodes` should preserve publisher-defined node identities such as `naptan:<ATCOCode>`, StopType, mode, source geometry, status, and provenance.

`transport_source_memberships` should strongly reference one source place and one source node, preserve membership revision/status, and enforce deterministic uniqueness on `(source_place_id, source_node_id)`.

An optional `transport_source_place_parents` relation should preserve official parent-area links without flattening hierarchy. It must reject self-links, missing parents, duplicate edges, and cycles in governed validation.

## Canonical boundary

These are source transport entities, not canonical Relief facilities. A later reconciliation process may attach one or more source places/nodes to an existing facility, but source hierarchy cannot create a facility or toilet automatically. Raw source provenance remains privileged unless a separate public projection is approved.

## Identity and idempotency

- StopArea key: `naptan-stop-area:<StopAreaCode>`.
- StopPoint key: `naptan:<ATCOCode>`.
- Preserve publisher casing/value separately from normalized lookup values.
- Missing or duplicate identities fail closed.
- Repeated identical source capture produces no duplicate source entities or memberships.
- Conflicting revisions are quarantined or versioned by a separately approved contract; they never overwrite canonical facilities silently.

## Coordinate ownership

Source coordinates remain `STOP_AREA_LEVEL` or `TRANSPORT_STOP_LEVEL`. A member centroid is `DERIVED_FROM_MEMBER_STOPPOINTS` and must retain original point coordinates and conversion/provenance metadata. No source geometry is toilet geometry.

## Security and governance

The future tables should use RLS and private-by-default grants consistent with `facility_source_observations`. Privileged ingestion may write through the existing governed server boundary; public clients should receive only an explicitly approved projection. No permissive policy is justified by this design.

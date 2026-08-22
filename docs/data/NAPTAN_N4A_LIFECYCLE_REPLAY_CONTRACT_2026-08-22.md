# NaPTAN N4A — lifecycle and replay contract

## Replay phases

1. Verify the exact source URL, checksum, byte size, licence, and attribution.
2. Register or reuse the immutable `source_snapshot_key`.
3. Parse StopAreas and StopPoints with publisher identities preserved.
4. Preserve every publisher membership and place-parent edge; coalesce only exact duplicate edge elements and retain the occurrence count.
5. Resolve references when the referenced row exists in the same snapshot; otherwise retain raw IDs and an unresolved status.
6. Run identity, coordinate, duplicate, and graph-cycle validation.
7. Calculate N3-style normalized complexes as a deterministic projection only.
8. Verify national/fixture counts and invariants.
9. A later separately authorized importer may commit the snapshot atomically.
10. Run a second read-only plan and require zero new logical keys.

## Snapshot A → B semantics

An unchanged entity has the same snapshot-local publisher identity and equal source fields. A renamed or re-geocoded entity is a changed entity in the new snapshot; the old row remains historical. A new entity is added only to the new snapshot. A removed entity is absent from the new snapshot but is not deleted from the old snapshot. Membership and parent changes are edge-level additions/removals. If a missing parent becomes available later, the new snapshot contains the resolved edge while the old unresolved edge remains explainable. If a previously valid parent disappears, the new edge is unresolved rather than fabricated.

Status changes are source facts, not deletion instructions. Inactive/deleted records remain in their captured snapshot and may be classified by a future current-state projection.

## Idempotency

The unique keys are snapshot key; `(snapshot_id, publisher_identity)` for places/nodes; `(snapshot_id, membership_key)` for memberships; and `(snapshot_id, parent_edge_key)` for parent edges. Replaying an identical snapshot therefore produces zero new logical keys and no source-value drift. A conflicting duplicate identity or changed payload under the same exact snapshot is a hard validation error, not an update shortcut.

## Derived complex replay

Projection traverses all resolved parent edges. No parent is selected when multiple parents resolve to different roots; the affected place is unresolved. Cycles are quarantined. A projection never changes publisher graph rows and never creates a canonical Relief facility.

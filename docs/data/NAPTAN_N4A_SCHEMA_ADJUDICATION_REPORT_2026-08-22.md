# Relief NaPTAN N4A — schema adjudication

Status: **candidate schema / not deployed / no source ingestion**.

## Decision

N4A stores the publisher graph as snapshot-scoped source evidence in five additive tables:

```text
transport_source_snapshots
  ├── transport_source_places          (publisher StopAreas)
  ├── transport_source_nodes           (publisher StopPoints)
  ├── transport_source_memberships     (publisher node → place edges)
  └── transport_source_place_parents   (publisher place → place edges)
```

The N3 normalized transport complex is a **DETERMINISTIC_PROJECTION** over resolved publisher place-parent edges. It is not stored as a publisher fact in N4A. This preserves the DfT graph, makes the derivation auditable, and avoids turning an inferred root into a second canonical place model. A future governed batch may persist a derived projection only if it needs a versioned reconciliation result; that is deliberately outside this migration.

## N3 input contract

The design uses the committed N1/N2/N3 evidence and the frozen N3 snapshot identity: UK Department for Transport NaPTAN XML, SHA-256 `6FC7E40E2AF3B30E9FD117BDAC313B58F3385BFF26517FD78D5554DA12B4183A`, 578,991,782 bytes, retrieved `2026-08-22T14:48:39.4826193Z`. The raw XML was not refreshed or committed in N4A.

N3 realities preserved by the design include 97,270 StopAreas, 436,428 StopPoints, 169,527 publisher membership elements, 701 multi-parent StopPoints, 3 duplicate membership elements, 1,543 missing member-parent references, 41 missing area-parent references, depth up to 13, 81,435 publisher geometries, 24 analysis-only derived geometries, and 12,292 areas without usable geometry.

## Publisher versus Relief-derived data

Publisher identity, display name, type, status, modification, source coordinates, memberships, and parent edges are stored as snapshot facts. `normalized_name`, `normalized_mode`, deterministic keys, and resolution status are Relief-derived fields that retain their raw source counterparts. Complex roots are derived projections. No table in this migration references `facilities`; canonical reconciliation remains a separately governed operation.

## Snapshot and lifecycle

`transport_source_snapshots` is separate from `import_runs`, whose existing semantics belong to the Toilet Map ingestion history. The source snapshot key is `<source_namespace>:sha256:<lowercase checksum>`, unique both globally and within namespace/checksum. A later snapshot appends a new snapshot-scoped fact set; it does not overwrite the old set. `CAPTURED → VALIDATING → VALIDATED → INGESTED` is the normal path, with `FAILED` and `SUPERSEDED` retained as explicit historical states.

Unchanged, changed, added, removed, and reappearing source entities are explained by comparing publisher identities between snapshots. Historical rows remain available for audit. A governed importer may maintain a separate current projection later; N4A does not add one.

## Identity and graph integrity

StopAreas use `naptan-stop-area:<UPPER StopAreaCode>`. StopPoints use `naptan-stop-point:<UPPER ATCOCode>`. These publisher identities are unique within a snapshot and remain queryable independently of internal UUIDs. Membership and parent-edge keys are ordered publisher-identity pairs and never depend on row order.

All 701 multi-parent cases remain representable, including the 628 that cross resolved complexes or remain unresolved. Exact duplicate publisher edges are represented once with `duplicate_occurrence_count`; the duplicate fact is not silently discarded. Missing references keep their raw publisher identity, a nullable resolved FK, and an explicit unresolved status. No placeholder parent or node is fabricated.

Parent chains have no database depth limit. The deterministic graph validator rejects or quarantines cycles and unresolved graphs before a snapshot can be marked `VALIDATED`; it never chooses a parent or truncates a chain.

## Geometry and modes

Source places and nodes store publisher latitude/longitude only when the pair is valid, with explicit `coordinate_scope`. Derived child/member centroids remain analysis-only in N4A and cannot masquerade as publisher geometry. Raw StopType and source status remain present; normalized mode is a derived helper and does not replace source values.

## Security and canonical boundary

All five tables enable RLS, revoke table privileges from `public`, `anon`, and `authenticated`, and grant only the intended `service_role` access. No policies are created. No public API or UI is changed. No canonical facility link is present in the candidate migration. A future reconciliation table may record a governed judgement without mutating source facts or creating a facility automatically.

## Validation status

The candidate migration is static-validated and covered by deterministic fixture tests. No local PostgreSQL execution was assumed; live database validation is required before any separate deployment authorization. Production was read-only verified and unchanged.

Final N4A state: **N4A_SCHEMA_SEALED / STATIC_MIGRATION_VALIDATED / LIVE_DATABASE_VALIDATION_REQUIRED / PRODUCTION MIGRATION NOT AUTHORIZED**.

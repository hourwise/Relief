# Proposed TfL Physical-Unit Promotion Contract — Batch 2

**PROPOSED / NOT EXECUTED / PRODUCTION PROMOTION NOT AUTHORIZED**

This contract is the future gate for converting a TfL `facility_source_observations` record into a canonical `toilet_units` relationship. It does not create units, link observations, or change production state.

## Required evidence

A future transaction may promote only when all of the following are true:

1. The canonical parent facility already exists and is unambiguous.
2. Independent authoritative evidence identifies a distinguishable physical toilet location, such as a platform, level, ticket hall, or separately named toilet area. A gender label, source-row count, source ID, accessibility flag, baby-changing flag, fee flag, or station coordinate alone is insufficient.
3. Every source row mapped to the unit is listed explicitly. A source row may remain unlinked when its relationship is unresolved.
4. Conflicting source evidence is quarantined rather than resolved by overwrite.
5. Any toilet-level coordinate is independently supported at toilet level. Station coordinates remain `STATION_LEVEL` and are never copied into a child unit.

## Identity and provenance

- Parent identity remains the existing `facilities.id`.
- A proposed child identity is deterministic under the parent: `relief:{facility_id}:unit:{adjudication_key}`. The key must be derived from an adjudicated physical location, not from a TfL row ID alone.
- The original TfL identity remains `tfl:{StationUniqueId}:toilet:{Id}` in `facility_source_observations` and, only after approval, in `toilet_unit_sources`.
- The original observation, observed attributes, source hashes, attribution, and timestamps remain unchanged after any future link.

## Attribute ownership

Canonical unit fields may be populated only from attributes supported by the adjudicated unit evidence. Source-only fields remain in the observation payload. Accessibility, baby changing, fee status, opening/access notes, gateline position, and management status must not be promoted merely because they are present in a TfL row.

## Idempotency and conflict handling

- The future transaction must preflight the parent, all source identities, existing observations, and existing units.
- A duplicate deterministic unit identity with identical evidence is an idempotent no-op.
- A duplicate identity with different physical or source evidence is a hard conflict.
- The observation-to-unit relationship is written only after the unit and all provenance links are validated.
- Any unexpected parent, unit, source, coordinate, or row-count delta aborts the transaction.

## Transaction boundary and rollback

The future apply must use one governed transaction limited to the explicitly approved parent, unit, and source identities. It must verify before and after that no canonical facility fields, unrelated TfL rows, Batch 1 rows, staging rows, import runs, or public security policies changed.

## Current Batch 2 result

The 14 applied observations remain `toilet_unit_id = NULL`, `physical_unit_asserted = false`, `unit_link_status = UNLINKED`. No Batch 2 row meets the evidence threshold for promotion, and no future operation is emitted by this batch.

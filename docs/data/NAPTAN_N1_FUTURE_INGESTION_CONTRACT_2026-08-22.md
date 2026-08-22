# NaPTAN N1 — future governed ingestion contract

This is a design artifact only. It contains no executable production apply path and authorizes no NaPTAN ingestion.

## Source capture

Capture the official DfT national node and hierarchy products with retrieval UTC, resolved URL, response metadata, byte size, raw/package SHA-256, extracted-file SHA-256, encoding, licence, and required attribution. Raw national files remain outside Git unless a separate repository decision approves a bounded fixture.

## Identity

Use the publisher-defined `ATCOCode` as the primary stop-point identity and namespace it as `naptan:<ATCOCode>` after trimming and ASCII-case normalization only. Never use row position. Preserve `NaptanCode`, locality, administrative, and hierarchy identifiers as source fields. Missing or duplicate ATCOCode is a hard quarantine condition.

## Hierarchy and candidate selection

Ingest stop-point, entrance, platform, access-area, interchange, and StopArea relationships as distinct source entities or private source evidence. Candidate transport places are limited to officially documented interchange/place-level types. Entrances, platforms, bays, on-street stops, and taxi ranks are supporting or excluded nodes unless a separately authorized model says otherwise. One node never automatically becomes one Relief facility.

## Reconciliation order

1. Exact existing source identity or explicit authoritative cross-reference.
2. Official StopArea/interchange relationship.
3. Verified mode/type and stable name + locality.
4. High-confidence geometry within a documented threshold.
5. Governed manual review.

Any identity conflict, duplicate publisher identity, ambiguous parent, inconsistent geometry, incompatible type, missing provenance, or unclear group topology fails closed. A multi-node transport complex remains one candidate complex until evidence supports a different canonical topology.

## Canonical behavior

NaPTAN may attach source evidence to an existing Relief facility without changing canonical fields. A new canonical transport place requires a separate authorization, an independently verified parent identity, and an idempotent operation plan. Supporting nodes can remain source-only. No NaPTAN record can create a toilet or physical unit.

## Idempotency and safety

The logical key is publisher namespace + authoritative identity. Repeating an identical source capture produces zero duplicate records or links. Changed source revision is a new observed version or governed update, never an identity rewrite. Conflicts quarantine rather than overwrite canonical data. Any future apply must be atomic, bounded to a frozen manifest/cohort, and prove pre/post counts.

## Future RDG compatibility

Future RDG/National Rail evidence can attach as another source-specific identity and reconcile through official names, modes, hierarchy, and geometry. No direct RDG-to-NaPTAN key is assumed; the future feed must prove one.

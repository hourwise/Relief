# NaPTAN N3 Normalisation Contract

Status: design/evidence only. No migration, source ingestion, canonical facility mutation, or production write is authorized.

## Source entity boundary

A `TRANSPORT_COMPLEX` is a source-level identity rooted in an authoritative NaPTAN `StopArea`. It is not a Relief facility and is not a toilet. The preferred identity is the publisher root identity, represented as `naptan-stop-area:<StopAreaCode>`. A derived UUID must not replace that identity.

## Root selection

1. Retain every publisher-declared StopArea parent edge.
2. Resolve a StopArea to the unique highest ancestor whose parent references are present and acyclic.
3. A root with no child areas is `SINGLE_AREA_COMPLEX`.
4. A root with child areas and one mode is `PARENT_AREA_COMPLEX`.
5. A root with child areas and more than one observed structured mode is `MULTIMODAL_PARENT_COMPLEX`.
6. A StopPoint with more than one parent is `MULTI_PARENT_NODE_COMPLEX`; all memberships are retained and no parent is selected by proximity, row order, member count, or name.
7. Missing parents, multiple resolved roots, or cycles produce `UNRESOLVED_COMPLEX`/`INVALID_HIERARCHY` evidence and never create a synthetic parent.

The deepest ancestor is not automatically the user-facing station. Root identity is authoritative only when the publisher graph resolves; area type, children, modes, name and geometry remain separate evidence.

## Subplace preservation

The normalized shape is:

```text
transport complex (root StopArea)
  └── source subplace (child StopArea)
        └── source node (StopPoint)
```

Rail, metro, bus, ferry and other child areas remain meaningful subplaces. Entrances, platforms, bays and ordinary access nodes remain source nodes or supporting evidence according to their StopType. Normalisation never destructively flattens child areas into multiple canonical facilities.

## Modes

Modes are unions of structured StopType-derived modes from member StopPoints. The source model preserves all modes. A complex is `multimodal` when the union contains more than one mode. No mode is inferred from display-name text. A primary mode is intentionally not persisted by N3 because it would discard secondary transport evidence.

## Names

Preserve the publisher root name as display data. Preserve child-area names as aliases/subplace names. Matching uses deterministic Unicode NFKC, case-folding, explicit punctuation-to-space normalization and whitespace collapse. Original strings are never overwritten. Names alone never collapse peer areas in different locations or without an official common parent.

## Geometry

Precedence is:

1. publisher root StopArea coordinate (`PUBLISHER_STOPAREA_COORDINATE` or `PUBLISHER_PARENT_AREA_COORDINATE`);
2. analysis-only centroid of child-area publisher coordinates (`DERIVED_CHILD_AREA_CENTROID`);
3. analysis-only centroid of member StopPoint coordinates (`DERIVED_MEMBER_CENTROID`);
4. `NO_USABLE_GEOMETRY`.

Derived geometry records its scope and inputs in the analysis. It never replaces publisher geometry and is never toilet geometry.

## Lifecycle and defects

Active, inactive/deleted, pending/new/revise values are retained at source level. Complex status is derived only as an aggregate (`ACTIVE`, `MIXED`, `PENDING`, `SOURCE_DELETED`, `UNRESOLVED`) and does not delete historical nodes. Missing member parents, missing area parents, duplicate/invalid relationship elements, invalid identities and cycles are explicit defect classes. Affected nodes/subgraphs are isolated; no missing area or parent is fabricated.

## Identity and replay

The stable source identity is the publisher root StopArea identity. Child nodes retain `naptan:<ATCOCode>` and child areas retain `naptan-stop-area:<StopAreaCode>`. Source ordering does not affect identity or output ordering. A future N4 ingest must use `(source_namespace, source_place_identity, source_revision)`/equivalent deterministic keys and reject conflicting duplicate identities.

## Canonical boundary

The normalized complex may later be reconciled to a Relief facility, but it never is one by definition. Facility creation, linking, and canonical updates require a separately authorized gate. Supporting-only, ambiguous, conflict, and unresolved source entities remain source evidence.

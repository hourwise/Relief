# NaPTAN N3 Canonical Reconciliation Contract

This is a future, declarative contract only. `TOTAL PRODUCTION MUTATIONS: 0` for N3.

## Boundary

**A NaPTAN transport complex is not a canonical Relief facility.** It is an authoritative external source entity that may be linked to, proposed beside, or kept separate from a canonical facility.

## Evidence ordering

Strong evidence, in order:

1. an existing authoritative `facility_sources` link;
2. a future TfL/RDG/other source identifier cross-reference;
3. a curated human adjudication record;
4. exact publisher identity already recorded in a governed source registry.

Medium evidence:

1. exact normalized complex name;
2. compatible mode and area type;
3. bounded geometry against the canonical place;
4. hierarchy-consistent child StopPoint/StopArea evidence.

Weak evidence includes proximity only, partial names, and generic words such as “Station”. Weak evidence cannot create or link a canonical facility by itself.

## Outcomes

The deterministic reconciliation result is one of:

- `EXISTING_CANONICAL_MATCH`
- `PROPOSED_CANONICAL_MATCH`
- `AMBIGUOUS_CANONICAL_MATCH`
- `PROPOSED_NEW_TRANSPORT_PLACE`
- `SUPPORTING_SOURCE_ONLY`
- `CONFLICT`
- `NO_ACTION`

`PROPOSED_*` results are declarative and require separate authorization. A source complex with several child areas produces one root candidate plus preserved subplace evidence, not one facility per node.

## New-facility gate

A future proposal must have a stable publisher identity, meaningful transport-place type, usable source status, resolved complex root, no blocking hierarchy defect, enough location evidence, no high-confidence existing canonical match, and no unresolved duplicate candidate. Missing geometry, unresolved parent references, conflicting identities, and peer-area ambiguity fail closed.

## Idempotency and conflict

Use the source namespace and publisher root identity as the idempotency key. Never use row order or a generated UUID as source identity. Replaying identical source bytes must produce zero duplicate links. Changed source revision is an observation/update event, not a new canonical facility. Conflicting candidates remain `CONFLICT` or `AMBIGUOUS_CANONICAL_MATCH`; no arbitrary nearest-neighbour tie break is allowed.

## Canonical write boundary

No N3 operation may insert/update `facilities`, `facility_sources`, `facility_source_observations`, or any public API object. A later migration/apply transaction must separately define authorization, RLS, audit trail, rollback, and pre/post row-count invariants.

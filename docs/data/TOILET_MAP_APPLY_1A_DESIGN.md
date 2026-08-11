# Relief Apply Engine 1A Design

**Status:** simulation only; no live data changes permitted

**Approved review commit:** `4710b9ec7a9f5a83aa9e7225400b8a6046ce0e77`

**Approved plan SHA-256:** `7400626bc99061af7ba82c29969fc8929d7394c59afcfe574e1880521bad2b45`

**Apply 1A manifest SHA-256:** `1de1a71186b80ce043b48fc5f4d6c4bc6ed9d1c964b3ddf7ad3b96ddd073bfa0`

**Approved source checksum:** `F6824FDC7CD29DF8C1F45BA749C1B28D319FB34803C55459BBE748EF65937624`
**Supabase project:** `bgwxrxkmyaihplaloely`

## Approved scope

Apply Engine 1A freezes exactly the 48 Review 1 entries whose category is
`would_enrich_existing`, whose action is `AUTO_ENRICH`, whose confidence is
`HIGH`, whose current value is null, whose proposed value is a boolean, and
whose matching basis is `EXACT_SOURCE_ID`.

The allowlist is limited to:

| Field | Operations |
|---|---:|
| `has_baby_changing` | 16 |
| `requires_radar_key` | 14 |
| `is_gender_neutral` | 15 |
| `is_accessible` | 2 |
| `is_free` | 1 |
| **Total** | **48** |

Each immutable operation records its facility ID, canonical source name,
source record ID, approved source checksum, source update timestamp, target
field, expected null value, proposed boolean, exact-ID basis, confidence,
reason, approved review commit, and a provenance template. Operation IDs and
the manifest hash are deterministic from the frozen plan.

## Enforced exclusions

The engine rejects entries outside the approved category/action/confidence
scope and rejects fields involving names, coordinates, address, town,
postcode, or opening hours. It has no execution path for:

- the 29 proposed new facilities;
- the 17 absent source IDs;
- the Hemsby source-link decision;
- the two possible duplicate records;
- the quarantined coordinate-corruption record;
- conflicts or manual-review entries;
- source lifecycle, publication-status, stale-state, or deletion operations.

The code does not contain a database mutation client. Its only live network
operation is an authenticated Supabase REST `GET` for the selected facilities
and source links.

## Read-only preflight

The current development project was queried immediately before and after the
simulation. All 48 operations were READY:

- facility exists: 48/48;
- exact `Toilet Map UK` source link identifies the facility: 48/48;
- source link is current: 48/48;
- live source timestamp is not newer than the approved source evidence: 48/48;
- target field remains null: 48/48;
- no stronger or uninterpretable target-field provenance: 48/48;
- stale/precondition failures: 0.

Existing source-link timestamps are older than the approved source snapshot,
which is expected for an enrichment run. A newer live timestamp than the
approved evidence would make that operation stale; an older timestamp does
not invalidate the exact source identity.

## Provenance handling

The live schema uses `public.facilities.field_provenance` as a JSONB object
keyed by facility field. Existing values are per-field objects such as
`source`, `field`, and `at`. The future write must copy that object and replace
only the approved target field with the same per-field object shape extended
with:

- Toilet Map UK source name and source record ID;
- source update timestamp;
- approved source snapshot checksum;
- observed `import_run_id`;
- field name;
- previous and new values;
- `EXACT_SOURCE_ID` decision basis;
- Apply 1A policy version;
- transaction timestamp.

Unrelated field-provenance keys are preserved. Stronger provenance is a hard
precondition failure; it is never overwritten. The current schema is safe for
this in-memory merge simulation. No migration is created or deployed.

## Future transaction design

A future live implementation, subject to a separate approval, should:

1. verify the exact project, source checksum, plan hash, manifest hash, and
   policy version;
2. begin one transaction;
3. revalidate every facility, exact source link, null target field, source
   recency, and provenance precondition inside that transaction;
4. update only the approved scalar and merge only its provenance key;
5. record per-operation evidence and verify affected-row counts;
6. commit atomically.

Any unexpected failure must roll back the complete run. Apply Engine 1A does
not open this transaction and does not create an audit row.

## Idempotency

The in-memory proof shows:

- first simulated run: 48 hypothetical changes;
- repeating the same manifest after those hypothetical changes: 0 additional
  changes and 48 explicit idempotent no-ops;
- a changed plan/source/engine identity fails manifest validation;
- a partial failure restores the original in-memory state.

## Audit design and remaining blocker

`public.import_runs` is the suitable parent for a future enrichment run and
already supports source identity, checksum, status, row counts, and error
summary. It does not have dedicated fields for approved plan hash, manifest
hash, policy version, or rollback state. Those values must not be hidden in an
unrelated column. A future live Apply 1A therefore needs an approved audit
schema decision or migration, plus an explicit live-apply review.

## Evidence

- Manifest: `TOILET_MAP_APPLY_1A_MANIFEST.json`
- Simulation JSON: `TOILET_MAP_APPLY_1A_SIMULATION.json`
- Simulation report: `TOILET_MAP_APPLY_1A_SIMULATION.md`
- Engine: `tools/enrichment/apply_engine_1a.py`
- Synthetic tests: `tools/enrichment/test_apply_engine_1a.py`

The simulation ended with:

```text
SIMULATED_ONLY
DATABASE_MUTATIONS_COMMITTED = 0
```

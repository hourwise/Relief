# Toilet Map Apply 1A — read-only live preflight

**SIMULATED_ONLY. GET-only evidence. No database transaction was opened.**

Captured 2026-08-11 at `2026-08-11T16:40:32.507135+00:00` against Supabase
project `bgwxrxkmyaihplaloely` using the existing Apply Engine REST GET path.
The engine fetched the relevant state twice immediately and compared the
before/after snapshots.

## Frozen identities

- Review commit: `4710b9ec7a9f5a83aa9e7225400b8a6046ce0e77`
- Plan SHA-256: `7400626bc99061af7ba82c29969fc8929d7394c59afcfe574e1880521bad2b45`
- Manifest SHA-256: `1de1a71186b80ce043b48fc5f4d6c4bc6ed9d1c964b3ddf7ad3b96ddd073bfa0`
- Source SHA-256: `F6824FDC7CD29DF8C1F45BA749C1B28D319FB34803C55459BBE748EF65937624`
- Apply Engine version: `relief.apply-engine-1a.v1`

## Current result

| Measure | Result |
|---|---:|
| Requested operations | 48 |
| READY | 48 |
| STALE / precondition failures | 0 |
| Source links found | 48 |
| Target provenance entries already present | 0 |
| Persistent facility/source differences | 0 |
| Before snapshot SHA-256 | `8d4d910af231a0a083316ee299678442b3e396a558d6a411d3109e92bfe764f1` |
| After snapshot SHA-256 | `8d4d910af231a0a083316ee299678442b3e396a558d6a411d3109e92bfe764f1` |
| Live mutations committed | 0 |

The accompanying JSON contains all 48 operation results, including facility
ID, exact source record ID, field, current value, proposed value, precondition
checks, exact source link, and observed target provenance.

## Existing importer audit reference

All 48 source links reference the existing completed importer run:

```text
run_id:         143e2b77-05b7-4415-aa29-0ea0f05190f4
source_name:    Toilet Map UK
source_file:    normalised.csv
source_checksum:24a3655f01f03596f3427c9b4af8c752bc0844eb8dbd66c066b04a82e1c2d40f
status:         completed
rows_received: 15584
rows_valid:    15584
rows_inserted: 15480
rows_unchanged:104
```

This historical importer checksum is not the approved Apply 1A source
snapshot checksum. No Apply 1A audit row exists because the audit migration
has not been deployed and no live apply was attempted.

## Safety statement

```text
LIVE_DATABASE_MUTATIONS = 0
MIGRATIONS_DEPLOYED = 0
LIVE_APPLY_EXECUTIONS = 0
```

This is a preflight only. It does not claim that any approved field or
provenance entry has been changed.

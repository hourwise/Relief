# Toilet Map Apply 2A existing-facility preparation plan

> This is a proposed execution package only. No Apply 2A operation was executed.

- Candidate operations: `22`
- Source version: `2026-08-18T01:00:00+00:00`
- Source checksum: `5600358ce06ca5dfdc0060968b26e8c9e05a1cb5c9dbe0455cdf3951f480ad7f`
- Production project: `bgwxrxkmyaihplaloely`
- Canonical mutations: `0`
- Production mutations: `0`

## Included future candidates

Only the 22 deterministic `APPLY_SOURCE` boolean enrichments are included. Each candidate has an exact target facility, exact source record, expected current canonical value, source checksum, and a required read-only preflight guard.

## Excluded decisions

The 98 `KEEP_CANONICAL`, 2 `PROTECTED`, and 10 `DEFER_EXTERNAL_VERIFICATION` decisions are not execution candidates. New facilities, stale candidates, quarantined rows, and deferred source omissions are outside this package and remain excluded.

## Required future gates

1. Obtain a separate explicit authorization for Apply 2A execution.
2. Re-read production and verify every target facility, source link, canonical value, provenance value, source version, and checksum.
3. Abort on any target drift, provenance drift, source drift, duplicate/collision signal, or failed guard.
4. Execute only through the separately approved apply path with auditable transaction and postcheck evidence.

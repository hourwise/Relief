# Toilet Map Refresh 2 — Proposed Apply 2 Plan

> **PROPOSED / NOT AUTHORIZED FOR PRODUCTION EXECUTION**

This plan is a deterministic review artifact. It does not add an `--apply` option, invoke Apply 1A, create import staging, create an import run, deploy SQL, or mutate production.

- Source checksum: `5600358ce06ca5dfdc0060968b26e8c9e05a1cb5c9dbe0455cdf3951f480ad7f`
- Generating commit: `623d07d`
- Canonical mutations: `0`

## Classification policy

- `SAFE_CANDIDATE`: exact source identity, explicit boolean enrichment, canonical value unknown, and no stronger provenance.
- `REVIEW_REQUIRED`: source/canonical conflict, unsupported material enrichment, inferred identity, or new-facility candidate.
- `REVIEW_DEFERRED`: source omission is retained as evidence but is not an Apply 2 candidate because unknown is not a clear instruction.
- `PROTECTED`: a proposed value would overwrite stronger Relief/community/staff/governed provenance.
- `QUARANTINED`: malformed, unusable, duplicate-identity or bad-name record.
- `STALE_CANDIDATE`: previous accepted source-linked record absent from the fresh source; preserve the canonical facility by default.

Every operation in the JSON manifest contains the target facility, stable source ID, field, before/after values, source checksum/version, current provenance, reason, confidence, and review/auto-apply flags.

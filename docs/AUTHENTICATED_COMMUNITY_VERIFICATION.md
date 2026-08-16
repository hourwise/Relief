# Authenticated Community Verification

**Date:** 2026-08-16
**Branch:** `codex/toilet-map-apply-1a-production-deploy`
**Starting committed SHA:** `cd6318025ebceb86a3ef3684d29e798bac6e0b75`
**Production project:** `bgwxrxkmyaihplaloely`

This was a bounded live verification, not a production schema change. One
disposable confirmed Auth account was used. Its community rows and profile
were removed, the Auth user was deleted, and the final read-only check found
zero marker rows and the original two Auth users. No credentials, user IDs or
facility IDs are recorded here.

## Results

| Flow | Result | Boundary |
|---|---|---|
| Profile/display name | VERIFIED | Auth metadata and profile update/readback passed. |
| Favourites | VERIFIED | Own create/read/delete passed; anonymous and other-user writes were denied. |
| Facility submission | BLOCKED | Own create/read passed, but reviewer fields accepted client values. |
| Temporary report | BLOCKED | Own create/read passed; own resolution returned denial. |
| Correction | BLOCKED | Own create/read passed, but reviewer fields accepted client values. |
| Access code | BLOCKED | Own create returned denial; update was unavailable. |
| Rate-limit records | VERIFIED (bounded) | Three own records/readback passed; other-user insertion was denied. This does not make client-side counting server-side abuse prevention. |
| Governed badges | VERIFIED (bounded) | Direct badge INSERT, UPDATE and DELETE were denied; a governed Explorer award was read back after a genuine facility submission. |

Anonymous writes to favourites, facility submissions, temporary reports and
corrections were denied. Other-user profile readback was not exposed. The
canonical facility was read only. Existing deployed badge triggers,
thresholds, RLS and schema were not changed.

## Source change

The obsolete client `checkAndAwardBadge()` helper and its non-fatal direct
`user_badges` insert side effects were removed from
`src/services/community.ts`. `getUserBadges()` remains a read-only client
path. `__tests__/communityIntegration.test.ts` asserts that the service no
longer contains a direct badge insert while retaining badge readback.

## Explicitly out of scope

No migration, RLS policy change, Edge Function, Storage upload, photo
processing, OAuth configuration, review-write contract, RevenueCat setup,
remote push setup, source import, OSM data, canonical facility mutation, or
account-deletion backend work was performed.

The self-elevation and own-report-resolution findings require a separate
approved design and deployment review. They must not be hidden by changing
the client status or by applying an ad-hoc production policy.

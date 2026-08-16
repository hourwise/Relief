# Authenticated Community Verification

**Date:** 2026-08-16
**Branch:** `codex/toilet-map-apply-1a-production-deploy`
**Starting committed SHA:** `abfe4bfc2d4a5f616a245d2c3028cf58ab1dc6d9`
**Production project:** `bgwxrxkmyaihplaloely`

This was a bounded live verification followed by the approved production
community-contract hardening migration. Two disposable confirmed Auth accounts
(A/B) were used only for owner and cross-user isolation checks. Their community
rows, profiles and Auth accounts were removed. The final read-only cleanup
query found zero marker rows in the tested community tables, zero favourites,
zero user badges, and the original two Auth users. No credentials, user IDs or
facility IDs are recorded here.

## Hardening deployment

The correction was committed and pushed before production mutation:

- correction commit: `35bf8e4c034a9465976e84f0b20f3de308a8509d`
- local migration file: `supabase/migrations/20260816205543_community_contract_hardening.sql`
- live migration id: `20260816210130` (`community_contract_hardening`)

Only these four contracts were changed:

1. `facility_submissions`: authenticated inserts are owner-bound and
   pending-only; status, reviewer, review timestamp and rejection fields are
   excluded from authenticated column grants.
2. `correction_requests`: authenticated inserts are owner-bound and
   pending-only; moderation fields are excluded from authenticated column
   grants.
3. `temporary_reports`: direct authenticated updates were removed. Owners use
   `resolve_own_temporary_report(uuid)`, a fixed-search-path SECURITY DEFINER
   RPC that changes only the owner’s expiry fields and is idempotent.
4. `access_codes`: direct authenticated writes were removed. Owners use
   `upsert_own_access_code(uuid,text,text)`, a fixed-search-path SECURITY
   DEFINER RPC that derives the actor from `auth.uid()` and cannot set
   verification state.

All four tables remain RLS-enabled and not forced. The two new RPCs are
executable by `authenticated` only (plus their owner role); anonymous,
`service_role`, and public execute privileges were revoked. Generated
Supabase TypeScript types were refreshed from the live schema and include both
RPC signatures.

## Results

| Flow | Result | Boundary |
|---|---|---|
| Profile/display name | VERIFIED | Auth metadata and profile update/readback passed. |
| Favourites | VERIFIED | Own create/read/delete passed; anonymous and other-user writes were denied. |
| Facility submission | VERIFIED | A normal owner insert returned 201; approved/rejected/reviewer/other-owner attempts returned 403; B could not alter A’s row. |
| Temporary report | VERIFIED | A created and resolved its own report through the RPC; repeat resolution was idempotent; B received a false result and direct broad updates returned 403. |
| Correction | VERIFIED | A normal owner insert returned 201; approved/reviewer/other-owner attempts returned 403; B could not alter A’s row. |
| Access code | VERIFIED | A owner upsert/create/update and readback passed; direct insert, self-verification and B cross-owner writes returned 403; B’s own upsert passed. |
| Rate-limit records | VERIFIED (bounded) | Three own records/readback passed; other-user insertion was denied. This does not make client-side counting server-side abuse prevention. |
| Governed badges | VERIFIED (bounded) | Direct badge INSERT, UPDATE and DELETE were denied; a governed Explorer award was read back after a genuine facility submission. |

Anonymous writes to favourites, facility submissions, temporary reports and
corrections were denied. Other-user profile readback was not exposed. The
canonical facility was read only. Existing deployed badge triggers,
thresholds and badge security were unchanged; RLS on all four hardened tables
remained enabled. The client still reads governed badges and does not write
`user_badges`.

## Source change

The obsolete client `checkAndAwardBadge()` helper and its non-fatal direct
`user_badges` insert side effects were removed from
`src/services/community.ts`. `getUserBadges()` remains a read-only client
path. `__tests__/communityIntegration.test.ts` asserts that the service no
longer contains a direct badge insert while retaining badge readback.

## Cleanup and advisor boundary

The post-test production cleanup counts were zero for marker rows in
`facility_submissions`, `temporary_reports`, `correction_requests`,
`access_codes`, `rate_limits` and `user_profiles`; zero for `favourites` and
`user_badges`; and exactly two Auth users remained. The two disposable users
were deleted successfully.

The post-migration security advisor reported existing out-of-scope findings
for `toilet_map_import_staging`, mutable search paths on pre-existing helper
functions, public PostGIS objects/functions, account-deletion/subscription
functions, and leaked-password protection. No unrelated advisor finding was
changed in this batch; `spatial_ref_sys` and source/import infrastructure
remain outside the approved scope.

## Explicitly out of scope

No additional migration, Edge Function, Storage upload, photo processing,
OAuth configuration, review-write contract, RevenueCat setup, remote push
setup, source import, OSM data, canonical facility mutation, or
account-deletion backend work was performed. Account deletion remains governed
by its separately approved contract; no new destructive behavior was
introduced here.

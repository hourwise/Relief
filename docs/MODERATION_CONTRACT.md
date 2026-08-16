# Relief Governed Moderation Contract

**Status:** SOURCE IMPLEMENTED / PRODUCTION GATED
**Date:** 2026-08-16
**Production project audited:** `bgwxrxkmyaihplaloely`
**Source-only migration:** `supabase/migrations/20260816220000_governed_moderation_contract.sql`

This document is the current design authority for community moderation. The
moderation migration and service wrapper are local source only. They have not
been applied to Supabase, no production moderator has been created, and no
production contribution has been approved, rejected, verified, revoked or
copied into the canonical facility table.

## Existing production contract discovered

The read-only production audit found these relevant tables:

| Table | Current moderation-relevant state |
|---|---|
| `facility_submissions` | Contributor-owned pending queue with `pending`, `approved`, and `rejected` status values; `reviewed_at`, `reviewed_by`, and `rejection_reason` already exist. |
| `correction_requests` | Contributor-owned pending queue with `pending`, `approved`, and `rejected` status values; `reviewed_at` and `reviewed_by` exist, but no rejection-reason column exists in production. |
| `access_codes` | Owner-derived upsert contract and `is_verified` current state; no moderator verification function or verification-history table exists. |
| `review_reports` | `review_id`, `user_id`, `reason`, and `created_at`; it has an authenticated owner INSERT policy, but no review table was found behind `review_id`. |
| `photo_moderation` | Pending/approved/rejected/reported state and owner/report fields exist; Storage and media processing remain outside this batch. |
| `facilities` | Canonical rows include `publication_status`, `verification_status`, `field_provenance`, `created_by`, `location`, and source/import-derived verification fields. |
| `user_profiles` | Profile and subscription fields only; no role or moderator field. |

No authoritative moderator, admin, role, permission, or staff table existed.
The only table matching a broad “role-like” name was `photo_moderation`, which
is content state rather than identity authorization.

Current live access is therefore asymmetric:

- ordinary authenticated users can read their own submissions/corrections and
  submit pending contributions;
- anonymous users cannot moderate;
- authenticated users cannot update moderation fields;
- the existing `service_role` policy can view and update facility submissions,
  but there is no narrow moderator RPC or server-derived reviewer contract;
- `reviewed_by` has no existing server-side population mechanism;
- facility approval currently has no trigger or function that creates a
  canonical facility;
- correction approval currently does not apply to `facilities`;
- access-code verification currently has no moderator mechanism;
- facility rejection reasons are retained; correction rejection reasons are
  not currently represented;
- no moderation event/history table exists;
- the canonical source/provenance fields make an ungoverned community copy or
  arbitrary correction unsafe.

The production audit also found no `reviews` table. The existing
`review_reports.review_id` therefore points to an unavailable/stale product
contract rather than to an active review system.

## Moderator authorization model

The local design introduces `public.relief_moderators` with:

- a database-generated row id;
- a unique `user_id` reference to `auth.users`;
- an `active` flag;
- creation and update timestamps;
- no grants or client RLS policy that permits direct reads or writes.

The private `private.relief_require_moderator()` function derives the caller
from `auth.uid()` and checks active membership in that table. It does not read
user metadata, email addresses, request fields, hidden navigation state, or
local feature flags. A moderator row must be created by a separately approved
authenticated database operation; there is no self-enrolment RPC.

The public moderation RPCs are executable by `authenticated` only. That
execute grant does not make an ordinary user a moderator: every RPC performs
the server-side membership check and raises `42501` when it fails. Anonymous,
public, and `service_role` execute privileges are explicitly revoked. The
mobile client never receives a service-role credential.

## Facility-submission lifecycle

The local contract provides:

1. `list_moderation_facility_submissions()` — returns pending rows only after
   moderator authorization.
2. `moderate_facility_submission(uuid, decision, rejection_reason)` — permits
   only `pending → approved` or `pending → rejected`.

Rejection requires a non-empty reason. The function derives `reviewed_by` from
`auth.uid()` and sets `reviewed_at` inside the database transaction. Approved
and rejected rows are terminal; replaying either decision is rejected. Row
locking prevents concurrent reviewers from both changing the same pending
row.

Approval is moderation-only in this batch. It does not insert or update
`public.facilities`, change `publication_status`, change
`verification_status`, alter `field_provenance`, or create a source marker.

## Canonical-facility boundary

The selected local policy is **A: approval marks a reviewed contribution only**.
Canonical creation/application is explicitly not implemented because the
current provenance model does not yet define:

- a community source identifier;
- duplicate detection against imported facilities;
- canonical field validation and required-field policy;
- generated canonical IDs;
- how imported versus community provenance is represented;
- rollback when a canonical write partially succeeds;
- idempotency for repeated approval;
- how a correction’s stale `old_value` is handled under concurrency.

Any future policy B implementation must use a single governed transaction and
an explicit field allowlist. It must never accept an arbitrary column name and
value from the client.

## Correction lifecycle

The local contract provides:

1. `list_moderation_correction_requests()` — returns pending rows only after
   moderator authorization.
2. `moderate_correction_request(uuid, decision, rejection_reason)` — permits
   only `pending → approved` or `pending → rejected`, derives reviewer and
   review time, and preserves the submitted old/new values.

The source-only migration adds a narrow `rejection_reason` column to the local
proposed schema. It has not been deployed, so the production generated types
and live schema remain unchanged.

Correction approval is also a reviewed record only. No canonical column is
interpreted or updated. Consequently there is no applicable canonical field
allowlist in this batch; a future apply path must introduce one before any
correction can affect `facilities`.

## Access-code verification lifecycle

The local contract provides:

1. `list_moderation_access_codes()` — returns unverified codes to an authorized
   moderator only.
2. `moderate_access_code(uuid, 'verify' | 'revoke')` — derives the reviewer,
   updates only `is_verified` and `updated_at`, and records the transition in
   `access_code_verification_history`.

Verification is idempotent: repeating the current state does not create a
duplicate history row. Revocation makes the code non-public again. The owner
continues to see their own code under the existing owner-read policy; public
reads remain limited to verified codes attached to published facilities.

The existing owner upsert does not enforce a database uniqueness constraint on
`(facility_id, user_id)`, so multiple rows remain possible at schema level and
the current owner RPC updates the earliest matching row. Whether Relief wants
one owner code or multiple codes per facility is an unresolved product
decision, not silently changed here.

## Review reports and photos

`review_reports` is classified **STALE / DEFERRED**: the report-write table
exists, but no canonical review table or review-write workflow exists. This
batch does not invent review submission, review deletion, report resolution, or
review moderation.

`photo_moderation` is **OUT OF SCOPE**. The local authorization model is
compatible with future photo moderation, but this batch does not create
Storage buckets, upload files, process EXIF, blur faces, or expose photo
moderation operations.

## UX and service boundary

No moderator screen was added. There is no safe existing admin surface, and a
web/internal admin portal is the recommended long-term interface. The local
`src/services/moderation.ts` wrapper calls only the governed RPC names and is
not routed from the mobile navigation. Hiding a route is not treated as a
security boundary.

## Local migration and security-definer design

The source-only migration adds:

- `relief_moderators` with no client grants;
- `access_code_verification_history` with no client grants;
- local `correction_requests.rejection_reason`;
- one private moderator-membership helper;
- three queue-read RPCs;
- four narrow moderation RPCs;
- authenticated-only execute grants for the public RPCs.

Every privileged function uses `SECURITY DEFINER` only where required and
sets `search_path = pg_catalog, public`. Relations are schema-qualified,
reviewer identity is derived from `auth.uid()`, decisions are explicit, and
ordinary authenticated users cannot supply ownership or reviewer identities.

## Production gate

No production action was taken. A separate approval would be required to:

- review the exact migration diff and apply it;
- decide whether the local correction rejection field is accepted;
- nominate and create production moderator memberships;
- regenerate Supabase types from the deployed schema;
- run disposable ordinary-user/moderator authorization tests against live
  RPCs;
- decide and implement any future canonical facility application path;
- decide access-code uniqueness and account-deletion treatment for moderation
  history;
- design a real review table and review-report moderation workflow.

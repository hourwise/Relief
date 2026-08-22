# Relief account-deletion contract

Status: `DEPLOYED — GUARDED FOR ACCOUNTS WITH SUBSCRIPTION HISTORY`

Production status: the guarded migration and `delete-account` Edge Function
are deployed to the Relief production project. Accounts with any row in
`user_subscriptions` or `subscription_events` fail closed with
`SUBSCRIPTION_RETENTION_UNRESOLVED` before destructive cleanup begins.

This document records the deletion inventory verified against the current
Relief Supabase schema and the deployed implementation in this branch. A
disposable Auth account was used for the live verification; existing users
and canonical facility/source data were not modified.

## Security boundary

The mobile client sends only the typed confirmation `DELETE MY ACCOUNT` to the
`delete-account` Edge Function. It never sends a target user ID. The Edge
Function verifies the bearer JWT with Supabase Auth, derives the subject from
the verified user, requires a recent sign-in, cleans Storage through the
Storage API, invokes `public.delete_my_account_data()` through a client bound
to that same user JWT, and calls `auth.admin.deleteUser(subject)` last.

The database function has no arguments and derives `auth.uid()` itself. It is
`SECURITY DEFINER` only because it must delete across RLS-protected tables; its
`search_path` is empty, all relations are schema-qualified, anonymous and
public execution are revoked, and only `authenticated` receives EXECUTE. It
does not delete `auth.users`; that operation is restricted to the server-only
Admin API in the Edge Function.

The request body rejects every field other than `confirmation`, including
`user_id` and `target_user_id`. The Edge Function does not trust client
metadata or a client-supplied identity.

## Moderator-reference reconciliation

The deployed deletion path was live-tested with a disposable moderator who had
reviewed another disposable user's facility submission and correction request
and had verified that user's access code. The moderator was deleted through
the `delete-account` Edge Function, not through a direct Auth Admin call.

The database cleanup first sets `reviewed_by` on retained facility submissions
and correction requests, and `reported_by` on retained photo-moderation rows,
to `NULL`. It also clears `facilities.created_by` attribution. Owned rows are
then deleted, while retained rows keep their status, review timestamp,
submitted values, rejection reason, and other non-identity history. The
`relief_moderators.user_id` membership cascades; retained
`access_code_verification_history` rows keep their action and timestamp while
`moderator_id` is set to `NULL`.

The earlier failed disposable test used `auth.admin.deleteUser` directly while
reviewer references still existed, so it bypassed this deployed cleanup path.
That was a test-harness bypass, not production function drift. The current
deployed migration, SQL functions, and Edge Function were audited and matched
the local contract; no successor migration was required.

## Live schema deletion inventory

The inventory below was read from the current Relief project schema. Counts at
inspection time were two Auth users, two profiles, zero user contributions,
zero subscriptions/events, zero photo-moderation rows, zero badges, zero
Storage buckets, and zero Storage objects. The zero counts do not remove any
resource from the design: the function handles rows if they exist later.

| Resource | Relationship / current FK | Action | Mechanism | Rationale and retry behaviour |
|---|---|---|---|---|
| `auth.users` | Supabase Auth identity; referenced by all user FKs | `DELETE` | Edge Function `auth.admin.deleteUser(subject)` | Performed only after data and Storage cleanup. If it fails, the result is `AUTH_DELETE_FAILED` and the user can retry while the Auth row still exists. |
| `user_profiles` | `id → auth.users.id ON DELETE CASCADE` | `DELETE` | SQL cleanup function | Explicit deletion makes the pre-Auth result deterministic; retry is a no-op. |
| `access_codes` | `user_id → auth.users.id ON DELETE CASCADE` | `DELETE` | SQL cleanup function | User-owned contribution data; retry is a no-op. |
| `correction_requests` | `user_id → auth.users.id ON DELETE CASCADE`; `reviewed_by → auth.users.id NO ACTION` | `DELETE` owned rows; `ANONYMISE` reviewer reference | SQL cleanup function | Deletes the user's requests but clears `reviewed_by` references first so moderation history does not block Auth deletion. |
| `facility_reports` | `user_id → auth.users.id ON DELETE CASCADE` | `DELETE` | SQL cleanup function | User-owned report data; retry is a no-op. |
| `facility_submissions` | `user_id → auth.users.id ON DELETE CASCADE`; `reviewed_by → auth.users.id NO ACTION` | `DELETE` owned rows; `ANONYMISE` reviewer reference | SQL cleanup function | Deletes the user's pending/submitted records and clears reviewer identity without deleting moderation history. |
| `temporary_reports` | `user_id → auth.users.id ON DELETE CASCADE` | `DELETE` | SQL cleanup function | User-owned temporary report data; retry is a no-op. |
| `favourites` | `user_id → auth.users.id ON DELETE CASCADE` | `DELETE` | SQL cleanup function | User preference data; retry is a no-op. |
| `saved_profiles` | `user_id → auth.users.id ON DELETE CASCADE` | `DELETE` | SQL cleanup function | User-owned saved preferences; retry is a no-op. |
| `user_badges` | `user_id → auth.users.id ON DELETE CASCADE` | `DELETE` | SQL cleanup function | Derived user data; retry is a no-op. Governed award triggers are not changed. |
| `rate_limits` | `user_id → auth.users.id ON DELETE CASCADE` | `DELETE` | SQL cleanup function | Operational user row; retry is a no-op. |
| `review_reports` | `user_id → auth.users.id ON DELETE CASCADE`; `review_id` has no confirmed canonical review table in the current schema | `DELETE` | SQL cleanup function | User-submitted report metadata is deleted; no review row is deleted. |
| `photo_moderation` | `user_id → auth.users.id ON DELETE CASCADE`; `reported_by → auth.users.id NO ACTION` | `DELETE` owned rows; `ANONYMISE` reporter reference | SQL cleanup function plus Storage API | Deletes the user's moderation row and clears reporter identity. Storage URLs are not treated as proof of an object; actual owned objects are removed through Storage API first. |
| `subscription_events` | `user_id → auth.users.id ON DELETE CASCADE` | `DELETE` for the current schema | SQL cleanup function | The current project has no approved accounting-retention/audit policy or active subscription rows. This classification must be reviewed before production activation if RevenueCat/accounting retention becomes real. |
| `user_subscriptions` | `user_id → auth.users.id ON DELETE CASCADE` | `DELETE` for the current schema | SQL cleanup function | No current rows and no approved provider-retention policy. Revisit before RevenueCat production activation. |
| `facilities.created_by` | `created_by → auth.users.id ON DELETE SET NULL` | `ANONYMISE` attribution | Existing FK plus explicit SQL update | Canonical facilities remain available; the deleted user's ownership attribution is removed. |
| `facility_sources`, `import_runs`, `toilet_map_import_staging` | No FK to `auth.users`; source/import operational records | `RETAIN` | No deletion action | These are canonical/source provenance records, not account-owned records. Source refresh remains review-only. |
| `storage.objects` | Storage metadata has `owner`/`owner_id`; no current buckets or objects | `DELETE` owned objects when present | Edge Function Storage API `remove`, batches of 1,000 | SQL never deletes Storage objects. Inventory/removal failure stops before database cleanup; partial removal is returned as retryable. A bounded 50,000-object safety limit surfaces an exceptional case instead of silently truncating. |
| Auth/session history and audit records | No dedicated Relief account-deletion audit table; Auth-managed records are not exposed as app rows | `RETAIN` only as platform-managed operational history | Supabase Auth/platform | The Edge Function logs only a request ID and outcome, not email or raw user data. A future legal/audit-retention decision may add a minimised pseudonymous audit table. |

## Subscription-history guard

The current production schema keeps `user_subscriptions.user_id` and
`subscription_events.user_id` as required links to `auth.users`, and no
approved retention or de-identification policy exists for those records.
Therefore automated account deletion is intentionally fail-closed for any
authenticated user with a row in either table.

The guard runs before Storage or application cleanup and returns
`SUBSCRIPTION_RETENTION_UNRESOLVED`. It performs no application cleanup, no
Storage deletion, and no Auth Admin deletion. The SQL cleanup function repeats
the guard immediately before its destructive statements. Neither subscription
table is deleted or de-identified by this contract.

This is a temporary product limitation while RevenueCat and paid entitlements
remain inactive. Subscription retention is not solved by this guard; users
with subscription or payment-event history require a separately governed
support/data-request path until the long-term retention design is approved.

## Failure and retry contract

1. Invalid method, missing/invalid JWT, unsupported body fields, invalid
   confirmation, or stale authentication fails before destructive work.
2. Storage objects are inventoried and removed through the Storage API before
   database deletion. Storage errors return `STORAGE_CLEANUP_FAILED` and
   `retryable: true`.
3. The SQL cleanup function runs in one database transaction. Any SQL error
   rolls back all of its row changes and returns `DATA_CLEANUP_FAILED`.
4. Auth admin deletion is last. If it fails after data cleanup, the response
   is `AUTH_DELETE_FAILED`, `partial: true`, and `retryable: true`; a retry is
   safe because the row cleanup and Storage removal are idempotent.
5. A successful response is returned only after the Auth admin deletion
   succeeds. The mobile client then removes its local session.

## Source files

- `supabase/migrations/20260814135046_account_deletion_cleanup_contract.sql`
- `supabase/functions/delete-account/contract.ts`
- `supabase/functions/delete-account/index.ts`
- `src/services/accountDeletion.ts`
- `src/screens/AccountDeletionScreen.tsx`
- `__tests__/accountDeletion.test.ts`

The production path is deployed with the migration, Edge Function secrets,
function grants, Storage behaviour, and Auth admin path verified. The legal
retention policy remains unresolved for accounts with subscription history;
those accounts are blocked with `SUBSCRIPTION_RETENTION_UNRESOLVED` until the
retention and anonymisation decisions are approved separately.

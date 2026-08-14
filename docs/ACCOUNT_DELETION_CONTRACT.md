# Relief account-deletion contract

Status: `CONTRACT_ONLY — PRODUCTION DELETION NOT CONFIGURED`

This document records the deletion boundary visible in the current live-schema
baseline. It is not an authorization to delete data and does not implement an
Edge Function, migration, Storage cleanup, or Auth admin call. The mobile
adapter remains `ACCOUNT_DELETION_NOT_CONFIGURED` in production.

## Required deletion invariant

An account deletion request must be authenticated as the requesting user and
must not accept an arbitrary target user ID. A future trusted server-side
function must require recent authentication plus an explicit confirmation,
perform the operation with its server-only admin credential, and return an
auditable outcome without exposing that credential to the mobile app.

## Current auth-user row inventory

The classifications below describe the current schema, not final legal policy.
`NO ACTION` foreign keys are deliberately not changed in this batch.

| Data category / relation | Current relationship | Contract classification | Reason / required follow-up |
|---|---|---|---|
| `access_codes.user_id` | `ON DELETE CASCADE` | `DELETE` | User-owned access-code contribution; cascade is already defined. |
| `correction_requests.user_id` | `ON DELETE CASCADE` | `DELETE` | User-owned correction request; cascade is already defined. |
| `facility_reports.user_id` | `ON DELETE CASCADE` | `DELETE` | User-owned report; cascade is already defined. |
| `facility_submissions.user_id` | `ON DELETE CASCADE` | `DELETE` | User-owned submission; cascade is already defined. |
| `favourites.user_id` | `ON DELETE CASCADE` | `DELETE` | User-owned preference; cascade is already defined. |
| `photo_moderation.user_id` | `ON DELETE CASCADE` | `DELETE` | User-owned moderation submission row; actual object cleanup remains unresolved because Storage has no bucket in the baseline. |
| `rate_limits.user_id` | `ON DELETE CASCADE` | `DELETE` | Operational anti-abuse row; cascade is already defined. |
| `review_reports.user_id` | `ON DELETE CASCADE` | `DELETE` | User-owned report row; the referenced canonical review table is not confirmed in this baseline. |
| `saved_profiles.user_id` | `ON DELETE CASCADE` | `DELETE` | User-owned saved profile; cascade is already defined. |
| `subscription_events.user_id` | `ON DELETE CASCADE` | `UNRESOLVED` | The FK cascades today, but accounting, tax, fraud, and entitlement-retention treatment requires an explicit legal/product decision before relying on deletion as the final policy. |
| `temporary_reports.user_id` | `ON DELETE CASCADE` | `DELETE` | User-owned temporary report; cascade is already defined. |
| `user_badges.user_id` | `ON DELETE CASCADE` | `DELETE` | Derived gamification row; cascade is already defined. |
| `user_profiles.id` | `ON DELETE CASCADE` | `DELETE` | Account profile row; cascade is already defined. |
| `user_subscriptions.user_id` | `ON DELETE CASCADE` | `UNRESOLVED` | Current cascade exists, but subscription history and provider identifiers need retention/anonymisation policy. |
| `facilities.created_by` | `ON DELETE SET NULL` | `SET NULL` | Public facility ownership attribution is removed while the canonical facility remains. |
| `correction_requests.reviewed_by` | `ON DELETE NO ACTION` | `UNRESOLVED` | A deleted moderator/reviewer can block Auth deletion. Decide `SET NULL` or an approved anonymised audit principal before enabling deletion. |
| `facility_submissions.reviewed_by` | `ON DELETE NO ACTION` | `UNRESOLVED` | Same blocker; decide `SET NULL` or an approved anonymised audit principal. |
| `photo_moderation.reported_by` | `ON DELETE NO ACTION` | `UNRESOLVED` | Same blocker; decide `SET NULL` or an approved anonymised audit principal. |
| Future `storage.objects` owned by a user | No bucket/policy exists in baseline | `NOT_APPLICABLE` for current data; `UNRESOLVED` for future | No Storage object exists to clean in this batch. Any future object-key ownership convention and cleanup order must be designed before enabling deletion. |

## Current `NO ACTION` blockers

The three reviewer/reporter references above can prevent deletion of
`auth.users` if they contain the target user. The deletion function must not
silently disable constraints, delete reviewer history, or guess an audit
policy. These references need a reviewed schema/legal decision first.

## Future trusted deletion architecture

1. The authenticated client requests deletion without supplying a target user
   other than the session identity and supplies the explicit typed confirmation.
2. A trusted Edge Function validates the JWT, checks recent-auth/confirmation,
   and derives the target from the authenticated subject.
3. The function uses its server-only service-role credential to resolve the
   approved `NO ACTION` policy, remove or anonymise rows in a transaction, and
   delete future user-owned Storage objects using a bounded key prefix.
4. Only after dependent rows/objects are handled does it call the Auth admin
   deletion operation for that same user.
5. It records a minimal auditable result (request ID, actor subject hash or
   approved pseudonym, timestamps, outcome, and failure category) without
   retaining unnecessary raw personal data.

No client-callable `SECURITY DEFINER` function may accept an arbitrary user ID,
and no service-role credential may be bundled into Expo variables or mobile
code.

## Decisions required before implementation

1. Should `subscription_events` and `user_subscriptions` be deleted,
   anonymised, or retained for an identified legal/accounting purpose?
2. Should the three `NO ACTION` reviewer/reporter foreign keys become
   `ON DELETE SET NULL`, or should a documented anonymised audit principal be
   introduced?
3. What exact audit record, if any, must be retained after deletion, for what
   purpose, and with what minimisation/pseudonymisation rule?
4. When Storage is introduced, what object-key ownership convention and
   deletion retry/audit policy will govern user-uploaded objects?

Until these decisions are recorded and reviewed, implementing destructive
deletion would be unsafe. This batch therefore stops at the contract boundary.

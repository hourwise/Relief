# Governed badge award contract

Status: `FORWARD MIGRATION PREPARED — NOT DEPLOYED`

## Existing product contract found

The mobile service currently defines these four badge types and thresholds:

| Badge | Existing condition | Existing invocation |
|---|---|---|
| `explorer` | At least one `facility_submissions` row for the user | Called after a facility submission |
| `community_hero` | At least five `temporary_reports` rows for the user | Called after a temporary report |
| `accessibility_champion` | At least three corrections whose `field` is one of the accessibility fields | Eligibility helper exists but is not currently invoked by the mobile service |
| `family_helper` | At least three corrections whose `field` is one of the baby/family fields | Eligibility helper exists but is not currently invoked by the mobile service |

The current client checks counts and then attempts to insert into
`user_badges`. RLS has no authenticated INSERT policy, so the insert is
blocked and wrapped as a non-fatal side effect. The baseline table also lacks
the `source` column that the client attempts to send.

## Forward backend path

`supabase/migrations/20260814113440_governed_badge_awards.sql` adds the missing
server-derived `source` field and a trigger-only `SECURITY DEFINER` function in
the private schema. The function accepts no user ID or badge type. Each trigger
passes the `user_id` from a real inserted contribution row, and the function
derives all four badge decisions from database state. There is no client-callable
award RPC and no authenticated badge-write policy.

The three triggers cover facility submissions, temporary reports, and
correction requests. Awards use the existing `(user_id, badge_type)` unique
constraint, `ON CONFLICT DO NOTHING`, and a per-user transaction advisory lock
so retries and concurrent threshold-crossing writes are idempotent.

## Security properties

- RLS remains enabled on `user_badges` and its public read policy is unchanged.
- `anon` and `authenticated` retain SELECT only; direct INSERT/UPDATE/DELETE is
  revoked.
- The trigger function has a hardened `search_path` and explicit execution
  revocation from client roles.
- No service-role credential is introduced into the app or an Expo variable.
- The trigger derives the contributor from `NEW.user_id`; callers cannot select
  an arbitrary victim or badge type.
- Null contributor IDs return without awarding anything.

## Cutover sequence

1. Review and test the migration against a disposable database.
2. Deploy the migration through the approved production review process.
3. Confirm the trigger awards, duplicate idempotency, client write denial, and
   public badge reads.
4. In a later mobile source change, remove the now-redundant client-side award
   side effects while keeping the primary contribution result unchanged.

Until that sequence is complete, the mobile service is intentionally unchanged:
its optional award attempt remains non-fatal and production-compatible while
the forward migration is undeployed.

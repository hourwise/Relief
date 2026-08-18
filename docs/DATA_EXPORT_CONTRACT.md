# Relief governed user data export contract

Status: `GOVERNED USER DATA EXPORT — LIVE DEPLOYED / VERIFIED`

This document describes the governed `Download my data` implementation and
its bounded production verification. The `export-account` Edge Function is
deployed with JWT verification enabled. No production migration was required;
the live test used two generated disposable accounts and removed them after
verification.

## Boundary and architecture

The mobile client sends an empty JSON object to the server-only
`export-account` Edge Function. The function verifies the bearer JWT, derives
the subject from `authData.user.id`, and requires recent authentication using
the same 15-minute helper as account deletion. The request body rejects every
field, including `user_id`, `target_user_id`, and `email`.

The function uses the server-only service-role credential internally to make
explicit, user-scoped reads. It returns a versioned JSON envelope immediately;
it does not write a file, persist an export, use public Storage, or mutate any
database row. The mobile Profile action passes the returned JSON to the native
share sheet. No service-role credential reaches the mobile bundle or response.

The live deployment uses the normal Supabase server-side secrets and retains
JWT verification. Protected moderation-summary data remains explicitly
omitted where unavailable through the current export data source; no
moderation security controls were weakened to include it.

## Export inventory

The inventory was derived from the current Relief production schema on project
`bgwxrxkmyaihplaloely` and from the current application source.

| Resource | Decision | Export treatment and rationale |
|---|---|---|
| Supabase Auth identity | `EXPORT_REDACTED` | Own ID, email, account creation time, email-confirmed time, and a safe display name only. Raw metadata, provider data, tokens, sessions, and password material are excluded. |
| `user_profiles` | `EXPORT` | Own user-facing profile fields, including display name, avatar reference, and current profile entitlement fields. |
| `favourites` | `EXPORT_REDACTED` | Own facility references and creation times, plus bounded public facility context: ID, name, address, town, postcode, and publication status. |
| `saved_profiles` | `EXPORT` | Own mode, name, preferences, and creation time. |
| `facility_submissions` | `EXPORT_REDACTED` | Own submitted fields and moderation outcome/rejection reason. `user_id` and `reviewed_by` are not returned, and submitted photo JSON is reduced to a bounded `photo_count`. |
| `facility_reports` | `EXPORT` | Own report type, reason, notes, expiry, creation time, and bounded facility context. |
| `temporary_reports` | `EXPORT` | Own report type, notes, expiry state, creation time, and bounded facility context. |
| `correction_requests` | `EXPORT_REDACTED` | Own old/new values, notes, status, review time, and rejection reason. Reviewer identity is omitted. |
| `access_codes` | `EXPORT_REDACTED` | The user’s own code is exported verbatim because it is user-provided account-linked data; its facility context and verification state are included. Other users’ codes are never queried. This remains a privacy/security consideration for later product review. |
| `review_reports` | `EXPORT_REDACTED` | Own report reason and creation time only. The stale `review_id` target is omitted because no active review table exists. |
| `photo_moderation` | `EXPORT_REDACTED` | Own moderation row status and processing flags are included. Photo URLs, storage object names, and third-party metadata are excluded; Storage is not enabled. |
| `user_badges` | `EXPORT` | Own badge type, award time, and governed source. |
| `rate_limits` | `DO_NOT_EXPORT` | Internal abuse-control/security metadata is not personal-access data needed by the user. |
| `relief_moderators` | `SUMMARY_ONLY` | Only the requester’s own active moderator role and assignment timestamps are represented when the protected source is available; the private roster is never exposed. If unavailable, the export explicitly discloses that some internal moderation activity is omitted. |
| `access_code_verification_history` | `SUMMARY_ONLY` | Only the requester’s own verification action and timestamp are included when the protected source is available. If unavailable, the export explicitly discloses that some internal moderation activity is omitted. Other users’ codes, IDs, and contribution content are omitted. |
| `user_subscriptions` | `EXPORT_REDACTED` | Own structured entitlement and lifecycle dates are included. Provider IDs and raw provider payloads are excluded. |
| `subscription_events` | `EXPORT_REDACTED` | Own event type, tier transition, and creation time are included. `details`, `revenuecat_event_id`, and raw provider payloads are excluded. No retention/legal decision is made here. |
| `facilities.created_by` | `EXPORT_REDACTED` | Bounded attribution only: canonical facility ID, public name/address/town/postcode, creator association, and creation time. `field_provenance`, source rows, and import internals are excluded. |
| Retained `reviewed_by` / `reported_by` references | `SUMMARY_ONLY` | Own review/report activity is represented by outcome and time without exporting another contributor’s row or identity. |
| Canonical facilities unrelated to the requester | `DO_NOT_EXPORT` | Public discovery data is not a personal export dump; unrelated canonical rows are excluded. |
| Source/import tables and provenance | `DO_NOT_EXPORT` | Full import datasets, source-review metadata, and operational internals are unrelated to the requester’s personal data. |
| `storage.objects` and photo files | `DO_NOT_EXPORT` | Storage is not currently enabled; no file is inventoried, copied, or exported. |
| Auth sessions, refresh/access tokens, password hashes, provider secrets | `DO_NOT_EXPORT` | Authentication and security secrets never enter the response. |

No other current public table with an Auth-linked `user_id`, `reviewed_by`,
`reported_by`, `moderator_id`, or `created_by` reference was found in the
inventory audit.

## Versioned JSON envelope

The response uses stable field names and returns empty arrays/nulls for absent
categories rather than omitting sections:

```json
{
  "export_version": 1,
  "generated_at": "2026-01-01T00:00:00.000Z",
  "account": {},
  "profile": null,
  "favourites": [],
  "saved_profiles": [],
  "contributions": {
    "facility_submissions": [],
    "reports": [],
    "temporary_reports": [],
    "corrections": [],
    "access_codes": [],
    "photo_moderation": [],
    "review_reports": []
  },
  "badges": [],
  "subscriptions": {
    "current": null,
    "events": [],
    "provider_payloads": "excluded"
  },
  "moderation_activity": {
    "role": "none",
    "availability": "complete",
    "limitation": null,
    "review_actions": [],
    "verification_actions": [],
    "photo_reports": []
  },
  "canonical_attribution": [],
  "excluded": []
}
```

When protected moderation-summary sources are unavailable to the current
export architecture, the response remains successful for the core export but
uses `role: null`, `availability: "partial"`, and the user-facing limitation
`Some internal moderation activity is not currently included in this export.`
This distinguishes unavailable information from a confirmed absence of
moderation activity without exposing protected table names or security
configuration.

The `excluded` field is an explicit human-readable reminder of categories that
are intentionally outside the export. It is not a promise about legal
retention periods or a substitute for approved public privacy wording.

## Mobile delivery

The signed-in path is `Profile → Privacy & Data → Download my data`. The native
share sheet receives the generated JSON text. If sharing is unavailable, the
app reports that condition without claiming that a file was saved. Guests are
sent to authentication instead of receiving an export.

In Relief test mode, the action is clearly labelled as a deterministic
synthetic example and reports that no production data was read. Test mode does
not fabricate a successful production export.

## Required later production gate

Before deployment, separately review the explicit query allowlist, Edge
Function JWT configuration, service-role secret handling, the decision to
export a user’s own access-code text, structured subscription fields, and the
public privacy/data-rights wording. A production test must use an approved
account and confirm cross-user exclusion without changing any data.

# Relief Supabase pause/reactivation handoff

## Capture boundary

This handoff was captured on 2026-08-23 as part of Release Closure R2. It is a read-only operational snapshot for the Relief production Supabase project. The project was not paused by this task, and no production data, schema, authentication, storage, policy, grant, Edge Function, or migration state was changed.

The repository checkpoint at the start of R2 was:

- Repository: `hourwise/Relief`
- Branch: `codex/toilet-map-apply-1a-production-deploy`
- Local and remote SHA: `7c47930149728548e12ef99b5c0b0b0063fac9c8`
- Supabase project: `Relief`
- Supabase ref: `bgwxrxkmyaihplaloely`
- Region: `eu-central-1`

## Production identity and runtime

The read-only Supabase project inspection identified the intended Relief project as `ACTIVE_HEALTHY` with PostgreSQL `17.6.1.127` (engine 17). The deployed migration ledger head is `20260822170000` (`naptan_transport_source_graph`).

Relevant installed extensions verified read-only:

- PostGIS `3.3.7` in `public`
- pgcrypto `1.3` in `extensions`

No migration is pending in the captured handoff. Do not run `supabase link`, `supabase db push`, or any other deployment command while the project is paused. The next operator should use the normal linked-project dry run only after the project is active again.

## Production row-count snapshot

The following counts were captured with read-only SQL and are a baseline for post-reactivation verification:

| Table | Rows |
| --- | ---: |
| `facilities` | 15,620 |
| `facility_sources` | 15,634 |
| `facility_source_observations` | 14 |
| `import_runs` | 5 |
| `toilet_units` | 0 |
| `toilet_unit_sources` | 0 |
| `transport_source_snapshots` | 1 |
| `transport_source_places` | 97,270 |
| `transport_source_nodes` | 436,428 |
| `transport_source_memberships` | 169,527 |
| `transport_source_place_parents` | 3,519 |

The NaPTAN source graph total is 706,745 rows. This is source evidence, not a facility or toilet count.

## Security and backend surface

The five NaPTAN source tables have RLS enabled, zero policies, zero direct `anon` grants, zero direct `authenticated` grants, and service-role-only direct table grants. The source graph therefore remains private to the governed backend access path.

The read-only policy inventory also confirmed the expected application boundary:

- Published `facilities` and `facility_sources` are publicly readable through their existing read policies.
- `facility_submissions` accepts authenticated owner submissions and has service-role moderation policies; it has no public grants.
- `temporary_reports` has authenticated submission and active-report read policies; it has no public grants.
- `correction_requests` has authenticated owner insert/read policies; it has no public grants.
- `favourites` is authenticated-owner scoped.
- `toilet_units` is publicly readable only through its published-read policy and has no direct public table grant.
- No storage buckets were returned by the read-only storage metadata query.

The deployed Edge Function inventory contains only:

- `delete-account` — active, JWT verification enabled
- `export-account` — active, JWT verification enabled

No Edge Function was invoked or changed during R2.

## Application handoff

The application can continue to be developed while Supabase is paused, provided development stays within local/mock/static boundaries. The following remain safe to work on offline:

- layout, navigation, accessibility, copy, and local validation;
- deterministic unit tests and TypeScript changes;
- local QA builds that do not expect live authentication, database reads, payments, exports, or deletion;
- the public website and its legal/support content, independently of the API.

The Internal Testing preview configuration is deliberately non-billing:

```text
EXPO_PUBLIC_RELIEF_TEST_MODE=true
EXPO_PUBLIC_PAYMENTS_ENABLED=false
EXPO_PUBLIC_QA_PREMIUM_OVERRIDE=true
```

In that state the app uses a QA-only entitlement source, does not initialize real billing, and disables purchase/restore actions. The override is only active when `RELIEF_TEST_MODE` is also true. The committed `.env.example` defaults all three switches to safe false values.

The following require the project to be active again and should not be treated as verified while it is paused:

- Supabase Auth registration, login, password reset callback, profile reads, favourites, and community submissions;
- read/write access to published facilities and source data;
- account export and account deletion Edge Functions;
- any moderation workflow or governed RPC;
- live app smoke tests against the production API;
- any future schema or data deployment.

## Public website status

The exact required public routes were checked in the in-app browser and each returned a non-empty Relief page over HTTPS:

- [Home](https://findrelief.co.uk/)
- [Privacy](https://findrelief.co.uk/privacy)
- [Terms](https://findrelief.co.uk/terms)
- [GDPR](https://findrelief.co.uk/gdpr)
- [Delete account](https://findrelief.co.uk/delete-account)
- [Support](https://findrelief.co.uk/support)
- [Contact](https://findrelief.co.uk/contact)
- [Data & sources](https://findrelief.co.uk/data)

The website was classified `RELIEF_WEBSITE_LIVE_VERIFIED`. This verifies reachability and route content, not legal approval of the copy.

## Reactivation checklist

After the user pauses and later resumes the project:

1. Confirm the active project is still `Relief` / `bgwxrxkmyaihplaloely` in `eu-central-1`.
2. Confirm project health is `ACTIVE_HEALTHY` and PostgreSQL/PostGIS are available.
3. Run `supabase db push --dry-run --linked`; require `Remote database is up to date.`
4. Confirm migration head remains `20260822170000` and no unexpected migration is pending.
5. Recheck the baseline counts above, especially the five source-graph tables and the canonical tables.
6. Recheck RLS, policies, and direct grants for the source graph; require no public/anon/authenticated direct write path.
7. Re-test Auth, password reset callback, account export, and account deletion in a controlled non-production test plan before relying on them.
8. Keep payments disabled until a separately authorized billing configuration and store-test plan exists.
9. Only then run the relevant read-only app smoke tests.

## R2 safety statement

R2 did not ingest data, create community production test rows, create payments or RevenueCat transactions, submit to Google Play, build an APK, pause Supabase, or change production. Total production mutations: **0**.

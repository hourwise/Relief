# Relief — Backend Test Build Plan

**Created:** 2026-07-24  
**Status:** PLANNED  
**Purpose:** Define the smallest safe build path for connecting enough backend infrastructure to test Relief with real development data.

This is a tactical companion to `docs/BACKEND_INTEGRATION_PLAN.md`. It does not replace the broader staged integration plan. The target here is a development-only test loop, not production readiness.

---

## Target Test Outcome

The first useful backend test should prove:

- a development Supabase project is connected;
- a test user can sign in;
- verified seed facilities can be queried from Supabase;
- the map/detail journey can render real facility records;
- unverified/private rows are not exposed by Row Level Security.

Do not use this plan to launch public community features, payments, photo uploads, push notifications, what3words, or production user data.

---

## Dependency Answer

`npm install` installs the packages already declared in `package.json`. That is enough for the current repository dependencies.

One additional npm dependency should be added when fixing Supabase Auth for React Native:

```bash
npm install react-native-url-polyfill
```

Reason: the current Supabase client uses `@supabase/supabase-js` in a React Native app, but the client setup does not include the URL polyfill normally required by Supabase React Native auth examples.

No additional npm packages are needed for the first Supabase data/auth test because these are already present:

- `@supabase/supabase-js`
- `@react-native-async-storage/async-storage`
- `expo-secure-store`
- `expo-location`
- `expo-sqlite`
- `react-native-maps`
- `react-native-purchases`

Tooling and accounts are separate from npm dependencies:

| Need | Required for first backend test? | Notes |
|---|---:|---|
| Node.js 18+ on PATH | Yes | Verify with `node -v`, `npm -v`, and `npx expo --version`. |
| Supabase project | Yes | Development project only. Do not use production data. |
| Supabase CLI | Optional | Use if applying migrations from CLI. Supabase SQL editor is enough for an initial dev test. |
| Docker Desktop | Optional | Only needed if using local Supabase emulation. |
| Google Maps API key | Needed for Android map rendering | Current code uses `react-native-maps`; Android uses Google provider. |
| Apple Developer / Google Play accounts | No | Not needed for local/dev backend testing. |
| RevenueCat account | No | Keep premium/payment flows disabled. |
| what3words key | No | Do not test W3W until fake fallback is removed. |
| Push credentials | No | Push is outside this first test scope. |

---

## Preflight Checks

Run these after `npm install`:

```bash
node -v
npm -v
npx expo --version
npx tsc --noEmit
```

Expected caveat: prior documentation reports TypeScript errors in Supabase Deno Edge Functions because the local TypeScript runtime does not know Deno globals/imports. App TypeScript should still be checked.

If `node` or `npx` is not found, fix local PATH before continuing.

---

## Decisions Required Before Connecting Services

Resolve or explicitly park these decisions for a development-only test:

1. **D01 Mapping provider:** choose Google Maps for the first test because current code already uses `react-native-maps`.
2. **D02 Unauthenticated discovery:** decide whether to test signed-in only first, or fix the auth gate before testing "Need One Now".
3. **D03 Initial launch/test area:** use one test town. Liverpool is already represented in mock list data.
4. **D04 Seed data source:** use clearly labelled development seed data first; do not present unverified data as public truth.
5. **D08 what3words:** remove or disable simulated W3W before testing location sharing.

---

## Code and Schema Fixes Before Applying Migrations

Do not apply the current migrations to a real project without reviewing these issues.

### 1. Fix `user_badges` schema conflict

`001_initial_schema.sql` creates `user_badges` with a `badge` column. `20260624_community_features.sql` later expects a `badge_type` column.

Because the later migration uses `CREATE TABLE IF NOT EXISTS`, the expected `badge_type` column will not be created if migration 001 has already created the table.

Fix path:

- choose one badge schema;
- prefer the app code shape: `badge_type` and `source`;
- update migration 001 or add an explicit alter migration before deploying.

### 2. Tighten `facilities` RLS

Current migration 001 allows public read of all facilities:

```sql
USING (true)
```

For test and production parity, public reads should be limited to verified facilities:

```sql
USING (is_verified = true)
```

Also remove direct authenticated inserts into `facilities`. User-created facilities should go through `facility_submissions`, not directly into live facility data.

### 3. Resolve `is_picnic_area`

The app type and filters reference `is_picnic_area`, but migration 001 does not define it. Either:

- add `is_picnic_area BOOLEAN DEFAULT false` to `facilities`; or
- remove/disable that filter until the schema owns it.

### 4. Add React Native Supabase auth storage setup

The current client in `src/services/supabase.ts` enables `persistSession`, but does not provide React Native storage.

When implementing the fix:

- install `react-native-url-polyfill`;
- import `react-native-url-polyfill/auto`;
- configure Supabase Auth storage with `@react-native-async-storage/async-storage`;
- keep `detectSessionInUrl: false` for native app usage.

### 5. Rename map env variable

Current config uses `EXPO_PUBLIC_GOOGLE_MAPS_API_KEY` for Android Google Maps via `react-native-maps`.

For the Google Maps test path:

- keep `EXPO_PUBLIC_GOOGLE_MAPS_API_KEY` in local `.env` and EAS environment variables when EAS is introduced;
- keep `app.config.js` / Expo config references aligned with the Android-only MVP setup;
- keep the key restricted by Android package name / SHA-1 and Maps SDK for Android only.

### 6. Enforce feature gates

`FEATURES` is defined in `src/utils/env.ts`, but current usage is not reliable. Before public testing, route access and UI actions should respect the feature gates.

For the first backend test, keep these out of scope:

- premium/paywall purchase flow;
- AI-branded screens;
- offline map/download claims;
- photo uploads;
- public community moderation flow.

### 7. Remove fake location codes

`coordsToWhat3Words()` currently returns simulated words when no W3W key exists. That is unsafe.

For test builds:

- return an unavailable/error state when no W3W key is present;
- do not display fake W3W values;
- keep Plus Codes only if the algorithm is verified or replaced with a trusted implementation.

---

## Supabase Development Setup

### Step 1 — Create development project

Create a Supabase development project under the project-owned account identity when available.

Record only public client values in local `.env`:

```env
EXPO_PUBLIC_SUPABASE_URL=https://your-project.supabase.co
EXPO_PUBLIC_SUPABASE_ANON_KEY=your-anon-or-publishable-key
```

Never put these in client files:

- `SUPABASE_SERVICE_ROLE_KEY`
- database password
- RevenueCat webhook secret
- push credentials
- private API keys

### Step 2 — Apply corrected migrations

Apply corrected migrations in this order:

1. `001_initial_schema.sql`
2. `20260624_community_features.sql`
3. `20260625_premium_features.sql`
4. `20260701_monetisation.sql`

For the first app boot test, the monetisation tables reduce noisy client fallback errors because `SubscriptionProvider` currently checks server-side subscription state.

### Step 3 — Configure auth

For the first test:

- enable email/password auth;
- create one test user manually in Supabase Auth;
- defer Google and Apple OAuth until basic email sign-in is VERIFIED in development.

### Step 4 — Seed verified facilities

Seed 5-20 development facilities in the selected test town.

Minimum fields:

- `name`
- `address`
- `latitude`
- `longitude`
- `postcode`
- `town`
- `country`
- `is_verified = true`
- `overall_score`
- `last_verified_at`
- useful amenity booleans for filters

Keep seed data labelled as test/dev unless it is manually verified.

### Step 5 — Optional storage setup

Skip photo uploads for the first test.

If storage is tested later:

- create `facility-photos` bucket;
- add storage policies;
- implement EXIF stripping;
- implement face blurring;
- keep public display limited to approved, processed photos.

---

## App Test Sequence

1. Start Expo:

   ```bash
   npx expo start -c
   ```

2. Sign in with the manually created test user.
3. Allow foreground location permission.
4. Verify map data:
   - nearby query returns seeded facilities;
   - only `is_verified = true` facilities render;
   - search by town/postcode returns seeded data.
5. Verify facility detail:
   - selecting a marker opens detail;
   - active reports query does not break the screen;
   - directions buttons open platform map URLs.
6. Verify "Need One Now":
   - signed-in test first if auth gate remains;
   - unauthenticated test only after navigation is changed to allow public discovery.
7. Verify RLS manually:
   - anon can read verified facilities;
   - anon cannot read unverified facilities;
   - anon cannot write facilities;
   - authenticated user cannot directly insert live facilities;
   - authenticated user can insert only into allowed moderation tables.

---

## Keep Disabled Until Acceptance Gates Exist

| Feature | Reason to keep disabled |
|---|---|
| Photo uploads | No EXIF stripping, face blurring, storage policy migration, or moderation pipeline yet. |
| Community public trust flows | Rate limiting is client-side only; no admin moderation UI exists. |
| RevenueCat payments | Products, webhook secret, and store configuration are not present. |
| Push notifications | No server-side push sender or background alert path exists. |
| what3words | Current fallback creates fake words. |
| AI-branded recommendations | Current logic is deterministic scoring, not model-backed AI. |
| Europe expansion | UK/test-town data model and seed quality are not VERIFIED. |

---

## Security Checklist For The Test Build

- `.env` remains uncommitted.
- Only public client values use `EXPO_PUBLIC_*`.
- Supabase service role key exists only in Supabase Edge Function/server environment.
- RLS is enabled on every table.
- Public facility reads are limited to verified data.
- Live facility writes are not allowed directly from the client.
- Test seed data does not include private locations or misleading claims.
- Logs do not print secrets, auth tokens, or precise user location history.
- W3W simulation is removed or hidden before any user-facing location-sharing test.

---

## Handoff Criteria

The backend test build can be treated as VERIFIED only when there is evidence for:

- successful email sign-in on device/emulator;
- Supabase query returning seeded verified facilities;
- map/detail journey using Supabase data;
- RLS checks proving unverified data is not public;
- no service role or server-only secret in client config;
- documented failures or deferred items recorded in `CURRENT_STATE.md` / `FEATURE_MATRIX.md` if status changes.

Until then, use **BACKEND-DEPENDENT** or **PLANNED** status vocabulary.

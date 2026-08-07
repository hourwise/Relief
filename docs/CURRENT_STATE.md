# Relief — Current State Assessment

**Last verified:** 2026-08-07
**Branch:** `claude/android-apk-stabilisation` (cut from `feat/figma-ui-refresh`)
**Verification method:** Live Supabase project queried directly (PostgreSQL 17.6) via `psql` and the anonymous REST endpoint; repository quality gates run locally; **release APK built, installed and driven on a physical Samsung Galaxy S24 Ultra with no Metro running.**

| Check | Command | Result |
|-------|---------|--------|
| Node | `node --version` | v24.12.0 |
| Install | `npm ci` | Passed — 583 packages |
| Expo doctor | `npx expo-doctor` | **21/21 checks passed** |
| Lint | `npm run lint` | **0 errors**, 92 warnings (ESLint + Prettier now configured) |
| TypeScript | `npx tsc --noEmit` | **0 errors** |
| Tests | `npm test` | **10 files, 453 assertions, all passing** |
| Public config | `npx expo config --type public` | Resolves; `com.relief.app`, SDK 56.0.0 |
| Android prebuild | `npx expo prebuild --platform android --clean` | Succeeded |
| APK build (local) | `gradlew assembleRelease -PreactNativeArchitectures=arm64-v8a` | **BUILD SUCCESSFUL** — `app-release.apk`, 48.8 MB, arm64-v8a, JS bundle embedded |
| APK build (EAS) | `eas build -p android --profile preview` | **NOT RUN** — no EAS project linked |
| Android smoke test | 22 required checks | **22/22 PASS** on a physical S24 Ultra — see `ANDROID_SMOKE_TEST.md` |
| Find UX acceptance test | 20 checks | **20/20 PASS** after the filter, viewport and locate-control pass |
| Signed-in journey | favourites, reports, corrections, sign-out | **PASS**, with database writes confirmed over `psql` and test rows removed afterwards |
| Pre-merge auth gate | audit + device pass | Guest, sign-in, session restoration and sign-out **VERIFIED**; new-account creation and Google OAuth **BLOCKED** on external setup — see `ANDROID_SMOKE_TEST.md` |

---

## Executive Summary

Relief is a React Native / Expo SDK 56 application whose **core discovery journey is now wired to live data end to end at the service layer**, and whose most urgent feature — "Need One Now" — has been repaired and verified against the live database.

What changed in this pass: the nearest-facility RPC was broken and is now fixed and verified; the database schema is now recorded in git for the first time; the mocked Nearby list is gone; discovery no longer requires an account; and the map's viewport loading no longer drops the user's latest pan.

A release APK has now been built, installed on a physical Samsung Galaxy S24 Ultra and driven through all 22 required smoke checks with no Metro or development server running. All 22 pass, as does a full signed-in journey covering favourites, reports, corrections and sign-out, with every database write confirmed over `psql`. Seven defects were found in the process and fixed — most importantly, the map never actually moved to the user location, so it showed the startup fallback while data loaded for somewhere else.

What is still **not** verified: account creation and Google OAuth (sign-in with an existing account was exercised); no EAS build exists; and the Google Maps key restrictions in Cloud Console have not been inspected.

---

## Database — VERIFIED

The live Supabase project was queried directly on 2026-08-06 and again on 2026-08-07.

| Item | Status | Evidence |
|------|--------|----------|
| Schema recorded in git | VERIFIED | **`supabase/` was previously listed in `.gitignore`, so GitHub contained no record of the database at all.** Now tracked, with `supabase/migrations/20260806000000_live_schema_baseline.sql` exported by `pg_dump --schema-only --schema=public` from the running database |
| Facility data | VERIFIED | 15,584 rows, all `publication_status = 'published'`, all with a non-null PostGIS `location` |
| Liverpool coverage | VERIFIED | **76** published facilities with `town` matching Liverpool (an earlier revision of this document claimed 104; that figure was wrong) |
| Anonymous read | VERIFIED | Published facilities readable with the anon key over REST |
| PostGIS | VERIFIED | `geography(Point,4326)` generated column plus `facilities_location_gix` GiST index |
| `find_nearest_facilities` RPC | **VERIFIED (repaired)** | See below |

### The RPC defect and its repair

The live function declared and selected six columns that do not exist on `facilities`:
`is_water_refill_station`, `is_shower_facility`, `is_breastfeeding_room`, `is_rest_area`, `is_changing_place`, `is_ev_charging`.

Every call failed at plan time with `42703 column f.is_water_refill_station does not exist`, which is what broke "Need One Now".

`supabase/migrations/20260806000100_repair_find_nearest_facilities.sql` replaces the function with a narrow, stable projection (id, name, address, coordinates, town, postcode, opening hours, free/paid, primary accessibility, overall score, verification status, distance in metres). **It has been applied to the live project.** Verification, both in-database and through the anonymous REST path the app uses:

```
find_nearest_facilities(53.4084, -2.9916, 5000, 1)
  → Moorfields, Liverpool, 162 m — HTTP 200, no PostgreSQL error
```

`is_picnic_area` does exist in the live schema and is retained on the table. It is not currently offered as a filter, because no published facility sets it — see the coverage note below.

The seven original hand-written migrations no longer describe the live database and have been moved to `supabase/legacy_migrations/` as history only.

### Filter data coverage

The schema carries far more amenity columns than the app offers as filters. Most are unpopulated, so a switch for them would always return nothing — which, to a user, is indistinguishable from a broken service.

Measured on 2026-08-07 across the 15,584 published facilities, these columns have usable coverage and are offered: `is_free` 12,216 (and 3,221 explicitly paid), `is_accessible` 6,374, `has_baby_changing` 4,889, `requires_radar_key` 2,453, `is_gender_neutral` 1,766, `is_24h` 984, `has_staff_nearby` 829, `is_family_friendly` 291. A further 6,718 rows carry `open_hours`, which is what makes the client-derived "Open now" filter meaningful.

**Every other amenity column measured 0**, as did `overall_score > 0` — so no facility is rated, and the minimum-rating selector was removed. Those columns are deliberately kept in the schema and listed in `HIDDEN_UNTIL_POPULATED` in `src/utils/filterDefinitions.ts`, with a test asserting they stay hidden. They can be offered again once ingestion or community contributions populate them.

---

## Application — VERIFIED on device

| Area | Status | Detail |
|------|--------|--------|
| Schema/type reconciliation | VERIFIED (compile-time) | `Facility` and `FacilityFilters` are **derived** from generated types in `src/types/database.types.ts`. `FILTERABLE_BOOLEAN_COLUMNS` uses `satisfies`, so naming a column the database lacks is now a compile error rather than a runtime 42703 |
| Generated types | VERIFIED | Generated from live `pg_catalog` by `tools/generate-database-types.mjs` (`npm run gen:types`). `supabase gen types` needs Docker, which is unavailable on this machine |
| Filters | VERIFIED on device | Only filters the live data can answer are offered, from one definition module shared by UI and query. Six phantom columns cannot be referenced at all (compile error); 26 real-but-unpopulated columns are hidden with their measured counts recorded. Cost is tri-state; the rating selector is gone while 0 facilities are rated |
| Mocked Nearby list | REMOVED | `MOCK_FACILITIES` and `ListScreen.tsx` deleted |
| Shared Find experience | VERIFIED on device | `FindScreen` + `useFindExperience` give the map and list one shared source of location, facilities, search, filters, loading/error state and selection. Map/List switching preserves viewport, filters and selection — the map captures the shared region when it mounts, so a return from List resumes where it left off rather than replaying the startup fallback |
| Map viewport loading | VERIFIED on device | Latest-request-wins via a request sequence plus a queued newest region. The previous code skipped fetches while a request was in flight *and* left `inFlightRef` stuck `true` on its early-return path, which could stall loading permanently |
| Runtime error states | VERIFIED on device | Distinct states for initial location loading, facility loading, permission denied, location unavailable, query failure, no facilities in area, and nearest-RPC failure. A failed query never renders as "no facilities found" |
| Guest discovery | VERIFIED on device | Root navigator renders the app with or without a session. Policy centralised in `src/utils/guestAccess.ts` and covered by 68 assertions. Authentication is requested only for favourites, submissions, corrections, reports and account settings |
| Onboarding | VERIFIED on device | Stored against a guest key when signed out and migrated on sign-in. The migration is awaited before the completion check — doing it in the auth listener raced that check and re-prompted a guest who had already finished |
| Navigation | VERIFIED on device | Three tabs (Find, Favourites, Profile) with Lucide icons. Unfinished features removed from Profile; a static audit confirms no reachable button targets an unregistered route |
| Facility detail | VERIFIED on device | Redesign preserved. The Lucide `Star` SVG is no longer nested inside a `<Text>` (a native view inside `Text` does not lay out reliably on Android). Nullable `overall_score` handled. Reports and corrections require authentication |
| Directions | VERIFIED on device | Coordinate deep links to Google Maps and Waze |
| Native splash / StartupWelcome | VERIFIED on device | Mint splash with the Relief mark, no white flash; welcome layer dismisses and does not reappear |

### Test coverage

`npm test` runs 8 files without a device or database:

| File | Assertions | Covers |
|------|-----------|--------|
| `distance.test.ts` | 18 | Distance calculation and metres/kilometres formatting; asserts no output uses miles; cross-checked against the PostGIS 162.08 m result |
| `facilityQuery.test.ts` | 40 | Filter-to-database-column mapping and nearest-facility result mapping, including that the six phantom columns cannot be filtered and that unusable rows are rejected rather than defaulted |
| `facilitySort.test.ts` | 11 | List sorting, with null and zero ratings sinking rather than ranking first |
| `guestAccess.test.ts` | 68 | Guest navigation decisions across the whole discovery journey |
| `estimateWalkingTime.test.ts` | 10 | Walking-time calculation |
| `onboardingPreferences.test.ts` | 2 | Onboarding preference selection |
| `onboardingMigration.test.ts` | 13 | Guest→user onboarding migration over an in-memory AsyncStorage, including the ordering contract whose violation re-prompted signed-in users |
| `reportTypes.test.ts` | 45 | Report type labels and durations, including that no label is the raw enum and that an unknown type is de-slugged rather than shown raw |

---

## External services

| Service | Status | Detail |
|---------|--------|--------|
| Supabase | VERIFIED for reads | Anonymous reads of published facilities and the repaired RPC both confirmed against the live project. Auth, storage and Edge Functions remain unverified |
| Google Maps (Android) | BACKEND-DEPENDENT | Key resolves through `app.config.js`; the prebuilt `AndroidManifest.xml` carries `com.google.android.geo.API_KEY` exactly once. **Key restrictions in Google Cloud Console are unverified** — package, signing SHA-1 and Maps SDK enablement all still need checking |
| EAS Build | PLANNED | `eas.json` defines an installable internal `preview` APK profile. No `projectId` is linked and the Expo login has two accounts, so no build has been started |
| RevenueCat | BLOCKED | No keys; paywall screens unrouted in the preview build |
| what3words | MOCKED — hidden | Returns simulated words. Location sharing is unrouted in the preview build |
| Notifications | BACKEND-DEPENDENT — hidden | No push server; alerts unrouted in the preview build |
| Photo upload / moderation | PLANNED — hidden | No bucket, no processing pipeline |

---

## Feature flags

From `src/utils/env.ts` — unchanged this pass:

| Flag | Value |
|------|-------|
| `COMMUNITY` | `true` |
| `ADVANCED_FILTERS` | `false` |
| `PREMIUM` | `false` |
| `AI` | `false` |
| `EUROPE` | `false` |

Hidden-but-retained screens (AI recommendations, predictive suggestions, route planning, offline maps, notification alerts, location sharing, saved profiles, paywall) still exist in `src/screens/` and compile, but are **not registered in the navigator**, so they are unreachable.

---

## Current blockers

1. **New-account creation is unverified.** Sign-in with an existing account is verified end to end. Creating an account requires typing an email and password, which the assistant does not do — a human must run that path. The live project has `mailer_autoconfirm: false`, so a new sign-up yields no session until the emailed link is opened.
2. **Google OAuth is not configured.** `GET /auth/v1/settings` reports `google: false`, so the provider cannot work at all. The button is now hidden behind `AUTH_PROVIDERS.GOOGLE` rather than failing in front of users. Enabling it needs Google Cloud credentials, SHA-1 registration, Supabase provider setup, a redirect allow-list entry, **and** an app-side deep-link handler that does not yet exist.
3. **Password reset does not exist.** There is no `resetPasswordForEmail` and no "Forgot password?" link, so a user who forgets their password cannot recover the account in-app.
4. **EAS project not linked.** Needs `eas init`, a decision on which Expo account owns it (`hourwiseeu` or `pcgsoft`), and the three `EXPO_PUBLIC_*` values added as `preview` environment variables. The APK under test was built locally instead.
5. **Local APK is debug-signed.** The Expo template signs `release` with the debug keystore (SHA-1 `84:91:66:28:20:F6:70:39:B9:8E:83:A8:4A:2D:86:68:CF:7B:B1:BE`). Fine for an internal preview, not a release artifact, and an EAS build will present a different certificate to the Maps key.
6. **Google Maps key restrictions not inspected.** Tiles render on this device, so the key works for the debug certificate and Maps SDK for Android is enabled — but the Cloud Console restriction list was not reviewed.
7. **Quality gates were run under Node 24.12.0**, while the EAS image uses Node 22. `.nvmrc`, `.node-version` and `engines` now pin 22; re-run `npm ci && npm run verify && npx expo-doctor` under Node 22 before the first EAS build.
8. **9 published facilities have unusable names** (two characters or fewer, or no alphanumerics) from the Toilet Map UK import — one renders as `]` in search results. A data cleanup, not an app defect.
9. **Storage, moderation, notifications, RevenueCat** remain unconfigured; the features that depend on them are hidden rather than finished.
10. **Lint warnings and unrouted-screen debt.** ESLint reports 0 errors but 92 warnings, mostly unused variables inside hidden features. The unrouted screens keep their React Compiler violations as scoped warnings and must be cleared — or those screens deleted — before any of them is registered again. Prettier is configured but has deliberately **not** been run repo-wide, so that a reformat does not bury real changes.
11. **No CI.** The quality gates exist as npm scripts but nothing runs them automatically.
12. **Machine-level `GRADLE_USER_HOME` is misconfigured** — it points inside a scoop-managed Gradle install of a different version, which prevented any Gradle build until overridden. Android Studio inherits this. See `ANDROID_SMOKE_TEST.md`.

---

## Safe next action

Exercise account **creation** and Google OAuth on the device — the two auth paths still unverified. Then, if a shareable build is wanted: `eas init` against the chosen Expo account, add the three `EXPO_PUBLIC_*` values as `preview` environment variables, register the EAS keystore's SHA-1 on the Maps key, and run `eas build -p android --profile preview`. Re-run the quality gates under Node 22 first.

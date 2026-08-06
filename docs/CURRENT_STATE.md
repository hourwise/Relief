# Relief — Current State Assessment

**Last verified:** 2026-08-06
**Branch:** `claude/android-apk-stabilisation` (cut from `feat/figma-ui-refresh`)
**Verification method:** Live Supabase project queried directly (PostgreSQL 17.6) via `psql` and the anonymous REST endpoint; repository quality gates run locally. **No Android build has been installed or opened.**

| Check | Command | Result |
|-------|---------|--------|
| Node | `node --version` | v24.12.0 |
| Install | `npm ci` | Passed — 583 packages |
| Expo doctor | `npx expo-doctor` | **21/21 checks passed** |
| TypeScript | `npx tsc --noEmit` | **0 errors** |
| Tests | `npm test` | **6 files, 149 assertions, all passing** |
| Public config | `npx expo config --type public` | Resolves; `com.relief.app`, SDK 56.0.0 |
| Android prebuild | `npx expo prebuild --platform android --clean` | Succeeded |
| APK build | `eas build -p android --profile preview` | **NOT RUN** — no EAS project linked |
| Android smoke test | 22 required checks | **NOT RUN** — see `ANDROID_SMOKE_TEST.md` |

---

## Executive Summary

Relief is a React Native / Expo SDK 56 application whose **core discovery journey is now wired to live data end to end at the service layer**, and whose most urgent feature — "Need One Now" — has been repaired and verified against the live database.

What changed in this pass: the nearest-facility RPC was broken and is now fixed and verified; the database schema is now recorded in git for the first time; the mocked Nearby list is gone; discovery no longer requires an account; and the map's viewport loading no longer drops the user's latest pan.

What has **not** changed: no APK has been built, installed or opened, so nothing in this document may be read as "the app works on a device". The status of every on-device behaviour is unverified.

---

## Database — VERIFIED

The live Supabase project was queried directly on 2026-08-06.

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

`is_picnic_area` does exist in the live schema and is retained on the table and as a filter.

The seven original hand-written migrations no longer describe the live database and have been moved to `supabase/legacy_migrations/` as history only.

---

## Application — code complete, device-unverified

| Area | Status | Detail |
|------|--------|--------|
| Schema/type reconciliation | VERIFIED (compile-time) | `Facility` and `FacilityFilters` are **derived** from generated types in `src/types/database.types.ts`. `FILTERABLE_BOOLEAN_COLUMNS` uses `satisfies`, so naming a column the database lacks is now a compile error rather than a runtime 42703 |
| Generated types | VERIFIED | Generated from live `pg_catalog` by `tools/generate-database-types.mjs` (`npm run gen:types`). `supabase gen types` needs Docker, which is unavailable on this machine |
| Invalid advanced filters | REMOVED | The six phantom filters are gone from the UI and from the client query map. A regression test asserts they cannot be offered or sent |
| Mocked Nearby list | REMOVED | `MOCK_FACILITIES` and `ListScreen.tsx` deleted |
| Shared Find experience | UI IMPLEMENTED — device-unverified | `FindScreen` + `useFindExperience` give the map and list one shared source of location, facilities, search, filters, loading/error state and selection. Map/List segmented switch |
| Map viewport loading | UI IMPLEMENTED — device-unverified | Latest-request-wins via a request sequence plus a queued newest region. The previous code skipped fetches while a request was in flight *and* left `inFlightRef` stuck `true` on its early-return path, which could stall loading permanently |
| Runtime error states | UI IMPLEMENTED — device-unverified | Distinct states for initial location loading, facility loading, permission denied, location unavailable, query failure, no facilities in area, and nearest-RPC failure. A failed query never renders as "no facilities found" |
| Guest discovery | UI IMPLEMENTED — device-unverified | Root navigator renders the app with or without a session. Policy centralised in `src/utils/guestAccess.ts` and covered by 68 assertions. Authentication is requested only for favourites, submissions, corrections, reports and account settings |
| Onboarding | UI IMPLEMENTED — device-unverified | Stored against a guest key when signed out, migrated to the user on sign-in |
| Navigation | UI IMPLEMENTED — device-unverified | Three tabs (Find, Favourites, Profile) with Lucide icons. Unfinished features removed from Profile; a static audit confirms no reachable button targets an unregistered route |
| Facility detail | UI IMPLEMENTED — device-unverified | Redesign preserved. The Lucide `Star` SVG is no longer nested inside a `<Text>` (a native view inside `Text` does not lay out reliably on Android). Nullable `overall_score` handled. Reports and corrections require authentication |
| Directions | UI IMPLEMENTED — **untested on device** | Coordinate deep links to Google Maps and Waze |
| Native splash / StartupWelcome | UI IMPLEMENTED — **untested on device** | Preserved from the UI branch; needs a release-build visual check |

### Test coverage

`npm test` runs 6 files without a device or database:

| File | Assertions | Covers |
|------|-----------|--------|
| `distance.test.ts` | 18 | Distance calculation and metres/kilometres formatting; asserts no output uses miles; cross-checked against the PostGIS 162.08 m result |
| `facilityQuery.test.ts` | 40 | Filter-to-database-column mapping and nearest-facility result mapping, including that the six phantom columns cannot be filtered and that unusable rows are rejected rather than defaulted |
| `facilitySort.test.ts` | 11 | List sorting, with null and zero ratings sinking rather than ranking first |
| `guestAccess.test.ts` | 68 | Guest navigation decisions across the whole discovery journey |
| `estimateWalkingTime.test.ts` | 10 | Walking-time calculation |
| `onboardingPreferences.test.ts` | 2 | Onboarding preference selection |

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

1. **No APK has been built, installed or opened.** This is the single largest gap. The emulator cannot start on the development machine: the hypervisor check passes, but the userdata partition needs 7,372 MB and `C:` has ~4–5 GB free (99% full). A physical device is the intended route.
2. **EAS project not linked.** Needs `eas init`, a decision on which Expo account owns it (`hourwiseeu` or `pcgsoft`), and the three `EXPO_PUBLIC_*` values added as `preview` environment variables.
3. **Google Maps key restrictions unverified.** Requires Google Cloud Console access. Note the Expo template signs `release` with the **debug** keystore, so a local release APK's SHA-1 differs from an EAS build's.
4. **Auth flows unverified.** Sign-in, registration and OAuth have not been exercised against the live project.
5. **Storage, moderation, notifications, RevenueCat** remain unconfigured; the features that depend on them are hidden rather than finished.
6. **No linting** configured (ESLint/Prettier still absent).
7. **No CI.** The quality gates exist as npm scripts but nothing runs them automatically.

---

## Safe next action

Build and install the preview APK on a physical Android device, then work through `docs/ANDROID_SMOKE_TEST.md` and record real results. Pay particular attention to check 16 — that a nearest-facility RPC failure surfaces as a retryable error and never as "no facilities found" — since that is the specific misdiagnosis this pass set out to eliminate.

# Relief — Current State Assessment

## Governed moderation contract — LIVE DEPLOYED — 2026-08-17

The governed moderation contract is deployed to the Relief production project
in migration `20260817062603 governed_moderation_contract`. It provides
database-backed moderator membership, narrow authenticated-only RPCs, and no
admin screen or canonical-application function. The design authority is
[`MODERATION_CONTRACT.md`](MODERATION_CONTRACT.md).

The design uses database-backed `relief_moderators` membership, narrow
authenticated-only SECURITY DEFINER RPCs, server-derived reviewer identity,
explicit terminal transitions, and no client write path to moderation fields.
Facility and correction approval only records the moderation result; it does
not mutate canonical `facilities`. Access-code verification/revocation has a
small deployed verification-history table. Disposable live verification
identities and rows were removed; no permanent moderator is configured and no
production contribution was changed.

Review reports remain stale/deferred because no review table exists. Photo
moderation remains out of scope. Android/EAS work files remain concurrent and
untouched.

## Phase G feature test readiness — 2026-08-14

Phase G adds the canonical source-derived inventory in [`FEATURE_TEST_READINESS.md`](./FEATURE_TEST_READINESS.md), opt-in `EXPO_PUBLIC_RELIEF_TEST_MODE`, password-reset screens and deep-link handling, a deployed governed account-deletion path, truthful photo/premium boundaries, and a QA Feature Lab. Production Storage, RevenueCat, remote push, OAuth, review writes, and public legal endpoints remain explicitly blocked or unconfigured. Per the user’s instruction, no Phase G APK was produced or installed; the Phase E hermetic APK is the last verified local APK baseline, and Android Studio physical-device testing plus the cloud EAS build are deferred.

## Phase E hermetic Android debug build — 2026-08-13

The Phase E evidence is recorded in
[`RELEASE_PREPARATION_PHASE_E.md`](RELEASE_PREPARATION_PHASE_E.md). The current
checkout passed the source gates, Expo Doctor, public config, and two successful
arm64 debug APK builds from independent fresh Gradle homes. The original React
Native Gradle plugin Kotlin settings error is absent when Gradle uses an
isolated user home. A tracked
[`tools/build-android-debug.ps1`](../tools/build-android-debug.ps1) helper now
selects a valid Android SDK and a dedicated process-local Relief Gradle home.

The debug APK gate is **VERIFIED** for local Android functional testing. This
does not change the existing backend and public-release classifications:
generated types remain **BLOCKED_BY_MISSING_DB_URL**, authenticated writes and
storage remain unverified or blocked as documented, and the deployed account
deletion path remains a public privacy/support release blocker until its public
legal materials are established. The local APK is a debug artifact and is not
a release-signed build.

**Last verified:** 2026-08-13

Current account-deletion status: the governed production backend is deployed
and the normal signed-in Profile entry is available. Public privacy, support,
data-rights, and account-deletion URL work remains a release blocker. See
[`ACCOUNT_DELETION_RELEASE_READINESS.md`](ACCOUNT_DELETION_RELEASE_READINESS.md).
**Branch:** `codex/toilet-map-apply-1a-production-deploy` at
`67eabbf496ecf53948998b7e002dd703beaba0cc`

## Phase B post-Apply integration and Android debug audit — 2026-08-12

The Phase B audit is recorded in
[`RELEASE_PREPARATION_PHASE_B.md`](RELEASE_PREPARATION_PHASE_B.md). The
Supabase client contract hardening is checkpointed at commit
`c9d228f3e796741024eedcd31981149a65b0379c`; badge awarding is now a non-fatal
optional side effect with regression coverage. A clean Expo SDK 56 prebuild
matches the current ignored Android Gradle files, but both clean and current
debug builds stop in the React Native Gradle plugin Kotlin DSL with
`plugins`/`id` unresolved. No native workaround or production mutation was
made, so the debug APK gate remains blocked by local Android toolchain state.

## Phase A post-Apply audit — 2026-08-12

The current Apply-sealed checkout was audited for mobile integration, RLS
compatibility, privacy/deletion readiness, and Android build readiness. The
evidence and release classification are recorded in
[`RELEASE_PREPARATION_PHASE_A.md`](RELEASE_PREPARATION_PHASE_A.md). The audit
made no production mutation; generated types remain refresh-blocked because
the approved generator did not receive `SUPABASE_DB_URL`. The app-side
integration contract/error-handling tests pass, while the local debug APK is
blocked by the React Native Gradle plugin settings failure and public release
is blocked by the unresolved account-deletion/privacy contract.

**Last verified:** 2026-08-11 (fresh short-path Android merge gate)
**Branch:** `claude/android-apk-stabilisation` at `11322abf27d6dd23a708b37e7aad88905d38f2db`
**Verification method:** Fresh clone at `D:\r\relief`, Node `22.22.2`, clean `npm ci`, source gates, Expo SDK 56 public config, Android prebuild, local arm64 release APK assembly, installation on the physical Samsung S24 Ultra, and the current 28-item smoke list. The existing working copy was not modified.

## Fresh short-path Android merge gate - 2026-08-11

The exact remote branch head was verified in a new clone at `D:\r\relief`:
`11322abf27d6dd23a708b37e7aad88905d38f2db`. The clone had no `node_modules`,
`android/`, or `.env` before setup. The local public environment was recreated
without printing or committing values; `.env` remains ignored.

| Gate | Result |
|------|--------|
| Node/npm | **VERIFIED** - Node `v22.22.2`, npm `10.9.7` |
| Source verification | **VERIFIED** - `npm run verify`; 11 test files and 461 assertions passed |
| Expo validation | **VERIFIED** - `npx expo-doctor` 21/21; public config resolved SDK 56 and package `com.relief.app` |
| Native generation | **VERIFIED** - clean Android prebuild; New Architecture setting unchanged |
| Local release build | **VERIFIED** - Expo device selection was non-interactive and the targeted run stalled without an APK; the permitted Gradle fallback succeeded |
| Install | **VERIFIED** - `adb install -r` returned `Success` on the S24 Ultra (`SM_S928B`, serial `R5CX13MZ2YF`) |
| Device smoke | **VERIFIED** - current 28-item guest, map/list/filter, urgent, detail, directions, profile, account handoff, sign-out, and cold-launch checks passed |
| Fatal Android exceptions | **VERIFIED** - 0 fatal matches after the smoke run; the relaunched app process remained alive |

The APK was `android/app/build/outputs/apk/release/app-release.apk`,
49,349,586 bytes, SHA-256
`84FD9ED90BBAC770022252A4CEC3CC4A88383098184C05C3951476B21547A99B`.
The Need One Now ranking source gate remains the authority for open/unknown/
closed ordering (8 assertions passed); the physical run returned a confirmed
open, free nearest candidate using live data.

**Merge decision for this gate: READY TO MERGE TO MAIN.** This is an internal
local-build/device decision only. It does not authorize EAS, production data
enrichment, external-service setup, or a merge/push operation.

Outstanding release setup remains explicit: EAS is **NOT RUN**; production
Supabase Auth, Storage, Edge Functions, moderation and operational setup remain
outside this gate; Google Play, Play App Signing and store submission setup are
**NOT RUN**; account deletion is deployed and reachable from Profile; and
legal/privacy/terms, support contact, and public account-deletion URL setup
remain outstanding.

The older check table below records the superseded 2026-08-10 pre-device state.

| Check | Command | Result |
|-------|---------|--------|
| Node 22 runtime | `node --version` | **PASS** — v22.22.2 used for the focused Node 22 test run |
| Install | `npm ci` | **BLOCKED** — Windows EPERM/non-terminating cleanup; a usable dependency tree was later recovered for direct checks |
| Expo doctor | `npx expo-doctor` | **BLOCKED** — package unavailable in the recovered local tree |
| Lint | direct ESLint on changed files | **PASS** — 0 reported errors; the `expo lint` wrapper rejects the temporary mapped-drive root |
| TypeScript | `tsc --noEmit` from the short mapped path | **PASS** — 0 errors |
| Tests | `tools/run-tests.mjs` | **PASS** — 11 files, 461 assertions |
| Public config | Expo config command | **PASS** — resolves `com.relief.app`, SDK 56.0.0 |
| Android prebuild | not rerun during consolidation | **NOT RUN** — no source regeneration requested |
| APK build (local) | `gradlew assembleRelease -PreactNativeArchitectures=arm64-v8a` | **NOT BUILT** — current-configuration mapped build hit mixed `R:`/`D:` roots in codegen; real-path New Architecture-off diagnostic build stalled during Metro bundling with no release APK |
| APK build (EAS) | `eas build -p android --profile preview` | **NOT RUN** — no EAS project linked |
| Android smoke test | consolidated 28-item gate | **NOT RUN** — no fresh APK was produced or installed; the S24 Ultra became visible to ADB only after the build attempts |
| Find UX acceptance test | 20 checks | **HISTORICAL PARENT BASELINE ONLY** — not rerun on the consolidated branch |
| Signed-in journey | favourites, reports, corrections, sign-out | **HISTORICAL PARENT BASELINE ONLY** — no consolidated APK/device run |
| Pre-merge auth gate | audit + device pass | **HISTORICAL PARENT BASELINE ONLY** — Google OAuth remains **BLOCKED** on external setup; account self-service (reset/delete/rename) is **not built** |

## Final consolidation gate — 2026-08-10

The requested fast-forward consolidation was performed without rewriting history:

| Check | Result |
|-------|--------|
| Remote ref comparison | **PASS** — Luna `065b42c9f9fb5226bcf2221f682a165a70e85757` was 1 commit ahead and 0 behind stabilisation `c54a977958e7f7afcdab3394449d08ba4f3278d9` |
| Consolidated branch | **PASS** — `claude/android-apk-stabilisation` fast-forwarded to Luna and the source/docs gate commits were pushed through `5dce071` |
| Node 22 runtime | **PASS** — `v22.22.2` |
| `npm ci` | **BLOCKED** — npm hit Windows `EPERM` while cleaning the existing native dependency tree and did not terminate cleanly within the bounded retry; the restored tree remained incomplete |
| `npm run verify` | **BLOCKED BY WRAPPER** — TypeScript and direct ESLint passed from the short path, but the Expo lint wrapper rejects the mapped-drive project root; focused tests passed separately |
| Focused tests | **PASS** — 11 files, 461 assertions, including the new Need One Now ranking tests, run with the Node 22.22.2 executable |
| `npx expo config --type public` | **PASS** — resolves Relief, package `com.relief.app`, SDK `56.0.0` |
| `npx expo-doctor` | **BLOCKED BY INSTALL** — the `expo-doctor` package was absent from the incomplete dependency tree |
| Local release APK | **NOT BUILT** — a short-path current-configuration retry reached codegen but failed on mixed mapped/real dependency roots; the consistent real-path New Architecture-off diagnostic build reached native compilation and Metro bundling, then stalled without emitting an APK |
| Consolidated physical-device smoke test | **NOT RUN** — no fresh APK was produced; the 2026-08-07 parent-branch run must not be reused as evidence for this branch |

### Need One Now consolidation fix

The previous implementation asked `find_nearest_facilities` for `result_limit: 1`, so the database-nearest row was returned even when it was confirmed closed. The consolidated implementation requests up to 25 candidates within the existing 25 km ceiling, reads `is_24h` only for those candidate IDs without widening the RPC projection, and ranks application-side as:

1. confirmed open or confirmed 24-hour;
2. opening status unknown;
3. confirmed closed.

Distance is the tie-breaker inside each class. Missing, null, or malformed `open_hours` remains unknown. A closed-only result is shown as a fallback with explicit `No confirmed-open facility found nearby` wording; no candidates continues to produce the existing truthful empty state.

The fix is covered by 8 new pure assertions: nearer closed versus farther open, unknown versus closed, closed-only fallback ordering, 24-hour handling, missing-hours unknown handling, and empty-result preservation.

---

## Executive Summary

The legacy consolidation narrative below predates the fresh 2026-08-11 device
gate above. Its source and parent-branch history remains useful for
traceability, but its pre-device merge warning is superseded by the current
gate decision recorded above.

Relief is a React Native / Expo SDK 56 application whose **core discovery journey is wired to live data end to end at the service layer**, and whose most urgent feature — "Need One Now" — has been repaired and verified at the source/data-contract gate. The parent-branch device evidence described below is historical and does not clear the consolidated branch for merge.

What changed in this pass: the nearest-facility RPC was broken and is now fixed and verified; the database schema is now recorded in git for the first time; the mocked Nearby list is gone; discovery no longer requires an account; and the map's viewport loading no longer drops the user's latest pan.

The parent branch previously produced a release APK, installed it on a physical Samsung Galaxy S24 Ultra and drove all 22 required smoke checks, plus a signed-in journey covering favourites, reports, corrections and sign-out. That evidence remains historical: the consolidated branch produced no fresh APK during this gate, so those results are not reused as current verification.

Email authentication was verified end to end on the parent branch: a genuinely new account was created on the device, confirmed by email, and signed in, with the profile row created automatically by the database trigger. This is not a consolidated-device claim. What is still **not** verified: Google OAuth (the provider is disabled, so the button is hidden rather than broken); no EAS build exists; and the Google Maps key restrictions in Cloud Console have not been inspected.

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
| Navigation | IMPLEMENTED BUT NOT DEVICE TESTED | Three primary tabs are now Home, Find, Profile. Favourites lives in a stack beneath Home; the transient BrandedHandoff remains an overlay, not a route |
| Facility detail | IMPLEMENTED BUT NOT DEVICE TESTED | Visual hierarchy refreshed with warm-white cards and denser header/section treatment. The Lucide `Star` SVG remains outside `<Text>`, nullable `overall_score` remains truthful, and reports/corrections still require authentication |
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

Phase G supersedes the older historical wording below for password recovery and navigation: password reset now has entry, callback, update, and expiry handling; account deletion now has a deployed governed backend and normal Profile entry; and the previously hidden capability screens are intentionally reachable from Feature Lab only in opt-in test mode. The remaining blockers are recorded canonically in `docs/FEATURE_TEST_READINESS.md` and `docs/ACCOUNT_DELETION_RELEASE_READINESS.md`.

1. **Account self-service remains partial.** Display-name editing is now implemented in the app, keeping Auth `full_name` metadata and the `user_profiles.display_name` row together. Password reset is implemented but email delivery is unverified; account deletion is deployed, verified against a disposable account, and reachable from Profile. Public privacy/support/data-rights materials and the public deletion URL are still required before store submission.
2. **Google OAuth is not configured.** `GET /auth/v1/settings` reports `google: false`, so the provider cannot work at all. The button is now hidden behind `AUTH_PROVIDERS.GOOGLE` rather than failing in front of users. Enabling it needs Google Cloud credentials, SHA-1 registration, Supabase provider setup, a redirect allow-list entry, **and** an app-side deep-link handler that does not yet exist.
3. **Password reset does not exist.** There is no `resetPasswordForEmail` and no "Forgot password?" link, so a user who forgets their password cannot recover the account in-app.
4. **EAS project not linked.** Needs `eas init`, a decision on which Expo account owns it (`hourwiseeu` or `pcgsoft`), and the three `EXPO_PUBLIC_*` values added as `preview` environment variables. The APK under test was built locally instead.
5. **Local APK is debug-signed.** The Expo template signs `release` with the debug keystore (SHA-1 `84:91:66:28:20:F6:70:39:B9:8E:83:A8:4A:2D:86:68:CF:7B:B1:BE`). Fine for an internal preview, not a release artifact, and an EAS build will present a different certificate to the Maps key.
6. **Google Maps key restrictions not inspected.** Tiles render on this device, so the key works for the debug certificate and Maps SDK for Android is enabled — but the Cloud Console restriction list was not reviewed.
7. **Quality gates were run under Node 24.12.0**, while the EAS image uses Node 22. `.nvmrc`, `.node-version` and `engines` now pin 22; re-run `npm ci && npm run verify && npx expo-doctor` under Node 22 before the first EAS build.
8. **9 published facilities have unusable names** (two characters or fewer, or no alphanumerics) from the Toilet Map UK import — one renders as `]` in search results. A data cleanup, not an app defect.
9. **Storage, notifications, and RevenueCat** remain unconfigured. The governed moderation contract is live, but the moderator UI, permanent moderator roster, canonical publishing, photo moderation, and review moderation remain outside this scope.
10. **Lint warnings and unrouted-screen debt.** ESLint reports 0 errors but 92 warnings, mostly unused variables inside hidden features. The unrouted screens keep their React Compiler violations as scoped warnings and must be cleared — or those screens deleted — before any of them is registered again. Prettier is configured but has deliberately **not** been run repo-wide, so that a reformat does not bury real changes.
11. **No CI.** The quality gates exist as npm scripts but nothing runs them automatically.
12. **Machine-level `GRADLE_USER_HOME` is misconfigured** — it points inside a scoop-managed Gradle install of a different version, which prevented any Gradle build until overridden. Android Studio inherits this. See `ANDROID_SMOKE_TEST.md`.

---

## Safe next action

Exercise account **creation** and Google OAuth on the device — the two auth paths still unverified. Then, if a shareable build is wanted: `eas init` against the chosen Expo account, add the three `EXPO_PUBLIC_*` values as `preview` environment variables, register the EAS keystore's SHA-1 on the Maps key, and run `eas build -p android --profile preview`. Re-run the quality gates under Node 22 first.

## Governed user data export — LIVE DEPLOYED / VERIFIED — 2026-08-18

The signed-in Profile now exposes `Download my data` under Privacy & Data.
The live `export-account` Edge Function uses an empty request body,
verified-subject identity, recent authentication, explicit user-scoped reads,
and a versioned redacted JSON envelope delivered through the native share
sheet. Production version 2 is active with JWT verification enabled. Live
verification passed for anonymous/invalid-auth rejection, authenticated
export, request-target rejection, two-way cross-user isolation, contribution
redaction, secret/provider exclusion, repeatability, and non-mutation using
two disposable accounts that were hard-deleted afterward. The protected
moderation-summary sources are not exposed through the current export data
source; the response explicitly reports partial availability instead of
claiming that moderation activity is absent. No production migration,
canonical mutation, Storage object, payment history, or real account was
created for this verification. The design authority is
[`DATA_EXPORT_CONTRACT.md`](DATA_EXPORT_CONTRACT.md).

## Luna continuation status (2026-08-08)

The following work is **IMPLEMENTED BUT NOT DEVICE TESTED** on this branch:

* Home is the persistent default after onboarding, with Find a facility,
  Need One Now, Saved places, and About Relief actions.
* The primary navigation is exactly Home / Find / Profile. Favourites is a
  nested Home stack screen and keeps the bottom navigation visible.
* Home Need One Now passes a one-shot action id into the existing Find flow;
  Home does not duplicate the nearest-facility query.
* Profile now has guest/signed-in account cards, display-name editing,
  location permission state/recovery, Saved places, config-derived app
  version/build information, and the normal signed-in account-deletion entry.
* Map/detail/filter visual polish is applied without changing the truthful
  filter set or the Need One Now bearing-line restriction.

The hidden-feature audit is recorded in `docs/HIDDEN_FEATURE_AUDIT.md`. A new
APK/device run is required before changing any of these statuses to VERIFIED.

## Toilet Map Refresh 2 — RECONCILED / APPLY NOT AUTHORIZED — 2026-08-18

The current official Toilet Map UK dataset was independently checked on its
dataset page, downloaded, checksum-preserved, normalized and reconciled
read-only against the accepted source-linked Relief baseline. The resulting
Refresh 2 and proposed Apply 2 evidence is under `docs/data/`. This work did
not insert, update, delete, stage, create an `import_runs` row, invoke Apply
1A, or change provenance. Apply 1A evidence remains immutable. See
[`ENRICHMENT_ARCHITECTURE.md`](data/ENRICHMENT_ARCHITECTURE.md) and the
versioned Refresh 2 artifacts for the exact counts and source checksum.

## Toilet Map Apply 2B — NEW FACILITY PACKAGE PREPARED / EXECUTION NOT AUTHORIZED

The bounded Refresh 2B review assessed all 42 new-facility candidates without
writing production. Thirty-six candidates are prepared for a separately
authorized future insert package, five remain deferred for identity or
collision verification, and one placeholder-name record is quarantined. The
three canonical-neighbour collisions are Hemsby Beach Toilets, Burns Mall
Toilets, and Tesco Extra; the two same-name Becky’s Barn Cafe rows are also
deferred because they are 217.1 m apart in the source batch. See the four
`TOILET_MAP_APPLY_2B_NEW_*` artifacts under `docs/data/`. Production mutations
remain `0`, and no Apply 2B execution is authorized by this package.

## Final pre-pause consolidation — 2026-08-20

Apply 2B is now accepted as live/verified. The current read-only production
checkpoint is `facilities=15,620`, `facility_sources=15,620`,
`import_runs=5`, and `toilet_map_import_staging=0`, with all 15,620 facilities
published and 15,620 current Toilet Map UK source links. No additional exact,
frozen data package was present for this final optional review, so this batch
performed no canonical, source-link, provenance, staging, or import-run
mutation. The nine unusable published names remain manual-review items because
the fresh source repeats the same unusable values; no deterministic correction
was invented.

The five SDK 56 patch dependencies were aligned in commit `36de210`, and the
repository `verify` gate passes with all 21 test files passing. Expo Doctor is
`21/22`: the remaining advisory is the known Hermes V1 memory regression, not
an SDK 57 migration performed by this batch. EAS preview build
`dbd8c240-3a77-4656-b726-c2c8bfc48736` was submitted from that commit using
Node 22.22.2 and finished successfully. The artifact checksum and the fact
that this exact build has no physical-device verification are recorded in
[`RELIEF_PRE_PAUSE_READINESS.md`](RELIEF_PRE_PAUSE_READINESS.md).

The Supabase project remains active and healthy; no pause operation was run.
The recovery and security-advisor capture is in
[`RELIEF_PRE_PAUSE_READINESS.md`](RELIEF_PRE_PAUSE_READINESS.md), and the
bounded final data decision is in
[`TOILET_MAP_FINAL_OPTIONAL_DATA_REVIEW.md`](data/TOILET_MAP_FINAL_OPTIONAL_DATA_REVIEW.md).

## UK public-source expansion — DISCOVERY / INGESTION PREPARATION — 2026-08-20

The bounded National Rail, TfL, local-authority, Welsh, Scottish, and Northern
Irish source review added no production data and left the accepted checkpoint
unchanged at `facilities=15,620`, `facility_sources=15,620`, `import_runs=5`,
and `toilet_map_import_staging=0`. The current `facility_sources` aggregate
contains only the 15,620 Toilet Map UK links. Production mutations remain `0`.

National Rail Knowledgebase and live TfL feeds require registered access or
source terms. The public TfL example was held as enrichment-only because it is
not updated and has no coordinates. Rother is a possible OGL local-authority
candidate pending current machine-resource verification. DataMapWales names
PSGA for its national layer, so reuse permission remains unresolved. No
Scottish or Northern Irish feed met the bounded selection bar. See
[`UK_PUBLIC_SOURCE_EXPANSION.md`](UK_PUBLIC_SOURCE_EXPANSION.md) and the
versioned JSON evidence under `docs/data/`.

## UK public-source expansion Phase 2 — LIVE FEED ACQUIRED / CANDIDATE RECONCILIATION — 2026-08-20

The first real additional source was acquired from the official Sheffield City
Council GeoJSON endpoint listed by the National Data Library under the UK OGL.
The 41-row snapshot has coordinates and UPRN identifiers but no facility names,
so all 41 remain review-required and zero are prepared for insertion. A
read-only production proximity check found 18 near existing facilities and 23
without a nearby facility; proximity was not promoted to identity. National
Rail and TfL still require their registered access actions, Rother remains
resource-quality blocked, and no Wales/Scotland/Northern Ireland feed was
promoted. Production remains unchanged with `production_mutations=0`. See
[`UK_PUBLIC_SOURCE_EXPANSION_PHASE2.md`](UK_PUBLIC_SOURCE_EXPANSION_PHASE2.md)
and the Phase 2 JSON evidence under `docs/data/`.

## UK public-source expansion Phase 3 — SHEFFIELD ADJUDICATED / ACCESS HANDOFF — 2026-08-20

The Sheffield layer metadata confirms a structural absence of names: its only
published fields are `objectid`, `uprn`, and `blpu_state`, with all 41 rows in
state `2`. Exact read-only PostGIS adjudication found 18 rows with exactly one
facility within 100 metres, 23 with none, zero with multiple nearby facilities,
and zero exact source links. All 41 are frozen as
`DEFER_EXTERNAL_VERIFICATION`; the proposed INSERT, SOURCE_LINK, and
ENRICHMENT counts are all `0`. National Rail and TfL registration handoff
instructions are recorded, but no account or credential action was performed.
Production mutations remain `0`. See
[`UK_PUBLIC_SOURCE_EXPANSION_PHASE3.md`](UK_PUBLIC_SOURCE_EXPANSION_PHASE3.md)
and the Phase 3 JSON evidence under `docs/data/`.

## UK public-source expansion Phase 4 — TfL real detailed feed — RECONCILED / PRODUCTION APPLY NOT AUTHORIZED — 2026-08-21

The current official TfL detailed station-data package was downloaded from
`https://api.tfl.gov.uk/stationdata/tfl-stationdata-detailed.zip` without an
API key. The frozen package is recorded in
[`UK_PUBLIC_SOURCE_EXPANSION_TFL_REAL_FEED_2026-08-21.md`](data/UK_PUBLIC_SOURCE_EXPANSION_TFL_REAL_FEED_2026-08-21.md)
and
[`UK_PUBLIC_SOURCE_EXPANSION_TFL_REAL_FEED_2026-08-21.json`](data/UK_PUBLIC_SOURCE_EXPANSION_TFL_REAL_FEED_2026-08-21.json).

The ZIP contains 11 files, 509 station records, and 410 toilet rows. All 410
toilet rows join to station records and have usable station-level coordinates;
the source does not provide toilet-specific coordinates. The reconciliation
classified 0 exact matches, 305 high-confidence matches, 33 review matches,
58 distinct-new candidates, 0 insufficient-location rows, and 14 quarantine
rows. The feed contains 147 stations with multiple toilet rows. A model guard
blocks automatic source-link/enrichment operations where 328 TfL rows map to
124 existing Relief facility candidates, so Male/Female/Unisex rows are not
collapsed. Proposed operations are 58 INSERT candidates, 14 SOURCE_LINK
candidates, and 14 ENRICHMENT candidates after the guard; none is authorized.

Production remains unchanged at `facilities=15,620`,
`facility_sources=15,620`, `import_runs=5`, and
`toilet_map_import_staging=0`. Production mutations remain `0`.

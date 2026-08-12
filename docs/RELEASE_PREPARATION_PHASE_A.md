# Relief Release Preparation Phase A — post-Apply integration and Android audit

**Audit date:** 2026-08-12
**Starting branch:** `codex/toilet-map-apply-1a-production-deploy`
**Starting HEAD / remote branch HEAD:** `1d2a82890da6d82ef77efbc1fe79c3f42076577`
**Production Supabase ref configured for the mobile build:** `bgwxrxkmyaihplaloely`
**Production mutation boundary:** preserved. No migration, Apply invocation, policy/grant change, mobile write, account creation, upload, deletion, or auth-configuration change was performed.

## Phase B superseding addendum

The Phase B follow-up is recorded in
[`RELEASE_PREPARATION_PHASE_B.md`](RELEASE_PREPARATION_PHASE_B.md). For the
current matrix, use `CATALOG_COMPATIBLE_NOT_LIVE_WRITE_TESTED` for the
catalog-compatible authenticated flows, `BLOCKED_BY_RLS` for the badge award
side effect, and `BLOCKED_BY_STORAGE_INFRASTRUCTURE` for photo upload. The
badge guard and regression coverage are included in the Phase A checkpoint;
the Android clean-prebuild comparison and Gradle reproduction are recorded in
the Phase B report.

## A. Current architecture

The app is a React Native 0.85.3 / Expo SDK 56.0.19 TypeScript app using
React Navigation 7. The client has three primary tabs: Home, Find, and
Profile. Find owns a shared Map/List experience, facility detail, and the
account-gated community routes. Supabase Auth uses AsyncStorage-backed
session persistence and AppState-driven token refresh. Supabase reads and
writes are initiated directly from the mobile client using the public anon /
publishable key.

Local-only persistence is AsyncStorage, expo-sqlite, and expo-secure-store.
Google Maps is configured for Android through `react-native-maps`; iOS uses
the default provider. RevenueCat, what3words, notifications, photo storage,
and moderation processing are not configured for this release gate. The
feature flags remain unchanged: COMMUNITY true; ADVANCED_FILTERS, PREMIUM,
AI, and EUROPE false.

## B. Implemented mobile flows and reachability

| Flow | Source evidence | Status | Reachable now |
|---|---|---|---|
| Guest Home / Find / Map / List | `AppNavigator.tsx`, `HomeScreen.tsx`, `FindScreen.tsx` | UI IMPLEMENTED; read backend-dependent | Yes |
| Facility search and detail | `facilities.ts`, `FindScreen.tsx`, `FacilityDetailScreen.tsx` | UI IMPLEMENTED; anonymous read confirmed below | Yes |
| Need One Now / nearest facility | `facilities.ts`, `nearestFacility.ts`, Home handoff | UI IMPLEMENTED; RPC read confirmed below | Yes |
| Basic filters | `filterDefinitions.ts`, `AdvancedFiltersScreen.tsx` | CLIENT LOGIC IMPLEMENTED; uses only populated fields | Yes |
| Directions | `FacilityDetailScreen.tsx` | UI IMPLEMENTED; external coordinate links | Yes |
| Email sign-up / sign-in / sign-out | `auth.ts`, Login/Register screens | UI IMPLEMENTED; authenticated device flow not exercised in this audit | Yes |
| Favourites | `favourites.ts`, `FavouritesScreen.tsx` | UI IMPLEMENTED; authenticated RLS write unverified | Yes, after auth |
| Display-name read/update | `account.ts`, `ProfileScreen.tsx` | UI IMPLEMENTED; authenticated RLS write unverified | Yes, after auth |
| Temporary reports | `community.ts`, `ReportFacilityScreen.tsx` | UI IMPLEMENTED; authenticated RLS write unverified | Yes, after auth |
| Corrections | `community.ts`, `CorrectInfoScreen.tsx` | UI IMPLEMENTED; authenticated RLS write unverified | Yes, after auth |
| Facility submissions | `community.ts`, `AddFacilityScreen.tsx` | UI IMPLEMENTED; authenticated RLS write unverified | Yes, after auth |
| Photo upload / moderation | `community.ts`; no registered photo UI or bucket evidence | BACKEND-DEPENDENT / BLOCKED | No |
| Saved profiles, offline data, alerts, AI, location sharing, paywall | Existing service/screen files but not registered in the active navigator | DEFERRED / NOT CURRENTLY REACHABLE | No |
| Password reset | No `resetPasswordForEmail` or reset screen found | NOT IMPLEMENTED | No |
| Account deletion | No UI, Auth admin function, Edge Function, or RPC found | BLOCKED | No |

## C. Generated database types

The approved generator is `npm run gen:types`, implemented by
`tools/generate-database-types.mjs`. It requires the server-only
`SUPABASE_DB_URL` and direct `psql` access. The existing process environment
did not contain that variable. The generator was run and returned:
`SUPABASE_DB_URL is not set. Export it before running this script.`

Therefore:

| State | Result |
|---|---|
| `GENERATED_TYPES_UPDATE_REQUIRED` | **True** |
| `GENERATED_TYPES_REFRESH_BLOCKED` | **True** |
| Manual edit to `src/types/database.types.ts` | Not performed |
| New credential or EXPO_PUBLIC database URL | Not created |

The checked-in generated types remain the source used by the TypeScript
client. The local integration boundary added in this audit uses those types
for the nearest RPC arguments and authenticated insert payloads; it does not
replace or hand-edit the generated file.

## D. Supabase environment and secrets audit

The mobile client reads only `EXPO_PUBLIC_SUPABASE_URL` and
`EXPO_PUBLIC_SUPABASE_ANON_KEY` from `src/utils/env.ts`. The app config also
passes only those client-safe values into Expo `extra`. No service-role key,
direct database URL, or database password is used by mobile source. The
server-only generator reads `SUPABASE_DB_URL` only from the process
environment.

The repository-wide search found references to server-only terms in
documentation, migration comments, generator/import tooling, and Edge
Function code; it did not find a committed `postgres://` or `postgresql://`
connection string, `sk_` key, or service-role value. The ignored local `.env`
contains client build variables and was not added to the patch. The generated
Android manifest contains a Maps key because the native tree is locally
prebuilt and ignored; the manifest is not tracked or committed. Its value was
not copied into source or this report.

Session behaviour is coherent at the client boundary: AsyncStorage is used,
`persistSession` and `autoRefreshToken` are enabled, URL session detection is
disabled for native, and AppState starts/stops refresh. The authenticated
device journey remains UNVERIFIED in this audit.

## E. Current Supabase operation inventory

The inventory below is derived from `src/services`, active screens, and the
active navigator. “Type coverage” means the checked-in generated database
types cover the table/RPC boundary; community domain types still contain
hand-written convenience shapes and are converted through the new typed
contract builders.

### Read operations

| Source function | Target | Auth | Flow / reachability | Type coverage | RLS result |
|---|---|---|---|---|---|
| `fetchViewportFacilities` | `facilities` SELECT, published + bounds + filters | anon or authenticated | Find map/list; reachable | `Facility` derived from generated `facilities` | PASS for anonymous read; HTTP 200 confirmed |
| `fetchNearbyFacilities` | delegates to `facilities` SELECT | anon or authenticated | Find/location path; reachable | Yes | PASS by same policy/read path |
| `searchFacilities` | `facilities` SELECT, town/postcode `ilike` | anon or authenticated | Find search; reachable | Yes | PASS by same policy/read path |
| `fetchFacilityById` | `facilities` SELECT | anon or authenticated | Facility detail; reachable | Yes | PASS by same policy/read path |
| `fetchClosestFacility` | `find_nearest_facilities` RPC, then bounded `facilities` lookup of `id,is_24h` | anon or authenticated | Need One Now; reachable | RPC args/return covered; `is_24h` table read covered | PASS for anonymous RPC; HTTP 200 confirmed |
| `getFavourites`, `getFavouriteFacilities`, `isFavourite`, `getFavouriteCount` | `favourites` and `facilities` SELECT | authenticated for owned rows; count currently has no auth guard | Favourites/detail; reachable after auth | Cast to hand-written `Favourite` / `Facility` | UNVERIFIED for authenticated; source policy is owner-scoped |
| `getAccountDetails` | Auth `getUser`; `user_profiles` SELECT | authenticated | Profile; reachable after auth | Hand-written `AccountDetails`; table generated | UNVERIFIED for authenticated profile read |
| `getActiveReports` | `temporary_reports` SELECT active rows | anon or authenticated | Facility detail/report flow; reachable | Hand-written community type; table generated | PASS by checked-in policy; live authenticated read not exercised |
| `getAccessCodes`, `getFacilityPhotos` | `access_codes` / `photo_moderation` SELECT | anon/authenticated subject to status | No active UI route found | Hand-written community types; tables generated | UNVERIFIED; photo path also lacks storage setup |
| `getUserSubmissions`, `getUserBadges` | owned `facility_submissions` / `user_badges` SELECT | authenticated | No active UI route found | Hand-written community types; tables generated | NOT CURRENTLY REACHABLE |
| `getSavedProfiles` | owned `saved_profiles` SELECT | authenticated | Hidden/unregistered feature | Generated table; cast convenience type | NOT CURRENTLY REACHABLE |
| `getServerSideEntitlement`, `getSubscriptionEvents` | `user_subscriptions` / `subscription_events` SELECT | authenticated | RevenueCat disabled; no active premium route | Generated tables; casts in service | NOT CURRENTLY REACHABLE |
| `checkFavouriteFacilityAlerts` | favourites, facilities, temporary reports SELECT | authenticated | Notification alerts unregistered | Mixed generated/custom | NOT CURRENTLY REACHABLE |

### Write operations

| Source function | Target and operation | Auth / ownership | Flow | RLS result |
|---|---|---|---|---|
| `signUpWithEmail` | Supabase Auth sign-up; profile creation is database-trigger dependent | anon | Register; reachable | UNVERIFIED; no user creation performed |
| `signInWithEmail`, OAuth helpers, `signOut` | Supabase Auth | anon/authenticated | Auth modal; reachable where provider configured | Email flow UNVERIFIED; Google/Apple disabled by app config |
| `addFavourite` | `favourites` INSERT | authenticated; `user_id = auth.uid()` | Facility detail; reachable after auth | UNVERIFIED; checked-in policy/grant are compatible |
| `removeFavourite` | `favourites` DELETE | authenticated; owner filter + policy | Detail/favourites; reachable after auth | UNVERIFIED; checked-in policy/grant are compatible |
| `updateDisplayName` | Auth metadata update, `user_profiles` UPDATE | authenticated; row id = auth.uid(); display-name grant | Profile; reachable after auth | UNVERIFIED; checked-in policy/grant are compatible |
| `submitTemporaryReport` | `temporary_reports` INSERT; also `rate_limits` INSERT and badge side effect | authenticated; user-owned check | Report screen | UNVERIFIED for report/rate-limit; badge side effect BLOCKED by source policy gap |
| `resolveOwnReport` | `temporary_reports` UPDATE | authenticated; owner + expiry check | Report screen | UNVERIFIED; checked-in policy/grant are compatible |
| `submitCorrection` | `correction_requests` INSERT; also `rate_limits` INSERT | authenticated; `user_id = auth.uid()` | Correction screen | UNVERIFIED; checked-in policy/grant are compatible |
| `submitFacility` | `facility_submissions` INSERT; also `rate_limits` INSERT and badge side effect | authenticated; `user_id = auth.uid()` | Add Facility screen | UNVERIFIED for submission/rate-limit; badge side effect BLOCKED by source policy gap |
| `addAccessCode` | `access_codes` INSERT/UPDATE | authenticated; user-owned policy | No active UI route found | NOT CURRENTLY REACHABLE |
| `uploadFacilityPhoto` | Storage upload, public URL, `photo_moderation` INSERT | authenticated; storage bucket/policies required | No active UI route found | BLOCKED: no verified bucket/policy/processing pipeline |
| `reportPhoto` | `photo_moderation` UPDATE | authenticated | No active UI route found | LIKELY BLOCKED: checked-in baseline has SELECT/INSERT policies but no user UPDATE policy |
| `reportReview` | `review_reports` INSERT | authenticated; user-owned policy | No active UI route found | NOT CURRENTLY REACHABLE |
| `create/update/deleteSavedProfile` | `saved_profiles` INSERT/UPDATE/DELETE | authenticated; owner policy | Hidden/unregistered | NOT CURRENTLY REACHABLE |
| RevenueCat purchase/webhook operations | SDK / subscription tables | premium disabled | Hidden/unregistered | NOT CURRENTLY REACHABLE |

## F. Live read-only RLS compatibility audit

The server-only catalog credential was not available, so this audit did not
query `pg_catalog`, `pg_policies`, grants, or function ownership directly.
No replacement credential was created. The checked-in live schema baseline
was compared with the client inventory, and the configured production REST
endpoint was used only for non-mutating checks:

| Check | Result |
|---|---|
| Anonymous published-facility REST SELECT | **PASS — HTTP 200** |
| Anonymous `find_nearest_facilities` RPC read | **PASS — HTTP 200** |
| Authenticated write policy behaviour | **UNVERIFIED — no production user/write test authorised** |
| Production catalog policy/grant/function-owner inspection | **BLOCKED — `SUPABASE_DB_URL` unavailable** |
| Storage bucket/policy inspection | **UNVERIFIED / BLOCKED — no storage catalog access and no mobile bucket evidence** |

The checked-in baseline contains an anon/authenticated published-facility
SELECT policy and anon/authenticated EXECUTE grants for the repaired nearest
RPC. It also contains owner-scoped authenticated policies for favourites,
saved profiles, reports, corrections, submissions, profile updates, access
codes, and rate limits. Those source policies are not proof of the current
production catalog after Apply 1A; the authenticated rows above therefore
remain UNVERIFIED.

The app’s Apply-related database changes are outside the mobile operation
surface. The sealed Apply operator path remains untouched; no Apply call or
new Apply migration was made.

## G. RPC compatibility

The app calls `find_nearest_facilities` with the generated argument names
`user_latitude`, `user_longitude`, `search_radius_metres`, and `result_limit`.
The repaired RPC projection is mapped through `mapNearestFacilityRow`, with a
bounded follow-up read for `is_24h`. The production anonymous RPC smoke check
returned HTTP 200. The local contract test pins the request shape and the
existing nearest-facility tests pin open/unknown/closed ranking and nullable
handling.

No other RPC is called by an active mobile route. Auth calls are Supabase Auth
methods, not public database RPCs.

## H. Storage compatibility

`community.ts` contains a photo upload path targeting the
`facility-photos` bucket, followed by `photo_moderation` metadata. No active
screen calls this function. The repository contains no verified storage bucket
setup, storage policy audit, EXIF stripping function, or face-blurring
pipeline. The path is therefore BLOCKED and must not be enabled for release.

## I. Account deletion and privacy contract

No account deletion UI, `supabase.auth.admin.deleteUser` server handler,
deletion Edge Function, or deletion RPC exists. No password reset flow or
data export flow exists. The i18n file contains labels for future privacy and
deletion surfaces, but labels are not implementation evidence.

The current schema baseline has `ON DELETE CASCADE` from `auth.users` to
user-owned rows including profiles, favourites, submissions, corrections,
temporary reports, photo metadata, rate limits, badges, subscriptions, and
subscription events. Facility-owned records also cascade when a facility is
deleted. Storage objects are outside those relational cascades. References
such as `reviewed_by` and `reported_by` do not provide a complete deletion
contract.

The following is a decision record, not an approval to delete production data:

| Decision area | Evidence / candidate | Current decision |
|---|---|---|
| A. Delete immediately | Candidate: account identity, `user_profiles`, favourites, saved profiles, rate limits, and other user-private rows | **Unresolved**; product/legal owner must approve exact scope and order |
| B. Anonymise | Candidate: authored submissions, reports, corrections, photo metadata, badges, and audit/history where community value is retained | **Unresolved**; no anonymisation fields or approved pseudonym scheme exists |
| C. Legitimate retention | Candidate: moderation/audit/history records and legally required transaction evidence | **Unresolved**; do not invent a retention period or legal basis |
| D. Relationships/cascades | Baseline cascades from `auth.users` cover many user rows; storage objects and some reviewer references need explicit handling | **Documented; not verified against live catalog** |
| E. Product/legal decisions | Public privacy policy, terms, support identity, deletion URL, export scope, retention basis, storage cleanup, and re-authentication/confirmation | **Open blockers** |

Do not implement destructive account deletion until this contract is approved
and a server-side handler can perform the required database and storage work.

## J. Android/native and build readiness

| Area | Finding | Status |
|---|---|---|
| Workflow | Expo app with a locally generated `android/` tree; the tree is ignored by Git and must be reproducible from app config | VERIFIED as configured |
| Package / namespace | `com.relief.app` | VERIFIED by Expo public config and Gradle files |
| Expo / React Native | Expo SDK 56.0.19, React Native 0.85.3 | VERIFIED; SDK 56 reference consulted |
| Compile / target / min SDK | Gradle delegates to Expo/RN root project values; public SDK 56 docs specify compile/target 36 and Android 7+ support | Native task did not reach evaluation; verify after Gradle repair |
| JDK / Gradle | JDK 17.0.17; wrapper Gradle 9.3.1 | Present, but build fails in RN plugin settings evaluation |
| New Architecture / Hermes | `newArchEnabled=true`, `hermesEnabled=true` | Configured; not changed |
| Location | Fine/coarse permissions in app config and manifest; foreground location hook | Configured; foreground only |
| Maps | Google Maps Android plugin and manifest metadata generated; key is local ignored config | Configured locally; Cloud Console restrictions/SHA-1 not audited |
| Notifications | Expo notifications plugin present, but no push backend and no active route | BACKEND-DEPENDENT / hidden |
| Deep links | `relief` scheme and Android VIEW intent filter; OAuth callback handling remains incomplete | Partial |
| Network | Android INTERNET permission present | Configured |
| Signing | Release build type currently uses the debug keystore | DEBUG/INTERNAL ONLY; not a production release configuration |
| EAS | Preview APK profile exists; no EAS project ID or preview environment setup verified | BLOCKED for EAS until account/environment setup |

Read-only / local checks:

- `npx expo-doctor`: **21/21 checks passed**.
- `npm run config`: **PASS**, SDK 56.0.0, package `com.relief.app`, scheme
  `relief`; values were not reproduced in this document.
- `android/gradlew.bat --version`: **PASS**, Gradle 9.3.1 / JDK 17.0.17.
- `:app:assembleDebug -PreactNativeArchitectures=arm64-v8a`: **BLOCKED**;
  the React Native Gradle plugin settings build fails with unresolved
  `plugins` / `id` references in
  `node_modules/@react-native/gradle-plugin/settings.gradle.kts`.
- No clean prebuild regeneration was run; the ignored native tree was not
  overwritten.

Eventually, after native configuration is repaired and environment gates are
cleared, the intended local validation command is:

```text
android\gradlew.bat -p android :app:assembleDebug -PreactNativeArchitectures=arm64-v8a
```

The eventual EAS command, only after EAS ownership, preview environment
variables, and Maps certificate restrictions are configured, is:

```text
eas build -p android --profile preview
```

## K. Local integration fixes and tests

The following bounded app-side changes were made:

1. Added `integrationContracts.ts` with generated-type-backed builders for
   nearest RPC args, favourite ownership/payloads, temporary reports,
   corrections, and facility submissions.
2. Updated the existing services to use those builders, preserving the
   authenticated user ID and request field names at the boundary.
3. Added `supabaseErrors.ts` and routed community/favourite/facility errors
   through safe RLS, offline, rate-limit, schema-drift, and fallback messages.
   Raw backend messages are no longer returned from those user-facing write
   paths.
4. Isolated native session options in `supabaseAuthConfig.ts` so persistence
   and refresh behaviour can be tested without loading React Native in Node.

Tests added: `__tests__/supabaseIntegrationContracts.test.ts` covering
session persistence configuration, nearest RPC shape, favourite add/remove
shape, report/correction/submission payloads, RLS denial handling, offline
handling, and schema drift.

## L. UI/UX release-blocker audit

| Area | Classification | Evidence |
|---|---|---|
| Navigation completeness | PARTIAL | Active guest discovery and auth modal are wired; hidden feature screens remain compiled but unrouted |
| Guest urgent journey | WORKING at source/read boundary | Main is guest-capable; Need One Now does not require auth; production anon RPC returned 200 |
| Map/list | PARTIAL | Source states and shared Find flow exist; current branch debug APK could not be built for device confirmation |
| Facility detail | PARTIAL | Read/error/loading/not-found states and actions exist; authenticated writes unverified |
| Filters | WORKING at source level | Exposed filters are derived from real columns and tests pass; Android device retest awaits build |
| Favourites | PARTIAL | UI and auth gate exist; live authenticated RLS not verified |
| Report/correction/submission | PARTIAL | Forms and service calls exist; live authenticated RLS not verified; badge side effect lacks insert policy |
| Profile/settings | PARTIAL | Display-name edit and sign-out exist; password reset/deletion/privacy links absent |
| Loading/error handling | WORKING at tested service boundary | Facility and auth network/schema errors are sanitised; new community write errors are sanitised |
| Privacy/legal | BLOCKED | No implemented deletion, export, published policy/terms, or public deletion URL |

## M. Security-advisor triage

Existing advisor findings were not remediated in this task. They are triaged
for release planning only:

| Finding | Priority / classification | Reason |
|---|---|---|
| `toilet_map_import_staging` RLS-no-policy | P1 before any importer exposure; not an active mobile route | Operational/import staging object; do not expose through app |
| Mutable-search-path functions | P1 database hardening | Review function definitions and set an explicit safe search path; outside this app-only patch |
| Public `SECURITY DEFINER` concerns | P1 review | Confirm each function owner, search path, and grants; do not assume exploitability from advisor label alone |
| Leaked-password protection | P1 before public auth release | Auth hardening and account-protection decision remain outstanding; not enabled here |
| `spatial_ref_sys` finding | KNOWN / ACCEPTED or unrelated platform object pending advisor evidence | Extension-owned PostGIS catalog object; do not alter extension setup in Phase A |
| PostGIS placement | KNOWN / ACCEPTED platform architecture item | Extension placement is not an app client defect; no change authorized |
| Apply operator/sealing findings | KNOWN / ACCEPTED for this phase | Apply 1A is sealed; no Apply machinery was reopened or changed |

No advisor finding was treated as proof that the mobile anon read or an
authenticated write succeeds. The missing live catalog inspection remains a
release evidence gap.

## N. Validation results

| Check | Result |
|---|---|
| `npm run gen:types` | BLOCKED — `SUPABASE_DB_URL` absent; generated file untouched |
| `npm run typecheck` | PASS |
| `npm test` | PASS — 12 test files, including the new integration-contract test |
| Direct ESLint on changed files | PASS — 0 errors, 4 pre-existing community unused-variable warnings |
| `npm run lint` / Expo wrapper | TIMEOUT — no diagnostics returned within bounded run; direct ESLint completed |
| `npx expo-doctor` | PASS — 21/21 |
| `npm run config` | PASS — public SDK/package/scheme resolved |
| `git diff --check` | Pending final working-tree check after documentation update |
| Production writes | **None attempted** |
| Production Apply | **Not invoked** |

## O. Release classification and ordered next actions

### Debug APK build readiness

**BLOCKED_BY_NATIVE_CONFIG.** The Expo config and dependency health are
clean, but the local Gradle assemble task fails in the React Native Gradle
plugin before producing an APK. Debug signing is also internal-only. The
debug APK is not currently READY_FOR_DEBUG_APK from this checkout.

### Public release readiness

**BLOCKED_BY_ACCOUNT-DELETION_CONTRACT**, with additional privacy/legal,
authenticated-RLS evidence, EAS/secrets environment, storage/moderation,
Maps restriction, and native-build blockers. This is not a public-release
candidate.

### Overall classification

**F. MULTIPLE RELEASE BLOCKERS**

Ordered next five actions:

1. Repair and reproduce the Expo SDK 56 / React Native 0.85 Android Gradle
   configuration without destructive prebuild regeneration; rerun the debug
   assemble and device smoke gate.
2. Provide the existing server-only `SUPABASE_DB_URL` securely to the approved
   generator process, refresh generated types, inspect the diff, and keep the
   credential out of app environment variables and Git.
3. Obtain a read-only production catalog audit or equivalent owner-provided
   evidence for all authenticated table policies, grants, RPC ownership, and
   storage policies; do not test writes until separately authorised.
4. Approve the account-deletion/privacy contract, including immediate-delete
   rows, anonymisation rules, legitimate retention, storage cleanup, export
   scope, public policy/terms URLs, and the support identity; then implement a
   server-side deletion path and in-app route.
5. Resolve release operations: EAS project ownership and preview variables,
   debug/EAS Maps SHA-1 restrictions, leaked-password protection decision,
   moderation/storage setup, and authenticated device tests for favourites,
   reports, corrections, submissions, and profile editing.

## P. Commit / remote state

No commit or push was made because the required release gates are not all
passing. The starting remote branch remains at
`1d2a82890da6d82ef77efbc1fe79c3f42076577`; local source/tests/documentation
changes remain for review in the working tree. No merge or tag was created.

**Phase conclusion:** `RELIEF RELEASE PREP PHASE A HAS BLOCKERS — STOP FOR REVIEW`

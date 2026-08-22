# Relief — Feature Matrix

**Last verified:** 2026-08-16
> Phase G canonical test-build readiness is maintained in [`FEATURE_TEST_READINESS.md`](./FEATURE_TEST_READINESS.md). This file contains historical feature-matrix and earlier verification evidence; do not use older status labels here to decide Phase G test-build readiness.

**Verification method:** Phase B post-Apply source audit, contract regression tests, Expo SDK 56 clean disposable prebuild, current/clean Android Gradle reproduction, and the bounded 2026-08-16 authenticated production community verification. No schema, policy, canonical-facility, import, Storage, OAuth, review, or account-deletion backend mutation was performed in the community verification.

## Governed moderation contract overlay — 2026-08-16

The governed moderation contract is **COMMUNITY MODERATION CONTRACT — LIVE DEPLOYED**.
It uses database-backed moderator membership and narrow server-authorized RPCs
for facility submissions, corrections, and access-code verification. The
production migration and live authorization tests passed. No permanent
moderator, moderation UI, canonical publication path, or canonical facility
mutation is enabled. See [`MODERATION_CONTRACT.md`](./MODERATION_CONTRACT.md).

## Authenticated community integration overlay - 2026-08-16

This overlay records the bounded production verification after the approved
community-contract hardening migration. Two disposable confirmed Auth accounts
were used only for owner and cross-user isolation checks. Their rows and
accounts were removed; the final production cleanup query found zero marker
rows, zero favourites, zero user badges, and the original two Auth users. The
live migration was `community_contract_hardening` (Supabase migration id
`20260816210130`; local file
`supabase/migrations/20260816205543_community_contract_hardening.sql`).

| Surface | Status | Live evidence / boundary |
|---------|--------|--------------------------|
| Profile/display name | VERIFIED | Auth metadata update, `user_profiles` update and owner readback passed; other-user profile read was not exposed. |
| Favourites | VERIFIED | Owner create/read/delete passed; anonymous and arbitrary-other-user writes were denied. |
| Facility submissions | VERIFIED | Authenticated INSERT is pending-only and owner-bound; status/reviewer columns are not writable by authenticated clients; A/B alteration and moderation self-elevation attempts returned denial. |
| Temporary reports | VERIFIED | Authenticated INSERT is owner-bound; resolution uses the owner-only `resolve_own_temporary_report` RPC, is idempotent for the owner, returns false for another owner, and broad direct UPDATE is denied. |
| Corrections | VERIFIED | Authenticated INSERT is pending-only and owner-bound; status/reviewer columns are not writable by authenticated clients; A/B alteration and moderation self-elevation attempts returned denial. |
| Access codes | VERIFIED | Owner upsert uses the `upsert_own_access_code` RPC; direct writes and self-verification are denied, and A/B facility/row isolation passed. |
| Rate-limit records | VERIFIED (bounded) | Three own records and readback passed; arbitrary-other-user record insertion was denied. The client-side count check is not server-side abuse prevention. |
| Governed badges | VERIFIED (bounded) | Direct client INSERT/UPDATE/DELETE were denied; the facility-submission trigger awarded Explorer and readback succeeded. The client award helper was removed. |
| Photos / Storage | BLOCKED | Not exercised; existing Storage infrastructure remains unavailable. |
| Reviews | DEFERRED | No approved review-write contract was exercised. |
| OAuth, RevenueCat, remote push | BLOCKED | External configuration remains required and was not changed. |

The anonymous negative checks for favourites, facility submissions, temporary
reports and corrections all returned denial. Canonical facility data was read
only. The hardening migration changed only the four approved community-write
contracts; it did not change badges, canonical facilities, imports, Storage,
OAuth, reviews, subscriptions, or account deletion.

## Phase B post-Apply integration overlay - 2026-08-12

This overlay supersedes older device/build notes where they conflict. It does
not convert catalog compatibility into a live authenticated write test.

| Surface | Status | Evidence / boundary |
|---------|--------|---------------------|
| Published facility reads | CATALOG_COMPATIBLE_NOT_LIVE_WRITE_TESTED | Current read-only evidence is compatible with anonymous published-facility reads. |
| Nearest-facility RPC | CATALOG_COMPATIBLE_NOT_LIVE_WRITE_TESTED | Anonymous/authenticated EXECUTE is compatible; the RPC is not security definer. |
| Favourites, profile, reports, corrections, facility submissions, rate limits, access codes, review reports | BACKEND-DEPENDENT | See the authenticated community integration overlay above for live owner/RLS results and blockers. |
| Saved profiles | CATALOG_COMPATIBLE_NOT_LIVE_WRITE_TESTED | Catalog-compatible but unreachable while the feature is disabled. |
| Subscription events | BACKEND-DEPENDENT | Server-write-only boundary; premium remains disabled. |
| Badge award side effect | VERIFIED | Governed database triggers award badges; the mobile client now reads badges only. |
| Photo upload / moderation | BLOCKED_BY_STORAGE_INFRASTRUCTURE | Storage bucket count and storage object policy count are zero; upload remains unreachable. |
| Android debug APK | BLOCKED | Clean and current trees reproduce the React Native Gradle plugin Kotlin DSL failure under the local toolchain. |

## Fresh Android gate overlay - 2026-08-11

The following statuses are newly verified on the fresh installed APK. They
supersede the older device-unverified notes in the detailed source matrix
below; backend, EAS, Google OAuth, and production-service setup remain separate
gates.

| Surface | Status | Fresh evidence |
|---------|--------|----------------|
| Map, markers, viewport and centre-on-user | VERIFIED | Google tiles, live markers, panned viewport, selected marker and centre control exercised on the S24 Ultra |
| List view and basic Free filter | VERIFIED | Map/List switch and one active Free filter returned a live free facility |
| Need One Now | VERIFIED | 8 source ranking assertions plus a guest live-data urgent journey with a confirmed open candidate |
| Facility detail and directions | VERIFIED | Detail, safe areas, deep-link controls and visible Google Maps walking route exercised |
| Native startup, onboarding and Home | VERIFIED | Fresh release install reached branded onboarding and Home with the three primary tabs |
| About Relief | VERIFIED | Fresh device run opened the artwork, app information and truthful preview copy |
| Guest-capable entry and auth handoff | VERIFIED | Guest Find/Need One Now worked; sign-in screen and Continue without an account returned to guest state |
| Signed-in profile editor and sign-out | VERIFIED | Existing unchanged value submitted safely; sign-out returned the app to guest state |

Each feature is assessed against the current repository, not against plans or intentions.

---

## Core Search and Discovery

| Feature | Surface | Files | Data Source | Backend Dependency | Status | Evidence | Risk | Next Step |
|---------|---------|-------|-------------|-------------------|--------|----------|------|-----------|
| Map view with pins | MapScreen | `screens/MapScreen.tsx` | Supabase `facilities` table | Supabase + Android Google Maps SDK | BACKEND-DEPENDENT | `fetchViewportFacilities()` preserves bounded/debounced real-data loading; Android uses `PROVIDER_GOOGLE`; native teal, cluster and selected/urgent marker visual components are applied | Android key and Supabase setup are user-reported; map/data path and marker performance not yet smoke-tested | Run Android build smoke test with real data |
| Map clustering | MapScreen | `screens/MapScreen.tsx` | Client-side calculation | None | CLIENT LOGIC IMPLEMENTED | `clusterFacilities()` groups by coordinate proximity | Grid-based, not true pixel-distance clustering | Test with real data densities |
| List view | ListScreen | `screens/ListScreen.tsx` | Supabase `facilities` table | Supabase | BACKEND-DEPENDENT | Supabase query exists; 15,584 UK facilities imported; previously showed 3 hardcoded Liverpool facilities | Needs client-side smoke test | Run smoke test; replace hardcoded fallback with real query |
| Search by town/postcode | MapScreen | `screens/MapScreen.tsx` | Supabase `facilities` table | Supabase | BACKEND-DEPENDENT | `searchFacilities()` queries Supabase; 383 distinct towns in imported data | Requires verified Supabase reads | Smoke test with real data |
| Facility detail | FacilityDetailScreen | `screens/FacilityDetailScreen.tsx`, `services/toiletUnits.ts`, `utils/toiletUnits.ts` | Supabase facility/read, additive published `toilet_units`, and reports service | Supabase (for facility, optional unit detail, photos, reports) | BACKEND-DEPENDENT — additive model deployed, no child rows | Renders real facility values and explicit unknown states for hours, cost, access notes, ratings and photos; optionally renders published explicit toilet units without fabricating station-toilet coordinates or blocking the parent | Requires live-data smoke test before publishing child rows; TfL canonical promotion remains unauthorized | Authorize a source-specific adjudication/import path separately |
| "Need One Now" emergency | Find experience | `hooks/useFindExperience.ts`, `services/facilities.ts`, `utils/nearestFacility.ts` | Supabase `facilities` table via `find_nearest_facilities` RPC | Supabase + PostGIS | UI IMPLEMENTED — BACKEND-DEPENDENT; source gate passed, device unverified | Requests up to 25 candidates within 25 km, enriches `is_24h` without widening the RPC projection, and ranks confirmed open → unknown → confirmed closed by distance; guest access remains in the routed navigation | Fresh consolidated APK/device run is blocked by local dependency/build prerequisites | Recreate dependencies, build/install the consolidated APK, and exercise the full urgent journey |
| Directions deep links | FacilityDetailScreen | `screens/FacilityDetailScreen.tsx` | Platform maps URLs | Google/Apple/Waze apps | UI IMPLEMENTED | Deep-link buttons exist | Requires maps app installed | Test on device |

---

## Filters

| Feature | Surface | Files | Data Source | Backend Dependency | Status | Evidence | Risk | Next Step |
|---------|---------|-------|-------------|-------------------|--------|----------|------|-----------|
| Basic filters (free, accessible, etc.) | MapScreen, filters service | `services/facilities.ts` | Supabase query filters | Supabase | BACKEND-DEPENDENT | Query builds `.eq()` clauses from filter state | Works only with Supabase backend | Test with real data |
| Advanced filters | AdvancedFiltersScreen | `screens/AdvancedFiltersScreen.tsx` | `FiltersContext` and Supabase query filters | Supabase | BACKEND-DEPENDENT | Uses the existing context as applied source of truth; inactive toggles are unset rather than written as false; provides native accessible controls and unknown-data guidance | Requires real database filter smoke test; `ADVANCED_FILTERS` remains false in environment flags | Enable flag after backend connection |
| Open now filter | facilities service | `services/facilities.ts` | Facility `open_hours` JSONB + `is_24h` boolean | Supabase | CLIENT LOGIC IMPLEMENTED | `getOpenStatus()` handles tri-state (open/closed/unknown) including overnight hours; 984 facilities marked is_24h, 6,718 have weekday-keyed hours | Requires smoke test of filter with real data | Run smoke test |

---

## Startup, Onboarding, and Brand

| Feature | Surface | Files | Data Source | Backend Dependency | Status | Evidence | Risk | Next Step |
|---------|---------|-------|-------------|-------------------|--------|----------|------|-----------|
| Native splash | Expo config plugin | `app.config.js`, `assets/branding/relief-splash-mark.png` | Local approved native mark | Native rebuild | UI IMPLEMENTED | `expo-splash-screen` plugin uses a centred mark on a mint background; Android prebuild generated splash density assets | Development/release build appearance is not yet VERIFIED | Install/run Android build and test release splash |
| Welcome transition | StartupWelcome | `App.tsx`, `screens/StartupWelcome.tsx` | Local decorative vector background | Auth/session startup state | UI IMPLEMENTED | Native welcome layer waits for fonts and initial session decision; tap skips decorative fade; reduced-motion checked | Device transition not yet smoke-tested | Test native hand-off on Android and iOS |
| First-run onboarding | AuthenticatedEntry, OnboardingScreen | `navigation/AppNavigator.tsx`, `screens/OnboardingScreen.tsx`, `utils/onboarding.ts` | User-scoped AsyncStorage plus `FiltersContext` | Supabase Auth session | BACKEND-DEPENDENT | Shows only for an authenticated user without local completion; selected preferences merge only true filter values | Auth/session flow not yet smoke-tested | Verify first sign-in and repeat launch |
| About Relief artwork | Profile, AboutReliefScreen | `screens/ProfileScreen.tsx`, `screens/AboutReliefScreen.tsx`, `assets/branding/relief-brand-poster.jpg` | Local supplied poster | None | UI IMPLEMENTED | Poster is rendered with `contain` and its source aspect ratio; it is not used on startup or the live map | Screen not yet device-tested | Verify large-font and screen-reader presentation |
| Persistent Home | HomeScreen | `screens/HomeScreen.tsx`, `navigation/AppNavigator.tsx` | Local brand assets plus existing navigation actions | Existing Find/Favourites/Auth routes | IMPLEMENTED BUT NOT DEVICE TESTED | Home is the default post-onboarding tab; Find, Need One Now, Saved places, and About Relief are reachable without duplicating facility queries | New APK has not been installed on the S24 Ultra | Build and run the Luna Android acceptance list |

---

## Accessibility

| Feature | Surface | Files | Data Source | Backend Dependency | Status | Evidence | Risk | Next Step |
|---------|---------|-------|-------------|-------------------|--------|----------|------|-----------|
| Accessibility attributes | Facility type, filters | `types/index.ts`, `services/facilities.ts` | Supabase | Supabase | BACKEND-DEPENDENT | 15+ boolean accessibility fields in Facility type; 6,374 accessible facilities imported; enriched: 4,534 with has_staff_nearby, 3,888 with is_gender_neutral, 2,765 with is_family_friendly, 101 with is_single_occupancy; 7,202 with access_notes | Requires smoke test with real data | Run smoke test |
| RADAR key filter | facilities service | `services/facilities.ts` | Supabase | Supabase | BACKEND-DEPENDENT | `requires_radar_key` field in query | UK-specific; may need geography filtering | Confirm UK launch scope |
| Adult changing place | facilities service | `services/facilities.ts` | Supabase | Supabase | BACKEND-DEPENDENT | `has_adult_changing_place` field | Requires verified data | Seed Changing Places data |

---

## Authentication

| Feature | Surface | Files | Data Source | Backend Dependency | Status | Evidence | Risk | Next Step |
|---------|---------|-------|-------------|-------------------|--------|----------|------|-----------|
| Email sign-in | LoginScreen | `screens/LoginScreen.tsx`, `services/auth.ts` | Supabase Auth | Supabase Auth | BACKEND-DEPENDENT | `signInWithPassword()` calls Supabase | Supabase project is user-reported connected; Auth settings not yet smoke-tested | Enable/verify email auth |
| Google OAuth | LoginScreen | `screens/LoginScreen.tsx`, `services/auth.ts` | Supabase Auth + Google | Supabase Auth, Google Cloud OAuth | BACKEND-DEPENDENT | `signInWithOAuth('google')` with WebBrowser flow | Requires Google OAuth configuration separate from Android Maps SDK key | Configure only after email auth/basic browse path is verified |
| Apple OAuth | LoginScreen | `screens/LoginScreen.tsx`, `services/auth.ts` | Supabase Auth + Apple | Supabase Auth, Apple Developer | BACKEND-DEPENDENT | `signInWithOAuth('apple')` with WebBrowser flow | Requires Apple Developer account | Configure for iOS |
| Session persistence | AppNavigator | `navigation/AppNavigator.tsx`, `services/auth.ts` | Supabase Auth | Supabase Auth | BACKEND-DEPENDENT | `onAuthStateChange()` listener + `persistSession: true` | Session may not restore without Supabase | Verify after Supabase connection |
| Guest-capable main entry | AppNavigator | `navigation/AppNavigator.tsx`, `utils/guestAccess.ts` | Supabase session when present; local guest onboarding otherwise | Supabase Auth for account actions only | VERIFIED on parent device; Luna navigation IMPLEMENTED BUT NOT DEVICE TESTED | Main renders for guests and signed-in users; Auth is an on-demand modal for account-dependent actions | The Home-default change needs a fresh device run | Verify Home → Find and guest Need One Now on the Luna APK |

---

## Profiles and Saved Data

| Feature | Surface | Files | Data Source | Backend Dependency | Status | Evidence | Risk | Next Step |
|---------|---------|-------|-------------|-------------------|--------|----------|------|-----------|
| User profile | ProfileScreen | `screens/ProfileScreen.tsx`, `services/account.ts` | Supabase Auth metadata + `user_profiles.display_name` | Supabase Auth + `user_profiles` RLS | IMPLEMENTED BUT NOT DEVICE TESTED | Reads guest/signed-in state and updates both `full_name` metadata and `display_name` with rollback on partial failure | Requires a signed-in device write test | Verify edit, failure handling, and sign-out |
| Saved filter profiles | SavedProfilesScreen | `screens/SavedProfilesScreen.tsx`, `services/profiles.ts` | Supabase `saved_profiles` table | Supabase | BACKEND-DEPENDENT | Profile CRUD operations; 10-profile limit | Feature flag `PREMIUM: false` disables | Enable after premium backend |
| Favourites | Home → Favourites | `screens/FavouritesScreen.tsx`, `navigation/AppNavigator.tsx`, `services/favourites.ts` | Supabase `favourites` table | Supabase | IMPLEMENTED BUT NOT DEVICE TESTED on Luna branch | Remains account-dependent, retains bottom navigation, and returns naturally to Home through the nested stack | Requires a fresh navigation/device run | Verify guest truthfulness, signed-in list, and back behavior |

---

## Community Contributions

| Feature | Surface | Files | Data Source | Backend Dependency | Status | Evidence | Risk | Next Step |
|---------|---------|-------|-------------|-------------------|--------|----------|------|-----------|
| Facility submission | AddFacilityScreen | `screens/AddFacilityScreen.tsx`, `services/community.ts` | Supabase `facility_submissions` | Supabase | VERIFIED | Live A/B owner create/read and isolation passed; pending-only insert policy and column grants deny client moderation fields | Moderation still requires a separate admin path; no client moderation path is enabled | Verify the approved admin moderation surface separately |
| Photo upload | community service | `services/community.ts` | Supabase Storage `facility-photos` | Supabase Storage | BACKEND-DEPENDENT | Upload to storage; insert into `photo_moderation` | **No EXIF stripping or face blurring** — fields set to `false` | Implement server-side media processing |
| Temporary reports | ReportFacilityScreen | `screens/ReportFacilityScreen.tsx`, `services/community.ts` | Supabase `temporary_reports` | Supabase | VERIFIED | Live A/B owner create/resolve/idempotency and isolation passed; direct broad UPDATE is denied | Expiry automation remains a separate operational concern | Verify scheduled expiry separately |
| Corrections | CorrectInfoScreen | `screens/CorrectInfoScreen.tsx`, `services/community.ts` | Supabase `correction_requests` | Supabase | VERIFIED | Live A/B owner create/read and isolation passed; pending-only insert policy and column grants deny client moderation fields | Moderation remains a separate admin concern | Verify the approved admin moderation surface separately |
| Badges | ProfileScreen, community service | `services/community.ts` | Supabase `user_badges` | Supabase | VERIFIED (bounded) | Governed trigger awarded Explorer from a genuine facility-submission row; direct client writes were denied; client reads remain | Other threshold crossings were not recreated in this bounded run | Retain governed trigger path and verify further thresholds in a dedicated approved test |
| Rate limiting | community service | `services/community.ts` | Supabase `rate_limits` table | Supabase | VERIFIED (bounded) | Own records/readback and arbitrary-other-user denial passed | **Client-side checks are not security** — server-side abuse enforcement remains unresolved | Move enforcement to an approved server-side boundary |
| Reviews | rating functions in facilities | `services/facilities.ts` | Supabase | Supabase | BACKEND-DEPENDENT | Rating fields in Facility type | No review submission UI found | Verify review flow completeness |

---

## Premium Features

| Feature | Surface | Files | Data Source | Backend Dependency | Status | Evidence | Risk | Next Step |
|---------|---------|-------|-------------|-------------------|--------|----------|------|-----------|
| Route planning | RoutePlanningScreen | `screens/RoutePlanningScreen.tsx`, `services/routePlanning.ts` | Supabase `facilities` for geocoding | Supabase | BACKEND-DEPENDENT | Haversine straight-line; 80 km/h assumption; no road routing | **Not road-aware**; geocoding uses facility table lookup | Integrate road-routing API; use proper geocoder |
| Offline facility data | OfflineMapsScreen | `screens/OfflineMapsScreen.tsx`, `services/offlineMaps.ts` | expo-sqlite local DB; Supabase for download | Supabase | BACKEND-DEPENDENT | Downloads facility JSON to SQLite; 12 UK towns pre-listed | **Not offline maps** — no map tiles, no offline rendering | Rename to "offline facility data"; document limitation |
| Smart alerts | NotificationAlertsScreen | `screens/NotificationAlertsScreen.tsx`, `services/notificationAlerts.ts` | Supabase for reports; AsyncStorage for prefs | Supabase | BACKEND-DEPENDENT | Local foreground polling; 1-hour in-memory cooldown | **Not background** — lost on app kill; not server-triggered | Implement server-side push after backend exists |
| Location sharing | LocationSharingScreen | `screens/LocationSharingScreen.tsx`, `services/locationSharing.ts` | what3words API (optional); local Plus Code | what3words API | MOCKED (W3W), CLIENT LOGIC IMPLEMENTED (Plus Code) | W3W returns simulated words without API key; Plus Code is simplified algorithm | **Safety risk** — simulated W3W words are not real locations | Disable simulation; require API key or remove feature |
| Subscriptions (RevenueCat) | PaywallScreen, SubscriptionContext | `screens/PaywallScreen.tsx`, `services/revenuecat.ts`, `context/SubscriptionContext.tsx` | RevenueCat SDK | RevenueCat, Supabase webhook | BLOCKED | No API keys; falls to console warning "Using mock mode" | Cannot process payments | Configure RevenueCat; deploy webhook |
| Premium gating | PremiumGate | `components/PremiumGate.tsx` | SubscriptionContext | RevenueCat | UI IMPLEMENTED | Gate component exists; feature flag `PREMIUM: false` | Currently disabled | Enable after RevenueCat configuration |

---

## Recommendation Logic ("AI")

| Feature | Surface | Files | Data Source | Backend Dependency | Status | Evidence | Risk | Next Step |
|---------|---------|-------|-------------|-------------------|--------|----------|------|-----------|
| Smart recommendations | AIRecommendationsScreen | `screens/AIRecommendationsScreen.tsx`, `services/aiRecommendations.ts` | Supabase `facilities`; local scoring | Supabase | CLIENT LOGIC IMPLEMENTED | Deterministic weighted scoring (preferences 40%, rating 25%, distance 20%, open 10%, freshness 5%) | **Not AI** — no model, no learning, no external service; flag `AI: false` disables | Rename to "Smart Recommendations"; remove AI branding until model-backed |
| Predictive suggestions | PredictiveSuggestionsScreen | `screens/PredictiveSuggestionsScreen.tsx`, `services/aiRecommendations.ts` | Supabase `facilities`; client calculation | Supabase | BACKEND-DEPENDENT | Finds highest-scored facility ahead on route | Requires functioning route and facility data | Implement after route planning is road-aware |
| AI ranking | aiRecommendations service | `services/aiRecommendations.ts` | Client-side scoring | None | CLIENT LOGIC IMPLEMENTED | Weighted multi-factor scoring algorithm | Same scoring used for all "AI" features | Rename; consider model-backed upgrade in future phase |

---

## Administration

| Feature | Surface | Files | Data Source | Backend Dependency | Status | Evidence | Risk | Next Step |
|---------|---------|-------|-------------|-------------------|--------|----------|------|-----------|
| Admin panel | None | No admin UI files exist | N/A | Supabase moderator RPCs | PLANNED | Web/internal admin surface remains the recommended interface; live queue and decision RPCs are deployed | No permanent moderator identity or portal | Approve a production moderator roster and admin-surface design |
| Moderation tools | None (source service only) | `src/services/moderation.ts`, governed migration | Supabase moderation RPCs | Supabase | VERIFIED | Live queues and decision RPCs passed ordinary-user denial, moderator authorization, server-derived reviewer, replay, and cleanup tests | No permanent moderator roster/UI; canonical application, photo moderation, and review moderation remain outside scope | Authorize a moderator roster and separate canonical-application design |
| Report expiry automation | Edge Function | `supabase/functions/expire-reports/index.ts` | Supabase cron + Edge Function | Supabase | PLANNED | Deno function written; not deployed | Reports would never expire without this | Deploy after Supabase project exists |

---

## Privacy and Account Management

| Feature | Surface | Files | Data Source | Backend Dependency | Status | Evidence | Risk | Next Step |
|---------|---------|-------|-------------|-------------------|--------|----------|------|-----------|
| Account deletion | Profile → Delete account | `screens/AccountDeletionScreen.tsx`, `services/accountDeletion.ts`, `supabase/functions/delete-account/`, `supabase/migrations/20260814135046_account_deletion_cleanup_contract.sql` | Supabase Auth, Postgres, Storage API | Governed Edge Function + Auth Admin API | BACKEND-DEPENDENT | Production migration and `delete-account` Edge Function are deployed; disposable-account flow verified; subscription-history accounts fail closed | Public privacy/support/data-rights materials, public deletion URL, unresolved retention wording, and real Storage-object deletion remain open | Publish approved legal/support surfaces; complete store-console disclosures; separately verify Storage when photo uploads are approved |
| Data export | Profile → Privacy & Data → Download my data | `services/dataExport.ts`, `screens/ProfileScreen.tsx`, `supabase/functions/export-account/`, `docs/DATA_EXPORT_CONTRACT.md` | Supabase Auth, explicit user-scoped Postgres reads | Server-governed Edge Function; native share sheet | LIVE DEPLOYED / VERIFIED | Versioned JSON envelope, subject-derived identity, recent-auth boundary, redacted inventory, two-way cross-user isolation, contribution/photo/provider redaction, repeatability, and non-mutation passed with two disposable accounts | Protected moderation-summary sources remain explicitly disclosed as partially unavailable; access-code export remains a later privacy/product decision | Keep the moderation limitation and access-code decision under review; no security weakening is required |
| Location privacy | useLocation hook | `hooks/useLocation.ts` | expo-location | None | UI IMPLEMENTED | Requests location permission; foreground only | Location usage descriptions in app.json | Verify no background tracking; add location clearing |
| Photo EXIF stripping | community service | `services/community.ts` | Supabase Storage | Supabase Edge Function | PLANNED | `exif_stripped: false` inserted; no processing | **Privacy risk** — location metadata in uploaded photos | Implement server-side EXIF removal |
| Face blurring | community service | `services/community.ts` | Supabase Storage | Supabase Edge Function | PLANNED | `faces_blurred: false` inserted; no processing | **Privacy risk** — identifiable faces in photos | Implement server-side blurring |

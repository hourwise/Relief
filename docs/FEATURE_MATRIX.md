# Relief — Feature Matrix

**Last verified:** 2026-08-12
**Verification method:** Phase B post-Apply source audit, contract regression tests, Expo SDK 56 clean disposable prebuild, and current/clean Android Gradle reproduction. No production mutation, authenticated production write, upload, or release signing was performed.

## Phase B post-Apply integration overlay - 2026-08-12

This overlay supersedes older device/build notes where they conflict. It does
not convert catalog compatibility into a live authenticated write test.

| Surface | Status | Evidence / boundary |
|---------|--------|---------------------|
| Published facility reads | CATALOG_COMPATIBLE_NOT_LIVE_WRITE_TESTED | Current read-only evidence is compatible with anonymous published-facility reads. |
| Nearest-facility RPC | CATALOG_COMPATIBLE_NOT_LIVE_WRITE_TESTED | Anonymous/authenticated EXECUTE is compatible; the RPC is not security definer. |
| Favourites, profile, reports, corrections, facility submissions, rate limits, access codes, review reports | CATALOG_COMPATIBLE_NOT_LIVE_WRITE_TESTED | Authenticated owner-flow catalog evidence is compatible; no production write was attempted. |
| Saved profiles | CATALOG_COMPATIBLE_NOT_LIVE_WRITE_TESTED | Catalog-compatible but unreachable while the feature is disabled. |
| Subscription events | BACKEND-DEPENDENT | Server-write-only boundary; premium remains disabled. |
| Badge award side effect | BLOCKED_BY_RLS | `user_badges` has no authenticated INSERT policy; client submission remains successful when award insertion is denied or throws. |
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
| Facility detail | FacilityDetailScreen | `screens/FacilityDetailScreen.tsx` | Supabase facility/read and reports service | Supabase (for facility, photos, reports) | BACKEND-DEPENDENT | Renders real facility values and explicit unknown states for hours, cost, access notes, ratings and photos; coordinate directions retained | Device/data behaviour not yet smoke-tested | Verify with real facility data |
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
| Facility submission | AddFacilityScreen | `screens/AddFacilityScreen.tsx`, `services/community.ts` | Supabase `facility_submissions` | Supabase | BACKEND-DEPENDENT | Submission with moderation queue; rate limiting (3/hr) | No moderation UI exists | Deploy migration; build admin panel |
| Photo upload | community service | `services/community.ts` | Supabase Storage `facility-photos` | Supabase Storage | BACKEND-DEPENDENT | Upload to storage; insert into `photo_moderation` | **No EXIF stripping or face blurring** — fields set to `false` | Implement server-side media processing |
| Temporary reports | ReportFacilityScreen | `screens/ReportFacilityScreen.tsx`, `services/community.ts` | Supabase `temporary_reports` | Supabase | BACKEND-DEPENDENT | Reports with expiry; duplicate detection | Expiry requires Edge Function cron | Deploy expire-reports function |
| Corrections | CorrectInfoScreen | `screens/CorrectInfoScreen.tsx`, `services/community.ts` | Supabase `correction_requests` | Supabase | BACKEND-DEPENDENT | Permanent edits to moderation queue | No admin review UI | Build moderation dashboard |
| Badges | ProfileScreen, community service | `services/community.ts` | Supabase `badges`/`user_badges` | Supabase | BACKEND-DEPENDENT | 4 badge types with award logic | Requires tracking user contribution counts | Deploy migration |
| Rate limiting | community service | `services/community.ts` | Supabase `rate_limits` table | Supabase | BACKEND-DEPENDENT | Client-side rate limit checks against Supabase table | **Client-side checks are not security** — must be enforced server-side | Move to Edge Function enforcement |
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
| Admin panel | None | No admin UI files exist | N/A | Supabase (service_role) | PLANNED | Referenced in plan; no implementation | No moderation tools exist | Build admin dashboard after backend |
| Moderation tools | None | No moderation UI | Supabase | Supabase | PLANNED | Approve/reject/edit/remove operations planned | Community contributions cannot be reviewed | Build after facility_submissions table deployed |
| Report expiry automation | Edge Function | `supabase/functions/expire-reports/index.ts` | Supabase cron + Edge Function | Supabase | PLANNED | Deno function written; not deployed | Reports would never expire without this | Deploy after Supabase project exists |

---

## Privacy and Account Management

| Feature | Surface | Files | Data Source | Backend Dependency | Status | Evidence | Risk | Next Step |
|---------|---------|-------|-------------|-------------------|--------|----------|------|-----------|
| Account deletion | Not found | No account deletion flow found | N/A | Supabase Auth | PLANNED | Referenced in security addendum; no implementation | GDPR compliance gap | Implement deletion UI + server-side handler |
| Data export | Not found | No data export flow found | N/A | Supabase | PLANNED | Referenced in security addendum; no implementation | GDPR compliance gap | Implement export UI + server-side handler |
| Location privacy | useLocation hook | `hooks/useLocation.ts` | expo-location | None | UI IMPLEMENTED | Requests location permission; foreground only | Location usage descriptions in app.json | Verify no background tracking; add location clearing |
| Photo EXIF stripping | community service | `services/community.ts` | Supabase Storage | Supabase Edge Function | PLANNED | `exif_stripped: false` inserted; no processing | **Privacy risk** — location metadata in uploaded photos | Implement server-side EXIF removal |
| Face blurring | community service | `services/community.ts` | Supabase Storage | Supabase Edge Function | PLANNED | `faces_blurred: false` inserted; no processing | **Privacy risk** — identifiable faces in photos | Implement server-side blurring |

# Relief — Feature Matrix

**Last verified:** 2026-07-12  
**Verification method:** Source code audit of all files under `relief-app/src/`

Each feature is assessed against the current repository, not against plans or intentions.

---

## Core Search and Discovery

| Feature | Surface | Files | Data Source | Backend Dependency | Status | Evidence | Risk | Next Step |
|---------|---------|-------|-------------|-------------------|--------|----------|------|-----------|
| Map view with pins | MapScreen | `screens/MapScreen.tsx` | Supabase `facilities` table | Supabase | BACKEND-DEPENDENT | `fetchNearbyFacilities()` calls Supabase; uses `PROVIDER_GOOGLE` | Cannot render without Supabase project and API key | Create Supabase project; add seed data |
| Map clustering | MapScreen | `screens/MapScreen.tsx` | Client-side calculation | None | CLIENT LOGIC IMPLEMENTED | `clusterFacilities()` groups by coordinate proximity | Grid-based, not true pixel-distance clustering | Test with real data densities |
| List view | ListScreen | `screens/ListScreen.tsx` | Hardcoded array `MOCK_FACILITIES` | None | MOCKED | 3 Liverpool facilities hardcoded; no Supabase query | Shows fake data; no distance sorting | Replace with Supabase query when backend available |
| Search by town/postcode | MapScreen | `screens/MapScreen.tsx` | Supabase `facilities` table | Supabase | BACKEND-DEPENDENT | `searchFacilities()` queries Supabase | Cannot search without backend | Implement after Supabase connection |
| Facility detail | FacilityDetailScreen | `screens/FacilityDetailScreen.tsx` | Passed via navigation params | Supabase (for photos, reports) | UI IMPLEMENTED | Screen renders detail layout | Unknown if all fields display correctly | Verify with real facility data |
| "Need One Now" emergency | MapScreen | `screens/MapScreen.tsx` | Supabase `facilities` table | Supabase | BACKEND-DEPENDENT | `fetchClosestFacility()` + `estimateWalkingTime()` | **Cannot be accessed without login** — auth gate blocks unauthenticated users | Fix auth gate; allow unauthenticated emergency access |
| Directions deep links | FacilityDetailScreen | `screens/FacilityDetailScreen.tsx` | Platform maps URLs | Google/Apple/Waze apps | UI IMPLEMENTED | Deep-link buttons exist | Requires maps app installed | Test on device |

---

## Filters

| Feature | Surface | Files | Data Source | Backend Dependency | Status | Evidence | Risk | Next Step |
|---------|---------|-------|-------------|-------------------|--------|----------|------|-----------|
| Basic filters (free, accessible, etc.) | MapScreen, filters service | `services/facilities.ts` | Supabase query filters | Supabase | BACKEND-DEPENDENT | Query builds `.eq()` clauses from filter state | Works only with Supabase backend | Test with real data |
| Advanced filters | AdvancedFiltersScreen | `screens/AdvancedFiltersScreen.tsx` | Feature flag gated | Supabase | BACKEND-DEPENDENT | Screen exists; flag `ADVANCED_FILTERS: false` | Currently disabled | Enable flag after backend connection |
| Open now filter | facilities service | `services/facilities.ts` | Facility `open_hours` JSONB | Supabase | CLIENT LOGIC IMPLEMENTED | Time-range comparison logic exists | Requires `open_hours` data in database | Populate open hours in seed data |

---

## Accessibility

| Feature | Surface | Files | Data Source | Backend Dependency | Status | Evidence | Risk | Next Step |
|---------|---------|-------|-------------|-------------------|--------|----------|------|-----------|
| Accessibility attributes | Facility type, filters | `types/index.ts`, `services/facilities.ts` | Supabase | Supabase | BACKEND-DEPENDENT | 15+ boolean accessibility fields in Facility type | Requires populated data | Seed accessibility data |
| RADAR key filter | facilities service | `services/facilities.ts` | Supabase | Supabase | BACKEND-DEPENDENT | `requires_radar_key` field in query | UK-specific; may need geography filtering | Confirm UK launch scope |
| Adult changing place | facilities service | `services/facilities.ts` | Supabase | Supabase | BACKEND-DEPENDENT | `has_adult_changing_place` field | Requires verified data | Seed Changing Places data |

---

## Authentication

| Feature | Surface | Files | Data Source | Backend Dependency | Status | Evidence | Risk | Next Step |
|---------|---------|-------|-------------|-------------------|--------|----------|------|-----------|
| Email sign-in | LoginScreen | `screens/LoginScreen.tsx`, `services/auth.ts` | Supabase Auth | Supabase Auth | BACKEND-DEPENDENT | `signInWithPassword()` calls Supabase | Cannot authenticate without Supabase project | Create Supabase project; enable email auth |
| Google OAuth | LoginScreen | `screens/LoginScreen.tsx`, `services/auth.ts` | Supabase Auth + Google | Supabase Auth, Google Cloud | BACKEND-DEPENDENT | `signInWithOAuth('google')` with WebBrowser flow | Requires Google Cloud project + Supabase config | Configure after Supabase project exists |
| Apple OAuth | LoginScreen | `screens/LoginScreen.tsx`, `services/auth.ts` | Supabase Auth + Apple | Supabase Auth, Apple Developer | BACKEND-DEPENDENT | `signInWithOAuth('apple')` with WebBrowser flow | Requires Apple Developer account | Configure for iOS |
| Session persistence | AppNavigator | `navigation/AppNavigator.tsx`, `services/auth.ts` | Supabase Auth | Supabase Auth | BACKEND-DEPENDENT | `onAuthStateChange()` listener + `persistSession: true` | Session may not restore without Supabase | Verify after Supabase connection |
| Auth gate (blocks unauthenticated) | AppNavigator | `navigation/AppNavigator.tsx` | Supabase Auth | Supabase Auth | UI IMPLEMENTED | Root navigator shows LoginScreen when no session | **Blocks urgent access for unauthenticated users** | Add unauthenticated browse path |

---

## Profiles and Saved Data

| Feature | Surface | Files | Data Source | Backend Dependency | Status | Evidence | Risk | Next Step |
|---------|---------|-------|-------------|-------------------|--------|----------|------|-----------|
| User profile | ProfileScreen | `screens/ProfileScreen.tsx` | Supabase Auth user | Supabase Auth | BACKEND-DEPENDENT | Reads `user.email`, `user.user_metadata` | No editable profile fields beyond auth data | Implement after auth |
| Saved filter profiles | SavedProfilesScreen | `screens/SavedProfilesScreen.tsx`, `services/profiles.ts` | Supabase `saved_profiles` table | Supabase | BACKEND-DEPENDENT | Profile CRUD operations; 10-profile limit | Feature flag `PREMIUM: false` disables | Enable after premium backend |
| Favourites | FavouritesScreen | `screens/FavouritesScreen.tsx`, `services/favourites.ts` | Supabase `favourites` table | Supabase | BACKEND-DEPENDENT | Add/remove/check/count operations | Requires `favourites` table with RLS | Deploy migration; test |

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

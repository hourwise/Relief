# Relief — Current State Assessment

**Last verified:** 2026-07-25  
**Verification method:** Full UK facility import completed (15,584 facilities from Toilet Map UK); database records verified; app smoke testing still pending  
**TypeScript check:** Not rerun in this pass; previous run (`npx tsc --noEmit`) showed 11 errors, all in Supabase Deno Edge Functions (expected, Deno runtime not available)  
**Build check:** Not run (no EAS/local build configured)  
**Test suite:** Not run (no test scripts exist)

---

## Executive Summary

Relief is a **frontend-heavy prototype** built with React Native and Expo SDK 56. The application has 18 screens, 13 service modules, comprehensive UI components, and a well-structured navigation system. Four Supabase SQL migration files define the intended database schema, and the development Supabase schema push is user-reported but not yet app-verified.

Backend setup has started. Supabase development URL/anon key names are present locally, and Android Google Maps SDK configuration is now aligned through Expo app config to `EXPO_PUBLIC_GOOGLE_MAPS_API_KEY`. RevenueCat, what3words, notifications infrastructure, storage, moderation pipeline, and most other external services are still not configured. The application is not yet VERIFIED end-to-end.

The codebase demonstrates a clear product vision and substantial implementation effort, but the gap between the UI code and a working end-to-end product is significant.

---

## Repository Maturity

| Aspect | Assessment |
|--------|-----------|
| **Code organisation** | Well-structured — clear separation of screens, services, components, theme, types |
| **TypeScript coverage** | Full — all application code is TypeScript with strict mode enabled |
| **Component library** | Implemented — Button, Card, Input, Badge, AnimatedPin, PremiumGate |
| **Navigation** | Implemented — React Navigation 7 with auth-gated root, 4-tab main navigator, map stack |
| **Theme system** | Implemented — colours, typography, spacing tokens consistent with design system |
| **i18n infrastructure** | Implemented — i18next with English locale, nested key structure |
| **Database schema** | Designed — 4 migration files + trust model/provenance tables; 15,584 UK facilities imported with source tracking; enriched from Toilet Map UK raw_data (access_notes, opening hours, accessibility flags); field-level provenance tracking; PostGIS enabled with geography(Point, 4326) generated column and GiST spatial index; find_nearest_facilities RPC for server-side nearest lookup |
| **Edge Functions** | Written — 2 Deno functions (expire-reports, revenuecat-webhook) |
| **Testing** | None — no test scripts, no test files, no CI configuration |
| **Linting/formatting** | None — no ESLint, Prettier, or formatting scripts configured |
| **CI/CD** | None — no EAS Build/Submit pipeline, no GitHub Actions |
| **Environment config** | Development `.env` exists locally; `.env.example` documents expected public variables; no startup validation |

---

## Actual Frontend State

### What works (UI-only, no backend)

| Component | Status | Evidence |
|-----------|--------|----------|
| Login screen UI | UI IMPLEMENTED | `LoginScreen.tsx` — email, Google, Apple buttons rendered |
| Map screen with markers | UI IMPLEMENTED | `MapScreen.tsx` — MapView with PROVIDER_GOOGLE, clustering, emergency button; PostGIS nearest-facility RPC wired |
| List screen | BACKEND-DEPENDENT | `ListScreen.tsx` — Supabase query exists; 15,584 UK facilities now in database; needs client-side verification |
| Facility detail screen | UI IMPLEMENTED | `FacilityDetailScreen.tsx` — detail layout exists |
| Profile screen | UI IMPLEMENTED | `ProfileScreen.tsx` — user info, badges, sign-out |
| Favourites screen | UI IMPLEMENTED | `FavouritesScreen.tsx` — list with empty state |
| All premium screens | UI IMPLEMENTED | RoutePlanning, OfflineMaps, SavedProfiles, etc. |

### Navigation structure

- **Root:** Auth check → LoginScreen (unauthenticated) or MainNavigator (authenticated)
- **Tabs:** Map, List (Nearby), Favourites, Profile — **4 tabs**, not the 3-tab maximum specified in the accessibility policy
- **Map stack:** MapView → FacilityDetail, AddFacility, ReportFacility, CorrectInfo, AdvancedFilters
- **Critical finding:** There is **no unauthenticated path** to the map or "Need One Now" functionality. Users must sign in before reaching any facility discovery.

---

## Backend and External Service State

### Supabase

| Component | Status | Detail |
|-----------|--------|--------|
| Supabase project | BACKEND-DEPENDENT | Development project connected per user report; app workflows not yet smoke-tested |
| Database tables | BACKEND-DEPENDENT | Schemas amended and pushed per user report; seed data and client queries not yet verified |
| Row Level Security | BACKEND-DEPENDENT | RLS policies defined in migrations and user-reported pushed; behaviour not yet verified |
| Auth (email/OAuth) | BACKEND-DEPENDENT | Code calls Supabase Auth; configured project needs smoke testing |
| Storage buckets | PLANNED | Code references `facility-photos` bucket; bucket does not exist |
| Edge Functions | PLANNED | 2 Deno functions written; not deployed |
| Anon key | BACKEND-DEPENDENT | Key name present in local `.env`; value not read; client initialisation needs smoke testing |
| Service role key | BLOCKED | Not present in codebase (correct) |

### External services

| Service | Status | Detail |
|---------|--------|--------|
| Map provider | BACKEND-DEPENDENT | Google Maps selected for Android MVP; Android SDK API key name present in local `.env`; Android build smoke test pending; iOS Google Maps not configured |
| RevenueCat | BLOCKED | No API keys; falls through to "mock mode" console warning |
| what3words | MOCKED | Returns simulated words when no API key; fallback words are deterministic from coordinates |
| Plus Codes | CLIENT LOGIC IMPLEMENTED | Simplified client-side algorithm; unknown accuracy vs official library |
| Notifications | BACKEND-DEPENDENT | `expo-notifications` configured; push token registration code exists; no push server |
| Photo processing | PLANNED | `photo_moderation` table references `exif_stripped` and `faces_blurred` fields; no processing pipeline exists |
| Image moderation | PLANNED | Moderation queue schema exists; no integration with moderation service |
| Directions | UI IMPLEMENTED | Deep-link buttons exist; would open Google/Apple/Waze if tapped |
| Geocoding | BACKEND-DEPENDENT | Route planner uses facilities table for geocoding; no geocoding API configured |

---

## Known Mocks, Fallbacks, and Approximations

| Feature | Approximation | Risk |
|---------|---------------|------|
| List screen data | 3 hardcoded Liverpool facilities | Cannot demonstrate real data |
| what3words | Deterministic simulated words from coordinate hash | **User safety risk** — simulated words are not real locations |
| Plus Codes | Simplified client-side algorithm | May not match official Open Location Code specification |
| Route planning | Haversine straight-line distance; 80 km/h assumed speed | Not road-aware; unsuitable for navigation |
| "Offline maps" | Downloads facility JSON records only, not map tiles | Name is misleading; no offline map rendering |
| "AI recommendations" | Deterministic weighted scoring algorithm | Not AI; feature flag `AI: false` confirms this |
| Alerts | Local foreground polling with in-memory cooldown | Not background; lost on app restart |
| Photo uploads | Sets `exif_stripped: false, faces_blurred: false` in moderation queue | No processing occurs; privacy obligations unmet |

---

## Feature Flag Status

From `src/utils/env.ts`:

| Flag | Value | Effect |
|------|-------|--------|
| `COMMUNITY` | `true` | Community features enabled in UI |
| `ADVANCED_FILTERS` | `false` | Advanced filter screens may not render |
| `PREMIUM` | `false` | Premium features gated |
| `AI` | `false` | AI-branded features disabled |
| `EUROPE` | `false` | Europe expansion disabled |

---

## Current Blockers

1. **Supabase smoke testing pending** — Development project/schema are user-reported connected, but app reads/auth/storage workflows are not VERIFIED
2. **Auth-gated navigation** — Contradicts "no login required for basic search" policy
3. ~~No verified seed data~~ **SEED DATA IMPORTED** — 15,584 UK public toilet facilities imported from Toilet Map UK (CC-BY-4.0); enriched with access_notes (7,202), price_note (1,315), last_verified_at (2,219), is_24h (984), is_gender_neutral (3,888), has_staff_nearby (4,534), is_family_friendly (2,765), is_single_occupancy (101); field-level provenance tracking enabled
4. **No RevenueCat configuration** — Blocks monetisation
5. **No storage bucket/media pipeline** — Photo uploads lack bucket setup, EXIF stripping, and face blurring
6. **No moderation pipeline** — Community submissions cannot be reviewed safely
7. **what3words simulation** — Returns fake location codes (safety risk)
8. **No testing infrastructure** — No way to verify correctness
9. **iOS map configuration deferred** — Current Google Maps setup is Android-only for development

---

## Checks Run and Not Run

| Check | Status | Result |
|-------|--------|--------|
| TypeScript (`tsc --noEmit`) | Run | 11 errors in Deno Edge Functions only (expected); 0 errors in app code |
| ESLint | Not run | No ESLint configured |
| Prettier | Not run | No Prettier configured |
| Unit tests | Not run | No test scripts or test files exist |
| Build (EAS) | Not run | No EAS configuration |
| Expo start | Not run | Would fail without `.env` file |
| Dependency audit | Not run | No audit script |

---

## Safe Next Action

**Run the first end-to-end smoke test on Android**, starting with:

1. Verify Expo config resolves the Android Google Maps SDK key for a development build
2. ~~Load seed data for a single UK town~~ **DONE** — 15,584 UK facilities in Supabase (104 Liverpool, full UK)
3. Replace/mock-bypass the hardcoded list data with Supabase reads for the smoke path
4. Verify map pins render with real coordinates from Supabase
5. Verify "Need One Now" can find the nearest seeded facility
6. Decide and implement unauthenticated access for basic emergency discovery

# Relief — Current State Assessment

**Last verified:** 2026-07-12  
**Verification method:** Full repository audit — all source files, configuration, migrations, and documentation read  
**TypeScript check:** Run (`npx tsc --noEmit`) — 11 errors, all in Supabase Deno Edge Functions (expected, Deno runtime not available)  
**Build check:** Not run (no EAS/local build configured)  
**Test suite:** Not run (no test scripts exist)

---

## Executive Summary

Relief is a **frontend-heavy prototype** built with React Native and Expo SDK 56. The application has 18 screens, 13 service modules, comprehensive UI components, and a well-structured navigation system. Four Supabase SQL migration files define the intended database schema.

**No backend is connected.** Supabase, mapping services, RevenueCat, what3words, notifications infrastructure, storage, moderation pipeline, and all other external services are not configured. The application cannot function as a usable product without a backend.

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
| **Database schema** | Designed — 4 migration files covering facilities, community, premium, monetisation tables |
| **Edge Functions** | Written — 2 Deno functions (expire-reports, revenuecat-webhook) |
| **Testing** | None — no test scripts, no test files, no CI configuration |
| **Linting/formatting** | None — no ESLint, Prettier, or formatting scripts configured |
| **CI/CD** | None — no EAS Build/Submit pipeline, no GitHub Actions |
| **Environment config** | Template only — `.env.example` exists, no `.env` file, no startup validation |

---

## Actual Frontend State

### What works (UI-only, no backend)

| Component | Status | Evidence |
|-----------|--------|----------|
| Login screen UI | UI IMPLEMENTED | `LoginScreen.tsx` — email, Google, Apple buttons rendered |
| Map screen with markers | UI IMPLEMENTED | `MapScreen.tsx` — MapView with PROVIDER_GOOGLE, clustering, emergency button |
| List screen | MOCKED | `ListScreen.tsx` — 3 hardcoded Liverpool facilities, no Supabase query |
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
| Supabase project | BLOCKED | No project created or connected |
| Database tables | PLANNED | 4 migration files exist but are not deployed |
| Row Level Security | PLANNED | RLS policies defined in migrations but not applied |
| Auth (email/OAuth) | BACKEND-DEPENDENT | Code calls Supabase Auth; no project to authenticate against |
| Storage buckets | PLANNED | Code references `facility-photos` bucket; bucket does not exist |
| Edge Functions | PLANNED | 2 Deno functions written; not deployed |
| Anon key | BLOCKED | No key; defaults to empty string in `env.ts` |
| Service role key | BLOCKED | Not present in codebase (correct) |

### External services

| Service | Status | Detail |
|---------|--------|--------|
| Map provider | BACKEND-DEPENDENT | `react-native-maps` with `PROVIDER_GOOGLE`; no API key configured |
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

1. **No Supabase project** — Blocks all data operations, authentication, storage, and edge functions
2. **No mapping API key** — Blocks map rendering and geocoding
3. **No RevenueCat configuration** — Blocks monetisation
4. **Auth-gated navigation** — Contradicts "no login required for basic search" policy
5. **No seed data** — No facility data exists for any geography
6. **No moderation pipeline** — Photo uploads lack EXIF stripping and face blurring
7. **what3words simulation** — Returns fake location codes (safety risk)
8. **No testing infrastructure** — No way to verify correctness
9. **Undecided map provider** — Google Maps vs Mapbox name confusion in config

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

**Complete the decisions in `docs/DECISIONS_NEEDED.md`** before any implementation, starting with:

1. Confirm map provider (Google Maps via `react-native-maps` is the current implementation)
2. Decide whether urgent discovery must work without authentication
3. Create a Supabase project for development
4. Apply existing migrations to a development database
5. Load seed data for a single UK town
6. Add a `.env` file with development values
7. Verify the map renders with real coordinates and a valid API key

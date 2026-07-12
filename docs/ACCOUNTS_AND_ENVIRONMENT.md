# Relief — Accounts and Environment Setup Register

**Last updated:** 2026-07-12  
**Status:** No accounts or services are currently configured. All are pending.

This document records every external service the project requires, its purpose, current state, and setup dependencies. It contains **no secrets, keys, or credentials** — only placeholders and classifications.

---

## Required Services and Accounts

### Project Identity

| Item | Detail |
|------|--------|
| **Project email** | TBD — needed for all service accounts |
| **Current state** | BLOCKED — not yet established |
| **Purpose** | Apple Developer, Google Play Console, Supabase, RevenueCat, support contact, privacy policy contact, domain registration |

---

### Supabase

| Item | Detail |
|------|--------|
| **Purpose** | Backend: Postgres database, Auth, Storage, Edge Functions |
| **Current state** | BLOCKED — no project created |
| **Intended owner** | Project email |
| **Environments needed** | Development, Staging, Production (separate projects recommended) |
| **Setup dependencies** | Project email |
| **Docs** | `https://supabase.com/docs` |

**Variables:**
| Variable | Classification | Notes |
|----------|---------------|-------|
| `EXPO_PUBLIC_SUPABASE_URL` | Public (client bundle) | Supabase project URL |
| `EXPO_PUBLIC_SUPABASE_ANON_KEY` | Public (client bundle) | Anon key — safe for client; RLS-enforced |
| `SUPABASE_SERVICE_ROLE_KEY` | **Server-only secret** | NEVER in client code or `.env`; Edge Functions only |

---

### Expo / EAS

| Item | Detail |
|------|--------|
| **Purpose** | App framework, build service, OTA updates |
| **Current state** | Local development only; no EAS account required yet |
| **Intended owner** | Project email |
| **Setup dependencies** | None for local dev; project email for EAS |
| **Docs** | `https://docs.expo.dev/` |

**Variables:**
| Variable | Classification | Notes |
|----------|---------------|-------|
| `EXPO_PUBLIC_*` prefix | Public (client bundle) | All `EXPO_PUBLIC_*` variables are bundled with the app |

---

### Mapping Provider

| Item | Detail |
|------|--------|
| **Purpose** | Map display, geocoding, potentially directions |
| **Current state** | BLOCKED — provider not confirmed (see D01) |
| **Current code default** | Google Maps via `react-native-maps` |
| **Intended owner** | Project email |
| **Setup dependencies** | D01 decision; billing account |
| **Docs** | Google Maps: `https://developers.google.com/maps`; Mapbox: `https://docs.mapbox.com/` |

**Variables:**
| Variable | Classification | Notes |
|----------|---------------|-------|
| `EXPO_PUBLIC_MAPBOX_ACCESS_TOKEN` (current name) | Public (client bundle) | Confusingly named — used for Google Maps API key in `app.json`. Rename to match provider. |

---

### Routing Provider

| Item | Detail |
|------|--------|
| **Purpose** | Road-aware route calculation for route planning feature |
| **Current state** | BLOCKED — not selected (see D07) |
| **Current fallback** | Straight-line Haversine distance |
| **Intended owner** | TBD |
| **Setup dependencies** | D07 decision; may be same account as mapping provider |

---

### RevenueCat

| Item | Detail |
|------|--------|
| **Purpose** | In-app purchase management, subscription lifecycle, server-side entitlement verification |
| **Current state** | BLOCKED — no account, no API keys |
| **Intended owner** | Project email |
| **Setup dependencies** | Apple Developer account, Google Play Console (for product configuration) |
| **Docs** | `https://www.revenuecat.com/docs/` |

**Variables:**
| Variable | Classification | Notes |
|----------|---------------|-------|
| `EXPO_PUBLIC_REVENUECAT_API_KEY_IOS` | Public (client bundle) | RevenueCat iOS API key |
| `EXPO_PUBLIC_REVENUECAT_API_KEY_ANDROID` | Public (client bundle) | RevenueCat Android API key |
| RevenueCat webhook shared secret | **Server-only secret** | NEVER in client; Edge Function only |

---

### what3words

| Item | Detail |
|------|--------|
| **Purpose** | Coordinate-to-3-word-address conversion |
| **Current state** | BLOCKED — no API key; simulated fallback returns fake words (see D08) |
| **Recommendation** | Consider removing until API key available; rely on Plus Codes instead |
| **Intended owner** | TBD |
| **Setup dependencies** | D08 decision |

**Variables:**
| Variable | Classification | Notes |
|----------|---------------|-------|
| `EXPO_PUBLIC_W3W_API_KEY` | Public (client bundle) | what3words API key; currently optional with unsafe simulation fallback |

---

### Push Notifications

| Item | Detail |
|------|--------|
| **Purpose** | Background alert delivery for favourited facility changes |
| **Current state** | PLANNED — expo-notifications configured; no push server |
| **Intended owner** | TBD |
| **Setup dependencies** | Supabase project (for Edge Function push sender); FCM/APNs credentials |

---

### Apple Developer

| Item | Detail |
|------|--------|
| **Purpose** | iOS app signing, App Store submission, OAuth (Sign in with Apple) |
| **Current state** | BLOCKED — no account |
| **Intended owner** | Project email |
| **Setup dependencies** | Apple Developer Program enrolment (£79/year) |

---

### Google Play Console

| Item | Detail |
|------|--------|
| **Purpose** | Android app signing, Play Store submission, OAuth (Google sign-in), Google Maps API key |
| **Current state** | BLOCKED — no account |
| **Intended owner** | Project email |
| **Setup dependencies** | Google Play Developer account ($25 one-time) |

---

### Error Monitoring

| Item | Detail |
|------|--------|
| **Purpose** | Crash reporting, error tracking |
| **Current state** | PLANNED — Sentry referenced in plan |
| **Intended owner** | TBD |
| **Setup dependencies** | Project email; decision on provider |

---

### Analytics

| Item | Detail |
|------|--------|
| **Purpose** | Usage analytics, with user consent |
| **Current state** | PLANNED — PostHog/Mixpanel referenced in plan |
| **Intended owner** | TBD |
| **Setup dependencies** | Privacy policy; consent mechanism |

---

### Support Contact

| Item | Detail |
|------|--------|
| **Purpose** | User support email, GDPR contact, app store contact |
| **Current state** | BLOCKED — no project email |

---

### Privacy Policy Hosting

| Item | Detail |
|------|--------|
| **Purpose** | Publicly accessible privacy policy URL (required by app stores) |
| **Current state** | PLANNED — no policy drafted |
| **Setup dependencies** | Legal document; hosting location |

---

### Domain

| Item | Detail |
|------|--------|
| **Purpose** | Project website, privacy policy hosting, email |
| **Current state** | BLOCKED |
| **Intended owner** | TBD |

---

## Environment Variable Catalogue

Based on variables found in `src/utils/env.ts`, `app.json`, `.env.example`, and service files.

### Present in repository

| Variable | Where Used | Classification | Status |
|----------|-----------|---------------|--------|
| `EXPO_PUBLIC_SUPABASE_URL` | `env.ts`, `app.json` | Public | Placeholder in `.env.example` |
| `EXPO_PUBLIC_SUPABASE_ANON_KEY` | `env.ts`, `app.json` | Public | Placeholder in `.env.example` |
| `EXPO_PUBLIC_MAPBOX_ACCESS_TOKEN` | `env.ts`, `app.json` | Public | Placeholder in `.env.example`; misleading name |
| `EXPO_PUBLIC_REVENUECAT_API_KEY_IOS` | `revenuecat.ts` | Public | Placeholder in `.env.example` |
| `EXPO_PUBLIC_REVENUECAT_API_KEY_ANDROID` | `revenuecat.ts` | Public | Placeholder in `.env.example` |
| `EXPO_PUBLIC_W3W_API_KEY` | `locationSharing.ts` | Public | Not in `.env.example` |

### Suspected missing but not yet referenced

| Variable | Where Needed | Classification |
|----------|-------------|---------------|
| `SUPABASE_SERVICE_ROLE_KEY` | Edge Functions | **Server-only secret** |
| RevenueCat webhook shared secret | `revenuecat-webhook` Edge Function | **Server-only secret** |
| Google Maps API key (if provider confirmed) | `app.json` | Public (rename from current MAPBOX variable) |
| Push notification credentials (FCM/APNs) | Push server / Edge Function | **Server-only secret** |
| Sentry DSN | Error monitoring | Public (client bundle) |

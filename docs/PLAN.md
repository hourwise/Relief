# Project "Relief" — Agent Plan & Progress
# Tagline: Find Comfort, Find Relief

## App Overview
React Native + Expo mobile app for finding safe, clean, and suitable toilet facilities. Backend powered by Supabase. Formerly "Placename".

### Mission
Help people confidently find safe, clean and suitable facilities wherever they are. Accessibility first. Dignity first. Community powered.

### Brand Direction
- Calm and reassuring
- Accessibility first
- Dignity and privacy focused
- Clean modern UI

### Tech Stack
| Layer | Technology |
|-------|-----------|
| Mobile | React Native + Expo |
| Backend | Supabase (Postgres, Auth, Storage, Edge Functions) |
| Maps | Mapbox + OpenStreetMap data |
| Storage | Supabase Storage |
| Images | Photo uploads with moderation |
| Notifications | Expo Notifications |
| Payments | RevenueCat (server-side entitlement verification) |

---

## Phase 0: Project Scaffolding & Base Setup

- [x] **0.1** Initialize Expo project with TypeScript
- [x] **0.2** Configure ESLint, Prettier, and project structure
- [x] **0.3** Install core dependencies (React Navigation, Supabase client, Mapbox, etc.)
- [x] **0.4** Set up Supabase project and initial schema (migrations)
- [x] **0.5** Create theme system (colors, fonts, typography) from roadmap design language
- [x] **0.6** Set up environment variables (.env, .env.example)
- [x] **0.7** Create reusable UI component library (Button, Card, Input, Badge)
- [x] **0.8** Set up navigation structure (AuthStack, MainTab)
- [x] **0.9** Create base screen templates (Login, Map, List, FacilityDetail, Profile)
- [x] **0.10** Configure Expo Notifications

---

## Phase 1: MVP — UK Launch

### Authentication
- [x] **1.1** Email login screen and logic
- [x] **1.2** Google OAuth login
- [x] **1.3** Apple OAuth login
- [x] **1.4** Session management and auth state persistence

### Map & List Screens
- [x] **1.5** Current location permission and detection
- [x] **1.6** Mapbox map integration with clustering
- [x] **1.7** Nearby facility pins on map (data layer)
- [x] **1.8** List view with distance sorting
- [x] **1.9** Search by town/postcode
- [x] **1.10** Facility detail screen (name, address, photos, hours, free/paid, access notes, last verified)

### Directions
- [x] **1.11** Google Maps deep link launch
- [x] **1.12** Apple Maps deep link launch
- [x] **1.13** Waze deep link launch

### Ratings
- [x] **1.14** Overall score display
- [x] **1.15** Separate ratings: Cleanliness, Privacy, Accessibility, Safety, Noise, Environment

### Filters
- [x] **1.16** Open now filter (data layer)
- [x] **1.17** Free/Paid filter (data layer)
- [x] **1.18** Accessible filter (data layer)
- [x] **1.19** Disabled access filter (data layer)
- [x] **1.20** Baby changing filter (data layer)
- [x] **1.21** Family room filter (data layer)
- [x] **1.22** Gender neutral filter (data layer)
- [x] **1.23** Single occupancy filter (data layer)
- [x] **1.24** 24 hour filter (data layer)
- [x] **1.25** Highly rated filter (data layer)

### Need One Now — Emergency Mode
- [x] **1.26** Large emergency button on home screen
- [x] **1.27** Shows closest option, walking time, open status, overall score

---

## Phase 2: Community Features

### User Contributions
- [x] **2.1** User facility submission form (→ moderation queue, not live)
- [x] **2.2** Photo uploads with moderation pipeline
- [x] **2.3** Report closure / out of order / no water / cleaning / busy (temporary reports with expiry)
- [x] **2.4** Correct information submission (permanent edits → moderation queue)
- [x] **2.5** Add access codes and notes
- [x] **2.6** Gamification badges: Explorer, Community Hero, Accessibility Champion, Family Helper
- [x] **2.7** Report expiry automation (cron/edge function)
- [x] **2.8** Duplicate report checks and rate limiting

---

## Phase 3: Advanced Filters

- [x] **3.1** Privacy filters: single room, floor-to-ceiling cubicles, quiet, gender neutral
- [x] **3.2** Accessibility filters: wheelchair access, RADAR key, adult changing place, lift, grab rails
- [x] **3.3** Baby facilities: changing inside room, separate changing room, family toilet, pram access
- [x] **3.4** Equipment: soap, paper towels, hand dryer, mirror, shelf, hooks, sanitary bins, free period products, drinking water
- [x] **3.5** Environment: noise level, temperature, lighting, smell
- [x] **3.6** Safety: staff nearby, CCTV, women friendly, family friendly
- [x] **3.7** Facility Types: water refill stations, shower facilities, breastfeeding rooms, rest areas, Changing Places, EV charging locations, picnic areas

---

## Phase 4: Premium Features

### Saved Profiles
- [x] **4.1** Saved profiles: IBS Mode, Family Mode, Accessibility Mode, Pregnancy Mode, Neurodivergent Mode, Elderly Mode
  - Store preferences as optional filters, not health declarations ✓
  - Use preference modes (Accessibility, Family, IBS-friendly, Quiet) — never ask for medical conditions directly ✓
  - SavedProfilesScreen with create/list/delete UI
  - profiles service with CRUD + default preference presets
  - saved_profiles table with RLS policy
  - Mode-specific icons, display names, and descriptions
  - 10 profile limit per user

### Route Planning
- [x] **4.2** Route planning with comfort stops every 60–90 mins (e.g. Liverpool → London)
  - RoutePlanningScreen with from/to inputs + popular routes
  - routePlanning service with Haversine distance, geocoding, interpolated stops
  - Suggests highest-rated facilities near route path
  - "Get Directions" deep link to Google Maps per stop
  - Text summary with formatRouteSummary()

### Favourites
- [x] **4.3** Favourite locations, favourite chains, favourite routes
  - FavouritesScreen with list of saved facilities
  - favourites service (add, remove, check, count)
  - favourites table with UNIQUE(user_id, facility_id) + RLS
  - Empty state with guidance

### Offline Maps
- [x] **4.4** Offline map region downloads
  - OfflineMapsScreen with popular towns grid + custom town download
  - offlineMaps service using expo-sqlite for local storage
  - Download/delete regions, progress tracking, storage size display
  - Search offline facilities by town/postcode/name
  - 12 popular UK towns pre-listed, custom input for any town

### Notifications
- [x] **4.5** Closure alerts, favourite facility updates
  - NotificationAlertsScreen with per-facility toggle for closure/update alerts
  - notificationAlerts service with periodic checking (30 min intervals)
  - Checks active reports on favourited facilities and sends local notifications
  - 1-hour cooldown to prevent duplicate alerts
  - "Check Now" button for manual refresh

### Enhanced Location Sharing
- [x] **4.6** What3Words lookup integration
  - coordsToWhat3Words service with simulated fallback for development
  - Open W3W website via deep link
- [x] **4.7** Plus Codes (Google Open Location) support
  - Client-side Plus Code generation algorithm
  - Open Google Maps with Plus Code
- [x] **4.8** Share precise location to contact
  - System share sheet with maps URL
- [x] **4.9** Copy W3W address to clipboard
  - expo-clipboard integration
- [x] **4.10** Copy coordinates to clipboard
  - Formatted coordinate string copy
- [x] **4.11** Send location to contact (SMS / messaging)
  - Platform-specific maps URLs shared via Share API
- [x] **4.12** Emergency location card (shareable)
  - Formatted emergency card with all location details
  - Share via system share sheet
  - LocationSharingScreen with all sharing options

### Monetisation
- [x] **4.13** **Basic Access** (£1.99 lifetime): Maps, Search, Ratings, Directions, Community updates, Favourites
- [x] **4.14** **Plus Subscription** (£1.99/mo or £14.99/yr): Route planner, Offline maps, AI recommendations, Saved profiles, Travel support, Europe expansion, Smart alerts
- [x] **4.15** Entitlements checked server-side via RevenueCat (not client-side only)
- [x] **4.16** Restore purchases flow
- [x] **4.17** Handle refunds, cancellations, expired subscriptions
- [x] **4.18** Paywall gating for premium features
- [x] **4.19** Cache entitlement locally for graceful offline use

---

## Phase 5: AI Features

- [x] **5.1** Smart recommendations matching facilities to user needs (quiet, single occupancy, baby changing, wheelchair access)
- [x] **5.2** Predictive suggestions ("Next suitable facility in 12 miles")
- [x] **5.3** AI ranking by user preferences

---

## Phase 6: Europe Expansion

- [ ] **6.1** Ireland
- [ ] **6.2** France
- [ ] **6.3** Germany
- [ ] **6.4** Spain
- [ ] **6.5** Italy
- [ ] **6.6** Netherlands
- [ ] **6.7** Belgium
- [x] **6.8** i18n / localization infrastructure (i18next + react-i18next installed, en.json with all nested keys created)
- [ ] **6.9** Multi-region data sourcing

---

## Infrastructure & DevOps

### Database & Backend
- [ ] Supabase migrations and seed data
- [ ] Supabase Edge Functions for server-side logic
- [ ] Supabase Storage rules for photo uploads
- [ ] Image moderation integration

### Security, Privacy & Trust (Non-Negotiables)
- [ ] **AUTH:** Do not require login for basic "Need One Now" search. Login only for reviews, photos, saved profiles, reports, premium.
- [ ] **AUTH:** Enable email verification. Never store passwords directly.
- [ ] **AUTH:** No service role key in client code.
- [ ] **SUPABASE RLS:** Row Level Security on every table. Default deny-all. Explicit policies per action.
- [ ] **SUPABASE RLS:** Users may only edit their own profile, reviews, reports and saved places.
- [ ] **SUPABASE RLS:** Public facility data = read-only from client.
- [ ] **SUPABASE RLS:** Facility creation/editing → moderation queue, not live.
- [ ] **SUPABASE RLS:** Admin actions via server-side functions only.
- [ ] **API KEYS:** No secret keys in Expo public config. No Supabase service_role key in app. No map provider secret keys in client. Separate dev/staging/prod keys. Rotate if exposed.
- [ ] **LOCATION:** Explain why location is needed in plain language.
- [ ] **LOCATION:** Do not continuously track users.
- [ ] **LOCATION:** Do not store precise user location history by default (approximate analytics only).
- [ ] **LOCATION:** Clear location from memory when no longer needed.
- [ ] **LOCATION:** Allow manual postcode/town search for users who deny location.
- [ ] **REVIEWS:** Prevent anonymous abuse — rate limits, duplicate checks, moderation queue.
- [ ] **REVIEWS:** Do not allow posting of private personal details.
- [ ] **IMAGES:** Strip EXIF/location metadata from uploaded photos.
- [ ] **IMAGES:** Blur faces before public display where possible.
- [ ] **CONTACT:** Use spam protection. Validate all inputs. Sanitize text. Server-side storage. Consent checkbox.
- [ ] **GDPR:** Publish Privacy Policy before beta. Publish Terms before payments.
- [ ] **GDPR:** Provide account deletion, data export, delete review/photo, privacy contact email.
- [ ] **GDPR:** Track consent for marketing emails separately. No auto-opt-in.
- [ ] **WEB:** Use HTTPS only. Secure headers. Environment variables. Validate API routes. Rate-limit forms. No PII in logs.
- [ ] **ADMIN PANEL:** Role-based admin access (not user-editable). All actions logged.
- [ ] **ADMIN MODERATION:** Approve facility, reject facility, edit facility, remove photo, remove review, mark report resolved.

### Admin Panel
- [ ] Role-based admin access (admin role not editable by user)
- [ ] All admin actions logged
- [ ] Moderation tools: approve/reject facility, edit facility, remove photo, remove review, mark report resolved

### CI/CD & Publishing
- [ ] CI/CD pipeline (EAS Build + Submit)
- [ ] App Store / Google Play listing assets
- [ ] Analytics (PostHog / Mixpanel)
- [ ] Crash reporting (Sentry)
- [ ] Privacy policy and terms of service

### Project Rename
- [x] **INFRA-1** Rename project from "Placename" to "Relief"
- [x] **INFRA-5** Harden `.gitignore` to prevent secret leakage
- [x] **INFRA-6** Create `.easignore` for EAS Build security
- [x] **INFRA-7** Verify no hardcoded secrets in source code

### i18n / Localization
- [x] **INFRA-2** Install i18next + react-i18next
- [x] **INFRA-3** Create i18n config (src/i18n/index.ts) with English defaults
- [x] **INFRA-4** Create en.json with all app translation keys in nested format

---

## Pre-Release Testing Checklist

Before any release, verify:

- [ ] RLS policies — unauthenticated access denied
- [ ] RLS policies — authenticated user can only access own data
- [ ] RLS policies — admin-only routes protected
- [ ] Payment unlock / restore / cancel flows end-to-end
- [ ] Form spam protection working
- [ ] Location denied flow (manual search works)
- [ ] Account deletion flow
- [ ] Photo metadata stripping
- [ ] Face blurring on uploaded images
- [ ] i18n translation strings match all UI elements
- [ ] Fallback language works when translation key is missing

---

## Legend
- `[ ]` — Not started
- `[x]` — Completed
- `[~]` — In progress
- `[!]` — Blocked
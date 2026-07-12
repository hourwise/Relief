# Relief — Backend Integration Plan

**Last updated:** 2026-07-12  
**Status:** Planning document — no implementation performed.

This plan defines a safe, staged route from the current frontend-only prototype to a functioning application with connected backend services. Each phase lists prerequisites, deliverables, security requirements, and acceptance criteria.

---

## Phase 0 — Ownership and Provider Decisions

**Prerequisites:** None.

**Deliverables:**
- Project email identity established
- All service accounts created under project email
- Mapping provider selected (see D01)
- Pricing model confirmed (see D09)
- Initial launch geography chosen (see D03)
- Seed data source identified (see D04)
- Moderation approach decided (see D10)

**Acceptance criteria:** All BLOCKER and HIGH decisions in `DECISIONS_NEEDED.md` resolved.

---

## Phase 1 — Backend Foundation (Supabase)

**Prerequisites:** Phase 0 complete.

**Deliverables:**
- Supabase organisation and development project created
- Development, staging, and production project separation planned
- All 4 migration files applied to development database in order:
  1. `001_initial_schema.sql` — facilities, reviews, ratings
  2. `20260624_community_features.sql` — submissions, reports, photos, badges, rate limits, corrections
  3. `20260625_premium_features.sql` — saved_profiles, favourites
  4. `20260701_monetisation.sql` — user_entitlements, subscription tracking
- RLS policies enabled on every table per migration definitions
- `facility-photos` storage bucket created with access policies
- Edge Functions deployed:
  - `expire-reports` — with cron schedule (every 15 minutes)
  - `revenuecat-webhook` — with HTTP endpoint
- Seed data loaded for launch city
- Backup and recovery configured (Supabase automated backups enabled)
- `EXPO_PUBLIC_SUPABASE_URL` and `EXPO_PUBLIC_SUPABASE_ANON_KEY` configured in `.env`

**Security requirements:**
- Default-deny RLS on every table
- Service role key NEVER in client code or `.env`
- Anon key restricted to public-read operations only
- Storage bucket: authenticated upload, public read (approved only)

**Acceptance criteria:**
- Client can query `facilities` table and receive seed data
- `is_verified = true` facilities are readable by anon and authenticated users
- Auth sign-up, sign-in, session refresh work end-to-end
- Edge Functions execute successfully when triggered

**Rollback:** Drop and recreate development project. Migrations are versioned and repeatable.

---

## Phase 2 — Identity and Privacy

**Prerequisites:** Phase 1 complete.

**Deliverables:**
- Email authentication enabled in Supabase
- Google OAuth configured (Google Cloud project + Supabase provider)
- Apple OAuth configured (Apple Developer account + Supabase provider)
- Deep linking configured (`relief://` scheme verified)
- OAuth callback URLs registered in Supabase dashboard
- User profile creation on first sign-in
- Privacy controls: account deletion flow (UI + server-side handler)
- Data export flow (UI + server-side handler)
- Consent tracking for any marketing communications

**Security requirements:**
- Email verification enabled before full access
- Passwords never stored — handled entirely by Supabase Auth
- Account deletion: hard-delete user data; retain anonymised facility contributions
- Data export: provide machine-readable format (JSON)

**Acceptance criteria:**
- User can register with email, verify, and sign in
- User can sign in with Google and Apple
- User can delete their account and all associated data
- User can request and receive their data

---

## Phase 3 — Trustworthy Facility Discovery

**Prerequisites:** Phase 2 complete.

**Deliverables:**
- Public facility reads: `facilities` table accessible to anon users (RLS: `is_verified = true`)
- Search by town, postcode, name working
- Geospatial queries optimised (consider PostGIS or GiST indexes)
- Geographic seed data loaded and verified
- Data freshness: `last_verified_at` updated on verification
- Directions provider integrated (deep links to platform maps)
- Degraded-network handling: graceful error states; cached last-known data
- Unauthenticated "Need One Now" path working (D02)

**Security requirements:**
- Public facility data = read-only from client (RLS enforced)
- No user location data stored server-side from anonymous queries
- Rate limiting on anonymous search endpoints to prevent scraping

**Acceptance criteria:**
- Unauthenticated user can open app, see nearby facilities, and use Need One Now
- Search returns relevant results within 2 seconds
- Directions open in platform maps app
- App shows clear error state when offline, not a crash

---

## Phase 4 — Community and Moderation

**Prerequisites:** Phase 3 complete.

**Deliverables:**
- Facility submission form → moderation queue (RLS: user sees own)
- Photo upload → Storage → moderation queue (RLS: user uploads; admin approves)
- Media processing pipeline:
  - EXIF metadata stripping on upload (Edge Function trigger)
  - Face detection and blurring (Edge Function + external API)
  - Content moderation filter (automated inappropriate-content detection)
- Temporary reports with expiry (Edge Function cron)
- Correction requests → moderation queue
- Review submission with six-dimension ratings
- Badge awards on contribution milestones
- Moderation admin dashboard:
  - Approve/reject facility submissions
  - Approve/reject photos
  - Resolve temporary reports
  - Review and apply corrections
  - Remove inappropriate reviews
  - Audit log of all admin actions
- Spam prevention:
  - Server-side rate limiting (Edge Function middleware)
  - Duplicate submission detection
  - Abuse reporting flow for users
- Moderation response targets defined (e.g., photo review within 24 hours)

**Security requirements:**
- All community writes authenticated only
- Rate limits enforced server-side, not client-side
- Photo EXIF stripped before storage; faces blurred before public display
- Review text sanitised to prevent injection
- No PII in review or report content
- Admin actions logged immutably

**Acceptance criteria:**
- User can submit facility, upload photo, write review, file report
- All submissions enter moderation queue (not immediately live)
- Photos have EXIF stripped and faces blurred when approved
- Reports auto-expire at their defined expiry time
- Admin can process all moderation actions
- Rate limits prevent abuse

**Rollback:** Community features can be disabled via feature flag `COMMUNITY: false` if abuse is detected.

---

## Phase 5 — Enhanced User Features

**Prerequisites:** Phase 4 complete.

**Deliverables:**
- Favourites: add, remove, list, count (RLS: user owns own)
- Saved filter profiles: create, read, update, delete (RLS: user owns own; max 10)
- Route planning with real road-routing API integration
- Offline facility data download and local search
- Push notification infrastructure:
  - Expo push token registration
  - Server-side push notification service
  - Favourited facility alerts (closure, update)
  - Background notification handling
- Location sharing:
  - Plus Codes (keep; free and open)
  - what3words (only if API key configured; remove simulation)
  - System share sheet integration
  - Emergency location card

**Acceptance criteria:**
- Favourites persist across sessions
- Saved profiles apply correct filters
- Route planning shows road-aware stops with real facilities
- Offline data available when device has no connectivity
- Push notifications delivered for favourited facility changes
- Location sharing produces real, usable location codes

---

## Phase 6 — Monetisation

**Prerequisites:** Phase 5 complete.

**Deliverables:**
- RevenueCat products configured (Basic Access lifetime, Plus monthly, Plus annual)
- RevenueCat SDK initialised with valid API keys
- RevenueCat webhook deployed and receiving events
- `user_entitlements` table synced from webhook events
- Paywall gating premium features per pricing model
- Restore purchases flow tested
- Refund/cancellation handling:
  - Webhook receives cancellation event
  - Entitlement marked inactive
  - Premium features disabled on next app launch
- Store listing compliance:
  - Apple App Store: in-app purchase configured
  - Google Play: products configured in Play Console
- Grace period handling for subscription lapses

**Security requirements:**
- Entitlements verified server-side (not trusted from client alone)
- Webhook signature verification (RevenueCat provides shared secret)
- No entitlement bypass via client-side manipulation

**Acceptance criteria:**
- User can purchase Basic Access (lifetime) and Plus (subscription)
- Entitlement is reflected in app immediately after purchase
- Restore purchases recovers previous purchases
- Cancelled subscription disables premium features
- Refund disables premium features
- Purchase flow works on both iOS and Android

---

## Phase 7 — Later Capabilities

**Prerequisites:** Phase 6 complete; product stable in UK market.

**Deliverables:**
- Smart recommendations enhancement (model-backed if justified)
- Europe expansion: per-country data, translations, compliance
- Operations dashboard: facility data quality metrics, moderation throughput, user growth
- Monitoring: Sentry for errors, PostHog/Mixpanel for analytics (with consent)
- Incident response plan
- Data quality operations: stale facility detection, verification reminders
- Scaling: query performance, geographic index tuning, CDN for photos

**Acceptance criteria:** Per-country launch criteria met; monitoring dashboards operational.

---

## Features That Must Remain Disabled Until Acceptance Gates Met

| Feature | Gate |
|---------|------|
| what3words (non-simulated) | Valid W3W API key configured |
| Photo uploads (public display) | EXIF stripping + face blurring operational |
| Community submissions (live) | Moderation dashboard + team in place |
| Premium features | RevenueCat configured + webhook deployed |
| Push notifications | Push server + background handler implemented |
| Europe expansion | UK product metrics positive; per-country data sourced |
| "AI" branding | Model-backed recommendation service implemented (or rename feature) |

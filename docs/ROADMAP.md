# Relief — Roadmap

**Last updated:** 2026-07-12  
**Status:** Evidence-based — replaces all previous phase-completion claims.

This roadmap uses outcome gates, not arbitrary percentages. Each phase has entry criteria, deliverables, exit criteria, and explicit blockers.

---

## Phase 1: Documentation and Truth Baseline ✅ (This Pass)

**Entry criteria:** Codebase exists; inconsistent documentation.  
**Deliverables:** Complete documentation set with honest status assessment.  
**Exit criteria:** New reader understands Relief's actual state within 5 minutes.  
**Status:** In progress (this pass).

---

## Phase 2: Frontend Stabilisation and Clear Demo Boundaries

**Entry criteria:** Documentation baseline complete.  
**Deliverables:**
- Resolve navigation: add unauthenticated browse path for urgent discovery (D02)
- Replace ListScreen hardcoded data with Supabase query (or clear mock boundary)
- Add `.env` file validation at startup
- Add ESLint + Prettier configuration
- Add TypeScript type-check script to package.json
- Rename "AI Recommendations" → "Smart Recommendations" (D05)
- Rename "Offline Maps" → "Save for Offline" / "Offline Facility Data" (D06)
- Align map provider naming in config (D01)
- Remove or gate what3words simulation with clear warning (D08)
- Add clear mock/prototype labels in UI for features without backends
**Exit criteria:** App runs locally with clear distinction between working features and prototypes.  
**Blockers:** D01, D02, D05, D06, D08.

---

## Phase 3: Provider and Product Decisions

**Entry criteria:** Frontend stabilisation complete.  
**Deliverables:**
- Select mapping provider; create account; obtain API key (D01)
- Select routing provider (D07)
- Confirm pricing model (D09)
- Select initial launch city (D03)
- Identify seed data source (D04)
- Establish project email and support identity (D11)
- Decide moderation approach (D10)
**Exit criteria:** All BLOCKER and HIGH decisions resolved. Accounts created for required services.  
**Blockers:** All open decisions in `DECISIONS_NEEDED.md`.

---

## Phase 4: Backend Foundation

**Entry criteria:** Decisions resolved; service accounts created.  
**Deliverables:**
- Create Supabase organisation and development project
- Apply all 4 migration files to development database
- Configure RLS policies as defined in migrations
- Create `facility-photos` storage bucket with access policies
- Deploy `expire-reports` and `revenuecat-webhook` Edge Functions
- Create development seed data for launch city
- Configure environment variables in `.env`
- Verify client can query facilities, authenticate, and read data
**Exit criteria:** App renders real facility data on map from Supabase. Auth flow works end-to-end.  
**Blockers:** Supabase account, D03, D04.

---

## Phase 5: Trustworthy Public-Facility MVP

**Entry criteria:** Backend foundation complete; seed data loaded.  
**Deliverables:**
- Map displays real facilities with correct locations
- List shows real facilities sorted by distance
- "Need One Now" works without authentication
- Search by town/postcode returns real results
- Filters apply correctly to database queries
- Facility detail shows all available data
- Directions deep links work on device
- Open-now logic functions with real open_hours data
- Degraded-network handling: graceful error states when offline
**Exit criteria:** Core discovery journey works end-to-end with real data. Usable as a read-only directory.  
**Blockers:** D02 (unauthenticated access must be resolved before this phase).

---

## Phase 6: Authenticated Community Contribution

**Entry criteria:** Public-facility MVP stable.  
**Deliverables:**
- User registration and login (email, Google, Apple)
- Facility submission → moderation queue
- Photo upload with EXIF stripping (server-side)
- Photo upload with face blurring (server-side)
- Temporary reports with auto-expiry
- Corrections submission
- Six-dimension ratings and reviews
- Badges awarded on contribution milestones
- Rate limiting enforced server-side
- Spam prevention measures
**Exit criteria:** Users can contribute; all contributions enter moderation queue; media is safely processed.  
**Blockers:** Media processing pipeline design, D10 (moderation ownership).

---

## Phase 7: Moderation and Operations

**Entry criteria:** Community contribution flow working.  
**Deliverables:**
- Admin dashboard for moderation
- Approve/reject facilities, photos, corrections
- Review and resolve temporary reports
- Remove inappropriate content
- Admin action audit logging
- Role-based admin access (not user-editable)
**Exit criteria:** Moderation team can process all contribution types efficiently.  
**Blockers:** Admin panel technology selection, D10.

---

## Phase 8: Monetisation

**Entry criteria:** Core product usable; community features gated behind moderation.  
**Deliverables:**
- Configure RevenueCat products and entitlements
- Deploy and test RevenueCat webhook
- Server-side entitlement verification
- Paywall gating for premium features
- Restore purchases flow
- Refund and cancellation handling
- Store listing compliance (Apple/Google)
**Exit criteria:** Purchase, restore, and cancellation flows work end-to-end. Entitlements verified server-side.  
**Blockers:** RevenueCat account, Apple Developer account, Google Play Console.

---

## Phase 9: Enhanced Features (Route, Offline, Alerts)

**Entry criteria:** Monetisation working.  
**Deliverables:**
- Road-aware route planning with real routing API
- Offline facility data download and search
- Server-triggered push notifications for favourited facility alerts
- Saved filter profiles (Accessibility, Family, etc.)
- Favourites sync across devices
**Exit criteria:** Premium features work with real backend data.  
**Blockers:** D07 (routing provider), push notification infrastructure.

---

## Phase 10: Smart Recommendations (Optional)

**Entry criteria:** Enhanced features stable.  
**Deliverables:**
- Evaluate whether model-backed recommendations add value beyond deterministic scoring
- If yes: select approach, implement, A/B test against deterministic baseline
- If no: keep deterministic scoring and document it clearly
**Exit criteria:** Decision documented and implemented.  
**Blockers:** None (this phase is decision-gated, not dependency-gated).

---

## Phase 11: Geographic Expansion

**Entry criteria:** UK product stable with positive user metrics.  
**Deliverables:**
- Ireland facility data
- France, Germany, Spain, Italy, Netherlands, Belgium (per original plan)
- Per-country data sourcing strategy
- Locale-specific translations (i18n keys exist, need translations)
- Country-specific accessibility attribute mapping
**Exit criteria:** First expansion country live with quality data.  
**Blockers:** D13, D14, per-country data sources.

---

## Deferred Work (Intentionally Outside Current Scope)

- Native mobile app rebuild (currently Expo managed workflow)
- Custom map rendering engine
- Real-time facility occupancy
- Social features beyond contributions
- Facility booking/reservation
- Integration with transport apps
- Voice-guided facility finding
- AR facility location

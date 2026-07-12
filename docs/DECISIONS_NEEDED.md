# Relief — Decisions Needed

**Last updated:** 2026-07-12  
**Status:** All decisions are open unless marked resolved.

Decisions are ordered by blocker level. A decision at BLOCKER level must be resolved before the next implementation phase can proceed.

---

## BLOCKER — Cannot proceed without resolution

### D01: Mapping Provider

**Context:** The codebase uses `react-native-maps` with `PROVIDER_GOOGLE` (Google Maps). The environment variable is named `EXPO_PUBLIC_MAPBOX_ACCESS_TOKEN`. The `app.json` maps this token into the `googleMapsApiKey` field. The README and design docs reference Mapbox.

**Options:**
- **A) Google Maps** — Already the code default. Requires Google Cloud billing account. Different pricing model. `react-native-maps` supports it natively.
- **B) Mapbox** — Would require switching to `@rnmapbox/maps` or Mapbox GL. Different pricing/packaging. Stronger privacy reputation.
- **C) Apple Maps (iOS) + Google Maps (Android)** — Platform-native approach using `react-native-maps` default providers.

**Recommendation:** Option A (Google Maps) — least code change. Rename env variable to `EXPO_PUBLIC_GOOGLE_MAPS_API_KEY`. Update all references.

**Consequences:** Google Cloud account required. Pricing based on Maps API usage. Privacy considerations for location data sent to Google.

**Blocker level:** BLOCKER  
**Owner:** TBD

---

### D02: Unauthenticated Access to Urgent Discovery

**Context:** The "Need One Now" emergency feature is a core product promise. Currently, the app requires authentication before any facility discovery. This contradicts the security addendum's statement: "Do not require login for basic Need One Now search."

**Options:**
- **A) Allow unauthenticated browse** — Add unauthenticated path to Map/List. Only require login for contributions, reviews, saved data, premium.
- **B) Require account for everything** — Keep current auth gate. Update security addendum to match.
- **C) Hybrid** — Allow 3 emergency uses without account, then prompt sign-up.

**Recommendation:** Option A — aligns with mission and accessibility policy. Low technical risk (Supabase permits anon reads).

**Consequences:** RLS policies must allow anon read on verified facilities. Rate limiting needed to prevent anonymous abuse of community features.

**Blocker level:** BLOCKER  
**Owner:** TBD

---

### D03: Initial Geographic Launch Area

**Context:** Seed data is needed for the MVP. The plan mentions UK launch but does not specify initial town, city, or region.

**Options:**
- **A) Single city (e.g., Liverpool)** — Manageable seed data scope; validate product-market fit before expanding.
- **B) Major UK cities** — Broader coverage; more complex seed data sourcing.
- **C) Full UK** — Requires comprehensive data sourcing; highest complexity.

**Recommendation:** Option A — start with one city, validate, then expand.

**Consequences:** Determines seed data scope, geographic indexing strategy, and launch marketing.

**Blocker level:** BLOCKER  
**Owner:** TBD

---

### D04: Trusted Seed Data Source

**Context:** Facilities need initial data. The app cannot launch with an empty database.

**Options:**
- **A) Council open data** — UK councils publish public toilet datasets. Varying quality and coverage.
- **B) OpenStreetMap** — Community-maintained; toilet data exists but may be incomplete.
- **C) Manual curation** — Team-verified initial dataset. High quality, slow to build.
- **D) Combination** — Import from open sources; verify top facilities manually.

**Recommendation:** Option D — import OSM + council data; manually verify top 50 facilities in launch city.

**Consequences:** Data quality directly impacts user trust. Inaccurate data in a toilet-finding app has immediate real-world consequences.

**Blocker level:** BLOCKER  
**Owner:** TBD

---

## HIGH — Resolution needed before backend integration

### D05: "AI Recommendations" Renaming

**Context:** The "AI" features are deterministic weighted scoring algorithms, not model-backed AI. The feature flag `AI: false` confirms the intent to separate this.

**Options:**
- **A) Rename to "Smart Recommendations"** — Honest about current capability.
- **B) Keep "AI" name** — Misleading until model-backed.
- **C) Implement model-backed recommendations** — Requires ML infrastructure.

**Recommendation:** Option A for now; evaluate Option C as a later phase.

**Consequences:** User trust; marketing claims.

**Blocker level:** HIGH  
**Owner:** TBD

---

### D06: "Offline Maps" Renaming

**Context:** The feature downloads facility JSON data to SQLite. It does not download map tiles or enable offline map rendering. The name "Offline Maps" is misleading.

**Options:**
- **A) Rename to "Offline Facility Data"** — Accurate.
- **B) Implement offline map tile download** — Complex; significant storage requirements.
- **C) Rename to "Save for Offline"** — User-friendly, less technical.

**Recommendation:** Option C for user-facing; Option A for technical documentation.

**Blocker level:** HIGH  
**Owner:** TBD

---

### D07: Routing Provider

**Context:** Route planning uses straight-line Haversine distance. No road network routing exists. A routing provider is needed for production.

**Options:**
- **A) Google Directions API** — If Google Maps is the mapping provider.
- **B) Mapbox Directions API** — If Mapbox.
- **C) OSRM (Open Source Routing Machine)** — Self-hosted or free tier.
- **D) Keep straight-line for MVP with clear disclaimer** — Fastest to launch.

**Recommendation:** Option D for MVP (clearly labelled as "estimate"); Option A or B for production, aligned with mapping provider decision.

**Blocker level:** HIGH  
**Owner:** TBD

---

### D08: what3words Retention

**Context:** Without a W3W API key, the service returns simulated (fake) location words. This is a safety risk for users relying on location codes.

**Options:**
- **A) Remove what3words until API key available** — Safest.
- **B) Keep with API key** — Requires W3W account and billing.
- **C) Replace with Plus Codes only** — Google Open Location Codes are free and open.

**Recommendation:** Option C — Plus Codes are free, open, and the client algorithm already exists. Consider W3W as a later enhancement.

**Blocker level:** HIGH  
**Owner:** TBD

---

## MEDIUM — Resolution needed before premium features launch

### D09: Pricing Model Confirmation

**Context:** The code supports 'free', 'basic' (lifetime £1.99), and 'plus' (£1.99/mo or £14.99/yr) tiers. The README previously described core features as both free and part of Basic Access.

**Recommendation:** Confirm: Free tier = map, search, "Need One Now," basic filters. Basic Access (£1.99 lifetime) = favourites, community contributions. Plus (£1.99/mo) = route planning, offline data, saved profiles, smart recommendations.

**Blocker level:** MEDIUM  
**Owner:** TBD

---

### D10: Moderation Ownership

**Context:** Community submissions, photos, reviews, and corrections require moderation. No admin panel or moderation workflow exists.

**Options:**
- **A) In-house moderation** — Team reviews submissions via admin dashboard.
- **B) Community moderation** — Flag-based; trusted users have moderation privileges.
- **C) Automated + human review** — Automated filters for spam/abuse; human review for edge cases.
- **D) Defer to pre-launch** — Launch without community features; add with moderation later.

**Recommendation:** Option D — launch as read-only directory; add community contributions post-launch with moderation in place.

**Blocker level:** MEDIUM  
**Owner:** TBD

---

### D11: Account Ownership and Support Identity

**Context:** The project needs a contact email for app store listings, privacy policy, GDPR requests, and user support.

**Status:** Not yet established.

**Blocker level:** MEDIUM  
**Owner:** TBD

---

### D12: Legal Document Ownership

**Context:** Privacy Policy and Terms of Service are needed before app store submission and certainly before any user data collection.

**Status:** Not drafted.

**Blocker level:** MEDIUM  
**Owner:** TBD

---

## LOW — Resolution needed before geographic expansion

### D13: Europe Expansion Priority

**Context:** Phase 6 lists 7 countries. i18n infrastructure is ready.

**Recommendation:** Complete UK launch and stabilise before selecting first expansion country.

**Blocker level:** LOW  
**Owner:** TBD

---

### D14: Multi-Region Data Sourcing

**Context:** Each country will require its own facility data sourcing strategy.

**Recommendation:** Defer until UK launch is stable.

**Blocker level:** LOW  
**Owner:** TBD

---

## Decision Summary

| ID | Decision | Blocker Level | Status |
|----|----------|---------------|--------|
| D01 | Mapping provider | BLOCKER | Open |
| D02 | Unauthenticated access | BLOCKER | Open |
| D03 | Launch geography | BLOCKER | Open |
| D04 | Seed data source | BLOCKER | Open |
| D05 | AI renaming | HIGH | Open |
| D06 | Offline renaming | HIGH | Open |
| D07 | Routing provider | HIGH | Open |
| D08 | what3words retention | HIGH | Open |
| D09 | Pricing model | MEDIUM | Open |
| D10 | Moderation ownership | MEDIUM | Open |
| D11 | Account/support identity | MEDIUM | Open |
| D12 | Legal documents | MEDIUM | Open |
| D13 | Europe priority | LOW | Open |
| D14 | Multi-region data | LOW | Open |

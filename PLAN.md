# Plan superseded

This file has been superseded by the documentation in `docs/`.

See:
- **Current state:** `docs/CURRENT_STATE.md`
- **Roadmap:** `docs/ROADMAP.md`
- **Architecture:** `docs/ARCHITECTURE.md`
- **Documentation index:** `docs/README.md`

### Map & List Screens
- [x] **1.5** Current location permission and detection
- [x] **1.6** Mapbox map integration with clustering
- [x] **1.7** Nearby facility pins on map
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
- [x] **1.16** Open now filter
- [x] **1.17** Free/Paid filter
- [x] **1.18** Accessible filter
- [x] **1.19** Disabled access filter
- [x] **1.20** Baby changing filter
- [x] **1.21** Family room filter
- [x] **1.22** Gender neutral filter
- [x] **1.23** Single occupancy filter
- [x] **1.24** 24 hour filter
- [x] **1.25** Highly rated filter

### Need One Now — Emergency Mode
- [x] **1.26** Large emergency button on home screen
- [x] **1.27** Shows closest option, walking time, open status, overall score

---

## Phase 2: Community Features

- [ ] **2.1** User facility submission form
- [ ] **2.2** Photo uploads with moderation pipeline
- [ ] **2.3** Report closure / out of order / no water / cleaning / busy (temporary reports with expiry)
- [ ] **2.4** Correct information submission (permanent edits)
- [ ] **2.5** Add access codes and notes
- [ ] **2.6** Gamification badges: Explorer, Community Hero, Accessibility Champion, Family Helper
- [ ] **2.7** Report expiry automation (cron/edge function)

---

## Phase 3: Advanced Filters

- [ ] **3.1** Privacy filters: single room, floor-to-ceiling cubicles, quiet, gender neutral
- [ ] **3.2** Accessibility filters: wheelchair access, RADAR key, adult changing place, lift, grab rails
- [ ] **3.3** Baby facilities: changing inside room, separate changing room, family toilet, pram access
- [ ] **3.4** Equipment: soap, paper towels, hand dryer, mirror, shelf, hooks, sanitary bins, free period products, drinking water
- [ ] **3.5** Environment: noise level, temperature, lighting, smell
- [ ] **3.6** Safety: staff nearby, CCTV, women friendly, family friendly

---

## Phase 4: Premium Features

- [ ] **4.1** Saved profiles: IBS Mode, Family Mode, Accessibility Mode, Pregnancy Mode, Neurodivergent Mode, Elderly Mode
- [ ] **4.2** Route planning with comfort stops every 60–90 mins (e.g. Liverpool → London)
- [ ] **4.3** Favourite locations, favourite chains, favourite routes
- [ ] **4.4** Offline map region downloads
- [ ] **4.5** Notifications: closure alerts, favourite facility updates
- [ ] **4.6** Monetisation: Basic Access (£1.99 lifetime), Plus Subscription (£1.99/mo or £14.99/yr)
- [ ] **4.7** Paywall gating for premium features

---

## Phase 5: AI Features

- [ ] **5.1** Smart recommendations matching facilities to user needs
- [ ] **5.2** Predictive suggestions ("Next suitable facility in 12 miles")
- [ ] **5.3** AI ranking by user preferences (quiet, single occupancy, baby changing, wheelchair access)

---

## Phase 6: Europe Expansion

- [ ] **6.1** Ireland
- [ ] **6.2** France
- [ ] **6.3** Germany
- [ ] **6.4** Spain
- [ ] **6.5** Italy
- [ ] **6.6** Netherlands
- [ ] **6.7** Belgium
- [ ] **6.8** i18n / localization infrastructure
- [ ] **6.9** Multi-region data sourcing

---

## Future Categories (Post-Europe)

- [ ] Water refill stations
- [ ] Shower facilities
- [ ] Breastfeeding rooms
- [ ] Rest areas
- [ ] Changing Places facilities
- [ ] EV charging locations
- [ ] Picnic areas

---

## Infrastructure & DevOps

- [ ] Supabase migrations and seed data
- [ ] Supabase Edge Functions for server-side logic
- [ ] Supabase Storage rules for photo uploads
- [ ] Image moderation integration
- [ ] CI/CD pipeline (EAS Build + Submit)
- [ ] App Store / Google Play listing assets
- [ ] Analytics (PostHog / Mixpanel)
- [ ] Crash reporting (Sentry)
- [ ] Privacy policy and terms of service

---

## Legend
- `[ ]` — Not started
- `[x]` — Completed
- `[~]` — In progress
- `[!]` — Blocked
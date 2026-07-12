# Relief — Accessibility and User Experience

**Last updated:** 2026-07-12  
**Status:** Policy consolidated from original Accessibility Addendum; implementation gaps identified.

---

## Accessibility Policy (from original addendum)

The app must be usable by an elderly person, a disabled user, or someone in distress within **10 seconds** of opening it.

Design for:
- Low confidence with technology
- Poor eyesight
- Shaky hands
- Cognitive overload
- Anxiety/urgency
- Screen readers
- One-handed use

---

## Navigation Requirements vs Implementation

| Policy Requirement | Implementation | Status |
|-------------------|---------------|--------|
| No more than 3 main tabs | 4 tabs: Map, List, Favourites, Profile | ❌ GAP — see C07 |
| Home screen: one obvious primary action | "Need One Now" button exists in MapScreen | ✅ IMPLEMENTED (UI) |
| No hidden menus | No hamburger menus found | ✅ COMPLIANT |
| No gesture-only controls | Navigation uses tap-based tabs | ✅ COMPLIANT |
| Every icon has text label | Tab icons use emoji + text labels | ⚠️ PARTIAL — emoji not ideal for screen readers |
| Every action reachable by tapping | Verified in navigation structure | ✅ COMPLIANT |

---

## Urgent-Use Journey

**Target:** User opens app → finds nearest facility within 10 seconds.

**Current state:** ❌ BLOCKED by authentication gate.

The "Need One Now" flow as implemented:
1. User taps emergency button
2. `fetchClosestFacility()` queries Supabase
3. Displays facility name, walking time, open status, score

But the user **cannot reach this flow without signing in first**. This is the single most critical accessibility gap.

**Required fix:** Add unauthenticated path to MapScreen with "Need One Now" available immediately.

---

## Navigation Structure Audit

| Tab | Icon | Purpose | Accessibility Notes |
|-----|------|---------|---------------------|
| Map | 🗺️ | Facility map with emergency button | Primary discovery surface |
| List (labelled "Nearby") | 📋 | Distance-sorted list | Currently MOCKED |
| Favourites | ⭐ | Saved facilities | Requires authentication (acceptable) |
| Profile | 👤 | User account, settings, premium | Requires authentication (acceptable) |

**Gap:** 4 tabs exceeds the 3-tab maximum. Recommendation: merge List into Map tab as a toggle (Map/List view switch), reducing to 3 tabs: Find, Favourites, Profile.

---

## Screen Reader Requirements

| Requirement | Current State | Evidence |
|-------------|---------------|----------|
| Accessible labels on all interactive elements | ⚠️ PARTIAL | Some components have labels; no systematic `accessibilityLabel` audit |
| Semantic heading hierarchy | ❌ UNKNOWN | Not tested with screen reader |
| Focus order logical | ❌ UNKNOWN | Not tested |
| Dynamic content announcements | ❌ UNKNOWN | Not tested |

---

## Dynamic Text / Font Scaling

| Requirement | Current State |
|-------------|---------------|
| Text scales with system font size | ❌ UNKNOWN — `typography.ts` uses fixed font sizes |
| Layout does not break at larger sizes | ❌ UNKNOWN — not tested |

---

## Contrast

| Requirement | Current State |
|-------------|---------------|
| Minimum 4.5:1 for body text | ⚠️ PARTIAL — `colors.ts` defines `text: '#0F172A'` on `background: '#F8FAFC'` — likely sufficient but not verified |
| Non-colour status indicators | ✅ PARTIAL — Badge component uses text labels alongside colours |

---

## Touch Targets

| Requirement | Current State |
|-------------|---------------|
| Minimum 44×44pt touch targets | ❌ UNKNOWN — not verified |
| Adequate spacing between tappable items | ⚠️ PARTIAL — spacing system exists but not audited for touch |

---

## Reduced Motion

| Requirement | Current State |
|-------------|---------------|
| Respect system reduced-motion setting | ❌ NOT IMPLEMENTED — `react-native-reanimated` animations do not check for reduced motion preference |

---

## Colour-Independent Status Communication

- Open/Closed status: Badge uses colour (green/red) + text label ✅
- Free/Paid: Text label ✅
- Ratings: Numeric score + star character ✅

---

## Accessible Facility Attributes

The `Facility` type includes comprehensive accessibility fields. These are **only as useful as the data** — seed data quality for accessibility attributes is critical.

Key fields for accessibility-filtered search:
- `is_accessible`, `has_wheelchair_access`
- `requires_radar_key`, `has_adult_changing_place`
- `has_lift`, `has_grab_rails`
- `is_single_room`, `is_quiet`
- `has_baby_changing`, `has_family_room`, `has_family_toilet`

---

## Dignity-Related Filters

- `is_gender_neutral` — important for non-binary and trans users
- `is_single_occupancy` — important for users needing privacy
- `is_quiet` — important for neurodivergent users
- `has_free_period_products` — dignity and health equity
- `has_sanitary_bins` — basic dignity requirement

---

## Offline and Degraded-Network Behaviour

| Scenario | Current State |
|----------|---------------|
| No network at app launch | ❌ UNKNOWN — likely shows blank/error |
| Network lost during use | ❌ UNKNOWN |
| Offline facility data available | 🔶 IMPLEMENTED (offline download), but not tested end-to-end |
| Clear offline status indicator | ❌ NOT IMPLEMENTED |

---

## iOS VoiceOver Test Matrix

| Test | Status |
|------|--------|
| All buttons have accessible labels | Not tested |
| Map markers are navigable | Not tested |
| Emergency button reachable within 3 swipes | Not tested |
| Facility detail readable | Not tested |
| Forms (login, submission) accessible | Not tested |

---

## Android TalkBack Test Matrix

| Test | Status |
|------|--------|
| All buttons have accessible labels | Not tested |
| Map markers are navigable | Not tested |
| Emergency button reachable within 3 swipes | Not tested |
| Facility detail readable | Not tested |
| Forms (login, submission) accessible | Not tested |

---

## Gap Summary

| Gap | Severity | Action |
|-----|----------|--------|
| Auth gate blocks urgent access | Critical | Add unauthenticated browse path |
| 4 tabs vs 3-tab policy | High | Merge Map+List into single Find tab |
| No screen reader testing | High | Test with VoiceOver and TalkBack; add accessibilityLabels |
| Fixed font sizes | Medium | Use scalable font units; test with accessibility sizes |
| No reduced motion support | Medium | Add `useReducedMotion()` hook; disable animations when set |
| Touch target sizes unknown | Medium | Audit and fix to 44pt minimum |
| Emoji tab icons | Low | Replace with proper vector icons with accessibility labels |
| No offline status indicator | Low | Add connectivity-aware banner |

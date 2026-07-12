# Relief — Testing and Release Strategy

**Last updated:** 2026-07-12  
**Status:** Strategy document — no testing infrastructure currently exists.

---

## Current State

| Quality Gate | Present? | Detail |
|-------------|----------|--------|
| Static type checking | ✅ TypeScript strict mode | `tsconfig.json`: `"strict": true`. Run: `npx tsc --noEmit` |
| Linting | ❌ | No ESLint dependency or configuration |
| Formatting | ❌ | No Prettier dependency or configuration |
| Unit tests | ❌ | No test framework, no test files |
| Integration tests | ❌ | No test framework |
| Component tests | ❌ | No test framework |
| End-to-end tests | ❌ | No test framework |
| CI pipeline | ❌ | No GitHub Actions, no EAS Build automation |
| Build verification | ❌ | No build scripts beyond `expo start` |
| Dependency audit | ❌ | No `npm audit` script |

---

## Required Testing Strategy

### Static Analysis

| Gate | Tool | When | Evidence |
|------|------|------|----------|
| Type checking | `tsc --noEmit` | Pre-commit, CI | Zero errors |
| Linting | ESLint + TypeScript plugin | Pre-commit, CI | Zero warnings |
| Formatting | Prettier | Pre-commit | Consistent formatting |

**Setup required:** Add ESLint, Prettier, and `lint-staged` to devDependencies. Add scripts to `package.json`.

---

### Unit Testing

| Target | Framework | Scope |
|--------|-----------|-------|
| Scoring algorithm (`aiRecommendations.ts`) | Jest + React Native Testing Library | Verify weights produce expected rankings given known inputs |
| Haversine distance (`routePlanning.ts`) | Jest | Verify distance calculations against known coordinate pairs |
| Plus Code encoding (`locationSharing.ts`) | Jest | Verify output matches known Plus Code reference values |
| Cluster algorithm (`MapScreen.tsx`) | Jest | Verify clustering with known facility positions |
| Filter query building (`facilities.ts`) | Jest | Verify correct Supabase query construction for filter combinations |
| Report expiry logic | Jest | Verify expiry time calculations |

**Setup required:** Add Jest, `@testing-library/react-native`, and test scripts.

---

### Component Testing

| Component | Scope |
|-----------|-------|
| Button, Card, Input, Badge | Render, interaction, accessibility labels |
| PremiumGate | Render with different entitlement states |
| AnimatedPin | Render at different coordinates |

---

### Navigation Testing

| Scenario | Scope |
|----------|-------|
| Unauthenticated → Login screen | Verify redirect |
| Authenticated → Main tabs | Verify session detection |
| "Need One Now" button → emergency display | Verify flow |
| Deep linking (`relief://`) | Verify scheme handling |

---

### Supabase Integration Testing

| Scenario | Scope |
|----------|-------|
| Anon read of verified facilities | Verify RLS allows |
| Anon write attempt | Verify RLS denies |
| Authenticated read of own data | Verify RLS scoping |
| Authenticated write to another user's data | Verify RLS denies |
| Storage upload (authenticated) | Verify bucket policies |
| Storage read (public, approved photos) | Verify access |
| Edge Function execution | Verify cron trigger, webhook receipt |

**Requires:** Development Supabase project with migrations applied and seed data.

---

### RLS Testing (Separate Suite)

Every RLS policy must be tested:
1. Anon user attempts operation → denied (except public reads)
2. Authenticated user A reads own data → allowed
3. Authenticated user A reads user B's data → denied
4. Service role performs admin operation → allowed
5. Authenticated user attempts admin operation → denied

---

### External Provider Contract Tests

| Provider | Test |
|----------|------|
| Mapping API | Geocoding returns expected coordinates for known address |
| Routing API | Route between two known points returns reasonable polyline |
| RevenueCat SDK | Products fetch, purchase flow (sandbox), restore flow (sandbox) |
| RevenueCat webhook | Webhook receipt → entitlement updated in database |
| what3words (if retained) | Known coordinate → expected 3-word address |

---

### End-to-End Urgent-Use Journey

The critical path test:
1. Open app (no account)
2. Location permission granted
3. "Need One Now" button visible and tapable
4. Closest facility displayed within 5 seconds
5. Facility name, walking time, open status, score visible
6. "Get Directions" opens platform maps

**Test on:** Real iOS device, real Android device, simulator with location mocking.

---

### Accessibility Testing

| Test | Tool | Target |
|------|------|--------|
| Screen reader navigation | VoiceOver (iOS), TalkBack (Android) | All screens navigable |
| Dynamic text | Accessibility Inspector | No layout breakage at largest text size |
| Contrast | Accessibility Inspector / contrast checker | All text meets 4.5:1 minimum |
| Touch targets | Manual / Accessibility Inspector | All interactive elements ≥ 44pt |
| Reduced motion | System setting | Animations disabled or reduced |

---

### Offline and Degraded-Network Testing

| Scenario | Expected Behaviour |
|----------|-------------------|
| Launch with no connectivity | Show cached data or clear offline message; no crash |
| Network lost after data load | Show last-known data with "offline" banner |
| Download region for offline | Verify data available when offline |
| Search offline data | Return results from SQLite |

---

### Purchase and Entitlement Testing

| Scenario | Expected Behaviour |
|----------|-------------------|
| Purchase Basic Access (lifetime) | Entitlement active immediately; premium features unlocked |
| Purchase Plus (monthly) | Entitlement active; expires after period if not renewed |
| Restore purchases | Previous purchases recovered |
| Cancel subscription | Entitlement remains active until period end |
| Refund | Entitlement revoked immediately |
| Purchase with no network | Clear error message |
| Sandbox testing | RevenueCat sandbox environment used for all test purchases |

---

### Privacy and Deletion Testing

| Scenario | Expected Behaviour |
|----------|-------------------|
| Account deletion | User data removed; anonymised contributions retained |
| Data export | Machine-readable JSON of all user data delivered |
| Photo upload → check EXIF | EXIF metadata stripped before public URL served |
| Photo upload → check faces | Faces blurred before public URL served |
| Location not stored server-side (anonymous) | Anon queries do not persist location data |

---

### Store Build Verification

| Check | Detail |
|-------|--------|
| EAS Build succeeds for iOS | Production build completed without errors |
| EAS Build succeeds for Android | Production build completed without errors |
| App size acceptable | Under store limits |
| No debug code in production bundle | Verified by build profile |
| Environment variables correct per environment | `.env.production` values used |

---

### Seed Data Quality

| Check | Detail |
|-------|--------|
| All facilities have coordinates | No null latitude/longitude |
| Coordinates within launch geography | Bounding box check |
| Accessibility attributes populated | Not all `false` by default |
| Opening hours structured correctly | Valid JSONB format |
| No duplicate facilities | Deduplication check |

---

### Production Smoke Tests (Post-Release)

| Check | Frequency |
|-------|-----------|
| Map renders with facilities | After every deploy |
| Search returns results | After every deploy |
| Auth sign-in works | After every deploy |
| Emergency button works | After every deploy |
| Purchase flow completes (sandbox) | Weekly |
| Edge Functions executing | Monitored continuously |

---

## Evidence Required for VERIFIED Status

A feature may only be marked **VERIFIED** when all of:
1. Implementation code exists and passes type checking
2. Unit tests pass (if applicable)
3. Integration with backend service works end-to-end in development environment
4. Manual testing on at least one real device confirms behaviour
5. Accessibility requirements met (labels, contrast, touch targets)
6. Error states handled (offline, timeout, permission denied)
7. Security requirements met (RLS, input validation, rate limiting where applicable)

---

## Release Checklist

Before any store submission:
- [ ] All TypeScript errors resolved
- [ ] ESLint zero warnings
- [ ] All BLOCKER decisions resolved
- [ ] RLS policies tested on all tables
- [ ] Photo processing pipeline verified (EXIF + faces)
- [ ] Account deletion flow tested
- [ ] Purchase, restore, cancel, refund flows tested
- [ ] Privacy Policy published and linked in app
- [ ] Terms of Service published and linked in app
- [ ] Support email operational
- [ ] App store listing assets prepared
- [ ] EAS Build succeeds for both platforms
- [ ] Smoke tests pass on production build

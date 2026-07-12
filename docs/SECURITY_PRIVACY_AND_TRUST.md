# Relief — Security, Privacy and Trust

**Last updated:** 2026-07-12  
**Status:** Requirements document — most security controls are not yet implemented.

This document consolidates the security, privacy, and trust requirements from the original Security Addendum with current-state evidence. It is an implementation obligations document, not a compliance attestation.

---

## Threat Model (Summary)

**Primary assets to protect:**
- User location data (even approximate)
- User authentication credentials
- User-submitted photos (may contain faces, location metadata, number plates)
- Facility data integrity (incorrect data has real-world safety implications)
- Subscription entitlements (financial)

**Primary threats:**
- Location tracking or exposure
- Photo metadata leaking precise locations
- Malicious facility data (fake locations, false accessibility claims)
- Review manipulation
- Spam and abuse of community features
- Subscription bypass
- Credential theft
- Unauthorised access to user data

---

## Trust Boundaries

### Current (all client-side — no server trust boundary)

```
User Device ─── [all logic runs here] ─── (no backend connected)
```

All code runs on the client. There is no server-side enforcement of any security property. The Supabase client libraries are present but will fail without a backend.

### Target

```
User Device ─── anon key ─── Supabase (RLS-enforced reads)
User Device ─── authenticated JWT ─── Supabase (RLS-enforced writes)
User Device ─── API key ─── RevenueCat
Supabase Edge Function ─── service_role ─── Supabase (privileged operations)
RevenueCat ─── webhook ─── Supabase Edge Function (entitlement sync)
```

---

## Authentication Security

| Requirement | Current State | Implementation |
|-------------|---------------|----------------|
| No login required for basic search | ❌ NOT IMPLEMENTED — auth gate blocks all access | Add unauthenticated browse path |
| Email verification | ❌ NOT IMPLEMENTED — Supabase Auth not configured | Enable in Supabase dashboard |
| No password storage | ✅ COMPLIANT — Supabase Auth handles credentials | N/A (by design) |
| No service_role key in client | ✅ COMPLIANT — no key present in codebase | Must maintain this |
| Session persistence | 🔶 CODE EXISTS — `persistSession: true` | Verify Secure Store usage vs AsyncStorage |

---

## Row Level Security (RLS)

| Requirement | Current State |
|-------------|---------------|
| RLS on every table | 🔶 DEFINED IN MIGRATIONS — not deployed |
| Default deny-all | 🔶 DEFINED IN MIGRATIONS — not deployed |
| Users edit own data only | 🔶 DEFINED IN MIGRATIONS — not deployed |
| Public facility data read-only | 🔶 DEFINED IN MIGRATIONS — not deployed |
| Facility creation → moderation queue | 🔶 DEFINED IN MIGRATIONS — not deployed |
| Admin actions via service_role only | 🔶 DEFINED IN MIGRATIONS — not deployed |

**Evidence:** Migration files contain RLS policy definitions. See `supabase/migrations/`.

---

## Location Privacy

| Requirement | Current State | Evidence |
|-------------|---------------|----------|
| Explain why location needed | ✅ IMPLEMENTED | `app.json` InfoPlist descriptions |
| No continuous tracking | ✅ COMPLIANT | `useLocation.ts` uses foreground location only |
| No precise location history storage | 🔶 UNKNOWN | No server to store data yet; but no explicit clearing in code |
| Clear location from memory | ❌ NOT IMPLEMENTED | No location-clearing logic found |
| Manual postcode/town search | ✅ IMPLEMENTED | `MapScreen.tsx` search input; BACKEND-DEPENDENT for results |

---

## Community Abuse Prevention

| Requirement | Current State | Evidence |
|-------------|---------------|----------|
| Rate limits | 🔶 CLIENT-SIDE ONLY | `checkRateLimit()` queries Supabase table; not server-enforced |
| Duplicate checks | 🔶 CODE EXISTS | `checkDuplicateReport()` in `community.ts` |
| Moderation queue | 🔶 CODE EXISTS | Tables defined; no admin UI |
| No anonymous abuse | ❌ NOT IMPLEMENTED | Auth required for contributions (correct); anon rate limits missing |
| Spam protection | ❌ NOT IMPLEMENTED | No CAPTCHA, no server-side spam detection |
| Input sanitisation | ❌ UNKNOWN | No sanitisation functions found in codebase |

---

## Photo and Media Security

| Requirement | Current State | Evidence |
|-------------|---------------|----------|
| EXIF metadata stripping | ❌ NOT IMPLEMENTED | `exif_stripped: false` set on upload; no processing |
| Face blurring | ❌ NOT IMPLEMENTED | `faces_blurred: false` set on upload; no processing |
| Content moderation | ❌ NOT IMPLEMENTED | Moderation queue exists; no automated screening |
| Photo storage access control | 🔶 PLANNED | Storage bucket policies defined; bucket not created |

**Critical gap:** Photos uploaded through the current code path would be stored with full EXIF metadata (potentially including GPS coordinates) and unblurred faces. This is the highest-priority privacy fix before any photo upload feature goes live.

---

## Subscription and Entitlement Security

| Requirement | Current State |
|-------------|---------------|
| Server-side entitlement verification | 🔶 PLANNED — RevenueCat webhook code exists; not deployed |
| Client-side entitlement caching | 🔶 CODE EXISTS — `SubscriptionContext.tsx` |
| No client-side entitlement bypass | 🔶 DEPENDENT ON SERVER-SIDE ENFORCEMENT |
| Restore purchases flow | 🔶 CODE EXISTS — `restorePurchases()` in `revenuecat.ts` |

---

## GDPR and UK Privacy Compliance

| Requirement | Current State |
|-------------|---------------|
| Privacy Policy published | ❌ NOT STARTED |
| Terms of Service published | ❌ NOT STARTED |
| Account deletion | ❌ NOT IMPLEMENTED |
| Data export | ❌ NOT IMPLEMENTED |
| Delete review/photo | ❌ NOT IMPLEMENTED |
| Privacy contact email | ❌ NOT ESTABLISHED |
| Marketing consent tracking | ❌ NOT IMPLEMENTED |
| PII in logs | ❌ UNKNOWN — no logging strategy defined |
| HTTPS | 🔶 Supabase provides HTTPS by default (when connected) |

---

## Simulated Location-Code Risk

**what3words simulation is a safety risk.** When no API key is configured, `coordsToWhat3Words()` returns deterministic fake words from a coordinate hash. Users relying on these codes in an emergency could be directed to non-existent locations.

**Recommendation:** Remove the simulation fallback. Return an error when no API key is configured. Display "Location code unavailable" rather than fake data.

---

## Child and Vulnerable User Considerations

- The app is a utility tool, not a social network. No direct user-to-user communication.
- Photo uploads and reviews could expose children or vulnerable users if not moderated.
- Accessibility features (adult changing places, RADAR key) indicate an intent to serve disabled users — data accuracy for these attributes is safety-critical.

---

## Security Gaps Blocking Release

| Gap | Severity | Blocks |
|-----|----------|--------|
| No RLS enforcement | Critical | Any data access |
| No EXIF stripping | Critical | Photo uploads |
| No face blurring | High | Photo uploads |
| No server-side rate limiting | High | Community features |
| No account deletion | High | GDPR compliance |
| what3words simulation | Medium | Location sharing |
| No admin audit logging | Medium | Moderation |
| No input sanitisation | Medium | All user-generated content |
| No CAPTCHA/spam prevention | Medium | Registration, contributions |

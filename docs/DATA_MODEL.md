# Relief — Proposed Data Model

> **Status: Proposed — not yet deployed.**  
> No Supabase project exists. These tables, views, RPCs, storage buckets, and Edge Functions are inferred from TypeScript types, service queries, and SQL migration files. Fields marked `TBD` are not yet defined in any source file.

---

## Tables

### `facilities`

**Purpose:** Core facility data — the primary table for all facility discovery.

**Referencing code:** `services/facilities.ts`, `services/routePlanning.ts`, `services/offlineMaps.ts`, `services/aiRecommendations.ts`, `services/notificationAlerts.ts`, `types/index.ts`

**Migration:** `supabase/migrations/001_initial_schema.sql` — exists, not deployed

| Column | Type | Notes |
|--------|------|-------|
| `id` | UUID PK | |
| `name` | TEXT NOT NULL | |
| `address` | TEXT NOT NULL | |
| `latitude` | DOUBLE PRECISION | Spatial queries use bounding box; PostGIS not yet used |
| `longitude` | DOUBLE PRECISION | |
| `postcode` | TEXT NOT NULL | Indexed |
| `town` | TEXT NOT NULL | Indexed |
| `country` | TEXT DEFAULT 'GB' | Indexed |
| `photos` | TEXT[] DEFAULT '{}' | Array of photo URLs |
| `open_hours` | JSONB | Structured open/close times per day |
| `is_free` | BOOLEAN DEFAULT true | |
| `price_note` | TEXT | |
| `access_notes` | TEXT | |
| `last_verified_at` | TIMESTAMPTZ | |
| `is_accessible` | BOOLEAN | Phase 1 amenity |
| `is_disabled_access` | BOOLEAN | Phase 1 amenity |
| `has_baby_changing` | BOOLEAN | Phase 1 amenity |
| `has_family_room` | BOOLEAN | Phase 1 amenity |
| `is_gender_neutral` | BOOLEAN | Phase 1 amenity |
| `is_single_occupancy` | BOOLEAN | Phase 1 amenity |
| `is_24h` | BOOLEAN | Phase 1 amenity |
| `is_single_room` | BOOLEAN | Phase 3 — privacy |
| `has_floor_to_ceiling_cubicles` | BOOLEAN | Phase 3 — privacy |
| `is_quiet` | BOOLEAN | Phase 3 — privacy |
| `has_wheelchair_access` | BOOLEAN | Phase 3 — accessibility |
| `requires_radar_key` | BOOLEAN | Phase 3 — accessibility |
| `has_adult_changing_place` | BOOLEAN | Phase 3 — accessibility |
| `has_lift` | BOOLEAN | Phase 3 — accessibility |
| `has_grab_rails` | BOOLEAN | Phase 3 — accessibility |
| `has_baby_changing_inside` | BOOLEAN | Phase 3 — baby |
| `has_separate_changing_room` | BOOLEAN | Phase 3 — baby |
| `has_family_toilet` | BOOLEAN | Phase 3 — baby |
| `has_pram_access` | BOOLEAN | Phase 3 — baby |
| `has_soap` through `has_drinking_water` | BOOLEAN | Phase 3 — 10 equipment fields |
| `noise_level` | INTEGER 1-5 CHECK | Phase 3 — environment |
| `temperature` | INTEGER 1-5 CHECK | Phase 3 — environment |
| `lighting` | INTEGER 1-5 CHECK | Phase 3 — environment |
| `smell` | INTEGER 1-5 CHECK | Phase 3 — environment |
| `has_staff_nearby` | BOOLEAN | Phase 3 — safety |
| `has_cctv` | BOOLEAN | Phase 3 — safety |
| `is_women_friendly` | BOOLEAN | Phase 3 — safety |
| `is_family_friendly` | BOOLEAN | Phase 3 — safety |
| `is_water_refill_station` through `is_ev_charging` | BOOLEAN | Phase 3 — facility types (7 fields + `is_picnic_area` TBD in types) |
| `overall_score` | DOUBLE PRECISION DEFAULT 0 | |
| `cleanliness_rating` through `environment_rating` | DOUBLE PRECISION | 6 rating dimensions |
| `created_at` | TIMESTAMPTZ DEFAULT NOW() | |
| `updated_at` | TIMESTAMPTZ DEFAULT NOW() | |
| `created_by` | UUID REFERENCES auth.users | |
| `is_verified` | BOOLEAN DEFAULT false | Indexed |

**RLS requirements:** Public read for verified facilities. Authenticated insert → moderation queue, not direct. Admin/service_role write.

**Open questions:**
- Should spatial queries use PostGIS `GEOGRAPHY` type instead of bounding-box?
- Is `country` necessary if launching UK-only initially?
- TBD: `is_picnic_area` field referenced in types but not in migration 001

---

### `facility_submissions`

**Purpose:** Moderation queue for user-submitted facilities.

**Migration:** `supabase/migrations/20260624_community_features.sql`

**RLS:** Users see own submissions; service_role full access.

| Column | Notes |
|--------|-------|
| `id` | UUID PK |
| `user_id` | FK auth.users |
| `status` | 'pending', 'approved', 'rejected' |
| `name`, `address`, `latitude`, `longitude`, `postcode`, `town`, `country` | Required fields |
| `access_notes`, `is_free`, `price_note`, `open_hours`, `photos` | Optional fields |
| `is_accessible` through `is_24h` | Amenity fields |
| `notes`, `access_codes`, `submission_notes` | Text fields |
| `created_at`, `reviewed_at`, `reviewed_by`, `rejection_reason` | Metadata |

---

### `photo_moderation`

**Purpose:** Queue for uploaded facility photos pending moderation.

**Migration:** `supabase/migrations/20260624_community_features.sql`

| Column | Notes |
|--------|-------|
| `id` | UUID PK |
| `facility_id` | FK facilities |
| `user_id` | FK auth.users |
| `url`, `thumbnail_url` | Storage URLs |
| `status` | 'pending', 'approved', 'rejected', 'reported' |
| `exif_stripped` | BOOLEAN DEFAULT false — **must be set true by server-side processing** |
| `faces_blurred` | BOOLEAN DEFAULT false — **must be set true by server-side processing** |
| `reported_by`, `report_reason` | For user reports |

**RLS:** Users insert own photos. Anyone views approved. Users view own pending.

**Open question:** What service performs EXIF stripping and face blurring?

---

### `temporary_reports`

**Purpose:** Time-limited reports (closure, busy, cleaning, no water) that auto-expire.

**Migration:** `supabase/migrations/20260624_community_features.sql`

**RLS:** Authenticated users insert; all view active reports.

**Edge Function:** `expire-reports` marks reports expired via cron.

---

### `correction_requests`

**Purpose:** User-submitted corrections to existing facility data.

**Migration:** `supabase/migrations/20260624_community_features.sql`

**RLS:** Users insert; service_role reviews.

---

### `access_codes`

**Purpose:** Community-shared door/access codes for facilities.

**Migration:** `supabase/migrations/20260624_community_features.sql`

**RLS:** Authenticated users insert and view.

**Security concern:** Access codes visible to all authenticated users. Consider abuse risk.

---

### `badges` / `user_badges`

**Purpose:** Gamification — badge definitions and user awards.

**Migration:** `supabase/migrations/20260624_community_features.sql`

**RLS:** Users view own badges; service_role awards.

---

### `rate_limits`

**Purpose:** Per-user, per-action rate limit tracking.

**Migration:** `supabase/migrations/20260624_community_features.sql`

**RLS:** Users read own; authenticated insert.

**Security concern:** Rate limits enforced at client level. Must be moved to Edge Function/server-side enforcement.

---

### `reviews`

**Purpose:** User reviews with six-dimensional ratings.

**Migration:** `supabase/migrations/20260624_community_features.sql`

**Referencing code:** `services/community.ts` (review reports); rating fields in `types/index.ts`

**RLS:** Authenticated users insert; all view.

---

### `review_reports`

**Purpose:** Abuse reports against reviews.

**Migration:** `supabase/migrations/20260624_community_features.sql`

---

### `saved_profiles`

**Purpose:** User-saved filter preference profiles (IBS Mode, Family Mode, etc.).

**Migration:** `supabase/migrations/20260625_premium_features.sql`

**RLS:** Users CRUD own profiles; 10-profile limit enforced in client.

---

### `favourites`

**Purpose:** User-favourited facilities.

**Migration:** `supabase/migrations/20260625_premium_features.sql`

**RLS:** Users CRUD own favourites.

| Column | Notes |
|--------|-------|
| `id` | UUID PK |
| `user_id` | FK auth.users |
| `facility_id` | FK facilities |
| UNIQUE(user_id, facility_id) | |

---

### `user_entitlements`

**Purpose:** Server-side subscription entitlement records (synced from RevenueCat webhook).

**Migration:** `supabase/migrations/20260701_monetisation.sql`

**RLS:** Users read own; service_role (webhook) writes.

| Column | Notes |
|--------|-------|
| `user_id` | FK auth.users |
| `tier` | 'free', 'basic', 'plus' |
| `is_active` | BOOLEAN |
| `is_lifetime` | BOOLEAN |
| `expires_at` | TIMESTAMPTZ |
| `will_renew` | BOOLEAN |
| `is_grace_period` | BOOLEAN |

---

## Storage Buckets

| Bucket Name | Purpose | Referenced In | Status |
|-------------|---------|---------------|--------|
| `facility-photos` | User-uploaded facility photos | `services/community.ts` | Not created |

**Required policies:** Authenticated upload; public read for approved; admin delete.

---

## Edge Functions

| Function | Purpose | File | Status |
|----------|---------|------|--------|
| `expire-reports` | Cron-triggered: marks expired temporary reports | `supabase/functions/expire-reports/index.ts` | Written, not deployed |
| `revenuecat-webhook` | Receives RevenueCat webhooks; syncs entitlements to `user_entitlements` | `supabase/functions/revenuecat-webhook/index.ts` | Written, not deployed |

---

## RPCs (Database Functions)

| Function | Purpose | Referenced In | Migration |
|----------|---------|---------------|-----------|
| `expire_temporary_reports()` | Marks reports past expiry as expired | `supabase/functions/expire-reports/index.ts` | TBD — not yet in migrations |

---

## Views

None currently defined or referenced.

---

## Open Questions

1. Should spatial queries use PostGIS instead of bounding-box latitude/longitude comparisons?
2. Where is `is_picnic_area` defined? Referenced in types but not in migration 001.
3. What is the exact list of facility type booleans? Types and migrations may differ.
4. Should `access_codes` be publicly viewable to all authenticated users?
5. Is `rate_limits` enforced server-side or client-side? Currently client-side only — insufficient.
6. Are `reviews` and `facilities` linked for automatic rating recalculation?
7. Should `user_entitlements` be the authoritative source, or is RevenueCat the source of truth?

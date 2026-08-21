# Relief TfL Facility Model Adjudication — 2026-08-21

> **PROPOSED / PRODUCTION EXECUTION NOT AUTHORIZED**

## Final classification

**RELIEF MULTI-TOILET FACILITY MODEL — ADJUDICATED / IMPLEMENTATION NOT AUTHORIZED**

The preceding TfL package remains classified **RELIEF TFL REAL FEED — RECONCILED / PRODUCTION APPLY NOT AUTHORIZED**. This document is an additive architecture decision and evidence package only. It does not apply TfL `INSERT`, `SOURCE_LINK`, or `ENRICHMENT` operations, write staging rows, create an import run, deploy a migration, or mutate Production Supabase.

Production mutations in this batch: **0**.

## Scope and starting state

The audit starts at commit `05d4d2cc372880953610539baa49892fab8856a1`, on branch `codex/toilet-map-apply-1a-production-deploy`, in `hourwise/Relief`. The protected unrelated working-tree changes were present and were not touched:

- `.easignore` — modified
- `app.json` — modified
- `docs/EAS_CONFIG_AUDIT.md` — untracked

The current read-only production checkpoint remains:

| Relation | Count |
|---|---:|
| `facilities` | 15,620 |
| `facility_sources` | 15,620 |
| `import_runs` | 5 |
| `toilet_map_import_staging` | 0 |

No production connection or mutation was required for this adjudication. The counts above are the already recorded baseline in the frozen TfL evidence package.

## Decision summary

### Recommendation

**INTRODUCE_TOILET_UNIT_MODEL**

Use an additive parent/child capability, with a separate strongly typed source table for unit-level source rows:

```text
facilities (discoverable venue/place and map anchor)
  └── toilet_units (optional explicit physical/provision units)
        └── toilet_unit_sources (source rows describing a unit or unit candidate)

facility_sources (source rows describing the parent venue/place)
```

This is a recommendation for a future, separately authorized schema and product change. It is not a migration and does not reinterpret or rewrite the current 15,620 rows.

### Why the current one-row model is insufficient for TfL

The live contract treats one `facilities` row as the public map/search/detail object. It contains a single coordinate, a single `open_hours` value, a single `is_free` value, and booleans such as `is_accessible`, `has_baby_changing`, and `is_gender_neutral`. It has no canonical toilet type, gateline position, toilet-specific location description, or stable unit identity.

The real TfL package contains 410 toilet rows across 179 stations. There are 147 stations with more than one toilet row, including 147 Male rows, 147 Female rows, and 116 Unisex rows. It also has 274 rows inside the gateline and 136 outside it, 119 accessible rows, and 80 baby-changing rows. TfL supplies station-level coordinates, not toilet-level coordinates. Therefore, one parent row cannot losslessly represent all source attributes without either collapsing distinctions or putting source-specific facts into misleading parent columns.

The current one-row model remains a valid compatibility surface for existing data, but it is not a sufficient canonical model for promoting multi-row TfL evidence into user-facing unit-level facts.

## Part A — current Relief model audit

### What one `facilities` row means today

Operationally, a row in `facilities` is a published discoverable facility at one map location. It can represent a standalone public toilet, a toilet in a venue, or an imported public provision record. The schema does not enforce whether the row is:

- a venue containing several toilets;
- one toilet room/unit;
- an aggregate of a venue’s toilet provision; or
- a source record that happens to have been promoted as a facility.

The application nevertheless assumes that the row is the complete object returned to a person. Map pins, search results, nearest-facility results, details, favourites, photos, reports, corrections, access codes, and exports all use `facilities.id` as their target. This is the key model ambiguity.

The existing data provides evidence that the row is not reliably one physical toilet: a read-only analysis of the published snapshot found 44 same-name/same-coordinate groups containing 94 rows. These are not automatically declared duplicates or multi-unit venues; identical names and coordinates are only evidence that parent identity needs stronger rules.

### Fields by current meaning

| Current field family | Current representation | Adjudication finding |
|---|---|---|
| Venue/place | `name`, `address`, `postcode`, `town`, `country` | Parent-like, but the schema does not formally identify a venue. |
| Location | `latitude`, `longitude`, generated `location` geography | One point for the public facility object; no precision enum and no unit coordinate. |
| Access/amenities | `is_accessible`, `is_disabled_access`, wheelchair/RADAR/lift/grab-rail and related booleans | Canonical row-level values; they cannot express which of several units has the capability. |
| Type/gender | `is_gender_neutral`, `is_single_occupancy`, `is_single_room` | Partial and ambiguous. There is no Male/Female/Unisex field. |
| Baby changing | `has_baby_changing`, `has_baby_changing_inside`, family/adult-changing fields | Row-level values; no unit ownership. |
| Cost | `is_free`, `price_note` | One value for the row; it cannot represent different charges by unit or access route. |
| Opening | `open_hours`, `is_24h`, `access_notes` | One aggregate/opening contract; no unit-specific schedules. |
| Location description | Mostly `access_notes` | Not a typed toilet location; gateline/platform/ticket-hall distinctions are not first-class. |
| Provenance | `field_provenance` JSONB and `facility_sources` | Parent-linked provenance; raw source data can be retained, but there is no canonical unit target. |
| Verification | publication, verification, community/staff timestamps | Parent-level governance and freshness. |
| Ratings | overall and category rating columns | Parent-level aggregates; no active review table or unit-level rating target. |

### Tables and user-linked references

The live schema has strong `facility_id` foreign keys from:

- `facility_sources`;
- `favourites`;
- `temporary_reports`;
- `facility_reports`;
- `correction_requests`;
- `access_codes`; and
- `photo_moderation`.

`facility_submissions` is a contributor-owned pending record and repeats facility-shaped fields, but does not directly link to an existing facility. `review_reports` exists as a stale table with `review_id`, but the audit found no active `reviews` table or review-write workflow. `saved_profiles` stores preferences rather than facility references.

The export Edge Function explicitly resolves facility context for favourites, submissions, reports, corrections, access codes, photos, and canonical attribution. Any future unit target must preserve this user-data boundary; adding a unit reference is not a reason to expose other users’ contributions or source internals.

### RPCs and query contracts

The map and search paths query published `facilities` rows directly:

- `fetchViewportFacilities()` uses latitude/longitude bounds and `facilities` filters;
- `fetchNearbyFacilities()` uses a bounded viewport approximation;
- `searchFacilities()` searches `town` and `postcode` and returns facilities;
- `fetchFacilityById()` returns one facility row;
- `fetchClosestFacility()` calls `find_nearest_facilities()` and then reads `is_24h` from `facilities` before ranking candidates.

`find_nearest_facilities()` returns one row per published `facilities` record with the full facility-shaped projection and a calculated distance. It does not join source rows or a child-unit relation. `expire_temporary_reports()` is the report-expiry function. Moderation RPCs list and decide facility submissions and correction requests, but the current moderation contract deliberately does not apply approved submissions or corrections to canonical facilities.

### Current failure modes for a multi-toilet station

If the current one-row model is used directly for a station with several TfL rows:

1. A Male, Female, and Unisex row cannot all be represented by the existing booleans.
2. `is_accessible = true` cannot say whether all units or only one unit is accessible.
3. `has_baby_changing = true` cannot identify which unit or location provides it.
4. `is_free` cannot represent different charges or an unknown charge across units.
5. `open_hours` and `access_notes` cannot represent unit-specific access windows.
6. `IsInsideGateLine` and a textual location such as ticket hall cannot be represented without overloading `access_notes`.
7. The station coordinate would look like a toilet coordinate even though TfL does not provide one.
8. One source row could be linked to a parent, but a second row would either collide, create a duplicate parent pin, or be left as raw evidence.
9. A parent enrichment could silently overwrite a canonical value supplied by another source.
10. Favourites and reports would have no way to state whether the whole venue or only one unit was saved/reported.

## Part B — candidate models

### Model 1 — retain the existing one-row model

**Classification: insufficient as the long-term canonical model; acceptable only as a compatibility and source-evidence surface.**

It is simple and does not require migration. It supports the present app contract and lets `facility_sources.raw_data` preserve source attributes. It cannot accurately promote multiple toilets with different type, gateline, location, opening, charge, or capability facts. It can preserve stable TfL IDs only as provenance, not as canonical unit identity. A parent boolean would become an ambiguous aggregate and would be unsafe for precise filters.

### Model 2 — parent facility plus child toilet units

**Classification: recommended, subject to a separately authorized additive migration.**

`facilities` remains the discoverable map/search parent. An optional `toilet_units` table stores explicit unit/provision details only when evidence supports them. Unit attributes can include type, accessibility, baby changing, charge, opening/access, gateline, text location, and precision. Unit sources are linked by a separate table with strong foreign keys.

This model preserves multiple source rows without requiring multiple map pins. It supports unit-aware detail and filters while retaining current parent-linked user data. Its costs are additive schema, query contracts, moderation decisions, and a unit-aware contribution workflow.

### Model 3 — parent plus source-level subrecords only

**Classification: useful interim stage, not sufficient as the final user-facing model.**

This would retain the current parent and add or extend source records so all TfL rows are preserved under the station/facility. It is the lowest-risk provenance improvement and is sufficient when the product only needs auditability. It does not let users filter for an accessible child unit, see Male/Female/Unisex choices, report one unit, or distinguish unit opening/access facts. It should be the fallback for unresolved source rows even after child support exists.

### Model 4 — generalized place/provision graph

**Classification: not selected for this bounded change.**

A broader graph of venues, rooms, services, operators, and source assertions could represent everything, but it would add unnecessary abstraction and migration risk before Relief has a stable unit contract. The recommended parent/unit model leaves room for future changing-room or service entities without forcing them into this batch.

## Part C — recommended architecture

### Canonical layers

1. **Parent facility** — the discoverable place and map anchor: station, venue, park, shopping centre, public building, or standalone public toilet location.
2. **Toilet unit** — an explicit provision/unit only where physical or operational distinction is supported. A unit can be Male, Female, Unisex, accessible, baby-changing, or another supported type; these are attributes, not automatic proof of a separate room.
3. **Source record** — the provider’s assertion and stable identity. Source records remain evidence even when the physical-unit relationship is unresolved.
4. **Derived aggregate** — a clearly named parent summary such as “at least one accessible unit”, never a silent overwrite of unit values.

Every layer must retain its own confidence, provenance, and update time. Source-specific attributes are not canonical merely because a feed supplies them.

## Part D — identity and deduplication rules

### Parent identity

Parent matching is deterministic and evidence-ranked:

1. An authoritative stable venue/station identifier from a source, when the source semantics identify the same place.
2. Existing source provenance already linked to that venue.
3. Normalized name plus address/postcode/town, with operator or venue context.
4. Coordinates as supporting evidence, with an explicit precision and tolerance appropriate to the source.
5. Human review where the above disagree or the place contains several nearby facilities.

Distance alone never creates a parent identity. A station name match without station identity or corroborating location is not enough.

### Toilet-unit identity

For TfL, the stable **source-row** identity is exactly `(StationUniqueId, Id)`, represented as a source record ID such as:

`tfl:{StationUniqueId}:toilet:{Id}`

That identity is unique and stable for deduplication of the same TfL row. It is **not** proof that the row is a distinct physical room. A different TfL ID, gender value, or source row count does not alone establish physical separation.

Until independent evidence is available, multi-row groups use one of these explicit classifications:

- `CONFIRMED_DISTINCT_UNIT` — direct physical evidence supports separate units;
- `LIKELY_DISTINCT_UNIT` — strong but not conclusive physical evidence;
- `SOURCE_DISTINCT_PHYSICAL_UNKNOWN` — source rows are distinct but physical relationship is unknown;
- `SAME_UNIT_MULTI_SOURCE` — multiple source assertions resolve to one unit;
- `UNRESOLVED` — insufficient evidence to relate the rows.

The current TfL multi-row evidence is conservatively `SOURCE_DISTINCT_PHYSICAL_UNKNOWN` or `UNRESOLVED`, not automatically a set of canonical children. Any later promotion must retain the source-row IDs and the adjudication reason.

## Part E — attribute ownership

| Attribute | Owner | Rule |
|---|---|---|
| Canonical name | Parent | Name of the discoverable place; unit labels appear separately. |
| Address | Parent | Venue/place address, not a source-specific room description. |
| Latitude/longitude | Parent by default | Must carry precision. TfL rows are `STATION_LEVEL_ONLY; TOILET_COORDINATES_NOT_PROVIDED`. Never fabricate child coordinates. |
| Male/Female/Unisex | Child or source record | Do not collapse values; retain source value when physical identity is unresolved. |
| Accessible | Child plus derived parent aggregate | Parent aggregate means “at least one explicitly accessible unit” only when named as such; it does not mean every unit. Existing legacy boolean is not silently reinterpreted. |
| Baby changing | Child plus derived parent aggregate | Same “at least one known unit” rule; preserve unknown separately. |
| Free/charged | Child or source record | Parent value only when it describes the whole venue or is independently adjudicated. |
| Opening hours | Parent or child | Parent for venue-wide access; child when schedules differ. `is_24h` must not imply every unit is open 24 hours. |
| Gateline status | Child/source | `IsInsideGateLine` is not a parent-wide fact when units differ. |
| Textual toilet location | Child/source | Preserve exact source text, e.g. ticket hall/platform, with provider provenance. |
| RADAR key | Child or parent | Unit-level when a key opens only a particular unit; parent-level only when venue-wide. |
| Ask staff | Child/source | Retain as source or unit access instruction; do not turn it into a universal parent fact. |
| Managed by TfL | Source record, possibly child | TfL operator metadata; not a generic canonical Relief operator field without a provider-neutral contract. |
| Source ID | Source record | `source_name` plus source record ID; for TfL the composite is preserved. |
| Source URL/provider/licence | Source record | Preserve attribution and terms with the source assertion. |
| Provenance | Source record and field-level assertion | The canonical field must identify origin, update time, and confidence. |
| Confidence | Parent, child, and source assertion as applicable | A match confidence is not physical-unit confidence. Keep them separate. |
| Last verified/update time | Parent, child, and source | Do not make a source refresh appear to be community verification. |

The existing parent booleans remain backwards-compatible legacy values until an explicit product/schema decision defines new aggregate columns or a read model. No future importer should set a parent boolean merely because one child/source row is true.

## Part F — feature impact

| Feature | Impact | Contract consequence |
|---|---|---|
| Map pins | `NO_CHANGE` for parent pins; `QUERY_CHANGE` for child-aware filters | One pin per parent by default; no pin per source row. |
| Clustering | `NO_CHANGE` | Cluster parent coordinates only. |
| Search | `QUERY_CHANGE` | Return parent results; search/filter can use indexed child aggregates later. |
| Nearest facility | `QUERY_CHANGE` | Keep `find_nearest_facilities()` parent-shaped; rank/describe child capabilities after parent selection. |
| Facility details | `QUERY_CHANGE` + `UI_CHANGE` | Show an optional list of explicit units and clearly label unknown/source-only facts. |
| Accessibility filters | `QUERY_CHANGE` | “Has an accessible unit” is an existential child query; do not imply all units are accessible. |
| Baby-changing filters | `QUERY_CHANGE` | Same existential/unknown semantics. |
| Free/paid filters | `QUERY_CHANGE` | Filter only on venue-wide or explicitly unit-qualified charge semantics. |
| Opening filters | `QUERY_CHANGE` | A venue open now is distinct from a particular unit open now. |
| Favourites | `NO_CHANGE` in phase 1; `UI_CHANGE` if unit favourites are later supported | Default favourite remains the parent venue. Do not add a nullable unit ID without a uniqueness and migration decision. |
| Temporary/permanent reports | `SCHEMA_CHANGE` for unit-specific reports; `NO_CHANGE` for parent-only phase 1 | Allow “venue closed” versus “one unit closed” only after a unit target exists. |
| Correction requests | `SCHEMA_CHANGE` for unit fields; current parent corrections remain unchanged | A correction must state whether it concerns the parent, a unit, or source evidence. |
| Photos | `QUERY_CHANGE` or `SCHEMA_CHANGE` if unit photos are needed | Existing photos remain parent-linked; no automatic child reassignment. |
| Ratings/reviews | `NO_CHANGE` now; `SCHEMA_CHANGE` if reviews are implemented | No active review table exists; future review target must be explicitly parent or unit. |
| Facility submission | `SCHEMA_CHANGE` if users can submit units | Phase 1 can remain parent-only and preserve current moderation boundary. |
| Moderation | `QUERY_CHANGE` + `SCHEMA_CHANGE` for unit adjudication | Source/unit decisions need a privileged, governed workflow; approvals do not bypass canonical application policy. |
| Source reconciliation | `SCHEMA_CHANGE` | Parent match, unit relationship, and source identity become separate decisions. |
| Account export/deletion | `QUERY_CHANGE` if unit references are added | Export own unit-targeted contributions and resolve parent context without exposing source internals or other users. Existing facility-linked records remain valid. |

## Part G — proposed UI contract

This is a narrow contract, not a broad redesign.

1. **Map:** one pin per discoverable parent venue/station. A station with three source rows does not get three overlapping pins.
2. **Search:** one parent result per venue/place. The result may show a count such as “3 toilet provisions” only when explicit child records exist; source-only rows do not become a fabricated count.
3. **Details:** show the parent name, address, coordinate precision, and aggregate availability. If explicit child units exist, show a list such as “Male — inside gateline”, “Female — inside gateline”, and “Unisex accessible — outside gateline”. Each item must identify whether it is confirmed, likely, source-only, or unknown.
4. **Accessibility:** a parent matches “has an accessible unit” when at least one published child is explicitly accessible. A future “all units accessible” filter would be separate. Unknown remains unknown, not false.
5. **Baby changing:** same existential semantics; show which unit provides it when known.
6. **Reports:** “venue closed” targets the parent. “One toilet closed” targets an explicit child. If no child exists, the UI must offer a parent/source-evidence report rather than pretending the user selected a unit.
7. **Corrections:** users choose parent information, unit information, or source evidence. Current correction workflow remains parent-only until the unit workflow is authorized.
8. **Favourites:** favourite the venue/parent by default. Unit favourites require a separate product decision because current `favourites` has a unique `(user_id, facility_id)` contract.
9. **Urgent journey:** nearest selection remains parent-based and fast. Child detail can be loaded after the parent is chosen; no child fan-out should block the initial nearest result.

## Part H — additive migration design (not deployed)

No migration was written or deployed in this batch. The safe design is:

### Phase 1 — capability without reinterpretation

Add a future `toilet_units` table with a non-null `facility_id` foreign key and an optional explicit unit identity/status. Add a future `toilet_unit_sources` table with a non-null `toilet_unit_id` foreign key. Keep `facility_sources` parent-only. Add public-read policies that require a published parent and governed writes for source/unit data.

Every current facility remains valid with **zero explicit child units**. Zero children means **facility with unit detail unknown**, not “the facility contains exactly one toilet”. Do not create 15,620 synthetic children.

### Phase 2 — source-only and selected providers

Allow selected providers such as TfL to populate source records. A source row may remain unattached to a canonical child while its parent or physical relationship is unresolved. A governed reconciliation process can later attach it to a child or create a child after review.

### Phase 3 — selective canonical promotion

Promote only independently supported child records. Preserve legacy parent values and field provenance. Recompute new aggregate read fields without silently changing the meaning of existing booleans. Existing facility IDs remain stable so favourites, reports, photos, access codes, exports, and deep links continue to resolve.

An optional implicit/default unit is not recommended at phase 1: it would falsely imply exactly one toilet for 15,620 legacy rows. If a compatibility layer later needs a unit-shaped API, it should expose a typed “unit detail unknown” projection rather than materializing synthetic rows.

## Part I — `facility_sources` and source integrity

`facility_sources` should remain parent-only. It has a clear `facility_id` foreign key, current-source semantics, and RLS tied to the parent’s publication status. Do not turn it into a nullable polymorphic table such as `(facility_id, toilet_unit_id)`; that weakens integrity, complicates RLS, and makes uniqueness ambiguous.

Use a separate `toilet_unit_sources` table with:

- `toilet_unit_id NOT NULL` referencing `toilet_units(id)`;
- `import_run_id` referencing `import_runs(id)` where applicable;
- `source_name`, `source_record_id`, URL, licence, timestamps, current flag, raw data;
- unique `(source_name, source_record_id)`;
- optional field-level source assertions or structured raw data; and
- no direct TfL-specific columns in the canonical unit table.

When a TfL row has a confirmed parent but no resolved physical unit, it should remain in a source-evidence/quarantine structure with strong ownership rather than being force-attached to a guessed child. The exact quarantine table and workflow need an implementation decision.

Required TfL attribution remains **Data provided by Transport for London**, with the applicable TfL transport-data terms recorded in source metadata. Do not use TfL logos or branding without separate permission.

## Part J — frozen TfL proposal impact

The following are aggregate reclassifications of the frozen package. They are not new executable operations, and overlapping populations must not be summed:

| Existing frozen item | Count | Adjudication handling |
|---|---:|---|
| Proposed `INSERT` | 58 | **SAFE_ONLY_AFTER_MODEL_CHANGE**. Do not create a parent-only facility for a row whose physical/unit relationship is unresolved. Re-evaluate as a parent plus optional child/source proposal after the additive model exists. |
| Proposed `SOURCE_LINK` | 14 | **HUMAN_PHYSICAL_UNIT_ADJUDICATION**. A stable source ID is not enough to choose a child. Preserve as source evidence until parent and unit relationship are resolved. |
| Proposed `ENRICHMENT` | 14 | **HUMAN_PHYSICAL_UNIT_ADJUDICATION**. Do not write unit attributes into parent fields. |
| Collision rows | 328 | **SOURCE_IDENTITY_ONLY / PHYSICAL_UNIT_UNRESOLVED**, across 124 existing facility candidates. Preserve evidence and review whether the candidate is the parent and whether a child is supported. |
| Unresolved positional/model rows | 338 | **PHYSICAL_UNIT_UNRESOLVED**. Quarantine or human review. All 410 rows have station-level coordinates only. |

The 328 collision rows are included in the 338 unresolved positional/model rows; the categories are not disjoint. No revised net-new facility count is asserted by this adjudication. The earlier expected net-new count of 58 is no longer safe as an approval count because it assumes the current one-row model can receive the rows.

The source identity itself remains usable for deduplicating repeated retrievals of the same TfL row. The physical-unit identity does not become known merely because that source identity is stable.

## Part K — future-source compatibility

The recommended structure is provider-neutral. It can represent:

- several toilets at one venue;
- Male/Female/Unisex and accessible provisions;
- baby-changing facilities;
- separate floors or ticket-barrier areas through unit location text and optional structured location;
- different opening/access rules;
- multiple operators through source assertions and provider-neutral operator fields only where justified;
- several providers describing one physical unit through multiple `toilet_unit_sources` rows; and
- provider rows that cannot yet be related to a physical unit through source-only/quarantine evidence.

Changing rooms and other non-toilet provisions should not be forced into `toilet_units` unless the product decides they share the same discoverability and attribute contract. A future generalized provision table may be appropriate, but it is outside this bounded decision.

## Part L — performance

The initial read path should continue to query parents for map viewport, clustering, search, and nearest-facility. This avoids multiplying map payloads by child count and preserves the urgent journey’s latency contract.

When child-aware filters are introduced, use indexed `EXISTS`/aggregate queries or a maintained parent summary rather than returning every child in every map response. Likely indexes are:

- `toilet_units(facility_id)`;
- selective child capability indexes such as `(facility_id, is_accessible)` and `(facility_id, has_baby_changing)`;
- `toilet_unit_sources(toilet_unit_id)`;
- unique `(source_name, source_record_id)`; and
- publication/status indexes aligned with parent visibility.

The nearest RPC should continue returning parent distance. A child-specific route would need an explicit product contract; station-level coordinates must not be presented as child-level navigation points.

## Part M — security and RLS

The additive tables should follow existing governance:

- public and anonymous reads only for published parents and published child/source data intended for public display;
- authenticated users may create only their own parent/unit reports or submissions, with pending-only fields;
- source and reconciliation writes are privileged import/governance operations, not client writes;
- moderation decisions derive reviewer identity from `auth.uid()` and preserve replay/ownership protections;
- unit-level source data must not expose raw moderation or operational metadata merely because a parent is public;
- account export must use explicit allowlisted reads and return only the requester’s own unit-linked contribution context; and
- no permissive service-role workaround or RLS weakening is justified by ingestion convenience.

The present moderation contract’s “reviewed record only” policy remains in force. A future unit adjudication workflow must separately decide whether it only records a review decision or is authorized to apply canonical changes.

## Unresolved decisions

These items remain explicit `DECISION_REQUIRED` before implementation:

1. Whether and how Relief defines a physical toilet unit independently of provider row identity.
2. The exact name and columns of the future child table, including unit status and confidence vocabulary.
3. Whether source-only unresolved rows need a dedicated quarantine table or can remain in an import evidence store.
4. Whether user reports and corrections may target units in the first implementation phase.
5. Whether favourites ever target units, or remain permanently parent-scoped.
6. Whether parent aggregate flags are added as new fields/read-model values or exposed only through queries.
7. The future review/rating target, because no active review table exists today.
8. The governed canonical-application policy for future source/unit adjudications.

## Validation boundary

Added deterministic pure tests cover:

- TfL identity remains `(StationUniqueId, Id)`;
- Male/Female/Unisex rows are not automatically collapsed;
- station coordinates are not promoted to toilet precision;
- a parent may have multiple source rows;
- multiple source rows do not prove multiple rooms;
- parent aggregates use explicit “at least one known” semantics without mutating child values; and
- frozen TfL reclassification has zero production mutations and no executable apply path.

No EAS, Gradle, Expo prebuild, Android, APK, migration deployment, staging write, import run, TfL proposal operation, or production mutation was performed.

## Conclusion

Relief should introduce an additive, provider-neutral toilet-unit capability while preserving the current parent facility contract. Existing facilities must remain stable and unit detail must be unknown unless supported. TfL source rows should be preserved with stable source identity and attribution, but physical-unit identity must be adjudicated separately. The 58 inserts, 14 source links, 14 enrichments, 328 collision rows, and 338 unresolved rows remain non-executable until that model and governance are separately authorized.

**Production mutations: 0.**

**RELIEF TFL REAL FEED — RECONCILED / PRODUCTION APPLY NOT AUTHORIZED**

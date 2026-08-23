# RELIEF — Net-New Toilet Source Expansion Audit

**Date:** 2026-08-23
**Scope:** bounded source discovery, licensing review, overlap estimation and net-new-yield planning
**Production writes:** none
**Final classification:** `PROCEED_WITH_SOURCE_LOCAL_AUTHORITY_OGL`

## Executive answer

The fastest credible path beyond the current 15,620 canonical facilities is a small, explicitly licensed local-authority open-data batch. It has direct toilet evidence, public machine-readable examples and a manageable adapter path. The first implementation should select two to five current, name-bearing, coordinate-bearing council resources whose individual resource terms explicitly permit reuse under OGL.

The audited Sheffield resource demonstrates the main quality gate: it contains 41 geolocated public-toilet records, but all 41 names are missing. Eighteen are within an approximate 100 m window of an existing canonical facility and 23 have no nearby canonical facility; none is safe to ingest automatically. Sheffield is therefore a quality-control sample, not a yield claim.

OSM is the largest potential opportunity, but it is not the fastest safe source: exact current OSM overlap was not measured, the existing `Toilet Map UK` provenance does not expose upstream lineage, and ODbL database/Produced Work/Derivative Database treatment needs legal and architecture review. Changing Places has excellent direct accessibility evidence and an official active count of 2,675, but a reusable bulk export/API and terms were not established. National Rail remains access-blocked.

The best conditional combined opportunity is approximately **400–900 conservative deduplicated net-new facilities**, with an upper scenario of **1,000–3,000** only after source permission, current extracts and measured overlap. This is a planning estimate, not an authorization or a measured production delta.

## Starting state and production baseline

| Item | Verified value |
|---|---|
| Repository | `hourwise/Relief` |
| Branch | `codex/toilet-map-apply-1a-production-deploy` |
| Starting local SHA | `9f053c18fa4e4d18ccc043a1d889452260092b15` |
| Starting remote SHA | `9f053c18fa4e4d18ccc043a1d889452260092b15` |
| Production project | `Relief` / `bgwxrxkmyaihplaloely` |
| Project health | `ACTIVE_HEALTHY`, `eu-central-1` |
| PostgreSQL / PostGIS / pgcrypto | `17.6.1.127` / `3.3.7` / `1.3` |
| Migration head | `20260822170000` |
| Canonical facilities | **15,620** |
| Facility sources | 15,634 |
| Facility source observations | 14 |
| Toilet units | 0 |
| NaPTAN source-graph rows | 706,745 |

The read-only production source aggregate was:

- `Toilet Map UK`: 15,620 source rows attached to 15,620 facilities;
- `TfL detailed station data � station facilities and toilets`: 14 source rows attached to 14 facilities.

This proves the current source labels, not the upstream composition of the 15,620 `Toilet Map UK` rows. It is not safe to assume that OSM, council or Changing Places records are absent from that baseline. The audit consequently uses conservative ranges rather than additive counts.

The sealed N4A migration remained byte-for-byte unchanged with SHA-256 `087A389B8CEAC021B12708BC55C39022CB38D5459510EFFB6CF057CEF232C44E`.

## Source findings

### 1. Local-authority OGL public-toilet data — recommended next source

This is the best current path. The National Data Library exposes public-toilet datasets and a common public-toilets schema. Leeds provides a direct Changing Places example explicitly licensed under OGL; Sheffield provides a current machine-readable ArcGIS example used in the committed preparation package. The GLA catalogue is useful as a discovery source, but its current page says `Licence: Not set`, so it must not be treated as automatically reusable merely because the portal states OGL by default.

Authoritative examples: [Sheffield public toilets](https://www.data.gov.uk/dataset/1e172d53-a4d2-4da3-8fe7-206537f0611d/public-toilets-sheffield), [Leeds Changing Places](https://www.data.gov.uk/dataset/1a2906ba-ecb1-4a2b-b89c-3a4b34812c4c/changing-places-toilets-in-leeds), [GLA public-toilet package](https://www.data.gov.uk/dataset/31f3a068-9505-4da2-88b3-8bfb3d53171d/public-toilets14), and the [public-toilets schema](https://schemas.opendata.esd.org.uk/publictoilets).

The Sheffield evidence is concrete but not ingestible: 41/41 records are geolocated and direct, 41/41 have missing names, 18 are near an existing facility, 23 are not near one, and exact source links are zero. That result supports a strict name/identity gate, not a 23-row automatic insert.

The OGL permits reuse subject to attribution and its terms; it has no general share-alike requirement. The individual dataset/resource must still be checked for licence, CRS, update date, stable record identity and operating status. The official OGL link is available from the data.gov.uk pages, including [Leeds’ explicit OGL entry](https://www.data.gov.uk/dataset/1a2906ba-ecb1-4a2b-b89c-3a4b34812c4c/changing-places-toilets-in-leeds).

Estimated family yield after selecting current name-bearing resources:

- `CONSERVATIVE_NET_NEW`: **100–600**;
- `UPPER_BOUND_NET_NEW`: **100–1,500**;
- value band: `MODERATE_YIELD`;
- engineering effort: **medium**;
- likely time-to-toilets: **2–6 weeks** for a bounded multi-council source batch after source selection.

These are conditional programme estimates. The verified Sheffield sample contributes **zero ready-to-ingest records** until its names/identity evidence are repaired or replaced.

### 2. OpenStreetMap `amenity=toilets` — high potential, legal gate required

OSM is direct toilet evidence when the feature is tagged as a toilet, and the tag documentation distinguishes public toilet features from entrances/areas. See the [amenity=toilets definition](https://wiki.openstreetmap.org/wiki/Tag%3Aamenity%3Dtoilets). A third-party composite currently reports 19,514 publicly accessible facilities, but that figure combines OSM, the Great British Public Toilet Map and community reports; it is not an authoritative OSM count and is not used as a production count.

Exact OSM overlap was not measured. The current production provenance only says `Toilet Map UK`, so it cannot prove whether OSM records are already embedded. A content-addressed extract and stable OSM identifiers are required before claiming a precise net-new number.

The [OSMF legal FAQ](https://osmfoundation.org/wiki/Licence/Licence_and_Legal_FAQ) describes ODbL attribution and share-alike obligations for OSM data and derivative databases, and distinguishes them from Produced Works. The [Produced Work guideline](https://osmfoundation.org/wiki/Licence/Community_Guidelines/Produced_Work_-_Guideline) makes clear that the classification depends on what is distributed and whether substantial data is extractable. Relief should obtain legal review of the proposed database/source separation before retaining a broad OSM-derived table in its own database.

Estimated opportunity:

- `CONSERVATIVE_NET_NEW`: **300–800**;
- `UPPER_BOUND_NET_NEW`: **800–2,500**;
- value band: `HIGH_YIELD`;
- engineering effort: **high**;
- status: `HIGH_VALUE_SOURCE` with `LEGAL_REVIEW_REQUIRED` / `BLOCKED_BY_LICENSING` for production ingestion.

OSM is not the recommended immediate source despite its potential scale.

### 3. Changing Places — high product value, bulk-reuse permission required

The official Changing Places map displays **2,675 active registered facilities** at the time of this audit. These are direct accessibility/toilet records, not inferences from venues or transport places. See the [official active register](https://www.changing-places.org/find?toilet=695). A small Leeds dataset is available under OGL, but it is historical and not a national feed.

The public map and terms pages did not establish a permissioned bulk export/API with stable identifiers or clear redistribution terms. Scraping is not an acceptable substitute. Exact overlap with the 15,620 baseline is therefore unknown and likely substantial.

Estimated opportunity:

- `CONSERVATIVE_NET_NEW`: **150–500**;
- `UPPER_BOUND_NET_NEW`: **500–1,000**;
- value band: `MODERATE_YIELD`, with very high accessibility value;
- engineering effort: **medium**;
- status: `BLOCKED_BY_LICENSING` until written bulk-reuse permission and a stable export/API are obtained.

### 4. TfL detailed station toilet feed — real direct evidence, bounded net-new yield

The committed TfL package contains 509 stations and 410 toilet rows, all with usable station coordinates. It also records 147 stations with multiple toilet rows. The previous read-only reconciliation found 305 high-confidence existing matches, 33 review matches, 14 quarantined rows and 58 distinct-new candidates. Exact TfL source-ID matches were zero. Station-level coordinates are not toilet-unit coordinates, so the 58 are proposals, not automatic new facilities.

The [TfL Transport Data Service terms](https://tfl.gov.uk/corporate/terms-and-conditions/transport-data-service) permit copying, publishing, distributing, adapting and commercial/non-commercial use subject to attribution, non-endorsement, registration and rate-limit requirements. Required attribution includes `Powered by TfL Open Data` and the applicable OS/Geomni attribution.

Estimated opportunity:

- `CONSERVATIVE_NET_NEW`: **0–20**;
- `UPPER_BOUND_NET_NEW`: **20–58**;
- value band: `LOW_YIELD`;
- engineering effort: **medium**;
- status: direct feed available, but physical-unit/facility-model review is required.

TfL is a useful small follow-up, not the primary route beyond 15,620.

### 5. National Rail / RDG — direct schema evidence, currently access-blocked

The public Stations V4 XML schema contains a `Toilets` availability field and location note, plus `NationalKeyToilets` fields. See the [Stations XML feed schema](https://assets.nationalrail.co.uk/e8xgegruud3g/oYB6snjp0EEEgtgH2d8i3/9fac3cba35e848b2c857307ddf6efaf7/Stations-40_XML_Feed_v2_Open.pdf). The current Knowledgebase station-facilities feed requires registered access; no current row count or reuse terms were available in this audit.

Classification: `BLOCKED_BY_ACCESS`. Current conservative net-new is **0**; an upper planning scenario of **0–150** is not a measured result and must not be used to justify ingestion before access and terms are obtained.

### 6. Toilet Map UK — existing baseline, not an expansion source

The current production set is already attributed to `Toilet Map UK` for all 15,620 canonical facilities. Its current public dataset is CC BY 4.0 and permits copying, adaptation and commercial use with attribution and a change notice; see [Toilet Map dataset terms](https://www.toiletmap.org.uk/dataset). A refresh may improve freshness but has no defensible net-new yield without a new content-addressed export and exact join.

Classification: `ZERO_OR_NEGLIGIBLE_YIELD`; conservative net-new **0**.

### Other credible sources

DataMapWales’ National Toilet Map is a potential direct source, but the layer metadata identifies PSGA; reuse and republishing permission must be confirmed. Scotland and Northern Ireland were not selected because a current coordinate-bearing facility feed with explicit terms was not verified. These remain `BLOCKED_BY_LICENSING` or `BLOCKED_BY_ACCESS`, not yield opportunities for the next batch.

## Ranked source table

| Rank | Source | Direct toilet records | Likely existing | Conservative net-new | Yield band | Licence/access | Effort | Recommendation |
|---:|---|---:|---|---:|---|---|---|---|
| 1 | Local-authority OGL batch | 41 verified Sheffield sample; national count not verified | 18/41 Sheffield within approx. 100 m; national unknown | **100–600 conditional** | MODERATE_YIELD | OGL only where explicit; per-resource gate | Medium | **Next source** |
| 2 | OSM `amenity=toilets` | Current exact count not extracted; 19,514 third-party composite indicator | Unknown; likely substantial overlap | **300–800 estimate** | HIGH_YIELD | ODbL legal/architecture review | High | Later, after legal gate |
| 3 | Changing Places | **2,675 active registered** | Unknown; likely substantial overlap | **150–500 estimate** | MODERATE_YIELD | Bulk reuse/API permission absent | Medium | Request permission |
| 4 | TfL detailed feed | **410 rows** | 305 high-confidence existing; 58 distinct-new proposals | **0–20** | LOW_YIELD | Current TfL terms | Medium | Small follow-up only |
| 5 | National Rail/RDG | Current count not retrieved | Unknown | **0** | ZERO_OR_NEGLIGIBLE_YIELD | Registered access/terms required | Medium | Wait for access |
| 6 | Toilet Map UK refresh | **15,620 current production rows** | **15,620** | **0** | ZERO_OR_NEGLIGIBLE_YIELD | CC BY 4.0 | Low | Baseline maintenance only |

## Growth targets

| Target | Additional toilets required | Best path | Plausible? |
|---:|---:|---|---|
| 16,000 | 380 | Name-bearing OGL council cluster, with the small TfL candidate set reviewed separately | **YES**, conditional on source quality |
| 17,000 | 1,380 | OGL council programme plus legally cleared OSM and/or permissioned Changing Places | **YES**, programme-scale only |
| 20,000 | 4,380 | National multi-source programme including councils, OSM, Changing Places and permissioned transport feeds | **NO** for the next bounded batch; not currently evidenced |

The best conditional combined range is **400–900** conservative deduplicated net-new facilities, implying an estimated post-batch baseline of **16,020–16,520**. This is not the expected outcome of the next implementation batch; it is the combined opportunity if the legal/access gates clear and the overlap joins support it. For the recommended OGL path alone, the conditional planning baseline is **15,720–16,220**.

## Licensing and overlap conclusions

1. The current provenance surface is insufficient to decompose the 15,620 `Toilet Map UK` set into OSM, council, community or Changing Places components. Exact net-new counts require source snapshots and stable source IDs.
2. OGL council records are the clearest legal path, but “OGL by default” on a catalogue page is not enough when an individual resource says licence not set.
3. OSM is not rejected on yield; it is deferred pending legal review of ODbL attribution, share-alike, Produced Work and Derivative/Collective Database treatment. Any future design must keep source separation and attribution explicit.
4. Changing Places is high-value direct evidence, but public map visibility does not establish bulk-reuse rights.
5. National Rail station identity and facility fields are useful, but registered access and reuse terms are prerequisites.
6. A nearby point, a transport station, a venue, a source name or a generic directory row is not enough to create a Relief toilet facility. Direct toilet evidence and conservative identity/deduplication remain required.

## Smallest next implementation batch

The next batch should be a read-only source acquisition and exact-overlap preparation for **two to five current local-authority datasets with explicit OGL, WGS84 coordinates, names, stable record IDs and operating-status fields**. It should:

- content-address each raw source outside Git;
- preserve licence/attribution and retrieval metadata;
- normalize with unknowns retained as null;
- reject missing names/CRS/identity rather than inventing values;
- compare against the 15,620 canonical facilities using source identity first, then conservative name/address/postcode/coordinate evidence;
- output an exact candidate/net-new range;
- stop before production DML.

No migration, schema change, ingestion, canonical promotion or provenance write is part of this recommendation.

## Production safety

This audit used read-only production metadata and aggregate SQL only.

- `TOTAL PRODUCTION MUTATIONS: 0`
- `TOTAL CANONICAL FACILITY MUTATIONS: 0`
- `TOTAL SOURCE-GRAPH MUTATIONS: 0`
- `TOTAL AUTH MUTATIONS: 0`
- `TOTAL SCHEMA MUTATIONS: 0`
- migration-ledger mutations: `0`
- NaPTAN promotion: not performed;
- N6D/N6E/mass transport promotion: not performed;
- raw national XML or other large source snapshots: not committed.

## Validation and files

The machine-readable companion is [`NET_NEW_TOILET_SOURCE_EXPANSION_AUDIT_2026-08-23.json`](NET_NEW_TOILET_SOURCE_EXPANSION_AUDIT_2026-08-23.json). It records the production baseline, source ranges, licensing gates, growth targets, and mutation counter.

Validation completed:

- exact local/remote checkpoint verification;
- protected-file inventory;
- sealed N4A hash verification;
- read-only Supabase project, migration and extension checks;
- read-only canonical/source-graph aggregate checks;
- reuse of committed Sheffield/TfL source hashes and overlap evidence;
- deterministic fixed-range analysis with no random sample;
- JSON parse and structural validation;
- `git diff --check`;
- bounded secret scan;
- no EAS, Expo, Gradle, APK or emulator work.

## Final classification

`PROCEED_WITH_SOURCE_LOCAL_AUTHORITY_OGL`

**CURRENT TOILET BASELINE:** 15,620
**BEST CONSERVATIVE NET-NEW OPPORTUNITY:** 100–600 conditional from a selected local-authority OGL family; 400–900 for a later cleared combined programme
**EXPECTED POST-INGESTION BASELINE:** 15,720–16,220 for the recommended OGL path; 16,020–16,520 for the conditional combined opportunity
**TOTAL PRODUCTION MUTATIONS: 0**

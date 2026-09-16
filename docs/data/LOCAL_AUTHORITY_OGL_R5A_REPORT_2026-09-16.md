# Relief R5A — bounded council expansion and secondary source feasibility

Date: 2026-09-16
Repository: `hourwise/Relief`
Branch: `codex/toilet-map-apply-1a-production-deploy`
Publication checkpoint: `e0393666b70ca4b93586b744c71aea95d9b0d5a9`

## Scope and safety

This was a discovery, source-acquisition, normalization and read-only production-comparison pass. No production INSERT, UPDATE, DELETE, DDL, migration, provenance write, source-graph write, or import-run write was performed. The production project was verified as Relief (`bgwxrxkmyaihplaloely`), ACTIVE_HEALTHY, PostgreSQL 17.6.1.127, PostGIS 3.3.7, pgcrypto 1.3. The live baseline was facilities 15,709, facility_sources 15,723, observations 14, import_runs 6, toilet_units 0 and toilet_unit_sources 0; the NaPTAN graph remained 706,745 rows.

The sealed N4A migration remained byte-for-byte unchanged at SHA-256 `087A389B8CEAC021B12708BC55C39022CB38D5459510EFFB6CF057CEF232C44E`.

The committed R4C evidence was checked before comparison. Its 89-row apply is already represented in the current live counts; its audit migration is the current post-N4A migration head. Historical R4C evidence was not rewritten.

## Council sweep

The strongest current machine-readable council sources are:

| Council | Source facts | Read-only comparison | R5A result |
|---|---:|---:|---|
| Mid Ulster | 27 named GeoJSON records, 27 valid geometries, 27 postcodes, stable OBJECTID | 17 beyond 250m; 10 within 250m | 17 `READY_NET_NEW` preparation candidates |
| Dover | 17 named CSV records, 17 UPRNs, 16 postcodes, 17 valid geometries | 6 beyond 250m; 11 within 250m | 6 `READY_NET_NEW` preparation candidates |
| Calderdale | 15 valid direct records, no stable IDs/postcodes | 6 beyond 250m, but identity is weak | 15 review; 1 malformed source row rejected |
| Sheffield | 41 geometries but no names in current payload | not safe to identify | 41 rejected for source quality |
| Rother | 15 current HTML locations | no machine IDs/coordinates | 15 review |
| North Somerset | 22 directory results | no verified structured feed | 22 review |
| Belfast | 14 current HTML locations; historical OGL resource | R4 found existing/review overlap, not strict net-new | 14 review/context; no new strict candidates |

The exact bounded preparation count is **23**: 17 Mid Ulster plus 6 Dover. This is not a production-ready sealed manifest and is not an authorization to insert. The next implementation slice should re-fetch/validate those two already-structured OGL resources, build a new versioned manifest, and perform one more complete source-identity/current-production collision gate.

The source-level hashes and detailed record metrics are in `LOCAL_AUTHORITY_OGL_R5A_SOURCE_ASSESSMENT_2026-09-16.json`; the comparison counts are in `LOCAL_AUTHORITY_OGL_R5A_PRODUCTION_COMPARISON_2026-09-16.json`.

### Council conclusions

- Mid Ulster and Dover are the only investigated council families that passed the bounded machine-readability, direct-toilet, identity and geometry gates.
- Calderdale has useful direct toilet and accessibility fields, including one Changing Places record, but no stable publisher identity/postcode in the acquired export; it belongs in a later review or source-rebinding pass.
- Sheffield's current API response still has the historical missing-name defect. Coordinates cannot be used to manufacture facility names.
- Rother, North Somerset and Belfast provide useful human-readable evidence, but the bounded pass did not establish a current structured resource suitable for automatic comparison. Belfast's former R4 overlap/review cases were not reopened.

## Heritage and Wikidata feasibility

Wikidata structured data in the relevant entity/property namespaces is CC0. A bounded UK query using `P912 (has facility)`, explicit toilet-related facility labels and coordinates returned 2,906 bindings representing 1,258 unique items after item-level deduplication. The result was dominated by `accessible toilet` statements (1,209 unique items) and also included `Changing Places toilet` (141 unique items), `public toilet` (30 unique items) and ordinary `toilet` statements (6 unique items); these categories overlap by item and must not be summed.

All 1,258 queried items had a coordinate, but the query did not establish toilet-specific coordinate precision, current access scope, or a lawful production source-record contract beyond CC0 statement reuse. A deterministic 100-item sample was compared read-only against the current 15,709 facilities: 4 were within 25m, 16 within 100m, 33 within 250m, and 47 beyond 250m; median nearest-facility distance was 241.6m and p95 was 5,952.0m. This is a venue-level feasibility sample, not a national net-new count.

Accordingly, the current Wikidata result is:

- direct structured evidence: useful;
- lawful statement reuse: CC0;
- measured unique cohort: 1,258 items;
- production-ready heritage candidates: **0** in this pass;
- coarse/location/access review: 1,258-item bounded opportunity cohort;
- production action: a separate precision/access review, not ingestion.

VocalEyes Heritage Access 2022 is valuable evidence that accessibility and toilet information exists at substantial scale (the published project describes 1,883 museum/heritage sites), and the Wikidata contribution is the most reusable projection found. No raw structured database licence/download suitable for direct Relief ingestion was established, so the raw survey is `PERMISSION_REQUIRED`.

Historic England's NHLE is an OGL identity/geometry backbone, not a toilet dataset. National Trust and English Heritage visibly publish site facilities, but no open reusable facility feed was established in this bounded pass; both are high-value partnership/permission routes, not scrape targets.

## Motorway-service feasibility

National Highways publishes access-guide links and general motorway-service requirements, and those requirements include toilets and disabled access. However, the bounded investigation did not find an explicit, reusable, facility-level service-area dataset with stable identifiers, coordinates and direct toilet records. AccessAble is the detailed guide route but is not an open Relief ingestion source. The previously identified non-exhaustive dataset was not used.

Result: `PERMISSION_REQUIRED` / no safe open cohort. No motorway records were counted as ready and no production comparison was attempted beyond this source/contract gate.

## National retail and commercial venue feasibility

At metadata/sample level, Tesco and Asda locators expose per-site fields including accessible toilets, baby changing and Changing Places; Sainsbury's sample location pages expose toilets, accessible toilets and baby change; IKEA publishes store-level accessibility guidance and identifies a small set of registered Changing Places stores; M&S, John Lewis and Lidl samples expose store toilets/accessibility or customer-toilet fields. These are useful signals, but no open downloadable facility feed or reuse licence was established in this pass. The access semantics are generally customer/visitor-facing rather than public-without-purchase.

Therefore no commercial operator contributes to the council `READY_NET_NEW` total and no nationwide commercial comparison was run. The three best future data-partnership targets are:

1. Tesco — broad UK footprint and rich per-site amenity vocabulary;
2. Asda — broad footprint and similar accessible/baby/Changing Places fields;
3. Sainsbury's — clear per-store facility fields and a tractable store-level partnership request.

IKEA is a strong specialist alternative if the product prioritises high-quality accessibility/Changing Places evidence over raw site count. The minimum partnership export should request a stable branch ID, name, address/postcode, latitude/longitude, ordinary/accessibility/Changing Places/baby-changing flags, store and facility opening hours, access restrictions and last-updated timestamp, with explicit reuse terms and attribution.

### Expanded hospitality and premises track

The extension covered fast food, coffee/café, pub/restaurant and casual-dining families at official metadata/sample level. The strongest direct evidence was:

- McDonald's: official help material says the restaurant locator identifies disabled toilets and wheelchair access; restaurant guidance mentions baby-changing facilities. The published material confirms more than 600 restaurants open 24 hours, but not a total UK estate. [McDonald's accessibility FAQ](https://www.mcdonalds.com/gb/en-gb/help/faq/do-you-have-disabled-toilets.html)
- KFC: official regional pages state that some restaurants have toilets, and location pages expose baby changing, disability access, address and opening hours. [KFC regional locator](https://www.kfc.co.uk/kfc-near-me/london)
- Harvester/Mitchells & Butlers: sample official pages expose `Disabled Toilets`, `Baby Changing`, address, hours and a stable restaurant slug. [Harvester sample location](https://www.harvester.co.uk/restaurants/london/themandevillearmsnortholt)
- ODEON: the operator states that AccessAble guides are produced for all ODEON cinemas and contain factual accessibility information, including toilets. [ODEON AccessAble guidance](https://help.odeon.co.uk/hc/en-gb/articles/360010323759-Who-are-AccessAble)

For other chains, a location system or dining venue was not treated as toilet evidence. No hospitality premises were counted as ready. Access is conservatively `customer_only`, `patrons_only` or `unknown`; no restaurant was treated as `public_without_purchase`.

### Destination venues and centres

The destination-venue track is more promising than individual tenants because a single agreement can describe common washrooms. Westfield publishes accessible-toilet/RADAR and hoist/changing-table location information; Landsec centre maps expose toilets, accessible toilets, Changing Places, baby changing and stoma-friendly facilities; McArthurGlen outlet pages expose toilets, Changing Places, baby changing and AccessAble links. These are `PERMISSION_REQUIRED` and generally `WASHROOM_BLOCK_LOCATION` or centre-level evidence, not automatic Relief facility points. [Westfield](https://www.westfield.com/en/united-kingdom/london/services/accessible-toilets), [Landsec centre map](https://content.landsec.com/media/nmobhrc2/65412-land-sec-large-print-guide-ss25_v4.pdf), [McArthurGlen](https://www.mcarthurglen.com/en/outlets/uk/designer-outlet-ashford/services/)

The best retail-centre/outlet partnership targets are McArthurGlen, Landsec and Westfield. Clarks Village is a useful bounded centre pilot. Bicester Village and other listed outlet families remain permission-gated because no reusable structured facility feed was established.

### Commercial data-reuse result

No commercial operator currently qualifies as `OPEN_REUSABLE_DATA` or `PUBLIC_API_REUSE_PERMITTED` on this evidence pass. The commercial `READY_NET_NEW` count is **0**, and no commercial records were compared nationally with Relief. The common partnership request must include stable site identity, coordinates, toilet/accessibility/Changing Places/baby-changing/RADAR/stoma flags, access scope, store and toilet opening hours, verification timestamps, and explicit reuse rights.

The commercial planning score is a 1–5 assessment across scale, apparent toilet coverage, richness, likely uniqueness and permission ease. It is not a count or authorization. The leading hospitality targets are McDonald's, Harvester/Mitchells & Butlers, KFC and ODEON; the leading destination targets are McArthurGlen, Landsec and Westfield. The full scorecard is in `COMMERCIAL_VENUE_TOILET_FEASIBILITY_2026-09-16.json`.

## Final source-ranking table

| Source/family | Classification | Direct toilet evidence | Reusable scale measured | Ready count | Next action |
|---|---|---:|---:|---:|---|
| Mid Ulster OGL | `READY_FOR_NEXT_INGEST_BATCH` | direct fields | 27 | 17 | prepare bounded manifest |
| Dover OGL | `READY_FOR_NEXT_INGEST_BATCH` | direct fields | 17 | 6 | prepare bounded manifest |
| Calderdale OGL | `REVIEW_REQUIRED` | direct fields | 15 valid | 0 | obtain stable identity/review |
| Sheffield OGL | `ZERO_OR_NEGLIGIBLE_YIELD` | current payload incomplete | 41 geometries | 0 | wait for named export |
| Rother | `REVIEW_REQUIRED` | HTML listing | 15 | 0 | request structured export |
| North Somerset | `REVIEW_REQUIRED` | directory listing | 22 | 0 | bind resource-level feed |
| Belfast | `REVIEW_REQUIRED` | HTML/current + historical OGL | 14 | 0 | do not reopen R4 overlap |
| Wikidata P912 | `DIRECT_EVIDENCE_LOCATION_COARSE` | explicit statements | 1,258 unique items | 0 | precision/access review |
| VocalEyes raw survey | `PERMISSION_REQUIRED` | reported survey fields | 1,883 sites reported | 0 | seek dataset permission |
| Historic England NHLE | `OPEN_IDENTITY_BACKBONE_ONLY` | none | national heritage identity | 0 | identity join only |
| National Trust / English Heritage | `PERMISSION_REQUIRED` | visible site facilities | not safely counted | 0 | partnership request |
| Motorway services | `PERMISSION_REQUIRED` | general/service-guide evidence | no lawful structured cohort | 0 | request licensed export |
| Hospitality premises | `PERMISSION_REQUIRED` | direct sample fields | not safely counted | 0 | partnership requests |
| Shopping centres/outlets | `PERMISSION_REQUIRED` | washroom/block-level samples | not safely counted | 0 | partnership requests |
| Leisure chains | `PERMISSION_REQUIRED` or `NO_STRUCTURED_FACILITY_DATA` | ODEON/AccessAble and limited samples | not safely counted | 0 | partnership requests |

## Validation and safety

- R4C committed evidence checked; live counts are 15,709 facilities and 15,723 facility_sources.
- N4A sealed migration hash checked before and after analysis.
- Council files were acquired only from identified official resources; no raw downloads were added to Git.
- Wikidata was queried through its public SPARQL endpoint; only compact hash/metrics were retained.
- No prohibited commercial bulk crawl or undocumented API extraction was performed.
- Hospitality, destination-centre and leisure pages were inspected only at metadata/sample level; no commercial dataset was copied or committed.
- No production DML or DDL occurred: `TOTAL PRODUCTION MUTATIONS: 0`.
- Source-graph RLS remained enabled with no policies and no public/anon/authenticated insert privileges.

## Single next slice

Prepare a new versioned production-manifest candidate for the **23 Mid Ulster/Dover records only**, including exact source hashes, stable source identities, licence/attribution, current collision checks and a dry-run report. Keep heritage, motorway and commercial work separate until a lawful structured source and location/access contract are established. The commercial follow-up should be three targeted permission requests rather than a crawl.

**Final classification: `R5A_COUNCIL_NEXT_BATCH_IDENTIFIED / HERITAGE_AND_MOTORWAY_FEASIBILITY_NOT_PRODUCTION_READY / COMMERCIAL_DATA_PARTNERSHIP_REQUIRED / PRODUCTION_UNCHANGED`**

**TOTAL PRODUCTION MUTATIONS: 0**

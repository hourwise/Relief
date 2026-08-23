# RELIEF — Local Authority OGL Pilot 1
## Source selection, deterministic normalization and net-new toilet candidate proof

**Date:** 2026-08-23  
**Classification:** LOCAL_AUTHORITY_OGL_PILOT_1 — PRODUCTION_READ_ONLY / INGESTION_NOT_AUTHORIZED

## Outcome

Two current, machine-readable, resource-level OGL sources were selected and normalized: City of York Council (18 records, including 11 Public toilets and 7 Changing Places) and Causeway Coast and Glens / OpenDataNI (52 Public toilets). The complete pilot contains **70 direct toilet records**.

A bounded read-only comparison against the Relief production facilities table classified **59** records as likely existing/duplicate and **11** as broad possible net-new candidates. Applying the stricter “no nearest existing facility within 250 m” gate leaves **9 CONSERVATIVE_NET_NEW candidates**. The two broad candidates inside 250 m are retained as near-overlap review cases. These are analytical candidates only; no production DML was executed or authorized.

The result is a small proof set, not evidence for building a national council ingestion framework or for automatically inserting records. The 9 strict candidates are suitable for a separately authorized, human-reviewed source/identity follow-up after normal TLS retrieval is restored.

## Starting and safety state

- Repository: hourwise/Relief
- Branch: codex/toilet-map-apply-1a-production-deploy
- Starting checkpoint: 513772892265e0d80619813b58e7944739d57a21 locally and remotely.
- Production target read-only: Relief / bgwxrxkmyaihplaloely / ACTIVE_HEALTHY / eu-central-1.
- Production baseline verified: facilities 15,620; facility_sources 15,634; facility_source_observations 14; toilet_units 0; source graph total 706,745.
- Production mutations: **0**.
- The protected .easignore, app.json, and docs/EAS_CONFIG_AUDIT.md, plus pre-existing N4/N5/N6 evidence/tooling, were not modified or staged.

## Selected resources

| Source | Evidence | Retrieved bytes / SHA-256 | Records |
|---|---|---:|---:|
| City of York Council | [catalogue](https://www.data.gov.uk/dataset/e49697a4-da67-429a-ac02-2a3d32023a12/public-toilets) · [ArcGIS layer](https://maps.york.gov.uk/arcgis/rest/services/Public/LV_TranStreetCare/MapServer/0) | 6,495 / 1da412b6731b8c07ced75a663098d9dee55cba4747503399b588572c2c4b5b12 | 18 (11 Public toilets; 7 Changing Places) |
| Causeway Coast and Glens / OpenDataNI | [catalogue](https://www.data.gov.uk/dataset/62eab2d2-2627-4616-8f12-412b48c80e35/public-toilet-locations-in-causeway-coast-and-glens11) · [ArcGIS layer](https://services.arcgis.com/kNPftFdcdm7bfDuO/arcgis/rest/services/Public_Toilets_CCGBC/FeatureServer/0) | 33,341 / 50eabf55fa58be22bcd09d1f9d0d94a61b17278e7f3434ad832b4df9cb884279 | 52 Public toilets |

Both resources have resource-level OGL evidence, with the [Open Government Licence v3.0](https://www.nationalarchives.gov.uk/doc/open-government-licence/version/3/) retained in the manifest. Required attribution: “Contains public sector information licensed under the Open Government Licence v3.0.” The council Changing Places rows were retained as part of the council source; no separate national Changing Places scrape was performed.

**Retrieval caveat:** ordinary local Windows HTTPS validation failed for the ArcGIS hostnames with a certificate-name error. For this disposable, read-only proof, the exact bytes were captured from the official HTTPS resource URLs with certificate verification disabled. This is a validation caveat, not an ingestion authorization; any future production ingestion must re-fetch and verify under normal certificate validation.

## Normalization contract

The adapter is tools/source_expansion/local_authority_ogl_pilot.py, version relief.local-authority-ogl-pilot-1.v1. It preserves source names, addresses, postcodes, WGS84 point coordinates, direct toilet type, accessibility/opening/payment metadata where supplied, operator, update value where supplied, per-record source fingerprint, licence and attribution. Name and postcode normalizations are comparison-only fields. Missing/invalid identity or geometry is fail-closed.

The adapter has PRODUCTION_WRITE_CAPABILITY = False, no database client, and no apply mode. The complete normalized records are bounded in LOCAL_AUTHORITY_OGL_PILOT_1_NORMALIZED_RECORDS_2026-08-23.json; source fingerprints are in the source manifest.

## Read-only comparison contract

The production query used facilities.location nearest-neighbour ordering, then applied deterministic guards:

1. exact normalized postcode; or
2. distance <= 100 m; or
3. source-name token subset within 250 m.

A record outside those guards is a broad possible net-new candidate. CONSERVATIVE_NET_NEW additionally requires the nearest canonical facility to be more than 250 m away. This is a candidate proof, not proof of an insert: a near facility can be a duplicate, and a distant record can still require identity review.

| Source | Total | Likely existing/duplicate | Broad possible net-new | Conservative net-new |
|---|---:|---:|---:|---:|
| Causeway Coast and Glens | 52 | 46 | 6 | 5 |
| City of York | 18 | 13 | 5 | 4 |
| **Total** | **70** | **59** | **11** | **9** |

### Broad candidate list

| Source | Source name | Postcode | Nearest canonical name | Distance (m) | Strict candidate |
|---|---|---|---|---:|:---:|
| Causeway | Flowerfield | BT55 7HU | Tesco Portstewart Toilets | 339.2 | yes |
| Causeway | Rasharkin Cemetery | BT44 8SD | Rasharkin, Bridge Street Public Toilet | 837.2 | yes |
| Causeway | Recreation Grounds | BT56 8BE | Landsdowne Public Toilets | 104.8 | no |
| Causeway | Portstewart Crescent | BT55 7AB | Atlantic Circle, Harbour Road | 563.5 | yes |
| Causeway | Dunluce Car Park | BT56 8DW | Portrush East Strand | 250.1 | yes |
| Causeway | Town Hall | BT55 7AG | Atlantic Circle, Harbour Road | 503.6 | yes |
| York | Front Street | YO24 3BZ | Unnamed Toilet | 1,098.1 | yes |
| York | Energise Leisure Centre | YO24 3DX | Unnamed Toilet | 1,163.7 | yes |
| York | McArthurGlen Designer Outlet York | YO19 4TA | Unnamed Toilet | 2,053.6 | yes |
| York | York Leisure Centre | YO32 9AF | Unnamed Toilet | 209.4 | no |
| York | New Earswick Folk Hall | YO32 4AQ | Unnamed Toilet | 1,569.7 | yes |

Recreation Grounds and York Leisure Centre are broad candidates but are excluded from the strict count because an existing canonical facility is within 250 m. Kinbane Castle is treated as existing/duplicate by the token-subset guard at 105.9 m, illustrating why distance alone is insufficient.

## Source exclusions

The pilot did not pad the selected set with weaker sources. Calderdale was excluded because licence/resource release was not proven; Sheffield was excluded from this pilot because the earlier 41-row review found all names missing; Bristol had non-OGL/constraint ambiguity; Hounslow’s available resource was historical (2015); Rother’s current machine-readable resource was not proven; North Somerset exposed a dashboard rather than a suitable released resource; GLA lacked a proven licence. National Changing Places data was not separately scraped.

## ROI and product conclusion

The pilot proves **70** clean direct source records but only **9** strict possible net-new records after the conservative duplicate guard. This is materially below the prior conditional 100–600 programme estimate and does not justify a national ingestion framework or automatic production DML. The appropriate next step, if desired, is a small separately authorized review of the 9 strict candidates, with the 2 near-overlap records retained as review context, not ingestion of all 70.

No council record is automatically safe to insert solely because it is licensed, named, geolocated, or distant from the nearest current facility. Direct source evidence supports later review; canonical creation requires the product/source governance boundary to be satisfied.

## Validation and evidence

- Source byte size/SHA gates: verified for both disposable resources.
- Feature counts: 18 + 52 = 70.
- Direct toilet evidence: 70/70; normalization errors: 0/70.
- Production comparison coverage: 70/70 records represented in the read-only query.
- Broad classification: 59 + 11 = 70.
- Conservative classification: 9; two broad candidates excluded by the 250 m gate.
- Production baseline after analysis: unchanged by read-only policy; no post-write DML occurred.
- Raw GeoJSON was not copied into the repository and is not staged.

## Final classification

LOCAL_AUTHORITY_OGL_PILOT_1 — PRODUCTION_READ_ONLY / 2 SOURCES VERIFIED / 70 DIRECT TOILET RECORDS NORMALIZED / 9 CONSERVATIVE_NET_NEW_CANDIDATES / INGESTION_NOT_AUTHORIZED

**TOTAL PRODUCTION MUTATIONS: 0**

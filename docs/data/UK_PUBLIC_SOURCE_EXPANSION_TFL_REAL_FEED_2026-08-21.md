# TfL detailed station-data package — frozen preparation

**PROPOSED / PRODUCTION EXECUTION NOT AUTHORIZED**
**Final classification:** `RELIEF TFL REAL FEED — RECONCILED / PRODUCTION APPLY NOT AUTHORIZED`

This package is preparation/evidence only. It contains no Supabase write, staging insert, import-run creation, canonical update, source-link mutation, deployment, EAS, Gradle, prebuild, or APK build.

The row-level JSON evidence is [`UK_PUBLIC_SOURCE_EXPANSION_TFL_REAL_FEED_2026-08-21.json`](UK_PUBLIC_SOURCE_EXPANSION_TFL_REAL_FEED_2026-08-21.json).

## Source provenance

| Item | Recorded value |
|---|---|
| Source URL | `https://api.tfl.gov.uk/stationdata/tfl-stationdata-detailed.zip` |
| Retrieval UTC | `2026-08-21T06:08:20.1476469Z` |
| ZIP byte size | `186,973` |
| ZIP SHA-256 | `19c50772febd1a3d7625f59e079b7590c5da4ed70424d6f552cfd7db1611e2ce` |
| Feed publisher | Transport for London |
| Feed start date | `2026-08-03T09:14+00:00` |
| Required Relief attribution | `Data provided by Transport for London` |
| TfL Transport Data Service attribution | `Powered by TfL Open Data` |
| Terms | [TfL Transport Data Service terms](https://tfl.gov.uk/corporate/terms-and-conditions/transport-data-service) |
| Official source page | [TfL open data](https://tfl.gov.uk/info-for/open-data-users/our-open-data) |

The applicable TfL terms are based on OGL 2.0 with TfL amendments. They permit copying, publishing, distribution, transmission, adaptation, and commercial/non-commercial exploitation subject to the licence conditions, including attribution, protection of TfL intellectual-property/branding rights, non-endorsement, accurate registration information, and a maximum of 500 calls per minute per feed. The terms may be revised and do not transfer intellectual-property rights. Where OS-derived data is included, retain the applicable OS/Geomni attribution recorded in the JSON evidence. Relief must not use TfL branding or imply TfL endorsement.

No API key was requested, printed, committed, or included in the evidence: the specified detailed ZIP endpoint returned the package without a key.

## ZIP inventory

All 11 ZIP entries were inspected. The archive and each extracted file were SHA-256 hashed.

| File | Rows | Uncompressed bytes | SHA-256 |
|---|---:|---:|---|
| `FeedInfo.csv` | 1 | 126 | `e49a244cccd20b07877920404b85966a890a30e3a1baf949772c1eaa5b68200e` |
| `Lifts.csv` | 569 | 60,132 | `b2963217674b63b0ffa467107b9fe30b53c78fa887ceefedb29f293aabacbf65` |
| `ModesAndLines.csv` | 23 | 441 | `3e6886e3f0e4fdc28207faf4f23ca39eb47ced03c246f05468677249ccf94551` |
| `PlatformServices.csv` | 1,878 | 194,161 | `bfda219f9eb1460c51fdbf7c881397d17dfdf7b03e51564db6cd8ff7b7964ae3` |
| `Platforms.csv` | 1,584 | 161,194 | `ccf6b4bb64e43a33c71f9c5d5efbc5cdb5220e54e78835a5afeebb7728783e99` |
| `RampRoutes.csv` | 418 | 21,967 | `fb20afe1c3f3ff4644b8e8ba0db06b0333dd5b64e4fa77429a04e609044d8ab5` |
| `SameLevelPaths.csv` | 8,176 | 446,706 | `a896d98cc3ea684a741ce1a73a9b6d9c93c28c18b397e487a44b89ebbbfef520` |
| `StationPoints.csv` | 4,084 | 293,096 | `c6743bda0901f2f2b7799adf21a6a937424f47a918753bb3d2f1e03e3bcde05f` |
| `Stations.csv` | 509 | 37,833 | `17a50c77798410cce109e5f8e0dd48c4079192f0c38977856d1b3103f8cd10e4` |
| `StepFreeIntechangeInfo.csv` | 114 | 8,540 | `d2028fb9b40cb99c9f5019c9cf2f7a3a56b6743485c21f4c9e429db3e2e30e36` |
| `Toilets.csv` | 410 | 45,061 | `69e2ecc977b6e685cd6fd8e7c86dc04c827cfd574b920c5c00a67a8edb67d49d` |

## Feed verification and station join

`Toilets.csv` is the current toilet dataset. Its real columns are:

`Station`, `StationUniqueId`, `Id`, `Type`, `IsAccessible`, `HasBabyChanging`, `IsInsideGateLine`, `Location`, `IsFeeCharged`, `IsManagedByTfL`, `AskStaff`, `RadarKey`, `OpeningHours`, `OpensWithStation`, `ClosesWithStation`, and the day/bank-holiday opening and closing fields.

The requested fields were all present. `Station` is blank in the toilet rows, so station names were joined from `Stations.csv` using `Stations.UniqueId = Toilets.StationUniqueId`. Stable source identity is the composite `(StationUniqueId, Id)`, represented in any future source link as a source-specific composite such as `tfl:{StationUniqueId}:toilet:{Id}`; the proposed package does not create it in production.

`Stations.csv` contains 509 stations. `StationPoints.csv` contains 4,084 station-linked points. All 410 toilet rows join to a station with usable coordinates; 179 distinct stations have toilet rows and 147 of those contain multiple toilet rows. The maximum toilet-row count at one station is 6.

TfL does not provide toilet-specific latitude/longitude. The package therefore labels every positional result `STATION_LEVEL_ONLY; TOILET_COORDINATES_NOT_PROVIDED`. The retained station coordinate is a median of the valid points for that station for comparison only. No toilet coordinate is fabricated, and station-level distance is never decisive by itself.

## Feed counts

| Measure | Count |
|---|---:|
| Station records | 509 |
| Toilet rows | 410 |
| Toilets with usable station coordinates | 410 |
| Accessible | 119 |
| Baby changing | 80 |
| Free | 397 |
| Charged | 13 |
| Fee unknown | 0 |
| Male | 147 |
| Female | 147 |
| Unisex | 116 |
| Inside gateline | 274 |
| Outside gateline | 136 |
| Gateline unknown | 0 |
| Missing station join | 0 |
| Missing toilet IDs | 0 |
| Duplicate `(StationUniqueId, Id)` rows | 0 |

## Relief reconciliation

Every real TfL toilet row was compared against the read-only published Relief snapshot of 15,620 facilities and 15,620 current facility-source links. The comparison used TfL identity/provenance first, station identity/name, canonical name/address, station-level coordinates/location, and current Toilet Map UK provenance. Distance was supporting evidence only.

| Required classification | Toilet rows |
|---|---:|
| `EXACT_MATCH` | 0 |
| `HIGH_CONFIDENCE_MATCH` | 305 |
| `REVIEW_MATCH` | 33 |
| `DISTINCT_NEW` | 58 |
| `INSUFFICIENT_LOCATION` | 0 |
| `QUARANTINE` | 14 |

There were no exact TfL identities in current Relief provenance. The 305 high-confidence identity/name-and-station-coordinate matches are not automatically executable because 291 of their rows are part of a multi-row collision on an existing facility candidate.

### Proposed operations

These are proposal counts after the facility-model guard; none was executed.

| Operation | Candidate rows | Treatment |
|---|---:|---|
| `INSERT` | 58 | Genuinely new candidate toilets with a stable TfL row identity and station-level location; still requires separate approval and model review before creation. |
| `SOURCE_LINK` | 14 | Existing-facility source-link candidates not blocked by a multi-toilet collision. |
| `ENRICHMENT` | 14 | Existing-facility candidates where TfL source attributes can be retained for review/provenance; no canonical overwrite is authorized. |

Before the model guard there were 305 source-link and 305 enrichment candidates. The guard blocked 291 source-link and 291 enrichment candidates because multiple distinct TfL toilet rows would map to one Relief facility. The frozen JSON records field-level `same`, `enrichment`, `conflict`, `omission`, and `unknown` results for the directly mappable fields (`is_accessible`, `has_baby_changing`, `is_free`, and the cautious Unisex-to-gender-neutral comparison), plus source-only fields.

## TfL IDs and the Relief facility model

TfL `Id` is stable only in combination with `StationUniqueId`; the numeric toilet ID alone is not a safe global key. A station may contain two, three, four, or six rows. The feed also distinguishes Male, Female, and Unisex rows and sometimes supplies different platform/ticket-hall locations.

Relief currently has one canonical `facilities` row per place and a `facility_sources` table for source identity. It has no child toilet table and no canonical fields for gateline status, TfL management, or toilet-specific location. Therefore:

- do not collapse Male/Female/Unisex rows into one facility;
- do not create separate facilities merely because the station has multiple rows when the physical distinction is not supportable;
- preserve each TfL row as a separate source candidate keyed by `(StationUniqueId, Id)`;
- require a model decision for every set of TfL rows that points to one existing Relief facility; and
- retain station-level precision explicitly if any candidate is approved.

The reconciliation found 328 rows requiring positional/model adjudication across 124 existing facility candidates. Including the other review/quarantine outcomes, 338 rows remain unresolved for positional or model reasons. Expected net-new Relief facilities if the 58 distinct-new candidates were separately approved is **58**, subject to the required human model decision.

## Production boundary

| Count | Pre | Proposed post |
|---|---:|---:|
| `facilities` | 15,620 | 15,620 |
| current `facility_sources` | 15,620 | 15,620 |
| `import_runs` | 5 | 5 |
| `toilet_map_import_staging` | 0 | 0 |

Production mutations are confirmed as **0**. The package has no apply option and no mutation path. The official ZIP and read-only snapshots remain local ignored cache material; only the derived evidence package and preparation code are committed.

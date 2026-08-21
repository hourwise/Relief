# UK public-source expansion — discovery and ingestion preparation

**Status:** `DISCOVERY / INGESTION PREPARATION / PRODUCTION APPLY NOT AUTHORIZED`
**Review date:** 2026-08-20
**Branch:** `codex/toilet-map-apply-1a-production-deploy`

This bounded batch investigated additional official UK public-toilet sources
without changing the accepted Toilet Map production state. The read-only
production checkpoint was `15,620` facilities, `15,620` current source links,
`5` import runs, and `0` staging rows. The only current source name in
`facility_sources` was `Toilet Map UK` (`15,620` rows). Production mutations
remain `0`.

## Results

National Rail Knowledgebase is high-value but not yet ingestible from the
public website. National Rail says that Knowledgebase contains station
facilities and is available through the registered data portal/API. The
specific feed and NRE licence terms must be obtained before any snapshot or
republishing decision. The official developer page is
<https://www.nationalrail.co.uk/developers/>.

TfL is also high-value but the public example is not a production source. TfL
states that live feeds require registration and that its bus-toilet example is
not updated. The example was downloaded only as a local, ignored fixture and
contains 48 station rows. It has no coordinates, so all 48 records are
`ENRICHMENT_ONLY_MISSING_COORDINATES`; there are no duplicate IDs or coordinate
collision groups. The source page is
<https://tfl.gov.uk/info-for/open-data-users/our-open-data?intcmp=3671> and the
example URL is
<https://tfl.gov.uk/cdn/static/cms/documents/bus-stations-with-public-toilets.csv>.

Rother District Council is a promising bounded local-authority candidate. The
National Data Library records the dataset as current metadata under the Open
Government Licence, but the listed resource is not enough to prove a current,
coordinate-bearing machine feed, stable row identity, or operating status.
That source remains pending direct resource confirmation:
<https://www.data.gov.uk/dataset/e318a429-678e-447d-adbd-88f03faaa271/rother-district-council-public-toilets>.

Wales has a useful national layer, but the layer metadata names the Public
Sector Geospatial Agreement (PSGA). This batch does not infer OGL reuse from a
portal-wide policy statement, and no Welsh records were ingested:
<https://datamap.gov.wales/layers/geonode%3Anational_toilet_map/metadata_detail>.

Scotland’s data platform is transitioning, and Northern Ireland did not yield
a selected current facility-level feed with clearly verified reuse terms in
this bounded review. Both remain investigation items rather than speculative
ingestion targets.

## Guardrails implemented

`tools/source_expansion/` contains a separate registry, a standard-library
normalizer, fixture tests, and a read-only evidence generator. It preserves
unknown values as null, refuses to reinterpret OSGB36 easting/northing as WGS84
coordinates, records source identity and checksums, reports duplicate and
coordinate collisions, and has no Supabase client or apply option. Raw source
snapshots are ignored and are not force-added. The derived assessment is in
[`docs/data/UK_PUBLIC_SOURCE_EXPANSION_REVIEW.json`](data/UK_PUBLIC_SOURCE_EXPANSION_REVIEW.json),
and the TfL fixture evidence is in
[`docs/data/UK_PUBLIC_SOURCE_EXPANSION_TFL_REVIEW.json`](data/UK_PUBLIC_SOURCE_EXPANSION_TFL_REVIEW.json).

No source is promoted to `CURRENT_SOURCE_READY` until its current endpoint,
stable record identity, coordinates/CRS, update cadence, licence, and required
attribution are independently verified. Any future insert/update package must
be a separately governed generation and must not reuse an Apply 2A or Apply 2B
writer.

## TfL real detailed feed — 2026-08-21

The official current detailed station-data ZIP was acquired successfully from
`https://api.tfl.gov.uk/stationdata/tfl-stationdata-detailed.zip` without an
API key. Its checksum, complete ZIP inventory, feed schema verification,
station join, row-level reconciliation, operation proposal, and production
boundary are frozen in
[`UK_PUBLIC_SOURCE_EXPANSION_TFL_REAL_FEED_2026-08-21.md`](data/UK_PUBLIC_SOURCE_EXPANSION_TFL_REAL_FEED_2026-08-21.md)
and its JSON companion.

The real feed has 509 stations and 410 toilet rows. `Toilets.csv` exposes the
requested station/toilet IDs, access, baby-changing, gateline, location, fee,
type, and TfL-management fields. All toilet rows join to `Stations.csv`; all
have station-level coordinates through `StationPoints.csv`, but none has a
toilet-specific coordinate. The package explicitly retains
`STATION_LEVEL_ONLY; TOILET_COORDINATES_NOT_PROVIDED`.

The row classifications are 0 `EXACT_MATCH`, 305 `HIGH_CONFIDENCE_MATCH`, 33
`REVIEW_MATCH`, 58 `DISTINCT_NEW`, 0 `INSUFFICIENT_LOCATION`, and 14
`QUARANTINE`. Because the source has multiple rows per station, the model
guard blocks automatic collapse: 328 rows map to 124 existing facility
candidates and require facility-model adjudication. After that guard, the
frozen proposal contains 58 `INSERT`, 14 `SOURCE_LINK`, and 14 `ENRICHMENT`
candidates. None was executed. Production mutations remain `0`.

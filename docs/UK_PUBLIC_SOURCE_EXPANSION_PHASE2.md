# UK source expansion Phase 2 — live acquisition and candidate reconciliation

**Status:** `LIVE FEED ACQUIRED / CANDIDATE RECONCILIATION / PRODUCTION APPLY NOT AUTHORIZED`
**Review date:** 2026-08-20
**Starting commit:** `334a12dee4fae50e6829e26298e0d0cebeb86252`

This phase acquired one current, clearly licensed facility-level source and
performed a read-only reconciliation against Relief. Production remains at
`15,620` facilities, `15,620` facility sources, `5` import runs, and `0`
staging rows. No canonical, source-link, provenance, staging, or import-run
mutation occurred.

## Sheffield City Council

The official National Data Library entry declares Public Toilets Sheffield
under the UK Open Government Licence and exposes the council’s ArcGIS GeoJSON
resource. The catalog entry was last updated 2025-02-20; the live resource was
retrieved on 2026-08-20 and has SHA-256
`0206086836c35ae3516531767563c8d2499994ed255c3555332169b942090e7f`.

The snapshot contains 41 features, each with a UPRN source identifier and WGS84
Point coordinates. The published feature properties contain no facility name,
so all 41 remain `REVIEW_REQUIRED_MISSING_NAME`. No record is prepared for
insertion. There are no duplicate source IDs.

A read-only production query found 18 source points with an existing Relief
facility inside an approximate 100 m latitude/longitude bounding window and 23
without one. No exact Sheffield source-record links were present. The 18
nearby points are not automatically classified as matches: the source has no
name, and proximity alone cannot safely distinguish a duplicate, a distinct
toilet at the same site, or a coordinate discrepancy. The 23 remaining points
also cannot be inserted without a meaningful source name and further review.

The catalog entry is
<https://www.data.gov.uk/dataset/1e172d53-a4d2-4da3-8fe7-206537f0611d/public-toilets-sheffield>.
The official GeoJSON endpoint is recorded in the registry and evidence. The
machine output is preserved only in the ignored content-addressed cache.

## Remaining access actions

- National Rail still requires data-portal self-sign-up and the applicable NRE
  feed terms before the Knowledgebase station-facilities feed can be acquired:
  <https://www.nationalrail.co.uk/developers/>.
- TfL still requires live-feed registration. Its public bus-toilet example is
  not current and has no coordinates:
  <https://tfl.gov.uk/info-for/open-data-users/our-open-data?intcmp=3671>.
- Rother’s official OGL catalog entry currently exposes a PDF resource rather
  than a confirmed current machine-readable facility feed:
  <https://www.data.gov.uk/dataset/e318a429-678e-447d-adbd-88f03faaa271/rother-district-council-public-toilets>.
- Wales remains pending layer-specific PSGA reuse confirmation; Scotland and
  Northern Ireland remain pending a current facility-level feed with explicit
  reuse terms.

## Evidence and implementation

- [Sheffield normalized review](data/UK_PUBLIC_SOURCE_EXPANSION_SHEFFIELD_REVIEW.json)
- [Phase 2 structured package](data/UK_PUBLIC_SOURCE_EXPANSION_PHASE2.json)
- [Expansion registry](../tools/source_expansion/source_registry.json)
- [Expansion pipeline](../tools/source_expansion/pipeline.py)

The package is candidate evidence only. It has no apply option and records
`production_mutations = 0`.

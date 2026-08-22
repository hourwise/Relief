# NaPTAN N4A — geometry-origin contract

Geometry is stored only with explicit origin and scope semantics.

| Origin | Scope | Stored in N4A source rows? | Meaning |
| --- | --- | --- | --- |
| `PUBLISHER` | `STOP_AREA_LEVEL` | Yes, on source places | Direct NaPTAN StopArea coordinates |
| `PUBLISHER` | `TRANSPORT_STOP_LEVEL` | Yes, on source nodes | Direct NaPTAN StopPoint coordinates |
| `DERIVED` | child/member centroid | No | N3 analysis-only geometry; must retain contributing IDs and method if later persisted |
| `NONE` | none | Yes as explicit scope | No usable source coordinate |

Publisher latitude/longitude are retained as scalar source values and a generated WGS84 geography is a query helper. It does not increase source precision. N3's 24 derived geometries (one child-area centroid and 23 member centroids) are not written into a publisher coordinate column and cannot be used to silently update a canonical Relief facility.

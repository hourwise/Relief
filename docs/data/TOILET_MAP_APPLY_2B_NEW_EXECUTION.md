# Toilet Map Apply 2B production execution

`TOILET MAP APPLY 2B — 36 NEW FACILITIES LIVE / VERIFIED`

The frozen Apply 2B manifest was executed against Supabase project
`bgwxrxkmyaihplaloely` on 2026-08-19. The transaction was bounded to the exact
36 `PREPARE_INSERT_CANDIDATE` operations in
`TOILET_MAP_APPLY_2B_NEW_MANIFEST.json`.

## Frozen package

- Preparation commit: `52669bdee8322c83f5cba8138e8c7d3e0746ef2f`
- Manifest SHA-256: `97AFCDECF7B492010A58D40259F1ED30666182565F36C593174E54BF6B4DA1A3`
- Source: `Toilet Map UK`
- Source version: `2026-08-18T01:00:00+00:00`
- Source checksum: `5600358CE06CA5DFDC0060968B26E8C9E05A1CB5C9DBE0455CDF3951F480AD7F`
- Licence: `CC BY 4.0`
- Authorized operations: `36`

## Transaction boundary

The one-time guarded transaction inserted exactly 36 new `facilities` rows and
their 36 one-to-one `facility_sources` rows. It did not update or delete an
existing facility, alter existing provenance, create an `import_runs` row,
write `toilet_map_import_staging`, or reopen Apply 2A. The exact public source
rows were retained in the corresponding `facility_sources.raw_data` values;
the ignored raw snapshot was not force-added or published.

The transaction aborted on any baseline drift, existing exact source link,
exact canonical identity, source checksum mismatch, insert count mismatch, or
source-link mapping mismatch.

## Postcheck

Postcheck time: `2026-08-19 22:31:24.633119+00` UTC.

| Check | Result |
|---|---:|
| Facilities before | 15,584 |
| Facilities after | 15,620 |
| Facility source links before | 15,584 |
| Facility source links after | 15,620 |
| Import runs after | 5 |
| Staging rows after | 0 |
| Authorized source links | 36 |
| Distinct inserted facilities | 36 |
| Missing authorized links | 0 |
| Exact field/source-value mismatches | 0 |
| Excluded records linked or inserted | 0 |

The five deferred records and the quarantined `Does not exist` record were not
inserted. Apply 2A remains closed and unchanged.

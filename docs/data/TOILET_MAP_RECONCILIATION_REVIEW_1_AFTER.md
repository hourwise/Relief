# Toilet Map UK Reconciliation Dry Run - 2026-08

> Read-only report. No Supabase inserts, updates, deletes, migrations, or deployments were performed.

## Source

- Canonical source: Toilet Map UK
- Official dataset page: https://www.toiletmap.org.uk/dataset
- Download URL used: https://p02w6qqjlqmja4sk.public.blob.vercel-storage.com/exports/toilets-2026-08-11T00%3A00%3A40.710Z-APHGhV8gen3MznZyQPYdAigXG8eRY7.csv?download=1
- Source-declared update timestamp: 2026-08-11T01:00:00+00:00
- Retrieved at: 2026-08-11T13:13:27+01:00
- Licence: CC BY 4.0
- Input checksum: `f6824fdc7cd29df8c1f45ba749c1b28d319fb34803c55459bbe748ef65937624`
- Input bytes: 7,856,657

## Baseline and input

- Relief facilities at baseline: **15,584**
- Toilet Map records in current input: **16,057**
- Active / removed-or-inactive / unknown status: **16,057 / 0 / 0**
- Existing Toilet Map-linked facilities in baseline: **15,584**
- Facilities with non-empty field provenance: **10,922**

## Reconciliation result

| Measure | Count |
|---|---:|
| Exact source-ID matches | 15,567 |
| High-confidence inferred matches | 0 |
| Ambiguous candidates | 1 |
| Likely-new facilities | 31 |
| Existing linked records unchanged | 15,526 |
| Existing linked records changed | 41 |
| Upstream removed/inactive records | 0 |
| Previously linked records absent upstream | 17 |
| Invalid source records | 458 |
| Source-quality warning records | 2,746 |
| Potential duplicate-risk clusters | 0 |

## Field enrichment opportunities

- `has_baby_changing` could supply a previously unknown Relief value for **16** matched records.
- `is_gender_neutral` could supply a previously unknown Relief value for **15** matched records.
- `requires_radar_key` could supply a previously unknown Relief value for **14** matched records.
- `opening_hours` could supply a previously unknown Relief value for **6** matched records.
- `is_accessible` could supply a previously unknown Relief value for **2** matched records.
- `is_free` could supply a previously unknown Relief value for **1** matched records.

## Field conflicts

- `name` disagrees with the current Relief value on **19** matched records.
- `is_accessible` disagrees with the current Relief value on **15** matched records.
- `opening_hours` disagrees with the current Relief value on **11** matched records.
- `longitude` disagrees with the current Relief value on **9** matched records.
- `latitude` disagrees with the current Relief value on **8** matched records.
- `requires_radar_key` disagrees with the current Relief value on **4** matched records.
- `has_baby_changing` disagrees with the current Relief value on **1** matched records.
- `is_gender_neutral` disagrees with the current Relief value on **1** matched records.

## Matching rules

- Existing `facility_sources` source ID linkage is authoritative.
- High-confidence inference requires a close name match plus a conservative 60m/150m geographic threshold and no close competitor.
- Ambiguous candidates are reported, never automatically merged.
- Missing upstream values remain unknown; they do not clear or become false in Relief.
- A source record missing from the current snapshot is reported for policy review; it is not deleted or unpublished.

## Representative review samples

- **likely_new:** 10 sample(s) in the machine-readable report.
- **changed:** 10 sample(s) in the machine-readable report.
- **ambiguous:** 1 sample(s) in the machine-readable report.
- **upstream_removed_or_inactive:** none available in this run.
- **previously_linked_absent_upstream:** 10 sample(s) in the machine-readable report.
- **invalid_or_source_quality:** 10 sample(s) in the machine-readable report.
- **field_conflicts:** 10 sample(s) in the machine-readable report.

## Safety boundary

This command uses only HTTP GET for the configured Supabase REST reads and local file writes for snapshots/reports. The existing live importer remains a separate, explicit path and was not invoked.

Machine-readable report: `docs/data/TOILET_MAP_RECONCILIATION_REVIEW_1_AFTER.json`

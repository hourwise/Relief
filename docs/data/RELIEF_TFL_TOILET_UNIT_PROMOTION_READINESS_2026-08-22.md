# Relief TfL Toilet-Unit Promotion Readiness — 2026-08-22

**NO-GO REQUIRES ADJUDICATION**

**PROPOSAL-ONLY / PRODUCTION EXECUTION NOT AUTHORIZED**

This package reassesses the frozen TfL reconciliation after deployment of the
additive `toilet_units` / `toilet_unit_sources` schema. It does not retrieve a
new feed, write production rows, write staging rows, create an import run, or
promote any TfL record. The historical reconciliation reports remain
unchanged.

## Starting and ending state

| Item | Starting | Ending |
|---|---|---|
| Branch | `codex/toilet-map-apply-1a-production-deploy` | same |
| Local HEAD | `c07d922e20ddf81053827ab86fc9dee7c6dc5267` | proposal package commit |
| Remote HEAD | `c07d922e20ddf81053827ab86fc9dee7c6dc5267` | proposal package commit |
| Staged paths | none | intentional package paths only |
| Protected files | present, untouched, unstaged | same |

The protected working-tree state was:

```text
 M .easignore
 M app.json
?? docs/EAS_CONFIG_AUDIT.md
```

No protected file is included in this package.

## Production preflight

The linked production project is `bgwxrxkmyaihplaloely`. Read-only checks
confirmed migration `20260821213435 add_toilet_unit_model` is present and the
two new tables are empty.

| Table | Before | After |
|---|---:|---:|
| `facilities` | 15,620 | 15,620 |
| `facility_sources` | 15,620 | 15,620 |
| `import_runs` | 5 | 5 |
| `toilet_map_import_staging` | 0 | 0 |
| `toilet_units` | 0 | 0 |
| `toilet_unit_sources` | 0 | 0 |

No TfL rows exist in either toilet-unit table. Production data mutations,
TfL promotion mutations, staging mutations, import-run creation, facility
mutations, and facility-source mutations all remain **0**.

The source exposure boundary remains intact:

- `toilet_units` has the published-parent/public-read policy;
- both tables have RLS enabled;
- `toilet_unit_sources` has no public read policy and no `public`, `anon`, or
  `authenticated` table grants;
- privileged service-role access remains available.

## Frozen inputs and provenance

The authoritative frozen inputs were not overwritten:

| Artifact | SHA-256 |
|---|---|
| `tools/source_expansion/cache/tfl-detailed-2026-08-21/tfl-reconciliation.json` | `65cc9cc8c41b7b3a003524610b674c7f2eae96ff7fe5116f38f2d2856cb777cb` |
| `docs/data/UK_PUBLIC_SOURCE_EXPANSION_TFL_REAL_FEED_2026-08-21.json` | `89b689c13699218d40a24134ebd3b95895844bff21ba6068c8e328d5bc2fc88a` |
| `docs/data/RELIEF_TFL_FACILITY_MODEL_ADJUDICATION_2026-08-21.json` | `df45ddc9b3b24d3292dbb93dd8a8ff5e1e4497199e8f3df7efa02c2496548ff8` |
| `tools/source_expansion/cache/tfl-detailed-2026-08-21/tfl-stationdata-detailed.zip` | `19c50772febd1a3d7625f59e079b7590c5da4ed70424d6f552cfd7db1611e2ce` |

The source ZIP was retrieved at `2026-08-21T06:08:20.1476469Z`, was 186,973
bytes, and came from:

`https://api.tfl.gov.uk/stationdata/tfl-stationdata-detailed.zip`

Required attribution remains:

`Data provided by Transport for London`

The applicable terms are recorded in the frozen report at:

`https://tfl.gov.uk/corporate/terms-and-conditions/transport-data-service`

The source package contained 509 stations and 410 toilet rows. All 410 rows
have station-level coordinates; none have toilet-level coordinates.

## Physical-unit identity rules

The deterministic hierarchy for this transaction is:

1. TfL source identity is `(StationUniqueId, Id)`, represented as
   `tfl:{StationUniqueId}:toilet:{Id}`. It is a source-row identity only.
2. Parent identity requires an existing authoritative venue/station identity
   or a separately verified canonical parent. Name, operator context, address,
   and coordinates support the decision but distance alone never creates it.
3. Physical-unit identity may use independently distinct platform, level,
   gateline, paid/unpaid-area, entrance, or other location descriptors.
4. Male/Female/Unisex, source row count, or different TfL IDs alone never prove
   separate physical rooms.
5. Station coordinates remain station coordinates. They are never written as
   toilet-unit coordinates.

## Reassessment of the 58 INSERT cohort

The previous 58 `INSERT` rows were re-evaluated against the live child model.
All 58 have no existing production `facility_id`, so none can produce a
schema-valid child row without first creating or adjudicating a canonical
parent. The source does not provide the independently verified canonical
address/town needed for that parent operation.

| Classification | Count | Meaning |
|---|---:|---|
| `SAFE_UNIT_INSERT` | 0 | No row is independently safe for production promotion |
| `DUPLICATE_PROPOSAL` | 0 | No duplicate proposal was accepted |
| `EXISTING_UNIT_MATCH` | 0 | Production contains zero toilet units |
| `PHYSICAL_UNIT_AMBIGUOUS` | 49 | Multiple rows share a station and lack independently distinct location descriptors |
| `POSITIONAL_AMBIGUITY` | 0 | Position is not the primary blocker for this cohort |
| `SOURCE_IDENTITY_AMBIGUOUS` | 0 | All 410 source IDs are present and unique |
| `OTHER_NO_GO` | 9 | Physical/source separation is plausible, but no canonical parent is safe |

The 9 `OTHER_NO_GO` rows comprise seven singleton-station rows and two rows
whose descriptions distinguish platform 1 from platform 2. This is not an
approval count: the parent facility gap still blocks them. The 49 ambiguous
rows include same-location Male/Female/Unisex groups such as Hayes &
Harlington, Penge West, and White Hart Lane. Those rows remain separate source
rows and are not collapsed.

Exact safe proposed payloads:

- `toilet_units` inserts: **0**
- `toilet_unit_sources` inserts: **0**
- `toilet_units` updates: **0**
- `toilet_unit_sources` updates: **0**

## Reassessment of SOURCE_LINK and ENRICHMENT

All 14 prior `SOURCE_LINK` rows are:

`HUMAN_UNIT_ADJUDICATION` — 0 safe links, 14 unresolved links.

They have facility-level candidates but no exact child-unit target. No source
link may be attached to a guessed unit.

All 14 prior `ENRICHMENT` rows are:

`HUMAN_UNIT_ADJUDICATION` — 0 safe enrichments, 14 unresolved enrichments.

Among those 14 rows, the frozen field comparison contains:

- 4 `is_free` conflicts;
- 3 `has_baby_changing` conflicts;
- 2 `is_accessible` conflicts;
- 1 `is_gender_neutral` conflict;
- 8 `is_gender_neutral` additive candidates;
- 6 `has_baby_changing` additive candidates;
- 2 `is_free` additive candidates;
- 2 `is_accessible` additive candidates.

These counts overlap by row and do not authorize parent-field overwrites.

## Collision decomposition — 328 rows

The collision categories are deliberately overlapping because one source row
can have both a parent ambiguity and a coordinate-support signal.

| Category | Count | Machine-resolvable? | Human review? |
|---|---:|---:|---:|
| Exact source-ID collision | 0 | Yes | No |
| Same source record mapped to multiple facilities | 0 | Yes | No |
| Multiple source rows sharing one parent candidate | 328 rows / 124 candidate facilities | No | Yes |
| Parent-facility ambiguity (`candidate_count > 1`) | 211 | No | Yes |
| Single parent candidate but child target unknown | 117 | No | Yes |
| Name match used as supporting evidence | 328 | No | Yes |
| Missing toilet location description | 41 | No | Yes |
| Unit-type ambiguity | 328 | No | Yes |

Station-coordinate distance is supporting evidence only, never a unit identity
decision. The 328 rows fall into these distance bands from the selected
facility candidate:

- exact 0 m: 0;
- 0–25 m: 105;
- 25–100 m: 168;
- over 100 m: 55.

The over-100 m values are especially unsuitable for automatic child linking;
the close values are not automatically safe either because the coordinates are
station-level and several source rows can share one parent candidate.

## Unresolved decomposition — 338 rows

These categories overlap and therefore must not be added together.

| Failure class | Count |
|---|---:|
| `POSITIONAL_UNCERTAINTY` | 338 |
| `PHYSICAL_UNIT_UNCERTAINTY` — station has multiple TfL rows | 317 |
| `PARENT_FACILITY_UNCERTAINTY` — more than one candidate | 222 |
| `INSUFFICIENT_SOURCE_IDENTITY` | 0 |
| `MISSING_COORDINATE` | 0 |
| `LOW_PRECISION_COORDINATE` — station-level only | 338 |
| `CONFLICTING_SOURCE_FIELDS` | 202 |
| Missing toilet location description | 48 |

All source identities are complete. The unresolved state is therefore not a
missing-ID problem; it is the inability to prove the parent and physical child
relationship without inventing toilet-level precision or collapsing rows.

## No-collapse and coordinate proof

- 410 source rows produce 410 unique `tfl:{StationUniqueId}:toilet:{Id}` IDs.
- 147 stations contain multiple toilet rows.
- No rows are collapsed by gender, source ID, station name, rounded
  coordinates, or generic toilet label.
- 410 rows are `STATION_LEVEL_ONLY; TOILET_COORDINATES_NOT_PROVIDED`.
- 0 rows have toilet-level coordinates.
- 0 safe payloads contain coordinates.

## Idempotency and replay

The safe operation set is empty, so the isolated proposal replay proof is
intentionally zero-operation:

| Replay | Unit inserts | Source inserts | Enrichment updates |
|---|---:|---:|---:|
| First proposal application | 0 | 0 | 0 |
| Second identical replay | 0 | 0 | 0 |
| Shuffled operation order | 0 | 0 | 0 |
| Partial interruption/replay | 0 | 0 | 0 |

No production fixture or production apply path was used. A future non-empty
apply must add an isolated fixture proving unique source-key replay,
interruption recovery, and no duplicate child rows before it is authorized.

## Human adjudication package

The machine-readable JSON contains compact per-row records for the 58 INSERT
rows, 14 SOURCE_LINK rows, 14 ENRICHMENT rows, the 328 collision rows, and the
338 unresolved rows. The recommended review cohorts are:

1. **New-station parent cohort — 9 rows:** verify a canonical parent address,
   town, discoverability identity, and whether a future parent + child proposal
   is permitted.
2. **Same-station multiplicity cohort — 49 rows:** decide physical-unit
   separation where rows share or omit location descriptions. Permitted
   answers are `CONFIRMED_DISTINCT_UNIT`, `LIKELY_DISTINCT_UNIT`,
   `SOURCE_DISTINCT_PHYSICAL_UNKNOWN`, or `UNRESOLVED`.
3. **Existing-parent child-target cohort — 14 source rows / 28 operation
   entries:** identify the exact child unit, or explicitly reject the source
   link/enrichment. Candidate parent similarity is not enough.

## Future production operation plan

No future operation is approved by this package. If a later adjudication
resolves a cohort, the apply must remain bounded to explicitly enumerated rows.

| Future operation | Proposed count now |
|---|---:|
| `toilet_units` inserts | 0 |
| `toilet_units` updates | 0 |
| `toilet_unit_sources` inserts | 0 |
| `toilet_unit_sources` updates | 0 |
| `import_runs` inserts | 0 |
| staging rows | 0 |
| `facilities` mutations | 0 |
| `facility_sources` mutations | 0 |

## Readiness decision

`NO_GO_REQUIRES_ADJUDICATION`

The live model is sufficient; this is not `NO_GO_MODEL_GAP`. The source IDs
and provenance are sufficient; this is not `NO_GO_SOURCE_PROVENANCE`. However,
there is no independently safe cohort today because:

- all 58 new candidates lack a production parent;
- no exact child-unit target exists for the 14 links or 14 enrichments;
- 49 new rows have unresolved physical multiplicity;
- every coordinate is station-level only.

### Recommended next bounded transaction

Do not run a production apply yet. The next bounded transaction should be a
human adjudication-only package for the 9 plausible new-station rows and the
49 same-station multiplicity rows, with independently verified parent address
and unit identity. Only after that package produces explicit child-unit IDs
should a separate, explicitly authorized apply enumerate `toilet_units` and
`toilet_unit_sources` rows. TfL promotion remains unauthorized until then.

## Validation and publication boundary

The package includes deterministic tests for:

- same-station multi-unit non-collapse;
- no parent invention from station coordinates;
- source identity and coordinate precision rules;
- zero-production-mutation and no-promotion guards;
- JSON-safe readiness output.

The full repository test suite and TypeScript typecheck must pass before the
package is committed. No EAS, Gradle, Expo prebuild, Android, APK, or native
build command is permitted.

Final state:

**RELIEF TFL TOILET-UNIT PROMOTION READINESS — NO-GO REQUIRES ADJUDICATION / PRODUCTION PROMOTION NOT AUTHORIZED**

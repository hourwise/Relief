# Relief TfL existing-parent observation ingestion — governed 14-row apply

## Final classification

**RELIEF TFL EXISTING-PARENT OBSERVATION INGESTION — 14 SOURCE OBSERVATIONS APPLIED / PHYSICAL-UNIT PROMOTION NOT AUTHORIZED**

This transaction applied only the previously reviewed 14 TfL facility-level source observations. It did not promote any source row to a physical toilet unit.

## Starting state

- Repository: `hourwise/Relief`
- Branch: `codex/toilet-map-apply-1a-production-deploy`
- Starting local SHA: `49b78cddc2afb7e25767f19881a769fc08173868`
- Starting remote SHA: `49b78cddc2afb7e25767f19881a769fc08173868`
- Starting commit: `docs(data): verify source observation production schema`
- Protected working-tree changes preserved untouched, unstaged, and uncommitted:
  - `.easignore`
  - `app.json`
  - `docs/EAS_CONFIG_AUDIT.md`

## Source integrity

- TfL ZIP URL: `https://api.tfl.gov.uk/stationdata/tfl-stationdata-detailed.zip`
- ZIP SHA-256: `19c50772febd1a3d7625f59e079b7590c5da4ed70424d6f552cfd7db1611e2ce`
- ZIP size: `186,973` bytes
- Retrieval UTC: `2026-08-21T06:08:20.1476469Z`
- Frozen reconciliation SHA-256: `65cc9cc8c41b7b3a003524610b674c7f2eae96ff7fe5116f38f2d2856cb777cb`
- Required attribution retained: `Data provided by Transport for London`
- No TfL source refresh, redownload, normalization, replacement, or fresh web evidence was used.

## Cohort

The frozen prior audit contained 28 operation entries:

- `SOURCE_LINK` entries: 14
- `ENRICHMENT` entries: 14
- Unique TfL source observations: **14**
- Station groups: **14**
- Canonical facility groups: **14**
- Batch 1 contamination: **0**
- New-parent contamination: **0**

The 58-row Human Adjudication Batch 1 cohort was not touched.

## Production target and preflight

- Supabase project: `Relief`
- Project ref: `bgwxrxkmyaihplaloely`
- Project status: `ACTIVE_HEALTHY`

Read-only production preflight passed:

- 14/14 canonical parent facilities present;
- 14 distinct canonical facility IDs;
- exact TfL source links already present: 0;
- missing exact TfL source links: 14;
- conflicting source links: 0;
- duplicate exact source links: 0;
- existing observations: 0;
- existing identical observations: 0;
- canonical parent snapshot MD5: `2aa9b2f8e2ff00609c59c58058fad093`.

Pre-apply counts:

| Object | Count |
| --- | ---: |
| `facilities` | 15,620 |
| `facility_sources` | 15,620 |
| `import_runs` | 5 |
| `toilet_map_import_staging` | 0 |
| `toilet_units` | 0 |
| `toilet_unit_sources` | 0 |
| `facility_source_observations` | 0 |

## Source-link analysis

The 14 source links were absent and had no conflicts. The exact source identity used for each link is:

`source_name = TfL detailed station data — station facilities and toilets`

with the immutable `source_record_id` values `tfl:{StationUniqueId}:toilet:{Id}`. Each new link points to the already-verified canonical facility, uses the frozen official ZIP URL, records the TfL Transport Data Service terms identifier, and has `import_run_id = NULL`.

## Import-run decision

**IMPORT_RUN_NOT_REQUIRED**

The deployed `facility_source_observations` table has no `import_runs` relationship. The existing `import_runs` apply contract is specifically constrained to the earlier Toilet Map UK Apply 1A workflow and cannot truthfully represent this TfL source-observation transaction. Creating an unbound generic import run would add no governance or traceability, so zero import runs were created.

## Apply plan and execution

The declarative plan was generated from committed evidence and enforced:

| Operation | Planned | Executed |
| --- | ---: | ---: |
| Canonical facility inserts | 0 | 0 |
| Facility-source inserts | 14 | 14 |
| Source-observation inserts | 14 | 14 |
| Canonical facility updates | 0 | 0 |
| Canonical enrichments | 0 | 0 |
| Toilet-unit inserts | 0 | 0 |
| Toilet-unit source links | 0 | 0 |
| Import runs | 0 | 0 |

Execution used one guarded production transaction. It refused to proceed unless all 14 parents existed, no conflicting links or observations existed, the source-link insert count was exactly 14, the observation insert count was exactly 14, all payloads matched, physical-unit invariants held, and protected-table counts were unchanged.

Apply plan SHA-256: `ed1aa9e7e5b54c65c18acd4c2d2ff4909782ff92383ed04ac910558642246a0e`

## Observation verification

Post-apply verification confirms:

- expected observations present: **14/14**;
- source identities and deterministic observation keys match;
- every observation references the intended facility-source row;
- all structured payloads match the frozen plan;
- all source links are current and have `import_run_id = NULL`;
- all observations are current;
- observed attribute hashes are recorded in the machine-readable verification artifact.

The final production observation identities and hashes are recorded in [RELIEF_TFL_EXISTING_PARENT_OBSERVATION_POST_APPLY_2026-08-22.json](<D:/Users/fleur/Nicola App/relief-app/docs/data/RELIEF_TFL_EXISTING_PARENT_OBSERVATION_POST_APPLY_2026-08-22.json>).

## Physical-unit safety

- Physical units created: **0**
- Physical-unit mappings inferred: **0**
- Observation-to-unit links: **0**
- Physical assertions: **0**
- Toilet-specific coordinates: **0**
- All observations: `coordinate_scope = STATION_LEVEL`
- All observations: `physical_unit_asserted = false`
- All observations: `unit_link_status = UNLINKED`
- All observations: `toilet_unit_id IS NULL`

No physical-unit inference was made from gender, accessibility, baby changing, fee status, IDs, row order, location text, multiple rows, or station coordinates.

## Canonical facility safety

- Facility inserts: **0**
- Facility updates: **0**
- Canonical enrichments: **0**
- Canonical parent snapshot MD5 before: `2aa9b2f8e2ff00609c59c58058fad093`
- Canonical parent snapshot MD5 after: `2aa9b2f8e2ff00609c59c58058fad093`

## Post-apply counts

| Object | Pre-apply | Post-apply | Delta caused by this transaction |
| --- | ---: | ---: | ---: |
| `facilities` | 15,620 | 15,620 | 0 |
| `facility_sources` | 15,620 | 15,634 | +14 |
| `import_runs` | 5 | 5 | 0 |
| `toilet_map_import_staging` | 0 | 0 | 0 |
| `toilet_units` | 0 | 0 | 0 |
| `toilet_unit_sources` | 0 | 0 | 0 |
| `facility_source_observations` | 0 | 14 | +14 |

## Idempotency

The second read-only plan classified all 14 rows as already applied identically:

- source-link inserts proposed: **0**;
- conflicting links: **0**;
- observation inserts proposed: **0**;
- already-applied-identically candidates: **14**;
- other mutation categories proposed: **0**.

## Security

The post-apply security posture remains unchanged and fail-closed:

- RLS enabled: yes;
- policies on `facility_source_observations`: 0;
- `public` SELECT: false;
- `anon` SELECT: false;
- `authenticated` SELECT: false;
- privileged `service_role` SELECT/INSERT: true;
- no public API or UI exposure was added.

## Validation

Passed checks:

- exact branch/local/remote checkpoint preflight;
- production project identity verification;
- deterministic 14-row cohort reproduction;
- planner focused tests: **5 passed**;
- existing source-expansion tests: **24 passed**;
- Python compilation;
- declarative plan and post-apply JSON parsing/invariants;
- TypeScript typecheck;
- full lightweight repository suite: **24 test files passed**;
- post-apply production identity, payload, count, security, and idempotency verification;
- `git diff --check`;
- bounded secret-pattern scan over intended new files.

The known environment workaround was used for test temporary output: a disposable D: workspace directory was used for temporary test files, then removed. No EAS, Gradle, Expo prebuild, Android, APK, or native build tooling was run.

## Production safety declaration

- TfL source observations ingested: **14**, exactly the authorized cohort;
- Batch 1 rows touched: **0**;
- physical-unit promotion: **not authorized and not executed**;
- production mutations outside the authorized 14 source links and 14 observations: **0**;
- RLS/grants changed: **0**;
- migrations applied: **0**;

## Files created / changed

- `tools/source_expansion/tfl_existing_parent_observation_apply.py`
- `tools/source_expansion/test_tfl_existing_parent_observation_apply.py`
- `docs/data/RELIEF_TFL_EXISTING_PARENT_OBSERVATION_APPLY_PLAN_2026-08-22.json`
- `docs/data/RELIEF_TFL_EXISTING_PARENT_OBSERVATION_POST_APPLY_2026-08-22.json`
- `docs/data/RELIEF_TFL_EXISTING_PARENT_OBSERVATION_INGESTION_2026-08-22.md`

The protected files remain outside this transaction.

## Git result

The five files above are the only intended transaction files. They will be committed separately from the starting checkpoint and pushed normally to `codex/toilet-map-apply-1a-production-deploy`; the final commit SHA and local/remote comparison are recorded in the transaction handoff.

## Final classification

**RELIEF TFL EXISTING-PARENT OBSERVATION INGESTION — 14 SOURCE OBSERVATIONS APPLIED / PHYSICAL-UNIT PROMOTION NOT AUTHORIZED**

Further TfL physical-unit adjudication or promotion remains a separate future transaction.

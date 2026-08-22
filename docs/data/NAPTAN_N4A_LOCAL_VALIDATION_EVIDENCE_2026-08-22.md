# NaPTAN N4A — local validation evidence

## Scope

Validation uses committed small JSON fixtures and static inspection of the candidate migration. The 578 MB N3 XML was not refreshed, copied, normalized, or committed.

## Checks

- N4A focused Python tests: deterministic source identity, duplicate rejection, multi-parent preservation, unresolved references, cycle quarantine, source-order independence, geometry-origin separation, replay idempotency, snapshot diff, migration security, scale estimates, and no production mutation surface.
- Python compilation: `python -m py_compile tools/source_expansion/naptan_n4a.py tools/source_expansion/test_naptan_n4a.py`.
- Candidate migration static validation: five expected tables, RLS/revoke/service-role posture, no source/canonical DML, no public policies.
- JSON parsing: fixtures and schema/replay evidence artifacts.
- Repository checks: `git diff --check`, bounded secret-pattern review, migration mutation-pattern review.

## Database validation boundary

No production or live database was used as a schema test. The resulting classification is `STATIC_MIGRATION_VALIDATED / LIVE_DATABASE_VALIDATION_REQUIRED`. A separate authorized deployment batch must validate catalog constraints, indexes, triggers, RLS, grants, and generated types before applying this candidate migration.

## Safety

Production read-only counts were checked before and after repository work. No source rows, source links, facilities, observations, toilets, staging rows, imports, schema objects, RLS policies, or grants were changed.

# Relief NaPTAN N4B.1 — hosted live-database validation report

## STARTING STATE

| Item | Result |
|---|---|
| Repository | hourwise/Relief |
| Branch | codex/toilet-map-apply-1a-production-deploy |
| Starting local SHA | 8627dbfd586df9069b2f73b0cc2d6543645fa950 |
| Starting remote SHA | 8627dbfd586df9069b2f73b0cc2d6543645fa950 |
| Remote verification | git fetch origin hit the known .git/FETCH_HEAD Windows permission error; git ls-remote verified the required remote SHA |
| Final validated commit | 644ff4915d39ec5347b1f51d0accc1de9d7015ca |

No merge, rebase, reset, amend, cherry-pick, or force-push was used. Protected working-tree changes were preserved.

## PROTECTED FILES

The following remained untouched, unstaged, and uncommitted:

- .easignore — pre-existing modified file
- app.json — pre-existing modified file
- docs/EAS_CONFIG_AUDIT.md — pre-existing untracked file

The pre-existing untracked N4B evidence files were retained and updated as part of this evidence transaction. No unrelated starting change was staged.

## SEALED N4A MIGRATION

Candidate: supabase/migrations/20260822170000_naptan_transport_source_graph.sql

SHA-256 before work, in hosted checkout, after all changes, and at final verification:

087A389B8CEAC021B12708BC55C39022CB38D5459510EFFB6CF057CEF232C44E

The sealed migration remained byte-for-byte unchanged. It was executed by the canonical migration mechanism after the historical chain reached it.

## HISTORICAL PRECONDITION ANALYSIS

The previous hosted run stopped at supabase/migrations/20260812190246_seal_apply_1a_execution_path.sql with:

    Apply 1A seal precondition failed: committed approved-manifest rows = 0, expected 1 (SQLSTATE P0001)

The seal’s contract is two separate checks:

1. private.relief_apply_1a_approved_operations must contain exactly the committed 48-operation Apply 1A registry.
2. public.import_runs must contain exactly one qualifying committed Apply 1A run, with the historical source name/file, source checksum, approved plan hash, manifest hash, review identity, engine identity, committed outcome, and the 48 requested/ready/applied and updated counts required by the seal.

The failure was the second condition: the qualifying committed run count was zero. It was not an N4A schema failure.

The required state is reproducible from committed repository evidence. The authoritative inputs are:

- supabase/migrations/20260811164202_apply_1a_audit_and_transaction.sql, which defines the immutable 48-operation registry and source identity;
- tools/enrichment/disposable_apply_1a_fixture.sql and tools/enrichment/disposable_apply_1a_seed.sql, which define the disposable historical data path;
- tools/enrichment/disposable_apply_1a_postcheck_fault.sql, which defines the committed post-check fault used to exercise rollback;
- tools/enrichment/test_apply_1a_sealing.py, which defines the two-run rollback/commit and seal expectations;
- the committed Apply 1A manifest, plan, and sealing evidence under docs/data/.

Therefore Path A was used. No value was guessed, copied from production, retrospectively invented, or obtained with production credentials.

## HOSTED VALIDATION WORKFLOW

.github/workflows/n4b-naptan-live-validation.yml is a manual-only workflow_dispatch validation workflow named N4B NaPTAN Live Validation. It uses ubuntu-latest, a disposable local Supabase stack, PostgreSQL, PostGIS, and read-only GitHub token permissions. It contains no production credentials, no production project configuration, no supabase link, and no remote migration command.

The workflow explicitly hashes the sealed N4A migration before execution. It temporarily holds only the migrations from the historical seal boundary onward, applies the canonical prefix, runs the repository-backed disposable historical bootstrap, restores the migrations, and resumes with the seal migration. The boundary was:

    pre_seal_last_migration=20260812124351_apply_1a_facilities_update_rls.sql
    resume_first_migration=20260812190246_seal_apply_1a_execution_path.sql

No migration was skipped, marked applied, rewritten, or manually patched.

## GITHUB ACTIONS RUN

Final successful run: [N4B NaPTAN Live Validation — run 17 / 32590319699](https://github.com/hourwise/Relief/actions/runs/32590319699)

- Tested commit: 644ff4915d39ec5347b1f51d0accc1de9d7015ca
- Job: 97073021827
- Artifact: [n4b-live-validation-32590319699](https://github.com/hourwise/Relief/actions/runs/32590319699/artifacts/9480182011)
- Artifact ID: 9480182011
- Artifact digest: sha256:6bf987cec5f574480b58059f94c5997f7a8635b6664e4b0cba87eadba80e194a
- Result: success; all 27 workflow steps passed; disposable stack cleanup passed

Materially relevant hosted attempts:

| Run | Commit | Job | First material result |
|---|---|---|---|
| [9 / 32588147118](https://github.com/hourwise/Relief/actions/runs/32588147118) | 563f6adf193f39419f27fb9bbd6521f07ca3a3f4 | 97067555048 | CI plan-byte representation check; no database started |
| [10 / 32588273496](https://github.com/hourwise/Relief/actions/runs/32588273496) | 28d898009a61d39c96488ee07ed78dfedcbe68f6 | 97067859707 | Bootstrap expected 26 disposable facilities, not 25 |
| [11 / 32588505785](https://github.com/hourwise/Relief/actions/runs/32588505785) | f7a09b8726e0b9fa5a1c80ebc832f7c163464fc0 | 97068437577 | Bootstrap expected 26 published facilities, not 25 |
| [12 / 32588745893](https://github.com/hourwise/Relief/actions/runs/32588745893) | 739a402fd3502ab93e94c109d14777b86a26ff93 | 97069088844 | Chain and N4A passed; migration-log filename assertion needed correction |
| [13 / 32588975296](https://github.com/hourwise/Relief/actions/runs/32588975296) | 966d2a18cdedd3dce0d9b2111086639ffe9eafc8 | 97069677334 | Chain/N4A/tooling passed; psql variable inside dollar-quoted block failed |
| [14 / 32589447364](https://github.com/hourwise/Relief/actions/runs/32589447364) | a6c3a6c05d50c900bd670242185541ea68ed131b | 97070799686 | Live harness fixture had six values for eight columns |
| [15 / 32589752664](https://github.com/hourwise/Relief/actions/runs/32589752664) | b37ce56bfa183050ec6f79ee38d19dbd8b344e53 | 97071588485 | Trigger assertion depended on transaction time advancing |
| [16 / 32590047075](https://github.com/hourwise/Relief/actions/runs/32590047075) | 1d28233e0a8b08b2cd3b88630ef94f446ce07178 | 97072334342 | Safety scan matched its own forbidden-pattern literals |

## RUNTIME VERSIONS

| Runtime | Hosted evidence |
|---|---|
| Runner | Ubuntu 24.04.4 LTS, ubuntu-latest |
| PostgreSQL server | 17.6 |
| PostgreSQL client | 16.15 |
| PostGIS | 3.3.7 |
| Supabase CLI | 2.75.0 |
| Node | v22.22.2 |
| Python | 3.12.14 |

## DATABASE BOOTSTRAP

The final run started a fresh disposable Supabase stack, reached PostgreSQL, bootstrapped the runner-local supabase_admin role, and replayed the complete repository migration chain. Generated disposable credentials were not written to evidence or artifacts.

## POSTGIS VERIFICATION

PostGIS was proven active before and after the full chain. Final evidence included:

    PostgreSQL 17.6 on x86_64-pc-linux-gnu, compiled by gcc (GCC) 15.2.0, 64-bit
    POSTGIS="3.3.7 a0c7967" [EXTENSION] PGSQL="170" GEOS="3.14.1-CAPI-1.20.5" PROJ="9.7.1"
    postgis=3.3.7

The live harness also exercised real geography values and PostGIS operators.

## MIGRATION EXECUTION

The canonical prefix completed. The disposable bootstrap reproduced the committed Apply 1A prerequisite, including the exact 48-operation registry, one qualifying historical import run, the two-run rollback/commit history, and the exact historical audit identities. The seal migration passed its own precondition and executed exactly once. The complete remaining chain then executed through supabase/migrations/20260822170000_naptan_transport_source_graph.sql.

The sealed N4A SHA was rechecked after bootstrap and matched exactly.

## LIVE DATABASE ASSERTIONS

tools/source_expansion/naptan_n4b_live_validation.sql completed with:

    N4B_LIVE_SQL_ASSERTIONS_PASSED

The live PostgreSQL/PostGIS run proved the N4A contract’s applicable:

- tables, columns, defaults, generated geography, keys and nullability;
- foreign keys, same-snapshot hierarchy relationships and cross-snapshot rejection;
- unique duplicate protection and invalid-coordinate rejection;
- required indexes, five update triggers, and trigger behavior;
- RLS state, policy/catalog checks, grants, and absence of anonymous/authenticated read access;
- PostGIS geography representation and coordinate behavior;
- source snapshots, StopAreas, StopPoints, memberships, parent edges, unresolved references, and duplicate occurrence counts;
- rollback of expected constraint failures;
- SQL-layer replay/idempotency and preservation of snapshot history.

## PYTHON VALIDATION

- N4A deterministic suite: 14 tests passed, 0 failed.
- Python compilation: passed.

## TYPESCRIPT / JAVASCRIPT VALIDATION

- Node setup and relevant Linux execution succeeded; the local Windows Node EPERM startup issue was not reproduced.
- TypeScript tsc --noEmit: passed.
- Repository JS/TS harness: 24 test files passed, 0 failed.
- Repository lint: 0 errors, 81 warnings. The warnings were pre-existing application lint findings and were not changed in this transaction.

## SECURITY / RLS / GRANTS VALIDATION

The hosted role checks recorded:

    anon=DENIED
    authenticated=DENIED
    service_role=READ_AND_ROLLBACK_WRITE

These were disposable roles only. No production credential, production database connection, production grant, production policy, or production RLS change was used.

## CI CORRECTIONS

Narrow corrections were required and recorded in the run table above:

- normalized the committed Apply plan bytes in memory for its recorded hash;
- corrected disposable facility/published-facility expectations;
- matched the CLI’s migration basename in evidence;
- materialized the generated snapshot ID for PL/pgSQL assertions;
- corrected a malformed synthetic cross-snapshot tuple;
- made the trigger assertion deterministic against transaction-stable NOW();
- prevented the safety scan from matching its own pattern literals.

The sealed N4A migration, all historical migrations, application code, N3 source evidence, and production configuration were not modified.

## FILES CREATED OR MODIFIED

Committed implementation files:

- .github/workflows/n4b-naptan-live-validation.yml
- tools/enrichment/n4b_historical_apply_1a_bootstrap.sql
- tools/source_expansion/naptan_n4b_live_validation.sql

Updated evidence files:

- docs/data/NAPTAN_N4B_HOSTED_VALIDATION_REPORT_2026-08-22.md
- docs/data/NAPTAN_N4B_HOSTED_VALIDATION_EVIDENCE_2026-08-22.json
- docs/data/NAPTAN_N4B_LIVE_DATABASE_VALIDATION_REPORT_2026-08-22.md
- docs/data/NAPTAN_N4B_DATABASE_ENVIRONMENT_2026-08-22.json

## COMMITS

N4B implementation and hosted-validation commits, in order:

- 563f6adf193f39419f27fb9bbd6521f07ca3a3f4 — resume N4B after Apply 1A seal prerequisite
- 28d898009a61d39c96488ee07ed78dfedcbe68f6 — normalize Apply plan bytes
- f7a09b8726e0b9fa5a1c80ebc832f7c163464fc0 — account for disposable Apply control facility
- 739a402fd3502ab93e94c109d14777b86a26ff93 — account for disposable published control
- 966d2a18cdedd3dce0d9b2111086639ffe9eafc8 — match migration filename in hosted evidence
- a6c3a6c05d50c900bd670242185541ea68ed131b — make N4B fixture ID visible inside PL/pgSQL
- b37ce56bfa183050ec6f79ee38d19dbd8b344e53 — correct N4B cross-snapshot fixture
- 1d28233e0a8b08b2cd3b88630ef94f446ce07178 — make N4B trigger assertion deterministic
- 644ff4915d39ec5347b1f51d0accc1de9d7015ca — avoid safety-scan self-match

The final evidence commit is recorded after this report is staged and pushed.

## PUSH STATUS

All implementation commits were pushed normally and non-force to the required branch. The final evidence commit will also be pushed non-force. No merge, rebase, amend, reset, or force-push was used.

## PRODUCTION SAFETY

The following were not performed:

- no production credentials or production database connection;
- no production SQL, supabase link, remote migration, or production apply;
- no production Edge Function, ingestion, RPC mutation, grant, RLS, policy, or migration-ledger change;
- no canonical facility, source observation, or toilet-unit mutation;
- no source promotion, N3 refresh, national XML download/commit, or N4C.

TOTAL PRODUCTION MUTATIONS: 0

## FINAL HASH VERIFICATION

Final sealed N4A migration SHA-256:

087A389B8CEAC021B12708BC55C39022CB38D5459510EFFB6CF057CEF232C44E

## FINAL CLASSIFICATION

LIVE_DATABASE_VALIDATION_PASSED

N4B_VALIDATION_PASSED

N4C_AWAITING_SEPARATE_AUTHORIZATION

TOTAL PRODUCTION MUTATIONS: 0

This result is live disposable PostgreSQL/PostGIS validation only. It does not authorize N4C or any production apply.


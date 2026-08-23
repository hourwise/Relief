# RELIEF NAPTAN N5-R1 — Frozen Source Count Contract Reconciliation

Status: read-only reconciliation completed. No production DML, schema mutation, ingestion, or N6 work was performed.

## Starting state

- Repository: `hourwise/Relief`
- Branch: `codex/toilet-map-apply-1a-production-deploy`
- Starting local and remote SHA: `26bd040a97571837e7747d1c792561a8d75aea2c`
- Production project: `Relief` / `bgwxrxkmyaihplaloely`
- Migration head: `20260822170000`
- `supabase db push --dry-run --linked`: `Remote database is up to date.`
- Production source graph before and after: all five tables at zero rows.
- Application baseline remained: facilities 15,620; facility_sources 15,634; facility_source_observations 14; import_runs 5; toilet_map_import_staging 0; toilet_units 0; toilet_unit_sources 0.

Protected files remained untouched, unstaged, and uncommitted: `.easignore`, `app.json`, and `docs/EAS_CONFIG_AUDIT.md`.

## Frozen source

The disposable cache `C:\Temp\relief-n5\NaPTAN.xml` matched the governed source exactly:

- size: `578,991,782` bytes
- SHA-256: `6FC7E40E2AF3B30E9FD117BDAC313B58F3385BFF26517FD78D5554DA12B4183A`
- UTF-8 XML: replacement characters rejected

The raw XML was not copied into the repository.

## Independent membership methods

Three deterministic methods agreed:

| Method | Raw XML elements | Unique keys | Duplicate extras | Stored rows |
|---|---:|---:|---:|---:|
| A — unchanged committed N3 parser, raw derived as unique plus duplicate extras | 169,530 | 169,527 | 3 | 169,527 |
| B — direct streaming `StopAreaRef` counter | 169,530 | not deduplicated | not deduplicated | not applicable |
| C — independent identity-key frequency counter | 169,530 | 169,527 | 3 | 169,527 |

The invariant is proven:

`169,530 = 169,527 + 3`

The old arithmetic `169,527 - 3 = 169,524` is not supported by the source. It subtracts duplicate extras from a count that was already a unique/set-based count.

## Exact duplicate memberships

Each duplicated key occurs twice, so each has `duplicate_occurrence_count = 2` in the future stored row:

1. `naptan-stop-point:64801285|naptan-stop-area:648G1285` — StopPoint sequence 411,310; reference positions 1 and 2.
2. `naptan-stop-point:64804134|naptan-stop-area:648G221434` — StopPoint sequence 412,887; reference positions 1 and 2.
3. `naptan-stop-point:64804135|naptan-stop-area:648G221434` — StopPoint sequence 412,888; reference positions 1 and 2.

These are exact repeated publisher relationship keys. No valid unique relationship is discarded.

## Root cause and provenance

Classification: `MULTIPLE_DEFECTS`.

The earliest committed occurrence of `169524` is commit `28195ff47b8559ad6c65f7d4866b47f45870560a`, in the original N4A `national_scale_estimate()` hard-coded field `membership_rows_after_exact_duplicate_coalescing`. The upstream N2/N3 artifacts consistently reported 169,527 logical/set-based membership rows, while wording in some reports called that value publisher membership elements. N4A then subtracted the three duplicate occurrences again and recorded 169,524.

The unresolved-reference values were also underspecified: 1,543 and 41 are distinct missing publisher identities, while the edge-row measures are 2,804 and 92.

Historical reports were not rewritten. The N5-R1 contract and corrected planning estimate supersede the ambiguous estimate for future ingestion decisions.

## Unresolved relationships

Memberships:

- unresolved logical membership edges: `2,804`
- distinct missing member-parent identities: `1,543`
- minimum references per missing identity: 1
- maximum: 20
- mean: 1.817239
- median: 2
- identities referenced more than once: 1,120

Parent edges:

- raw parent relationship elements: `3,519`
- unique/logical parent edges: `3,519`
- duplicate parent extras: `0`
- stored parent rows: `3,519`
- unresolved logical parent edges: `92`
- distinct missing area-parent identities: `41`
- minimum references per missing identity: 1
- maximum: 8
- mean: 2.243902
- median: 2
- identities referenced more than once: 33

The full identity-to-reference distributions are in the JSON evidence files.

## N3 invariants

The unchanged N3 parser and projection reproduced:

- StopPoints: 436,428
- StopAreas: 97,270
- normalized complexes: 93,751
- single-area complexes: 91,757
- parent-area complexes: 559
- multimodal parent complexes: 1,435
- unresolved area nodes: 93
- multi-parent nodes: 701
- shared-root multi-parent nodes: 73
- cross-complex or unresolved multi-parent nodes: 628
- maximum hierarchy depth: 13
- hierarchy cycles: 0

Mode distribution also matched the established evidence: bus/coach 75,920; multimodal 1,541; no observed mode 13,591; metro/tram/underground 641; rail 1,519; ferry/port 470; air 65; taxi 4.

## Schema representability

Classification: `N4A_SCHEMA_SUPPORTS_CORRECTED_COUNTS`.

The sealed migration and deployed schema support one row per unique membership or parent key, retain total occurrence counts, preserve all multi-parent relationships, and represent unresolved references with raw identities plus nullable resolved UUIDs. The five tables have RLS enabled, no policies, and service-role privileges only; no public, anonymous, or authenticated table grants were added.

Sealed migration SHA-256 remained:

`087A389B8CEAC021B12708BC55C39022CB38D5459510EFFB6CF057CEF232C44E`

## Corrected future N5 contract

- source snapshots: 1
- StopArea/place rows: 97,270
- StopPoint/node rows: 436,428
- raw publisher membership elements: 169,530
- unique membership keys: 169,527
- stored membership rows: 169,527
- duplicate extra occurrences: 3
- raw parent elements: 3,519
- unique/stored parent rows: 3,519
- unresolved membership edges: 2,804
- distinct missing member-parent identities: 1,543
- unresolved parent edges: 92
- distinct missing area-parent identities: 41
- normalized complexes: 93,751
- total stored source-graph rows: `706,745`

The corrected contract is authoritative for a separately authorized N5-R2 ingestion attempt. N5-R1 itself performed no ingestion.

## Regression validation

- N5-R1 synthetic count-semantics tests: passed
- existing N4A tests: passed
- existing N3 tests: passed
- total executed in combined run: 26 tests passed
- Python compilation: passed
- JSON evidence parsing: passed
- sealed migration hash: passed

## Production safety

- `TOTAL PRODUCTION MUTATIONS: 0`
- `TOTAL PRODUCTION SOURCE-GRAPH ROWS: 0`
- `TOTAL SCHEMA MUTATIONS: 0`
- `TOTAL CANONICAL FACILITY MUTATIONS: 0`
- `TOTAL AUTH MUTATIONS: 0`
- no source ingestion
- no canonical facility or toilet mutation
- no N6 work

## Classification

`N5_REAUTHORIZED_CONTRACT_READY`

`N6_CANONICAL_RECONCILIATION_NOT_AUTHORIZED`

N5-R2 requires a new explicit authorization and must use only the corrected contract above.

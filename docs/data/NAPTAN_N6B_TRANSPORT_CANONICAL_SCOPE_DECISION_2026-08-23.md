# RELIEF NAPTAN N6B — Transport Canonical Scope Decision

## Starting state

- Repository: `hourwise/Relief`
- Branch: `codex/toilet-map-apply-1a-production-deploy`
- Starting local SHA: `5ff54eba5ca248d818c9f0ba6af01df98e54ce80`
- Starting remote SHA: `5ff54eba5ca248d818c9f0ba6af01df98e54ce80`
- Production project: `Relief` / `bgwxrxkmyaihplaloely`; analysis path read-only.
- Protected files were preserved and were not staged or committed.

## N6A baseline preserved

The N6A production-backed results remain authoritative and unchanged: 93,751 normalized complexes; 51 proposed canonical matches; 9 ambiguous matches; 4,163 proposed-new analytical rows; and 75,933 supporting/no-action outcomes in the committed N6A classification contract.

Source graph counts remain 1 snapshot, 97,270 places, 436,428 nodes, 169,527 memberships, and 3,519 parent edges (706,745 total). No N6B production DML was executed.

## Mode cohort analysis

| Mode | Complexes | Candidate complexes at 500m | N6A proposed | N6A ambiguous | N6A proposed-new | N6A supporting | N6A no-action | Generic-name complexes |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| rail | 1,519 | 7 | 6 | 1 | 1,503 | 9 | 0 | 0 |
| metro_tram_underground | 641 | 1 | 1 | 0 | 640 | 0 | 0 | 0 |
| multimodal | 1,541 | 38 | 34 | 4 | 1,500 | 3 | 0 | 1 |
| ferry_port | 470 | 7 | 5 | 2 | 462 | 1 | 0 | 0 |
| air | 65 | 7 | 5 | 2 | 58 | 0 | 0 | 0 |
| bus_coach | 75,920 | 545 | 0 | 0 | 0 | 75,920 | 0 | 373 |
| taxi | 4 | 0 | 0 | 0 | 0 | 0 | 4 | 0 |
| no_mode | 13,591 | 49 | 0 | 0 | 0 | 0 | 13,591 | 33 |

The 75,920 ordinary bus/coach complexes remain `SUPPORTING_SOURCE_ONLY`. Mode, scale, or proximity is not toilet evidence. The 4,163 proposed-new population is not an insertion queue.

## 51 proposed and 9 ambiguous cases

The machine-readable review tables contain `51` proposed existing-facility cases and `9` ambiguous cases. Proposed cases are eligible only for a future review; the 9 ambiguous cases require human adjudication. No case was promoted.

Known collision examples are retained: Cockfosters Underground Station has two canonical facilities; Wapping Wharf has two canonical facilities; and Oakwood Underground Station/Oakwood Station compete for one canonical facility. Nearest distance is not used as an automatic tie-breaker.

## Toilet-evidence hierarchy

1. Tier A: direct official toilet evidence may support bounded review of an actual toilet facility or unit.
2. Tier B: existing Relief canonical toilet evidence plus NaPTAN identity may support a future link review.
3. Tier C: strong place reconciliation alone is supporting context.
4. Tier D: proximity/context alone never supports promotion.

## Product policy

NaPTAN transport places are not equivalent to Relief toilet facilities. New canonical transport-related facilities require direct toilet evidence. NaPTAN identity can support reconciliation of an existing canonical facility, but proximity alone is not promotion evidence. Multimodal complexes require subplace-aware review. Ordinary bus stops remain supporting-source-only. Ambiguous cases require human adjudication. Mass transport-place promotion is not authorized.

## Facility versus place model

The current `facilities` entity represents actual public toilet facilities and is not a safe home for 93,751 transport complexes. N6B therefore retains the facility-only write boundary and keeps NaPTAN as private identity/context evidence. A separate canonical place or transport-place entity remains an open product/schema decision; N6B does not implement it.

## TfL decision

The frozen 509-station reproduction remains exact: 47 high-confidence complex matches, 7 high-confidence subplace matches, 104 multimodal matches, 2 ambiguous complexes, 349 no-match, and 0 exact official identifier matches. NaPTAN contributes station/complex identity context; TfL can contribute direct toilet evidence. A station root must not be collapsed into one toilet facility where multiple physical toilets or subplaces exist.

## N6C recommendation

Define N6C as a bounded, read-only/human-adjudication review of exactly the 51 proposed existing-canonical candidates plus the 9 ambiguous collision cases. Exclude all 4,163 proposed-new complexes and ordinary bus/coach stops. Any later facility or provenance write requires a separate authorization.

## Safety and classification

- `PRODUCTION_RECONCILIATION_ANALYSIS_READ_ONLY`
- `TOTAL PRODUCTION MUTATIONS: 0`
- No facilities, facility sources, observations, toilet units, source graph rows, migrations, policies, grants, or schema objects were written.

## Final decision

`RELIEF NAPTAN N6B — TRANSPORT CANONICAL SCOPE DEFINED / NAPTAN RETAINED AS SUPPORTING IDENTITY EVIDENCE BY DEFAULT / MASS TRANSPORT PROMOTION NOT AUTHORIZED / BOUNDED N6C ADJUDICATION SCOPE DEFINED / PRODUCTION UNCHANGED`

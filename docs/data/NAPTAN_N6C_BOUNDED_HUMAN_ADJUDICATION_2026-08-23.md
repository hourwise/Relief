# RELIEF NAPTAN N6C — Bounded Human Adjudication of 60 Cases

## Scope and safety

This is a read-only adjudication-preparation transaction. The case register is derived from the committed N6B 51 proposed existing-canonical cases and 9 ambiguous/collision cases. It does not represent human decisions or production authorization.

- Production project: `Relief` / `bgwxrxkmyaihplaloely` (`ACTIVE_HEALTHY`), region `eu-central-1`.
- Starting checkpoint: `fead5b71aa8e3170733a85f3a49bb1ee23d166c6` local and `fead5b71aa8e3170733a85f3a49bb1ee23d166c6` remote.
- Sealed N4A SHA-256: `087A389B8CEAC021B12708BC55C39022CB38D5459510EFFB6CF057CEF232C44E`.
- `PRODUCTION_WRITE_CAPABILITY = false`; no production DML, DDL, provenance, source-graph, canonical, or migration operation was executed.

## N6A/N6B baseline preserved

The authoritative N6A/N6B source classifications are unchanged: 51 `PROPOSED_CANONICAL_MATCH`, 9 `AMBIGUOUS_CANONICAL_MATCH`, 4,163 proposed-new analytical complexes, and 75,933 supporting/no-action outcomes. N6C excludes the proposed-new and supporting/no-action populations.

The production source graph remains 1 snapshot, 97,270 places, 436,428 nodes, 169,527 memberships, and 3,519 parent edges: 706,745 rows. The normalized projection remains 93,751 complexes; N6C does not persist it.

## Case register

Exactly 60 deterministic cases are registered: 51 proposed existing-canonical cases and 9 ambiguous/collision cases. Each has a stable case ID, frozen source classification, machine recommendation, evidence deficiencies, warnings, and a human decision initialized to `PENDING_HUMAN_REVIEW`.

Machine recommendation counts: `{"PENDING_HUMAN_REVIEW": 3, "RECOMMEND_COLLISION_REVIEW": 9, "RECOMMEND_EXISTING_CANONICAL_LINK": 5, "RECOMMEND_SUBPLACE_REVIEW": 43}`. These are review guidance only; no recommendation is a decision.

The nine ambiguous cases retain all competing candidate/source relationships. Cockfosters, Wapping Wharf, Oakwood, Falkirk Grahamston, Dunoon Ferry Terminal, Canary Wharf, Hillingdon, and North Greenwich remain visible as collision/subplace cases. Nearest distance is explicitly prohibited as a tie-breaker.

## Mode cohort view

| Mode | N6C cases | Direct official toilet evidence | Existing Relief toilet evidence | Machine recommendations |
|---|---:|---:|---:|---|
| rail | 7 | 0 | 7 | `{"RECOMMEND_COLLISION_REVIEW": 1, "RECOMMEND_EXISTING_CANONICAL_LINK": 1, "RECOMMEND_SUBPLACE_REVIEW": 5}` |
| metro_tram_underground | 1 | 0 | 1 | `{"RECOMMEND_COLLISION_REVIEW": 1}` |
| multimodal | 38 | 0 | 38 | `{"RECOMMEND_COLLISION_REVIEW": 5, "RECOMMEND_SUBPLACE_REVIEW": 33}` |
| ferry_port | 7 | 0 | 7 | `{"PENDING_HUMAN_REVIEW": 1, "RECOMMEND_COLLISION_REVIEW": 2, "RECOMMEND_EXISTING_CANONICAL_LINK": 1, "RECOMMEND_SUBPLACE_REVIEW": 3}` |
| air | 7 | 0 | 7 | `{"PENDING_HUMAN_REVIEW": 2, "RECOMMEND_EXISTING_CANONICAL_LINK": 3, "RECOMMEND_SUBPLACE_REVIEW": 2}` |
| bus_coach | 0 | 0 | 0 | `{}` |
| taxi | 0 | 0 | 0 | `{}` |
| no_mode | 0 | 0 | 0 | `{}` |

Ordinary bus/coach stops remain outside N6C. The 4,163 proposed-new transport places are not a promotion backlog. NaPTAN identity is context and reconciliation evidence, not proof that a transport root is a toilet facility.

## Evidence policy

1. Direct official toilet evidence may support bounded review of an actual toilet facility or unit.
2. Existing Relief canonical toilet evidence plus NaPTAN identity may support review of an existing facility relationship.
3. Strong transport-place reconciliation alone remains supporting context.
4. Proximity/context alone never supports canonical promotion.

Rail, metro/Underground/tram, ferry/port, and air cases retain mode-specific warnings. Multimodal cases require subplace-aware review; a station, interchange, or terminal root is not collapsed into one physical toilet location.

## TfL cross-evidence

The frozen 509-station reproduction remains exact: 47 high-confidence complex, 7 high-confidence subplace, 104 multimodal, 2 ambiguous, and 349 no-match; exact official identifier matches remain 0 and 28 N2 ambiguities remain resolved. Existing 14 TfL observations are unchanged.

NaPTAN can supply station/complex identity context. TfL can supply direct toilet evidence. Neither source authorizes representing an entire complex as one toilet facility when multiple physical locations or units exist.

## Facility versus place boundary

The current product boundary remains: retain facility-only canonical writes for now and keep NaPTAN as private source/context evidence. `facilities` should not be overloaded with 93,751 transport complexes. A separate place/transport entity would require a distinct product/schema authorization and is not implemented here.

## Human adjudication boundary

Human review is required for source-to-multiple-facility collisions, multiple source complexes claiming one facility, multimodal root/subplace uncertainty, generic or token-subset-only names, nearby-but-separate toilet locations, and conflicting authoritative evidence. No reviewer identity, timestamp, rationale, approval, or rejection has been fabricated.

## N6C outputs and next boundary

The JSON case register and human-review queue are the deterministic evidence. All 60 cases remain `PENDING_HUMAN_REVIEW` and `REVIEW_ONLY_NOT_AUTHORIZED`. The smallest next transaction is a separately authorized human adjudication review of these 60 cases; any production promotion would require another explicit authorization and must remain separate from this preparation batch.

## Final classifications

- `N6B_SOURCE_CLASSIFICATION_PRESERVED`
- `N6C_CASE_REGISTER_COMPLETE`
- `N6C_MACHINE_RECOMMENDATIONS_COMPLETE`
- `N6C_HUMAN_DECISIONS_PENDING`
- `N6C_PRODUCTION_READ_ONLY`
- `N6C_NO_CANONICAL_PROMOTION`
- `N6C_NO_NEW_TRANSPORT_PLACES`
- `N6C_NO_SOURCE_GRAPH_MUTATION`
- `N6C_BOUNDED_HUMAN_REVIEW_READY`

`TOTAL PRODUCTION MUTATIONS: 0`

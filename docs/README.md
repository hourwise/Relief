# Relief — Documentation Index

**Last updated:** 2026-07-12  
**Verification scope:** Full repository audit of `relief-app/` source code, configuration, and migrations

---

## Source of Truth Hierarchy

The following documents are authoritative for the Relief project. When documents disagree, follow this precedence order:

| Priority | Document | Owns |
|----------|----------|------|
| 1 | `docs/CURRENT_STATE.md` | What exists right now |
| 2 | `docs/ARCHITECTURE.md` | How the system is and will be structured |
| 3 | `docs/FEATURE_MATRIX.md` | Per-feature implementation evidence |
| 4 | `docs/DATA_MODEL.md` | Intended database schema and backend objects |
| 5 | `docs/ROADMAP.md` | Planned development sequence |
| 6 | `docs/DECISIONS_NEEDED.md` | Open product and technical decisions |
| 7 | `docs/SECURITY_PRIVACY_AND_TRUST.md` | Security, privacy, trust requirements |
| 8 | `docs/ACCESSIBILITY_AND_UX.md` | Accessibility policy and implementation gaps |
| 9 | `docs/BACKEND_INTEGRATION_PLAN.md` | Staged backend integration plan |
| 10 | `docs/ACCOUNTS_AND_ENVIRONMENT.md` | Service accounts and environment variables |
| 11 | `docs/TESTING_AND_RELEASE.md` | Quality gates and release strategy |
| 12 | `docs/CONTRADICTION_REGISTER.md` | Resolved and open contradictions |
| 13 | `docs/DOC_PASS_REPORT.md` | This documentation pass report |
| 14 | `docs/archive/` | Historical, non-authoritative material |

---

## Required Reading Order

### For new developers and coding agents

1. **`README.md`** (root) — What Relief is and its current status
2. **`docs/README.md`** (this file) — Documentation map
3. **`docs/CURRENT_STATE.md`** — Honest assessment of what exists
4. **`docs/ARCHITECTURE.md`** — Current and target architecture
5. **`docs/DECISIONS_NEEDED.md`** — What still needs deciding

### Before implementing any feature

1. **`docs/CURRENT_STATE.md`** — Verify current status
2. **`docs/FEATURE_MATRIX.md`** — Check the feature's actual state
3. **`docs/ARCHITECTURE.md`** — Understand boundaries
4. **`docs/DECISIONS_NEEDED.md`** — Check for unresolved decisions affecting the feature

### Before connecting backend services

1. **`docs/BACKEND_INTEGRATION_PLAN.md`** — Staged integration plan
2. **`docs/ACCOUNTS_AND_ENVIRONMENT.md`** — Required accounts and variables
3. **`docs/DATA_MODEL.md`** — Database schema to deploy
4. **`docs/SECURITY_PRIVACY_AND_TRUST.md`** — Security requirements

---

## Guidance for Coding Agents

1. **Read before coding.** Start with `README.md`, this file, `CURRENT_STATE.md`, `ARCHITECTURE.md`, and `DECISIONS_NEEDED.md`.
2. **Do not trust filenames or comments alone.** A screen or service file may exist without the backend it depends on. Verify against `FEATURE_MATRIX.md`.
3. **UI implementation ≠ feature completion.** Many features have UI surfaces but depend on unavailable backend infrastructure.
4. **Check feature flags.** `src/utils/env.ts` disables ADVANCED_FILTERS, PREMIUM, AI, and EUROPE features. Do not enable them without meeting their acceptance gates.
5. **Do not connect external services** without completing the decisions and account setup in `DECISIONS_NEEDED.md` and `ACCOUNTS_AND_ENVIRONMENT.md`.
6. **Never expose secrets.** Use `EXPO_PUBLIC_*` only for values safe in the client bundle. Server-only secrets belong in Edge Functions or backend environment.
7. **Consult Expo SDK v56 docs** at `https://docs.expo.dev/versions/v56.0.0/` before changing Expo APIs.
8. **Update documentation** when implementation status changes, especially `CURRENT_STATE.md` and `FEATURE_MATRIX.md`.
9. **`docs/archive/` is historical only.** Do not use archived documents for implementation decisions.
10. **Preserve urgent-use accessibility.** The "Need One Now" journey must remain fast and require no account.

---

## Status Vocabulary

| Term | Meaning |
|------|---------|
| **VERIFIED** | Exercised successfully with evidence |
| **UI IMPLEMENTED** | Interface exists, full workflow unproven |
| **CLIENT LOGIC IMPLEMENTED** | Local deterministic logic exists |
| **MOCKED** | Uses sample, hardcoded, simulated or fallback data |
| **PROTOTYPE** | Demonstrates an approach, not production-grade |
| **BACKEND-DEPENDENT** | Requires unavailable database/storage/function/webhook infrastructure |
| **BLOCKED** | Cannot proceed until external dependency resolved |
| **PLANNED** | Documented intent, no meaningful implementation |
| **DEFERRED** | Intentionally outside current release scope |

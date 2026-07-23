# Expo HAS CHANGED

Read the exact versioned docs at https://docs.expo.dev/versions/v56.0.0/ before writing any code.

---

# Relief Project — Agent Instructions

Before any implementation work on this project, you MUST read these documents in order:

1. **`README.md`** (repository root) — Project overview and current status
2. **`docs/README.md`** — Documentation index and source-of-truth hierarchy
3. **`docs/CURRENT_STATE.md`** — Honest assessment of what exists right now
4. **`docs/ARCHITECTURE.md`** — Current and target architecture
5. **`docs/DECISIONS_NEEDED.md`** — Open decisions that may affect your work

## Critical Rules

1. **UI implementation ≠ feature complete.** A screen or service file may exist without the backend it depends on. Always check `docs/FEATURE_MATRIX.md` before assuming a feature works.
2. **`docs/archive/` is non-authoritative.** Archived documents are historical only. Do not use them for implementation decisions.
3. **Feature flags matter.** `src/utils/env.ts` disables ADVANCED_FILTERS, PREMIUM, AI, and EUROPE. Do not enable these without meeting their acceptance gates.
4. **Do not connect external services** without completing the decisions and account setup in `DECISIONS_NEEDED.md` and `ACCOUNTS_AND_ENVIRONMENT.md`.
5. **Never expose secrets.** `EXPO_PUBLIC_*` variables are bundled with the app. Server-only secrets go in Edge Functions or backend environment.
6. **Preserve urgent-use accessibility.** The "Need One Now" journey must remain fast and require no account.
7. **Update documentation** when implementation status changes — especially `CURRENT_STATE.md` and `FEATURE_MATRIX.md`.
8. **Consult Expo SDK v56 docs** at the URL above before changing Expo APIs.
9. **Use the status vocabulary** from `docs/README.md` (VERIFIED, UI IMPLEMENTED, MOCKED, BACKEND-DEPENDENT, BLOCKED, PLANNED, DEFERRED). Never use "Complete", "Built", or "✅" unless a feature is genuinely VERIFIED end-to-end.
10. **This is a pre-backend prototype.** No Supabase project, mapping API key, RevenueCat account, or any external service is connected. Do not write code that assumes otherwise.

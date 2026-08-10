# Relief — Hidden feature audit

**Audit date:** 2026-08-08  
**Scope:** Screens retained in `src/screens/` but intentionally not registered
in the reachable navigator.

The rule for this preview build is simple: a feature is exposed only when its
current data, dependencies, and user-facing promise work together. Source
existence is not evidence that a feature is safe to expose.

| Feature | Current implementation state | Dependencies | Current-data compatibility | Safe to expose now? | Reason |
|---|---|---|---|---|---|
| Saved Profiles | UI IMPLEMENTED; CLIENT LOGIC IMPLEMENTED | Supabase `saved_profiles`, FiltersContext, saved-profile service | No. Presets still refer to quiet, grab rails, family rooms, single occupancy, minimum rating, and other fields that are unpopulated or deliberately hidden from public filters | No | Leave hidden until redesigned against the truthful filter model and applying a saved profile is verified end to end |
| Notification Alerts | UI IMPLEMENTED; CLIENT LOGIC IMPLEMENTED | Supabase temporary reports, AsyncStorage, foreground polling | Partly. Reports exist, but there is no background push/server-triggered alert path | No | The current screen would imply persistent alerts while the implementation stops with the app or relies on foreground polling |
| Offline Maps | UI IMPLEMENTED; CLIENT LOGIC IMPLEMENTED | Supabase download, `expo-sqlite` | No. It stores facility JSON only; it does not download map tiles or render an offline map | No | Rename/reframe as offline facility data before any user exposure |
| Location Sharing | UI IMPLEMENTED; MOCKED (what3words); CLIENT LOGIC IMPLEMENTED (Plus Code) | what3words API or Plus Codes, native sharing | No for the current what3words path. The service can return simulated words without a real API key | No | Simulated location words are a safety risk; require real provider setup or remove that path |
| Smart Recommendations | UI IMPLEMENTED; CLIENT LOGIC IMPLEMENTED | Supabase facilities, local deterministic scoring, saved profiles | Partly. It is not model-backed AI and depends on the stale saved-profile model | No | `AI` is disabled and the current label would overclaim capability; redesign as honest Smart Recommendations later |
| Predictive Suggestions | UI IMPLEMENTED; CLIENT LOGIC IMPLEMENTED | Route planning, facility data, local scoring | No. Route planning is straight-line only and not road-aware | No | Requires a real route model and a truthful product name |
| Route Planning | UI IMPLEMENTED; CLIENT LOGIC IMPLEMENTED | Facility lookup/geocoding, Haversine calculations | No. It produces estimates and interpolated straight-line paths, not walking routes | No | A road-routing provider is not selected; Google Maps remains the walking-route hand-off |
| Premium / Paywall | UI IMPLEMENTED; BLOCKED | RevenueCat keys, products, webhook, subscription state | No. RevenueCat is not configured and the feature flag is false | No | No purchase or entitlement surface is exposed until external setup and verification are complete |

## Result

All audited screens remain hidden from the three primary tabs. The Home,
Find, and Profile pass does not register historic prototype routes or add
buttons that would navigate to them. Reconsider a row only after its data
model, external dependencies, and acceptance evidence are updated together.

# Relief pre-pause readiness and recovery capture

**Date:** 2026-08-20  
**Branch:** `codex/toilet-map-apply-1a-production-deploy`  
**Build-readiness commit:** `36de2101be6462a8036ac4e2d0d9a7b8b1f884fa`  
**Production project:** `Relief` / `bgwxrxkmyaihplaloely`

This is the current consolidation overlay. Earlier phase documents remain
historical evidence; this document records the state to recover after a
planned pause.

## Production data checkpoint

The current production project is `ACTIVE_HEALTHY` in `eu-central-1`, running
Postgres 17.6.1.127. Read-only verification recorded:

| Measure | Value |
|---|---:|
| Facilities | 15,620 |
| Facility-source rows | 15,620 |
| Import runs | 5 |
| Toilet Map import staging rows | 0 |
| Published facilities | 15,620 |
| Current Toilet Map UK links | 15,620 |
| Data mutations in this consolidation batch | 0 |

The final optional data review found no separately frozen exact operation
manifest. The nine published unusable-name records remain manual-review
items; no broad cleanup or inferred correction was applied. See
[`TOILET_MAP_FINAL_OPTIONAL_DATA_REVIEW.md`](data/TOILET_MAP_FINAL_OPTIONAL_DATA_REVIEW.md).

The completed source lineage and checksums are preserved in the committed
Refresh 2 and Apply 2B artifacts. The ignored raw/content-addressed source
cache is not part of the repository or publication set.

## Test and APK readiness

- `npm.cmd run verify`: **PASS** — typecheck, lint with warnings only, and all
  21 test files passed.
- Expo Doctor: **21/22 checks passed** after aligning the five SDK 56 patch
  dependencies. The remaining check is the known Hermes V1 memory regression,
  which would require SDK 57 / React Native 0.86.2 and is intentionally not
  part of this bounded pause batch.
- Expo public config resolves to package `com.relief.app`, scheme `relief`,
  owner `pcgsoft`, and EAS project
  `6295bbe4-47b2-4fc2-8d47-cdf9fc15f6c2`.
- The EAS `preview` environment contains the three required public client
  variable names. Their values are intentionally not recorded here.
- EAS build `dbd8c240-3a77-4656-b726-c2c8bfc48736` was submitted from the
  build-readiness commit using Node `22.22.2`, the preview APK profile, and
  the remote Android keystore. Its artifact and physical-device result are
  pending this capture's final update.

The build is an internal preview/test artifact, not a store-release claim.
The EAS keystore certificate and Google Maps key restrictions still require
the normal owner-controlled verification on the device/build being tested.

## Pause and recovery checklist

Before pausing Relief backend development:

1. Keep the branch SHA, all committed migrations, and the `docs/data/` source,
   reconciliation, manifest, and execution evidence together.
2. Keep the EAS preview environment configured outside the repository. Never
   commit `.env` contents, Supabase service-role credentials, database
   passwords, access tokens, refresh tokens, JWTs, or private user data.
3. Keep the raw source cache ignored. Recovery requires the recorded source
   URL, version, licence, and SHA-256 plus a newly verified download; it does
   not require force-adding the cache.
4. Treat Apply 1A, Apply 2A, and Apply 2B as closed generations. Do not reuse
   their operation identity or reopen their execution mechanisms.
5. On a future restore, confirm the project is healthy, run the read-only
   count/source-link checks above, and compare against the committed evidence
   before any new authorization is considered.
6. Do not treat a restored project or a successful APK launch as evidence that
   authenticated writes, Storage, OAuth, RevenueCat, remote push, moderation
   workflows, or legal/public account-deletion contracts are verified.

No Supabase pause operation was performed by this batch. The project remains
available so that pausing, if desired, remains an explicit owner-controlled
operational decision rather than an accidental side effect of preparation.

## Supabase security advisories retained

The read-only security-advisor check reports pre-existing notices, including
RLS disabled on `public.spatial_ref_sys`, RLS-enabled tables without policies,
mutable function search paths, and publicly executable security-definer
functions. These were not changed in this consolidation batch. Any RLS
remediation must be designed with its required policies first; enabling RLS
without policies can block intended access.

## Concurrent local work preserved

The following user-owned files remain outside this batch and were not edited:

```text
M .easignore
M app.json
?? docs/EAS_CONFIG_AUDIT.md
```

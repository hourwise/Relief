# Relief Release Preparation Phase B - Android debug recovery and authenticated-flow readiness

**Audit date:** 2026-08-12

This is a historical Phase B snapshot. The current account-deletion state is
recorded in `ACCOUNT_DELETION_CONTRACT.md` and
`ACCOUNT_DELETION_RELEASE_READINESS.md`.
**Branch:** `codex/toilet-map-apply-1a-production-deploy`
**Phase A checkpoint:** `c9d228f3e796741024eedcd31981149a65b0379c`
**Production boundary:** preserved. No migration, Apply invocation, policy or grant change, production write, account creation, upload, deletion, Storage change, or auth configuration change was performed.

## Outcome

The app-side integration contract work is checkpointed and validated. The
badge award is treated as an optional side effect: a denied or unavailable
`user_badges` insert cannot turn a successful report or facility submission
into a failed primary operation. Focused regression coverage, the full test
harness, TypeScript, and changed-file lint checks pass.

The Android debug APK gate is blocked by the local Gradle toolchain. The
current ignored Android tree and a clean Expo SDK 56 prebuild have identical
Gradle configuration files, and both reproduce the same React Native Gradle
plugin Kotlin DSL error. No arbitrary Gradle, AGP, Kotlin, React Native, or
New Architecture workaround was applied.

## Authenticated-flow evidence boundary

The current read-only production evidence classifies the following as
`CATALOG_COMPATIBLE_NOT_LIVE_WRITE_TESTED`: published facility reads; the
nearest-facility RPC; authenticated owner flows for favourites, user profiles,
temporary reports, correction requests, facility submissions, rate limits,
access codes, and review reports; and the catalog-compatible saved-profiles
table, which is unreachable while disabled. Subscription events remain
server-write-only and premium remains disabled.

This is compatibility evidence, not proof from a live authenticated write.
No user was created, no production sign-in was performed, and no production
write was attempted.

The badge side effect is `BLOCKED_BY_RLS`: the current evidence shows no
authenticated INSERT policy for `user_badges`. The client now logs and
absorbs both returned Supabase errors and thrown errors from that optional
award operation. Photo upload is `BLOCKED_BY_STORAGE_INFRASTRUCTURE`: storage
bucket count and storage object policy count are zero, so the path remains
unreachable and was not enabled.

Generated database types remain refresh-blocked because `SUPABASE_DB_URL` was
not available. The approved generator was not bypassed and
`src/types/database.types.ts` was not manually edited. The app-side typed
contract builders use the checked-in generated types and TypeScript passes.

## Android reproduction record

Environment:

- Node `v24.12.0`; npm `11.6.2`.
- JDK `17.0.17` (Microsoft OpenJDK).
- Expo `~56.0.19`; React Native `0.85.3`; React Native Gradle plugin `0.85.3`.
- Gradle wrapper `9.3.1`.
- Process `GRADLE_USER_HOME` points to `C:\Users\USER\scoop\apps\gradle\current\.gradle`.

Current-tree command:

```text
android\gradlew.bat -p D:\Users\fleur\Nicola App\relief-app\android :app:assembleDebug -PreactNativeArchitectures=arm64-v8a --stacktrace --no-daemon
```

Result: `BUILD FAILED`. The failure is in
`node_modules/@react-native/gradle-plugin/settings.gradle.kts:16`; Gradle's
Kotlin DSL reports unresolved references for the standard `plugins` and `id`
calls in `org.gradle.toolchains.foojay-resolver-convention`.

Clean-prebuild comparison:

- `npx expo prebuild --platform android --no-install` succeeded in a disposable copy with no `android/` directory.
- The generated `settings.gradle`, root/app Gradle files, `gradle.properties`, and wrapper properties are byte-for-byte identical to the current ignored Android tree.
- The local manifest is the only compared difference; it contains local Maps configuration while the clean copy has no secret-backed key.
- The clean generated project reproduces the same Kotlin DSL failure at the same React Native plugin line after its dependency junction is restored.

Because clean prebuild does not remove the failure and there is no important
tracked native difference to preserve, the ignored Android tree was not
regenerated and no debug APK was produced. The local `GRADLE_USER_HOME`
configuration/cache requires environment-owner repair or an equivalent
approved toolchain fix before retrying the APK gate.

## Validation

- `npx.cmd tsc --noEmit --pretty false --incremental false` - PASS.
- Focused non-fatal side-effect regression test - PASS, 5 assertions.
- Full `node tools/run-tests.mjs` - PASS, all 13 test files.
- Direct changed-file ESLint - PASS, 0 errors; 4 pre-existing warnings in `community.ts`.
- `git diff --check` - PASS before checkpoint commit.
- Expo SDK 56 clean prebuild - PASS.
- Current and clean `:app:assembleDebug` - BLOCKED by the Gradle/Kotlin DSL failure above.

## Release classification

| Gate | Classification |
|---|---|
| Phase A app contract checkpoint | VERIFIED at source/test level |
| Badge primary-flow resilience | VERIFIED at source/test level; award itself BLOCKED_BY_RLS |
| Authenticated production writes | CATALOG_COMPATIBLE_NOT_LIVE_WRITE_TESTED |
| Photo upload | BLOCKED_BY_STORAGE_INFRASTRUCTURE |
| Generated type refresh | BLOCKED by missing server-only `SUPABASE_DB_URL`; generated file untouched |
| Android debug APK | BLOCKED by local Gradle/Kotlin DSL toolchain state |
| Public release | BLOCKED by Android APK gate plus unresolved account-deletion/privacy contract |

No release signing, EAS, Play submission, merge, tag, or production backend
change is authorized by this phase.

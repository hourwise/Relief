# Relief Phase G — Feature completion and test-build readiness

Date: 2026-08-14

Phase G is source/test readiness work only. The user has stopped local Android/Gradle/APK work on this desktop because the system drive is accumulating repeated Android and Gradle files. Do not run `tools/build-android-debug.ps1`, `expo run:android`, Android Studio builds, or EAS from this phase without explicit renewed instruction.

## Source completion delivered

- Canonical 42-feature inventory: [`FEATURE_TEST_READINESS.md`](./FEATURE_TEST_READINESS.md).
- Password reset: email entry, safe success state, `resetPasswordForEmail`, `relief://auth/callback`, recovery event/deep-link handling, new password form, `updateUser`, safe expired/invalid-link state, and contract tests.
- Account deletion: Profile → Delete account → explanation → typed confirmation → destructive reconfirmation. Test mode simulates only; production returns `ACCOUNT_DELETION_NOT_CONFIGURED`.
- QA Feature Lab: opt-in only through `EXPO_PUBLIC_RELIEF_TEST_MODE=true`; default false. It exposes advanced filters, saved profiles, route estimate, offline facility data, local alerts, premium UI, photo adapter, deletion adapter, and legal state.
- Adapter boundaries: photo storage and account deletion never report fake production success; premium test mode unlocks presentation only; remote push and RevenueCat remain unavailable.
- Misleading “Offline Maps” language is renamed to offline facility data. Route planning is labelled as a straight-line estimate and does not claim road-aware navigation.
- Navigation contract tests cover the Feature Lab routes; auth-error, recovery-link, and adapter tests were added.

## Current source-level gate results

- `npm.cmd run typecheck`: PASS.
- `npm.cmd test`: PASS — all 16 test files passed.
- Focused ESLint on changed source: PASS with 0 errors and 16 warnings; the remaining warnings are primarily existing hidden-feature unused imports/React Compiler warnings.
- `npx.cmd expo-doctor`: PASS — 21/21 checks.
- `npm.cmd run config`: PASS — Expo SDK 56, scheme `relief`.
- `git diff --check`: PASS.
- Read-only `npm audit`: 27 total vulnerabilities, 8 moderate, 19 high, 0 critical. No audit fix was run.

## EAS preview profile requirements

The existing `eas.json` `preview` profile is an internal Android APK profile. Before a cloud build, configure the Expo project/account deliberately and provide preview environment values through EAS secrets/environment configuration, not committed files:

- `EXPO_PUBLIC_SUPABASE_URL`
- `EXPO_PUBLIC_SUPABASE_ANON_KEY`
- `EXPO_PUBLIC_GOOGLE_MAPS_API_KEY`
- `EXPO_PUBLIC_RELIEF_TEST_MODE=true` only for a disposable QA build; use false for a normal preview.
- RevenueCat keys remain absent until the RevenueCat product and entitlement contract is approved; do not enable premium production behavior by adding speculative credentials.

`EXPO_PUBLIC_*` values are bundled into the app. No service-role key belongs in EAS or the client. Confirm the Supabase Auth redirect allow-list contains `relief://auth/callback` before testing password recovery or OAuth.

## Explicitly not verified in this phase

No local APK was produced, installed, or tested after the Phase G source changes. Physical-device testing in Android Studio and the cloud EAS build are the next verification stages. Live password-mail delivery, OAuth, user-owned RLS writes, review writes, Storage/moderation, RevenueCat, remote push, legal endpoints, and generated database types remain externally blocked as classified in the canonical inventory.

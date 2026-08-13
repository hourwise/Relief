# Relief Release Preparation — Phase E

**Verified:** 2026-08-13  
**Branch:** `codex/toilet-map-apply-1a-production-deploy`  
**Checkout:** `67eabbf496ecf53948998b7e002dd703beaba0cc` (clean before Phase E)

## Scope and root cause

Phase D identified `NORMAL_GRADLE_USER_HOME_CONTAMINATION` as the accepted root-cause class. The normal Scoop-managed Gradle home causes the React Native Gradle settings compilation failure (`Unresolved reference 'plugins'` / `Unresolved reference 'id'`). Phase E kept that home unchanged and used only process-local Gradle and Android SDK variables.

No React Native, Expo, Gradle, AGP, Kotlin, New Architecture, `android/` source/config, or production service configuration was changed.

## Environment

- Node `v24.12.0`
- npm `11.7.0`
- Microsoft OpenJDK `17.0.17`
- React Native `0.85.3`
- Expo `56.0.19` / SDK `56.0.0`
- Android SDK: `C:\Users\USER\AppData\Local\Android\Sdk`
- Android compile SDK: `36`
- Gradle wrapper: `9.3.1`
- Build architecture: `arm64-v8a`

The first build used the empty `D:\tmp\relief-gradle-home-phase-e-20260813` home. The second independent attempt initially used an empty longer path and reached a Windows CMake/Ninja `Filename longer than 260 characters` failure in generated native state. The generated `.cxx` directories were removed, and the independent reproducibility run was repeated from the brand-new short path `D:\g2`; it passed. No caches were copied between homes.

## Gates

| Gate | Result | Evidence |
| --- | --- | --- |
| Locked dependency restore | **VERIFIED** | `npm ci` added 816 packages from `package-lock.json`; npm reported 26 audit findings (8 moderate, 18 high) and deprecation warnings. |
| Tests | **VERIFIED** | `npm test`; all 13 test files passed. Badge optional-side-effect regression passed: 5/5. |
| TypeScript | **VERIFIED** | `npm run typecheck` passed after restoring the locked dependency tree. |
| Expo Doctor | **VERIFIED** | `npx expo-doctor`; 21/21 checks passed. |
| Expo public config | **VERIFIED** | `npm run config`; Android package resolved to `com.relief.app`. Existing public environment values were not reproduced or changed. |
| Current hermetic checkout build | **VERIFIED** | `:app:assembleDebug -PreactNativeArchitectures=arm64-v8a --stacktrace --no-daemon`; `BUILD SUCCESSFUL in 20m 4s`. |
| Independent fresh-home build | **VERIFIED** | Same command from empty `D:\g2`; `BUILD SUCCESSFUL in 28m 24s`. |
| Original Kotlin failure | **VERIFIED ABSENT** | Neither successful build log contains the unresolved `plugins` / `id` error. |
| Helper validation | **VERIFIED** | `tools/build-android-debug.ps1` ran against the actual checkout and exited `0`. |

## Debug APK evidence

- Path: `android/app/build/outputs/apk/debug/app-debug.apk`
- Name: `app-debug.apk`
- Variant: debug
- Application ID: `com.relief.app`
- ABI: `arm64-v8a`
- First successful build size: `87,991,458` bytes
- First successful build SHA-256: `FAAA3B988F0EAF5EB725C8AFC313AD3F2ACB4F195B76822DDCA98203D83B7840`
- Independent successful build size: `80,370,439` bytes
- Independent successful build SHA-256: `7C1E299426DD6C1F455D40430CDA6B4C928FBE7A352F515D16251B92F7CA009C`

The APK is a local debug artifact only. It is not tracked, copied into the repository, or treated as a release-signed artifact. The differing hashes reflect non-byte-identical native/archive packaging; both builds passed the Gradle task, application-ID, variant, and ABI gates.

## Tracked helper

`tools/build-android-debug.ps1`:

- resolves the repository from `$PSScriptRoot`;
- prefers a valid existing `ANDROID_HOME`, otherwise detects `%LOCALAPPDATA%\Android\Sdk`;
- fails clearly when the SDK is absent;
- uses `%LOCALAPPDATA%\Relief\gradle-user-home`, never the Scoop Gradle home;
- sets `GRADLE_USER_HOME`, `ANDROID_HOME`, and `ANDROID_SDK_ROOT` only for its process and child Gradle process;
- runs the repository wrapper for the arm64 debug APK; and
- contains no credentials or global environment mutation.

## Unchanged classifications

- `GENERATED_TYPES = BLOCKED_BY_MISSING_DB_URL`
- `CORE_AUTH_RLS = CATALOG_COMPATIBLE_NOT_LIVE_WRITE_TESTED`
- `BADGES = BLOCKED_BY_RLS_WITH_NON_FATAL_APP_FAILOVER`
- `PHOTO_UPLOAD = BLOCKED_BY_STORAGE_INFRASTRUCTURE`
- Public release remains blocked by the unresolved account-deletion/privacy contract.

Phase E verifies the local hermetic Android debug build path and makes the checkout ready for Android functional testing. It does not verify production services, authenticated writes, storage, notifications, RevenueCat, what3words, EAS, or public release readiness.

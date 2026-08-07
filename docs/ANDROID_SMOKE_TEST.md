# Android Preview Smoke Test

**Status: EXECUTED — 22 of 22 checks PASS.**

**Build under test:** local release APK, `app-release.apk` (48.8 MB),
`com.relief.app` versionCode 1 / versionName 1.0.0, targetSdk 36, `arm64-v8a`,
containing `assets/index.android.bundle` (6.4 MB).
**Device:** Samsung Galaxy S24 Ultra (`SM_S928B`, serial `R5CX13MZ2YF`),
Android 16, physical, over USB.
**Date:** 2026-08-07.
**Metro:** not running at any point — nothing listening on port 8081, verified
before each cold launch. All launches reported `LaunchState: COLD`.
**Fatal exceptions in logcat:** 0.

Six defects were found and fixed during this run; the results below are from the
final build with all six in place. See "Defects found" at the end.

> Signing caveat: this APK is signed with the **debug** keystore, because the
> Expo template's `release` buildType does that by default. It is valid for an
> internal preview but is not a release-signed artifact, and an EAS build will
> have a different certificate. See "Google Maps key verification".

---

## Still outstanding

| Item | Detail |
|------|--------|
| EAS build | Not run. No `projectId` is linked, and the Expo login has two accounts (`hourwiseeu`, `pcgsoft`), so project ownership is an unmade decision. The local APK above was used instead. |
| Google Maps key restrictions | Tiles render on this device, so the key works for the debug certificate. The Cloud Console configuration itself was not inspected — see below. |
| Emulator | Never used. It cannot start on this machine, but **not** for the reason assumed: the log passes the hypervisor check (`Ok: Hypervisor compatibility to run avd: Pixel_7_Pro are met`) and then fails on disk — `FATAL │ Not enough space to create userdata partition. Available: 4949.80 MB … need 7372.80 MB`, with `C:` at 98–99% full. Freeing ~3 GB or pointing `ANDROID_AVD_HOME` at `D:` should unblock it. Not needed now that a physical device works. |
| Signed-in journeys | Every check below was performed **as a guest**. Sign-in, registration and OAuth were not exercised, so favourite persistence, report submission and correction submission are unverified beyond the point where the auth gate correctly intercepts them. |

---

## Producing the APK

### Node version

The Expo SDK 56 EAS build image runs **Node 22**, so local checks should be run
under Node 22 before trusting them as a predictor of an EAS build. `.nvmrc` and
`.node-version` pin `22.22.2`, and `package.json` declares
`engines.node: ">=22.0.0 <25.0.0"`.

The gates recorded in `CURRENT_STATE.md` were run under Node **24.12.0**. They
should be re-run under Node 22 before the first EAS build:

```bash
node --version && npm ci && npm run verify && npx expo-doctor
```

### Option A — EAS preview build (the profile `eas.json` defines)

Requires decisions only the project owner can make:

1. `eas init` — creates the EAS project. **Choose which account owns it**
   (`hourwiseeu` or `pcgsoft`). This writes `extra.eas.projectId` into `app.json`.
2. Create EAS environment variables for the **`preview`** environment. Values
   must never be committed:
   - `EXPO_PUBLIC_SUPABASE_URL`
   - `EXPO_PUBLIC_SUPABASE_ANON_KEY`
   - `EXPO_PUBLIC_GOOGLE_MAPS_API_KEY`
3. Let EAS generate an Android keystore (or supply one).
4. `eas build -p android --profile preview`

The resulting APK is signed by the **EAS-managed keystore**, whose SHA-1 must be
read from `eas credentials` and allowed on the Google Maps key.

### Option B — local release APK (no EAS account needed)

```bash
npx expo prebuild --platform android --clean
```

```bash
cd android && ./gradlew assembleRelease -PreactNativeArchitectures=arm64-v8a --no-daemon
```

Output: `android/app/build/outputs/apk/release/app-release.apk`.

### Use JDK 17 — not Android Studio's bundled JBR

Neither `JAVA_HOME` nor `ANDROID_HOME` is set globally on the development
machine. Set them first:

```powershell
$env:JAVA_HOME = "C:\Program Files\Microsoft\jdk-17.0.17.10-hotspot"
$env:ANDROID_HOME = "$env:LOCALAPPDATA\Android\Sdk"
$env:Path = "$env:JAVA_HOME\bin;$env:ANDROID_HOME\platform-tools;$env:Path"
java -version
```

`java -version` must report **17**, not 25.

> **Android Studio's bundled JBR is JDK 25 and will fail this build.** Under it,
> AGP's native configure tasks abort with
> `Execution failed for task ':react-native-screens:configureCMakeRelWithDebInfo[arm64-v8a]' > WARNING: A restricted method in java.lang.System has been called`
> (and the same for `react-native-worklets`), because JDK 25 enforces
> restricted native access. React Native and the Expo SDK 56 EAS image both
> target Java 17.
>
> In Android Studio, set this explicitly: **Settings → Build, Execution,
> Deployment → Build Tools → Gradle → Gradle JDK → JDK 17**. The IDE otherwise
> defaults to its own JBR and reproduces the failure.

Build **only `arm64-v8a`** unless you need the others. The default
`reactNativeArchitectures=armeabi-v7a,arm64-v8a,x86,x86_64` compiles four ABIs,
which on this machine took 18 minutes and crashed a Gradle worker daemon
(`Failed to run Gradle Worker Daemon`). A modern physical device — including the
S24 Ultra used for this test — is arm64.

If a CMake failure survives the JDK switch:

```powershell
.\gradlew --stop
.\gradlew clean
Remove-Item -Recurse -Force .gradle -ErrorAction SilentlyContinue
.\gradlew assembleRelease -PreactNativeArchitectures=arm64-v8a --no-daemon --stacktrace
```

### Override `GRADLE_USER_HOME` — this machine's is broken

This machine sets, globally:

```
GRADLE_USER_HOME=C:\Users\USER\scoop\apps\gradle\current\.gradle
```

`current` is a scoop symlink to a **different** Gradle version (9.6.1) than the
wrapper the project uses (9.3.1), and scoop repoints it on every upgrade. With
Gradle's user home living inside another version's install directory, the Kotlin
DSL classpath came out wrong and the build failed while merely *compiling*
`node_modules/@react-native/gradle-plugin/settings.gradle.kts`:

```
Unresolved reference 'plugins'.
Unresolved reference 'id'.
```

That error names the `plugins` keyword itself, which is the tell: the settings
script was being compiled without the Settings API on its classpath, not
mis-written. Clearing `~/.gradle` caches does nothing, because that is not the
directory in use.

Override it to the standard location:

```powershell
$env:GRADLE_USER_HOME = "C:\Users\USER\.gradle"
```

Android Studio inherits the broken environment variable, so set this before
launching it, or fix the machine-level variable. Expect a first build after the
change to re-download dependencies (~1.5 GB into `C:`, which is nearly full).

With JDK 17, a single ABI and a corrected `GRADLE_USER_HOME`, a clean build took
**53m 30s**; incremental rebuilds took **3m 29s** and **8m 38s**.

> **Signing caveat.** The Expo template signs the `release` buildType with the
> **debug** keystore (`android/app/build.gradle`: `release { signingConfig
> signingConfigs.debug }`). A local release APK is therefore debug-signed, with
> SHA-1 `84:91:66:28:20:F6:70:39:B9:8E:83:A8:4A:2D:86:68:CF:7B:B1:BE`. This is
> acceptable for an internal preview but is **not** a release-signed artifact,
> and its SHA-1 differs from an EAS build's.

Install and launch with Metro absent, which is what item 22 exists to prove:

```bash
adb install -r android/app/build/outputs/apk/release/app-release.apk
```

---

## Defects found by this run

All six were fixed and the results above are from the rebuilt APK.

| # | Defect | Why it mattered |
|---|--------|-----------------|
| 1 | **The map never moved to the user's location.** `MapView` consumes only `initialRegion`, so updating the hook's `region` recorded the intent without moving the camera. | The map sat on the London startup fallback while facilities were fetched for the user's real position — the badge said "2 facilities nearby" about somewhere else, and none of those markers were on screen. Fixed with a single `cameraTarget` that every programmatic move publishes. |
| 2 | **Network errors leaked a raw exception.** | Offline, the card showed `java.net.UnknownHostException: Unable to resolve host "<project>.supabase.co"` — meaningless to a user, and it published the backend hostname on screen. |
| 3 | **Unrated facilities were shown as zero-rated** on the detail screen. | The dataset stores `0`, not `null`, for "no ratings", so the "is it rated?" test passed and the screen showed "0.0" with stars — while the list said "Not yet rated" for the same facility. |
| 4 | **Search results were unreadable in List view.** | The overlay used `SoftCard`'s translucent glass fill; fine over map tiles, but over the list the rows behind bled through and the first result was illegible. |
| 5 | **"1 facilities nearby".** | The count string had no plural forms. |
| 6 | **Gradle could not build at all** — see the JDK and `GRADLE_USER_HOME` notes above. | Not app code, but it blocked producing an APK entirely. |

## Data-quality finding (not an app defect)

The first Liverpool search result renders as `]`. That is faithful rendering of
real data: the row's `name` is literally `]` (length 1). **9 of the 15,584
published facilities** have a name of two characters or fewer, or no
alphanumeric characters at all:

```sql
SELECT count(*) FROM facilities
WHERE publication_status = 'published'
  AND (length(trim(name)) <= 2 OR name ~ '^[^a-zA-Z0-9]+$');
```

These came in with the Toilet Map UK import. Worth cleaning at source, or
falling back to a placeholder when a name carries no information — but the fix
belongs in the data or in an explicit presentation rule, not in silently
filtering facilities out of results.

## Cosmetic observations (not fixed)

- The map renders in a dark style, following the device theme, which sits oddly
  against the light app chrome. Decide deliberately whether to pin a light map
  style.
- In List view the floating "Need One Now" button overlaps the row beneath it.
  Expected for a floating action button, but it can obscure a row's status
  badge.

## Google Maps key verification — PARTIALLY OUTSTANDING

Tiles rendered on this device with the debug-signed APK, which demonstrates the
key is accepted for that certificate and that Maps SDK for Android is enabled.
The Cloud Console configuration itself was **not** inspected, and the following
still need confirming by hand:

Cannot be checked from this repository; it lives in Google Cloud Console. Confirm
all three before trusting a "tiles render" result:

- [ ] **Maps SDK for Android** is enabled on the project owning the key.
- [ ] Application restriction lists package `com.relief.app`.
- [ ] Application restriction lists the SHA-1 of the keystore that actually
      signed the APK under test — the debug SHA-1 above for Option B, or the
      EAS-managed certificate for Option A. A key restricted only to a different
      certificate produces a blank/grey map with no obvious error in the UI.

If tiles fail to render, capture `adb logcat | grep -i "Google Maps\|Authorization"`
— key-restriction failures are reported there, not on screen.

---

## The 22 required checks

Record PASS/FAIL plus evidence (screenshot filename, or the logcat line) for each.

| # | Check | Result | Evidence |
|---|-------|--------|----------|
| 1 | Native splash appears correctly | **PASS** | Cold launch shows the mint `#F3F8F5` surface with the Relief mark; no white flash, no stretched artwork. `TotalTime: 381–398 ms`. |
| 2 | StartupWelcome exits correctly | **PASS** | Welcome layer dismisses itself once startup resolves and does not reappear on subsequent cold launches. |
| 3 | Signed-out user reaches Find without registering | **PASS** | Fresh install, no session: onboarding → "Explore Nearby" → Find. No login wall anywhere. Onboarding stored against the guest key and did **not** reappear after later cold launches. |
| 4 | Permission-granted path works | **PASS** | Map recentres on the user (Wirral), blue user dot visible, facilities load for that region. |
| 5 | Permission-denied path does not crash | **PASS** | Permission revoked via `pm revoke` + `appops deny`, then "Don't allow" on the dialog. App stayed alive (`pidof` non-empty), **0 fatal exceptions**. Shows "Location is turned off — Relief works without it…" with an **Allow location** action, and the fallback viewport still loaded facilities, so search and browsing remain usable. |
| 6 | Google map tiles render | **PASS** | Real Google tiles with labels and the Google attribution, both in London (fallback) and Wirral. Not a grey grid. |
| 7 | Real facility markers appear | **PASS** | Green `FacilityMarker` pins matching live Supabase rows; clustering confirmed in London (counts 2–11 in cluster bubbles). |
| 8 | Map panning loads the newest viewport | **PASS** | Five rapid consecutive swipes moved the map from London to Kent; facilities for the **final** region (Halstead / Knockholt / Badgers Mount) loaded and the loading state cleared. No stale result won, no stalled load. |
| 9 | Map/List toggle works | **PASS** | Switching preserved location, facilities, filters, search text, sort and the open nearest-facility card. Same facility, same 1.8 km, same "Open now" in both views — one query, two presentations. |
| 10 | List contains no mocked facilities | **PASS** | Live Wirral and Liverpool rows only. No "Central Station Toilets", "City Library Facilities" or "Shopping Centre"; `MOCK_FACILITIES` and `ListScreen.tsx` are deleted from the codebase. |
| 11 | Nearest sorting works | **PASS** | Ascending distance, rendered in km (1.7 km, 2.8 km, 4.5 km). No miles anywhere. |
| 12 | Rating sorting works | **PASS** | "Top rated" with an all-unrated set falls back to alphabetical (Cherry Tree Centre, Leasowe Common, Tam 'O' Shanter Farm, Wallasey…), and each row reads "Not yet rated" rather than 0 stars — unrated sinks, it is not ranked as zero. |
| 13 | Search returns a known Liverpool result | **PASS** | "Liverpool" returned live rows including Toxteth Library and Unnamed Toilet, each labelled Liverpool with "Hours unknown". |
| 14 | Filters using real columns work | **PASS** | "Free" chip active → `Filters (1)` badge, results refetched, every row "Free". No 42703 or other error. |
| 15 | "Need One Now" returns a real facility | **PASS** | As a guest: **Tam 'O' Shanter Farm, Boundary Road — 1.8 km away · approx. 21 min walk · Free · Open now**, urgent marker centred. This is the journey that previously failed outright with `42703`. |
| 16 | RPC failure produces a retryable error, not "no facilities" | **PASS** | With Wi-Fi *and* mobile data disabled (`ping` → "Network is unreachable"), the card read "We could not complete the search" with **Try again**, and the already-loaded list was preserved rather than blanked. It never said "Nothing found within 25 km". |
| 17 | Facility details load from Supabase | **PASS** | Real record: name, town Wirral, "Open now", cost "Free", verification "Source imported", amenities RADAR Key + Baby changing. Unknown values read "Access information unavailable", never "no". Rating icons render correctly beside their values (the `Star`-inside-`Text` fix). |
| 18 | Directions open on Android | **PASS** | "Get directions" launched Google Maps in walking navigation to the facility (32 min walk). `topResumedActivity=com.google.android.apps.maps/com.google.android.maps.MapsActivity`. |
| 19 | Guest attempting to favourite is prompted to sign in | **PASS** | Heart on facility detail raised "Sign in required — Sign in to save favourites to your account." with **NOT NOW** / **SIGN IN**; dismissible, and dismissing left the user where they were. |
| 20 | Offline/network-loss behaviour is understandable | **PASS** (after fix) | Initially leaked a raw `UnknownHostException` including the Supabase hostname. Now reads "No connection. Check your internet and try again." with **Try again**. Note: on Samsung, airplane mode alone leaves Wi-Fi on — `svc wifi disable` + `svc data disable` is required to test this properly. |
| 21 | No visible button produces an unhandled navigation action | **PASS** | Profile exposes exactly three things: Sign In (→ Auth modal), About Relief (→ registered route), and a non-interactive "This is a preview build" note. No AI, route planning, offline maps, alerts, location sharing, saved profiles, badges or paywall entry points. Corroborated by the static route audit below. |
| 22 | Installed APK restarts without Metro | **PASS** | Nothing listening on 8081 at any point. Repeated `am force-stop` + cold relaunch: app starts, recentres, and loads live data. JS is served from the bundled `assets/index.android.bundle`. |

### How to force the item 16 failure

Item 16 is the one most easily faked by a passing-looking screen, so exercise it
deliberately.

> **Never rename or drop the live `find_nearest_facilities` function to test
> this.** A forgotten rename, a dropped connection mid-test, or a second person
> using the app would leave the urgent journey broken for real users. The live
> function stays untouched.

**Option 1 — airplane mode (no rebuild).** Enable airplane mode and tap "Need
One Now". The RPC call fails at the network layer and travels the same
`{ ok: false }` path, so the UI must show the retryable error card. This also
satisfies check 20.

**Option 2 — build-time fault injection.** For the case where the network is
healthy but the RPC is not, `fetchClosestFacility` honours a flag:

```bash
EXPO_PUBLIC_FORCE_NEAREST_FAILURE=true npx expo prebuild --platform android --clean
```

Build a **throwaway** APK with that set, verify the error state, then rebuild
without it. The flag returns a failure rather than throwing, so it exercises the
real path the UI handles rather than a crash path.

It is intentionally **not** gated on `__DEV__`: `__DEV__` is false in a release
APK, so a dev-only guard could never be exercised on the build actually under
test. It is inert unless the value is exactly `"true"` at build time — confirm
it is absent from any APK you intend to distribute.

In both cases the pass criterion is the same: the card reads "We could not
complete the search" with a **Try again** action, and never "Nothing found
within 25 km".

---

## Static audit already completed (item 21 groundwork)

Every `navigation.navigate(...)` target in `src/` was checked against the routes
registered in `src/navigation/AppNavigator.tsx`.

Registered: `Main`, `Auth` (`Login`, `Register`), `AboutRelief`, tabs `Find` /
`Favourites` / `Profile`, and the Find stack `FindHome`, `FacilityDetail`,
`AddFacility`, `ReportFacility`, `CorrectInfo`, `AdvancedFilters`.

All navigation calls from reachable screens resolve to registered routes. The
remaining calls to unregistered routes (`SavedProfiles`, `Paywall`) exist only
inside screens that are themselves unrouted in the preview build
(`AIRecommendationsScreen`, `PredictiveSuggestionsScreen`, and `PremiumGate`,
which is used only by `OfflineMapsScreen`, `RoutePlanningScreen` and
`SavedProfilesScreen`). None is reachable from the tab bar, so no visible button
triggers them. This is a static result and still needs confirming by hand.

`FacilityDetail` from the Favourites tab is addressed through the Find tab
(`navigate('Find', { screen: 'FacilityDetail', … })`) because the route lives in
that tab's stack; navigating to it directly would be an unhandled action.

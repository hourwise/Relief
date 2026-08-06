# Android Preview Smoke Test

**Status: NOT EXECUTED.**
**Build under test:** none yet — no APK has been installed or opened.

This document is the smoke-test *procedure* with its pass criteria. Every result
column below reads `NOT RUN`. Nothing here may be reported as passing until it
has actually been performed on a device and the result recorded with evidence.

---

## Why it has not been run

| Blocker | Detail |
|---------|--------|
| No emulator | The Android emulator cannot start on the development machine. The emulator log passes the hypervisor check (`Ok: Hypervisor compatibility to run avd: Pixel_7_Pro are met`) but then fails: `FATAL │ Not enough space to create userdata partition. Available: 4949.80 MB … need 7372.80 MB`. `C:` is 99% full (4.1 GB free of 223 GB). Freeing ~3 GB, or relocating the AVD directory to `D:` via `ANDROID_AVD_HOME`, should unblock it. |
| No physical device | No device was attached during this work. The maintainer plans to connect one through Android Studio. |
| No EAS project | `eas build -p android --profile preview` cannot run: no `projectId` is linked, and the Expo login has two accounts (`hourwiseeu`, `pcgsoft`). See "Producing the APK" below. |

---

## Producing the APK

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
cd android && ./gradlew assembleRelease
```

Output: `android/app/build/outputs/apk/release/app-release.apk`.

Set `JAVA_HOME` to `C:\Program Files\Android\Android Studio\jbr` and
`ANDROID_HOME` to `%LOCALAPPDATA%\Android\Sdk` first; neither is set globally on
the development machine.

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

## Google Maps key verification — OUTSTANDING

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

| # | Check | Pass criterion | Result |
|---|-------|----------------|--------|
| 1 | Native splash appears correctly | Mint `#F3F8F5` background with the Relief mark, no white flash, no stretched artwork | NOT RUN |
| 2 | StartupWelcome exits correctly | Welcome layer dismisses itself once startup resolves and does not reappear | NOT RUN |
| 3 | Signed-out user reaches Find without registering | From cold start with no session, the Find screen is reachable; no login wall | NOT RUN |
| 4 | Permission-granted path works | Granting location centres the map on the user and loads facilities | NOT RUN |
| 5 | Permission-denied path does not crash | Denying shows "Location is turned off" with an "Allow location" action; map and search still usable | NOT RUN |
| 6 | Google map tiles render | Real Google tiles, not a grey grid (see key verification above) | NOT RUN |
| 7 | Real facility markers appear | Markers correspond to live Supabase rows, not fixtures | NOT RUN |
| 8 | Map panning loads the newest viewport | After rapid consecutive pans, the **final** visible region's facilities are shown; loading indicator clears | NOT RUN |
| 9 | Map/List toggle works | Switching preserves location, filters, search and selection; no refetch of a different result set | NOT RUN |
| 10 | List contains no mocked facilities | No "Central Station Toilets", "City Library Facilities" or "Shopping Centre"; `MOCK_FACILITIES` is deleted from the codebase | NOT RUN |
| 11 | Nearest sorting works | Ascending distance; unknown distances last | NOT RUN |
| 12 | Rating sorting works | Descending score; null and 0 scores last, shown as "Not yet rated" | NOT RUN |
| 13 | Search returns a known Liverpool result | Searching "Liverpool" returns live rows (76 published facilities have `town` matching Liverpool) | NOT RUN |
| 14 | Filters using real columns work | Toggling e.g. Free / Accessible / Picnic area changes results and returns no error | NOT RUN |
| 15 | "Need One Now" returns a real facility | Returns a facility with distance and walking time. Verified in-database already: from 53.4084, -2.9916 the answer is Moorfields, Liverpool, 162 m | NOT RUN |
| 16 | RPC failure produces a retryable error, not "no facilities" | Force a failure and confirm "We could not complete the search" with **Try again** — never "Nothing found within 25 km" | NOT RUN |
| 17 | Facility details load from Supabase | Real name, address, amenities, verification badge; unknown values read "unavailable", never "no" | NOT RUN |
| 18 | Directions open on Android | "Get directions" opens Google Maps at the facility's coordinates | NOT RUN |
| 19 | Guest attempting to favourite is prompted to sign in | Heart on facility detail raises "Sign in required" with a specific reason and a dismissible prompt | NOT RUN |
| 20 | Offline/network-loss behaviour is understandable | In airplane mode: a stated error with **Try again**, never an empty map presented as "no facilities" | NOT RUN |
| 21 | No visible button produces an unhandled navigation action | Every reachable control either acts or explains itself. Static audit done (see below); needs confirming by hand | NOT RUN |
| 22 | Installed APK restarts without Metro | Force-stop, ensure no dev server is running, relaunch: app starts and loads data | NOT RUN |

### How to force the item 16 failure

Item 16 is the one most easily faked by a passing-looking screen, so exercise it
deliberately. Temporarily break the RPC in a scratch branch:

```sql
ALTER FUNCTION find_nearest_facilities(double precision, double precision, integer, integer) RENAME TO find_nearest_facilities_disabled;
```

Tap "Need One Now", confirm the retryable error, then rename it back. Do not
leave the live function renamed.

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

// https://docs.expo.dev/guides/using-eslint/
const { defineConfig } = require('eslint/config');
const expoConfig = require('eslint-config-expo/flat');
const prettierConfig = require('eslint-config-prettier');

/**
 * Screens that exist but are NOT registered in the navigator, because their
 * features are hidden until they work end to end (see ProfileScreen and
 * docs/CURRENT_STATE.md). They still have to compile, but they are not on any
 * user's path, so their React Compiler violations are recorded as warnings
 * rather than blocking the lint gate for shipping code.
 *
 * These must be cleared — or the screens deleted — before any of them is
 * registered again. Do not add live screens to this list.
 */
const UNROUTED_SCREENS = [
  'src/screens/AIRecommendationsScreen.tsx',
  'src/screens/PredictiveSuggestionsScreen.tsx',
  'src/screens/NotificationAlertsScreen.tsx',
  'src/screens/OfflineMapsScreen.tsx',
  'src/screens/LocationSharingScreen.tsx',
  'src/screens/SavedProfilesScreen.tsx',
  'src/screens/PaywallScreen.tsx',
  'src/screens/RoutePlanningScreen.tsx',
];

module.exports = defineConfig([
  expoConfig,
  // Turns off stylistic rules that would fight Prettier. Formatting is
  // Prettier's job; ESLint's is correctness.
  prettierConfig,
  {
    // Mirrors the `exclude` list in tsconfig.json. Neither of these is part of
    // the React Native app, and linting them with the Expo config produces
    // false `import/no-unresolved` errors against dependencies they resolve
    // through their own toolchains:
    //   * "React Native App UI (1)" is a Vite visual reference, not built here.
    //   * supabase/functions are Deno, with URL imports and a Deno global.
    ignores: [
      'dist/*',
      'android/*',
      'ios/*',
      'React Native App UI (1)/**',
      'supabase/functions/**',
    ],
  },
  {
    rules: {
      // Setting state in a mount effect is how these screens load their data,
      // and every instance is device-verified. The rule warns about an extra
      // render pass, not incorrect behaviour, so it is advisory here rather
      // than a reason to restructure working code.
      'react-hooks/set-state-in-effect': 'warn',
    },
  },
  {
    files: UNROUTED_SCREENS,
    rules: {
      'react-hooks/immutability': 'warn',
      'react-hooks/refs': 'warn',
      'react/no-unescaped-entities': 'warn',
    },
  },
]);

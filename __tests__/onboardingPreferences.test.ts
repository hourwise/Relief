import { selectedOnboardingFilters } from '../src/utils/onboardingPreferences';

function assertEqual(label: string, actual: unknown, expected: unknown) {
  if (JSON.stringify(actual) !== JSON.stringify(expected)) {
    throw new Error(`${label}: expected ${JSON.stringify(expected)}, got ${JSON.stringify(actual)}`);
  }
  console.log(`PASS: ${label}`);
}

assertEqual(
  'selected onboarding choices only add true filters',
  selectedOnboardingFilters({ radar: true, babyChanging: false, genderNeutral: true }),
  { requires_radar_key: true, is_gender_neutral: true },
);
assertEqual(
  'skipped choices do not add false filter values',
  selectedOnboardingFilters({ radar: false, babyChanging: false, genderNeutral: false }),
  {},
);

import type { FacilityFilters } from '../types';

/** Only selected preferences are applied; skipped fields remain unfiltered. */
export function selectedOnboardingFilters(preferences: {
  radar: boolean;
  babyChanging: boolean;
  genderNeutral: boolean;
}): Partial<FacilityFilters> {
  const selected: Partial<FacilityFilters> = {};
  if (preferences.radar) selected.requires_radar_key = true;
  if (preferences.babyChanging) selected.has_baby_changing = true;
  if (preferences.genderNeutral) selected.is_gender_neutral = true;
  return selected;
}

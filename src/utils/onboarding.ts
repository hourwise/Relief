import AsyncStorage from '@react-native-async-storage/async-storage';
import type { FacilityFilters } from '../types';

const keyFor = (userId: string) => `relief:onboarding-complete:${userId}`;

export async function hasCompletedOnboarding(userId: string): Promise<boolean> {
  return (await AsyncStorage.getItem(keyFor(userId))) === 'true';
}

export async function completeOnboarding(userId: string): Promise<void> {
  await AsyncStorage.setItem(keyFor(userId), 'true');
}

/** Only selected preferences are applied; skipped fields remain unknown/unfiltered. */
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

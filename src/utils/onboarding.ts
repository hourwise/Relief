// ============================================================
// Project "Relief" — First-run onboarding state
// ============================================================
// Onboarding must not force account creation before discovery, so
// completion is recorded against a guest key when there is no
// session and migrated to the user on sign-in.
// ============================================================

import AsyncStorage from '@react-native-async-storage/async-storage';

export { selectedOnboardingFilters } from './onboardingPreferences';

/** Storage scope used before any account exists. */
export const GUEST_ONBOARDING_KEY = 'guest';

const keyFor = (scope: string) => `relief:onboarding-complete:${scope}`;

export async function hasCompletedOnboarding(scope: string): Promise<boolean> {
  return (await AsyncStorage.getItem(keyFor(scope))) === 'true';
}

export async function completeOnboarding(scope: string): Promise<void> {
  await AsyncStorage.setItem(keyFor(scope), 'true');
}

/**
 * Carry a guest's completed onboarding over to their new account.
 *
 * The guest record is left in place so signing out does not re-trigger
 * onboarding on the same device.
 */
export async function migrateGuestOnboarding(userId: string): Promise<void> {
  if (!userId || userId === GUEST_ONBOARDING_KEY) return;
  const guestCompleted = await hasCompletedOnboarding(GUEST_ONBOARDING_KEY);
  if (!guestCompleted) return;
  if (await hasCompletedOnboarding(userId)) return;
  await completeOnboarding(userId);
}

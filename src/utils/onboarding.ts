import AsyncStorage from '@react-native-async-storage/async-storage';
export { selectedOnboardingFilters } from './onboardingPreferences';

const keyFor = (userId: string) => `relief:onboarding-complete:${userId}`;

export async function hasCompletedOnboarding(userId: string): Promise<boolean> {
  return (await AsyncStorage.getItem(keyFor(userId))) === 'true';
}

export async function completeOnboarding(userId: string): Promise<void> {
  await AsyncStorage.setItem(keyFor(userId), 'true');
}

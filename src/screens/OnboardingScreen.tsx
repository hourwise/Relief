import React, { useState } from 'react';
import { Pressable, SafeAreaView, ScrollView, StyleSheet, Switch, Text, View } from 'react-native';
import { ReliefLogo, PrimaryButton, ScreenBackground, SoftCard, WatercolorMapBackdrop } from '../components';
import { useFilters } from '../context/FiltersContext';
import { borderRadius, colors, spacing, touchTargets, typography } from '../theme';
import { completeOnboarding } from '../utils/onboarding';
import { selectedOnboardingFilters } from '../utils/onboardingPreferences';

interface OnboardingScreenProps { userId: string; onFinished: () => void; }

interface PreferenceRowProps { label: string; description: string; value: boolean; onChange: (next: boolean) => void; }
const PreferenceRow: React.FC<PreferenceRowProps> = ({ label, description, value, onChange }) => (
  <View style={styles.preferenceRow}>
    <View style={styles.preferenceCopy}>
      <Text style={styles.preferenceTitle}>{label}</Text>
      <Text style={styles.preferenceDescription}>{description}</Text>
    </View>
    <Switch
      accessibilityLabel={label}
      accessibilityHint={description}
      accessibilityState={{ checked: value }}
      value={value}
      onValueChange={onChange}
      trackColor={{ false: colors.gray200, true: colors.primaryLight }}
      thumbColor={value ? colors.primary : colors.white}
    />
  </View>
);

export const OnboardingScreen: React.FC<OnboardingScreenProps> = ({ userId, onFinished }) => {
  const { filters, setFilters } = useFilters();
  const [radar, setRadar] = useState(false);
  const [babyChanging, setBabyChanging] = useState(false);
  const [genderNeutral, setGenderNeutral] = useState(false);
  const [saving, setSaving] = useState(false);

  const finish = async (applyPreferences: boolean) => {
    setSaving(true);
    if (applyPreferences) {
      // Merge true selections only. Existing values are never reset to false.
      setFilters({ ...filters, ...selectedOnboardingFilters({ radar, babyChanging, genderNeutral }) });
    }
    await completeOnboarding(userId);
    onFinished();
  };

  return (
    <ScreenBackground>
      <WatercolorMapBackdrop />
      <View style={styles.wash} pointerEvents="none" />
      <SafeAreaView style={styles.safeArea}>
        <ScrollView contentContainerStyle={styles.scrollContent} showsVerticalScrollIndicator={false}>
          <SoftCard style={styles.sheet}>
            <View style={styles.handle} />
            <View style={styles.brandRow}>
              <View style={styles.logoBox}><ReliefLogo size={30} color={colors.white} /></View>
              <Text style={styles.title}>Welcome to Relief</Text>
            </View>
            <Text style={styles.intro}>Find accessible, safe, and comfortable facilities nearby — without friction.</Text>
            <Text style={styles.eyebrow}>YOUR PREFERENCES</Text>
            <PreferenceRow label="RADAR Key facilities first" description="Show facilities that require a RADAR Key." value={radar} onChange={setRadar} />
            <PreferenceRow label="Baby changing needed" description="Show facilities with baby-changing information." value={babyChanging} onChange={setBabyChanging} />
            <PreferenceRow label="Gender-neutral facilities" description="Show facilities with gender-neutral information." value={genderNeutral} onChange={setGenderNeutral} />
            <PrimaryButton title="Explore Nearby" onPress={() => finish(true)} loading={saving} style={styles.exploreButton} />
            <Pressable accessibilityRole="button" accessibilityLabel="Skip preferences for now" onPress={() => finish(false)} style={styles.skip}><Text style={styles.skipText}>Skip for now</Text></Pressable>
          </SoftCard>
        </ScrollView>
      </SafeAreaView>
    </ScreenBackground>
  );
};

const styles = StyleSheet.create({
  wash: { ...StyleSheet.absoluteFill, backgroundColor: 'rgba(243, 248, 245, 0.64)' },
  safeArea: { flex: 1 },
  scrollContent: { flexGrow: 1, justifyContent: 'flex-end', paddingTop: spacing['6xl'] },
  sheet: { borderBottomLeftRadius: 0, borderBottomRightRadius: 0, paddingHorizontal: spacing['2xl'], paddingTop: spacing.md, paddingBottom: spacing['3xl'] },
  handle: { alignSelf: 'center', width: 40, height: 4, borderRadius: borderRadius.full, backgroundColor: colors.border, marginBottom: spacing['2xl'] },
  brandRow: { flexDirection: 'row', alignItems: 'center' },
  logoBox: { width: 46, height: 46, borderRadius: 14, alignItems: 'center', justifyContent: 'center', backgroundColor: colors.primary, marginRight: spacing.md },
  title: { ...typography.h2, color: colors.textPrimary, flex: 1 },
  intro: { ...typography.bodySmall, color: colors.textSecondary, marginTop: spacing.lg, lineHeight: 23 },
  eyebrow: { ...typography.caption, color: colors.textSecondary, fontFamily: 'PlusJakartaSans_700Bold', letterSpacing: 1.1, marginTop: spacing['2xl'], marginBottom: spacing.sm },
  preferenceRow: { minHeight: 68, flexDirection: 'row', alignItems: 'center', paddingVertical: spacing.sm, borderBottomWidth: 1, borderBottomColor: colors.borderLight },
  preferenceCopy: { flex: 1, paddingRight: spacing.md },
  preferenceTitle: { ...typography.label, color: colors.textPrimary },
  preferenceDescription: { ...typography.caption, color: colors.textSecondary, marginTop: 2 },
  exploreButton: { marginTop: spacing['2xl'] },
  skip: { minHeight: touchTargets.minimum, alignItems: 'center', justifyContent: 'center', marginTop: spacing.sm },
  skipText: { ...typography.buttonSmall, color: colors.textSecondary },
});

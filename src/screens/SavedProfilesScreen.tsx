// ============================================================
// Project "Relief" — Saved Profiles Screen (4.1)
// Preference modes: Accessibility, Family, IBS-friendly, Quiet
// NOT health declarations — optional filter presets
// ============================================================

import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TouchableOpacity,
  Alert,
  TextInput,
} from 'react-native';
import { colors, typography, spacing, borderRadius } from '../theme';
import { Button, Card } from '../components';
import {
  getSavedProfiles,
  createSavedProfile,
  deleteSavedProfile,
  getDefaultPreferencesForMode,
  getModeDisplayName,
  getModeIcon,
} from '../services/profiles';
import { useNavigation, NavigationProp } from '@react-navigation/native';
import { PremiumGate } from '../components';
import type { SavedProfile, SavedProfileMode } from '../types';

const PROFILE_MODES: { mode: SavedProfileMode; description: string }[] = [
  { mode: 'accessibility', description: 'Wheelchair access, grab rails, lifts' },
  { mode: 'family', description: 'Baby changing, family rooms, pram access' },
  { mode: 'ibs', description: 'Single occupancy, quiet, high rated' },
  { mode: 'pregnancy', description: 'Single occupancy, close by' },
  { mode: 'neurodivergent', description: 'Quiet, single occupancy, calm' },
  { mode: 'elderly', description: 'Accessible, grab rails, easy access' },
];

export const SavedProfilesScreen: React.FC = () => {
  const navigation = useNavigation<NavigationProp<any>>();
  const [profiles, setProfiles] = useState<SavedProfile[]>([]);
  const [loading, setLoading] = useState(true);
  const [showCreate, setShowCreate] = useState(false);
  const [selectedMode, setSelectedMode] = useState<SavedProfileMode | null>(null);
  const [profileName, setProfileName] = useState('');
  const [creating, setCreating] = useState(false);

  useEffect(() => {
    loadProfiles();
  }, []);

  const loadProfiles = async () => {
    setLoading(true);
    const data = await getSavedProfiles();
    setProfiles(data);
    setLoading(false);
  };

  const handleCreate = async () => {
    if (!selectedMode) {
      Alert.alert('Required', 'Please select a profile type');
      return;
    }
    if (!profileName.trim()) {
      Alert.alert('Required', 'Please give your profile a name');
      return;
    }

    setCreating(true);
    const prefs = getDefaultPreferencesForMode(selectedMode);
    const result = await createSavedProfile(selectedMode, profileName.trim(), prefs);
    setCreating(false);

    if (result.success) {
      setShowCreate(false);
      setSelectedMode(null);
      setProfileName('');
      loadProfiles();
    } else {
      Alert.alert('Error', result.error || 'Failed to create profile');
    }
  };

  const handleDelete = (profile: SavedProfile) => {
    Alert.alert(
      'Delete Profile',
      `Are you sure you want to delete "${profile.name}"?`,
      [
        { text: 'Cancel', style: 'cancel' },
        {
          text: 'Delete',
          style: 'destructive',
          onPress: async () => {
            await deleteSavedProfile(profile.id);
            loadProfiles();
          },
        },
      ],
    );
  };

  return (
    <PremiumGate feature="saved_profiles">
    <ScrollView style={styles.container} contentContainerStyle={styles.content}>
      <Text style={styles.title}>Saved Profiles</Text>
      <Text style={styles.subtitle}>
        Create preference profiles to quickly filter facilities that match your
        needs. These are optional preferences, not medical declarations.
      </Text>

      {/* Existing Profiles */}
      {profiles.length > 0 && (
        <>
          <Text style={styles.sectionTitle}>Your Profiles</Text>
          {profiles.map((profile) => (
            <Card key={profile.id} variant="outlined" style={styles.profileCard}>
              <View style={styles.profileHeader}>
                <Text style={styles.profileIcon}>
                  {getModeIcon(profile.mode)}
                </Text>
                <View style={styles.profileInfo}>
                  <Text style={styles.profileName}>{profile.name}</Text>
                  <Text style={styles.profileMode}>
                    {getModeDisplayName(profile.mode)}
                  </Text>
                </View>
                <TouchableOpacity
                  onPress={() => handleDelete(profile)}
                  style={styles.deleteButton}
                >
                  <Text style={styles.deleteText}>✕</Text>
                </TouchableOpacity>
              </View>
              <View style={styles.profilePrefs}>
                {profile.preferences.requires_accessible && (
                  <Text style={styles.prefTag}>♿ Accessible</Text>
                )}
                {profile.preferences.requires_baby_changing && (
                  <Text style={styles.prefTag}>🍼 Baby</Text>
                )}
                {profile.preferences.requires_family_room && (
                  <Text style={styles.prefTag}>👨‍👩‍👧‍👧 Family</Text>
                )}
                {profile.preferences.requires_single_occupancy && (
                  <Text style={styles.prefTag}>🚪 Single</Text>
                )}
                {profile.preferences.requires_quiet && (
                  <Text style={styles.prefTag}>🔇 Quiet</Text>
                )}
                {profile.preferences.requires_radar_key && (
                  <Text style={styles.prefTag}>🔑 RADAR</Text>
                )}
                {profile.preferences.min_rating > 0 && (
                  <Text style={styles.prefTag}>
                    ★ {profile.preferences.min_rating}+
                  </Text>
                )}
              </View>
            </Card>
          ))}
        </>
      )}

      {/* Create New Profile */}
      {!showCreate ? (
        <Button
          title="Create New Profile"
          onPress={() => setShowCreate(true)}
          fullWidth
          variant="outline"
          style={styles.createButton}
        />
      ) : (
        <Card variant="outlined" style={styles.createCard}>
          <Text style={styles.createTitle}>New Profile</Text>

          <Text style={styles.label}>Profile Name</Text>
          <TextInput
            style={styles.input}
            value={profileName}
            onChangeText={setProfileName}
            placeholder="e.g. My Work Commute"
            placeholderTextColor={colors.textMuted}
          />

          <Text style={styles.label}>Profile Type</Text>
          <Text style={styles.hint}>
            Choose what matters most. You can customise preferences later.
          </Text>

          {PROFILE_MODES.map((pm) => (
            <TouchableOpacity
              key={pm.mode}
              style={[
                styles.modeOption,
                selectedMode === pm.mode && styles.modeOptionSelected,
              ]}
              onPress={() => setSelectedMode(pm.mode)}
            >
              <Text style={styles.modeIcon}>{getModeIcon(pm.mode)}</Text>
              <View style={styles.modeInfo}>
                <Text style={styles.modeName}>{getModeDisplayName(pm.mode)}</Text>
                <Text style={styles.modeDesc}>{pm.description}</Text>
              </View>
              {selectedMode === pm.mode && (
                <Text style={styles.checkmark}>✓</Text>
              )}
            </TouchableOpacity>
          ))}

          <View style={styles.createActions}>
            <Button
              title="Cancel"
              onPress={() => {
                setShowCreate(false);
                setSelectedMode(null);
                setProfileName('');
              }}
              variant="ghost"
              style={styles.createActionButton}
            />
            <Button
              title="Create"
              onPress={handleCreate}
              loading={creating}
              disabled={!selectedMode || !profileName.trim()}
              style={styles.createActionButton}
            />
          </View>
        </Card>
      )}

      {/* Info Note */}
      <Card variant="glass" style={styles.infoCard}>
        <Text style={styles.infoTitle}>💡 About Profiles</Text>
        <Text style={styles.infoText}>
          Saved profiles are optional preference shortcuts. They help you quickly
          filter facilities without having to set multiple toggles each time.
          Your health information is never stored or requested.
        </Text>
      </Card>
    </ScrollView>
    </PremiumGate>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: colors.background,
  },
  content: {
    padding: spacing.lg,
    paddingBottom: spacing['6xl'],
  },
  title: {
    fontFamily: 'PlusJakartaSans_700Bold',
    fontSize: 28,
    fontWeight: '700',
    color: colors.textPrimary,
    marginBottom: spacing.xs,
  },
  subtitle: {
    fontFamily: 'Inter_400Regular',
    fontSize: 15,
    color: colors.textSecondary,
    lineHeight: 22,
    marginBottom: spacing.xl,
  },
  sectionTitle: {
    fontFamily: 'PlusJakartaSans_600SemiBold',
    fontSize: 18,
    fontWeight: '600',
    color: colors.textPrimary,
    marginBottom: spacing.md,
  },
  profileCard: {
    marginBottom: spacing.md,
  },
  profileHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: spacing.sm,
  },
  profileIcon: {
    fontSize: 28,
    marginRight: spacing.md,
  },
  profileInfo: {
    flex: 1,
  },
  profileName: {
    fontFamily: 'Inter_600SemiBold',
    fontSize: 16,
    fontWeight: '600',
    color: colors.textPrimary,
  },
  profileMode: {
    fontFamily: 'Inter_400Regular',
    fontSize: 13,
    color: colors.textSecondary,
    marginTop: 2,
  },
  deleteButton: {
    padding: spacing.sm,
  },
  deleteText: {
    fontSize: 16,
    color: colors.textMuted,
  },
  profilePrefs: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: spacing.xs,
  },
  prefTag: {
    fontFamily: 'Inter_500Medium',
    fontSize: 12,
    fontWeight: '500',
    color: colors.primary,
    backgroundColor: colors.tealSoft,
    borderRadius: borderRadius.full,
    paddingVertical: 2,
    paddingHorizontal: spacing.sm,
  },
  createButton: {
    marginTop: spacing.md,
  },
  createCard: {
    marginTop: spacing.md,
  },
  createTitle: {
    fontFamily: 'PlusJakartaSans_600SemiBold',
    fontSize: 18,
    fontWeight: '600',
    color: colors.textPrimary,
    marginBottom: spacing.lg,
  },
  label: {
    fontFamily: 'Inter_500Medium',
    fontSize: 14,
    fontWeight: '500',
    color: colors.textPrimary,
    marginBottom: spacing.xs,
    marginTop: spacing.md,
  },
  hint: {
    fontFamily: 'Inter_400Regular',
    fontSize: 13,
    color: colors.textSecondary,
    marginBottom: spacing.md,
  },
  input: {
    fontFamily: 'Inter_400Regular',
    fontSize: 16,
    color: colors.textPrimary,
    backgroundColor: colors.white,
    borderWidth: 1,
    borderColor: colors.border,
    borderRadius: borderRadius.md,
    padding: spacing.md,
  },
  modeOption: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingVertical: spacing.md,
    paddingHorizontal: spacing.md,
    borderRadius: borderRadius.md,
    marginBottom: spacing.xs,
    borderWidth: 1,
    borderColor: colors.border,
  },
  modeOptionSelected: {
    borderColor: colors.primary,
    backgroundColor: colors.tealSoft,
  },
  modeIcon: {
    fontSize: 24,
    marginRight: spacing.md,
  },
  modeInfo: {
    flex: 1,
  },
  modeName: {
    fontFamily: 'Inter_600SemiBold',
    fontSize: 15,
    fontWeight: '600',
    color: colors.textPrimary,
  },
  modeDesc: {
    fontFamily: 'Inter_400Regular',
    fontSize: 12,
    color: colors.textSecondary,
    marginTop: 2,
  },
  checkmark: {
    fontSize: 18,
    color: colors.primary,
    fontWeight: '700',
  },
  createActions: {
    flexDirection: 'row',
    gap: spacing.md,
    marginTop: spacing.xl,
  },
  createActionButton: {
    flex: 1,
  },
  infoCard: {
    marginTop: spacing.xl,
  },
  infoTitle: {
    fontFamily: 'Inter_600SemiBold',
    fontSize: 15,
    fontWeight: '600',
    color: colors.textPrimary,
    marginBottom: spacing.xs,
  },
  infoText: {
    fontFamily: 'Inter_400Regular',
    fontSize: 13,
    color: colors.textSecondary,
    lineHeight: 20,
  },
});
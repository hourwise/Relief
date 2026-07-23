// ============================================================
// Project "Relief" — Predictive Suggestions Screen (Phase 5.2)
// "Next suitable facility in X miles" — AI-powered lookahead
// ============================================================

import React, { useState, useEffect, useCallback } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TouchableOpacity,
  ActivityIndicator,
  RefreshControl,
} from 'react-native';
import { useTranslation } from 'react-i18next';
import { useNavigation, useFocusEffect } from '@react-navigation/native';
import { colors, typography, spacing, borderRadius, shadows } from '../theme';
import { Card, Button } from '../components';
import { useLocation } from '../hooks/useLocation';
import { getSavedProfiles } from '../services/profiles';
import { getPredictiveSuggestions } from '../services/aiRecommendations';
import type { PredictiveSuggestion } from '../services/aiRecommendations';
import type { SavedProfile, ProfileStackParamList } from '../types';
import type { NativeStackNavigationProp } from '@react-navigation/native-stack';

type ProfileNavProp = NativeStackNavigationProp<ProfileStackParamList, 'PredictiveSuggestions'>;

// Direction labels mapped to degrees
const DIRECTION_MAP: { label: string; degrees: number }[] = [
  { label: 'North', degrees: 0 },
  { label: 'North East', degrees: 45 },
  { label: 'East', degrees: 90 },
  { label: 'South East', degrees: 135 },
  { label: 'South', degrees: 180 },
  { label: 'South West', degrees: 225 },
  { label: 'West', degrees: 270 },
  { label: 'North West', degrees: 315 },
];

export const PredictiveSuggestionsScreen: React.FC = () => {
  const { t } = useTranslation();
  const navigation = useNavigation<ProfileNavProp>();
  const { location, loading: locationLoading } = useLocation();

  const [profiles, setProfiles] = useState<SavedProfile[]>([]);
  const [selectedProfile, setSelectedProfile] = useState<SavedProfile | null>(null);
  const [selectedDirection, setSelectedDirection] = useState<number>(0);
  const [suggestions, setSuggestions] = useState<PredictiveSuggestion[]>([]);
  const [loading, setLoading] = useState(false);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useFocusEffect(
    useCallback(() => {
      loadProfiles();
    }, []),
  );

  const loadProfiles = async () => {
    const saved = await getSavedProfiles();
    setProfiles(saved);
    if (saved.length > 0 && !selectedProfile) {
      setSelectedProfile(saved[0]);
    }
  };

  const loadSuggestions = async (profile: SavedProfile, direction: number) => {
    if (!location) {
      setError('Location not available. Please enable location services.');
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const results = await getPredictiveSuggestions(
        location.latitude,
        location.longitude,
        direction,
        profile.preferences,
        { lookAheadRadiusKm: 20, minScore: 40, maxResults: 5 },
      );
      setSuggestions(results);
    } catch (err) {
      setError('Failed to load predictions. Please try again.');
      console.error('Predictive suggestions error:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleProfileSelect = (profile: SavedProfile) => {
    setSelectedProfile(profile);
    loadSuggestions(profile, selectedDirection);
  };

  const handleDirectionSelect = (degrees: number) => {
    setSelectedDirection(degrees);
    if (selectedProfile) {
      loadSuggestions(selectedProfile, degrees);
    }
  };

  const handleRefresh = async () => {
    if (!selectedProfile) return;
    setRefreshing(true);
    await loadSuggestions(selectedProfile, selectedDirection);
    setRefreshing(false);
  };

  const handleFacilityPress = (facilityId: string) => {
    navigation.navigate('FacilityDetail' as any, { facilityId });
  };

  const getDirectionLabel = (degrees: number): string => {
    const dir = DIRECTION_MAP.find((d) => d.degrees === degrees);
    return dir?.label ?? `${degrees}°`;
  };

  const getRelevanceColor = (score: number): string => {
    if (score >= 70) return colors.ratingHigh;
    if (score >= 50) return colors.ratingMedium;
    return colors.ratingLow;
  };

  return (
    <ScrollView
      style={styles.container}
      contentContainerStyle={styles.content}
      refreshControl={
        <RefreshControl
          refreshing={refreshing}
          onRefresh={handleRefresh}
          tintColor={colors.primary}
        />
      }
    >
      {/* Header */}
      <View style={styles.header}>
        <Text style={styles.headerTitle}>Predictive Suggestions</Text>
        <Text style={styles.headerSubtitle}>
          Find the next suitable facility ahead in your direction of travel
        </Text>
      </View>

      {/* Profile Selector */}
      {profiles.length > 0 && (
        <View style={styles.selectorSection}>
          <Text style={styles.sectionLabel}>Using profile:</Text>
          <ScrollView
            horizontal
            showsHorizontalScrollIndicator={false}
            contentContainerStyle={styles.chipList}
          >
            {profiles.map((profile) => (
              <TouchableOpacity
                key={profile.id}
                style={[
                  styles.chip,
                  selectedProfile?.id === profile.id && styles.chipActive,
                ]}
                onPress={() => handleProfileSelect(profile)}
                activeOpacity={0.7}
              >
                <Text
                  style={[
                    styles.chipText,
                    selectedProfile?.id === profile.id && styles.chipTextActive,
                  ]}
                >
                  {profile.name}
                </Text>
              </TouchableOpacity>
            ))}
          </ScrollView>
        </View>
      )}

      {/* Direction Selector */}
      <View style={styles.selectorSection}>
        <Text style={styles.sectionLabel}>Direction of travel:</Text>
        <ScrollView
          horizontal
          showsHorizontalScrollIndicator={false}
          contentContainerStyle={styles.chipList}
        >
          {DIRECTION_MAP.map((dir) => (
            <TouchableOpacity
              key={dir.degrees}
              style={[
                styles.chip,
                selectedDirection === dir.degrees && styles.chipActive,
              ]}
              onPress={() => handleDirectionSelect(dir.degrees)}
              activeOpacity={0.7}
            >
              <Text
                style={[
                  styles.chipText,
                  selectedDirection === dir.degrees && styles.chipTextActive,
                ]}
              >
                {dir.label} {dir.degrees === 0 ? '↑' : dir.degrees === 90 ? '→' : dir.degrees === 180 ? '↓' : dir.degrees === 270 ? '←' : ''}
              </Text>
            </TouchableOpacity>
          ))}
        </ScrollView>
      </View>

      {/* Location required */}
      {!location && !locationLoading && (
        <Card variant="outlined" style={styles.emptyCard}>
          <Text style={styles.emptyIcon}>📍</Text>
          <Text style={styles.emptyTitle}>Location required</Text>
          <Text style={styles.emptyDescription}>
            Enable location services to find facilities ahead of you.
          </Text>
        </Card>
      )}

      {/* No profiles state */}
      {profiles.length === 0 && (
        <Card variant="outlined" style={styles.emptyCard}>
          <Text style={styles.emptyIcon}>📋</Text>
          <Text style={styles.emptyTitle}>No saved profiles yet</Text>
          <Text style={styles.emptyDescription}>
            Create a saved profile first to get predictive facility suggestions.
          </Text>
          <Button
            title="Create Profile"
            onPress={() => navigation.navigate('SavedProfiles')}
            variant="outline"
            size="sm"
          />
        </Card>
      )}

      {/* Loading */}
      {loading && (
        <View style={styles.loadingContainer}>
          <ActivityIndicator size="large" color={colors.primary} />
          <Text style={styles.loadingText}>Scanning ahead...</Text>
        </View>
      )}

      {/* Error */}
      {error && (
        <Card variant="outlined" style={styles.errorCard}>
          <Text style={styles.errorText}>{error}</Text>
          <Button
            title="Retry"
            onPress={() => selectedProfile && loadSuggestions(selectedProfile, selectedDirection)}
            variant="outline"
            size="sm"
          />
        </Card>
      )}

      {/* Suggestions List */}
      {!loading && !error && suggestions.length > 0 && selectedProfile && (
        <View style={styles.suggestionsSection}>
          <View style={styles.suggestionsHeader}>
            <Text style={styles.sectionTitle}>
              Facilities to the {getDirectionLabel(selectedDirection).toLowerCase()}
            </Text>
            <Text style={styles.suggestionsSubtitle}>
              Next facilities matching your "{selectedProfile.name}" preferences
            </Text>
          </View>

          {suggestions.map((suggestion, index) => (
            <TouchableOpacity
              key={suggestion.facility.id}
              onPress={() => handleFacilityPress(suggestion.facility.id)}
              activeOpacity={0.7}
            >
              <Card variant="elevated" style={styles.suggestionCard}>
                {/* Relevance indicator */}
                <View style={styles.suggestionHeader}>
                  <View
                    style={[
                      styles.relevanceDot,
                      { backgroundColor: getRelevanceColor(suggestion.relevanceScore) },
                    ]}
                  />
                  <Text style={styles.suggestionReason}>{suggestion.reason}</Text>
                </View>

                {/* Distance indicator */}
                <View style={styles.distanceSection}>
                  <View style={styles.distanceBadge}>
                    <Text style={styles.distanceIcon}>🚶</Text>
                    <Text style={styles.distanceText}>
                      ~{suggestion.estimatedWalkingMinutes} min walk
                    </Text>
                  </View>
                  {suggestion.distanceKm > 0 && (
                    <Text style={styles.distanceKmText}>
                      {suggestion.distanceKm.toFixed(1)} km
                    </Text>
                  )}
                </View>

                {/* Facility info */}
                <View style={styles.facilityInfo}>
                  <Text style={styles.facilityName}>{suggestion.facility.name}</Text>
                  <Text style={styles.facilityAddress} numberOfLines={1}>
                    {suggestion.facility.address}
                  </Text>
                  <View style={styles.facilityMeta}>
                    <Text style={styles.facilityRating}>
                      ★ {suggestion.facility.overall_score.toFixed(1)}
                    </Text>
                    <Text style={styles.facilityTown}>
                      {suggestion.facility.town}
                    </Text>
                  </View>
                </View>

                {/* Open status */}
                <View style={styles.statusRow}>
                  {isOpenNow(suggestion.facility) ? (
                    <View style={styles.openBadge}>
                      <Text style={styles.openBadgeText}>Open now</Text>
                    </View>
                  ) : suggestion.facility.is_24h ? (
                    <View style={styles.openBadge}>
                      <Text style={styles.openBadgeText}>Open 24h</Text>
                    </View>
                  ) : (
                    <View style={styles.closedBadge}>
                      <Text style={styles.closedBadgeText}>Check hours</Text>
                    </View>
                  )}
                  {suggestion.facility.is_free && (
                    <View style={styles.freeBadge}>
                      <Text style={styles.freeBadgeText}>Free</Text>
                    </View>
                  )}
                </View>
              </Card>
            </TouchableOpacity>
          ))}
        </View>
      )}

      {/* Empty state */}
      {!loading && !error && suggestions.length === 0 && selectedProfile && location && (
        <Card variant="outlined" style={styles.emptyCard}>
          <Text style={styles.emptyIcon}>🔮</Text>
          <Text style={styles.emptyTitle}>No facilities ahead</Text>
          <Text style={styles.emptyDescription}>
            No suitable facilities found {getDirectionLabel(selectedDirection).toLowerCase()} of your
            current location matching "{selectedProfile.name}" preferences.
          </Text>
          <Button
            title="Try Another Direction"
            onPress={() => handleDirectionSelect((selectedDirection + 45) % 360)}
            variant="outline"
            size="sm"
          />
        </Card>
      )}
    </ScrollView>
  );
};

/**
 * Check if a facility is currently open.
 */
function isOpenNow(facility: { is_24h: boolean; open_hours: Record<string, { open: string; close: string } | null> | null }): boolean {
  if (facility.is_24h) return true;
  if (!facility.open_hours) return false;
  const days = ['sunday', 'monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday'];
  const today = days[new Date().getDay()];
  const hours = facility.open_hours[today];
  if (!hours) return false;
  const now = new Date();
  const [openH, openM] = hours.open.split(':').map(Number);
  const [closeH, closeM] = hours.close.split(':').map(Number);
  const openMinutes = openH * 60 + openM;
  const closeMinutes = closeH * 60 + closeM;
  const nowMinutes = now.getHours() * 60 + now.getMinutes();
  return nowMinutes >= openMinutes && nowMinutes <= closeMinutes;
}

// ─── Styles ──────────────────────────────────────────────────

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: colors.background,
  },
  content: {
    padding: spacing.lg,
    paddingBottom: spacing['6xl'],
  },
  header: {
    marginBottom: spacing.lg,
  },
  headerTitle: {
    ...typography.h2,
    color: colors.textPrimary,
    marginBottom: spacing.xs,
  },
  headerSubtitle: {
    ...typography.body,
    color: colors.textSecondary,
  },
  // Selectors
  selectorSection: {
    marginBottom: spacing.lg,
  },
  sectionLabel: {
    ...typography.caption,
    color: colors.textMuted,
    marginBottom: spacing.sm,
    textTransform: 'uppercase',
    letterSpacing: 1,
  },
  chipList: {
    gap: spacing.sm,
    flexDirection: 'row',
  },
  chip: {
    paddingVertical: spacing.sm,
    paddingHorizontal: spacing.lg,
    borderRadius: borderRadius.full,
    backgroundColor: colors.gray100,
    borderWidth: 1,
    borderColor: colors.border,
  },
  chipActive: {
    backgroundColor: colors.tealSoft,
    borderColor: colors.primary,
  },
  chipText: {
    ...typography.bodySmall,
    color: colors.textSecondary,
    fontWeight: '600',
  },
  chipTextActive: {
    color: colors.primary,
  },
  // Loading
  loadingContainer: {
    alignItems: 'center',
    paddingVertical: spacing['4xl'],
  },
  loadingText: {
    ...typography.body,
    color: colors.textSecondary,
    marginTop: spacing.md,
  },
  // Error
  errorCard: {
    padding: spacing.lg,
    alignItems: 'center',
  },
  errorText: {
    ...typography.body,
    color: colors.error,
    textAlign: 'center',
    marginBottom: spacing.md,
  },
  // Suggestions
  suggestionsSection: {
    marginTop: spacing.sm,
  },
  suggestionsHeader: {
    marginBottom: spacing.lg,
  },
  sectionTitle: {
    ...typography.h3,
    color: colors.textPrimary,
    marginBottom: spacing.xs,
  },
  suggestionsSubtitle: {
    ...typography.caption,
    color: colors.textSecondary,
  },
  suggestionCard: {
    marginBottom: spacing.md,
    padding: spacing.lg,
  },
  suggestionHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: spacing.sm,
  },
  relevanceDot: {
    width: 10,
    height: 10,
    borderRadius: 5,
    marginRight: spacing.sm,
  },
  suggestionReason: {
    ...typography.bodySmall,
    color: colors.textSecondary,
    fontStyle: 'italic',
    flex: 1,
  },
  distanceSection: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    marginBottom: spacing.md,
    backgroundColor: colors.gray50,
    borderRadius: borderRadius.md,
    padding: spacing.sm,
  },
  distanceBadge: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  distanceIcon: {
    fontSize: 16,
    marginRight: spacing.xs,
  },
  distanceText: {
    ...typography.bodySmall,
    color: colors.textPrimary,
    fontWeight: '600',
  },
  distanceKmText: {
    ...typography.caption,
    color: colors.textSecondary,
  },
  facilityInfo: {
    marginBottom: spacing.sm,
  },
  facilityName: {
    ...typography.h4,
    color: colors.textPrimary,
    marginBottom: 2,
  },
  facilityAddress: {
    ...typography.caption,
    color: colors.textSecondary,
    marginBottom: spacing.xs,
  },
  facilityMeta: {
    flexDirection: 'row',
    justifyContent: 'space-between',
  },
  facilityRating: {
    ...typography.bodySmall,
    color: colors.textPrimary,
    fontWeight: '600',
  },
  facilityTown: {
    ...typography.caption,
    color: colors.textSecondary,
  },
  statusRow: {
    flexDirection: 'row',
    gap: spacing.sm,
  },
  openBadge: {
    backgroundColor: colors.tealSoft,
    borderRadius: borderRadius.sm,
    paddingVertical: 2,
    paddingHorizontal: spacing.sm,
  },
  openBadgeText: {
    ...typography.caption,
    color: colors.primary,
    fontWeight: '600',
    fontSize: 11,
  },
  closedBadge: {
    backgroundColor: colors.gray100,
    borderRadius: borderRadius.sm,
    paddingVertical: 2,
    paddingHorizontal: spacing.sm,
  },
  closedBadgeText: {
    ...typography.caption,
    color: colors.textMuted,
    fontWeight: '600',
    fontSize: 11,
  },
  freeBadge: {
    backgroundColor: colors.tealSoft,
    borderRadius: borderRadius.sm,
    paddingVertical: 2,
    paddingHorizontal: spacing.sm,
  },
  freeBadgeText: {
    ...typography.caption,
    color: colors.primary,
    fontWeight: '600',
    fontSize: 11,
  },
  // Empty state
  emptyCard: {
    padding: spacing['3xl'],
    alignItems: 'center',
  },
  emptyIcon: {
    fontSize: 48,
    marginBottom: spacing.md,
  },
  emptyTitle: {
    ...typography.h3,
    color: colors.textPrimary,
    marginBottom: spacing.sm,
    textAlign: 'center',
  },
  emptyDescription: {
    ...typography.body,
    color: colors.textSecondary,
    textAlign: 'center',
    marginBottom: spacing.lg,
    lineHeight: 22,
  },
});
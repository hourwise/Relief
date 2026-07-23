// ============================================================
// Project "Relief" — AI Recommendations Screen (Phase 5.1)
// Smart facility recommendations matching user needs
// ============================================================

import React, { useState, useEffect, useCallback } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TouchableOpacity,
  ActivityIndicator,
  FlatList,
  RefreshControl,
} from 'react-native';
import { useTranslation } from 'react-i18next';
import { useNavigation, useFocusEffect } from '@react-navigation/native';
import { colors, typography, spacing, borderRadius, shadows } from '../theme';
import { Card, Button } from '../components';
import { useLocation } from '../hooks/useLocation';
import { getSavedProfiles } from '../services/profiles';
import { getSmartRecommendations, getRecommendationsForProfile } from '../services/aiRecommendations';
import type { RecommendationScore } from '../services/aiRecommendations';
import type { SavedProfile, ProfileStackParamList } from '../types';
import type { NativeStackNavigationProp } from '@react-navigation/native-stack';

type ProfileNavProp = NativeStackNavigationProp<ProfileStackParamList, 'AIRecommendations'>;

export const AIRecommendationsScreen: React.FC = () => {
  const { t } = useTranslation();
  const navigation = useNavigation<ProfileNavProp>();
  const { location, loading: locationLoading } = useLocation();

  const [profiles, setProfiles] = useState<SavedProfile[]>([]);
  const [selectedProfile, setSelectedProfile] = useState<SavedProfile | null>(null);
  const [recommendations, setRecommendations] = useState<RecommendationScore[]>([]);
  const [loading, setLoading] = useState(false);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Load saved profiles on mount
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

  const loadRecommendations = async (profile: SavedProfile) => {
    if (!location) {
      setError('Location not available. Please enable location services.');
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const results = await getRecommendationsForProfile(
        location.latitude,
        location.longitude,
        profile,
        { limit: 20 },
      );
      setRecommendations(results);
    } catch (err) {
      setError('Failed to load recommendations. Please try again.');
      console.error('AI recommendations error:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleProfileSelect = (profile: SavedProfile) => {
    setSelectedProfile(profile);
    loadRecommendations(profile);
  };

  const handleRefresh = async () => {
    if (!selectedProfile) return;
    setRefreshing(true);
    await loadRecommendations(selectedProfile);
    setRefreshing(false);
  };

  const handleFacilityPress = (facilityId: string) => {
    navigation.navigate('FacilityDetail' as any, { facilityId });
  };

  // Get score color
  const getScoreColor = (score: number): string => {
    if (score >= 80) return colors.ratingHigh;
    if (score >= 60) return colors.ratingMedium;
    return colors.ratingLow;
  };

  const getScoreLabel = (score: number): string => {
    if (score >= 80) return 'Excellent match';
    if (score >= 60) return 'Good match';
    if (score >= 40) return 'Fair match';
    return 'Low match';
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
        <Text style={styles.headerTitle}>AI Recommendations</Text>
        <Text style={styles.headerSubtitle}>
          Facilities matched to your needs using smart scoring
        </Text>
      </View>

      {/* Profile Selector */}
      {profiles.length > 0 && (
        <View style={styles.profileSelector}>
          <Text style={styles.sectionLabel}>Using profile:</Text>
          <ScrollView
            horizontal
            showsHorizontalScrollIndicator={false}
            contentContainerStyle={styles.profileList}
          >
            {profiles.map((profile) => (
              <TouchableOpacity
                key={profile.id}
                style={[
                  styles.profileChip,
                  selectedProfile?.id === profile.id && styles.profileChipActive,
                ]}
                onPress={() => handleProfileSelect(profile)}
                activeOpacity={0.7}
              >
                <Text
                  style={[
                    styles.profileChipText,
                    selectedProfile?.id === profile.id && styles.profileChipTextActive,
                  ]}
                >
                  {profile.name}
                </Text>
              </TouchableOpacity>
            ))}
          </ScrollView>
        </View>
      )}

      {/* No profiles state */}
      {profiles.length === 0 && (
        <Card variant="outlined" style={styles.emptyCard}>
          <Text style={styles.emptyIcon}>📋</Text>
          <Text style={styles.emptyTitle}>No saved profiles yet</Text>
          <Text style={styles.emptyDescription}>
            Create a saved profile first to get personalised facility recommendations.
          </Text>
          <Button
            title="Create Profile"
            onPress={() => navigation.navigate('SavedProfiles')}
            variant="outline"
            size="sm"
          />
        </Card>
      )}

      {/* Location required */}
      {!location && !locationLoading && (
        <Card variant="outlined" style={styles.emptyCard}>
          <Text style={styles.emptyIcon}>📍</Text>
          <Text style={styles.emptyTitle}>Location required</Text>
          <Text style={styles.emptyDescription}>
            Enable location services to get recommendations for nearby facilities.
          </Text>
        </Card>
      )}

      {/* Loading */}
      {loading && (
        <View style={styles.loadingContainer}>
          <ActivityIndicator size="large" color={colors.primary} />
          <Text style={styles.loadingText}>Analysing facilities...</Text>
        </View>
      )}

      {/* Error */}
      {error && (
        <Card variant="outlined" style={styles.errorCard}>
          <Text style={styles.errorText}>{error}</Text>
          <Button
            title="Retry"
            onPress={() => selectedProfile && loadRecommendations(selectedProfile)}
            variant="outline"
            size="sm"
          />
        </Card>
      )}

      {/* Recommendations List */}
      {!loading && !error && recommendations.length > 0 && selectedProfile && (
        <View style={styles.recommendationsSection}>
          <Text style={styles.sectionTitle}>
            Recommended Facilities ({recommendations.length})
          </Text>
          <Text style={styles.sectionSubtitle}>
            Scored based on your "{selectedProfile.name}" preferences
          </Text>

          {recommendations.map((rec, index) => (
            <TouchableOpacity
              key={rec.facility.id}
              onPress={() => handleFacilityPress(rec.facility.id)}
              activeOpacity={0.7}
            >
              <Card variant="elevated" style={styles.recommendationCard}>
                {/* Rank badge */}
                <View style={styles.rankBadge}>
                  <Text style={styles.rankBadgeText}>#{index + 1}</Text>
                </View>

                {/* Score indicator */}
                <View style={styles.scoreSection}>
                  <View
                    style={[
                      styles.scoreCircle,
                      { backgroundColor: getScoreColor(rec.totalScore) },
                    ]}
                  >
                    <Text style={styles.scoreText}>
                      {Math.round(rec.totalScore)}
                    </Text>
                  </View>
                  <Text style={styles.scoreLabel}>
                    {getScoreLabel(rec.totalScore)}
                  </Text>
                </View>

                {/* Facility info */}
                <View style={styles.facilityInfo}>
                  <Text style={styles.facilityName}>{rec.facility.name}</Text>
                  <Text style={styles.facilityAddress} numberOfLines={1}>
                    {rec.facility.address}
                  </Text>
                  <View style={styles.facilityMeta}>
                    <Text style={styles.facilityRating}>
                      ★ {rec.facility.overall_score.toFixed(1)}
                    </Text>
                    <Text style={styles.facilityDistance}>
                      {rec.facility.town}
                    </Text>
                  </View>
                </View>

                {/* Matching preferences */}
                {rec.matchingPreferences.length > 0 && (
                  <View style={styles.matchesSection}>
                    <Text style={styles.matchesLabel}>Matches:</Text>
                    <View style={styles.matchesList}>
                      {rec.matchingPreferences.slice(0, 3).map((match, i) => (
                        <View key={i} style={styles.matchTag}>
                          <Text style={styles.matchTagText}>{match}</Text>
                        </View>
                      ))}
                      {rec.matchingPreferences.length > 3 && (
                        <Text style={styles.matchesMore}>
                          +{rec.matchingPreferences.length - 3} more
                        </Text>
                      )}
                    </View>
                  </View>
                )}

                {/* Score breakdown */}
                <View style={styles.breakdownSection}>
                  <Text style={styles.breakdownLabel}>Score breakdown:</Text>
                  <View style={styles.breakdownBars}>
                    <BreakdownBar
                      label="Preferences"
                      value={rec.breakdown.preferenceMatch}
                      color={colors.primary}
                    />
                    <BreakdownBar
                      label="Rating"
                      value={rec.breakdown.rating}
                      color={colors.ratingHigh}
                    />
                    <BreakdownBar
                      label="Distance"
                      value={rec.breakdown.distance}
                      color={colors.mapPinAccessible}
                    />
                    <BreakdownBar
                      label="Open"
                      value={rec.breakdown.openStatus}
                      color={rec.breakdown.openStatus >= 50 ? colors.success : colors.error}
                    />
                  </View>
                </View>
              </Card>
            </TouchableOpacity>
          ))}
        </View>
      )}

      {/* Empty state */}
      {!loading && !error && recommendations.length === 0 && selectedProfile && location && (
        <Card variant="outlined" style={styles.emptyCard}>
          <Text style={styles.emptyIcon}>🔍</Text>
          <Text style={styles.emptyTitle}>No matching facilities</Text>
          <Text style={styles.emptyDescription}>
            No facilities found nearby that match your "{selectedProfile.name}" preferences.
            Try expanding your search area or adjusting your profile.
          </Text>
          <Button
            title="Refresh"
            onPress={handleRefresh}
            variant="outline"
            size="sm"
          />
        </Card>
      )}
    </ScrollView>
  );
};

// ─── Breakdown Bar Component ─────────────────────────────────

const BreakdownBar: React.FC<{
  label: string;
  value: number;
  color: string;
}> = ({ label, value, color }) => (
  <View style={styles.breakdownRow}>
    <Text style={styles.breakdownLabelText}>{label}</Text>
    <View style={styles.breakdownBarTrack}>
      <View
        style={[
          styles.breakdownBarFill,
          { width: `${value}%`, backgroundColor: color },
        ]}
      />
    </View>
    <Text style={styles.breakdownValueText}>{Math.round(value)}%</Text>
  </View>
);

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
  // Profile selector
  profileSelector: {
    marginBottom: spacing.lg,
  },
  sectionLabel: {
    ...typography.caption,
    color: colors.textMuted,
    marginBottom: spacing.sm,
    textTransform: 'uppercase',
    letterSpacing: 1,
  },
  profileList: {
    gap: spacing.sm,
    flexDirection: 'row',
  },
  profileChip: {
    paddingVertical: spacing.sm,
    paddingHorizontal: spacing.lg,
    borderRadius: borderRadius.full,
    backgroundColor: colors.gray100,
    borderWidth: 1,
    borderColor: colors.border,
  },
  profileChipActive: {
    backgroundColor: colors.tealSoft,
    borderColor: colors.primary,
  },
  profileChipText: {
    ...typography.bodySmall,
    color: colors.textSecondary,
    fontWeight: '600',
  },
  profileChipTextActive: {
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
  // Recommendations
  recommendationsSection: {
    marginTop: spacing.sm,
  },
  sectionTitle: {
    ...typography.h3,
    color: colors.textPrimary,
    marginBottom: spacing.xs,
  },
  sectionSubtitle: {
    ...typography.caption,
    color: colors.textSecondary,
    marginBottom: spacing.lg,
  },
  recommendationCard: {
    marginBottom: spacing.md,
    padding: spacing.lg,
    position: 'relative',
  },
  rankBadge: {
    position: 'absolute',
    top: spacing.sm,
    right: spacing.sm,
    backgroundColor: colors.primary,
    borderRadius: borderRadius.sm,
    paddingVertical: 2,
    paddingHorizontal: spacing.sm,
  },
  rankBadgeText: {
    ...typography.caption,
    color: colors.white,
    fontWeight: '700',
  },
  scoreSection: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: spacing.md,
  },
  scoreCircle: {
    width: 48,
    height: 48,
    borderRadius: 24,
    justifyContent: 'center',
    alignItems: 'center',
    marginRight: spacing.md,
  },
  scoreText: {
    ...typography.h3,
    color: colors.white,
    fontWeight: '800',
  },
  scoreLabel: {
    ...typography.bodySmall,
    color: colors.textSecondary,
    fontWeight: '600',
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
  facilityDistance: {
    ...typography.caption,
    color: colors.textSecondary,
  },
  // Matching preferences
  matchesSection: {
    marginBottom: spacing.md,
  },
  matchesLabel: {
    ...typography.caption,
    color: colors.textMuted,
    marginBottom: spacing.xs,
  },
  matchesList: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: spacing.xs,
  },
  matchTag: {
    backgroundColor: colors.tealSoft,
    borderRadius: borderRadius.sm,
    paddingVertical: 2,
    paddingHorizontal: spacing.sm,
  },
  matchTagText: {
    ...typography.caption,
    color: colors.primary,
    fontWeight: '600',
    fontSize: 11,
  },
  matchesMore: {
    ...typography.caption,
    color: colors.textMuted,
    alignSelf: 'center',
  },
  // Score breakdown
  breakdownSection: {
    borderTopWidth: 1,
    borderTopColor: colors.borderLight,
    paddingTop: spacing.sm,
  },
  breakdownLabel: {
    ...typography.caption,
    color: colors.textMuted,
    marginBottom: spacing.sm,
  },
  breakdownBars: {
    gap: spacing.xs,
  },
  breakdownRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: spacing.sm,
  },
  breakdownLabelText: {
    ...typography.caption,
    color: colors.textSecondary,
    width: 70,
    fontSize: 10,
  },
  breakdownBarTrack: {
    flex: 1,
    height: 6,
    backgroundColor: colors.gray100,
    borderRadius: 3,
    overflow: 'hidden',
  },
  breakdownBarFill: {
    height: '100%',
    borderRadius: 3,
  },
  breakdownValueText: {
    ...typography.caption,
    color: colors.textMuted,
    width: 32,
    textAlign: 'right',
    fontSize: 10,
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
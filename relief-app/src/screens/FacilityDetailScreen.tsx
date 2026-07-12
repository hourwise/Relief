// ============================================================
// Project "Relief" — Facility Detail Screen
// ============================================================

import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TouchableOpacity,
  Linking,
  ActivityIndicator,
} from 'react-native';
import { useRoute, useNavigation, RouteProp, NavigationProp } from '@react-navigation/native';
import { colors, typography, spacing, borderRadius, shadows } from '../theme';
import { Card, Badge, Button } from '../components';
import { fetchFacilityById } from '../services/facilities';
import { getActiveReports } from '../services/community';
import type { Facility, MapStackParamList } from '../types';
import type { TemporaryReport } from '../types/community';

type FacilityDetailRouteProp = RouteProp<MapStackParamList, 'FacilityDetail'>;

export const FacilityDetailScreen: React.FC = () => {
  const route = useRoute<FacilityDetailRouteProp>();
  const navigation = useNavigation<NavigationProp<MapStackParamList>>();
  const { facilityId } = route.params;
  const [facility, setFacility] = useState<Facility | null>(null);
  const [loading, setLoading] = useState(true);
  const [activeReports, setActiveReports] = useState<TemporaryReport[]>([]);

  useEffect(() => {
    loadFacility();
    loadReports();
  }, [facilityId]);

  const loadFacility = async () => {
    setLoading(true);
    const data = await fetchFacilityById(facilityId);
    setFacility(data);
    setLoading(false);
  };

  const loadReports = async () => {
    const reports = await getActiveReports(facilityId);
    setActiveReports(reports);
  };

  const openMaps = (provider: 'google' | 'apple' | 'waze') => {
    if (!facility) return;
    const { latitude, longitude } = facility;
    const encodedAddress = encodeURIComponent(facility.address);
    switch (provider) {
      case 'google':
        Linking.openURL(`https://maps.google.com/?q=${encodedAddress}`);
        break;
      case 'apple':
        Linking.openURL(`maps://app?daddr=${latitude},${longitude}`);
        break;
      case 'waze':
        Linking.openURL(`https://waze.com/ul?ll=${latitude},${longitude}&navigate=yes`);
        break;
    }
  };

  if (loading) {
    return (
      <View style={styles.loadingContainer}>
        <ActivityIndicator size="large" color={colors.primary} />
      </View>
    );
  }

  if (!facility) {
    return (
      <View style={styles.loadingContainer}>
        <Text style={styles.errorText}>Facility not found</Text>
      </View>
    );
  }

  return (
    <ScrollView style={styles.container} contentContainerStyle={styles.content}>
      {/* Active Reports Warning */}
      {activeReports.length > 0 && (
        <Card variant="outlined" style={styles.reportWarning}>
          <Text style={styles.reportWarningTitle}>⚠ Active Reports</Text>
          {activeReports.map((report) => (
            <Text key={report.id} style={styles.reportWarningItem}>
              {report.type}: {report.notes || 'No details'}
            </Text>
          ))}
        </Card>
      )}

      {/* Header */}
      <Card variant="elevated" style={styles.headerCard}>
        <View style={styles.headerRow}>
          <Text style={styles.name}>{facility.name}</Text>
          <Badge
            label={facility.is_24h ? 'Open 24h' : 'See hours'}
            variant={facility.is_24h ? 'success' : 'info'}
          />
        </View>
        <Text style={styles.address}>{facility.address}</Text>
        <View style={styles.priceRow}>
          <Text style={styles.price}>
            {facility.is_free ? 'Free' : facility.price_note || 'Paid'}
          </Text>
          <Text style={styles.verified}>
            Verified {new Date(facility.last_verified_at).toLocaleDateString()}
          </Text>
        </View>
      </Card>

      {/* Rating */}
      <Card variant="outlined" style={styles.section}>
        <Text style={styles.sectionTitle}>Overall Score</Text>
        <Text style={styles.overallScore}>
          ★ {facility.overall_score.toFixed(1)}
        </Text>
        <View style={styles.ratingsGrid}>
          {[
            { label: 'Cleanliness', value: facility.cleanliness_rating },
            { label: 'Privacy', value: facility.privacy_rating },
            { label: 'Accessibility', value: facility.accessibility_rating },
            { label: 'Safety', value: facility.safety_rating },
            { label: 'Noise', value: facility.noise_rating },
            { label: 'Environment', value: facility.environment_rating },
          ].map((rating) => (
            <View key={rating.label} style={styles.ratingItem}>
              <Text style={styles.ratingLabel}>{rating.label}</Text>
              <Text style={styles.ratingValue}>★ {rating.value.toFixed(1)}</Text>
            </View>
          ))}
        </View>
      </Card>

      {/* Amenities */}
      <Card variant="outlined" style={styles.section}>
        <Text style={styles.sectionTitle}>Amenities</Text>
        <View style={styles.amenitiesGrid}>
          {facility.is_accessible && (
            <Badge label="Accessible" variant="success" size="sm" />
          )}
          {facility.is_disabled_access && (
            <Badge label="Disabled Access" variant="success" size="sm" />
          )}
          {facility.has_baby_changing && (
            <Badge label="Baby Changing" variant="success" size="sm" />
          )}
          {facility.has_family_room && (
            <Badge label="Family Room" variant="success" size="sm" />
          )}
          {facility.is_gender_neutral && (
            <Badge label="Gender Neutral" variant="success" size="sm" />
          )}
          {facility.is_single_occupancy && (
            <Badge label="Single Occupancy" variant="success" size="sm" />
          )}
          {facility.is_24h && (
            <Badge label="24 Hours" variant="success" size="sm" />
          )}
        </View>
      </Card>

      {/* Access Notes */}
      {facility.access_notes ? (
        <Card variant="outlined" style={styles.section}>
          <Text style={styles.sectionTitle}>Access Notes</Text>
          <Text style={styles.accessNotes}>{facility.access_notes}</Text>
        </Card>
      ) : null}

      {/* Directions */}
      <Card variant="outlined" style={styles.section}>
        <Text style={styles.sectionTitle}>Get Directions</Text>
        <View style={styles.directionsRow}>
          <Button
            title="Google Maps"
            onPress={() => openMaps('google')}
            size="sm"
            variant="outline"
          />
          <Button
            title="Apple Maps"
            onPress={() => openMaps('apple')}
            size="sm"
            variant="outline"
          />
          <Button
            title="Waze"
            onPress={() => openMaps('waze')}
            size="sm"
            variant="outline"
          />
        </View>
      </Card>

      {/* Community Actions */}
      <Card variant="outlined" style={styles.section}>
        <Text style={styles.sectionTitle}>Help Improve This Facility</Text>
        <View style={styles.communityActions}>
          <Button
            title="Report Issue"
            onPress={() => navigation.navigate('ReportFacility', { facilityId })}
            size="sm"
            variant="outline"
            style={styles.communityButton}
          />
          <Button
            title="Correct Info"
            onPress={() => navigation.navigate('CorrectInfo', { facilityId })}
            size="sm"
            variant="outline"
            style={styles.communityButton}
          />
        </View>
      </Card>
    </ScrollView>
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
  loadingContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    backgroundColor: colors.background,
  },
  errorText: {
    ...typography.body,
    color: colors.textMuted,
  },
  reportWarning: {
    marginBottom: spacing.lg,
    backgroundColor: '#FEF3C7',
    borderColor: colors.warning,
  },
  reportWarningTitle: {
    ...typography.h4,
    color: colors.textPrimary,
    marginBottom: spacing.xs,
  },
  reportWarningItem: {
    ...typography.bodySmall,
    color: colors.textSecondary,
    marginBottom: 2,
  },
  headerCard: {
    marginBottom: spacing.lg,
  },
  headerRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'flex-start',
    marginBottom: spacing.sm,
  },
  name: {
    ...typography.h2,
    color: colors.textPrimary,
    flex: 1,
    marginRight: spacing.sm,
  },
  address: {
    ...typography.body,
    color: colors.textSecondary,
    marginBottom: spacing.sm,
  },
  priceRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  price: {
    ...typography.label,
    color: colors.primary,
  },
  verified: {
    ...typography.caption,
    color: colors.textMuted,
  },
  section: {
    marginBottom: spacing.lg,
  },
  sectionTitle: {
    ...typography.h4,
    color: colors.textPrimary,
    marginBottom: spacing.md,
  },
  overallScore: {
    ...typography.h1,
    color: colors.warning,
    textAlign: 'center',
    marginBottom: spacing.lg,
  },
  ratingsGrid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: spacing.md,
  },
  ratingItem: {
    width: '45%',
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  ratingLabel: {
    ...typography.bodySmall,
    color: colors.textSecondary,
  },
  ratingValue: {
    ...typography.bodySmall,
    color: colors.warning,
    fontWeight: '600',
  },
  amenitiesGrid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: spacing.sm,
  },
  accessNotes: {
    ...typography.body,
    color: colors.textPrimary,
  },
  directionsRow: {
    flexDirection: 'row',
    gap: spacing.sm,
  },
  communityActions: {
    flexDirection: 'row',
    gap: spacing.sm,
  },
  communityButton: {
    flex: 1,
  },
});
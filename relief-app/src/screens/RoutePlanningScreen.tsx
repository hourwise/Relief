// ============================================================
// Project "Relief" — Route Planning Screen (4.2)
// Plan a route with comfort stops every 60-90 minutes
// e.g. Liverpool → London
// ============================================================

import React, { useState } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TextInput,
  TouchableOpacity,
  ActivityIndicator,
  Linking,
} from 'react-native';
import { colors, typography, spacing, borderRadius } from '../theme';
import { Button, Card, Badge } from '../components';
import { planRoute, formatRouteSummary } from '../services/routePlanning';
import type { RoutePlan } from '../services/routePlanning';
import type { Facility } from '../types';
import { PremiumGate } from '../components';

const SUGGESTED_ROUTES = [
  { from: 'Liverpool', to: 'London' },
  { from: 'Manchester', to: 'Birmingham' },
  { from: 'Birmingham', to: 'Bristol' },
  { from: 'Leeds', to: 'London' },
  { from: 'Edinburgh', to: 'Glasgow' },
  { from: 'London', to: 'Brighton' },
];

export const RoutePlanningScreen: React.FC = () => {
  const [from, setFrom] = useState('');
  const [to, setTo] = useState('');
  const [planning, setPlanning] = useState(false);
  const [routePlan, setRoutePlan] = useState<RoutePlan | null>(null);
  const [error, setError] = useState<string | null>(null);

  const handlePlan = async () => {
    if (!from.trim() || !to.trim()) return;

    setPlanning(true);
    setError(null);
    setRoutePlan(null);

    const result = await planRoute(from.trim(), to.trim());

    if ('error' in result) {
      setError(result.error);
    } else {
      setRoutePlan(result);
    }

    setPlanning(false);
  };

  const handleSuggestedRoute = (route: { from: string; to: string }) => {
    setFrom(route.from);
    setTo(route.to);
    // Auto-plan after a short delay
    setTimeout(() => {
      planRoute(route.from, route.to).then((result) => {
        if ('error' in result) {
          setError(result.error);
        } else {
          setRoutePlan(result);
        }
      });
    }, 100);
  };

  const handleOpenDirections = (facility: Facility) => {
    Linking.openURL(
      `https://maps.google.com/?daddr=${facility.latitude},${facility.longitude}`,
    );
  };

  return (
    <PremiumGate feature="route_planning">
    <ScrollView style={styles.container} contentContainerStyle={styles.content}>
      <Text style={styles.title}>Route Planning</Text>
      <Text style={styles.subtitle}>
        Plan a journey with suggested comfort stops every 60-90 minutes.
      </Text>

      {/* Input Fields */}
      <Card variant="outlined" style={styles.inputCard}>
        <Text style={styles.label}>From</Text>
        <TextInput
          style={styles.input}
          value={from}
          onChangeText={setFrom}
          placeholder="e.g. Liverpool"
          placeholderTextColor={colors.textMuted}
        />

        <Text style={styles.label}>To</Text>
        <TextInput
          style={styles.input}
          value={to}
          onChangeText={setTo}
          placeholder="e.g. London"
          placeholderTextColor={colors.textMuted}
        />

        <Button
          title={planning ? 'Planning...' : 'Plan Route'}
          onPress={handlePlan}
          loading={planning}
          disabled={!from.trim() || !to.trim()}
          fullWidth
          style={styles.planButton}
        />
      </Card>

      {/* Suggested Routes */}
      <Text style={styles.sectionTitle}>Popular Routes</Text>
      <View style={styles.suggestedGrid}>
        {SUGGESTED_ROUTES.map((route) => (
          <TouchableOpacity
            key={`${route.from}-${route.to}`}
            style={styles.suggestedChip}
            onPress={() => handleSuggestedRoute(route)}
          >
            <Text style={styles.suggestedText}>
              {route.from} → {route.to}
            </Text>
          </TouchableOpacity>
        ))}
      </View>

      {/* Error */}
      {error && (
        <Card variant="outlined" style={styles.errorCard}>
          <Text style={styles.errorText}>{error}</Text>
        </Card>
      )}

      {/* Route Plan Results */}
      {routePlan && (
        <>
          {/* Summary */}
          <Card variant="elevated" style={styles.summaryCard}>
            <Text style={styles.summaryRoute}>
              {routePlan.from} → {routePlan.to}
            </Text>
            <View style={styles.summaryStats}>
              <View style={styles.stat}>
                <Text style={styles.statValue}>
                  {routePlan.totalDistanceKm} km
                </Text>
                <Text style={styles.statLabel}>Distance</Text>
              </View>
              <View style={styles.stat}>
                <Text style={styles.statValue}>
                  {Math.floor(routePlan.estimatedDrivingMinutes / 60)}h{' '}
                  {routePlan.estimatedDrivingMinutes % 60}m
                </Text>
                <Text style={styles.statLabel}>Driving Time</Text>
              </View>
              <View style={styles.stat}>
                <Text style={styles.statValue}>{routePlan.comfortStops.length}</Text>
                <Text style={styles.statLabel}>Comfort Stops</Text>
              </View>
            </View>
          </Card>

          {/* Comfort Stops */}
          <Text style={styles.sectionTitle}>Suggested Comfort Stops</Text>
          {routePlan.comfortStops.length === 0 ? (
            <Card variant="outlined" style={styles.noStopsCard}>
              <Text style={styles.noStopsText}>
                No comfort stops needed for this short journey.
              </Text>
            </Card>
          ) : (
            routePlan.comfortStops.map((stop, index) => (
              <Card key={index} variant="outlined" style={styles.stopCard}>
                <View style={styles.stopHeader}>
                  <View style={styles.stopNumberBadge}>
                    <Text style={styles.stopNumberText}>{index + 1}</Text>
                  </View>
                  <View style={styles.stopInfo}>
                    <Text style={styles.stopName}>{stop.facility.name}</Text>
                    <Text style={styles.stopAddress}>
                      {stop.facility.address}
                    </Text>
                  </View>
                </View>

                <View style={styles.stopMeta}>
                  <View style={styles.stopMetaItem}>
                    <Text style={styles.stopMetaLabel}>Arrival</Text>
                    <Text style={styles.stopMetaValue}>
                      ~{Math.floor(stop.estimatedArrivalMinutes / 60)}h{' '}
                      {stop.estimatedArrivalMinutes % 60}m
                    </Text>
                  </View>
                  <View style={styles.stopMetaItem}>
                    <Text style={styles.stopMetaLabel}>Rating</Text>
                    <Text style={styles.stopMetaValue}>
                      ★ {stop.facility.overall_score.toFixed(1)}
                    </Text>
                  </View>
                  <View style={styles.stopMetaItem}>
                    <Text style={styles.stopMetaLabel}>Stop</Text>
                    <Text style={styles.stopMetaValue}>
                      {stop.stopDurationMinutes} min
                    </Text>
                  </View>
                </View>

                <View style={styles.stopBadges}>
                  {stop.facility.is_24h && (
                    <Badge label="24h" variant="success" size="sm" />
                  )}
                  {stop.facility.is_free && (
                    <Badge label="Free" variant="success" size="sm" />
                  )}
                  {stop.facility.is_accessible && (
                    <Badge label="Accessible" variant="info" size="sm" />
                  )}
                </View>

                <Button
                  title="Get Directions"
                  onPress={() => handleOpenDirections(stop.facility)}
                  size="sm"
                  variant="outline"
                  fullWidth
                  style={styles.directionsButton}
                />
              </Card>
            ))
          )}

          {/* Route Summary Text */}
          <Card variant="glass" style={styles.summaryTextCard}>
            <Text style={styles.summaryTextTitle}>📋 Route Summary</Text>
            <Text style={styles.summaryTextBody}>
              {formatRouteSummary(routePlan)}
            </Text>
          </Card>
        </>
      )}
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
  inputCard: {
    marginBottom: spacing.lg,
  },
  label: {
    fontFamily: 'Inter_500Medium',
    fontSize: 14,
    fontWeight: '500',
    color: colors.textPrimary,
    marginBottom: spacing.xs,
    marginTop: spacing.sm,
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
  planButton: {
    marginTop: spacing.lg,
  },
  sectionTitle: {
    fontFamily: 'PlusJakartaSans_600SemiBold',
    fontSize: 18,
    fontWeight: '600',
    color: colors.textPrimary,
    marginBottom: spacing.md,
    marginTop: spacing.md,
  },
  suggestedGrid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: spacing.sm,
    marginBottom: spacing.lg,
  },
  suggestedChip: {
    backgroundColor: colors.white,
    borderRadius: borderRadius.full,
    paddingVertical: spacing.sm,
    paddingHorizontal: spacing.lg,
    borderWidth: 1,
    borderColor: colors.border,
  },
  suggestedText: {
    fontFamily: 'Inter_500Medium',
    fontSize: 13,
    fontWeight: '500',
    color: colors.primary,
  },
  errorCard: {
    backgroundColor: '#FEE2E2',
    borderColor: colors.error,
    marginBottom: spacing.lg,
  },
  errorText: {
    fontFamily: 'Inter_400Regular',
    fontSize: 14,
    color: colors.error,
  },
  summaryCard: {
    marginBottom: spacing.lg,
  },
  summaryRoute: {
    fontFamily: 'PlusJakartaSans_600SemiBold',
    fontSize: 20,
    fontWeight: '600',
    color: colors.textPrimary,
    textAlign: 'center',
    marginBottom: spacing.lg,
  },
  summaryStats: {
    flexDirection: 'row',
    justifyContent: 'space-around',
  },
  stat: {
    alignItems: 'center',
  },
  statValue: {
    fontFamily: 'Inter_700Bold',
    fontSize: 18,
    fontWeight: '700',
    color: colors.primary,
  },
  statLabel: {
    fontFamily: 'Inter_400Regular',
    fontSize: 12,
    color: colors.textSecondary,
    marginTop: 2,
  },
  noStopsCard: {
    marginBottom: spacing.lg,
  },
  noStopsText: {
    fontFamily: 'Inter_400Regular',
    fontSize: 14,
    color: colors.textSecondary,
    textAlign: 'center',
  },
  stopCard: {
    marginBottom: spacing.md,
  },
  stopHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: spacing.md,
  },
  stopNumberBadge: {
    width: 32,
    height: 32,
    borderRadius: 16,
    backgroundColor: colors.primary,
    justifyContent: 'center',
    alignItems: 'center',
    marginRight: spacing.md,
  },
  stopNumberText: {
    fontFamily: 'Inter_700Bold',
    fontSize: 14,
    fontWeight: '700',
    color: colors.white,
  },
  stopInfo: {
    flex: 1,
  },
  stopName: {
    fontFamily: 'Inter_600SemiBold',
    fontSize: 16,
    fontWeight: '600',
    color: colors.textPrimary,
  },
  stopAddress: {
    fontFamily: 'Inter_400Regular',
    fontSize: 13,
    color: colors.textSecondary,
    marginTop: 2,
  },
  stopMeta: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    marginBottom: spacing.sm,
  },
  stopMetaItem: {
    alignItems: 'center',
  },
  stopMetaLabel: {
    fontFamily: 'Inter_400Regular',
    fontSize: 11,
    color: colors.textMuted,
  },
  stopMetaValue: {
    fontFamily: 'Inter_600SemiBold',
    fontSize: 14,
    fontWeight: '600',
    color: colors.textPrimary,
    marginTop: 2,
  },
  stopBadges: {
    flexDirection: 'row',
    gap: spacing.xs,
    marginBottom: spacing.md,
  },
  directionsButton: {
    marginTop: spacing.xs,
  },
  summaryTextCard: {
    marginTop: spacing.lg,
  },
  summaryTextTitle: {
    fontFamily: 'Inter_600SemiBold',
    fontSize: 15,
    fontWeight: '600',
    color: colors.textPrimary,
    marginBottom: spacing.sm,
  },
  summaryTextBody: {
    fontFamily: 'Inter_400Regular',
    fontSize: 13,
    color: colors.textSecondary,
    lineHeight: 20,
  },
});
// ============================================================
// Project "Relief" — Notification Alerts Screen (4.5)
// Manage closure alerts and favourite facility updates
// ============================================================

import React, { useState, useEffect, useCallback } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  Switch,
  TouchableOpacity,
  Alert,
} from 'react-native';
import { colors, typography, spacing, borderRadius } from '../theme';
import { Button, Card, Badge } from '../components';
import {
  getAlertPreferences,
  saveAlertPreferences,
  checkFavouriteFacilityAlerts,
} from '../services/notificationAlerts';
import { getFavourites } from '../services/favourites';
import { useNavigation, NavigationProp, useFocusEffect } from '@react-navigation/native';
import type { AlertPreference } from '../services/notificationAlerts';
import type { Favourite } from '../types';

export const NotificationAlertsScreen: React.FC = () => {
  const navigation = useNavigation<NavigationProp<any>>();
  const [preferences, setPreferences] = useState<AlertPreference[]>([]);
  const [favourites, setFavourites] = useState<Favourite[]>([]);
  const [loading, setLoading] = useState(true);

  useFocusEffect(
    useCallback(() => {
      loadData();
    }, []),
  );

  const loadData = async () => {
    setLoading(true);
    const [prefs, favs] = await Promise.all([
      getAlertPreferences(),
      getFavourites(),
    ]);
    setPreferences(prefs);
    setFavourites(favs);
    setLoading(false);
  };

  const toggleAlerts = async (facilityId: string, enabled: boolean) => {
    const updated = preferences.map((p) =>
      p.facilityId === facilityId ? { ...p, alertsEnabled: enabled } : p,
    );

    if (enabled && !updated.find((p) => p.facilityId === facilityId)) {
      // Need to create a new preference entry
      const facility = favourites.find((f) => f.facility_id === facilityId);
      if (facility) {
        updated.push({
          facilityId,
          facilityName: '',
          alertsEnabled: true,
          closureAlerts: true,
          updateAlerts: true,
        });
      }
    }

    setPreferences(updated);
    await saveAlertPreferences(updated);
  };

  const toggleClosureAlerts = async (facilityId: string) => {
    const updated = preferences.map((p) =>
      p.facilityId === facilityId
        ? { ...p, closureAlerts: !p.closureAlerts }
        : p,
    );
    setPreferences(updated);
    await saveAlertPreferences(updated);
  };

  const toggleUpdateAlerts = async (facilityId: string) => {
    const updated = preferences.map((p) =>
      p.facilityId === facilityId
        ? { ...p, updateAlerts: !p.updateAlerts }
        : p,
    );
    setPreferences(updated);
    await saveAlertPreferences(updated);
  };

  const handleCheckNow = async () => {
    await checkFavouriteFacilityAlerts();
    Alert.alert('Checked', 'Alert check complete. Any new alerts will appear as notifications.');
  };

  const getPrefForFacility = (facilityId: string): AlertPreference | undefined => {
    return preferences.find((p) => p.facilityId === facilityId);
  };

  return (
    <ScrollView style={styles.container} contentContainerStyle={styles.content}>
      <Text style={styles.title}>Notification Alerts</Text>
      <Text style={styles.subtitle}>
        Get notified when your favourite facilities have closures, are busy, or
        have other status updates.
      </Text>

      {/* Check Now */}
      <Card variant="glass" style={styles.checkCard}>
        <Text style={styles.checkTitle}>🔔 Check for Updates</Text>
        <Text style={styles.checkText}>
          Manually check all your favourited facilities for active reports.
        </Text>
        <Button
          title="Check Now"
          onPress={handleCheckNow}
          size="sm"
          fullWidth
        />
      </Card>

      {/* Favourite Facilities */}
      <Text style={styles.sectionTitle}>Favourite Facilities</Text>

      {favourites.length === 0 ? (
        <Card variant="outlined" style={styles.emptyCard}>
          <Text style={styles.emptyText}>
            No favourites yet. Add facilities to your favourites to manage
            alerts for them.
          </Text>
        </Card>
      ) : (
        favourites.map((fav) => {
          const pref = getPrefForFacility(fav.facility_id);
          const isEnabled = pref?.alertsEnabled ?? false;

          return (
            <Card key={fav.id} variant="outlined" style={styles.facilityCard}>
              <View style={styles.facilityHeader}>
                <View style={styles.facilityInfo}>
                  <Text style={styles.facilityIdText}>
                    Facility ID: {fav.facility_id.slice(0, 8)}...
                  </Text>
                </View>
                <Switch
                  value={isEnabled}
                  onValueChange={(val) => toggleAlerts(fav.facility_id, val)}
                  trackColor={{ true: colors.primaryLight, false: colors.gray200 }}
                  thumbColor={isEnabled ? colors.primary : colors.gray400}
                />
              </View>

              {isEnabled && (
                <View style={styles.alertOptions}>
                  <View style={styles.optionRow}>
                    <View style={styles.optionInfo}>
                      <Text style={styles.optionLabel}>⚠️ Closure Alerts</Text>
                      <Text style={styles.optionDesc}>
                        Closed, out of order, refurbishment
                      </Text>
                    </View>
                    <Switch
                      value={pref?.closureAlerts ?? true}
                      onValueChange={() => toggleClosureAlerts(fav.facility_id)}
                      trackColor={{ true: colors.primaryLight, false: colors.gray200 }}
                      thumbColor={pref?.closureAlerts ? colors.primary : colors.gray400}
                    />
                  </View>

                  <View style={styles.optionRow}>
                    <View style={styles.optionInfo}>
                      <Text style={styles.optionLabel}>📢 Update Alerts</Text>
                      <Text style={styles.optionDesc}>
                        Cleaning, busy, no water
                      </Text>
                    </View>
                    <Switch
                      value={pref?.updateAlerts ?? true}
                      onValueChange={() => toggleUpdateAlerts(fav.facility_id)}
                      trackColor={{ true: colors.primaryLight, false: colors.gray200 }}
                      thumbColor={pref?.updateAlerts ? colors.primary : colors.gray400}
                    />
                  </View>
                </View>
              )}
            </Card>
          );
        })
      )}

      {/* Info */}
      <Card variant="glass" style={styles.infoCard}>
        <Text style={styles.infoTitle}>ℹ️ About Alerts</Text>
        <Text style={styles.infoText}>
          Alerts are checked every 30 minutes while the app is running. You'll
          receive a local notification when a status change is detected for your
          favourited facilities. Duplicate alerts are suppressed for 1 hour.
        </Text>
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
  checkCard: {
    marginBottom: spacing.lg,
  },
  checkTitle: {
    fontFamily: 'Inter_600SemiBold',
    fontSize: 16,
    fontWeight: '600',
    color: colors.textPrimary,
    marginBottom: spacing.xs,
  },
  checkText: {
    fontFamily: 'Inter_400Regular',
    fontSize: 13,
    color: colors.textSecondary,
    marginBottom: spacing.md,
  },
  sectionTitle: {
    fontFamily: 'PlusJakartaSans_600SemiBold',
    fontSize: 18,
    fontWeight: '600',
    color: colors.textPrimary,
    marginBottom: spacing.md,
  },
  emptyCard: {
    marginBottom: spacing.lg,
  },
  emptyText: {
    fontFamily: 'Inter_400Regular',
    fontSize: 14,
    color: colors.textSecondary,
    textAlign: 'center',
  },
  facilityCard: {
    marginBottom: spacing.md,
  },
  facilityHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  facilityInfo: {
    flex: 1,
    marginRight: spacing.md,
  },
  facilityIdText: {
    fontFamily: 'Inter_500Medium',
    fontSize: 14,
    fontWeight: '500',
    color: colors.textPrimary,
  },
  alertOptions: {
    marginTop: spacing.md,
    paddingTop: spacing.md,
    borderTopWidth: 1,
    borderTopColor: colors.gray100,
  },
  optionRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingVertical: spacing.sm,
  },
  optionInfo: {
    flex: 1,
    marginRight: spacing.md,
  },
  optionLabel: {
    fontFamily: 'Inter_500Medium',
    fontSize: 14,
    fontWeight: '500',
    color: colors.textPrimary,
  },
  optionDesc: {
    fontFamily: 'Inter_400Regular',
    fontSize: 12,
    color: colors.textSecondary,
    marginTop: 2,
  },
  infoCard: {
    marginTop: spacing.lg,
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
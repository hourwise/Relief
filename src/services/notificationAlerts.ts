// ============================================================
// Project "Relief" — Notification Alerts Service (4.5)
// Closure alerts, favourite facility updates
// Checks active reports on favourited facilities
// ============================================================

import * as Notifications from 'expo-notifications';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { supabase } from './supabase';
import { getFavourites } from './favourites';
import { getActiveReports } from './community';
import type { TemporaryReport } from '../types/community';
import type { Favourite } from '../types';

export interface AlertPreference {
  facilityId: string;
  facilityName: string;
  alertsEnabled: boolean;
  closureAlerts: boolean;
  updateAlerts: boolean;
}

const ALERT_PREFS_KEY = 'relief_alert_preferences';

/**
 * Check all favourited facilities for active reports and notify if needed.
 * Call this on app foreground and periodically.
 */
export async function checkFavouriteFacilityAlerts(): Promise<void> {
  try {
    const favourites = await getFavourites();
    if (favourites.length === 0) return;

    const prefs = await getAlertPreferences();

    for (const fav of favourites) {
      const pref = prefs.find((p) => p.facilityId === fav.facility_id);
      if (!pref || !pref.alertsEnabled) continue;

      // Get the facility name
      const { data: facility } = await supabase
        .from('facilities')
        .select('name')
        .eq('id', fav.facility_id)
        .single();

      if (!facility) continue;

      // Check for active reports on this facility
      const activeReports = await getActiveReports(fav.facility_id);

      // Send closure alert
      if (pref.closureAlerts) {
        const closureReports = activeReports.filter(
          (r) => r.type === 'closed' || r.type === 'out_of_order' || r.type === 'refurbishment',
        );

        for (const report of closureReports) {
          await sendAlertNotification(
            `⚠️ ${facility.name} - ${formatReportType(report.type)}`,
            report.notes || `This facility has been reported as ${report.type}.`,
          );
        }
      }

      // Send update alerts
      if (pref.updateAlerts && activeReports.length > 0) {
        const updateReports = activeReports.filter(
          (r) => r.type === 'cleaning' || r.type === 'busy' || r.type === 'no_water',
        );

        for (const report of updateReports) {
          await sendAlertNotification(
            `📢 ${facility.name} Update`,
            report.notes || `Status: ${formatReportType(report.type)}`,
          );
        }
      }
    }
  } catch (err) {
    console.error('Error checking favourite facility alerts:', err);
  }
}

/**
 * Send a local push notification for an alert.
 * Uses a cooldown to avoid duplicate alerts within 1 hour.
 */
const alertSentTimestamps: Record<string, number> = {};

async function sendAlertNotification(
  title: string,
  body: string,
): Promise<void> {
  const key = `${title}:${body}`;
  const lastSent = alertSentTimestamps[key];
  const cooldownMs = 60 * 60 * 1000; // 1 hour cooldown

  if (lastSent && Date.now() - lastSent < cooldownMs) {
    return; // Skip duplicate alert within cooldown
  }

  alertSentTimestamps[key] = Date.now();

  await Notifications.scheduleNotificationAsync({
    content: {
      title,
      body,
      sound: true,
      priority: Notifications.AndroidNotificationPriority.HIGH,
    },
    trigger: {
      type: Notifications.SchedulableTriggerInputTypes.TIME_INTERVAL,
      seconds: 1,
    },
  });
}

/**
 * Get alert preferences from local storage.
 */
export async function getAlertPreferences(): Promise<AlertPreference[]> {
  try {
    const stored = await AsyncStorage.getItem(ALERT_PREFS_KEY);
    return stored ? JSON.parse(stored) : [];
  } catch {
    return [];
  }
}

/**
 * Save alert preferences to local storage.
 */
export async function saveAlertPreferences(
  prefs: AlertPreference[],
): Promise<void> {
  try {
    await AsyncStorage.setItem(ALERT_PREFS_KEY, JSON.stringify(prefs));
  } catch (err) {
    console.error('Error saving alert preferences:', err);
  }
}

/**
 * Enable alerts for a specific facility.
 */
export async function enableAlertsForFacility(
  facilityId: string,
  facilityName: string,
): Promise<void> {
  const prefs = await getAlertPreferences();
  const existing = prefs.find((p) => p.facilityId === facilityId);

  if (existing) {
    existing.alertsEnabled = true;
    existing.closureAlerts = true;
    existing.updateAlerts = true;
  } else {
    prefs.push({
      facilityId,
      facilityName,
      alertsEnabled: true,
      closureAlerts: true,
      updateAlerts: true,
    });
  }

  await saveAlertPreferences(prefs);
}

/**
 * Disable alerts for a specific facility.
 */
export async function disableAlertsForFacility(
  facilityId: string,
): Promise<void> {
  const prefs = await getAlertPreferences();
  const existing = prefs.find((p) => p.facilityId === facilityId);
  if (existing) {
    existing.alertsEnabled = false;
  }
  await saveAlertPreferences(prefs);
}

/**
 * Check if alerts are enabled for a facility.
 */
export async function areAlertsEnabledForFacility(
  facilityId: string,
): Promise<boolean> {
  const prefs = await getAlertPreferences();
  const pref = prefs.find((p) => p.facilityId === facilityId);
  return pref?.alertsEnabled ?? false;
}

/**
 * Format a report type string to a readable label.
 */
function formatReportType(type: string): string {
  const labels: Record<string, string> = {
    closed: 'Closed',
    out_of_order: 'Out of Order',
    refurbishment: 'Under Refurbishment',
    cleaning: 'Being Cleaned',
    busy: 'Very Busy',
    no_water: 'No Water',
  };
  return labels[type] || type;
}

/**
 * Schedule periodic alert checking (every 30 minutes while app is in use).
 */
let alertCheckInterval: ReturnType<typeof setInterval> | null = null;

export function startPeriodicAlertCheck(): void {
  if (alertCheckInterval) return;

  // Check immediately on start
  checkFavouriteFacilityAlerts();

  // Then every 30 minutes
  alertCheckInterval = setInterval(() => {
    checkFavouriteFacilityAlerts();
  }, 30 * 60 * 1000);
}

export function stopPeriodicAlertCheck(): void {
  if (alertCheckInterval) {
    clearInterval(alertCheckInterval);
    alertCheckInterval = null;
  }
}
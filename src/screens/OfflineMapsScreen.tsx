// ============================================================
// Project "Relief" — Offline Maps Screen (4.4)
// Download facility regions for offline use
// ============================================================

import React, { useState, useEffect, useCallback } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TouchableOpacity,
  TextInput,
  Alert,
  ActivityIndicator,
} from 'react-native';
import { colors, typography, spacing, borderRadius } from '../theme';
import { Button, Card, Badge } from '../components';
import {
  downloadRegion,
  getDownloadedRegions,
  deleteRegion,
  getOfflineStorageSize,
  formatBytes,
  isRegionDownloaded,
} from '../services/offlineMaps';
import { useNavigation, NavigationProp, useFocusEffect } from '@react-navigation/native';
import { PremiumGate } from '../components';
import type { DownloadedRegion } from '../services/offlineMaps';

const POPULAR_TOWNS = [
  'London', 'Manchester', 'Birmingham', 'Liverpool',
  'Leeds', 'Glasgow', 'Edinburgh', 'Bristol',
  'Brighton', 'Oxford', 'Cambridge', 'Cardiff',
];

export const OfflineMapsScreen: React.FC = () => {
  const navigation = useNavigation<NavigationProp<any>>();
  const [regions, setRegions] = useState<DownloadedRegion[]>([]);
  const [storageSize, setStorageSize] = useState(0);
  const [loading, setLoading] = useState(true);
  const [downloading, setDownloading] = useState<string | null>(null);
  const [downloadProgress, setDownloadProgress] = useState(0);
  const [downloadTotal, setDownloadTotal] = useState(0);
  const [customTown, setCustomTown] = useState('');

  useFocusEffect(
    useCallback(() => {
      loadData();
    }, []),
  );

  const loadData = async () => {
    setLoading(true);
    const [downloaded, size] = await Promise.all([
      getDownloadedRegions(),
      getOfflineStorageSize(),
    ]);
    setRegions(downloaded);
    setStorageSize(size);
    setLoading(false);
  };

  const handleDownload = async (town: string) => {
    if (downloading) return;

    const alreadyDownloaded = await isRegionDownloaded(town);
    if (alreadyDownloaded) {
      Alert.alert('Already Downloaded', `${town} is already downloaded.`);
      return;
    }

    setDownloading(town);
    setDownloadProgress(0);
    setDownloadTotal(0);

    const result = await downloadRegion(town, (current, total) => {
      setDownloadProgress(current);
      setDownloadTotal(total);
    });

    setDownloading(null);

    if (result.success) {
      Alert.alert('Downloaded', `Successfully downloaded ${town} area (${result.region?.facilityCount} facilities).`);
      loadData();
    } else {
      Alert.alert('Error', result.error || 'Failed to download region');
    }
  };

  const handleDelete = (region: DownloadedRegion) => {
    Alert.alert(
      'Delete Region',
      `Delete "${region.name}" (${region.facilityCount} facilities)?`,
      [
        { text: 'Cancel', style: 'cancel' },
        {
          text: 'Delete',
          style: 'destructive',
          onPress: async () => {
            await deleteRegion(region.id);
            loadData();
          },
        },
      ],
    );
  };

  const handleCustomDownload = () => {
    const town = customTown.trim();
    if (!town) {
      Alert.alert('Required', 'Please enter a town or city name');
      return;
    }
    handleDownload(town);
    setCustomTown('');
  };

  return (
    <PremiumGate feature="offline_maps">
    <ScrollView style={styles.container} contentContainerStyle={styles.content}>
      <Text style={styles.title}>Offline Maps</Text>
      <Text style={styles.subtitle}>
        Download facility data for towns and cities to use offline when you
        don't have an internet connection.
      </Text>

      {/* Storage Info */}
      <Card variant="glass" style={styles.storageCard}>
        <Text style={styles.storageTitle}>💾 Storage Used</Text>
        <Text style={styles.storageValue}>
          {formatBytes(storageSize)}
        </Text>
        <Text style={styles.storageSub}>
          {regions.length} region{regions.length !== 1 ? 's' : ''} downloaded
        </Text>
      </Card>

      {/* Custom Download */}
      <Card variant="outlined" style={styles.customCard}>
        <Text style={styles.customTitle}>Download a Town/City</Text>
        <View style={styles.customRow}>
          <TextInput
            style={styles.customInput}
            value={customTown}
            onChangeText={setCustomTown}
            placeholder="e.g. Sheffield"
            placeholderTextColor={colors.textMuted}
          />
          <Button
            title="Download"
            onPress={handleCustomDownload}
            loading={downloading !== null}
            disabled={!customTown.trim() || downloading !== null}
            size="sm"
          />
        </View>
      </Card>

      {/* Popular Towns */}
      <Text style={styles.sectionTitle}>Popular Towns & Cities</Text>
      <View style={styles.townGrid}>
        {POPULAR_TOWNS.map((town) => {
          const isDownloading = downloading === town;
          const progress = downloadTotal > 0
            ? Math.round((downloadProgress / downloadTotal) * 100)
            : 0;

          return (
            <TouchableOpacity
              key={town}
              style={[
                styles.townCard,
                regions.some((r) => r.town === town) && styles.townCardDownloaded,
              ]}
              onPress={() => handleDownload(town)}
              disabled={isDownloading}
              activeOpacity={0.7}
            >
              <Text style={styles.townName}>{town}</Text>
              {regions.some((r) => r.town === town) ? (
                <Badge label="Downloaded" variant="success" size="sm" />
              ) : isDownloading ? (
                <View style={styles.progressContainer}>
                  <ActivityIndicator size="small" color={colors.primary} />
                  <Text style={styles.progressText}>{progress}%</Text>
                </View>
              ) : (
                <Text style={styles.downloadAction}>Download</Text>
              )}
            </TouchableOpacity>
          );
        })}
      </View>

      {/* Downloaded Regions */}
      {regions.length > 0 && (
        <>
          <Text style={styles.sectionTitle}>Downloaded Regions</Text>
          {regions.map((region) => (
            <Card key={region.id} variant="outlined" style={styles.regionCard}>
              <View style={styles.regionHeader}>
                <View style={styles.regionInfo}>
                  <Text style={styles.regionName}>{region.name}</Text>
                  <Text style={styles.regionMeta}>
                    {region.facilityCount} facilities • {formatBytes(region.sizeBytes)}
                  </Text>
                  <Text style={styles.regionDate}>
                    Downloaded {new Date(region.downloadedAt).toLocaleDateString()}
                  </Text>
                </View>
                <TouchableOpacity
                  onPress={() => handleDelete(region)}
                  style={styles.deleteButton}
                >
                  <Text style={styles.deleteText}>🗑️</Text>
                </TouchableOpacity>
              </View>
            </Card>
          ))}
        </>
      )}

      {/* Info */}
      <Card variant="glass" style={styles.infoCard}>
        <Text style={styles.infoTitle}>ℹ️ About Offline Maps</Text>
        <Text style={styles.infoText}>
          Downloaded regions store facility data locally on your device. You can
          browse facilities, view details, and get directions even without an
          internet connection. Map tiles are not stored — directions will open
          in your default maps app.
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
  storageCard: {
    marginBottom: spacing.lg,
    alignItems: 'center',
  },
  storageTitle: {
    fontFamily: 'Inter_600SemiBold',
    fontSize: 15,
    fontWeight: '600',
    color: colors.textPrimary,
    marginBottom: spacing.xs,
  },
  storageValue: {
    fontFamily: 'PlusJakartaSans_700Bold',
    fontSize: 32,
    fontWeight: '700',
    color: colors.primary,
  },
  storageSub: {
    fontFamily: 'Inter_400Regular',
    fontSize: 13,
    color: colors.textSecondary,
    marginTop: spacing.xs,
  },
  customCard: {
    marginBottom: spacing.lg,
  },
  customTitle: {
    fontFamily: 'Inter_600SemiBold',
    fontSize: 15,
    fontWeight: '600',
    color: colors.textPrimary,
    marginBottom: spacing.md,
  },
  customRow: {
    flexDirection: 'row',
    gap: spacing.sm,
    alignItems: 'center',
  },
  customInput: {
    flex: 1,
    fontFamily: 'Inter_400Regular',
    fontSize: 16,
    color: colors.textPrimary,
    backgroundColor: colors.white,
    borderWidth: 1,
    borderColor: colors.border,
    borderRadius: borderRadius.md,
    padding: spacing.md,
  },
  sectionTitle: {
    fontFamily: 'PlusJakartaSans_600SemiBold',
    fontSize: 18,
    fontWeight: '600',
    color: colors.textPrimary,
    marginBottom: spacing.md,
    marginTop: spacing.md,
  },
  townGrid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: spacing.sm,
    marginBottom: spacing.lg,
  },
  townCard: {
    width: '48%',
    backgroundColor: colors.white,
    borderRadius: borderRadius['2xl'],
    padding: spacing.lg,
    borderWidth: 1,
    borderColor: colors.border,
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  townCardDownloaded: {
    borderColor: colors.success,
    backgroundColor: colors.tealSoft,
  },
  townName: {
    fontFamily: 'Inter_600SemiBold',
    fontSize: 15,
    fontWeight: '600',
    color: colors.textPrimary,
  },
  downloadAction: {
    fontFamily: 'Inter_500Medium',
    fontSize: 12,
    fontWeight: '500',
    color: colors.primary,
  },
  progressContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: spacing.xs,
  },
  progressText: {
    fontFamily: 'Inter_500Medium',
    fontSize: 12,
    fontWeight: '500',
    color: colors.primary,
  },
  regionCard: {
    marginBottom: spacing.md,
  },
  regionHeader: {
    flexDirection: 'row',
    alignItems: 'flex-start',
  },
  regionInfo: {
    flex: 1,
  },
  regionName: {
    fontFamily: 'Inter_600SemiBold',
    fontSize: 16,
    fontWeight: '600',
    color: colors.textPrimary,
    marginBottom: 2,
  },
  regionMeta: {
    fontFamily: 'Inter_400Regular',
    fontSize: 13,
    color: colors.textSecondary,
  },
  regionDate: {
    fontFamily: 'Inter_400Regular',
    fontSize: 12,
    color: colors.textMuted,
    marginTop: 2,
  },
  deleteButton: {
    padding: spacing.sm,
  },
  deleteText: {
    fontSize: 20,
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
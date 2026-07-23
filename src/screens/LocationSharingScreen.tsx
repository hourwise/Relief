// ============================================================
// Project "Relief" — Location Sharing Screen (4.6-4.12)
// Share exact location via What3Words, Plus Codes, coordinates,
// SMS/messaging, and emergency location card
// ============================================================

import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TouchableOpacity,
  Alert,
  ActivityIndicator,
} from 'react-native';
import { colors, typography, spacing, borderRadius } from '../theme';
import { Button, Card, Badge } from '../components';
import { useLocation } from '../hooks/useLocation';
import {
  coordsToWhat3Words,
  coordsToPlusCode,
  copyWhat3WordsToClipboard,
  copyCoordinatesToClipboard,
  shareLocation,
  shareEmergencyCard,
  openWhat3Words,
  openPlusCode,
} from '../services/locationSharing';
import { useNavigation, NavigationProp } from '@react-navigation/native';

export const LocationSharingScreen: React.FC = () => {
  const navigation = useNavigation<NavigationProp<any>>();
  const { location, loading: locationLoading, refreshLocation } = useLocation();
  const [w3w, setW3w] = useState<string | null>(null);
  const [plusCode, setPlusCode] = useState<string | null>(null);
  const [loadingW3W, setLoadingW3W] = useState(false);
  const [copiedField, setCopiedField] = useState<string | null>(null);

  useEffect(() => {
    if (location) {
      generateLocationData();
    }
  }, [location]);

  const generateLocationData = async () => {
    if (!location) return;

    // Generate Plus Code (client-side)
    const pc = coordsToPlusCode(location.latitude, location.longitude);
    setPlusCode(pc);

    // Fetch What3Words
    setLoadingW3W(true);
    const result = await coordsToWhat3Words(location.latitude, location.longitude);
    setW3w(result.words);
    setLoadingW3W(false);
  };

  const handleCopy = async (field: string, action: () => Promise<void>) => {
    await action();
    setCopiedField(field);
    setTimeout(() => setCopiedField(null), 2000);
  };

  const handleShare = () => {
    if (!location) return;
    shareLocation(location.latitude, location.longitude);
  };

  const handleEmergencyCard = () => {
    if (!location) return;
    shareEmergencyCard(
      location.latitude,
      location.longitude,
      w3w || undefined,
      plusCode || undefined,
    );
  };

  if (locationLoading) {
    return (
      <View style={styles.centered}>
        <ActivityIndicator size="large" color={colors.primary} />
        <Text style={styles.loadingText}>Getting your location...</Text>
      </View>
    );
  }

  if (!location) {
    return (
      <View style={styles.centered}>
        <Text style={styles.emptyIcon}>📍</Text>
        <Text style={styles.emptyTitle}>Location Required</Text>
        <Text style={styles.emptySubtitle}>
          Enable location access to use location sharing features.
        </Text>
        <Button
          title="Enable Location"
          onPress={refreshLocation}
          style={styles.enableButton}
        />
      </View>
    );
  }

  const coords = `${location.latitude.toFixed(6)}, ${location.longitude.toFixed(6)}`;

  return (
    <ScrollView style={styles.container} contentContainerStyle={styles.content}>
      <Text style={styles.title}>Share Location</Text>
      <Text style={styles.subtitle}>
        Share your precise location using coordinates, What3Words, or Plus Codes.
      </Text>

      {/* Current Coordinates */}
      <Card variant="elevated" style={styles.coordsCard}>
        <Text style={styles.coordsLabel}>Your Current Location</Text>
        <Text style={styles.coordsValue}>{coords}</Text>
        <TouchableOpacity
          style={styles.copyButton}
          onPress={() =>
            handleCopy('coords', () =>
              copyCoordinatesToClipboard(location.latitude, location.longitude),
            )
          }
        >
          <Text style={styles.copyText}>
            {copiedField === 'coords' ? '✓ Copied!' : '📋 Copy Coordinates'}
          </Text>
        </TouchableOpacity>
      </Card>

      {/* What3Words */}
      <Card variant="outlined" style={styles.sectionCard}>
        <View style={styles.sectionHeader}>
          <Text style={styles.sectionIcon}>🔤</Text>
          <Text style={styles.sectionTitle}>What3Words</Text>
        </View>
        {loadingW3W ? (
          <ActivityIndicator size="small" color={colors.primary} style={styles.sectionLoader} />
        ) : w3w ? (
          <>
            <Text style={styles.codeValue}>{w3w}</Text>
            <View style={styles.actionRow}>
              <TouchableOpacity
                style={styles.actionButton}
                onPress={() => handleCopy('w3w', () => copyWhat3WordsToClipboard(w3w))}
              >
                <Text style={styles.actionText}>
                  {copiedField === 'w3w' ? '✓ Copied!' : '📋 Copy'}
                </Text>
              </TouchableOpacity>
              <TouchableOpacity
                style={styles.actionButton}
                onPress={() => openWhat3Words(w3w)}
              >
                <Text style={styles.actionText}>🌐 Open</Text>
              </TouchableOpacity>
            </View>
          </>
        ) : (
          <Text style={styles.errorText}>Unable to generate What3Words address</Text>
        )}
      </Card>

      {/* Plus Codes */}
      <Card variant="outlined" style={styles.sectionCard}>
        <View style={styles.sectionHeader}>
          <Text style={styles.sectionIcon}>🔣</Text>
          <Text style={styles.sectionTitle}>Plus Code</Text>
        </View>
        {plusCode ? (
          <>
            <Text style={styles.codeValue}>{plusCode}</Text>
            <View style={styles.actionRow}>
              <TouchableOpacity
                style={styles.actionButton}
                onPress={() =>
                  handleCopy('plus', () => copyWhat3WordsToClipboard(plusCode))
                }
              >
                <Text style={styles.actionText}>
                  {copiedField === 'plus' ? '✓ Copied!' : '📋 Copy'}
                </Text>
              </TouchableOpacity>
              <TouchableOpacity
                style={styles.actionButton}
                onPress={() => openPlusCode(plusCode)}
              >
                <Text style={styles.actionText}>🌐 Open</Text>
              </TouchableOpacity>
            </View>
          </>
        ) : (
          <Text style={styles.errorText}>Unable to generate Plus Code</Text>
        )}
      </Card>

      {/* Share Actions */}
      <Text style={styles.sectionTitle}>Share</Text>

      <Card variant="outlined" style={styles.sectionCard}>
        <TouchableOpacity style={styles.shareRow} onPress={handleShare}>
          <Text style={styles.shareIcon}>💬</Text>
          <View style={styles.shareInfo}>
            <Text style={styles.shareLabel}>Send to Contact</Text>
            <Text style={styles.shareDesc}>Share via SMS, messaging, or email</Text>
          </View>
        </TouchableOpacity>
      </Card>

      <Card variant="outlined" style={styles.sectionCard}>
        <TouchableOpacity style={styles.shareRow} onPress={handleEmergencyCard}>
          <Text style={styles.shareIcon}>🚨</Text>
          <View style={styles.shareInfo}>
            <Text style={styles.shareLabel}>Emergency Location Card</Text>
            <Text style={styles.shareDesc}>
              Share a formatted card with all location details
            </Text>
          </View>
        </TouchableOpacity>
      </Card>

      {/* Info */}
      <Card variant="glass" style={styles.infoCard}>
        <Text style={styles.infoTitle}>ℹ️ About Location Sharing</Text>
        <Text style={styles.infoText}>
          What3Words divides the world into 3m squares, each with a unique 3-word
          address. Plus Codes (Google Open Location Code) provide a similar
          address based on latitude/longitude. Both work offline.
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
  centered: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    backgroundColor: colors.background,
    padding: spacing['2xl'],
  },
  loadingText: {
    fontFamily: 'Inter_400Regular',
    fontSize: 15,
    color: colors.textSecondary,
    marginTop: spacing.md,
  },
  emptyIcon: {
    fontSize: 48,
    marginBottom: spacing.md,
  },
  emptyTitle: {
    fontFamily: 'PlusJakartaSans_600SemiBold',
    fontSize: 20,
    fontWeight: '600',
    color: colors.textPrimary,
    marginBottom: spacing.xs,
  },
  emptySubtitle: {
    fontFamily: 'Inter_400Regular',
    fontSize: 15,
    color: colors.textSecondary,
    textAlign: 'center',
    lineHeight: 22,
    marginBottom: spacing.xl,
  },
  enableButton: {
    minWidth: 200,
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
  coordsCard: {
    marginBottom: spacing.lg,
    alignItems: 'center',
  },
  coordsLabel: {
    fontFamily: 'Inter_500Medium',
    fontSize: 14,
    fontWeight: '500',
    color: colors.textSecondary,
    marginBottom: spacing.xs,
  },
  coordsValue: {
    fontFamily: 'Inter_700Bold',
    fontSize: 18,
    fontWeight: '700',
    color: colors.textPrimary,
    marginBottom: spacing.md,
  },
  copyButton: {
    paddingVertical: spacing.sm,
    paddingHorizontal: spacing.xl,
    backgroundColor: colors.tealSoft,
    borderRadius: borderRadius.full,
  },
  copyText: {
    fontFamily: 'Inter_600SemiBold',
    fontSize: 14,
    fontWeight: '600',
    color: colors.primary,
  },
  sectionCard: {
    marginBottom: spacing.md,
  },
  sectionHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: spacing.md,
    gap: spacing.sm,
  },
  sectionIcon: {
    fontSize: 24,
  },
  sectionTitle: {
    fontFamily: 'PlusJakartaSans_600SemiBold',
    fontSize: 18,
    fontWeight: '600',
    color: colors.textPrimary,
    marginBottom: spacing.md,
    marginTop: spacing.md,
  },
  sectionLoader: {
    paddingVertical: spacing.lg,
  },
  codeValue: {
    fontFamily: 'Inter_600SemiBold',
    fontSize: 16,
    fontWeight: '600',
    color: colors.primary,
    marginBottom: spacing.md,
  },
  actionRow: {
    flexDirection: 'row',
    gap: spacing.md,
  },
  actionButton: {
    flex: 1,
    paddingVertical: spacing.sm,
    paddingHorizontal: spacing.md,
    backgroundColor: colors.tealSoft,
    borderRadius: borderRadius.md,
    alignItems: 'center',
  },
  actionText: {
    fontFamily: 'Inter_600SemiBold',
    fontSize: 13,
    fontWeight: '600',
    color: colors.primary,
  },
  errorText: {
    fontFamily: 'Inter_400Regular',
    fontSize: 14,
    color: colors.textMuted,
  },
  shareRow: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingVertical: spacing.sm,
  },
  shareIcon: {
    fontSize: 28,
    marginRight: spacing.md,
  },
  shareInfo: {
    flex: 1,
  },
  shareLabel: {
    fontFamily: 'Inter_600SemiBold',
    fontSize: 16,
    fontWeight: '600',
    color: colors.textPrimary,
  },
  shareDesc: {
    fontFamily: 'Inter_400Regular',
    fontSize: 13,
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
// ============================================================
// Project "Relief" — Favourites Screen
// ============================================================
// Favourites are account-dependent, so this is one of the few
// places that legitimately asks for sign-in. It explains why and
// makes clear that finding a facility never requires an account.
// ============================================================

import React, { useCallback, useState } from 'react';
import {
  ActivityIndicator,
  Alert,
  FlatList,
  Pressable,
  StyleSheet,
  Text,
  View,
} from 'react-native';
import { Heart, Star } from 'lucide-react-native';
import { useFocusEffect, useNavigation } from '@react-navigation/native';
import type { NavigationProp } from '@react-navigation/native';
import { colors, spacing, touchTargets, typography } from '../theme';
import { PrimaryButton, SoftCard, StateNotice, StatusBadge } from '../components';
import { getFavouriteFacilities, removeFavourite } from '../services/favourites';
import { getOpenStatus } from '../utils/openingHours';
import { useAuth } from '../context/AuthContext';
import { signInReason } from '../utils/guestAccess';
import type { Facility, MainTabParamList, RootStackParamList } from '../types';

type FavouritesNavigation = NavigationProp<RootStackParamList & MainTabParamList>;

export const FavouritesScreen: React.FC = () => {
  const navigation = useNavigation<FavouritesNavigation>();
  const { isAuthenticated } = useAuth();
  const [facilities, setFacilities] = useState<Facility[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const loadFavourites = useCallback(async () => {
    if (!isAuthenticated) {
      setFacilities([]);
      setLoading(false);
      return;
    }
    setLoading(true);
    setError(null);
    try {
      setFacilities(await getFavouriteFacilities());
    } catch {
      setError('Your favourites could not be loaded.');
    } finally {
      setLoading(false);
    }
  }, [isAuthenticated]);

  useFocusEffect(
    useCallback(() => {
      loadFavourites();
    }, [loadFavourites]),
  );

  // FacilityDetail lives in the Find tab's stack, so it must be addressed
  // through that tab. Navigating to it directly from here would be an
  // unhandled action.
  const openFacility = (facility: Facility) =>
    navigation.navigate('Find', {
      screen: 'FacilityDetail',
      params: { facilityId: facility.id },
    } as never);

  const handleRemove = (facility: Facility) => {
    Alert.alert('Remove favourite', `Remove “${facility.name}” from your favourites?`, [
      { text: 'Cancel', style: 'cancel' },
      {
        text: 'Remove',
        style: 'destructive',
        onPress: async () => {
          await removeFavourite(facility.id);
          loadFavourites();
        },
      },
    ]);
  };

  if (!isAuthenticated) {
    return (
      <View style={styles.centered}>
        <View style={styles.emptyIcon}>
          <Heart size={34} color={colors.primary} />
        </View>
        <Text style={styles.emptyTitle}>Save your regular places</Text>
        <Text style={styles.emptySubtitle}>
          {signInReason('view_favourites')} Finding a facility never needs an account —
          only saving one does.
        </Text>
        <PrimaryButton
          title="Sign in"
          onPress={() =>
            navigation.navigate('Auth', { reason: signInReason('view_favourites') })
          }
          style={styles.signIn}
        />
      </View>
    );
  }

  if (loading) {
    return (
      <View style={styles.centered}>
        <ActivityIndicator size="large" color={colors.primary} />
      </View>
    );
  }

  if (error) {
    return (
      <View style={styles.noticeWrap}>
        <StateNotice
          tone="problem"
          title="Favourites could not be loaded"
          detail={error}
          actionLabel="Try again"
          onAction={loadFavourites}
        />
      </View>
    );
  }

  if (facilities.length === 0) {
    return (
      <View style={styles.centered}>
        <View style={styles.emptyIcon}>
          <Heart size={34} color={colors.primary} />
        </View>
        <Text style={styles.emptyTitle}>No favourites yet</Text>
        <Text style={styles.emptySubtitle}>
          Save a facility from its details screen to keep it here for quick access.
        </Text>
      </View>
    );
  }

  return (
    <View style={styles.container}>
      <FlatList
        data={facilities}
        keyExtractor={(item) => item.id}
        contentContainerStyle={styles.listContent}
        showsVerticalScrollIndicator={false}
        renderItem={({ item }) => {
          const score = item.overall_score ?? 0;
          return (
            <SoftCard
              onPress={() => openFacility(item)}
              accessibilityLabel={`View details for ${item.name}`}
              style={styles.card}
            >
              <View style={styles.cardHeader}>
                <View style={styles.cardCopy}>
                  <Text style={styles.name} numberOfLines={2}>
                    {item.name}
                  </Text>
                  <Text style={styles.address} numberOfLines={1}>
                    {item.address || item.town || 'Location unavailable'}
                  </Text>
                </View>
                <Pressable
                  accessibilityRole="button"
                  accessibilityLabel={`Remove ${item.name} from favourites`}
                  onPress={() => handleRemove(item)}
                  style={styles.removeButton}
                >
                  <Heart size={22} color={colors.urgent} fill={colors.urgent} />
                </Pressable>
              </View>
              <View style={styles.metaRow}>
                <StatusBadge status={getOpenStatus(item)} />
                {score > 0 ? (
                  <View style={styles.scoreRow}>
                    <Star size={13} color={colors.amber} fill={colors.amber} />
                    <Text style={styles.score}>{score.toFixed(1)}</Text>
                  </View>
                ) : (
                  <Text style={styles.unrated}>Not yet rated</Text>
                )}
              </View>
            </SoftCard>
          );
        }}
      />
    </View>
  );
};

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: colors.background },
  centered: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    backgroundColor: colors.background,
    padding: spacing['2xl'],
  },
  noticeWrap: { flex: 1, backgroundColor: colors.background, padding: spacing.lg },
  listContent: { padding: spacing.lg, paddingBottom: spacing['6xl'] },
  emptyIcon: {
    width: 68,
    height: 68,
    borderRadius: 24,
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: colors.secondarySurface,
    marginBottom: spacing.lg,
  },
  emptyTitle: { ...typography.h3, color: colors.textPrimary, marginBottom: spacing.xs },
  emptySubtitle: {
    ...typography.bodySmall,
    color: colors.textSecondary,
    textAlign: 'center',
    lineHeight: 22,
  },
  signIn: { marginTop: spacing['2xl'], alignSelf: 'stretch' },
  card: { marginBottom: spacing.md },
  cardHeader: { flexDirection: 'row', alignItems: 'flex-start' },
  cardCopy: { flex: 1, paddingRight: spacing.sm },
  name: { ...typography.h4, color: colors.textPrimary },
  address: { ...typography.bodySmall, color: colors.textSecondary, marginTop: 3 },
  removeButton: {
    minWidth: touchTargets.minimum,
    minHeight: touchTargets.minimum,
    alignItems: 'center',
    justifyContent: 'center',
  },
  metaRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: spacing.md,
    marginTop: spacing.sm,
  },
  scoreRow: { flexDirection: 'row', alignItems: 'center', gap: 4 },
  score: {
    ...typography.bodySmall,
    color: colors.textPrimary,
    fontFamily: 'PlusJakartaSans_600SemiBold',
  },
  unrated: { ...typography.caption, color: colors.textMuted },
});

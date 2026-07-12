// ============================================================
// Project "Relief" — Favourites Screen (4.3)
// Lists favourite facilities, chains, and routes
// ============================================================

import React, { useState, useEffect, useCallback } from 'react';
import {
  View,
  Text,
  StyleSheet,
  FlatList,
  TouchableOpacity,
  ActivityIndicator,
  Alert,
} from 'react-native';
import { colors, typography, spacing, borderRadius } from '../theme';
import { Card, Button, Badge } from '../components';
import {
  getFavouriteFacilities,
  removeFavourite,
} from '../services/favourites';
import { useNavigation, NavigationProp, useFocusEffect } from '@react-navigation/native';
import type { Facility } from '../types';

export const FavouritesScreen: React.FC = () => {
  const navigation = useNavigation<NavigationProp<any>>();
  const [facilities, setFacilities] = useState<Facility[]>([]);
  const [loading, setLoading] = useState(true);

  useFocusEffect(
    useCallback(() => {
      loadFavourites();
    }, []),
  );

  const loadFavourites = async () => {
    setLoading(true);
    const data = await getFavouriteFacilities();
    setFacilities(data);
    setLoading(false);
  };

  const handleRemove = (facility: Facility) => {
    Alert.alert(
      'Remove Favourite',
      `Remove "${facility.name}" from your favourites?`,
      [
        { text: 'Cancel', style: 'cancel' },
        {
          text: 'Remove',
          style: 'destructive',
          onPress: async () => {
            await removeFavourite(facility.id);
            loadFavourites();
          },
        },
      ],
    );
  };

  const handleFacilityPress = (facility: Facility) => {
    navigation.navigate('FacilityDetail', { facilityId: facility.id });
  };

  if (loading) {
    return (
      <View style={styles.centered}>
        <ActivityIndicator size="large" color={colors.primary} />
      </View>
    );
  }

  if (facilities.length === 0) {
    return (
      <View style={styles.centered}>
        <Text style={styles.emptyIcon}>⭐</Text>
        <Text style={styles.emptyTitle}>No Favourites Yet</Text>
        <Text style={styles.emptySubtitle}>
          Tap the star icon on any facility to save it here for quick access.
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
        renderItem={({ item }) => (
          <TouchableOpacity
            onPress={() => handleFacilityPress(item)}
            activeOpacity={0.7}
          >
            <Card variant="outlined" style={styles.facilityCard}>
              <View style={styles.facilityHeader}>
                <View style={styles.facilityInfo}>
                  <Text style={styles.facilityName}>{item.name}</Text>
                  <Text style={styles.facilityAddress}>{item.address}</Text>
                </View>
                <TouchableOpacity
                  onPress={() => handleRemove(item)}
                  style={styles.removeButton}
                >
                  <Text style={styles.removeIcon}>★</Text>
                </TouchableOpacity>
              </View>
              <View style={styles.facilityMeta}>
                <Badge
                  label={`★ ${item.overall_score.toFixed(1)}`}
                  variant="success"
                  size="sm"
                />
                <Text style={styles.facilityTown}>{item.town}</Text>
              </View>
            </Card>
          </TouchableOpacity>
        )}
      />
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: colors.background,
  },
  centered: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    backgroundColor: colors.background,
    padding: spacing['2xl'],
  },
  listContent: {
    padding: spacing.lg,
    paddingBottom: spacing['6xl'],
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
  },
  facilityCard: {
    marginBottom: spacing.md,
  },
  facilityHeader: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    marginBottom: spacing.sm,
  },
  facilityInfo: {
    flex: 1,
    marginRight: spacing.sm,
  },
  facilityName: {
    fontFamily: 'Inter_600SemiBold',
    fontSize: 16,
    fontWeight: '600',
    color: colors.textPrimary,
    marginBottom: 2,
  },
  facilityAddress: {
    fontFamily: 'Inter_400Regular',
    fontSize: 13,
    color: colors.textSecondary,
  },
  removeButton: {
    padding: spacing.xs,
  },
  removeIcon: {
    fontSize: 24,
    color: colors.warning,
  },
  facilityMeta: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: spacing.sm,
  },
  facilityTown: {
    fontFamily: 'Inter_400Regular',
    fontSize: 12,
    color: colors.textMuted,
  },
});
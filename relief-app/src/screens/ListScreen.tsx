// ============================================================
// Project "Relief" — List Screen
// ============================================================

import React, { useState } from 'react';
import {
  View,
  Text,
  StyleSheet,
  FlatList,
  TouchableOpacity,
} from 'react-native';
import { colors, typography, spacing, borderRadius, shadows } from '../theme';
import { Card, Badge } from '../components';

interface FacilityListItem {
  id: string;
  name: string;
  address: string;
  distance: number;
  is_free: boolean;
  is_open: boolean;
  overall_score: number;
}

const MOCK_FACILITIES: FacilityListItem[] = [
  {
    id: '1',
    name: 'Central Station Toilets',
    address: '1 Station Road, Liverpool',
    distance: 0.3,
    is_free: true,
    is_open: true,
    overall_score: 4.2,
  },
  {
    id: '2',
    name: 'City Library Facilities',
    address: '25 Library Street, Liverpool',
    distance: 0.6,
    is_free: true,
    is_open: true,
    overall_score: 3.8,
  },
  {
    id: '3',
    name: 'Shopping Centre',
    address: '100 High Street, Liverpool',
    distance: 0.8,
    is_free: false,
    is_open: true,
    overall_score: 4.5,
  },
];

export const ListScreen: React.FC = () => {
  const [facilities] = useState<FacilityListItem[]>(MOCK_FACILITIES);
  const [sortBy, setSortBy] = useState<'distance' | 'rating'>('distance');

  const renderItem = ({ item }: { item: FacilityListItem }) => (
    <TouchableOpacity activeOpacity={0.7}>
      <Card variant="outlined" style={styles.card}>
        <View style={styles.cardHeader}>
          <Text style={styles.facilityName}>{item.name}</Text>
          <Badge
            label={item.is_open ? 'Open' : 'Closed'}
            variant={item.is_open ? 'success' : 'error'}
            size="sm"
          />
        </View>
        <Text style={styles.facilityAddress}>{item.address}</Text>
        <View style={styles.cardFooter}>
          <Text style={styles.distance}>{item.distance.toFixed(1)} mi</Text>
          <Text style={styles.price}>{item.is_free ? 'Free' : 'Paid'}</Text>
          <Text style={styles.score}>★ {item.overall_score.toFixed(1)}</Text>
        </View>
      </Card>
    </TouchableOpacity>
  );

  return (
    <View style={styles.container}>
      {/* Sort Toggle */}
      <View style={styles.sortBar}>
        <TouchableOpacity
          style={[styles.sortButton, sortBy === 'distance' && styles.sortButtonActive]}
          onPress={() => setSortBy('distance')}
        >
          <Text
            style={[
              styles.sortButtonText,
              sortBy === 'distance' && styles.sortButtonTextActive,
            ]}
          >
            Nearest
          </Text>
        </TouchableOpacity>
        <TouchableOpacity
          style={[styles.sortButton, sortBy === 'rating' && styles.sortButtonActive]}
          onPress={() => setSortBy('rating')}
        >
          <Text
            style={[
              styles.sortButtonText,
              sortBy === 'rating' && styles.sortButtonTextActive,
            ]}
          >
            Top Rated
          </Text>
        </TouchableOpacity>
      </View>

      {/* Facility List */}
      <FlatList
        data={facilities}
        renderItem={renderItem}
        keyExtractor={(item) => item.id}
        contentContainerStyle={styles.list}
        showsVerticalScrollIndicator={false}
        ListEmptyComponent={
          <View style={styles.empty}>
            <Text style={styles.emptyText}>No facilities found nearby</Text>
          </View>
        }
      />
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: colors.background,
  },
  sortBar: {
    flexDirection: 'row',
    padding: spacing.lg,
    gap: spacing.sm,
  },
  sortButton: {
    paddingVertical: spacing.sm,
    paddingHorizontal: spacing.lg,
    borderRadius: borderRadius.full,
    backgroundColor: colors.gray100,
  },
  sortButtonActive: {
    backgroundColor: colors.primary,
  },
  sortButtonText: {
    ...typography.buttonSmall,
    color: colors.textSecondary,
  },
  sortButtonTextActive: {
    color: colors.textOnPrimary,
  },
  list: {
    paddingHorizontal: spacing.lg,
    paddingBottom: spacing['4xl'],
  },
  card: {
    marginBottom: spacing.md,
  },
  cardHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: spacing.xs,
  },
  facilityName: {
    ...typography.h4,
    color: colors.textPrimary,
    flex: 1,
    marginRight: spacing.sm,
  },
  facilityAddress: {
    ...typography.bodySmall,
    color: colors.textSecondary,
    marginBottom: spacing.sm,
  },
  cardFooter: {
    flexDirection: 'row',
    gap: spacing.lg,
  },
  distance: {
    ...typography.bodySmall,
    color: colors.primary,
    fontWeight: '600',
  },
  price: {
    ...typography.bodySmall,
    color: colors.textSecondary,
  },
  score: {
    ...typography.bodySmall,
    color: colors.warning,
    fontWeight: '600',
  },
  empty: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    paddingVertical: spacing['6xl'],
  },
  emptyText: {
    ...typography.body,
    color: colors.textMuted,
  },
});
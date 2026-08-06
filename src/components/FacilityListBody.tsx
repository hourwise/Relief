import React, { useCallback } from 'react';
import { FlatList, Pressable, StyleSheet, Text, View } from 'react-native';
import { Star } from 'lucide-react-native';
import { SoftCard } from './SoftCard';
import { StatusBadge } from './StatusBadge';
import { colors, borderRadius, spacing, typography } from '../theme';
import { formatDistance } from '../utils/distance';
import { getOpenStatus } from '../utils/openingHours';
import type { RankedFacility, SortMode } from '../utils/facilitySort';
import type { Facility } from '../types';

interface FacilityListBodyProps {
  items: readonly RankedFacility[];
  sortMode: SortMode;
  onChangeSort: (mode: SortMode) => void;
  onSelect: (facility: Facility) => void;
  /** Rendered above the list — loading, error and empty states live here. */
  header?: React.ReactNode;
  /** True when distance is unavailable, so the sort control can explain itself. */
  distanceUnavailable: boolean;
  contentPaddingTop: number;
  contentPaddingBottom: number;
}

const SORT_OPTIONS: { value: SortMode; label: string }[] = [
  { value: 'distance', label: 'Nearest' },
  { value: 'rating', label: 'Top rated' },
];

const FacilityRow: React.FC<{ item: RankedFacility; onSelect: (facility: Facility) => void }> = ({
  item,
  onSelect,
}) => {
  const { facility, distanceMetres } = item;
  const distance = formatDistance(distanceMetres);
  const score = facility.overall_score ?? 0;
  const cost =
    facility.is_free === true
      ? 'Free'
      : facility.is_free === false
        ? facility.price_note || 'Paid'
        : 'Cost unknown';

  return (
    <SoftCard
      onPress={() => onSelect(facility)}
      accessibilityLabel={`${facility.name}${distance ? `, ${distance} away` : ''}. View details.`}
      style={styles.card}
    >
      <View style={styles.cardHeader}>
        <Text style={styles.name} numberOfLines={2}>
          {facility.name}
        </Text>
        <StatusBadge status={getOpenStatus(facility)} />
      </View>

      <Text style={styles.address} numberOfLines={1}>
        {facility.address || facility.town || 'Location unavailable'}
      </Text>

      <View style={styles.metaRow}>
        {/* Distance is omitted rather than faked when there is no position. */}
        {distance ? <Text style={styles.distance}>{distance}</Text> : null}
        <Text style={styles.cost}>{cost}</Text>
        {score > 0 ? (
          // Icon and text are siblings in a View. A react-native-svg element
          // nested inside <Text> does not lay out reliably on Android.
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
};

/**
 * The real nearby list, rendered from live Supabase facilities.
 *
 * It shares its data, filters and selection with the map through
 * useFindExperience — there is no second query and no mock data.
 */
export const FacilityListBody: React.FC<FacilityListBodyProps> = ({
  items,
  sortMode,
  onChangeSort,
  onSelect,
  header,
  distanceUnavailable,
  contentPaddingTop,
  contentPaddingBottom,
}) => {
  const renderItem = useCallback(
    ({ item }: { item: RankedFacility }) => (
      <FacilityRow item={item} onSelect={onSelect} />
    ),
    [onSelect],
  );

  return (
    <FlatList
      data={items as RankedFacility[]}
      renderItem={renderItem}
      keyExtractor={(item) => item.facility.id}
      contentContainerStyle={[
        styles.list,
        { paddingTop: contentPaddingTop, paddingBottom: contentPaddingBottom },
      ]}
      showsVerticalScrollIndicator={false}
      keyboardShouldPersistTaps="handled"
      ListHeaderComponent={
        <View>
          {header}
          <View style={styles.sortBar}>
            {SORT_OPTIONS.map((option) => {
              const selected = option.value === sortMode;
              const disabled = option.value === 'distance' && distanceUnavailable;
              return (
                <Pressable
                  key={option.value}
                  accessibilityRole="radio"
                  accessibilityLabel={`Sort by ${option.label}`}
                  accessibilityState={{ selected, disabled }}
                  accessibilityHint={
                    disabled ? 'Needs your location to sort by distance' : undefined
                  }
                  disabled={disabled}
                  onPress={() => onChangeSort(option.value)}
                  style={[
                    styles.sortButton,
                    selected && styles.sortButtonActive,
                    disabled && styles.sortButtonDisabled,
                  ]}
                >
                  <Text
                    style={[styles.sortLabel, selected && styles.sortLabelActive]}
                  >
                    {option.label}
                  </Text>
                </Pressable>
              );
            })}
          </View>
        </View>
      }
    />
  );
};

const styles = StyleSheet.create({
  list: { paddingHorizontal: spacing.lg },
  sortBar: { flexDirection: 'row', gap: spacing.sm, marginBottom: spacing.md },
  sortButton: {
    minHeight: 40,
    justifyContent: 'center',
    paddingHorizontal: spacing.lg,
    borderRadius: borderRadius.full,
    backgroundColor: colors.white,
    borderWidth: 1,
    borderColor: colors.border,
  },
  sortButtonActive: { backgroundColor: colors.primary, borderColor: colors.primary },
  sortButtonDisabled: { opacity: 0.45 },
  sortLabel: { ...typography.buttonSmall, color: colors.textSecondary },
  sortLabelActive: { color: colors.white },

  card: { marginBottom: spacing.md },
  cardHeader: { flexDirection: 'row', alignItems: 'flex-start', gap: spacing.sm },
  name: { ...typography.h4, color: colors.textPrimary, flex: 1 },
  address: { ...typography.bodySmall, color: colors.textSecondary, marginTop: 4 },
  metaRow: {
    flexDirection: 'row',
    alignItems: 'center',
    flexWrap: 'wrap',
    gap: spacing.md,
    marginTop: spacing.sm,
  },
  distance: {
    ...typography.bodySmall,
    color: colors.primary,
    fontFamily: 'PlusJakartaSans_600SemiBold',
  },
  cost: { ...typography.bodySmall, color: colors.textSecondary },
  scoreRow: { flexDirection: 'row', alignItems: 'center', gap: 4 },
  score: {
    ...typography.bodySmall,
    color: colors.textPrimary,
    fontFamily: 'PlusJakartaSans_600SemiBold',
  },
  unrated: { ...typography.caption, color: colors.textMuted },
});

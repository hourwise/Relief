// ============================================================
// Project "Relief" — Advanced Filters Screen (Phase 3)
// Collapsible sections: Privacy, Accessibility, Baby, Equipment,
// Environment, Safety, Minimum Rating
// ============================================================

import React, { useState } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  Switch,
  TouchableOpacity,
} from 'react-native';
import { colors, typography, spacing, borderRadius } from '../theme';
import { Button } from '../components';
import { useNavigation, NavigationProp } from '@react-navigation/native';
import { useFilters } from '../context/FiltersContext';
import type { FacilityFilters } from '../types';

// ── Filter section definitions ──

interface ToggleFilter {
  key: keyof FacilityFilters;
  label: string;
  icon: string;
}

interface SectionDef {
  title: string;
  icon: string;
  filters: ToggleFilter[];
}

const FILTER_SECTIONS: SectionDef[] = [
  {
    title: 'Privacy',
    icon: '🛡️',
    filters: [
      { key: 'is_single_room', label: 'Single Room', icon: '🚪' },
      { key: 'has_floor_to_ceiling_cubicles', label: 'Floor-to-ceiling cubicles', icon: '🧱' },
      { key: 'is_quiet', label: 'Quiet', icon: '🔇' },
      { key: 'is_gender_neutral', label: 'Gender Neutral', icon: '⚧️' },
    ],
  },
  {
    title: 'Accessibility',
    icon: '♿',
    filters: [
      { key: 'has_wheelchair_access', label: 'Wheelchair Access', icon: '♿' },
      { key: 'requires_radar_key', label: 'RADAR Key', icon: '🔑' },
      { key: 'has_adult_changing_place', label: 'Adult Changing Place', icon: '🛋️' },
      { key: 'has_lift', label: 'Lift', icon: '🛗' },
      { key: 'has_grab_rails', label: 'Grab Rails', icon: '📐' },
    ],
  },
  {
    title: 'Baby Facilities',
    icon: '🍼',
    filters: [
      { key: 'has_baby_changing_inside', label: 'Changing Inside Room', icon: '🚼' },
      { key: 'has_separate_changing_room', label: 'Separate Changing Room', icon: '🚻' },
      { key: 'has_family_toilet', label: 'Family Toilet', icon: '👨‍👩‍👧‍👧' },
      { key: 'has_pram_access', label: 'Pram Access', icon: '🛒' },
    ],
  },
  {
    title: 'Equipment',
    icon: '🧴',
    filters: [
      { key: 'has_soap', label: 'Soap', icon: '🧼' },
      { key: 'has_paper_towels', label: 'Paper Towels', icon: '🧻' },
      { key: 'has_hand_dryer', label: 'Hand Dryer', icon: '💨' },
      { key: 'has_mirror', label: 'Mirror', icon: '🪞' },
      { key: 'has_shelf', label: 'Shelf', icon: '📦' },
      { key: 'has_hooks', label: 'Hooks', icon: '🪝' },
      { key: 'has_sanitary_bins', label: 'Sanitary Bins', icon: '🗑️' },
      { key: 'has_free_period_products', label: 'Free Period Products', icon: '🩸' },
      { key: 'has_drinking_water', label: 'Drinking Water', icon: '🚰' },
    ],
  },
  {
    title: 'Environment',
    icon: '🌿',
    filters: [
      { key: 'is_quiet', label: 'Quiet', icon: '🔇' },
    ],
  },
  {
    title: 'Safety',
    icon: '🛡️',
    filters: [
      { key: 'has_staff_nearby', label: 'Staff Nearby', icon: '👥' },
      { key: 'has_cctv', label: 'CCTV', icon: '📹' },
      { key: 'is_women_friendly', label: 'Women Friendly', icon: '👩' },
      { key: 'is_family_friendly', label: 'Family Friendly', icon: '👨‍👩‍👧‍👦' },
    ],
  },
  {
    title: 'Facility Types',
    icon: '🏗️',
    filters: [
      { key: 'is_water_refill_station', label: 'Water Refill Station', icon: '🚰' },
      { key: 'is_shower_facility', label: 'Shower Facility', icon: '🚿' },
      { key: 'is_breastfeeding_room', label: 'Breastfeeding Room', icon: '🤱' },
      { key: 'is_rest_area', label: 'Rest Area', icon: '🛋️' },
      { key: 'is_changing_place', label: 'Changing Place', icon: '♿' },
      { key: 'is_ev_charging', label: 'EV Charging', icon: '⚡' },
      { key: 'is_picnic_area', label: 'Picnic Area', icon: '🧺' },
    ],
  },
];

// ── Collapsible Section Component ──
const FilterSection: React.FC<{
  section: SectionDef;
  filters: Partial<FacilityFilters>;
  onToggle: (key: keyof FacilityFilters) => void;
}> = ({ section, filters, onToggle }) => {
  const [expanded, setExpanded] = useState(true);

  const activeCount = section.filters.filter(
    (f) => filters[f.key] === true,
  ).length;

  return (
    <View style={styles.section}>
      <TouchableOpacity
        style={styles.sectionHeader}
        onPress={() => setExpanded(!expanded)}
        activeOpacity={0.7}
      >
        <View style={styles.sectionHeaderLeft}>
          <Text style={styles.sectionIcon}>{section.icon}</Text>
          <Text style={styles.sectionTitle}>{section.title}</Text>
          {activeCount > 0 && (
            <View style={styles.activeCountBadge}>
              <Text style={styles.activeCountText}>{activeCount}</Text>
            </View>
          )}
        </View>
        <Text style={styles.expandIcon}>{expanded ? '▼' : '▶'}</Text>
      </TouchableOpacity>

      {expanded && (
        <View style={styles.sectionContent}>
          {section.filters.map((filter) => (
            <View key={filter.key} style={styles.filterRow}>
              <View style={styles.filterLabel}>
                <Text style={styles.filterIcon}>{filter.icon}</Text>
                <Text style={styles.filterText}>{filter.label}</Text>
              </View>
              <Switch
                value={filters[filter.key] === true}
                onValueChange={() => onToggle(filter.key)}
                trackColor={{ true: colors.primaryLight, false: colors.gray200 }}
                thumbColor={
                  filters[filter.key] === true ? colors.primary : colors.gray400
                }
              />
            </View>
          ))}
        </View>
      )}
    </View>
  );
};

// ── Rating Selector ──
const RatingSelector: React.FC<{
  value: number;
  onChange: (val: number) => void;
}> = ({ value, onChange }) => {
  const ratings = [0, 1, 2, 3, 4, 5];
  return (
    <View style={styles.ratingContainer}>
      <Text style={styles.ratingLabel}>Minimum Rating</Text>
      <View style={styles.ratingStars}>
        {ratings.map((r) => (
          <TouchableOpacity
            key={r}
            onPress={() => onChange(r)}
            style={[
              styles.ratingStar,
              value >= r && r > 0 && styles.ratingStarActive,
              value === r && styles.ratingStarSelected,
            ]}
          >
            <Text
              style={[
                styles.ratingStarText,
                value >= r && r > 0 && styles.ratingStarTextActive,
              ]}
            >
              {r === 0 ? 'Any' : r}
            </Text>
          </TouchableOpacity>
        ))}
      </View>
    </View>
  );
};

// ── Main Screen Component ──
export const AdvancedFiltersScreen: React.FC = () => {
  const navigation = useNavigation<NavigationProp<any>>();
  const { filters: contextFilters, setFilters: setContextFilters } = useFilters();

  const [localFilters, setLocalFilters] = useState<Partial<FacilityFilters>>({
    ...contextFilters,
  });

  const toggleFilter = (key: keyof FacilityFilters) => {
    setLocalFilters((prev) => ({
      ...prev,
      [key]: prev[key] === true ? false : true,
    }));
  };

  const setMinRating = (val: number) => {
    setLocalFilters((prev) => ({
      ...prev,
      min_rating: val,
    }));
  };

  const clearAll = () => {
    setLocalFilters({});
  };

  const activeCount = Object.entries(localFilters).filter(
    ([key, val]) => {
      if (key === 'min_rating') return (val as number) > 0;
      return val === true;
    },
  ).length;

  const handleApply = () => {
    setContextFilters(localFilters);
    navigation.goBack();
  };

  return (
    <View style={styles.container}>
      {/* Header */}
      <View style={styles.header}>
        <View>
          <Text style={styles.headerTitle}>Advanced Filters</Text>
          <Text style={styles.headerSubtitle}>
            {activeCount > 0
              ? `${activeCount} filter${activeCount !== 1 ? 's' : ''} active`
              : 'No filters applied'}
          </Text>
        </View>
        {activeCount > 0 && (
          <TouchableOpacity onPress={clearAll}>
            <Text style={styles.clearText}>Clear All</Text>
          </TouchableOpacity>
        )}
      </View>

      <ScrollView
        style={styles.scrollView}
        contentContainerStyle={styles.scrollContent}
        showsVerticalScrollIndicator={false}
      >
        {/* Rating */}
        <RatingSelector
          value={localFilters.min_rating || 0}
          onChange={setMinRating}
        />

        {/* Sections */}
        {FILTER_SECTIONS.map((section) => (
          <FilterSection
            key={section.title}
            section={section}
            filters={localFilters}
            onToggle={toggleFilter}
          />
        ))}
      </ScrollView>

      {/* Bottom Action */}
      <View style={styles.bottomBar}>
        <Button
          title={`Apply Filters${activeCount > 0 ? ` (${activeCount})` : ''}`}
          onPress={handleApply}
          fullWidth
          size="lg"
        />
      </View>
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: colors.background,
  },
  header: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'flex-start',
    padding: spacing.lg,
    paddingBottom: spacing.md,
    backgroundColor: colors.white,
    borderBottomWidth: 1,
    borderBottomColor: colors.border,
  },
  headerTitle: {
    fontFamily: 'PlusJakartaSans_600SemiBold',
    fontSize: 24,
    fontWeight: '600',
    color: colors.textPrimary,
  },
  headerSubtitle: {
    fontFamily: 'Inter_400Regular',
    fontSize: 14,
    color: colors.textSecondary,
    marginTop: 2,
  },
  clearText: {
    fontFamily: 'Inter_600SemiBold',
    fontSize: 14,
    fontWeight: '600',
    color: colors.primary,
  },
  scrollView: {
    flex: 1,
  },
  scrollContent: {
    padding: spacing.lg,
    paddingBottom: spacing['6xl'],
  },
  // Rating
  ratingContainer: {
    backgroundColor: colors.white,
    borderRadius: borderRadius['2xl'],
    padding: spacing.lg,
    marginBottom: spacing.md,
  },
  ratingLabel: {
    fontFamily: 'PlusJakartaSans_600SemiBold',
    fontSize: 17,
    fontWeight: '600',
    color: colors.textPrimary,
    marginBottom: spacing.md,
  },
  ratingStars: {
    flexDirection: 'row',
    gap: spacing.sm,
    justifyContent: 'center',
  },
  ratingStar: {
    width: 48,
    height: 48,
    borderRadius: 24,
    backgroundColor: colors.gray100,
    justifyContent: 'center',
    alignItems: 'center',
    borderWidth: 2,
    borderColor: 'transparent',
  },
  ratingStarActive: {
    backgroundColor: colors.tealSoft,
    borderColor: colors.primary,
  },
  ratingStarSelected: {
    borderColor: colors.primary,
    backgroundColor: colors.primary,
  },
  ratingStarText: {
    fontFamily: 'Inter_600SemiBold',
    fontSize: 14,
    fontWeight: '600',
    color: colors.textMuted,
  },
  ratingStarTextActive: {
    color: colors.primary,
  },
  // Section
  section: {
    backgroundColor: colors.white,
    borderRadius: borderRadius['2xl'],
    marginBottom: spacing.sm,
    overflow: 'hidden',
  },
  sectionHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    padding: spacing.lg,
  },
  sectionHeaderLeft: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: spacing.sm,
  },
  sectionIcon: {
    fontSize: 20,
  },
  sectionTitle: {
    fontFamily: 'PlusJakartaSans_600SemiBold',
    fontSize: 17,
    fontWeight: '600',
    color: colors.textPrimary,
  },
  activeCountBadge: {
    backgroundColor: colors.primary,
    borderRadius: 10,
    width: 20,
    height: 20,
    justifyContent: 'center',
    alignItems: 'center',
  },
  activeCountText: {
    fontFamily: 'Inter_600SemiBold',
    fontSize: 11,
    fontWeight: '600',
    color: colors.white,
  },
  expandIcon: {
    fontSize: 14,
    color: colors.textMuted,
  },
  sectionContent: {
    paddingHorizontal: spacing.lg,
    paddingBottom: spacing.md,
  },
  filterRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingVertical: spacing.sm,
    borderBottomWidth: 1,
    borderBottomColor: colors.gray100,
  },
  filterLabel: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: spacing.sm,
    flex: 1,
  },
  filterIcon: {
    fontSize: 18,
  },
  filterText: {
    fontFamily: 'Inter_400Regular',
    fontSize: 15,
    color: colors.textPrimary,
    flex: 1,
  },
  // Bottom
  bottomBar: {
    padding: spacing.lg,
    paddingBottom: spacing['3xl'],
    backgroundColor: colors.white,
    borderTopWidth: 1,
    borderTopColor: colors.border,
  },
});
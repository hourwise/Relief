import React from 'react';
import { Pressable, SafeAreaView, ScrollView, StyleSheet, Switch, Text, View } from 'react-native';
import { ArrowLeft, RotateCcw } from 'lucide-react-native';
import { useNavigation } from '@react-navigation/native';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import type { FacilityFilters } from '../types';
import { PrimaryButton, ScreenBackground, SoftCard } from '../components';
import { useFilters } from '../context/FiltersContext';
import {
  applyCostOption,
  costOptionFromFilters,
  countActiveFilters,
  COST_OPTIONS,
  EXPOSED_BOOLEAN_FILTERS,
  type CostOption,
  type ExposedFilterKey,
} from '../utils/filterDefinitions';
import { borderRadius, colors, spacing, touchTargets, typography } from '../theme';

/**
 * Only filters backed by real data are offered — see filterDefinitions.ts.
 * The schema has many more amenity columns, but they are unpopulated, so a
 * switch for them would always return nothing and read as a broken service.
 *
 * The minimum-rating selector is also gone: no published facility has a rating
 * yet, so every threshold above "Any" returned an empty list.
 */
export const AdvancedFiltersScreen: React.FC = () => {
  const navigation = useNavigation();
  const insets = useSafeAreaInsets();
  const { filters: savedFilters, setFilters } = useFilters();
  const [draft, setDraft] = React.useState<Partial<FacilityFilters>>({ ...savedFilters });

  const activeCount = countActiveFilters(draft);
  const cost = costOptionFromFilters(draft);

  const toggleFilter = (key: ExposedFilterKey | 'open_now') =>
    setDraft((previous) => {
      const next = { ...previous };
      if (previous[key] === true) delete next[key];
      else next[key] = true;
      return next;
    });

  const setCost = (option: CostOption) =>
    setDraft((previous) => applyCostOption(previous, option));

  return <ScreenBackground>
    <SafeAreaView style={styles.safeArea}>
      {/* react-native's SafeAreaView is a no-op on Android, so the top inset is
          applied here. Without it the title and Reset sat under the status bar. */}
      <View style={[styles.header, { paddingTop: insets.top }]}>
        <Pressable accessibilityRole="button" accessibilityLabel="Back" onPress={() => navigation.goBack()} style={styles.backButton}><ArrowLeft size={22} color={colors.textPrimary} /></Pressable>
        <View style={styles.headerCopy}><Text style={styles.headerTitle}>Filters</Text><Text style={styles.headerSubtitle}>{activeCount ? `${activeCount} active filter${activeCount === 1 ? '' : 's'}` : 'No filters applied'}</Text></View>
        <Pressable accessibilityRole="button" accessibilityLabel="Reset filters" disabled={!activeCount} onPress={() => setDraft({})} style={[styles.reset, !activeCount && styles.resetDisabled]}><RotateCcw size={17} color={colors.primary} /><Text style={styles.resetText}>Reset</Text></Pressable>
      </View>

      <ScrollView contentContainerStyle={styles.content} showsVerticalScrollIndicator={false}>
        <SoftCard style={styles.notice}>
          <Text style={styles.noticeTitle}>Use confirmed details</Text>
          <Text style={styles.noticeText}>Filters include facilities only when that detail is confirmed. Missing information is not treated as “no”.</Text>
        </SoftCard>

        {/* Cost is tri-state: "Paid" is a real request, not the absence of a filter. */}
        <SoftCard style={styles.section}>
          <Text style={styles.sectionTitle}>Cost</Text>
          <View accessibilityRole="radiogroup" accessibilityLabel="Cost" style={styles.costRow}>
            {COST_OPTIONS.map((option) => {
              const selected = cost === option.value;
              return (
                <Pressable
                  key={option.value}
                  accessibilityRole="radio"
                  accessibilityState={{ selected, checked: selected }}
                  accessibilityLabel={`Cost: ${option.label}`}
                  onPress={() => setCost(option.value)}
                  style={[styles.costOption, selected && styles.costSelected]}
                >
                  <Text style={[styles.costText, selected && styles.costTextSelected]}>{option.label}</Text>
                </Pressable>
              );
            })}
          </View>
        </SoftCard>

        <SoftCard style={styles.section}>
          <Text style={styles.sectionTitle}>Availability</Text>
          <View style={styles.filterRow}>
            <View style={styles.filterCopy}>
              <Text style={styles.filterTitle}>Open now</Text>
              <Text style={styles.filterDescription}>Based on recorded opening hours.</Text>
            </View>
            <Switch
              accessibilityLabel="Open now"
              accessibilityState={{ checked: draft.open_now === true }}
              value={draft.open_now === true}
              onValueChange={() => toggleFilter('open_now')}
              trackColor={{ false: colors.gray200, true: colors.primaryLight }}
              thumbColor={draft.open_now === true ? colors.primary : colors.white}
            />
          </View>
        </SoftCard>

        <SoftCard style={styles.section}>
          <Text style={styles.sectionTitle}>Facilities</Text>
          {EXPOSED_BOOLEAN_FILTERS.map((filter, index) => {
            const value = draft[filter.key] === true;
            return (
              <View key={filter.key} style={[styles.filterRow, index > 0 && styles.filterRowDivided]}>
                <View style={styles.filterCopy}>
                  <Text style={styles.filterTitle}>{filter.label}</Text>
                  {filter.description ? <Text style={styles.filterDescription}>{filter.description}</Text> : null}
                </View>
                <Switch
                  accessibilityLabel={filter.label}
                  accessibilityHint={filter.description}
                  accessibilityState={{ checked: value }}
                  value={value}
                  onValueChange={() => toggleFilter(filter.key)}
                  trackColor={{ false: colors.gray200, true: colors.primaryLight }}
                  thumbColor={value ? colors.primary : colors.white}
                />
              </View>
            );
          })}
        </SoftCard>

        <Text style={styles.footnote}>
          More filters — cubicle privacy, equipment, changing places — will appear here as facility data is collected. They are hidden for now because no facility carries that information yet.
        </Text>
      </ScrollView>

      <View style={[styles.footer, { paddingBottom: Math.max(spacing.lg, insets.bottom + spacing.sm) }]}>
        <PrimaryButton title={activeCount ? `Apply Filters (${activeCount})` : 'Apply Filters'} onPress={() => { setFilters(draft); navigation.goBack(); }} />
      </View>
    </SafeAreaView>
  </ScreenBackground>;
};

const styles = StyleSheet.create({
  safeArea: { flex: 1 },
  header: { minHeight: 68, flexDirection: 'row', alignItems: 'center', paddingHorizontal: spacing.lg, paddingBottom: spacing.sm, backgroundColor: colors.white, borderBottomWidth: 1, borderBottomColor: colors.borderLight },
  backButton: { minWidth: touchTargets.minimum, minHeight: touchTargets.minimum, alignItems: 'center', justifyContent: 'center', marginRight: spacing.sm },
  headerCopy: { flex: 1 },
  headerTitle: { ...typography.h3, color: colors.textPrimary },
  headerSubtitle: { ...typography.caption, color: colors.textSecondary, marginTop: 1 },
  reset: { minHeight: touchTargets.minimum, flexDirection: 'row', gap: 5, alignItems: 'center', justifyContent: 'center', paddingHorizontal: spacing.sm },
  resetDisabled: { opacity: 0.45 },
  resetText: { ...typography.buttonSmall, color: colors.primary },

  content: { padding: spacing.lg, paddingBottom: spacing['5xl'] },
  notice: { backgroundColor: colors.secondarySurface, marginBottom: spacing.md },
  noticeTitle: { ...typography.label, color: colors.primary },
  noticeText: { ...typography.bodySmall, color: colors.textSecondary, marginTop: 3 },

  section: { marginBottom: spacing.md },
  sectionTitle: { ...typography.h4, color: colors.textPrimary, marginBottom: spacing.sm },

  costRow: { flexDirection: 'row', gap: spacing.sm },
  costOption: { flex: 1, minHeight: touchTargets.minimum, borderRadius: borderRadius.full, alignItems: 'center', justifyContent: 'center', backgroundColor: colors.gray100, borderWidth: 1, borderColor: colors.border },
  costSelected: { backgroundColor: colors.primary, borderColor: colors.primary },
  costText: { ...typography.buttonSmall, color: colors.textSecondary },
  costTextSelected: { color: colors.white },

  filterRow: { minHeight: 64, flexDirection: 'row', alignItems: 'center' },
  filterRowDivided: { borderTopWidth: 1, borderTopColor: colors.borderLight },
  filterCopy: { flex: 1, paddingRight: spacing.md },
  filterTitle: { ...typography.label, color: colors.textPrimary },
  filterDescription: { ...typography.caption, color: colors.textSecondary, marginTop: 2 },

  footnote: { ...typography.caption, color: colors.textMuted, lineHeight: 18, paddingHorizontal: spacing.xs, marginTop: spacing.xs },
  footer: { paddingHorizontal: spacing.lg, paddingTop: spacing.md, backgroundColor: colors.white, borderTopWidth: 1, borderTopColor: colors.border },
});

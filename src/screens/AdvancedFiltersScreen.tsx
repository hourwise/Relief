import React, { useState } from 'react';
import { Pressable, SafeAreaView, ScrollView, StyleSheet, Switch, Text, View } from 'react-native';
import { ArrowLeft, ChevronDown, ChevronRight, RotateCcw } from 'lucide-react-native';
import { useNavigation } from '@react-navigation/native';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import type { FacilityFilters } from '../types';
import { PrimaryButton, ScreenBackground, SoftCard } from '../components';
import { useFilters } from '../context/FiltersContext';
import { borderRadius, colors, spacing, touchTargets, typography } from '../theme';

interface ToggleFilter { key: keyof FacilityFilters; label: string; description?: string; }
interface SectionDef { title: string; filters: ToggleFilter[]; }

const FILTER_SECTIONS: SectionDef[] = [
  { title: 'Privacy', filters: [{ key: 'is_single_room', label: 'Single room' }, { key: 'has_floor_to_ceiling_cubicles', label: 'Floor-to-ceiling cubicles' }, { key: 'is_quiet', label: 'Quiet' }, { key: 'is_gender_neutral', label: 'Gender-neutral' }] },
  { title: 'Accessibility', filters: [{ key: 'is_accessible', label: 'Accessible' }, { key: 'has_wheelchair_access', label: 'Wheelchair access' }, { key: 'requires_radar_key', label: 'RADAR Key' }, { key: 'has_adult_changing_place', label: 'Adult changing place' }, { key: 'has_lift', label: 'Lift' }, { key: 'has_grab_rails', label: 'Grab rails' }] },
  { title: 'Baby and family', filters: [{ key: 'has_baby_changing', label: 'Baby changing' }, { key: 'has_baby_changing_inside', label: 'Changing inside the room' }, { key: 'has_separate_changing_room', label: 'Separate changing room' }, { key: 'has_family_room', label: 'Family room' }, { key: 'has_family_toilet', label: 'Family toilet' }, { key: 'has_pram_access', label: 'Pram access' }] },
  { title: 'Equipment', filters: [{ key: 'has_soap', label: 'Soap' }, { key: 'has_paper_towels', label: 'Paper towels' }, { key: 'has_hand_dryer', label: 'Hand dryer' }, { key: 'has_mirror', label: 'Mirror' }, { key: 'has_shelf', label: 'Shelf' }, { key: 'has_hooks', label: 'Hooks' }, { key: 'has_sanitary_bins', label: 'Sanitary bins' }, { key: 'has_free_period_products', label: 'Free period products' }, { key: 'has_drinking_water', label: 'Drinking water' }] },
  { title: 'Safety and setting', filters: [{ key: 'has_staff_nearby', label: 'Staff nearby' }, { key: 'has_cctv', label: 'CCTV' }, { key: 'is_women_friendly', label: 'Women-friendly' }, { key: 'is_family_friendly', label: 'Family-friendly' }] },
  // Water refill station, shower facility, breastfeeding room, rest area,
  // Changing Place and EV charging are deliberately absent: the live schema has
  // no such columns, so offering them produced filters that silently matched
  // nothing (and, in the nearest-facility RPC, a hard 42703 failure). They can
  // return once the columns are deliberately introduced and populated.
  // is_picnic_area does exist and is kept.
  { title: 'Other facility types', filters: [{ key: 'is_picnic_area', label: 'Picnic area' }] },
];

const activeCountFor = (filters: Partial<FacilityFilters>) => Object.entries(filters).filter(([key, value]) => key === 'min_rating' ? (value as number) > 0 : value === true).length;

const FilterSection: React.FC<{ section: SectionDef; filters: Partial<FacilityFilters>; onToggle: (key: keyof FacilityFilters) => void }> = ({ section, filters, onToggle }) => {
  const [expanded, setExpanded] = useState(true);
  const count = section.filters.filter((item) => filters[item.key] === true).length;
  return <SoftCard style={styles.section}>
    <Pressable accessibilityRole="button" accessibilityLabel={`${section.title}, ${expanded ? 'expanded' : 'collapsed'}`} onPress={() => setExpanded((value) => !value)} style={styles.sectionHeader}>
      <View style={styles.sectionTitleRow}><Text style={styles.sectionTitle}>{section.title}</Text>{count ? <View style={styles.count}><Text style={styles.countText}>{count}</Text></View> : null}</View>
      {expanded ? <ChevronDown color={colors.textSecondary} size={20} /> : <ChevronRight color={colors.textSecondary} size={20} />}
    </Pressable>
    {expanded ? <View>{section.filters.map((filter) => {
      const value = filters[filter.key] === true;
      return <View key={filter.key} style={styles.filterRow}><View style={styles.filterCopy}><Text style={styles.filterTitle}>{filter.label}</Text>{filter.description ? <Text style={styles.filterDescription}>{filter.description}</Text> : null}</View><Switch accessibilityLabel={filter.label} accessibilityState={{ checked: value }} value={value} onValueChange={() => onToggle(filter.key)} trackColor={{ false: colors.gray200, true: colors.primaryLight }} thumbColor={value ? colors.primary : colors.white} /></View>;
    })}</View> : null}
  </SoftCard>;
};

export const AdvancedFiltersScreen: React.FC = () => {
  const navigation = useNavigation();
  const insets = useSafeAreaInsets();
  const { filters: savedFilters, setFilters } = useFilters();
  const [draft, setDraft] = useState<Partial<FacilityFilters>>({ ...savedFilters });
  const activeCount = activeCountFor(draft);
  const toggleFilter = (key: keyof FacilityFilters) => setDraft((previous) => {
    if (previous[key] === true) {
      const next = { ...previous };
      delete next[key];
      return next;
    }
    return { ...previous, [key]: true } as Partial<FacilityFilters>;
  });
  const setRating = (min_rating: number) => setDraft((previous) => {
    const next = { ...previous };
    if (!min_rating) delete next.min_rating; else next.min_rating = min_rating;
    return next;
  });

  return <ScreenBackground>
    <SafeAreaView style={styles.safeArea}>
      <View style={styles.header}>
        <Pressable accessibilityRole="button" accessibilityLabel="Back" onPress={() => navigation.goBack()} style={styles.backButton}><ArrowLeft size={22} color={colors.textPrimary} /></Pressable>
        <View style={styles.headerCopy}><Text style={styles.headerTitle}>Filters</Text><Text style={styles.headerSubtitle}>{activeCount ? `${activeCount} active filter${activeCount === 1 ? '' : 's'}` : 'No filters applied'}</Text></View>
        <Pressable accessibilityRole="button" accessibilityLabel="Reset filters" disabled={!activeCount} onPress={() => setDraft({})} style={[styles.reset, !activeCount && styles.resetDisabled]}><RotateCcw size={17} color={colors.primary} /><Text style={styles.resetText}>Reset</Text></Pressable>
      </View>
      <ScrollView contentContainerStyle={styles.content} showsVerticalScrollIndicator={false}>
        <SoftCard style={styles.notice}><Text style={styles.noticeTitle}>Use confirmed details</Text><Text style={styles.noticeText}>Filters include facilities only when that detail is confirmed. Missing information is not treated as “no”.</Text></SoftCard>
        <SoftCard style={styles.ratingCard}><Text style={styles.ratingTitle}>Minimum community rating</Text><View style={styles.ratings}>{[0, 1, 2, 3, 4, 5].map((rating) => { const selected = (draft.min_rating || 0) === rating; return <Pressable key={rating} accessibilityRole="button" accessibilityState={{ selected }} accessibilityLabel={rating ? `Minimum rating ${rating}` : 'Any rating'} onPress={() => setRating(rating)} style={[styles.ratingOption, selected && styles.ratingSelected]}><Text style={[styles.ratingText, selected && styles.ratingTextSelected]}>{rating || 'Any'}</Text></Pressable>; })}</View></SoftCard>
        {FILTER_SECTIONS.map((section) => <FilterSection key={section.title} section={section} filters={draft} onToggle={toggleFilter} />)}
      </ScrollView>
      <View style={[styles.footer, { paddingBottom: Math.max(spacing.lg, insets.bottom + spacing.sm) }]}><PrimaryButton title={activeCount ? `Apply Filters (${activeCount})` : 'Apply Filters'} onPress={() => { setFilters(draft); navigation.goBack(); }} /></View>
    </SafeAreaView>
  </ScreenBackground>;
};

const styles = StyleSheet.create({
  safeArea: { flex: 1 }, header: { minHeight: 68, flexDirection: 'row', alignItems: 'center', paddingHorizontal: spacing.lg, backgroundColor: colors.white, borderBottomWidth: 1, borderBottomColor: colors.borderLight }, backButton: { minWidth: touchTargets.minimum, minHeight: touchTargets.minimum, alignItems: 'center', justifyContent: 'center', marginRight: spacing.sm }, headerCopy: { flex: 1 }, headerTitle: { ...typography.h3, color: colors.textPrimary }, headerSubtitle: { ...typography.caption, color: colors.textSecondary, marginTop: 1 }, reset: { minHeight: touchTargets.minimum, flexDirection: 'row', gap: 5, alignItems: 'center', justifyContent: 'center', paddingHorizontal: spacing.sm }, resetDisabled: { opacity: 0.45 }, resetText: { ...typography.buttonSmall, color: colors.primary },
  content: { padding: spacing.lg, paddingBottom: spacing['5xl'] }, notice: { backgroundColor: colors.secondarySurface, marginBottom: spacing.md }, noticeTitle: { ...typography.label, color: colors.primary }, noticeText: { ...typography.bodySmall, color: colors.textSecondary, marginTop: 3 }, ratingCard: { marginBottom: spacing.md }, ratingTitle: { ...typography.h4, color: colors.textPrimary }, ratings: { flexDirection: 'row', flexWrap: 'wrap', gap: spacing.sm, marginTop: spacing.md }, ratingOption: { minWidth: 48, minHeight: touchTargets.minimum, borderRadius: borderRadius.full, alignItems: 'center', justifyContent: 'center', paddingHorizontal: 11, backgroundColor: colors.gray100, borderWidth: 1, borderColor: colors.border }, ratingSelected: { backgroundColor: colors.primary, borderColor: colors.primary }, ratingText: { ...typography.buttonSmall, color: colors.textSecondary }, ratingTextSelected: { color: colors.white },
  section: { marginBottom: spacing.sm, padding: 0, overflow: 'hidden' }, sectionHeader: { minHeight: 60, flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between', paddingHorizontal: spacing.lg }, sectionTitleRow: { flexDirection: 'row', alignItems: 'center', gap: spacing.sm }, sectionTitle: { ...typography.h4, color: colors.textPrimary }, count: { minWidth: 20, height: 20, borderRadius: 10, paddingHorizontal: 4, alignItems: 'center', justifyContent: 'center', backgroundColor: colors.primary }, countText: { ...typography.caption, color: colors.white, fontFamily: 'PlusJakartaSans_700Bold' }, filterRow: { minHeight: 64, flexDirection: 'row', alignItems: 'center', paddingHorizontal: spacing.lg, borderTopWidth: 1, borderTopColor: colors.borderLight }, filterCopy: { flex: 1, paddingRight: spacing.md }, filterTitle: { ...typography.label, color: colors.textPrimary }, filterDescription: { ...typography.caption, color: colors.textSecondary, marginTop: 2 }, footer: { paddingHorizontal: spacing.lg, paddingTop: spacing.md, backgroundColor: colors.white, borderTopWidth: 1, borderTopColor: colors.border },
});

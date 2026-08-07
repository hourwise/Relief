// ============================================================
// Project "Relief" — Find (shared Map + List)
// ============================================================
// One search, two views. The segmented switch changes how results
// are presented; it never re-runs or forks the query.
//
// No state here is allowed to be ambiguous. "We could not reach
// the service" and "there is nothing here" are different messages
// with different recovery, and an RPC failure is never dressed up
// as "no facilities found".
// ============================================================

import React, { useCallback, useEffect, useRef, useState } from 'react';
import {
  ActivityIndicator,
  FlatList,
  Linking,
  Pressable,
  ScrollView,
  StyleSheet,
  Text,
  TextInput,
  View,
} from 'react-native';
import type MapView from 'react-native-maps';
import { List, Map as MapIcon, SlidersHorizontal, X } from 'lucide-react-native';
import { useNavigation } from '@react-navigation/native';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import { useTranslation } from 'react-i18next';
import type { NativeStackNavigationProp } from '@react-navigation/native-stack';
import {
  FacilityListBody,
  FacilityMapBody,
  FilterChip,
  PrimaryButton,
  SegmentedSwitch,
  SoftCard,
  StateNotice,
  StatusBadge,
  UrgentButton,
} from '../components';
import {
  borderRadius,
  colors,
  mapOverlaySurface,
  shadows,
  spacing,
  typography,
} from '../theme';
import {
  useFindExperience,
  type FindView,
  type Region,
} from '../hooks/useFindExperience';
import { useFilters } from '../context/FiltersContext';
import { estimateWalkingTime } from '../utils/walkingTime';
import { formatDistance } from '../utils/distance';
import { getOpenStatus } from '../utils/openingHours';
import type { Facility, FindStackParamList } from '../types';

type FindNavigationProp = NativeStackNavigationProp<FindStackParamList, 'FindHome'>;

const QUICK_FILTERS = [
  { label: 'Free', key: 'is_free' },
  { label: 'Accessible', key: 'is_accessible' },
  { label: 'Baby changing', key: 'has_baby_changing' },
  { label: 'Gender-neutral', key: 'is_gender_neutral' },
] as const;

const VIEW_OPTIONS = [
  { value: 'map' as FindView, label: 'Map', icon: <MapIcon size={16} color={colors.textSecondary} /> },
  { value: 'list' as FindView, label: 'List', icon: <List size={16} color={colors.textSecondary} /> },
] as const;

const costLabel = (facility: { is_free: boolean | null; price_note?: string | null }) =>
  facility.is_free === true
    ? 'Free'
    : facility.is_free === false
      ? facility.price_note || 'Paid'
      : 'Cost unknown';

export const FindScreen: React.FC = () => {
  const { t } = useTranslation();
  const navigation = useNavigation<FindNavigationProp>();
  const insets = useSafeAreaInsets();
  const mapRef = useRef<MapView | null>(null);
  const { filters, setFilters, activeFilterCount } = useFilters();
  const find = useFindExperience();
  const [chromeHeight, setChromeHeight] = useState(160);

  // The map's initialRegion is captured once. Later movement goes through
  // animateToRegion so the user's own gestures are never fought.
  const initialRegionRef = useRef<Region>(find.region);

  const openFacility = useCallback(
    (facility: Facility) =>
      navigation.navigate('FacilityDetail', { facilityId: facility.id }),
    [navigation],
  );

  const animateTo = useCallback(
    (latitude: number, longitude: number) => {
      // Publishing a target is enough; the effect below drives the camera.
      find.focusRegion(latitude, longitude);
    },
    [find],
  );

  // The single place the camera is moved programmatically. MapView takes only
  // `initialRegion`, so without this nothing would ever recentre — the map
  // would stay on the startup fallback while data loaded for somewhere else.
  const cameraTarget = find.cameraTarget;
  useEffect(() => {
    if (!cameraTarget) return;
    mapRef.current?.animateToRegion(cameraTarget, 500);
  }, [cameraTarget]);

  const handleSearchResultPress = useCallback(
    (facility: Facility) => {
      find.clearSearch();
      find.selectFacility(facility);
      if (find.view === 'map') animateTo(facility.latitude, facility.longitude);
      else openFacility(facility);
    },
    [find, animateTo, openFacility],
  );

  const handleFindNearest = useCallback(() => find.findNearest(), [find]);

  const nearestResult = find.nearest.result;

  // Centre on the nearest facility once per result, and only on success — a
  // failed lookup must leave the user's current view alone.
  const centredNearestIdRef = useRef<string | null>(null);
  useEffect(() => {
    if (!nearestResult) {
      centredNearestIdRef.current = null;
      return;
    }
    const { facility_id, latitude, longitude } = nearestResult.facility;
    if (centredNearestIdRef.current === facility_id) return;
    centredNearestIdRef.current = facility_id;
    if (find.view === 'map') animateTo(latitude, longitude);
  }, [nearestResult, find.view, animateTo]);

  const toggleQuickFilter = (key: (typeof QUICK_FILTERS)[number]['key']) => {
    const next = { ...filters };
    if (next[key] === true) delete next[key];
    else next[key] = true;
    setFilters(next);
  };

  const openDirections = (latitude: number, longitude: number) =>
    Linking.openURL(
      `https://www.google.com/maps/dir/?api=1&destination=${latitude},${longitude}&travelmode=walking&dir_action=navigate`,
    );

  // ── Runtime states, in priority order ─────────────────────
  const notice = (() => {
    if (find.locationInitialising && find.facilities.length === 0) {
      return (
        <StateNotice
          title="Finding your location"
          detail="You can search by town or postcode instead."
        />
      );
    }

    if (find.facilitiesError) {
      return (
        <StateNotice
          tone="problem"
          title="Facilities could not be loaded"
          detail={find.facilitiesError}
          actionLabel="Try again"
          onAction={find.retry}
        />
      );
    }

    if (find.locationStatus === 'denied') {
      return (
        <StateNotice
          title="Location is turned off"
          detail="Relief works without it — search by town or postcode to see facilities. Allow location to sort by distance and use Need One Now."
          actionLabel="Allow location"
          onAction={find.refreshLocation}
        />
      );
    }

    if (find.locationStatus === 'unavailable') {
      return (
        <StateNotice
          title="Your location is unavailable"
          detail="Your device could not get a position. Search by town or postcode, or try again."
          actionLabel="Try again"
          onAction={find.refreshLocation}
        />
      );
    }

    if (find.noFacilitiesInArea) {
      return (
        <StateNotice
          title="No facilities in this area"
          detail={
            activeFilterCount > 0
              ? 'Nothing here matches your filters. Try removing a filter or moving the map.'
              : 'Move the map or search another town to look somewhere else.'
          }
          actionLabel={activeFilterCount > 0 ? 'Clear filters' : undefined}
          onAction={activeFilterCount > 0 ? () => setFilters({}) : undefined}
        />
      );
    }

    if (find.truncated) {
      return (
        <StateNotice
          title="Showing the closest 500 facilities"
          detail="Zoom in to see everything in a smaller area."
        />
      );
    }

    return null;
  })();

  // ── Bottom sheet: nearest result, selection, or the urgent CTA ──
  const bottomCard = (() => {
    if (find.nearest.active) {
      if (find.nearest.loading) {
        return (
          <SoftCard style={styles.bottomCard}>
            <Text style={styles.cardEyebrow}>NEAREST FACILITY</Text>
            <View style={styles.cardLoadingRow}>
              <ActivityIndicator color={colors.primary} />
              <Text style={styles.cardMeta}>Searching for the closest facility…</Text>
            </View>
          </SoftCard>
        );
      }

      // An RPC failure is a failure. It must never read as "nothing nearby".
      if (find.nearest.error) {
        return (
          <SoftCard style={[styles.bottomCard, styles.bottomCardProblem]}>
            <Text style={styles.cardEyebrow}>NEAREST FACILITY</Text>
            <Text style={styles.cardTitle}>We could not complete the search</Text>
            <Text style={styles.cardMeta}>{find.nearest.error}</Text>
            <View style={styles.cardActions}>
              <PrimaryButton
                title="Try again"
                onPress={handleFindNearest}
                style={styles.cardPrimary}
              />
              <Pressable
                accessibilityRole="button"
                accessibilityLabel="Close nearest facility"
                onPress={find.dismissNearest}
                style={styles.dismiss}
              >
                <Text style={styles.dismissText}>Close</Text>
              </Pressable>
            </View>
          </SoftCard>
        );
      }

      if (find.nearest.notFound) {
        return (
          <SoftCard style={styles.bottomCard}>
            <Text style={styles.cardEyebrow}>NEAREST FACILITY</Text>
            <Text style={styles.cardTitle}>Nothing found within 25 km</Text>
            <Text style={styles.cardMeta}>
              We searched up to 25 km and found no published facility.
            </Text>
            <View style={styles.cardActions}>
              <PrimaryButton
                title="Search again"
                onPress={handleFindNearest}
                style={styles.cardPrimary}
              />
              <Pressable
                accessibilityRole="button"
                accessibilityLabel="Close nearest facility"
                onPress={find.dismissNearest}
                style={styles.dismiss}
              >
                <Text style={styles.dismissText}>Close</Text>
              </Pressable>
            </View>
          </SoftCard>
        );
      }

      if (nearestResult) {
        const nearby = nearestResult.facility;
        return (
          <SoftCard style={styles.bottomCard}>
            <Text style={styles.cardEyebrow}>NEAREST FACILITY</Text>
            <Text style={styles.cardTitle} numberOfLines={2}>
              {nearby.name}
            </Text>
            <Text style={styles.cardMeta}>
              {formatDistance(nearestResult.distance_metres)} away · approx.{' '}
              {estimateWalkingTime(nearestResult.distance_metres)} min walk ·{' '}
              {costLabel(nearby)}
            </Text>
            <View style={styles.cardStatus}>
              <StatusBadge status={getOpenStatus(nearby)} />
            </View>
            <View style={styles.cardActions}>
              <PrimaryButton
                title="Get directions"
                onPress={() => openDirections(nearby.latitude, nearby.longitude)}
                style={styles.cardPrimary}
              />
              <Pressable
                accessibilityRole="button"
                accessibilityLabel="Close nearest facility"
                onPress={find.dismissNearest}
                style={styles.dismiss}
              >
                <Text style={styles.dismissText}>Close</Text>
              </Pressable>
            </View>
            <Pressable
              accessibilityRole="button"
              accessibilityLabel={`View full details for ${nearby.name}`}
              onPress={() =>
                navigation.navigate('FacilityDetail', {
                  facilityId: nearby.facility_id,
                })
              }
              style={styles.detailsLinkButton}
            >
              <Text style={styles.detailsLink}>View full details</Text>
            </Pressable>
          </SoftCard>
        );
      }
    }

    if (find.selectedFacility) {
      const selected = find.selectedFacility;
      return (
        <SoftCard
          onPress={() => openFacility(selected)}
          accessibilityLabel={`View details for ${selected.name}`}
          style={styles.bottomCard}
        >
          <View style={styles.selectedRow}>
            <View style={styles.selectedCopy}>
              <Text style={styles.cardTitle} numberOfLines={1}>
                {selected.name}
              </Text>
              <Text style={styles.cardMeta} numberOfLines={1}>
                {selected.town || selected.address || 'Location unavailable'} ·{' '}
                {costLabel(selected)}
              </Text>
            </View>
            <StatusBadge status={getOpenStatus(selected)} />
          </View>
          <Text style={styles.detailsLink}>View details</Text>
        </SoftCard>
      );
    }

    return <UrgentButton onPress={handleFindNearest} style={styles.urgentButton} />;
  })();

  return (
    <View style={styles.container}>
      {/* Body: the two views share every piece of state above. */}
      {find.view === 'map' ? (
        <FacilityMapBody
          mapRef={mapRef}
          initialRegion={initialRegionRef.current}
          region={find.region}
          facilities={find.facilities}
          selectedFacilityId={find.selectedFacility?.id ?? null}
          urgentFacilityId={nearestResult?.facility.facility_id ?? null}
          onRegionChangeComplete={find.onRegionChangeComplete}
          onSelectFacility={find.selectFacility}
          onZoomToCluster={animateTo}
        />
      ) : (
        <FacilityListBody
          items={find.ranked}
          sortMode={find.sortMode}
          onChangeSort={find.setSortMode}
          onSelect={openFacility}
          distanceUnavailable={!find.location}
          contentPaddingTop={chromeHeight + spacing.md}
          contentPaddingBottom={spacing['6xl'] * 2}
          header={
            <View>
              {find.facilitiesLoading ? (
                <View style={styles.listLoading}>
                  <ActivityIndicator color={colors.primary} />
                </View>
              ) : null}
              {notice ? <View style={styles.listNotice}>{notice}</View> : null}
            </View>
          }
        />
      )}

      {/* Chrome: search, view switch, quick filters */}
      <View
        style={[styles.chrome, { paddingTop: insets.top + spacing.md }]}
        onLayout={(event) => setChromeHeight(event.nativeEvent.layout.height)}
        pointerEvents="box-none"
      >
        <View style={styles.searchRow}>
          <View style={styles.searchBar}>
            <TextInput
              accessibilityLabel="Search by town or postcode"
              style={styles.searchInput}
              placeholder={t('map.searchPlaceholder')}
              placeholderTextColor={colors.textMuted}
              value={find.searchQuery}
              onChangeText={find.setSearchQuery}
              onSubmitEditing={find.runSearch}
              returnKeyType="search"
            />
            {find.searchQuery ? (
              <Pressable
                accessibilityRole="button"
                accessibilityLabel="Clear search"
                onPress={find.clearSearch}
                style={styles.iconButton}
              >
                <X size={20} color={colors.textSecondary} />
              </Pressable>
            ) : null}
          </View>
          <Pressable
            accessibilityRole="button"
            accessibilityLabel={`Filters${activeFilterCount ? `, ${activeFilterCount} active` : ''}`}
            onPress={() => navigation.navigate('AdvancedFilters')}
            style={styles.filtersButton}
          >
            <SlidersHorizontal size={19} color={colors.primary} />
            <Text style={styles.filtersText}>
              Filters{activeFilterCount ? ` (${activeFilterCount})` : ''}
            </Text>
          </Pressable>
        </View>

        <SegmentedSwitch
          accessibilityLabel="Choose map or list view"
          options={VIEW_OPTIONS}
          value={find.view}
          onChange={find.setView}
          style={styles.viewSwitch}
        />

        <ScrollView
          horizontal
          showsHorizontalScrollIndicator={false}
          contentContainerStyle={styles.quickFilters}
          keyboardShouldPersistTaps="handled"
        >
          {QUICK_FILTERS.map((item) => (
            <View key={item.key} style={styles.chipWrap}>
              <FilterChip
                label={item.label}
                selected={filters[item.key] === true}
                onPress={() => toggleQuickFilter(item.key)}
              />
            </View>
          ))}
        </ScrollView>
      </View>

      {/* Map-only floating status. In list view these live in the list header. */}
      {find.view === 'map' ? (
        <>
          {find.facilitiesLoading ? (
            <View style={[styles.loadingOverlay, { top: chromeHeight + spacing.xs }]}>
              <ActivityIndicator size="small" color={colors.primary} />
            </View>
          ) : null}
          {!find.facilitiesLoading && !notice && find.ranked.length > 0 ? (
            <View style={[styles.countBadge, { top: chromeHeight + spacing.xs }]}>
              <Text style={styles.countText}>
                {t('map.facilitiesNearby', { count: find.ranked.length })}
              </Text>
            </View>
          ) : null}
          {notice ? (
            <View style={[styles.mapNotice, { top: chromeHeight + spacing.xs }]}>
              {notice}
            </View>
          ) : null}
        </>
      ) : null}

      {/* Search results overlay, shared by both views */}
      {find.searchActive ? (
        <SoftCard style={[styles.searchResults, { top: chromeHeight }]}>
          {find.searching ? (
            <ActivityIndicator color={colors.primary} />
          ) : find.searchError ? (
            <View style={styles.searchProblem}>
              <Text style={styles.searchProblemTitle}>Search failed</Text>
              <Text style={styles.searchProblemDetail}>{find.searchError}</Text>
              <PrimaryButton title="Try again" onPress={find.runSearch} />
            </View>
          ) : find.searchResults.length ? (
            <FlatList
              data={find.searchResults}
              keyExtractor={(item) => item.id}
              keyboardShouldPersistTaps="handled"
              renderItem={({ item }) => (
                <Pressable
                  accessibilityRole="button"
                  accessibilityLabel={`Select ${item.name}`}
                  onPress={() => handleSearchResultPress(item)}
                  style={styles.searchResultItem}
                >
                  <Text style={styles.searchResultName} numberOfLines={1}>
                    {item.name}
                  </Text>
                  <Text style={styles.searchResultAddress} numberOfLines={1}>
                    {item.town || item.address || 'Location unavailable'}
                  </Text>
                  <StatusBadge status={getOpenStatus(item)} />
                </Pressable>
              )}
            />
          ) : (
            <Text style={styles.noResults}>
              No facilities found for “{find.searchQuery.trim()}”.
            </Text>
          )}
        </SoftCard>
      ) : null}

      {bottomCard}
    </View>
  );
};

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: colors.mintSurface },

  chrome: {
    position: 'absolute',
    top: 0,
    left: 0,
    right: 0,
    zIndex: 20,
    paddingHorizontal: spacing.lg,
  },
  searchRow: { flexDirection: 'row', gap: spacing.sm },
  searchBar: {
    ...mapOverlaySurface,
    flex: 1,
    minHeight: 48,
    flexDirection: 'row',
    alignItems: 'center',
    paddingLeft: spacing.lg,
  },
  searchInput: {
    ...typography.bodySmall,
    color: colors.textPrimary,
    flex: 1,
    paddingVertical: 12,
  },
  iconButton: {
    minWidth: 44,
    minHeight: 44,
    alignItems: 'center',
    justifyContent: 'center',
  },
  filtersButton: {
    ...mapOverlaySurface,
    minHeight: 48,
    flexDirection: 'row',
    gap: 6,
    alignItems: 'center',
    justifyContent: 'center',
    paddingHorizontal: 12,
  },
  filtersText: { ...typography.buttonSmall, color: colors.primary },
  viewSwitch: { marginTop: spacing.sm },
  quickFilters: { paddingTop: spacing.sm, paddingBottom: spacing.xs },
  chipWrap: { marginRight: spacing.sm },

  loadingOverlay: {
    position: 'absolute',
    right: spacing.lg,
    width: 36,
    height: 36,
    alignItems: 'center',
    justifyContent: 'center',
    borderRadius: borderRadius.full,
    backgroundColor: colors.mapOverlay,
    ...shadows.sm,
  },
  countBadge: {
    position: 'absolute',
    alignSelf: 'center',
    backgroundColor: colors.primary,
    borderRadius: borderRadius.full,
    paddingHorizontal: 12,
    paddingVertical: 6,
    ...shadows.sm,
  },
  countText: {
    ...typography.caption,
    color: colors.white,
    fontFamily: 'PlusJakartaSans_600SemiBold',
  },
  mapNotice: { position: 'absolute', left: spacing.lg, right: spacing.lg, zIndex: 15 },
  listNotice: { marginBottom: spacing.md },
  listLoading: { paddingVertical: spacing.md, alignItems: 'center' },

  searchResults: {
    position: 'absolute',
    left: spacing.lg,
    right: spacing.lg,
    maxHeight: 310,
    padding: spacing.sm,
    zIndex: 30,
    // SoftCard's glass fill is legible over map tiles but not over the list,
    // where the rows behind bled through and made results unreadable.
    backgroundColor: colors.white,
  },
  searchResultItem: {
    padding: spacing.md,
    borderBottomWidth: 1,
    borderBottomColor: colors.borderLight,
  },
  searchResultName: { ...typography.label, color: colors.textPrimary },
  searchResultAddress: {
    ...typography.caption,
    color: colors.textSecondary,
    marginTop: 2,
    marginBottom: spacing.xs,
  },
  noResults: {
    ...typography.bodySmall,
    color: colors.textMuted,
    textAlign: 'center',
    padding: spacing.lg,
  },
  searchProblem: { padding: spacing.md, gap: spacing.sm },
  searchProblemTitle: { ...typography.label, color: colors.textPrimary },
  searchProblemDetail: {
    ...typography.bodySmall,
    color: colors.textSecondary,
    marginBottom: spacing.xs,
  },

  urgentButton: {
    position: 'absolute',
    bottom: spacing.lg,
    alignSelf: 'center',
    zIndex: 20,
  },
  bottomCard: {
    position: 'absolute',
    left: spacing.lg,
    right: spacing.lg,
    bottom: spacing.md,
    zIndex: 20,
    padding: spacing.lg,
  },
  bottomCardProblem: { backgroundColor: '#FFF4D9' },
  cardEyebrow: {
    ...typography.caption,
    fontFamily: 'PlusJakartaSans_700Bold',
    letterSpacing: 1,
    color: colors.textSecondary,
  },
  cardTitle: { ...typography.h4, color: colors.textPrimary, marginTop: 3 },
  cardMeta: { ...typography.bodySmall, color: colors.textSecondary, marginTop: 2 },
  cardLoadingRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: spacing.md,
    marginTop: spacing.sm,
  },
  cardStatus: { marginTop: spacing.sm },
  cardActions: { flexDirection: 'row', alignItems: 'center', marginTop: spacing.md },
  cardPrimary: { flex: 1 },
  dismiss: {
    minWidth: 60,
    minHeight: 44,
    alignItems: 'center',
    justifyContent: 'center',
    marginLeft: spacing.sm,
  },
  dismissText: { ...typography.buttonSmall, color: colors.textSecondary },
  selectedRow: { flexDirection: 'row', alignItems: 'flex-start' },
  selectedCopy: { flex: 1, paddingRight: spacing.sm },
  detailsLink: { ...typography.buttonSmall, color: colors.primary, marginTop: spacing.sm },
  detailsLinkButton: { minHeight: 44, justifyContent: 'center' },
});

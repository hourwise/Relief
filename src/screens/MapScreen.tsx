import React, { useCallback, useEffect, useRef, useState } from 'react';
import { ActivityIndicator, Dimensions, FlatList, Linking, Platform, Pressable, StyleSheet, Text, TextInput, View } from 'react-native';
import MapView, { Marker, PROVIDER_GOOGLE } from 'react-native-maps';
import { SlidersHorizontal, X } from 'lucide-react-native';
import { useNavigation } from '@react-navigation/native';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import { useTranslation } from 'react-i18next';
import type { NativeStackNavigationProp } from '@react-navigation/native-stack';
import { ClusterMarker, FacilityMarker, FilterChip, PrimaryButton, SelectedFacilityMarker, SoftCard, StatusBadge, UrgentButton } from '../components';
import { borderRadius, colors, mapOverlaySurface, shadows, spacing, typography } from '../theme';
import { useLocation } from '../hooks/useLocation';
import { useFilters } from '../context/FiltersContext';
import { estimateWalkingTime, fetchClosestFacility, fetchViewportFacilities, searchFacilities } from '../services/facilities';
import { getOpenStatus } from '../utils/openingHours';
import type { Facility, MapStackParamList } from '../types';

const { width, height } = Dimensions.get('window');
const ASPECT_RATIO = width / height;
const LATITUDE_DELTA = 0.0922;
const LONGITUDE_DELTA = LATITUDE_DELTA * ASPECT_RATIO;
const CLUSTER_RADIUS = 60;
const DEBOUNCE_MS = 400;
type MapNavigationProp = NativeStackNavigationProp<MapStackParamList, 'MapView'>;

interface Cluster { id: string; latitude: number; longitude: number; count: number; facilities: Facility[]; }
type Region = { latitude: number; longitude: number; latitudeDelta: number; longitudeDelta: number; };

function clusterFacilities(facilities: Facility[], region: Region): Cluster[] {
  if (!facilities.length) return [];
  const zoomLevel = Math.log2(360 / region.longitudeDelta);
  const clusterDistance = (region.latitudeDelta / height) * CLUSTER_RADIUS * (10 / zoomLevel);
  const clusters: Cluster[] = [];
  const assigned = new Set<string>();
  for (const facility of facilities) {
    if (assigned.has(facility.id)) continue;
    const members = [facility];
    assigned.add(facility.id);
    for (const other of facilities) {
      if (assigned.has(other.id)) continue;
      if (Math.hypot(facility.latitude - other.latitude, facility.longitude - other.longitude) < clusterDistance) {
        members.push(other);
        assigned.add(other.id);
      }
    }
    const latitude = members.reduce((sum, item) => sum + item.latitude, 0) / members.length;
    const longitude = members.reduce((sum, item) => sum + item.longitude, 0) / members.length;
    const sortedIds = members.map((item) => item.id).sort();
    clusters.push({ id: members.length > 1 ? `cluster-${sortedIds[0]}-${members.length}` : `single-${facility.id}`, latitude, longitude, count: members.length, facilities: members });
  }
  return clusters;
}

const quickFilters: Array<{ label: string; key: 'is_free' | 'is_accessible' | 'has_baby_changing' | 'is_gender_neutral'; }> = [
  { label: 'Free', key: 'is_free' },
  { label: 'Accessible', key: 'is_accessible' },
  { label: 'Baby changing', key: 'has_baby_changing' },
  { label: 'Gender-neutral', key: 'is_gender_neutral' },
];

export const MapScreen: React.FC = () => {
  const { t } = useTranslation();
  const navigation = useNavigation<MapNavigationProp>();
  const insets = useSafeAreaInsets();
  const mapRef = useRef<MapView>(null);
  const { location, loading: locationLoading, refreshLocation } = useLocation();
  const { filters, setFilters, activeFilterCount } = useFilters();
  const [facilities, setFacilities] = useState<Facility[]>([]);
  const [loading, setLoading] = useState(false);
  const [showEmergency, setShowEmergency] = useState(false);
  const [emergencyFacility, setEmergencyFacility] = useState<Facility | null>(null);
  const [walkingTime, setWalkingTime] = useState(0);
  const [searchQuery, setSearchQuery] = useState('');
  const [searchResults, setSearchResults] = useState<Facility[]>([]);
  const [showSearch, setShowSearch] = useState(false);
  const [searching, setSearching] = useState(false);
  const [selectedFacility, setSelectedFacility] = useState<Facility | null>(null);
  const [currentRegion, setCurrentRegion] = useState<Region>({ latitude: 51.5074, longitude: -0.1278, latitudeDelta: LATITUDE_DELTA, longitudeDelta: LONGITUDE_DELTA });
  const [mapInitialized, setMapInitialized] = useState(false);
  const requestIdRef = useRef(0);
  const debounceRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const inFlightRef = useRef(false);

  const loadFacilitiesForRegion = useCallback(async (region: Region) => {
    const requestId = ++requestIdRef.current;
    const result = await fetchViewportFacilities({ minLatitude: region.latitude - region.latitudeDelta / 2, maxLatitude: region.latitude + region.latitudeDelta / 2, minLongitude: region.longitude - region.longitudeDelta / 2, maxLongitude: region.longitude + region.longitudeDelta / 2 }, activeFilterCount > 0 ? filters : undefined);
    if (requestId < requestIdRef.current) return;
    setFacilities(result.facilities);
    setLoading(false);
    inFlightRef.current = false;
  }, [activeFilterCount, filters]);

  useEffect(() => {
    if (!location || mapInitialized) return;
    const region = { latitude: location.latitude, longitude: location.longitude, latitudeDelta: LATITUDE_DELTA, longitudeDelta: LONGITUDE_DELTA };
    setCurrentRegion(region);
    setMapInitialized(true);
    loadFacilitiesForRegion(region);
  }, [loadFacilitiesForRegion, location, mapInitialized]);

  useEffect(() => () => { if (debounceRef.current) clearTimeout(debounceRef.current); }, []);

  const handleEmergencyPress = async () => {
    if (!location) { await refreshLocation(); return; }
    setShowEmergency(true);
    setSelectedFacility(null);
    const result = await fetchClosestFacility(location.latitude, location.longitude);
    if (!result) return;
    setEmergencyFacility(result.facility);
    setWalkingTime(estimateWalkingTime(result.distance_metres));
    mapRef.current?.animateToRegion({ latitude: result.facility.latitude, longitude: result.facility.longitude, latitudeDelta: 0.02, longitudeDelta: 0.02 * ASPECT_RATIO }, 500);
  };

  const handleSearch = useCallback(async () => {
    if (!searchQuery.trim()) return;
    setSearching(true);
    setShowSearch(true);
    setSearchResults(await searchFacilities(searchQuery.trim()));
    setSearching(false);
  }, [searchQuery]);

  const selectFacility = useCallback((facility: Facility) => { setSelectedFacility(facility); setShowEmergency(false); }, []);
  const openFacility = useCallback((facility: Facility) => navigation.navigate('FacilityDetail', { facilityId: facility.id }), [navigation]);
  const handleSearchResultPress = useCallback((facility: Facility) => {
    setShowSearch(false); setSearchQuery(''); selectFacility(facility);
    mapRef.current?.animateToRegion({ latitude: facility.latitude, longitude: facility.longitude, latitudeDelta: 0.02, longitudeDelta: 0.02 * ASPECT_RATIO }, 500);
  }, [selectFacility]);

  const handleRegionChangeComplete = useCallback((region: Region) => {
    setCurrentRegion(region);
    if (debounceRef.current) clearTimeout(debounceRef.current);
    debounceRef.current = setTimeout(() => {
      if (!inFlightRef.current) { inFlightRef.current = true; setLoading(true); loadFacilitiesForRegion(region); }
    }, DEBOUNCE_MS);
  }, [loadFacilitiesForRegion]);

  const handleClusterPress = useCallback((cluster: Cluster) => {
    mapRef.current?.animateToRegion({ latitude: cluster.latitude, longitude: cluster.longitude, latitudeDelta: currentRegion.latitudeDelta / 3, longitudeDelta: currentRegion.longitudeDelta / 3 }, 500);
  }, [currentRegion]);

  const markers = React.useMemo<(Facility | Cluster)[]>(() => clusterFacilities(facilities, currentRegion).map((cluster) => cluster.count === 1 ? cluster.facilities[0] : cluster), [facilities, currentRegion]);
  const isCluster = (item: Facility | Cluster): item is Cluster => 'count' in item && item.count > 1;
  const updateQuickFilter = (key: (typeof quickFilters)[number]['key']) => {
    const next = { ...filters };
    if (next[key] === true) delete next[key]; else next[key] = true;
    setFilters(next);
  };
  const priceLabel = (facility: Facility) => facility.is_free === true ? 'Free' : facility.is_free === false ? (facility.price_note || 'Paid') : 'Cost unknown';

  return (
    <View style={styles.container}>
      {locationLoading && !mapInitialized ? <View style={styles.loadingContainer}><ActivityIndicator size="large" color={colors.primary} /><Text style={styles.loadingText}>{t('common.loading')}</Text></View> : (
        <MapView ref={mapRef} style={styles.map} initialRegion={currentRegion} onRegionChangeComplete={handleRegionChangeComplete} showsUserLocation showsMyLocationButton showsCompass rotateEnabled zoomEnabled scrollEnabled pitchEnabled={false} provider={Platform.OS === 'android' ? PROVIDER_GOOGLE : undefined}>
          {markers.map((item) => {
            if (isCluster(item)) return <Marker key={item.id} coordinate={{ latitude: item.latitude, longitude: item.longitude }} onPress={() => handleClusterPress(item)} anchor={{ x: 0.5, y: 0.5 }} tracksViewChanges={false}><ClusterMarker count={item.count} /></Marker>;
            const isSelected = selectedFacility?.id === item.id || emergencyFacility?.id === item.id;
            return <Marker key={item.id} coordinate={{ latitude: item.latitude, longitude: item.longitude }} onPress={() => selectFacility(item)} anchor={{ x: 0.5, y: 0.5 }} tracksViewChanges={isSelected}>{isSelected ? <SelectedFacilityMarker urgent={emergencyFacility?.id === item.id} /> : <FacilityMarker />}</Marker>;
          })}
        </MapView>
      )}

      <View style={[styles.searchRow, { top: insets.top + spacing.md }]}>
        <View style={styles.searchBar}><TextInput accessibilityLabel="Search by town or postcode" style={styles.searchInput} placeholder={t('map.searchPlaceholder')} placeholderTextColor={colors.textMuted} value={searchQuery} onChangeText={setSearchQuery} onSubmitEditing={handleSearch} returnKeyType="search" />
          {searchQuery ? <Pressable accessibilityRole="button" accessibilityLabel="Clear search" onPress={() => { setSearchQuery(''); setShowSearch(false); setSearchResults([]); }} style={styles.iconButton}><X size={20} color={colors.textSecondary} /></Pressable> : null}
        </View>
        <Pressable accessibilityRole="button" accessibilityLabel={`Filters${activeFilterCount ? `, ${activeFilterCount} active` : ''}`} onPress={() => navigation.navigate('AdvancedFilters')} style={styles.filtersButton}><SlidersHorizontal size={19} color={colors.primary} /><Text style={styles.filtersText}>Filters{activeFilterCount ? ` (${activeFilterCount})` : ''}</Text></Pressable>
      </View>

      <FlatList horizontal data={quickFilters} keyExtractor={(item) => item.key} contentContainerStyle={[styles.quickFilters, { paddingTop: insets.top + 76 }]} showsHorizontalScrollIndicator={false} renderItem={({ item }) => <View style={styles.chipWrap}><FilterChip label={item.label} selected={filters[item.key] === true} onPress={() => updateQuickFilter(item.key)} /></View>} />

      {loading ? <View style={[styles.loadingOverlay, { top: insets.top + 132 }]}><ActivityIndicator size="small" color={colors.primary} /></View> : null}
      {location && facilities.length > 0 ? <View style={[styles.countBadge, { top: insets.top + 134 }]}><Text style={styles.countText}>{t('map.facilitiesNearby', { count: facilities.length })}</Text></View> : null}

      {showSearch ? <SoftCard style={[styles.searchResults, { top: insets.top + 126 }]}>{searching ? <ActivityIndicator color={colors.primary} /> : searchResults.length ? <FlatList data={searchResults} keyExtractor={(item) => item.id} keyboardShouldPersistTaps="handled" renderItem={({ item }) => <Pressable accessibilityRole="button" accessibilityLabel={`Select ${item.name}`} onPress={() => handleSearchResultPress(item)} style={styles.searchResultItem}><Text style={styles.searchResultName} numberOfLines={1}>{item.name}</Text><Text style={styles.searchResultAddress} numberOfLines={1}>{item.town || item.address || 'Location unavailable'}</Text><StatusBadge status={getOpenStatus(item)} /></Pressable>} /> : <Text style={styles.noResults}>{t('list.empty')}</Text>}</SoftCard> : null}

      {showEmergency ? <SoftCard style={styles.bottomCard}><Text style={styles.cardEyebrow}>NEAREST FACILITY</Text>{emergencyFacility ? <><Text style={styles.cardTitle} numberOfLines={2}>{emergencyFacility.name}</Text><Text style={styles.cardMeta}>Approx. {walkingTime} min walk · {priceLabel(emergencyFacility)}</Text><View style={styles.cardStatus}><StatusBadge status={getOpenStatus(emergencyFacility)} /></View><View style={styles.cardActions}><PrimaryButton title="Get directions" onPress={() => Linking.openURL(`https://www.google.com/maps/dir/?api=1&destination=${emergencyFacility.latitude},${emergencyFacility.longitude}&travelmode=walking&dir_action=navigate`)} style={styles.cardPrimary} /><Pressable accessibilityRole="button" accessibilityLabel="Close nearest facility" onPress={() => setShowEmergency(false)} style={styles.dismiss}><Text style={styles.dismissText}>Close</Text></Pressable></View></> : <><Text style={styles.cardTitle}>{t('map.noFacilitiesFound')}</Text><Pressable accessibilityRole="button" onPress={() => setShowEmergency(false)} style={styles.dismiss}><Text style={styles.dismissText}>Close</Text></Pressable></>}</SoftCard> : selectedFacility ? <SoftCard onPress={() => openFacility(selectedFacility)} accessibilityLabel={`View details for ${selectedFacility.name}`} style={styles.bottomCard}><View style={styles.selectedRow}><View style={styles.selectedCopy}><Text style={styles.cardTitle} numberOfLines={1}>{selectedFacility.name}</Text><Text style={styles.cardMeta} numberOfLines={1}>{selectedFacility.town || selectedFacility.address || 'Location unavailable'} · {priceLabel(selectedFacility)}</Text></View><StatusBadge status={getOpenStatus(selectedFacility)} /></View><Text style={styles.detailsLink}>View details</Text></SoftCard> : <UrgentButton onPress={handleEmergencyPress} style={styles.urgentButton} />}
    </View>
  );
};

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: colors.mintSurface }, map: { flex: 1 },
  loadingContainer: { flex: 1, justifyContent: 'center', alignItems: 'center', backgroundColor: colors.mintSurface }, loadingText: { ...typography.bodySmall, color: colors.textSecondary, marginTop: spacing.md },
  searchRow: { position: 'absolute', left: spacing.lg, right: spacing.lg, flexDirection: 'row', gap: spacing.sm, zIndex: 20 },
  searchBar: { ...mapOverlaySurface, flex: 1, minHeight: 48, flexDirection: 'row', alignItems: 'center', paddingLeft: spacing.lg }, searchInput: { ...typography.bodySmall, color: colors.textPrimary, flex: 1, paddingVertical: 12 }, iconButton: { minWidth: 44, minHeight: 44, alignItems: 'center', justifyContent: 'center' },
  filtersButton: { ...mapOverlaySurface, minHeight: 48, flexDirection: 'row', gap: 6, alignItems: 'center', justifyContent: 'center', paddingHorizontal: 12 }, filtersText: { ...typography.buttonSmall, color: colors.primary },
  quickFilters: { paddingLeft: spacing.lg, paddingRight: spacing.lg, paddingBottom: spacing.sm }, chipWrap: { marginRight: spacing.sm },
  loadingOverlay: { position: 'absolute', right: spacing.lg, width: 36, height: 36, alignItems: 'center', justifyContent: 'center', borderRadius: borderRadius.full, backgroundColor: colors.mapOverlay, ...shadows.sm },
  countBadge: { position: 'absolute', alignSelf: 'center', backgroundColor: colors.primary, borderRadius: borderRadius.full, paddingHorizontal: 12, paddingVertical: 6, ...shadows.sm }, countText: { ...typography.caption, color: colors.white, fontFamily: 'PlusJakartaSans_600SemiBold' },
  searchResults: { position: 'absolute', left: spacing.lg, right: spacing.lg, maxHeight: 310, padding: spacing.sm, zIndex: 30 }, searchResultItem: { padding: spacing.md, borderBottomWidth: 1, borderBottomColor: colors.borderLight }, searchResultName: { ...typography.label, color: colors.textPrimary }, searchResultAddress: { ...typography.caption, color: colors.textSecondary, marginTop: 2, marginBottom: spacing.xs }, noResults: { ...typography.bodySmall, color: colors.textMuted, textAlign: 'center', padding: spacing.lg },
  urgentButton: { position: 'absolute', bottom: spacing.lg, alignSelf: 'center', zIndex: 20 }, bottomCard: { position: 'absolute', left: spacing.lg, right: spacing.lg, bottom: spacing.md, zIndex: 20, padding: spacing.lg }, cardEyebrow: { ...typography.caption, fontFamily: 'PlusJakartaSans_700Bold', letterSpacing: 1, color: colors.textSecondary }, cardTitle: { ...typography.h4, color: colors.textPrimary, marginTop: 3 }, cardMeta: { ...typography.bodySmall, color: colors.textSecondary, marginTop: 2 }, cardStatus: { marginTop: spacing.sm }, cardActions: { flexDirection: 'row', alignItems: 'center', marginTop: spacing.md }, cardPrimary: { flex: 1 }, dismiss: { minWidth: 60, minHeight: 44, alignItems: 'center', justifyContent: 'center', marginLeft: spacing.sm }, dismissText: { ...typography.buttonSmall, color: colors.textSecondary }, selectedRow: { flexDirection: 'row', alignItems: 'flex-start' }, selectedCopy: { flex: 1, paddingRight: spacing.sm }, detailsLink: { ...typography.buttonSmall, color: colors.primary, marginTop: spacing.sm },
});

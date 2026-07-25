// ============================================================
// Project "Relief" — Map Screen
// Tagline: Find Comfort, Find Relief
// ============================================================

import React, { useState, useEffect, useCallback, useRef } from 'react';
import {
  View,
  Text,
  StyleSheet,
  TouchableOpacity,
  TextInput,
  FlatList,
  ActivityIndicator,
  Dimensions,
  Linking,
  Platform,
} from 'react-native';
import MapView, { Marker, Callout, PROVIDER_GOOGLE } from 'react-native-maps';
import { useTranslation } from 'react-i18next';
import { useNavigation, useFocusEffect } from '@react-navigation/native';
import { colors, typography, spacing, borderRadius, shadows } from '../theme';
import { Button, Card } from '../components';
import { useLocation } from '../hooks/useLocation';
import { useFilters } from '../context/FiltersContext';
import {
  fetchViewportFacilities,
  fetchClosestFacility,
  estimateWalkingTime,
  searchFacilities,
} from '../services/facilities';
import { getOpenStatus } from '../utils/openingHours';
import type { Facility, MapStackParamList } from '../types';
import type { NativeStackNavigationProp } from '@react-navigation/native-stack';

const { width, height } = Dimensions.get('window');
const ASPECT_RATIO = width / height;
const LATITUDE_DELTA = 0.0922;
const LONGITUDE_DELTA = LATITUDE_DELTA * ASPECT_RATIO;

const CLUSTER_RADIUS = 60;
const DEBOUNCE_MS = 400;

type MapNavigationProp = NativeStackNavigationProp<MapStackParamList, 'MapView'>;

interface Cluster {
  id: string;
  latitude: number;
  longitude: number;
  count: number;
  facilities: Facility[];
}

function clusterFacilities(
  facilities: Facility[],
  region: {
    latitude: number;
    longitude: number;
    latitudeDelta: number;
    longitudeDelta: number;
  },
): Cluster[] {
  if (facilities.length === 0) return [];

  const zoomLevel = Math.log2(360 / region.longitudeDelta);
  const clusterDistance =
    (region.latitudeDelta / height) * CLUSTER_RADIUS * (10 / zoomLevel);

  const clusters: Cluster[] = [];
  const assigned = new Set<string>();

  for (const facility of facilities) {
    if (assigned.has(facility.id)) continue;

    const clusterFacilities: Facility[] = [facility];
    assigned.add(facility.id);

    for (const other of facilities) {
      if (assigned.has(other.id)) continue;

      const dist = Math.sqrt(
        Math.pow(facility.latitude - other.latitude, 2) +
          Math.pow(facility.longitude - other.longitude, 2),
      );

      if (dist < clusterDistance) {
        clusterFacilities.push(other);
        assigned.add(other.id);
      }
    }

    if (clusterFacilities.length > 1) {
      const avgLat =
        clusterFacilities.reduce((s, f) => s + f.latitude, 0) /
        clusterFacilities.length;
      const avgLng =
        clusterFacilities.reduce((s, f) => s + f.longitude, 0) /
        clusterFacilities.length;

      // Stable cluster ID from sorted member IDs
      const sortedIds = clusterFacilities.map((f) => f.id).sort();
      clusters.push({
        id: `cluster-${sortedIds[0]}-${sortedIds.length}`,
        latitude: avgLat,
        longitude: avgLng,
        count: clusterFacilities.length,
        facilities: clusterFacilities,
      });
    } else {
      clusters.push({
        id: `single-${facility.id}`,
        latitude: facility.latitude,
        longitude: facility.longitude,
        count: 1,
        facilities: clusterFacilities,
      });
    }
  }

  return clusters;
}

export const MapScreen: React.FC = () => {
  const { t } = useTranslation();
  const navigation = useNavigation<MapNavigationProp>();
  const mapRef = useRef<MapView>(null);
  const { location, loading: locationLoading, refreshLocation } = useLocation();
  const { filters, activeFilterCount } = useFilters();

  const [facilities, setFacilities] = useState<Facility[]>([]);
  const [loading, setLoading] = useState(false);
  const [showEmergency, setShowEmergency] = useState(false);
  const [emergencyFacility, setEmergencyFacility] = useState<Facility | null>(null);
  const [walkingTime, setWalkingTime] = useState<number>(0);
  const [searchQuery, setSearchQuery] = useState('');
  const [searchResults, setSearchResults] = useState<Facility[]>([]);
  const [showSearch, setShowSearch] = useState(false);
  const [searching, setSearching] = useState(false);
  const [selectedFacility, setSelectedFacility] = useState<Facility | null>(null);
  const [currentRegion, setCurrentRegion] = useState({
    latitude: 51.5074,
    longitude: -0.1278,
    latitudeDelta: LATITUDE_DELTA,
    longitudeDelta: LONGITUDE_DELTA,
  });
  const [mapInitialized, setMapInitialized] = useState(false);

  // Monotonically increasing request ID for stale-response protection
  const requestIdRef = useRef(0);
  // Debounce timer
  const debounceRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  // Track whether a network request is in flight
  const inFlightRef = useRef(false);

  // Initial load when location arrives
  useEffect(() => {
    if (location && !mapInitialized) {
      const region = {
        latitude: location.latitude,
        longitude: location.longitude,
        latitudeDelta: LATITUDE_DELTA,
        longitudeDelta: LONGITUDE_DELTA,
      };
      setCurrentRegion(region);
      setMapInitialized(true);
      loadFacilitiesForRegion(region);
    }
  }, [location]);

  const loadFacilitiesForRegion = useCallback(
    async (region: {
      latitude: number;
      longitude: number;
      latitudeDelta: number;
      longitudeDelta: number;
    }) => {
      const myRequestId = ++requestIdRef.current;

      const minLat = region.latitude - region.latitudeDelta / 2;
      const maxLat = region.latitude + region.latitudeDelta / 2;
      const minLng = region.longitude - region.longitudeDelta / 2;
      const maxLng = region.longitude + region.longitudeDelta / 2;

      const hasActiveFilters = activeFilterCount > 0;
      const result = await fetchViewportFacilities(
        {
          minLatitude: minLat,
          maxLatitude: maxLat,
          minLongitude: minLng,
          maxLongitude: maxLng,
        },
        hasActiveFilters ? filters : undefined,
      );

      // Ignore stale responses — only apply if this is the latest request
      if (myRequestId < requestIdRef.current) return;

      setFacilities(result.facilities);
      setLoading(false);
      inFlightRef.current = false;
    },
    [activeFilterCount, filters],
  );

  const handleEmergencyPress = async () => {
    if (!location) {
      await refreshLocation();
      return;
    }
    setShowEmergency(true);
    const closest = await fetchClosestFacility(
      location.latitude,
      location.longitude,
    );
    if (closest) {
      setEmergencyFacility(closest);
      const time = estimateWalkingTime(
        location.latitude,
        location.longitude,
        closest.latitude,
        closest.longitude,
      );
      setWalkingTime(time);
      if (mapRef.current) {
        mapRef.current.animateToRegion(
          {
            latitude: closest.latitude,
            longitude: closest.longitude,
            latitudeDelta: 0.02,
            longitudeDelta: 0.02 * ASPECT_RATIO,
          },
          500,
        );
      }
    }
  };

  const handleSearch = useCallback(async () => {
    if (!searchQuery.trim()) return;
    setSearching(true);
    setShowSearch(true);
    const results = await searchFacilities(searchQuery.trim());
    setSearchResults(results);
    setSearching(false);
  }, [searchQuery]);

  const handleMarkerPress = useCallback((facility: Facility) => {
    setSelectedFacility(facility);
  }, []);

  const handleCalloutPress = useCallback(
    (facility: Facility) => {
      navigation.navigate('FacilityDetail', { facilityId: facility.id });
    },
    [navigation],
  );

  const handleSearchResultPress = useCallback((facility: Facility) => {
    setShowSearch(false);
    setSearchQuery('');
    if (mapRef.current) {
      mapRef.current.animateToRegion(
        {
          latitude: facility.latitude,
          longitude: facility.longitude,
          latitudeDelta: 0.02,
          longitudeDelta: 0.02 * ASPECT_RATIO,
        },
        500,
      );
    }
    setSelectedFacility(facility);
  }, []);

  // Debounced region change — does NOT clear existing markers
  const handleRegionChangeComplete = useCallback(
    (newRegion: any) => {
      setCurrentRegion(newRegion);

      if (debounceRef.current) {
        clearTimeout(debounceRef.current);
      }

      debounceRef.current = setTimeout(() => {
        if (!inFlightRef.current) {
          inFlightRef.current = true;
          setLoading(true);
          loadFacilitiesForRegion(newRegion);
        }
      }, DEBOUNCE_MS);
    },
    [loadFacilitiesForRegion],
  );

  const handleClusterPress = useCallback(
    (cluster: Cluster) => {
      if (mapRef.current) {
        mapRef.current.animateToRegion(
          {
            latitude: cluster.latitude,
            longitude: cluster.longitude,
            latitudeDelta: currentRegion.latitudeDelta / 3,
            longitudeDelta: currentRegion.longitudeDelta / 3,
          },
          500,
        );
      }
    },
    [currentRegion],
  );

  const getMarkerColor = (facility: Facility): string => {
    if (facility.is_accessible || facility.has_wheelchair_access)
      return colors.mapPinAccessible;
    if (facility.has_baby_changing || facility.has_family_room)
      return colors.mapPinFamily;
    return colors.mapPinDefault;
  };

  const isCluster = (item: Facility | Cluster): item is Cluster => {
    return 'count' in item && (item as Cluster).count > 1;
  };

  // Clustering is memoised on facilities only — region changes don't
  // re-cluster until new data arrives (no flickering).
  const markers = React.useMemo<(Facility | Cluster)[]>(() => {
    const clusters = clusterFacilities(facilities, currentRegion);
    return clusters.map((c: Cluster) => {
      if (c.count === 1) {
        return c.facilities[0];
      }
      return c;
    });
  }, [facilities, currentRegion]);

  const renderCalloutStatus = (facility: Facility) => {
    const status = getOpenStatus(facility);
    const label =
      status === 'open'
        ? t('map.open')
        : status === 'closed'
        ? t('map.closed')
        : t('map.hoursUnknown', { defaultValue: 'Hours unknown' });
    const color =
      status === 'open'
        ? colors.success
        : status === 'closed'
        ? colors.error
        : colors.textMuted;
    return (
      <Text style={[styles.calloutStatus, { color }]}>{label}</Text>
    );
  };

  return (
    <View style={styles.container}>
      {locationLoading && !mapInitialized ? (
        <View style={styles.loadingContainer}>
          <ActivityIndicator size="large" color={colors.primary} />
          <Text style={styles.loadingText}>{t('common.loading')}</Text>
        </View>
      ) : (
        <MapView
          ref={mapRef}
          style={styles.map}
          initialRegion={currentRegion}
          onRegionChangeComplete={handleRegionChangeComplete}
          showsUserLocation={true}
          showsMyLocationButton={true}
          showsCompass={true}
          rotateEnabled={true}
          zoomEnabled={true}
          scrollEnabled={true}
          pitchEnabled={false}
          provider={Platform.OS === 'android' ? PROVIDER_GOOGLE : undefined}
        >
          {markers.map((item) => {
            if (isCluster(item)) {
              return (
                <Marker
                  key={item.id}
                  coordinate={{
                    latitude: item.latitude,
                    longitude: item.longitude,
                  }}
                  onPress={() => handleClusterPress(item)}
                  anchor={{ x: 0.5, y: 0.5 }}
                >
                  <View style={styles.clusterCircle}>
                    <Text style={styles.clusterText}>{item.count}</Text>
                  </View>
                </Marker>
              );
            }

            const facility = item;
            return (
              <Marker
                key={facility.id}
                coordinate={{
                  latitude: facility.latitude,
                  longitude: facility.longitude,
                }}
                pinColor={getMarkerColor(facility)}
                onPress={() => handleMarkerPress(facility)}
                tracksViewChanges={false}
              >
                <Callout onPress={() => handleCalloutPress(facility)}>
                  <View style={styles.calloutContainer}>
                    <Text style={styles.calloutName} numberOfLines={1}>
                      {facility.name}
                    </Text>
                    <Text style={styles.calloutAddress} numberOfLines={1}>
                      {facility.town || facility.address}
                    </Text>
                    <View style={styles.calloutRow}>
                      {renderCalloutStatus(facility)}
                      {facility.is_free !== undefined && (
                        <Text style={styles.calloutPrice}>
                          {facility.is_free
                            ? t('facility.free')
                            : t('facility.paid')}
                        </Text>
                      )}
                    </View>
                    <Text style={styles.calloutAction}>
                      {t('map.tapForDetails')}
                    </Text>
                  </View>
                </Callout>
              </Marker>
            );
          })}
        </MapView>
      )}

      {/* Loading Overlay — does NOT remove markers */}
      {loading && (
        <View style={styles.loadingOverlay}>
          <ActivityIndicator size="small" color={colors.primary} />
        </View>
      )}

      {/* Emergency Button */}
      {!showEmergency && (
        <TouchableOpacity
          style={styles.emergencyButton}
          onPress={handleEmergencyPress}
          activeOpacity={0.8}
        >
          <Text style={styles.emergencyButtonText}>
            {t('map.needOneNow')}
          </Text>
          <Text style={styles.emergencyButtonSubtext}>
            {t('map.needOneNowSubtext')}
          </Text>
        </TouchableOpacity>
      )}

      {/* Emergency Result Card */}
      {showEmergency && (
        <Card variant="elevated" style={styles.emergencyCard}>
          <Text style={styles.emergencyCardTitle}>
            {t('map.closestFacility')}
          </Text>
          {emergencyFacility ? (
            <>
              <Text style={styles.emergencyCardName}>
                {emergencyFacility.name}
              </Text>
              <Text style={styles.emergencyCardInfo}>
                {t('map.walkingTime', { minutes: walkingTime })}
              </Text>
              <View style={styles.emergencyCardRow}>
                {renderCalloutStatus(emergencyFacility)}
              </View>
            </>
          ) : (
            <Text style={styles.emergencyCardName}>
              {t('map.noFacilitiesFound')}
            </Text>
          )}
          <View style={styles.emergencyCardActions}>
            <Button
              title={t('map.getDirections')}
              onPress={() => {
                if (!emergencyFacility) return;
                const url = `https://www.google.com/maps/dir/?api=1&destination=${emergencyFacility.latitude},${emergencyFacility.longitude}&travelmode=walking&dir_action=navigate`;
                Linking.openURL(url);
              }}
              size="sm"
              style={styles.emergencyCardButton}
            />
            <TouchableOpacity
              onPress={() => setShowEmergency(false)}
              style={styles.emergencyDismissButton}
            >
              <Text style={styles.emergencyDismissText}>
                {t('common.close')}
              </Text>
            </TouchableOpacity>
          </View>
        </Card>
      )}

      {/* Search Bar */}
      <View style={styles.searchBar}>
        <TextInput
          style={styles.searchInput}
          placeholder={t('map.searchPlaceholder')}
          placeholderTextColor={colors.textMuted}
          value={searchQuery}
          onChangeText={setSearchQuery}
          onSubmitEditing={handleSearch}
          returnKeyType="search"
        />
        {searchQuery.length > 0 && (
          <TouchableOpacity
            onPress={() => {
              setSearchQuery('');
              setShowSearch(false);
              setSearchResults([]);
            }}
            style={styles.searchClearButton}
          >
            <Text style={styles.searchClearText}>✕</Text>
          </TouchableOpacity>
        )}
      </View>

      {/* Filter Button */}
      <TouchableOpacity
        style={[
          styles.filterButton,
          activeFilterCount > 0 && styles.filterButtonActive,
        ]}
        onPress={() => navigation.navigate('AdvancedFilters')}
        activeOpacity={0.7}
      >
        <Text style={styles.filterButtonIcon}>🔍</Text>
        {activeFilterCount > 0 && (
          <View style={styles.filterBadge}>
            <Text style={styles.filterBadgeText}>{activeFilterCount}</Text>
          </View>
        )}
      </TouchableOpacity>

      {/* Search Results */}
      {showSearch && (
        <View style={styles.searchResults}>
          {searching ? (
            <ActivityIndicator
              size="small"
              color={colors.primary}
              style={styles.searchLoadingIndicator}
            />
          ) : searchResults.length > 0 ? (
            <FlatList
              data={searchResults}
              keyExtractor={(item) => item.id}
              renderItem={({ item }) => (
                <TouchableOpacity
                  style={styles.searchResultItem}
                  onPress={() => handleSearchResultPress(item)}
                >
                  <Text style={styles.searchResultName}>{item.name}</Text>
                  <Text style={styles.searchResultAddress}>
                    {item.town || item.address}
                  </Text>
                  <View style={styles.searchResultMeta}>
                    {renderCalloutStatus(item)}
                    <Text style={styles.searchResultDistance}>
                      {item.town}
                    </Text>
                  </View>
                </TouchableOpacity>
              )}
              style={styles.searchResultsList}
              keyboardShouldPersistTaps="handled"
            />
          ) : (
            <Text style={styles.searchNoResults}>{t('list.empty')}</Text>
          )}
        </View>
      )}

      {/* Facility Count Badge */}
      {location && facilities.length > 0 && (
        <View style={styles.facilityCountBadge}>
          <Text style={styles.facilityCountText}>
            {t('map.facilitiesNearby', { count: facilities.length })}
          </Text>
        </View>
      )}
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: colors.background,
  },
  map: {
    flex: 1,
  },
  loadingContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    backgroundColor: colors.gray100,
  },
  loadingText: {
    ...typography.bodySmall,
    color: colors.textSecondary,
    marginTop: spacing.md,
  },
  loadingOverlay: {
    position: 'absolute',
    top: 60,
    right: spacing.lg,
    backgroundColor: colors.white,
    borderRadius: borderRadius.full,
    padding: spacing.sm,
    ...shadows.sm,
  },
  calloutContainer: {
    width: 200,
    padding: spacing.sm,
  },
  calloutName: {
    ...typography.bodySmall,
    color: colors.textPrimary,
    fontWeight: '600',
  },
  calloutAddress: {
    ...typography.caption,
    color: colors.textSecondary,
    marginTop: 2,
  },
  calloutRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    marginTop: spacing.xs,
  },
  calloutStatus: {
    ...typography.caption,
    fontWeight: '600',
  },
  calloutPrice: {
    ...typography.caption,
    color: colors.textSecondary,
  },
  calloutAction: {
    ...typography.caption,
    color: colors.primary,
    marginTop: spacing.xs,
    fontStyle: 'italic',
  },
  clusterCircle: {
    width: 40,
    height: 40,
    borderRadius: 20,
    backgroundColor: colors.mapCluster,
    justifyContent: 'center',
    alignItems: 'center',
    borderWidth: 3,
    borderColor: colors.white,
    ...Platform.select({
      ios: {
        shadowColor: colors.black,
        shadowOffset: { width: 0, height: 2 },
        shadowOpacity: 0.3,
        shadowRadius: 4,
      },
      android: {
        elevation: 5,
      },
    }),
  },
  clusterText: {
    color: colors.white,
    fontWeight: '800',
    fontSize: 14,
    includeFontPadding: false,
  },
  emergencyButton: {
    position: 'absolute',
    bottom: 120,
    alignSelf: 'center',
    backgroundColor: colors.error,
    paddingVertical: spacing.lg,
    paddingHorizontal: spacing['3xl'],
    borderRadius: borderRadius.full,
    ...shadows.lg,
  },
  emergencyButtonText: {
    ...typography.emergency,
    color: colors.white,
    textAlign: 'center',
  },
  emergencyButtonSubtext: {
    ...typography.caption,
    color: colors.white,
    textAlign: 'center',
    marginTop: 2,
  },
  emergencyCard: {
    position: 'absolute',
    bottom: 120,
    left: spacing.lg,
    right: spacing.lg,
    padding: spacing.lg,
  },
  emergencyCardTitle: {
    ...typography.label,
    color: colors.textSecondary,
  },
  emergencyCardName: {
    ...typography.h3,
    color: colors.textPrimary,
    marginTop: spacing.xs,
  },
  emergencyCardInfo: {
    ...typography.body,
    color: colors.textSecondary,
    marginTop: spacing.xs,
  },
  emergencyCardRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    marginTop: spacing.sm,
  },
  emergencyCardActions: {
    flexDirection: 'row',
    alignItems: 'center',
    marginTop: spacing.md,
  },
  emergencyCardButton: {
    flex: 1,
  },
  emergencyDismissButton: {
    marginLeft: spacing.md,
    paddingVertical: spacing.sm,
    paddingHorizontal: spacing.md,
  },
  emergencyDismissText: {
    ...typography.bodySmall,
    color: colors.textSecondary,
  },
  searchBar: {
    position: 'absolute',
    top: 60,
    left: spacing.lg,
    right: spacing.lg,
    backgroundColor: colors.white,
    borderRadius: borderRadius.lg,
    paddingHorizontal: spacing.lg,
    flexDirection: 'row',
    alignItems: 'center',
    ...shadows.md,
  },
  searchInput: {
    ...typography.body,
    color: colors.textPrimary,
    paddingVertical: spacing.md,
    flex: 1,
  },
  searchClearButton: {
    padding: spacing.xs,
  },
  searchClearText: {
    ...typography.bodySmall,
    color: colors.textMuted,
  },
  searchResults: {
    position: 'absolute',
    top: 110,
    left: spacing.lg,
    right: spacing.lg,
    backgroundColor: colors.white,
    borderRadius: borderRadius.lg,
    maxHeight: 300,
    ...shadows.md,
  },
  searchResultsList: {
    padding: spacing.sm,
  },
  searchResultItem: {
    paddingVertical: spacing.md,
    paddingHorizontal: spacing.sm,
    borderBottomWidth: 1,
    borderBottomColor: colors.borderLight,
  },
  searchResultName: {
    ...typography.body,
    color: colors.textPrimary,
    fontWeight: '600',
  },
  searchResultAddress: {
    ...typography.caption,
    color: colors.textSecondary,
    marginTop: 2,
  },
  searchResultMeta: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    marginTop: spacing.xs,
  },
  searchResultDistance: {
    ...typography.caption,
    color: colors.textSecondary,
  },
  searchLoadingIndicator: {
    padding: spacing.lg,
  },
  searchNoResults: {
    ...typography.body,
    color: colors.textMuted,
    textAlign: 'center',
    padding: spacing.lg,
  },
  filterButton: {
    position: 'absolute',
    top: 115,
    right: spacing.lg,
    backgroundColor: colors.white,
    borderRadius: borderRadius.full,
    width: 44,
    height: 44,
    justifyContent: 'center',
    alignItems: 'center',
    ...shadows.md,
    zIndex: 10,
  },
  filterButtonActive: {
    backgroundColor: colors.tealSoft,
    borderWidth: 2,
    borderColor: colors.primary,
  },
  filterButtonIcon: {
    fontSize: 18,
  },
  filterBadge: {
    position: 'absolute',
    top: -4,
    right: -4,
    backgroundColor: colors.primary,
    borderRadius: 10,
    width: 20,
    height: 20,
    justifyContent: 'center',
    alignItems: 'center',
    borderWidth: 2,
    borderColor: colors.white,
  },
  filterBadgeText: {
    fontFamily: 'Inter_600SemiBold',
    fontSize: 10,
    fontWeight: '600',
    color: colors.white,
  },
  facilityCountBadge: {
    position: 'absolute',
    top: 110,
    alignSelf: 'center',
    backgroundColor: colors.primary,
    borderRadius: borderRadius.full,
    paddingVertical: spacing.xs,
    paddingHorizontal: spacing.md,
    ...shadows.sm,
  },
  facilityCountText: {
    ...typography.caption,
    color: colors.white,
    fontWeight: '600',
  },
});

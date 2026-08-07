import React, { useMemo, useState } from 'react';
import { Dimensions, Platform, StyleSheet } from 'react-native';
import MapView, { Marker, Polyline, PROVIDER_GOOGLE } from 'react-native-maps';
import { ClusterMarker } from './ClusterMarker';
import { FacilityMarker } from './FacilityMarker';
import { SelectedFacilityMarker } from './SelectedFacilityMarker';
import type { Region } from '../hooks/useFindExperience';
import { colors } from '../theme';
import { RELIEF_MAP_STYLE } from '../theme/mapStyle';
import type { Facility } from '../types';

const { height } = Dimensions.get('window');
const CLUSTER_RADIUS = 60;

interface Cluster {
  id: string;
  latitude: number;
  longitude: number;
  count: number;
  facilities: Facility[];
}

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
      if (
        Math.hypot(
          facility.latitude - other.latitude,
          facility.longitude - other.longitude,
        ) < clusterDistance
      ) {
        members.push(other);
        assigned.add(other.id);
      }
    }
    const latitude = members.reduce((sum, item) => sum + item.latitude, 0) / members.length;
    const longitude = members.reduce((sum, item) => sum + item.longitude, 0) / members.length;
    const sortedIds = members.map((item) => item.id).sort();
    clusters.push({
      id: members.length > 1 ? `cluster-${sortedIds[0]}-${members.length}` : `single-${facility.id}`,
      latitude,
      longitude,
      count: members.length,
      facilities: members,
    });
  }
  return clusters;
}

interface FacilityMapBodyProps {
  mapRef: React.RefObject<MapView | null>;
  region: Region;
  facilities: Facility[];
  selectedFacilityId: string | null;
  urgentFacilityId: string | null;
  onRegionChangeComplete: (region: Region) => void;
  onSelectFacility: (facility: Facility) => void;
  onZoomToCluster: (latitude: number, longitude: number) => void;
  /** Straight line from the user to the active destination, or null. */
  routeLine: { latitude: number; longitude: number }[] | null;
}

/**
 * The map surface: Google tiles on Android, plus the refreshed native markers
 * and clustering from the UI work.
 */
export const FacilityMapBody: React.FC<FacilityMapBodyProps> = ({
  mapRef,
  region,
  facilities,
  selectedFacilityId,
  urgentFacilityId,
  onRegionChangeComplete,
  onSelectFacility,
  onZoomToCluster,
  routeLine,
}) => {
  const markers = useMemo<(Facility | Cluster)[]>(
    () =>
      clusterFacilities(facilities, region).map((cluster) =>
        cluster.count === 1 ? cluster.facilities[0] : cluster,
      ),
    [facilities, region],
  );

  const isCluster = (item: Facility | Cluster): item is Cluster =>
    'count' in item && item.count > 1;

  // Captured when THIS MapView mounts, not when the screen first rendered.
  //
  // Switching to List unmounts the map, and switching back mounts a new one.
  // Previously the screen captured `initialRegion` on its own first render —
  // while the region was still the London fallback — so every return to Map
  // jumped back to London, discarding wherever the user had panned or
  // searched. Reading the shared region here means a remount resumes exactly
  // where the map left off. It is read once, so it never fights panning.
  const [mountRegion] = useState<Region>(region);

  return (
    <MapView
      ref={mapRef}
      style={styles.map}
      initialRegion={mountRegion}
      onRegionChangeComplete={onRegionChangeComplete}
      showsUserLocation
      // Replaced by Relief's own locate control, which is easier to find and
      // shares the app's camera pathway. Two controls would be redundant.
      showsMyLocationButton={false}
      showsCompass
      rotateEnabled
      zoomEnabled
      scrollEnabled
      pitchEnabled={false}
      provider={Platform.OS === 'android' ? PROVIDER_GOOGLE : undefined}
      customMapStyle={RELIEF_MAP_STYLE}
      // The style is the brand surface; without this the map follows the device
      // theme and rendered dark navy against Relief's light mint chrome.
      userInterfaceStyle="light"
    >
      {/* Direct line to the selected destination.
          Relief previously drew nothing at all: "Get directions" handed straight
          off to Google Maps, so there was never a line on our own map. This is a
          straight geodesic path, not a routed one — it is drawn dashed and
          labelled as direct distance precisely so it is not mistaken for a
          turn-by-turn route. Real routing needs the Directions API. */}
      {routeLine ? (
        <>
          <Polyline
            coordinates={routeLine}
            strokeColor={colors.primary}
            strokeWidth={8}
            lineCap="round"
            geodesic
            zIndex={1}
          />
          <Polyline
            coordinates={routeLine}
            strokeColor={colors.amber}
            strokeWidth={4}
            lineCap="round"
            lineDashPattern={[10, 12]}
            geodesic
            zIndex={2}
          />
        </>
      ) : null}
      {markers.map((item) => {
        if (isCluster(item)) {
          return (
            <Marker
              key={item.id}
              coordinate={{ latitude: item.latitude, longitude: item.longitude }}
              onPress={() => onZoomToCluster(item.latitude, item.longitude)}
              anchor={{ x: 0.5, y: 0.5 }}
              tracksViewChanges={false}
            >
              <ClusterMarker count={item.count} />
            </Marker>
          );
        }
        const isSelected =
          selectedFacilityId === item.id || urgentFacilityId === item.id;
        return (
          <Marker
            key={item.id}
            coordinate={{ latitude: item.latitude, longitude: item.longitude }}
            onPress={() => onSelectFacility(item)}
            anchor={{ x: 0.5, y: 0.5 }}
            tracksViewChanges={isSelected}
          >
            {isSelected ? (
              <SelectedFacilityMarker urgent={urgentFacilityId === item.id} />
            ) : (
              <FacilityMarker />
            )}
          </Marker>
        );
      })}
    </MapView>
  );
};

const styles = StyleSheet.create({ map: { flex: 1 } });

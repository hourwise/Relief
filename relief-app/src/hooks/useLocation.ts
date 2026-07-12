// ============================================================
// Project "Relief" — Location Hook
// ============================================================

import { useState, useEffect } from 'react';
import * as Location from 'expo-location';
import { Alert, Linking } from 'react-native';

export interface UserLocation {
  latitude: number;
  longitude: number;
  accuracy: number | null;
  address: string | null;
}

interface UseLocationReturn {
  location: UserLocation | null;
  error: string | null;
  loading: boolean;
  requestPermission: () => Promise<boolean>;
  refreshLocation: () => Promise<void>;
}

export function useLocation(): UseLocationReturn {
  const [location, setLocation] = useState<UserLocation | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  const requestPermission = async (): Promise<boolean> => {
    try {
      const { status } = await Location.requestForegroundPermissionsAsync();
      if (status !== 'granted') {
        setError('Location permission denied');
        Alert.alert(
          'Location Required',
          'Relief needs your location to find nearby facilities. Please enable location access in Settings.',
          [
            { text: 'Cancel', style: 'cancel' },
            { text: 'Open Settings', onPress: () => Linking.openSettings() },
          ],
        );
        return false;
      }
      return true;
    } catch (err) {
      setError('Failed to request location permission');
      return false;
    }
  };

  const refreshLocation = async () => {
    try {
      setLoading(true);
      setError(null);

      const hasPermission = await requestPermission();
      if (!hasPermission) {
        setLoading(false);
        return;
      }

      const loc = await Location.getCurrentPositionAsync({
        accuracy: Location.Accuracy.Balanced,
      });

      // Reverse geocode to get address
      const geocode = await Location.reverseGeocodeAsync({
        latitude: loc.coords.latitude,
        longitude: loc.coords.longitude,
      });

      const address = geocode.length > 0
        ? [
            geocode[0].street,
            geocode[0].city,
            geocode[0].postalCode,
          ]
            .filter(Boolean)
            .join(', ')
        : null;

      setLocation({
        latitude: loc.coords.latitude,
        longitude: loc.coords.longitude,
        accuracy: loc.coords.accuracy,
        address,
      });
    } catch (err) {
      setError('Failed to get current location');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    refreshLocation();
  }, []);

  return {
    location,
    error,
    loading,
    requestPermission,
    refreshLocation,
  };
}
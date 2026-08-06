// ============================================================
// Project "Relief" — Location Hook
// ============================================================
// Location failure is not one state. "Still asking", "you said
// no", and "the device could not get a fix" need different UI and
// different recovery, so they are reported separately.
//
// This hook never raises an Alert of its own. A modal on first
// launch blocks the urgent journey, and a guest who declines
// location must still reach the map and search by town.
// ============================================================

import { useCallback, useEffect, useRef, useState } from 'react';
import * as Location from 'expo-location';

export interface UserLocation {
  latitude: number;
  longitude: number;
  accuracy: number | null;
  address: string | null;
}

export type LocationStatus =
  /** Permission check or fix in progress. */
  | 'loading'
  /** Permission granted and a fix is held. */
  | 'granted'
  /** The user declined; do not ask again unprompted. */
  | 'denied'
  /** Permission granted but no fix could be obtained. */
  | 'unavailable';

interface UseLocationReturn {
  location: UserLocation | null;
  status: LocationStatus;
  /** True only during the very first resolution, for the initial splash state. */
  initialising: boolean;
  requestPermission: () => Promise<boolean>;
  refreshLocation: () => Promise<void>;
}

export function useLocation(): UseLocationReturn {
  const [location, setLocation] = useState<UserLocation | null>(null);
  const [status, setStatus] = useState<LocationStatus>('loading');
  const [initialising, setInitialising] = useState(true);
  const mountedRef = useRef(true);

  useEffect(() => {
    mountedRef.current = true;
    return () => {
      mountedRef.current = false;
    };
  }, []);

  const requestPermission = useCallback(async (): Promise<boolean> => {
    try {
      const { status: permission } =
        await Location.requestForegroundPermissionsAsync();
      const granted = permission === 'granted';
      if (!granted && mountedRef.current) setStatus('denied');
      return granted;
    } catch {
      if (mountedRef.current) setStatus('denied');
      return false;
    }
  }, []);

  const refreshLocation = useCallback(async () => {
    if (mountedRef.current) setStatus('loading');

    try {
      // Check the existing grant before prompting, so a returning user is not
      // re-asked and a previous refusal is respected.
      const existing = await Location.getForegroundPermissionsAsync();
      const granted =
        existing.status === 'granted' || (await requestPermission());

      if (!granted) {
        if (mountedRef.current) setStatus('denied');
        return;
      }

      const fix = await Location.getCurrentPositionAsync({
        accuracy: Location.Accuracy.Balanced,
      });

      // Reverse geocoding is a nicety for the UI label. It must never decide
      // whether we have a usable position.
      let address: string | null = null;
      try {
        const geocode = await Location.reverseGeocodeAsync({
          latitude: fix.coords.latitude,
          longitude: fix.coords.longitude,
        });
        if (geocode.length > 0) {
          address =
            [geocode[0].street, geocode[0].city, geocode[0].postalCode]
              .filter(Boolean)
              .join(', ') || null;
        }
      } catch {
        address = null;
      }

      if (!mountedRef.current) return;
      setLocation({
        latitude: fix.coords.latitude,
        longitude: fix.coords.longitude,
        accuracy: fix.coords.accuracy,
        address,
      });
      setStatus('granted');
    } catch {
      // Permission held but no fix: indoors, airplane mode, GPS disabled.
      if (mountedRef.current) setStatus('unavailable');
    } finally {
      if (mountedRef.current) setInitialising(false);
    }
  }, [requestPermission]);

  useEffect(() => {
    refreshLocation();
  }, [refreshLocation]);

  return { location, status, initialising, requestPermission, refreshLocation };
}

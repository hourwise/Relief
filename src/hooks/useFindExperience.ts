// ============================================================
// Project "Relief" — Shared Find state (Map + List)
// ============================================================
// Map and List are two views of ONE search. They share location,
// loaded facilities, search state, filters, loading/error state
// and the selected facility, because a user who filters on the
// map and then switches to the list expects the same results —
// not a second, differently-stale query.
// ============================================================

import { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import { Dimensions } from 'react-native';
import {
  fetchClosestFacility,
  fetchViewportFacilities,
  searchFacilities,
} from '../services/facilities';
import { useFilters } from '../context/FiltersContext';
import { useLocation, type LocationStatus, type UserLocation } from './useLocation';
import { distanceMetres } from '../utils/distance';
import { getOpenStatus } from '../utils/openingHours';
import { sortFacilities, type RankedFacility, type SortMode } from '../utils/facilitySort';
import type { Facility, NearestFacilityResult } from '../types';

const { width, height } = Dimensions.get('window');
const ASPECT_RATIO = width / height;
const LATITUDE_DELTA = 0.0922;
const LONGITUDE_DELTA = LATITUDE_DELTA * ASPECT_RATIO;
const DEBOUNCE_MS = 400;

/** Fallback view (central London) used only until a real position arrives. */
const FALLBACK_REGION: Region = {
  latitude: 51.5074,
  longitude: -0.1278,
  latitudeDelta: LATITUDE_DELTA,
  longitudeDelta: LONGITUDE_DELTA,
};

export interface Region {
  latitude: number;
  longitude: number;
  latitudeDelta: number;
  longitudeDelta: number;
}

export type FindView = 'map' | 'list';

/**
 * The nearest-facility ("Need One Now") request, kept separate from the
 * viewport query so an RPC failure is never rendered as an empty map.
 */
export interface NearestState {
  active: boolean;
  loading: boolean;
  result: NearestFacilityResult | null;
  /** Set only when the RPC itself failed. Distinct from `notFound`. */
  error: string | null;
  /** The RPC succeeded and there is genuinely nothing within 25 km. */
  notFound: boolean;
}

export interface FindExperience {
  view: FindView;
  setView: (view: FindView) => void;

  // Location
  location: UserLocation | null;
  locationStatus: LocationStatus;
  locationInitialising: boolean;
  refreshLocation: () => Promise<void>;

  // Viewport facilities, shared by both views
  facilities: Facility[];
  ranked: RankedFacility[];
  facilitiesLoading: boolean;
  facilitiesError: string | null;
  truncated: boolean;
  /** The query succeeded and this area genuinely has no matching facilities. */
  noFacilitiesInArea: boolean;

  // Region
  region: Region;
  onRegionChangeComplete: (region: Region) => void;
  focusRegion: (latitude: number, longitude: number) => Region;
  /**
   * Where the camera should move to next, or null if it should stay put.
   *
   * The MapView takes `initialRegion` only, so updating `region` alone never
   * moves the camera — it just records where the user has panned to. Every
   * programmatic move (first fix, search result, cluster zoom, nearest
   * facility) publishes a target here and the screen animates to it.
   */
  cameraTarget: Region | null;
  /**
   * Move the camera back to the user's current position.
   *
   * Reuses the fix already held rather than asking the OS again — the position
   * is already good enough, and a fresh request would add latency for nothing.
   * If there is no fix because permission was denied or unavailable, this goes
   * through the normal location recovery instead of silently doing nothing.
   */
  centreOnUser: () => Promise<void>;
  /** True when a position is held, so the locate control can reflect it. */
  hasUserLocation: boolean;

  // Sorting (list)
  sortMode: SortMode;
  setSortMode: (mode: SortMode) => void;

  // Search
  searchQuery: string;
  setSearchQuery: (value: string) => void;
  runSearch: () => Promise<void>;
  clearSearch: () => void;
  searchResults: Facility[];
  searchActive: boolean;
  searching: boolean;
  searchError: string | null;

  // Selection
  selectedFacility: Facility | null;
  selectFacility: (facility: Facility | null) => void;

  // Need One Now
  nearest: NearestState;
  findNearest: () => Promise<void>;
  dismissNearest: () => void;

  // Recovery
  retry: () => void;
}

export function useFindExperience(): FindExperience {
  const { filters, activeFilterCount } = useFilters();
  const {
    location,
    status: locationStatus,
    initialising: locationInitialising,
    refreshLocation,
  } = useLocation();

  const [view, setView] = useState<FindView>('map');
  const [facilities, setFacilities] = useState<Facility[]>([]);
  const [facilitiesLoading, setFacilitiesLoading] = useState(false);
  const [facilitiesError, setFacilitiesError] = useState<string | null>(null);
  const [truncated, setTruncated] = useState(false);
  const [hasLoadedOnce, setHasLoadedOnce] = useState(false);
  const [region, setRegion] = useState<Region>(FALLBACK_REGION);
  const [sortMode, setSortMode] = useState<SortMode>('distance');
  const [centredOnUser, setCentredOnUser] = useState(false);
  const [cameraTarget, setCameraTarget] = useState<Region | null>(null);

  const [searchQuery, setSearchQuery] = useState('');
  const [searchResults, setSearchResults] = useState<Facility[]>([]);
  const [searchActive, setSearchActive] = useState(false);
  const [searching, setSearching] = useState(false);
  const [searchError, setSearchError] = useState<string | null>(null);

  const [selectedFacility, setSelectedFacility] = useState<Facility | null>(null);
  const [nearest, setNearest] = useState<NearestState>({
    active: false,
    loading: false,
    result: null,
    error: null,
    notFound: false,
  });

  // ── Viewport loading: latest request wins ──────────────────
  // `sequence` discards responses that arrive after a newer request, and
  // `queuedRegion` guarantees the newest region is still fetched even if it
  // arrived while an older request was in flight. The previous implementation
  // dropped that region entirely, so a fast pan could leave the visible area
  // permanently unfetched.
  const sequenceRef = useRef(0);
  const inFlightRef = useRef(false);
  const queuedRegionRef = useRef<Region | null>(null);
  const debounceRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const filtersRef = useRef(filters);
  const activeFilterCountRef = useRef(activeFilterCount);
  const loadRef = useRef<(region: Region) => void>(() => undefined);
  const mountedRef = useRef(true);

  useEffect(() => {
    filtersRef.current = filters;
    activeFilterCountRef.current = activeFilterCount;
  }, [filters, activeFilterCount]);

  useEffect(() => {
    mountedRef.current = true;
    return () => {
      mountedRef.current = false;
      if (debounceRef.current) clearTimeout(debounceRef.current);
    };
  }, []);

  const load = useCallback(async (target: Region) => {
    if (inFlightRef.current) {
      // Keep only the newest region; older queued regions are already stale.
      queuedRegionRef.current = target;
      return;
    }

    inFlightRef.current = true;
    const sequence = ++sequenceRef.current;
    setFacilitiesLoading(true);

    try {
      const result = await fetchViewportFacilities(
        {
          minLatitude: target.latitude - target.latitudeDelta / 2,
          maxLatitude: target.latitude + target.latitudeDelta / 2,
          minLongitude: target.longitude - target.longitudeDelta / 2,
          maxLongitude: target.longitude + target.longitudeDelta / 2,
        },
        activeFilterCountRef.current > 0 ? filtersRef.current : undefined,
      );

      // A newer request has been issued; its response is the truth.
      if (sequence !== sequenceRef.current || !mountedRef.current) return;

      if (result.ok) {
        setFacilities(result.data.facilities);
        setTruncated(result.data.truncated);
        setFacilitiesError(null);
      } else {
        // Keep whatever is already on screen rather than blanking it, and say
        // what went wrong. Never substitute fake or empty data for a failure.
        setFacilitiesError(result.error);
      }
      setHasLoadedOnce(true);
    } finally {
      inFlightRef.current = false;
      const queued = queuedRegionRef.current;
      queuedRegionRef.current = null;

      if (queued && mountedRef.current) {
        // Serve the newest region immediately; stay in the loading state.
        loadRef.current(queued);
      } else if (mountedRef.current) {
        setFacilitiesLoading(false);
      }
    }
  }, []);

  useEffect(() => {
    loadRef.current = load;
  }, [load]);

  // Centre on the user once a real position arrives, then fetch.
  useEffect(() => {
    if (!location || centredOnUser) return;
    const next: Region = {
      latitude: location.latitude,
      longitude: location.longitude,
      latitudeDelta: LATITUDE_DELTA,
      longitudeDelta: LONGITUDE_DELTA,
    };
    setRegion(next);
    // The camera must be told to move; setRegion alone only records state.
    // Without this the map sat on the London fallback while facilities were
    // fetched for the user's real position, so the count and the visible
    // markers disagreed.
    setCameraTarget(next);
    setCentredOnUser(true);
    load(next);
  }, [location, centredOnUser, load]);

  // If location is refused or unavailable, still load the fallback viewport so
  // the map and list are usable and search by town remains the way in.
  useEffect(() => {
    if (centredOnUser || hasLoadedOnce) return;
    if (locationStatus === 'denied' || locationStatus === 'unavailable') {
      load(FALLBACK_REGION);
    }
  }, [locationStatus, centredOnUser, hasLoadedOnce, load]);

  // A filter change must refresh the current viewport without needing a pan.
  const filterSignature = useMemo(() => JSON.stringify(filters), [filters]);
  const previousSignatureRef = useRef(filterSignature);
  useEffect(() => {
    if (previousSignatureRef.current === filterSignature) return;
    previousSignatureRef.current = filterSignature;
    if (hasLoadedOnce) load(region);
    // `region` is read as of this render on purpose: region changes have their
    // own debounced path and must not be duplicated here.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [filterSignature, hasLoadedOnce, load]);

  const onRegionChangeComplete = useCallback(
    (next: Region) => {
      setRegion(next);
      if (debounceRef.current) clearTimeout(debounceRef.current);
      debounceRef.current = setTimeout(() => load(next), DEBOUNCE_MS);
    },
    [load],
  );

  const focusRegion = useCallback((latitude: number, longitude: number): Region => {
    const next: Region = {
      latitude,
      longitude,
      latitudeDelta: 0.02,
      longitudeDelta: 0.02 * ASPECT_RATIO,
    };
    setRegion(next);
    setCameraTarget(next);
    return next;
  }, []);

  const retry = useCallback(() => {
    setFacilitiesError(null);
    load(region);
  }, [load, region]);

  const centreOnUser = useCallback(async () => {
    if (!location) {
      // No fix: run the normal recovery, which re-requests permission if that
      // is what is missing. The centring effect takes over once a fix lands.
      await refreshLocation();
      return;
    }

    const next: Region = {
      latitude: location.latitude,
      longitude: location.longitude,
      // Neighbourhood zoom: tight enough to be useful on arrival, wide enough
      // to show more than the pavement you are standing on.
      latitudeDelta: 0.01,
      longitudeDelta: 0.01 * ASPECT_RATIO,
    };

    setRegion(next);
    setCameraTarget(next);
    load(next);
  }, [location, refreshLocation, load]);

  // ── Ranked list, shared by both views ─────────────────────
  const ranked = useMemo<RankedFacility[]>(() => {
    const openNowOnly = filters.open_now === true;

    const items: RankedFacility[] = facilities
      .filter((facility) => !openNowOnly || getOpenStatus(facility) === 'open')
      .map((facility) => ({
        facility,
        distanceMetres: location
          ? distanceMetres(
              location.latitude,
              location.longitude,
              facility.latitude,
              facility.longitude,
            )
          : null,
      }));

    // Without a position there is no distance to sort by, so fall back to
    // rating rather than presenting an arbitrary order as "nearest".
    const effectiveMode: SortMode =
      sortMode === 'distance' && !location ? 'rating' : sortMode;

    return sortFacilities(items, effectiveMode);
  }, [facilities, location, sortMode, filters.open_now]);

  // ── Search ────────────────────────────────────────────────
  const runSearch = useCallback(async () => {
    const term = searchQuery.trim();
    if (!term) return;
    setSearching(true);
    setSearchActive(true);
    setSearchError(null);
    const result = await searchFacilities(term);
    if (!mountedRef.current) return;
    if (result.ok) {
      setSearchResults(result.data);
    } else {
      setSearchResults([]);
      setSearchError(result.error);
    }
    setSearching(false);
  }, [searchQuery]);

  const clearSearch = useCallback(() => {
    setSearchQuery('');
    setSearchResults([]);
    setSearchActive(false);
    setSearchError(null);
  }, []);

  const selectFacility = useCallback((facility: Facility | null) => {
    setSelectedFacility(facility);
    if (facility) {
      setNearest((previous) => ({ ...previous, active: false }));
    }
  }, []);

  // ── Need One Now ──────────────────────────────────────────
  const findNearest = useCallback(async () => {
    if (!location) {
      // No position yet: ask again rather than reporting "nothing nearby".
      await refreshLocation();
      return;
    }

    setSelectedFacility(null);
    setNearest({
      active: true,
      loading: true,
      result: null,
      error: null,
      notFound: false,
    });

    const result = await fetchClosestFacility(location.latitude, location.longitude);
    if (!mountedRef.current) return;

    if (!result.ok) {
      setNearest({
        active: true,
        loading: false,
        result: null,
        error: result.error,
        notFound: false,
      });
      return;
    }

    setNearest({
      active: true,
      loading: false,
      result: result.data,
      error: null,
      notFound: result.data === null,
    });
  }, [location, refreshLocation]);

  const dismissNearest = useCallback(() => {
    setNearest({
      active: false,
      loading: false,
      result: null,
      error: null,
      notFound: false,
    });
  }, []);

  return {
    view,
    setView,

    location,
    locationStatus,
    locationInitialising,
    refreshLocation,

    facilities,
    ranked,
    facilitiesLoading,
    facilitiesError,
    truncated,
    noFacilitiesInArea:
      hasLoadedOnce && !facilitiesLoading && !facilitiesError && ranked.length === 0,

    region,
    onRegionChangeComplete,
    focusRegion,
    cameraTarget,
    centreOnUser,
    hasUserLocation: location !== null,

    sortMode,
    setSortMode,

    searchQuery,
    setSearchQuery,
    runSearch,
    clearSearch,
    searchResults,
    searchActive,
    searching,
    searchError,

    selectedFacility,
    selectFacility,

    nearest,
    findNearest,
    dismissNearest,

    retry,
  };
}

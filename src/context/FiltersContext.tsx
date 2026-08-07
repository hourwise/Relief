// ============================================================
// Project "Relief" — Filters Context (Phase 3)
// Shared filter state between MapScreen, ListScreen,
// and AdvancedFiltersScreen
// ============================================================

import React, { createContext, useContext, useState, useCallback } from 'react';
import type { FacilityFilters } from '../types';
import { countActiveFilters } from '../utils/filterDefinitions';

interface FiltersContextType {
  filters: Partial<FacilityFilters>;
  setFilters: (filters: Partial<FacilityFilters>) => void;
  clearFilters: () => void;
  activeFilterCount: number;
}

const defaultFilters: Partial<FacilityFilters> = {};

const FiltersContext = createContext<FiltersContextType>({
  filters: defaultFilters,
  setFilters: () => {},
  clearFilters: () => {},
  activeFilterCount: 0,
});

export const FiltersProvider: React.FC<{ children: React.ReactNode }> = ({
  children,
}) => {
  const [filters, setFiltersState] = useState<Partial<FacilityFilters>>(defaultFilters);

  const setFilters = useCallback((newFilters: Partial<FacilityFilters>) => {
    setFiltersState(newFilters);
  }, []);

  const clearFilters = useCallback(() => {
    setFiltersState(defaultFilters);
  }, []);

  // Counted through the shared definition so the badge matches what the
  // Filters screen shows. Counting only `true` here meant a Paid-only filter
  // (`is_free: false`) was active but the button still read "Filters".
  const activeFilterCount = countActiveFilters(filters);

  return (
    <FiltersContext.Provider
      value={{ filters, setFilters, clearFilters, activeFilterCount }}
    >
      {children}
    </FiltersContext.Provider>
  );
};

export const useFilters = () => useContext(FiltersContext);
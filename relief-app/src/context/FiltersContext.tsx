// ============================================================
// Project "Relief" — Filters Context (Phase 3)
// Shared filter state between MapScreen, ListScreen,
// and AdvancedFiltersScreen
// ============================================================

import React, { createContext, useContext, useState, useCallback } from 'react';
import type { FacilityFilters } from '../types';

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

  const activeFilterCount = Object.entries(filters).filter(
    ([key, val]) => {
      if (key === 'min_rating') return (val as number) > 0;
      return val === true;
    },
  ).length;

  return (
    <FiltersContext.Provider
      value={{ filters, setFilters, clearFilters, activeFilterCount }}
    >
      {children}
    </FiltersContext.Provider>
  );
};

export const useFilters = () => useContext(FiltersContext);
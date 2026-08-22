import type { Json, Tables } from './database.types';

export type FacilitySourceObservationCoordinateScope =
  | 'NONE'
  | 'FACILITY_LEVEL'
  | 'STATION_LEVEL'
  | 'TOILET_LEVEL';

export type FacilitySourceObservationUnitLinkStatus =
  | 'UNLINKED'
  | 'UNRESOLVED'
  | 'CONFIRMED_DISTINCT_UNIT'
  | 'SAME_UNIT_MULTI_SOURCE';

export type FacilitySourceObservationRow = Tables<'facility_source_observations'>;

export interface FacilitySourceObservation
  extends Omit<
    FacilitySourceObservationRow,
    'coordinate_scope' | 'unit_link_status' | 'observed_attributes'
  > {
  coordinate_scope: FacilitySourceObservationCoordinateScope;
  unit_link_status: FacilitySourceObservationUnitLinkStatus;
  observed_attributes: Json;
}

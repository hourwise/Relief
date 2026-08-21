import type { Tables } from './database.types';
import type { OpenHours, VerificationStatus } from './index';

export type ToiletUnitType =
  | 'male'
  | 'female'
  | 'unisex'
  | 'other'
  | 'unknown';

export type ToiletUnitIdentityStatus =
  | 'CONFIRMED_DISTINCT_UNIT'
  | 'LIKELY_DISTINCT_UNIT'
  | 'SOURCE_DISTINCT_PHYSICAL_UNKNOWN'
  | 'SAME_UNIT_MULTI_SOURCE'
  | 'UNRESOLVED';

export type ToiletUnitCoordinatePrecision = 'UNKNOWN' | 'TOILET_LEVEL';

export type ToiletUnitRow = Tables<'toilet_units'>;

export interface ToiletUnit
  extends Omit<
    ToiletUnitRow,
    | 'coordinate_precision'
    | 'identity_status'
    | 'open_hours'
    | 'publication_status'
    | 'unit_type'
    | 'verification_status'
  > {
  coordinate_precision: ToiletUnitCoordinatePrecision;
  identity_status: ToiletUnitIdentityStatus;
  open_hours: OpenHours | null;
  publication_status: 'published' | 'hidden' | 'under_review' | 'removed';
  unit_type: ToiletUnitType;
  verification_status: VerificationStatus;
}

export type ToiletUnitSource = Tables<'toilet_unit_sources'>;

export const TOILET_UNIT_TYPE_LABELS: Record<ToiletUnitType, string> = {
  male: 'Male',
  female: 'Female',
  unisex: 'Unisex',
  other: 'Other toilet provision',
  unknown: 'Toilet type unknown',
};

export const TOILET_UNIT_IDENTITY_LABELS: Record<ToiletUnitIdentityStatus, string> = {
  CONFIRMED_DISTINCT_UNIT: 'Confirmed unit',
  LIKELY_DISTINCT_UNIT: 'Likely separate unit',
  SOURCE_DISTINCT_PHYSICAL_UNKNOWN: 'Source row; physical unit unconfirmed',
  SAME_UNIT_MULTI_SOURCE: 'Multiple source records; same unit',
  UNRESOLVED: 'Physical unit unconfirmed',
};

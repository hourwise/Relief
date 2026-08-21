import {
  TOILET_UNIT_IDENTITY_LABELS,
  TOILET_UNIT_TYPE_LABELS,
  type ToiletUnit,
} from '../types/toiletUnits';

export function toiletUnitTypeLabel(unit: ToiletUnit): string {
  return TOILET_UNIT_TYPE_LABELS[unit.unit_type];
}

export function toiletUnitIdentityLabel(unit: ToiletUnit): string {
  return TOILET_UNIT_IDENTITY_LABELS[unit.identity_status];
}

/**
 * Return only attributes explicitly supported by the child row. In
 * particular, this never treats a missing value as false and never derives a
 * toilet coordinate from the parent station coordinate.
 */
export function toiletUnitAttributeLabels(unit: ToiletUnit): string[] {
  const labels: string[] = [];
  if (unit.is_accessible === true) labels.push('Accessible');
  if (unit.has_baby_changing === true) labels.push('Baby changing');
  if (unit.is_inside_gateline === true) labels.push('Inside gateline');
  if (unit.is_inside_gateline === false) labels.push('Outside gateline');
  if (unit.is_free === true) labels.push('Free');
  if (unit.is_free === false) labels.push('Paid');
  return labels;
}

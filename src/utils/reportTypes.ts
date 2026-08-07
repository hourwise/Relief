// ============================================================
// Project "Relief" — Temporary report presentation
// ============================================================
// Shared so the facility detail banner and the report form cannot
// drift apart. The banner previously rendered the raw enum
// ("busy: No details provided"), which reads like a leaked
// database value rather than a community report.
// ============================================================

import type { TemporaryReport } from '../types/community';

export type ReportType = TemporaryReport['type'];

interface ReportTypeMeta {
  label: string;
  icon: string;
  /** How long the report stays live. Transient states expire soonest. */
  durationHours: number;
}

export const REPORT_TYPE_META: Record<ReportType, ReportTypeMeta> = {
  closed: { label: 'Closed', icon: '🔒', durationHours: 2 },
  out_of_order: { label: 'Out of order', icon: '🔧', durationHours: 4 },
  cleaning: { label: 'Being cleaned', icon: '🧹', durationHours: 1 },
  busy: { label: 'Busy', icon: '🚶', durationHours: 1 },
  no_water: { label: 'No water', icon: '🚱', durationHours: 4 },
  refurbishment: { label: 'Under refurbishment', icon: '🔨', durationHours: 24 },
};

/**
 * Human-readable label for a report type.
 *
 * Falls back to a de-slugged version of an unrecognised value rather than
 * showing the raw enum, so a new report type added server-side still reads
 * acceptably before the client knows about it.
 */
export function reportTypeLabel(type: string): string {
  const known = REPORT_TYPE_META[type as ReportType];
  if (known) return known.label;
  const words = type.replace(/_/g, ' ').trim();
  return words ? words.charAt(0).toUpperCase() + words.slice(1) : 'Issue reported';
}

/** How long a report of this type should stay live, in hours. */
export function reportDurationHours(type: string): number {
  return REPORT_TYPE_META[type as ReportType]?.durationHours ?? 2;
}

import { describeSupabaseError } from '../utils/supabaseErrors';
import { supabase } from './supabase';
import type { ToiletUnit } from '../types/toiletUnits';

export type ToiletUnitQueryResult =
  | { ok: true; data: ToiletUnit[] }
  | { ok: false; error: string };

/**
 * Read published, explicitly adjudicated child units for a published parent.
 *
 * The parent remains usable when this additive relation is empty or
 * unavailable. The query intentionally does not copy parent coordinates into
 * child rows and does not expose source evidence as canonical unit detail.
 */
export async function fetchFacilityToiletUnits(
  facilityId: string,
): Promise<ToiletUnitQueryResult> {
  const { data, error } = await supabase
    .from('toilet_units')
    .select('*')
    .eq('facility_id', facilityId)
    .eq('publication_status', 'published')
    .order('unit_type')
    .order('unit_label', { ascending: true, nullsFirst: false });

  if (error) {
    console.error('fetchFacilityToiletUnits failed:', error);
    return {
      ok: false,
      error: describeSupabaseError(
        error,
        'Toilet unit details could not be loaded.',
      ),
    };
  }

  return { ok: true, data: (data ?? []) as unknown as ToiletUnit[] };
}

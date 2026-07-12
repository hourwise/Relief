// ============================================================
// Project "Relief" — Favourites Service (4.3)
// Favourite locations, chains, and routes
// ============================================================

import { supabase } from './supabase';
import type { Favourite, Facility } from '../types';

/**
 * Fetch all favourites for the current user.
 */
export async function getFavourites(): Promise<Favourite[]> {
  const { data: userData } = await supabase.auth.getUser();
  if (!userData?.user) return [];

  const { data, error } = await supabase
    .from('favourites')
    .select('*')
    .eq('user_id', userData.user.id)
    .order('created_at', { ascending: false });

  if (error) {
    console.error('Error fetching favourites:', error);
    return [];
  }

  return data as unknown as Favourite[];
}

/**
 * Fetch favourite facilities with full details.
 */
export async function getFavouriteFacilities(): Promise<Facility[]> {
  const { data: userData } = await supabase.auth.getUser();
  if (!userData?.user) return [];

  // First get the list of favourite facility IDs
  const { data: favs, error: favError } = await supabase
    .from('favourites')
    .select('facility_id')
    .eq('user_id', userData.user.id);

  if (favError || !favs || favs.length === 0) return [];

  const facilityIds = favs.map((f) => f.facility_id);

  const { data, error } = await supabase
    .from('facilities')
    .select('*')
    .in('id', facilityIds)
    .order('name');

  if (error) {
    console.error('Error fetching favourite facilities:', error);
    return [];
  }

  return data as unknown as Facility[];
}

/**
 * Add a facility to favourites.
 */
export async function addFavourite(
  facilityId: string,
): Promise<{ success: boolean; error?: string }> {
  const { data: userData, error: userError } = await supabase.auth.getUser();
  if (userError || !userData?.user) {
    return { success: false, error: 'You must be signed in' };
  }

  // Check if already favourited
  const { data: existing } = await supabase
    .from('favourites')
    .select('id')
    .eq('user_id', userData.user.id)
    .eq('facility_id', facilityId)
    .single();

  if (existing) {
    return { success: false, error: 'Already in favourites' };
  }

  const { error } = await supabase.from('favourites').insert({
    user_id: userData.user.id,
    facility_id: facilityId,
  });

  if (error) {
    console.error('Error adding favourite:', error);
    return { success: false, error: error.message };
  }

  return { success: true };
}

/**
 * Remove a facility from favourites.
 */
export async function removeFavourite(
  facilityId: string,
): Promise<{ success: boolean; error?: string }> {
  const { data: userData } = await supabase.auth.getUser();
  if (!userData?.user) {
    return { success: false, error: 'You must be signed in' };
  }

  const { error } = await supabase
    .from('favourites')
    .delete()
    .eq('user_id', userData.user.id)
    .eq('facility_id', facilityId);

  if (error) {
    console.error('Error removing favourite:', error);
    return { success: false, error: error.message };
  }

  return { success: true };
}

/**
 * Check if a facility is in the user's favourites.
 */
export async function isFavourite(
  facilityId: string,
): Promise<boolean> {
  const { data: userData } = await supabase.auth.getUser();
  if (!userData?.user) return false;

  const { data } = await supabase
    .from('favourites')
    .select('id')
    .eq('user_id', userData.user.id)
    .eq('facility_id', facilityId)
    .single();

  return !!data;
}

/**
 * Get favourite count for a facility.
 */
export async function getFavouriteCount(
  facilityId: string,
): Promise<number> {
  const { count } = await supabase
    .from('favourites')
    .select('id', { count: 'exact' })
    .eq('facility_id', facilityId);

  return count ?? 0;
}
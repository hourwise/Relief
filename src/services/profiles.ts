// ============================================================
// Project "Relief" — Saved Profiles Service (4.1)
// CRUD for user preference profiles (not health declarations)
// Modes: Accessibility, Family, IBS-friendly, Quiet, etc.
// ============================================================

import { supabase } from './supabase';
import type { SavedProfile, SavedProfileMode, ProfilePreferences } from '../types';

/**
 * Fetch all saved profiles for the current user.
 */
export async function getSavedProfiles(): Promise<SavedProfile[]> {
  const { data: userData } = await supabase.auth.getUser();
  if (!userData?.user) return [];

  const { data, error } = await supabase
    .from('saved_profiles')
    .select('*')
    .eq('user_id', userData.user.id)
    .order('created_at', { ascending: false });

  if (error) {
    console.error('Error fetching saved profiles:', error);
    return [];
  }

  return data as unknown as SavedProfile[];
}

/**
 * Create a new saved profile.
 */
export async function createSavedProfile(
  mode: SavedProfileMode,
  name: string,
  preferences: ProfilePreferences,
): Promise<{ success: boolean; error?: string; profile?: SavedProfile }> {
  const { data: userData, error: userError } = await supabase.auth.getUser();
  if (userError || !userData?.user) {
    return { success: false, error: 'You must be signed in' };
  }

  // Limit: max 10 saved profiles per user
  const { count, error: countError } = await supabase
    .from('saved_profiles')
    .select('id', { count: 'exact' })
    .eq('user_id', userData.user.id);

  if ((count ?? 0) >= 10) {
    return { success: false, error: 'Maximum 10 saved profiles allowed' };
  }

  const { data, error } = await supabase
    .from('saved_profiles')
    .insert({
      user_id: userData.user.id,
      mode,
      name,
      preferences,
    })
    .select()
    .single();

  if (error) {
    console.error('Error creating saved profile:', error);
    return { success: false, error: error.message };
  }

  return { success: true, profile: data as unknown as SavedProfile };
}

/**
 * Update an existing saved profile.
 */
export async function updateSavedProfile(
  profileId: string,
  updates: Partial<{
    name: string;
    mode: SavedProfileMode;
    preferences: ProfilePreferences;
  }>,
): Promise<{ success: boolean; error?: string }> {
  const { data: userData } = await supabase.auth.getUser();
  if (!userData?.user) {
    return { success: false, error: 'You must be signed in' };
  }

  const { error } = await supabase
    .from('saved_profiles')
    .update(updates)
    .eq('id', profileId)
    .eq('user_id', userData.user.id); // Own profiles only

  if (error) {
    console.error('Error updating saved profile:', error);
    return { success: false, error: error.message };
  }

  return { success: true };
}

/**
 * Delete a saved profile.
 */
export async function deleteSavedProfile(
  profileId: string,
): Promise<{ success: boolean; error?: string }> {
  const { data: userData } = await supabase.auth.getUser();
  if (!userData?.user) {
    return { success: false, error: 'You must be signed in' };
  }

  const { error } = await supabase
    .from('saved_profiles')
    .delete()
    .eq('id', profileId)
    .eq('user_id', userData.user.id);

  if (error) {
    console.error('Error deleting saved profile:', error);
    return { success: false, error: error.message };
  }

  return { success: true };
}

/**
 * Get default preferences for a given mode.
 * These are preference presets — NOT health declarations.
 */
export function getDefaultPreferencesForMode(
  mode: SavedProfileMode,
): ProfilePreferences {
  switch (mode) {
    case 'accessibility':
      return {
        requires_accessible: true,
        requires_baby_changing: false,
        requires_family_room: false,
        requires_gender_neutral: false,
        requires_single_occupancy: false,
        requires_quiet: false,
        requires_radar_key: false,
        requires_adult_changing: false,
        min_rating: 2,
      };
    case 'family':
      return {
        requires_accessible: false,
        requires_baby_changing: true,
        requires_family_room: true,
        requires_gender_neutral: false,
        requires_single_occupancy: false,
        requires_quiet: false,
        requires_radar_key: false,
        requires_adult_changing: false,
        min_rating: 2,
      };
    case 'ibs':
      return {
        requires_accessible: false,
        requires_baby_changing: false,
        requires_family_room: false,
        requires_gender_neutral: false,
        requires_single_occupancy: true,
        requires_quiet: true,
        requires_radar_key: false,
        requires_adult_changing: false,
        min_rating: 3,
      };
    case 'pregnancy':
      return {
        requires_accessible: false,
        requires_baby_changing: false,
        requires_family_room: false,
        requires_gender_neutral: false,
        requires_single_occupancy: true,
        requires_quiet: false,
        requires_radar_key: false,
        requires_adult_changing: false,
        min_rating: 3,
      };
    case 'neurodivergent':
      return {
        requires_accessible: false,
        requires_baby_changing: false,
        requires_family_room: false,
        requires_gender_neutral: false,
        requires_single_occupancy: true,
        requires_quiet: true,
        requires_radar_key: false,
        requires_adult_changing: false,
        min_rating: 2,
      };
    case 'elderly':
      return {
        requires_accessible: true,
        requires_baby_changing: false,
        requires_family_room: false,
        requires_gender_neutral: false,
        requires_single_occupancy: false,
        requires_quiet: false,
        requires_radar_key: false,
        requires_adult_changing: false,
        min_rating: 2,
      };
    default:
      return {
        requires_accessible: false,
        requires_baby_changing: false,
        requires_family_room: false,
        requires_gender_neutral: false,
        requires_single_occupancy: false,
        requires_quiet: false,
        requires_radar_key: false,
        requires_adult_changing: false,
        min_rating: 0,
      };
  }
}

/**
 * Get a friendly display name for a saved profile mode.
 */
export function getModeDisplayName(mode: SavedProfileMode): string {
  const names: Record<SavedProfileMode, string> = {
    accessibility: 'Accessibility Mode',
    family: 'Family Mode',
    ibs: 'IBS-friendly Mode',
    pregnancy: 'Pregnancy Mode',
    neurodivergent: 'Neurodivergent Mode',
    elderly: 'Elderly Mode',
  };
  return names[mode] || mode;
}

/**
 * Get an emoji icon for a saved profile mode.
 */
export function getModeIcon(mode: SavedProfileMode): string {
  const icons: Record<SavedProfileMode, string> = {
    accessibility: '♿',
    family: '👨‍👩‍👧‍👧',
    ibs: '🫃',
    pregnancy: '🤰',
    neurodivergent: '🧠',
    elderly: '👴',
  };
  return icons[mode] || '📋';
}
import type { User } from '@supabase/supabase-js';
import { supabase } from './supabase';

export interface AccountDetails {
  user: User;
  displayName: string | null;
}

function metadataDisplayName(user: User): string | null {
  const metadataName = user.user_metadata?.full_name ?? user.user_metadata?.name;
  return typeof metadataName === 'string' && metadataName.trim()
    ? metadataName.trim()
    : null;
}

export async function getAccountDetails(): Promise<{
  account: AccountDetails | null;
  error?: string;
}> {
  const { data: userData, error: userError } = await supabase.auth.getUser();
  if (userError || !userData.user) {
    return { account: null, error: 'Your account details could not be loaded.' };
  }

  const { data: profile, error: profileError } = await supabase
    .from('user_profiles')
    .select('display_name')
    .eq('id', userData.user.id)
    .maybeSingle();

  if (profileError) {
    return { account: null, error: 'Your profile details could not be loaded.' };
  }

  return {
    account: {
      user: userData.user,
      displayName: profile?.display_name?.trim() || metadataDisplayName(userData.user),
    },
  };
}

/**
 * Update the two existing representations of a user's name together.
 *
 * Auth metadata is updated first because it is the identity returned by the
 * session. If the public profile row cannot be updated, the metadata write is
 * rolled back and the caller receives a failure rather than a false success.
 */
export async function updateDisplayName(displayName: string): Promise<{
  success: boolean;
  account?: AccountDetails;
  error?: string;
}> {
  const nextName = displayName.trim();
  if (!nextName) return { success: false, error: 'Enter a display name.' };
  if (nextName.length > 80) {
    return { success: false, error: 'Display names must be 80 characters or fewer.' };
  }

  const { data: userData, error: userError } = await supabase.auth.getUser();
  const user = userData.user;
  if (userError || !user) {
    return { success: false, error: 'You need to be signed in to edit your name.' };
  }

  const previousMetadata = { ...(user.user_metadata ?? {}) };
  const previousName = metadataDisplayName(user);
  const { data: authData, error: authError } = await supabase.auth.updateUser({
    data: { ...previousMetadata, full_name: nextName },
  });

  if (authError || !authData.user) {
    return { success: false, error: 'Your display name could not be updated. Please try again.' };
  }

  const { data: profile, error: profileError } = await supabase
    .from('user_profiles')
    .update({ display_name: nextName })
    .eq('id', user.id)
    .select('display_name')
    .maybeSingle();

  if (profileError || !profile) {
    await supabase.auth.updateUser({
      data: { ...previousMetadata, full_name: previousName },
    });
    return {
      success: false,
      error: 'Your display name could not be saved. Please try again.',
    };
  }

  return {
    success: true,
    account: { user: authData.user, displayName: profile.display_name },
  };
}

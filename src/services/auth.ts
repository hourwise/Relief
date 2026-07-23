// ============================================================
// Project "Relief" — Authentication Service
// ============================================================

import { supabase } from './supabase';
import * as WebBrowser from 'expo-web-browser';
import { Session, User } from '@supabase/supabase-js';

// Required for OAuth flow
WebBrowser.maybeCompleteAuthSession();

// The redirect URI must match what's configured in Supabase dashboard
// For Expo, this is typically: relief://auth/callback
const redirectUri = __DEV__
  ? 'relief://auth/callback'
  : 'relief://auth/callback';

// ============================================================
// Email / Password
// ============================================================

export async function signUpWithEmail(email: string, password: string) {
  const { data, error } = await supabase.auth.signUp({
    email,
    password,
    options: {
      emailRedirectTo: redirectUri,
    },
  });
  return { data, error };
}

export async function signInWithEmail(email: string, password: string) {
  const { data, error } = await supabase.auth.signInWithPassword({
    email,
    password,
  });
  return { data, error };
}

export async function signOut() {
  const { error } = await supabase.auth.signOut();
  return { error };
}

// ============================================================
// OAuth (Google / Apple)
// ============================================================

async function signInWithOAuthProvider(provider: 'google' | 'apple') {
  const { data, error } = await supabase.auth.signInWithOAuth({
    provider,
    options: {
      redirectTo: redirectUri,
      skipBrowserRedirect: true,
    },
  });

  if (error || !data.url) {
    return { data: null, error };
  }

  // Open the OAuth URL in a browser
  const result = await WebBrowser.openAuthSessionAsync(
    data.url,
    redirectUri,
  );

  if (result.type !== 'success') {
    return { data: null, error: new Error('OAuth cancelled') };
  }

  // Parse the callback URL to extract the code or tokens
  const { url } = result;
  const params = new URLSearchParams(url.split('#')[0].split('?')[1] || '');
  const code = params.get('code');

  if (code) {
    // Exchange the code for a session
    const { data: sessionData, error: sessionError } =
      await supabase.auth.exchangeCodeForSession(code);
    return { data: sessionData, error: sessionError };
  }

  // Fallback: try to get existing session (tokens may be in URL hash)
  await supabase.auth.startAutoRefresh();
  const { data: currentSession } = await supabase.auth.getSession();
  if (currentSession.session) {
    return { data: { session: currentSession.session, user: currentSession.session.user }, error: null };
  }

  return { data: null, error: new Error('Failed to complete OAuth') };
}

export async function signInWithGoogle() {
  return signInWithOAuthProvider('google');
}

export async function signInWithApple() {
  return signInWithOAuthProvider('apple');
}

// ============================================================
// Session Management
// ============================================================

export async function getCurrentSession(): Promise<Session | null> {
  const { data } = await supabase.auth.getSession();
  return data.session;
}

export async function getCurrentUser(): Promise<User | null> {
  const { data } = await supabase.auth.getUser();
  return data.user;
}

export function onAuthStateChange(callback: (session: Session | null) => void) {
  const { data: subscription } = supabase.auth.onAuthStateChange(
    (_event, session) => {
      callback(session);
    },
  );
  return subscription;
}

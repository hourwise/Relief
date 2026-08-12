// ============================================================
// Project "Relief" — Supabase Client
// ============================================================

import 'react-native-url-polyfill/auto';
import { AppState } from 'react-native';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { createClient } from '@supabase/supabase-js';
import { SUPABASE_URL, SUPABASE_ANON_KEY } from '../utils/env';
import { SUPABASE_AUTH_OPTIONS } from './supabaseAuthConfig';
export { SUPABASE_AUTH_OPTIONS } from './supabaseAuthConfig';

export const supabase = createClient(SUPABASE_URL, SUPABASE_ANON_KEY, {
  auth: {
    storage: AsyncStorage,
    ...SUPABASE_AUTH_OPTIONS,
  },
});

// Handle AppState token refresh
// https://supabase.com/docs/guides/auth/quickstarts/react-native
AppState.addEventListener('change', (state) => {
  if (state === 'active') {
    supabase.auth.startAutoRefresh();
  } else {
    supabase.auth.stopAutoRefresh();
  }
});

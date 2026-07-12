// ============================================================
// Project "Relief" — Environment Configuration
// ============================================================

// These are set via environment variables at build time
// In development, they come from .env file loaded by Expo

// Supabase
export const SUPABASE_URL = process.env.EXPO_PUBLIC_SUPABASE_URL || '';
export const SUPABASE_ANON_KEY = process.env.EXPO_PUBLIC_SUPABASE_ANON_KEY || '';

// Mapbox
export const MAPBOX_ACCESS_TOKEN =
  process.env.EXPO_PUBLIC_MAPBOX_ACCESS_TOKEN || '';

// Deep linking / scheme
export const APP_SCHEME = 'relief';

// API timeouts
export const API_TIMEOUT = 10000;

// Feature flags
export const FEATURES = {
  COMMUNITY: true,
  ADVANCED_FILTERS: false,
  PREMIUM: false,
  AI: false,
  EUROPE: false,
};
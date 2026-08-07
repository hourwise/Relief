// ============================================================
// Project "Relief" — Environment Configuration
// ============================================================

// These are set via environment variables at build time
// In development, they come from .env file loaded by Expo

// Supabase
export const SUPABASE_URL = process.env.EXPO_PUBLIC_SUPABASE_URL || '';
export const SUPABASE_ANON_KEY = process.env.EXPO_PUBLIC_SUPABASE_ANON_KEY || '';

// Google Maps
export const GOOGLE_MAPS_API_KEY =
  process.env.EXPO_PUBLIC_GOOGLE_MAPS_API_KEY || '';

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

/**
 * Which sign-in methods the app may offer.
 *
 * These mirror what the live Supabase project actually has enabled — checked
 * via GET /auth/v1/settings on 2026-08-07, which reported `email: true` and
 * `google: false` (along with every other provider disabled).
 *
 * GOOGLE is false because the provider is not configured. Offering the button
 * anyway produced a guaranteed failure: signInWithOAuth returns "Unsupported
 * provider: provider is not enabled", which the user saw as a broken app rather
 * than an unfinished one. A sign-in method must not advertise itself until it
 * works.
 *
 * Turning GOOGLE on requires ALL of the following first — see
 * docs/ANDROID_SMOKE_TEST.md for the checklist:
 *   1. Google Cloud OAuth client IDs (Web + Android for com.relief.app).
 *   2. The signing certificate SHA-1 for each build that must work.
 *   3. Google enabled in Supabase Auth with that client ID and secret.
 *   4. relief://auth/callback added to Supabase's redirect allow-list.
 *   5. A deep-link handler in the app to complete the callback.
 *
 * APPLE additionally needs an Apple developer configuration and is iOS-only;
 * this build is Android.
 */
export const AUTH_PROVIDERS = {
  EMAIL: true,
  GOOGLE: false,
  APPLE: false,
};

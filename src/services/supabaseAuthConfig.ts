// Native Supabase session behaviour kept in a pure module so it can be tested
// without loading React Native inside the Node unit-test process.
export const SUPABASE_AUTH_OPTIONS = {
  autoRefreshToken: true,
  persistSession: true,
  detectSessionInUrl: false,
} as const;

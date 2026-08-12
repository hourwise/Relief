// ============================================================
// Relief - safe Supabase error descriptions
// ============================================================
// Raw PostgREST/Auth errors can contain backend hostnames, SQL details, or
// policy names. Keep those in logs for developer diagnostics, but never pass
// them through to a user-facing screen.

export interface SupabaseLikeError {
  code?: string;
  message?: string;
  status?: number;
}

export function describeSupabaseError(
  error: SupabaseLikeError | null | undefined,
  fallback: string,
): string {
  if (!error) return fallback;

  if (error.code === '42501' || error.status === 401 || error.status === 403) {
    return 'This action is not available for your account right now.';
  }

  if (error.status === 429) {
    return 'Too many attempts. Please wait a few minutes and try again.';
  }

  if (error.code === '42703' || error.code === '42883') {
    return 'The facility service is out of date. Please update the app.';
  }

  const raw = error.message ?? '';
  if (/network|fetch failed|unknownhost|unable to resolve host|timeout|timed out|econn/i.test(raw)) {
    return 'No connection. Check your internet and try again.';
  }

  return fallback;
}

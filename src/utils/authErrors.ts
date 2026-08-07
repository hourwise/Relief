// ============================================================
// Project "Relief" — Authentication error messages
// ============================================================
// Supabase error text is written for developers. Surfacing it
// raw put strings like "AuthApiError: Invalid login credentials"
// and "java.net.UnknownHostException: Unable to resolve host
// <project>.supabase.co" in front of users — unhelpful, and the
// second leaks the backend hostname.
//
// Every auth failure the user can see is mapped here, so the two
// auth screens cannot drift and no raw message escapes.
// ============================================================

export type AuthAction = 'sign_in' | 'sign_up';

interface AuthErrorLike {
  message?: string;
  code?: string;
  status?: number;
}

const FALLBACK: Record<AuthAction, string> = {
  sign_in: 'Could not sign you in. Please try again.',
  sign_up: 'Could not create your account. Please try again.',
};

/**
 * Turn a Supabase auth error into something worth reading.
 *
 * Matching is on `code` first (stable) and falls back to message text, because
 * older supabase-js versions and some gateway errors carry no code.
 */
export function describeAuthError(
  error: AuthErrorLike | null | undefined,
  action: AuthAction,
): string {
  if (!error) return FALLBACK[action];

  const code = (error.code ?? '').toLowerCase();
  const raw = (error.message ?? '').toLowerCase();
  const has = (...needles: string[]) => needles.some((n) => raw.includes(n));

  // --- Network / reachability. Checked first: offline produces a variety of
  // messages that would otherwise fall through to a misleading credential hint.
  if (
    has(
      'network request failed',
      'fetch failed',
      'unknownhost',
      'unable to resolve host',
      'timeout',
      'timed out',
      'econnrefused',
      'econnreset',
      'failed to fetch',
    )
  ) {
    return 'No connection. Check your internet and try again.';
  }

  // --- Rate limiting
  if (code === 'over_email_send_rate_limit' || error.status === 429 || has('rate limit', 'too many requests')) {
    return 'Too many attempts. Please wait a few minutes and try again.';
  }

  // --- Credentials
  if (code === 'invalid_credentials' || has('invalid login credentials', 'invalid grant')) {
    // Deliberately does not say which of the two was wrong — telling a stranger
    // that an email exists is an account-enumeration leak.
    return 'That email and password do not match. Please check both and try again.';
  }

  // --- Unconfirmed email
  if (code === 'email_not_confirmed' || has('email not confirmed', 'not confirmed')) {
    return 'Please confirm your email address first. Check your inbox for the link we sent.';
  }

  // --- Duplicate account
  if (code === 'user_already_exists' || has('already registered', 'already been registered', 'user already exists')) {
    return 'An account already exists for that email. Try signing in instead.';
  }

  // --- Password rules
  if (code === 'weak_password' || has('password should be', 'password is too short', 'weak password')) {
    return 'Please choose a longer password — at least 6 characters.';
  }

  // --- Email validity / disallowed address
  if (code === 'email_address_invalid' || has('invalid email', 'unable to validate email', 'email address is invalid')) {
    return 'That email address does not look valid. Please check it and try again.';
  }
  if (code === 'email_address_not_authorized' || has('not authorized')) {
    return 'That email address cannot be used to sign up. Please try another.';
  }

  // --- Signups disabled server-side
  if (code === 'signup_disabled' || has('signups not allowed', 'signup is disabled')) {
    return 'New accounts are not being accepted at the moment.';
  }

  // --- Provider not enabled. Should be unreachable while the UI hides
  // unconfigured providers, but it must never surface as a raw string.
  if (code === 'provider_disabled' || has('unsupported provider', 'provider is not enabled')) {
    return 'That sign-in method is not available yet.';
  }

  // --- Server-side failure
  if ((error.status ?? 0) >= 500 || has('internal server error', 'service unavailable', 'database error')) {
    return 'The sign-in service is having trouble. Please try again shortly.';
  }

  return FALLBACK[action];
}

/**
 * Basic email shape check, so an obvious typo is caught before a round trip.
 *
 * Deliberately permissive — the server is the authority on deliverability. This
 * only rejects input that cannot be an address at all.
 */
export function isPlausibleEmail(value: string): boolean {
  const trimmed = value.trim();
  if (trimmed.length < 3 || trimmed.length > 254) return false;
  if (/\s/.test(trimmed)) return false;
  return /^[^@]+@[^@.]+(\.[^@.]+)+$/.test(trimmed);
}

/** Minimum password length, matching Supabase's default policy. */
export const MIN_PASSWORD_LENGTH = 6;

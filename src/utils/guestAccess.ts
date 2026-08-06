// ============================================================
// Project "Relief" — Guest access policy
// ============================================================
// Basic discovery must work without an account. This module is
// the single place that decides which actions need a session, so
// the rule is testable and cannot drift screen by screen.
//
// Policy source: docs/ACCESSIBILITY_AND_UX.md — the urgent-use
// journey must be fast and must not require registration.
// ============================================================

/**
 * Every user-initiated action whose availability depends on authentication.
 */
export type AppAction =
  // --- Discovery: always available, signed in or not ---
  | 'open_app'
  | 'view_find'
  | 'grant_location_permission'
  | 'view_map'
  | 'view_list'
  | 'search_town_or_postcode'
  | 'apply_filters'
  | 'need_one_now'
  | 'view_facility_detail'
  | 'open_external_directions'
  // --- Account-dependent ---
  | 'save_favourite'
  | 'view_favourites'
  | 'submit_facility'
  | 'correct_facility_info'
  | 'report_problem'
  | 'account_settings';

const ACTIONS_REQUIRING_AUTH: ReadonlySet<AppAction> = new Set<AppAction>([
  'save_favourite',
  'view_favourites',
  'submit_facility',
  'correct_facility_info',
  'report_problem',
  'account_settings',
]);

/**
 * Whether an action needs a signed-in user.
 *
 * Anything not listed as account-dependent is available to guests. Defaulting
 * to "open" is deliberate: a new discovery action should not silently acquire
 * a sign-in wall.
 */
export function requiresAuthentication(action: AppAction): boolean {
  return ACTIONS_REQUIRING_AUTH.has(action);
}

export type GuestDecision = 'allow' | 'prompt_sign_in';

/**
 * The navigation decision for an action given the current session state.
 */
export function resolveAction(
  action: AppAction,
  isAuthenticated: boolean,
): GuestDecision {
  if (!requiresAuthentication(action)) return 'allow';
  return isAuthenticated ? 'allow' : 'prompt_sign_in';
}

/**
 * Human-readable reason shown on the sign-in prompt, so a guest understands
 * why they are being asked rather than being bounced without explanation.
 */
export function signInReason(action: AppAction): string {
  switch (action) {
    case 'save_favourite':
      return 'Sign in to save favourites to your account.';
    case 'view_favourites':
      return 'Sign in to see the facilities you have saved.';
    case 'submit_facility':
      return 'Sign in to add a facility.';
    case 'correct_facility_info':
      return 'Sign in to suggest a correction.';
    case 'report_problem':
      return 'Sign in to report a problem with this facility.';
    case 'account_settings':
      return 'Sign in to manage your account.';
    default:
      return 'Sign in to continue.';
  }
}

/**
 * The ordered guest journey that must work end to end without a session.
 * Exported so the test suite asserts the whole path, not individual actions.
 */
export const GUEST_DISCOVERY_JOURNEY: readonly AppAction[] = [
  'open_app',
  'view_find',
  'grant_location_permission',
  'view_map',
  'search_town_or_postcode',
  'view_list',
  'need_one_now',
  'view_facility_detail',
  'open_external_directions',
] as const;

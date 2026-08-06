// ============================================================
// Relief — guest navigation decisions
// ============================================================
// The core discovery journey must work with no account. These
// tests pin that policy so a future change cannot quietly put a
// sign-in wall back in front of the urgent journey.
// ============================================================

import {
  GUEST_DISCOVERY_JOURNEY,
  requiresAuthentication,
  resolveAction,
  signInReason,
  type AppAction,
} from '../src/utils/guestAccess';
import { assertEqual, assertTrue, section } from './helpers/harness';

const GUEST = false;
const SIGNED_IN = true;

section('the whole discovery journey is open to guests');

// Every step the brief requires of a signed-out user, in order.
for (const action of GUEST_DISCOVERY_JOURNEY) {
  assertEqual(`guest may ${action}`, resolveAction(action, GUEST), 'allow');
  assertEqual(`${action} needs no account`, requiresAuthentication(action), false);
}

assertEqual(
  'the journey covers all nine required steps',
  GUEST_DISCOVERY_JOURNEY.length,
  9,
);

// Explicitly: the two most urgent capabilities.
assertEqual('Need One Now works signed out', resolveAction('need_one_now', GUEST), 'allow');
assertEqual(
  'external directions work signed out',
  resolveAction('open_external_directions', GUEST),
  'allow',
);
assertEqual('filters work signed out', resolveAction('apply_filters', GUEST), 'allow');
assertEqual('the list view works signed out', resolveAction('view_list', GUEST), 'allow');

section('account-dependent actions prompt sign-in for guests');

const ACCOUNT_ACTIONS: AppAction[] = [
  'save_favourite',
  'view_favourites',
  'submit_facility',
  'correct_facility_info',
  'report_problem',
  'account_settings',
];

for (const action of ACCOUNT_ACTIONS) {
  assertEqual(`${action} requires an account`, requiresAuthentication(action), true);
  assertEqual(`guest attempting ${action} is prompted`, resolveAction(action, GUEST), 'prompt_sign_in');
  assertEqual(`signed-in user may ${action}`, resolveAction(action, SIGNED_IN), 'allow');
}

section('signing in never removes access');

const ALL_ACTIONS: AppAction[] = [...GUEST_DISCOVERY_JOURNEY, ...ACCOUNT_ACTIONS];
for (const action of ALL_ACTIONS) {
  assertEqual(
    `${action} is allowed once signed in`,
    resolveAction(action, SIGNED_IN),
    'allow',
  );
}

section('prompts explain themselves');

for (const action of ACCOUNT_ACTIONS) {
  const reason = signInReason(action);
  assertTrue(`${action} has a non-empty reason`, reason.length > 0);
  // A bare "Sign in to continue." tells the user nothing about what they did.
  assertTrue(`${action} reason is specific`, reason !== 'Sign in to continue.');
}

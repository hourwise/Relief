// ============================================================
// Relief — authentication error messages
// ============================================================
// Both auth screens used to Alert Supabase's raw error.message.
// That put developer text in front of users, and on network
// failure it leaked the backend hostname
// ("...Unable to resolve host <project>.supabase.co").
//
// These tests pin the mapping and, most importantly, assert that
// nothing raw can escape.
// ============================================================

import {
  describeAuthError,
  isPlausibleEmail,
  MIN_PASSWORD_LENGTH,
} from '../src/utils/authErrors';
import { assertEqual, assertTrue, section } from './helpers/harness';

section('credentials');

assertEqual(
  'invalid credentials by code',
  describeAuthError({ code: 'invalid_credentials' }, 'sign_in'),
  'That email and password do not match. Please check both and try again.',
);
assertEqual(
  'invalid credentials by message',
  describeAuthError({ message: 'Invalid login credentials' }, 'sign_in'),
  'That email and password do not match. Please check both and try again.',
);

// The message must not reveal whether the email exists — that is an
// account-enumeration leak.
const wrongPassword = describeAuthError({ code: 'invalid_credentials' }, 'sign_in');
assertTrue('does not confirm the email exists', !/email (?:is |was )?(?:correct|registered|found)/i.test(wrongPassword));
assertTrue('does not single out the password', !/password is (?:wrong|incorrect)/i.test(wrongPassword));

section('sign-up failures');

assertEqual(
  'duplicate email by code',
  describeAuthError({ code: 'user_already_exists' }, 'sign_up'),
  'An account already exists for that email. Try signing in instead.',
);
assertEqual(
  'duplicate email by message',
  describeAuthError({ message: 'User already registered' }, 'sign_up'),
  'An account already exists for that email. Try signing in instead.',
);
assertEqual(
  'weak password',
  describeAuthError({ message: 'Password should be at least 6 characters' }, 'sign_up'),
  'Please choose a longer password — at least 6 characters.',
);
assertEqual(
  'invalid email address',
  describeAuthError({ code: 'email_address_invalid' }, 'sign_up'),
  'That email address does not look valid. Please check it and try again.',
);
assertEqual(
  'signups disabled server-side',
  describeAuthError({ code: 'signup_disabled' }, 'sign_up'),
  'New accounts are not being accepted at the moment.',
);

section('unconfirmed email');

// The live project has mailer_autoconfirm = false, so this is the state a real
// new user lands in before clicking the link.
assertEqual(
  'email not confirmed',
  describeAuthError({ code: 'email_not_confirmed' }, 'sign_in'),
  'Please confirm your email address first. Check your inbox for the link we sent.',
);

section('network failures must not leak the backend');

const networkMessages = [
  'Network request failed',
  'TypeError: Failed to fetch',
  'fetch failed: java.net.UnknownHostException: Unable to resolve host "abcdefg.supabase.co": No address associated with hostname',
  'connect ECONNREFUSED 10.0.0.1:443',
  'The request timed out',
];

for (const message of networkMessages) {
  const shown = describeAuthError({ message }, 'sign_in');
  assertEqual(`network: ${message.slice(0, 28)}…`, shown, 'No connection. Check your internet and try again.');
  assertTrue('does not leak a hostname', !/supabase\.co/i.test(shown));
  assertTrue('does not leak an exception class', !/exception|typeerror/i.test(shown));
}

section('rate limiting and server errors');

assertEqual(
  'HTTP 429 is rate limiting',
  describeAuthError({ status: 429, message: 'Too Many Requests' }, 'sign_up'),
  'Too many attempts. Please wait a few minutes and try again.',
);
assertEqual(
  'HTTP 500 is a service problem',
  describeAuthError({ status: 500, message: 'Internal Server Error' }, 'sign_in'),
  'The sign-in service is having trouble. Please try again shortly.',
);

section('disabled provider never surfaces raw');

// Reachable only if a provider button is shown while unconfigured. The UI now
// hides those, but the mapping is the backstop.
assertEqual(
  'provider disabled',
  describeAuthError({ message: 'Unsupported provider: provider is not enabled' }, 'sign_in'),
  'That sign-in method is not available yet.',
);

section('nothing raw escapes');

// The property that actually matters: whatever Supabase says, the user sees one
// of our sentences.
const RAW_LEAKS = [
  'AuthApiError: something went bang',
  'PGRST301 JWT expired',
  'duplicate key value violates unique constraint "users_email_key"',
  'relation "auth.users" does not exist',
  '',
  'undefined',
];

const ALLOWED = new Set([
  'That email and password do not match. Please check both and try again.',
  'Please confirm your email address first. Check your inbox for the link we sent.',
  'An account already exists for that email. Try signing in instead.',
  'Please choose a longer password — at least 6 characters.',
  'That email address does not look valid. Please check it and try again.',
  'That email address cannot be used to sign up. Please try another.',
  'New accounts are not being accepted at the moment.',
  'That sign-in method is not available yet.',
  'No connection. Check your internet and try again.',
  'Too many attempts. Please wait a few minutes and try again.',
  'The sign-in service is having trouble. Please try again shortly.',
  'Could not sign you in. Please try again.',
  'Could not create your account. Please try again.',
]);

for (const message of RAW_LEAKS) {
  for (const action of ['sign_in', 'sign_up'] as const) {
    const shown = describeAuthError({ message }, action);
    assertTrue(`"${message.slice(0, 26)}…" (${action}) maps to a known sentence`, ALLOWED.has(shown));
    assertTrue('never returns the raw text', message.length === 0 || shown !== message);
  }
}

assertEqual('null error still yields a sentence', describeAuthError(null, 'sign_in'), 'Could not sign you in. Please try again.');
assertEqual('undefined error still yields a sentence', describeAuthError(undefined, 'sign_up'), 'Could not create your account. Please try again.');

section('email shape check');

for (const good of ['a@b.co', 'someone@example.com', 'first.last+tag@sub.example.co.uk']) {
  assertTrue(`accepts ${good}`, isPlausibleEmail(good));
}
for (const bad of ['', 'nope', 'no@domain', 'two@@at.com', 'has space@x.com', '@x.com', 'x@.com', 'x@com.']) {
  assertEqual(`rejects "${bad}"`, isPlausibleEmail(bad), false);
}
assertTrue('trims surrounding whitespace', isPlausibleEmail('  ok@example.com  '));

assertEqual('minimum password length matches Supabase default', MIN_PASSWORD_LENGTH, 6);

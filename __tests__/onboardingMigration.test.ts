// ============================================================
// Relief — guest → user onboarding migration
// ============================================================
// A guest who completes onboarding and then signs in must not be
// asked again. That regressed on a real device because the
// migration was fired from the auth listener without being
// awaited, so the onboarding check ran first and saw nothing.
//
// AsyncStorage is a native module, so it is replaced here with an
// in-memory store injected via module mocking. These tests cover
// the ordering contract the navigator depends on.
// ============================================================

import { assertEqual, assertTrue, section } from './helpers/harness';

// ── In-memory AsyncStorage stand-in ───────────────────────────
const store = new Map<string, string>();
let getItemCalls = 0;

const fakeAsyncStorage = {
  async getItem(key: string) {
    getItemCalls++;
    return store.get(key) ?? null;
  },
  async setItem(key: string, value: string) {
    store.set(key, value);
  },
  async removeItem(key: string) {
    store.delete(key);
  },
};

// Register the mock before the module under test resolves its import.
const Module = require('node:module');
const originalResolve = Module._resolveFilename;
const originalLoad = Module._load;
Module._load = function patchedLoad(request: string, parent: unknown, isMain: boolean) {
  if (request === '@react-native-async-storage/async-storage') {
    return { default: fakeAsyncStorage, __esModule: true };
  }
  return originalLoad.apply(this, [request, parent, isMain]);
};

// eslint-disable-next-line @typescript-eslint/no-var-requires
const onboarding = require('../src/utils/onboarding');
Module._load = originalLoad;
Module._resolveFilename = originalResolve;

const {
  GUEST_ONBOARDING_KEY,
  hasCompletedOnboarding,
  completeOnboarding,
  migrateGuestOnboarding,
} = onboarding as typeof import('../src/utils/onboarding');

const USER_ID = 'user-abc-123';

function reset() {
  store.clear();
  getItemCalls = 0;
}

async function main() {
  section('guest scope');

  reset();
  assertEqual(
    'a fresh guest has not completed onboarding',
    await hasCompletedOnboarding(GUEST_ONBOARDING_KEY),
    false,
  );

  await completeOnboarding(GUEST_ONBOARDING_KEY);
  assertEqual(
    'completing as a guest is recorded',
    await hasCompletedOnboarding(GUEST_ONBOARDING_KEY),
    true,
  );
  assertEqual(
    'the guest record does not leak into a user scope',
    await hasCompletedOnboarding(USER_ID),
    false,
  );

  section('migration on sign-in');

  // The regression: guest completed, user scope empty. Migrating must make the
  // user scope report completed, so onboarding is not shown a second time.
  reset();
  await completeOnboarding(GUEST_ONBOARDING_KEY);
  await migrateGuestOnboarding(USER_ID);
  assertEqual(
    'a guest who signs in is not asked to onboard again',
    await hasCompletedOnboarding(USER_ID),
    true,
  );
  assertEqual(
    'the guest record is kept, so signing out does not re-trigger onboarding',
    await hasCompletedOnboarding(GUEST_ONBOARDING_KEY),
    true,
  );

  section('migration does not invent completion');

  reset();
  await migrateGuestOnboarding(USER_ID);
  assertEqual(
    'a user with no guest history still onboards',
    await hasCompletedOnboarding(USER_ID),
    false,
  );

  section('migration is safe to repeat and never downgrades');

  reset();
  await completeOnboarding(USER_ID);
  // No guest record at all; an existing user record must survive.
  await migrateGuestOnboarding(USER_ID);
  assertEqual(
    'an already-onboarded user is left alone',
    await hasCompletedOnboarding(USER_ID),
    true,
  );

  reset();
  await completeOnboarding(GUEST_ONBOARDING_KEY);
  await migrateGuestOnboarding(USER_ID);
  await migrateGuestOnboarding(USER_ID);
  assertEqual(
    'migrating twice is idempotent',
    await hasCompletedOnboarding(USER_ID),
    true,
  );

  section('guards');

  reset();
  await completeOnboarding(GUEST_ONBOARDING_KEY);
  await migrateGuestOnboarding('');
  assertTrue('an empty user id is ignored', store.size === 1);

  await migrateGuestOnboarding(GUEST_ONBOARDING_KEY);
  assertTrue(
    'migrating the guest scope onto itself is a no-op',
    store.size === 1,
  );

  section('ordering contract');

  // What the navigator relies on: awaiting the migration before checking must
  // yield `true`. Checking without awaiting it is what produced the bug.
  reset();
  await completeOnboarding(GUEST_ONBOARDING_KEY);
  const migration = migrateGuestOnboarding(USER_ID);
  const checkedTooEarly = await hasCompletedOnboarding(USER_ID);
  await migration;
  const checkedAfterAwait = await hasCompletedOnboarding(USER_ID);

  assertEqual(
    'checking before the migration resolves can miss it (the original bug)',
    checkedTooEarly,
    false,
  );
  assertEqual(
    'checking after awaiting the migration always sees it',
    checkedAfterAwait,
    true,
  );
  assertTrue('storage was actually exercised', getItemCalls > 0);
}

main().catch((error) => {
  console.error('  FAIL  unexpected error:', error);
  process.exitCode = 1;
});

// ============================================================
// Relief — minimal test harness
// ============================================================
// Deliberately dependency-free. These are pure-function tests
// that must run without a React Native runtime, a simulator or a
// database, so `npm test` stays fast enough to run on every
// change. Anything needing a real device belongs in the Android
// smoke test instead.
// ============================================================

let passed = 0;
const failures: string[] = [];

function record(ok: boolean, label: string, detail?: string) {
  if (ok) {
    passed++;
    console.log(`  PASS  ${label}`);
  } else {
    failures.push(`${label}${detail ? ` — ${detail}` : ''}`);
    console.error(`  FAIL  ${label}${detail ? ` — ${detail}` : ''}`);
  }
}

/** Strict equality for primitives. */
export function assertEqual<T>(label: string, actual: T, expected: T) {
  record(
    actual === expected,
    label,
    actual === expected ? undefined : `expected ${String(expected)}, got ${String(actual)}`,
  );
}

/** Structural equality via JSON, for objects and arrays. */
export function assertDeepEqual(label: string, actual: unknown, expected: unknown) {
  const a = JSON.stringify(actual);
  const b = JSON.stringify(expected);
  record(a === b, label, a === b ? undefined : `expected ${b}, got ${a}`);
}

export function assertTrue(label: string, actual: boolean) {
  record(actual === true, label, actual === true ? undefined : 'expected true');
}

export function assertNull(label: string, actual: unknown) {
  record(actual === null, label, actual === null ? undefined : `expected null, got ${JSON.stringify(actual)}`);
}

/** Numeric comparison with a tolerance, for distance maths. */
export function assertClose(
  label: string,
  actual: number,
  expected: number,
  tolerance: number,
) {
  const ok = Math.abs(actual - expected) <= tolerance;
  record(ok, label, ok ? undefined : `expected ${expected} ±${tolerance}, got ${actual}`);
}

export function section(title: string) {
  console.log(`\n=== ${title} ===`);
}

/**
 * Print the summary and set a failing exit code. Called automatically on exit
 * so a test file cannot pass by forgetting to report.
 */
process.on('exit', (code: number) => {
  console.log(`\n${passed} passed, ${failures.length} failed`);
  if (failures.length > 0 && code === 0) process.exitCode = 1;
});

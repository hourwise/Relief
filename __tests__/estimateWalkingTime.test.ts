// ============================================================
// Relief — estimateWalkingTime Unit Tests
// ============================================================
// Run: npx ts-node --skip-project __tests__/estimateWalkingTime.test.ts
// Or simply review for correctness — no framework required.
// ============================================================

import { estimateWalkingTime } from '../src/services/facilities';

let passed = 0;
let failed = 0;

function assert(label: string, actual: unknown, expected: unknown) {
  if (actual === expected) {
    console.log(`  PASS: ${label}`);
    passed++;
  } else {
    console.error(`  FAIL: ${label} — expected ${expected}, got ${actual}`);
    failed++;
  }
}

// ─── Single-arg (PostGIS metres path) ─────────────────────

console.log('\n=== Single-arg (metres) path ===');

// 1 km = 12 minutes at 5 km/h
assert('1000m → 12 min', estimateWalkingTime(1000), 12);

// 500m = 6 minutes
assert('500m → 6 min', estimateWalkingTime(500), 6);

// 2500m = 30 minutes
assert('2500m → 30 min', estimateWalkingTime(2500), 30);

// 100m = 1.2 min → rounds to 1, min is 1
assert('100m → 1 min (min clamp)', estimateWalkingTime(100), 1);

// 0m → 1 min (min clamp)
assert('0m → 1 min (min clamp)', estimateWalkingTime(0), 1);

// 10000m = 120 minutes
assert('10000m → 120 min', estimateWalkingTime(10000), 120);

// Negative metres → min clamp
assert('-500m → 1 min (min clamp)', estimateWalkingTime(-500), 1);

// ─── 4-arg (Haversine legacy) path ────────────────────────

console.log('\n=== 4-arg (Haversine) legacy path ===');

// Liverpool Lime St to Liverpool Cathedral (~1.5 km)
// Approx: 53.4078,-2.9817 → 53.3952,-2.9712
const limeToCathedral = estimateWalkingTime(53.4078, -2.9817, 53.3952, -2.9712);
assert(
  'Liverpool Lime St → Cathedral ~18-22 min',
  limeToCathedral >= 15 && limeToCathedral <= 25,
  true,
);

// Same point → 0 distance → 1 min (min clamp)
assert('Same point → 1 min (min clamp)', estimateWalkingTime(53.4, -2.9, 53.4, -2.9), 1);

// London to Manchester (~260 km as-the-crow-flies)
const londonToManchester = estimateWalkingTime(51.5074, -0.1278, 53.4808, -2.2426);
assert(
  'London → Manchester ~3000+ min',
  londonToManchester > 3000,
  true,
);

// ─── Summary ──────────────────────────────────────────────

console.log(`\n=== Results: ${passed} passed, ${failed} failed ===`);
if (failed > 0) {
  process.exit(1);
}

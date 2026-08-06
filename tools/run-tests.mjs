// ============================================================
// Relief — test runner
// ============================================================
// Runs every *.test.ts in __tests__ as its own process via tsx,
// and fails if any of them fail. Separate processes keep the
// per-file exit codes meaningful and stop one file's state from
// leaking into another.
// ============================================================

import { existsSync, readdirSync } from 'node:fs';
import { spawnSync } from 'node:child_process';
import path from 'node:path';

const TSX_CLI = 'node_modules/tsx/dist/cli.mjs';
if (!existsSync(TSX_CLI)) {
  console.error(`tsx not found at ${TSX_CLI}. Run \`npm ci\` first.`);
  process.exit(1);
}

const testDir = '__tests__';
const files = readdirSync(testDir)
  .filter((name) => name.endsWith('.test.ts'))
  .sort();

if (files.length === 0) {
  console.error('No test files found in __tests__/');
  process.exit(1);
}

const failed = [];

for (const file of files) {
  const target = path.join(testDir, file);
  console.log(`\n${'─'.repeat(60)}\n${target}\n${'─'.repeat(60)}`);
  // Run tsx's JS entry with the current node binary. Spawning the `.bin`
  // wrapper would need shell:true on Windows, which concatenates arguments
  // unescaped, and Windows cannot exec a .cmd without a shell at all.
  const result = spawnSync(process.execPath, [TSX_CLI, target], { stdio: 'inherit' });
  if (result.status !== 0) failed.push(file);
}

console.log(`\n${'═'.repeat(60)}`);
if (failed.length > 0) {
  console.error(`FAILED: ${failed.length} of ${files.length} test files`);
  for (const file of failed) console.error(`  - ${file}`);
  process.exit(1);
}
console.log(`All ${files.length} test files passed.`);

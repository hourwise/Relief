// Node typings are intentionally not part of the mobile app dependency graph.
// tsx supplies this runtime import for the source-boundary assertion.
// @ts-expect-error -- the test runner executes this under Node via tsx.
import { readFileSync } from 'node:fs';
import { assertEqual, assertTrue, section } from './helpers/harness';

section('governed community badge boundary');

const communitySource = readFileSync(
  new URL('../src/services/community.ts', import.meta.url),
  'utf8',
);

assertTrue(
  'community service retains badge readback',
  communitySource.includes(".from('user_badges')"),
);
assertEqual(
  'community service does not insert privileged badge rows',
  /\.from\(['"]user_badges['"]\)[\s\S]{0,200}\.insert/.test(communitySource),
  false,
);
assertEqual(
  'obsolete client badge award helper is removed',
  communitySource.includes('checkAndAwardBadge'),
  false,
);

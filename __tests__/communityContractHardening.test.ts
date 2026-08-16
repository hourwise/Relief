// Node typings are intentionally not part of the mobile app dependency graph.
// tsx supplies this runtime import for the source-boundary assertions.
// @ts-expect-error -- the test runner executes this under Node via tsx.
import { readFileSync } from 'node:fs';
import { assertEqual, assertTrue, section } from './helpers/harness';

section('community contract hardening boundary');

const migration = readFileSync(
  new URL('../supabase/migrations/20260816205543_community_contract_hardening.sql', import.meta.url),
  'utf8',
);
const contracts = readFileSync(
  new URL('../src/services/integrationContracts.ts', import.meta.url),
  'utf8',
);
const community = readFileSync(
  new URL('../src/services/community.ts', import.meta.url),
  'utf8',
);

assertTrue(
  'facility submission migration rejects privileged client columns',
  migration.includes('create policy "Users can insert their own pending submissions"') &&
    migration.includes("and status = 'pending'") &&
    migration.includes('reviewed_by is null') &&
    migration.includes('rejection_reason is null'),
);
assertTrue(
  'correction migration rejects privileged client columns',
  migration.includes('create policy "Users can insert their own pending corrections"') &&
    migration.includes("and status = 'pending'") &&
    migration.includes('reviewed_at is null'),
);
assertTrue(
  'temporary report update is replaced by an owner RPC',
  migration.includes('resolve_own_temporary_report') &&
    migration.includes('revoke insert, update, delete, truncate, trigger'),
);
assertTrue(
  'access-code writes use the owner-derived RPC',
  migration.includes('upsert_own_access_code') &&
    migration.includes('is_verified') &&
    migration.includes('values (\n    p_facility_id, actor, p_code, coalesce(p_description, \'\'), false\n  )'),
);
assertTrue(
  'privileged functions use a fixed search path',
  migration.match(/security definer[\s\S]*?set search_path = pg_catalog, public/g)?.length === 2,
);
assertTrue(
  'temporary report builder leaves expiry state to the database',
  !contracts.includes('is_expired: false'),
);
assertTrue(
  'contribution builders leave moderation state to the database',
  !contracts.includes("status: 'pending'"),
);
assertTrue(
  'mobile resolution calls the governed RPC',
  community.includes("supabase.rpc(\n    'resolve_own_temporary_report'") &&
    !community.includes(".from('temporary_reports')\n    .update({"),
);
assertTrue(
  'mobile access-code writes call the governed RPC',
  community.includes("supabase.rpc('upsert_own_access_code'") &&
    !community.includes(".from('access_codes').insert"),
);
assertEqual(
  'mobile badge writes remain absent',
  /\.from\(['"]user_badges['"]\)[\s\S]{0,200}\.insert/.test(community),
  false,
);

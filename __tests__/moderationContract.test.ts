// Node typings are intentionally not part of the mobile app dependency graph.
// tsx supplies this runtime import for the source-boundary assertions.
// @ts-expect-error -- the test runner executes this under Node via tsx.
import { readFileSync } from 'node:fs';
import { assertEqual, assertTrue, section } from './helpers/harness';

section('governed moderation contract boundary');

const migration = readFileSync(
  new URL('../supabase/migrations/20260816220000_governed_moderation_contract.sql', import.meta.url),
  'utf8',
);
const moderation = readFileSync(
  new URL('../src/services/moderation.ts', import.meta.url),
  'utf8',
);

assertTrue(
  'moderator membership is database-backed and not client-writable',
  migration.includes('create table if not exists public.relief_moderators') &&
    migration.includes('revoke all on table public.relief_moderators') &&
    migration.includes('from public, anon, authenticated, service_role'),
);
assertTrue(
  'moderator authorization derives from auth.uid and active database state',
  migration.includes('private.relief_require_moderator') &&
    migration.includes('actor uuid := auth.uid()') &&
    migration.includes('where user_id = actor') &&
    migration.includes('active = true'),
);
assertEqual(
  'client metadata is not used for moderator authorization',
  /user_metadata|raw_user_meta_data|app_metadata|raw_app_meta_data/.test(migration),
  false,
);
assertTrue(
  'facility moderation has explicit terminal transitions and server reviewer',
  migration.includes("p_decision not in ('approved', 'rejected')") &&
    migration.includes("current_submission.status <> 'pending'") &&
    migration.includes('reviewed_by = actor') &&
    migration.includes('reviewed_at = pg_catalog.now()'),
);
assertTrue(
  'facility approval cannot mutate canonical facilities',
  migration.includes('No facilities row is') &&
    migration.includes('inserted or updated by this function') &&
    !/moderate_facility_submission[\s\S]*?insert into public\.facilities/.test(migration),
);
assertTrue(
  'correction moderation records rejection reason without applying arbitrary columns',
    migration.includes('add column if not exists rejection_reason text') &&
    migration.includes('No arbitrary canonical column is') &&
    migration.includes('interpreted or updated'),
);
assertTrue(
  'access-code verification and revocation have narrow explicit decisions',
  migration.includes("p_decision not in ('verify', 'revoke')") &&
    migration.includes('access_code_verification_history') &&
    migration.includes("action in ('verified', 'revoked')"),
);
assertTrue(
  'all privileged moderation functions use a controlled search path',
  migration.match(/security definer\s+set search_path = pg_catalog, public/g)?.length === 7,
);
assertTrue(
  'moderation RPCs are authenticated-only and never anonymous or service-role paths',
  migration.match(/grant execute on function public\.(list_moderation|moderate_)[\s\S]*?to authenticated/g)?.length === 6 &&
    migration.match(/revoke all on function public\.(list_moderation|moderate_)[\s\S]*?from public, anon, authenticated, service_role/g)?.length === 6,
);
assertTrue(
  'mobile moderation wrapper uses only governed RPCs',
  moderation.includes("moderate_facility_submission") &&
    moderation.includes("moderate_correction_request") &&
    moderation.includes("moderate_access_code") &&
    !moderation.includes("supabase.from('facilities')") &&
    !moderation.includes("supabase.from('relief_moderators')"),
);

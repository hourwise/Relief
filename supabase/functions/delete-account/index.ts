import { serve } from 'https://deno.land/std@0.168.0/http/server.ts';
import { createClient } from 'https://esm.sh/@supabase/supabase-js@2';
import {
  parseDeletionRequestBody,
  isRecentlyAuthenticated,
} from './contract.ts';

const STORAGE_PAGE_SIZE = 1000;
const STORAGE_REMOVE_BATCH_SIZE = 1000;
const MAX_STORAGE_OBJECTS = 50_000;

type OwnedStorageObject = {
  bucket_id: string;
  name: string;
};

function jsonResponse(body: Record<string, unknown>, status: number): Response {
  return new Response(JSON.stringify(body), {
    status,
    headers: {
      'Content-Type': 'application/json',
      'Access-Control-Allow-Headers': 'authorization, x-client-info, apikey, content-type',
      'Access-Control-Allow-Methods': 'POST, OPTIONS',
      'Access-Control-Allow-Origin': '*',
    },
  });
}

function bearerToken(request: Request): string | null {
  const value = request.headers.get('authorization') ?? '';
  const match = value.match(/^Bearer\s+(.+)$/i);
  return match?.[1] ?? null;
}

async function listOwnedStorageObjects(
  admin: any,
  userId: string,
): Promise<OwnedStorageObject[]> {
  const { data: buckets, error: bucketError } = await admin.storage.listBuckets();
  if (bucketError) throw new Error(`Storage bucket inventory failed: ${bucketError.message}`);
  if (!buckets || buckets.length === 0) return [];

  const objects = new Map<string, OwnedStorageObject>();
  for (const ownerColumn of ['owner', 'owner_id'] as const) {
    let offset = 0;
    while (true) {
      const { data, error } = await admin
        .schema('storage')
        .from('objects')
        .select('bucket_id,name')
        .eq(ownerColumn, userId)
        .range(offset, offset + STORAGE_PAGE_SIZE - 1);

      if (error) throw new Error(`Storage object inventory failed: ${error.message}`);
      for (const row of (data ?? []) as OwnedStorageObject[]) {
        objects.set(`${row.bucket_id}:${row.name}`, row);
      }

      if (!data || data.length < STORAGE_PAGE_SIZE) break;
      offset += STORAGE_PAGE_SIZE;
      if (objects.size > MAX_STORAGE_OBJECTS) {
        throw new Error('Storage object inventory exceeds the bounded deletion limit');
      }
    }
  }

  return [...objects.values()];
}

async function removeOwnedStorageObjects(
  admin: any,
  userId: string,
): Promise<number> {
  const objects = await listOwnedStorageObjects(admin, userId);
  const byBucket = new Map<string, string[]>();
  for (const object of objects) {
    const names = byBucket.get(object.bucket_id) ?? [];
    names.push(object.name);
    byBucket.set(object.bucket_id, names);
  }

  let removed = 0;
  for (const [bucketId, names] of byBucket) {
    for (let index = 0; index < names.length; index += STORAGE_REMOVE_BATCH_SIZE) {
      const batch = names.slice(index, index + STORAGE_REMOVE_BATCH_SIZE);
      const { error } = await admin.storage.from(bucketId).remove(batch);
      if (error) throw new Error(`Storage object removal failed: ${error.message}`);
      removed += batch.length;
    }
  }
  return removed;
}

serve(async (request) => {
  const requestId = crypto.randomUUID();
  if (request.method === 'OPTIONS') return jsonResponse({}, 204);
  if (request.method !== 'POST') {
    return jsonResponse({ ok: false, code: 'METHOD_NOT_ALLOWED', request_id: requestId }, 405);
  }

  const token = bearerToken(request);
  if (!token) {
    return jsonResponse({ ok: false, code: 'AUTHENTICATION_REQUIRED', request_id: requestId }, 401);
  }

  const supabaseUrl = Deno.env.get('SUPABASE_URL') ?? '';
  const supabaseAnonKey = Deno.env.get('SUPABASE_ANON_KEY') ?? '';
  const supabaseServiceRoleKey = Deno.env.get('SUPABASE_SERVICE_ROLE_KEY') ?? '';
  if (!supabaseUrl || !supabaseAnonKey || !supabaseServiceRoleKey) {
    console.error(JSON.stringify({ request_id: requestId, outcome: 'misconfigured' }));
    return jsonResponse({ ok: false, code: 'DELETION_BACKEND_MISCONFIGURED', request_id: requestId }, 503);
  }

  let body: unknown;
  try {
    body = await request.json();
  } catch {
    return jsonResponse({ ok: false, code: 'INVALID_REQUEST', request_id: requestId }, 400);
  }
  const parsed = parseDeletionRequestBody(body);
  if (!parsed.ok) {
    return jsonResponse({ ok: false, code: parsed.code, error: parsed.error, request_id: requestId }, 400);
  }

  const authClient = createClient(supabaseUrl, supabaseAnonKey, {
    auth: { autoRefreshToken: false, persistSession: false },
  });
  const { data: authData, error: authError } = await authClient.auth.getUser(token);
  if (authError || !authData.user) {
    return jsonResponse({ ok: false, code: 'AUTHENTICATION_REQUIRED', request_id: requestId }, 401);
  }
  if (!isRecentlyAuthenticated(authData.user.last_sign_in_at)) {
    return jsonResponse({ ok: false, code: 'RECENT_AUTHENTICATION_REQUIRED', request_id: requestId }, 401);
  }

  const userId = authData.user.id;
  const admin = createClient(supabaseUrl, supabaseServiceRoleKey, {
    auth: { autoRefreshToken: false, persistSession: false },
  });
  const userClient = createClient(supabaseUrl, supabaseAnonKey, {
    auth: { autoRefreshToken: false, persistSession: false },
    global: { headers: { Authorization: `Bearer ${token}` } },
  });

  let storageObjectsRemoved = 0;
  try {
    storageObjectsRemoved = await removeOwnedStorageObjects(admin, userId);
  } catch (error) {
    console.error(JSON.stringify({ request_id: requestId, outcome: 'storage_failed' }));
    return jsonResponse({
      ok: false,
      code: 'STORAGE_CLEANUP_FAILED',
      partial: storageObjectsRemoved > 0,
      retryable: true,
      request_id: requestId,
    }, 502);
  }

  const { data: cleanup, error: cleanupError } = await userClient.rpc('delete_my_account_data');
  if (cleanupError || !cleanup) {
    console.error(JSON.stringify({ request_id: requestId, outcome: 'data_cleanup_failed' }));
    return jsonResponse({
      ok: false,
      code: 'DATA_CLEANUP_FAILED',
      partial: storageObjectsRemoved > 0,
      retryable: true,
      request_id: requestId,
    }, 502);
  }

  const { error: authDeleteError } = await admin.auth.admin.deleteUser(userId);
  if (authDeleteError) {
    console.error(JSON.stringify({ request_id: requestId, outcome: 'auth_delete_failed' }));
    return jsonResponse({
      ok: false,
      code: 'AUTH_DELETE_FAILED',
      partial: true,
      retryable: true,
      request_id: requestId,
    }, 502);
  }

  console.log(JSON.stringify({ request_id: requestId, outcome: 'deleted' }));
  return jsonResponse({
    ok: true,
    status: 'deleted',
    storage_objects_removed: storageObjectsRemoved,
    data_cleanup: cleanup,
    request_id: requestId,
  }, 200);
});

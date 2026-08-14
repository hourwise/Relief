export const DELETE_ACCOUNT_CONFIRMATION = 'DELETE MY ACCOUNT';
export const RECENT_AUTH_WINDOW_MS = 15 * 60 * 1000;
const CLOCK_SKEW_MS = 60 * 1000;

export type ParsedDeletionRequest =
  | { ok: true; confirmation: typeof DELETE_ACCOUNT_CONFIRMATION }
  | { ok: false; code: 'INVALID_REQUEST'; error: string };

/**
 * The request body deliberately has no target-user field. Any future caller
 * that tries to provide one is rejected rather than silently ignored.
 */
export function parseDeletionRequestBody(input: unknown): ParsedDeletionRequest {
  if (input === null || typeof input !== 'object' || Array.isArray(input)) {
    return { ok: false, code: 'INVALID_REQUEST', error: 'A confirmation object is required.' };
  }

  const body = input as Record<string, unknown>;
  const unexpectedKeys = Object.keys(body).filter((key) => key !== 'confirmation');
  if (unexpectedKeys.length > 0) {
    return { ok: false, code: 'INVALID_REQUEST', error: 'The deletion request contains unsupported fields.' };
  }

  if (typeof body.confirmation !== 'string' || body.confirmation.trim().toUpperCase() !== DELETE_ACCOUNT_CONFIRMATION) {
    return { ok: false, code: 'INVALID_REQUEST', error: `Type ${DELETE_ACCOUNT_CONFIRMATION} to confirm this request.` };
  }

  return { ok: true, confirmation: DELETE_ACCOUNT_CONFIRMATION };
}

export function isRecentlyAuthenticated(
  lastSignInAt: string | null | undefined,
  nowMs: number = Date.now(),
): boolean {
  if (!lastSignInAt) return false;
  const signInMs = Date.parse(lastSignInAt);
  if (!Number.isFinite(signInMs)) return false;
  return signInMs <= nowMs + CLOCK_SKEW_MS && nowMs - signInMs <= RECENT_AUTH_WINDOW_MS;
}

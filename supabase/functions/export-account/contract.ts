export type ParsedExportRequest =
  | { ok: true }
  | { ok: false; code: 'INVALID_REQUEST'; error: string };

/**
 * The export target is always the verified bearer subject. An empty object is
 * the complete request contract so user_id, target_user_id, email, and every
 * future arbitrary selector fail closed rather than being ignored.
 */
export function parseExportRequestBody(input: unknown): ParsedExportRequest {
  if (input === null || typeof input !== 'object' || Array.isArray(input)) {
    return { ok: false, code: 'INVALID_REQUEST', error: 'An empty export request object is required.' };
  }

  if (Object.keys(input as Record<string, unknown>).length > 0) {
    return { ok: false, code: 'INVALID_REQUEST', error: 'The export request cannot select another account.' };
  }

  return { ok: true };
}

/** Pure recovery-link predicate used by native deep-link handling and tests. */
export function isPasswordRecoveryUrl(url: string): boolean {
  const lower = url.toLowerCase();
  return lower.includes('type=recovery') || lower.includes('code=') || lower.includes('access_token=');
}

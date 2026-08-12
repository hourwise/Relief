// Optional follow-up work must never change the result of a primary action.
// This is intentionally dependency-free so the contract can be tested without
// loading the native Supabase client.
export async function runNonFatalSideEffect(
  task: () => Promise<void>,
  onError: (error: unknown) => void = () => undefined,
): Promise<boolean> {
  try {
    await task();
    return true;
  } catch (error) {
    onError(error);
    return false;
  }
}

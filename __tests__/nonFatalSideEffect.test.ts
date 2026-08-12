import { runNonFatalSideEffect } from '../src/utils/nonFatalSideEffect';
import { assertEqual, assertTrue, section } from './helpers/harness';

section('optional badge side effects');

async function runAssertions(): Promise<void> {
  const primaryResult = 'submitted';
  const success = await runNonFatalSideEffect(async () => undefined);
  assertTrue('successful optional work reports success', success);
  assertEqual('primary action result remains successful', primaryResult, 'submitted');

  let loggedError: unknown = null;
  const failed = await runNonFatalSideEffect(
    async () => {
      throw new Error('RLS denied badge insert');
    },
    (error) => {
      loggedError = error;
    },
  );
  assertEqual('failed optional work reports non-fatal failure', failed, false);
  assertTrue('optional failure is available for development logging', loggedError instanceof Error);
  assertEqual('primary action is not changed by optional failure', primaryResult, 'submitted');
}

runAssertions().catch((error) => {
  console.error(error);
  process.exitCode = 1;
});

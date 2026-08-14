import { createAccountDeletionAdapter } from '../src/services/accountDeletion';
import { createPhotoStorageAdapter } from '../src/services/photoStorage';
import { assertEqual, assertTrue, section } from './helpers/harness';

section('account deletion adapters');
(async () => {
  const testDelete = createAccountDeletionAdapter(true);
  const testDeleteResult = await testDelete('DELETE MY ACCOUNT');
  assertTrue('test deletion simulates success', testDeleteResult.success === true && testDeleteResult.simulated === true);
  const productionDelete = createAccountDeletionAdapter(false, async () => ({
    success: false,
    code: 'DELETION_BACKEND_MISCONFIGURED',
    error: 'backend unavailable',
  }));
  const productionDeleteResult = await productionDelete('DELETE MY ACCOUNT');
  assertEqual('production deletion reports backend failure without claiming success', productionDeleteResult.success, false);
  if (!productionDeleteResult.success) assertEqual('production deletion code', productionDeleteResult.code, 'DELETION_BACKEND_MISCONFIGURED');

  section('photo storage adapters');
  const testPhoto = createPhotoStorageAdapter(true);
  const selected = await testPhoto.selectPhoto();
  assertTrue('test photo selection is deterministic', selected?.uri === 'relief://test/photo-sample');
  if (selected) {
    const uploaded = await testPhoto.uploadAndModerate(selected.uri);
    assertTrue('test photo stays pending moderation', uploaded.success && uploaded.simulated && uploaded.moderation === 'pending');
  }
  const productionPhoto = createPhotoStorageAdapter(false);
  const unavailable = await productionPhoto.uploadAndModerate('file://not-uploaded');
  assertEqual('production photo upload is unavailable', unavailable.moderation, 'unavailable');
})().catch((error) => {
  console.error(error);
  process.exitCode = 1;
});

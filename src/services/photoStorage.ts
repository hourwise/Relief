import { RELIEF_TEST_MODE } from '../utils/env';

export type PhotoModerationState = 'pending' | 'approved' | 'blocked' | 'unavailable';

export interface PhotoUploadResult {
  success: boolean;
  uri?: string;
  moderation: PhotoModerationState;
  simulated: boolean;
  error?: string;
}

export interface PhotoStorageAdapter {
  selectPhoto(): Promise<{ uri: string } | null>;
  uploadAndModerate(uri: string): Promise<PhotoUploadResult>;
  cancel(uri?: string): Promise<void>;
}

const testPhotoAdapter: PhotoStorageAdapter = {
  async selectPhoto() {
    return { uri: 'relief://test/photo-sample' };
  },
  async uploadAndModerate(uri) {
    return {
      success: true,
      uri,
      moderation: 'pending',
      simulated: true,
    };
  },
  async cancel() {
    return undefined;
  },
};

const productionPhotoAdapter: PhotoStorageAdapter = {
  async selectPhoto() {
    return null;
  },
  async uploadAndModerate() {
    return {
      success: false,
      moderation: 'unavailable',
      simulated: false,
      error: 'Photo upload is not available until storage and moderation are configured.',
    };
  },
  async cancel() {
    return undefined;
  },
};

export function createPhotoStorageAdapter(testMode: boolean = RELIEF_TEST_MODE): PhotoStorageAdapter {
  return testMode ? testPhotoAdapter : productionPhotoAdapter;
}

export function getPhotoStorageAdapter(): PhotoStorageAdapter {
  return createPhotoStorageAdapter();
}

import { RELIEF_TEST_MODE } from '../utils/env';

export const DATA_EXPORT_FUNCTION = 'export-account' as const;
export const DATA_EXPORT_VERSION = 1 as const;

export type DataExportErrorCode =
  | 'INVALID_REQUEST'
  | 'AUTHENTICATION_REQUIRED'
  | 'RECENT_AUTHENTICATION_REQUIRED'
  | 'EXPORT_BACKEND_MISCONFIGURED'
  | 'EXPORT_GENERATION_FAILED'
  | 'EXPORT_REQUEST_FAILED';

export interface DataExportFacilityReference {
  id: string;
  name: string;
  address: string | null;
  town: string;
  postcode: string | null;
  publication_status?: string;
}

export interface ReliefDataExport {
  export_version: typeof DATA_EXPORT_VERSION;
  generated_at: string;
  account: {
    id: string;
    email: string | null;
    created_at: string | null;
    email_confirmed_at: string | null;
    display_name: string | null;
  };
  profile: Record<string, unknown> | null;
  favourites: (Record<string, unknown> & { facility: DataExportFacilityReference | null })[];
  saved_profiles: Record<string, unknown>[];
  contributions: {
    facility_submissions: Record<string, unknown>[];
    reports: (Record<string, unknown> & { facility: DataExportFacilityReference | null })[];
    temporary_reports: (Record<string, unknown> & { facility: DataExportFacilityReference | null })[];
    corrections: (Record<string, unknown> & { facility: DataExportFacilityReference | null })[];
    access_codes: (Record<string, unknown> & { facility: DataExportFacilityReference | null })[];
    photo_moderation: (Record<string, unknown> & { facility: DataExportFacilityReference | null })[];
    review_reports: Record<string, unknown>[];
  };
  badges: Record<string, unknown>[];
  subscriptions: {
    current: Record<string, unknown> | null;
    events: Record<string, unknown>[];
    provider_payloads: 'excluded';
  };
  moderation_activity: {
    role: 'moderator' | 'none' | null;
    availability: 'complete' | 'partial';
    limitation: string | null;
    review_actions: Record<string, unknown>[];
    verification_actions: Record<string, unknown>[];
    photo_reports: Record<string, unknown>[];
  };
  canonical_attribution: Record<string, unknown>[];
  excluded: string[];
}

export type DataExportResult =
  | { success: true; simulated: boolean; payload: ReliefDataExport; json: string }
  | { success: false; code: DataExportErrorCode; error: string; retryable?: boolean };

type ExportResponse = {
  ok: boolean;
  export?: ReliefDataExport;
  code?: DataExportErrorCode;
  error?: string;
  retryable?: boolean;
};

async function responseFromFunctionError(error: unknown): Promise<ExportResponse | null> {
  const context = (error as { context?: { json?: () => Promise<unknown> } } | null)?.context;
  if (!context?.json) return null;
  try {
    const body = await context.json();
    return body && typeof body === 'object' ? body as ExportResponse : null;
  } catch {
    return null;
  }
}

export type DataExportInvoker = () => Promise<DataExportResult>;

export function formatDataExport(payload: ReliefDataExport): string {
  return `${JSON.stringify(payload, null, 2)}\n`;
}

export function getDataExportErrorMessage(
  result: Extract<DataExportResult, { success: false }>,
): string {
  switch (result.code) {
    case 'INVALID_REQUEST':
      return 'Relief could not understand the export request. No account data was changed.';
    case 'AUTHENTICATION_REQUIRED':
      return 'Sign in to request a copy of your Relief data.';
    case 'RECENT_AUTHENTICATION_REQUIRED':
      return 'For your security, please sign in again and then retry the data export.';
    case 'EXPORT_BACKEND_MISCONFIGURED':
    case 'EXPORT_GENERATION_FAILED':
    case 'EXPORT_REQUEST_FAILED':
      return 'Relief could not generate your data export. No account data was changed. Please try again later.';
    default:
      return result.error;
  }
}

export function buildTestDataExport(): ReliefDataExport {
  return {
    export_version: DATA_EXPORT_VERSION,
    generated_at: '2026-01-01T00:00:00.000Z',
    account: {
      id: 'relief-test-account',
      email: 'example.user@invalid.test',
      created_at: '2026-01-01T00:00:00.000Z',
      email_confirmed_at: '2026-01-01T00:00:00.000Z',
      display_name: 'Example Relief user',
    },
    profile: null,
    favourites: [],
    saved_profiles: [],
    contributions: {
      facility_submissions: [],
      reports: [],
      temporary_reports: [],
      corrections: [],
      access_codes: [],
      photo_moderation: [],
      review_reports: [],
    },
    badges: [],
    subscriptions: { current: null, events: [], provider_payloads: 'excluded' },
    moderation_activity: {
      role: 'none',
      availability: 'complete',
      limitation: null,
      review_actions: [],
      verification_actions: [],
      photo_reports: [],
    },
    canonical_attribution: [],
    excluded: [
      'passwords_and_authentication_tokens',
      'internal_security_controls',
      'reviewer_identity_references',
      'canonical_import_and_provenance_internals',
      'raw_revenuecat_webhook_payloads',
    ],
  };
}

async function invokeProductionExport(): Promise<DataExportResult> {
  const { supabase } = await import('./supabase');
  const { data, error } = await supabase.functions.invoke<ExportResponse>(DATA_EXPORT_FUNCTION, {
    body: {},
  });

  if (error) {
    const errorResponse = await responseFromFunctionError(error);
    if (errorResponse?.code) {
      return {
        success: false,
        code: errorResponse.code,
        error: errorResponse.error ?? 'The data export could not be generated.',
        retryable: errorResponse.retryable,
      };
    }
    return {
      success: false,
      code: 'EXPORT_REQUEST_FAILED',
      error: 'The data export service could not be reached.',
      retryable: true,
    };
  }

  if (!data) {
    return {
      success: false,
      code: 'EXPORT_REQUEST_FAILED',
      error: 'The data export service returned no response.',
      retryable: true,
    };
  }

  if (!data.ok || !data.export) {
    return {
      success: false,
      code: data.code ?? 'EXPORT_GENERATION_FAILED',
      error: data.error ?? 'The data export could not be generated.',
      retryable: data.retryable,
    };
  }

  return {
    success: true,
    simulated: false,
    payload: data.export,
    json: formatDataExport(data.export),
  };
}

export function createDataExportAdapter(
  testMode: boolean = RELIEF_TEST_MODE,
  invoke: DataExportInvoker = invokeProductionExport,
): DataExportInvoker {
  return async (): Promise<DataExportResult> => {
    if (testMode) {
      const payload = buildTestDataExport();
      return { success: true, simulated: true, payload, json: formatDataExport(payload) };
    }
    return invoke();
  };
}

export const requestDataExport = createDataExportAdapter();

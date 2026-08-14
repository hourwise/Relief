export const FEATURE_LAB_ROUTES = [
  'AdvancedFilters',
  'SavedProfiles',
  'RoutePlanning',
  'OfflineMaps',
  'NotificationAlerts',
  'Paywall',
  'PhotoFlow',
  'AccountDeletion',
  'LegalInfo',
  'ForgotPassword',
  'UpdatePassword',
] as const;

export type FeatureLabRoute = typeof FEATURE_LAB_ROUTES[number];

import { FEATURE_LAB_ROUTES } from '../src/navigation/featureRoutes';
import { assertEqual, assertTrue, section } from './helpers/harness';

section('test-mode navigation contract');
assertTrue('Feature Lab routes are unique', new Set(FEATURE_LAB_ROUTES).size === FEATURE_LAB_ROUTES.length);
for (const route of ['AdvancedFilters', 'SavedProfiles', 'RoutePlanning', 'OfflineMaps', 'NotificationAlerts', 'Paywall', 'PhotoFlow', 'AccountDeletion', 'LegalInfo']) {
  assertTrue(`${route} has a Feature Lab entry`, FEATURE_LAB_ROUTES.includes(route as typeof FEATURE_LAB_ROUTES[number]));
}
assertEqual('Feature Lab has expected route count', FEATURE_LAB_ROUTES.length, 11);

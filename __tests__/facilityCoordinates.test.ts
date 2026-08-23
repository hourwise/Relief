import { assertDeepEqual, assertEqual, assertTrue, section } from './helpers/harness';
import {
  getFacilitySubmissionCoordinates,
  isValidFacilityCoordinates,
} from '../src/utils/facilityCoordinates';

section('Add Facility coordinate safety contract');

const selected = { latitude: 53.4808, longitude: -2.2426 };
assertTrue('valid selected coordinates are accepted', isValidFacilityCoordinates(selected));
assertDeepEqual(
  'valid selected coordinates pass through unchanged',
  getFacilitySubmissionCoordinates(selected),
  selected,
);

assertEqual('missing coordinates fail closed', getFacilitySubmissionCoordinates(null), null);
assertEqual(
  'non-finite latitude fails closed',
  getFacilitySubmissionCoordinates({ latitude: Number.NaN, longitude: -2.2 }),
  null,
);
assertEqual(
  'non-finite longitude fails closed',
  getFacilitySubmissionCoordinates({ latitude: 53.4, longitude: Number.POSITIVE_INFINITY }),
  null,
);
assertEqual(
  'out-of-range latitude fails closed',
  getFacilitySubmissionCoordinates({ latitude: 90.1, longitude: -2.2 }),
  null,
);
assertEqual(
  'out-of-range longitude fails closed',
  getFacilitySubmissionCoordinates({ latitude: 53.4, longitude: -180.1 }),
  null,
);
assertEqual(
  '0,0 placeholder fails closed',
  getFacilitySubmissionCoordinates({ latitude: 0, longitude: 0 }),
  null,
);

// ============================================================
// Relief — list ordering, including null ratings
// ============================================================

import { sortFacilities, type RankedFacility } from '../src/utils/facilitySort';
import type { Facility } from '../src/types';
import { assertDeepEqual, section } from './helpers/harness';

/** Only the fields the sort reads; the rest of Facility is irrelevant here. */
function ranked(
  name: string,
  distanceMetres: number | null,
  overall_score: number | null,
): RankedFacility {
  return {
    facility: { id: name, name, overall_score } as unknown as Facility,
    distanceMetres,
  };
}

const names = (items: RankedFacility[]) => items.map((item) => item.facility.name);

section('sort by distance');

assertDeepEqual(
  'nearest first',
  names(sortFacilities([ranked('far', 900, 4), ranked('near', 100, 2), ranked('mid', 400, 5)], 'distance')),
  ['near', 'mid', 'far'],
);

// A facility whose distance cannot be computed must not masquerade as nearest.
assertDeepEqual(
  'unknown distance sorts last, not first',
  names(sortFacilities([ranked('unknown', null, 5), ranked('near', 100, 1)], 'distance')),
  ['near', 'unknown'],
);

assertDeepEqual(
  'all-unknown distances fall back to name order',
  names(sortFacilities([ranked('Bravo', null, null), ranked('Alpha', null, null)], 'distance')),
  ['Alpha', 'Bravo'],
);

assertDeepEqual(
  'equal distances break ties by name, so order is stable',
  names(sortFacilities([ranked('Bravo', 250, 1), ranked('Alpha', 250, 5)], 'distance')),
  ['Alpha', 'Bravo'],
);

assertDeepEqual(
  'zero distance is a real distance and sorts first',
  names(sortFacilities([ranked('here', 0, null), ranked('there', 10, 5)], 'distance')),
  ['here', 'there'],
);

section('sort by rating');

assertDeepEqual(
  'highest rated first',
  names(sortFacilities([ranked('ok', 100, 3.2), ranked('best', 900, 4.8), ranked('poor', 50, 1.5)], 'rating')),
  ['best', 'ok', 'poor'],
);

// The imported UK dataset stores overall_score = 0 for facilities with no
// community ratings. Zero means "unrated", so it must sink like null does
// rather than being ranked as a genuinely terrible facility.
assertDeepEqual(
  'null rating sorts last',
  names(sortFacilities([ranked('unrated', 100, null), ranked('rated', 900, 2)], 'rating')),
  ['rated', 'unrated'],
);

assertDeepEqual(
  'zero rating is treated as unrated and sorts last',
  names(sortFacilities([ranked('zero', 100, 0), ranked('rated', 900, 1)], 'rating')),
  ['rated', 'zero'],
);

assertDeepEqual(
  'null and zero ratings tie and fall back to name order',
  names(sortFacilities([ranked('Bravo', 10, 0), ranked('Alpha', 20, null)], 'rating')),
  ['Alpha', 'Bravo'],
);

assertDeepEqual(
  'equal ratings break ties by name',
  names(sortFacilities([ranked('Bravo', 10, 4), ranked('Alpha', 20, 4)], 'rating')),
  ['Alpha', 'Bravo'],
);

section('purity');

const input = [ranked('b', 200, 1), ranked('a', 100, 2)];
const before = names(input);
sortFacilities(input, 'distance');
assertDeepEqual('does not mutate its input', names(input), before);

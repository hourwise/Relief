import { rankNearestFacilities } from '../src/utils/nearestFacility';
import { getOpenStatus } from '../src/utils/openingHours';
import type { NearestFacility } from '../src/types';
import { assertDeepEqual, assertEqual, assertTrue, section } from './helpers/harness';

const dayNames = [
  'sunday',
  'monday',
  'tuesday',
  'wednesday',
  'thursday',
  'friday',
  'saturday',
] as const;

function timeString(totalMinutes: number): string {
  const minutes = ((totalMinutes % 1440) + 1440) % 1440;
  return `${String(Math.floor(minutes / 60)).padStart(2, '0')}:${String(minutes % 60).padStart(2, '0')}`;
}

function hours(open: string, close: string) {
  return {
    [dayNames[new Date().getDay()]]: { open, close },
  };
}

function facility(
  id: string,
  distance_metres: number,
  availability: 'open' | 'unknown' | 'closed' | '24h',
): NearestFacility {
  const nowMinutes = new Date().getHours() * 60 + new Date().getMinutes();
  const openHours =
    availability === 'open'
      ? hours('00:00', '23:59')
      : availability === 'closed'
        ? hours(timeString(nowMinutes + 60), timeString(nowMinutes + 61))
        : null;

  return {
    facility_id: id,
    name: id,
    address: null,
    latitude: 53.4,
    longitude: -2.9,
    town: 'Liverpool',
    postcode: null,
    open_hours: openHours,
    is_24h: availability === '24h' ? true : null,
    is_free: true,
    is_accessible: null,
    overall_score: null,
    verification_status: 'source_imported',
    distance_metres,
  };
}

section('availability ranking');

const nearerClosed = facility('closed-near', 100, 'closed');
const fartherOpen = facility('open-far', 250, 'open');
assertEqual(
  'slightly farther confirmed-open facility beats nearer confirmed-closed',
  rankNearestFacilities([nearerClosed, fartherOpen])[0].facility_id,
  fartherOpen.facility_id,
);

const nearerUnknown = facility('unknown-near', 100, 'unknown');
assertEqual(
  'unknown facility beats confirmed-closed fallback',
  rankNearestFacilities([nearerClosed, nearerUnknown])[0].facility_id,
  nearerUnknown.facility_id,
);

const closedA = facility('closed-a', 600, 'closed');
const closedB = facility('closed-b', 300, 'closed');
assertEqual(
  'nearest confirmed-closed facility is returned when all candidates are closed',
  rankNearestFacilities([closedA, closedB])[0].facility_id,
  closedB.facility_id,
);

const allDay = facility('all-day', 900, '24h');
assertEqual('24-hour candidate is confirmed open', getOpenStatus(allDay), 'open');
assertEqual(
  '24-hour candidate wins over a nearer closed facility',
  rankNearestFacilities([nearerClosed, allDay])[0].facility_id,
  allDay.facility_id,
);

assertEqual(
  'missing opening hours remain unknown',
  getOpenStatus(facility('unknown', 100, 'unknown')),
  'unknown',
);

const noCandidates = rankNearestFacilities([]);
assertTrue('no candidates stays an empty result', noCandidates.length === 0);
assertDeepEqual('empty candidate list remains empty', noCandidates, []);

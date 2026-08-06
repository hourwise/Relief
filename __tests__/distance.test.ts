// ============================================================
// Relief — distance calculation and formatting
// ============================================================

import { distanceMetres, formatDistance } from '../src/utils/distance';
import { assertClose, assertEqual, assertNull, section } from './helpers/harness';

section('distanceMetres');

assertEqual('identical points are 0 m apart', distanceMetres(53.4084, -2.9916, 53.4084, -2.9916), 0);

// Liverpool city centre to the nearest facility returned by the live PostGIS
// RPC. The RPC reported 162.08 m, so the client haversine must agree closely.
assertClose(
  'matches PostGIS for the verified Liverpool case',
  distanceMetres(53.4084, -2.9916, 53.408573, -2.98918),
  162.08,
  2,
);

// One degree of latitude is ~111.2 km anywhere on the globe.
assertClose('1° of latitude ≈ 111.2 km', distanceMetres(53, 0, 54, 0), 111195, 500);

// Longitude degrees shrink with latitude; at 53°N one degree is ~67 km.
assertClose('1° of longitude at 53°N ≈ 67 km', distanceMetres(53, 0, 53, 1), 67000, 800);

assertEqual('distance is symmetric', distanceMetres(53.4, -2.9, 53.5, -3.0), distanceMetres(53.5, -3.0, 53.4, -2.9));

section('formatDistance — UK build uses metres and kilometres');

assertEqual('rounds to the nearest 10 m below 1 km', formatDistance(162), '160 m');
assertEqual('rounds up to the nearest 10 m', formatDistance(167), '170 m');
assertEqual('switches to km at exactly 1000 m', formatDistance(1000), '1.0 km');
assertEqual('formats km to one decimal place', formatDistance(1540), '1.5 km');
assertEqual('handles large distances', formatDistance(24800), '24.8 km');

// A facility a few metres away is still "10 m", never "0 m": claiming zero
// distance reads as "you are standing in it".
assertEqual('never reports 0 m', formatDistance(3), '10 m');
assertEqual('never reports 0 m at exactly 0', formatDistance(0), '10 m');

// No position means no distance. The UI omits the label rather than inventing
// one, so null must stay null.
assertNull('null distance formats as null', formatDistance(null));
assertNull('undefined distance formats as null', formatDistance(undefined));
assertNull('negative distance formats as null', formatDistance(-5));
assertNull('NaN formats as null', formatDistance(Number.NaN));
assertNull('Infinity formats as null', formatDistance(Number.POSITIVE_INFINITY));

// Miles must never appear in the UK build.
const samples = [0, 50, 999, 1000, 5000, 30000].map((m) => formatDistance(m) ?? '');
assertEqual(
  'no output mentions miles',
  samples.some((s) => /mi\b/i.test(s)),
  false,
);

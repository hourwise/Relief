// ============================================================
// Relief — report type presentation
// ============================================================
// The facility detail banner rendered the raw enum ("busy:"),
// which reads like a leaked database value. Labels and durations
// now come from one shared source; these tests pin both.
// ============================================================

import {
  REPORT_TYPE_META,
  reportDurationHours,
  reportTypeLabel,
  type ReportType,
} from '../src/utils/reportTypes';
import { assertEqual, assertTrue, section } from './helpers/harness';

const ALL_TYPES: ReportType[] = [
  'closed',
  'out_of_order',
  'cleaning',
  'busy',
  'no_water',
  'refurbishment',
];

section('every report type has presentation metadata');

for (const type of ALL_TYPES) {
  const meta = REPORT_TYPE_META[type];
  assertTrue(`${type} has a label`, !!meta && meta.label.length > 0);
  assertTrue(`${type} has an icon`, !!meta && meta.icon.length > 0);
  assertTrue(`${type} has a positive duration`, !!meta && meta.durationHours > 0);
  // The label is what a user reads, so it must not be the raw enum.
  assertTrue(`${type} label is not the raw enum`, meta.label !== type);
  assertTrue(`${type} label has no underscores`, !meta.label.includes('_'));
}

section('labels');

assertEqual('busy reads as Busy', reportTypeLabel('busy'), 'Busy');
assertEqual('out_of_order is de-slugged', reportTypeLabel('out_of_order'), 'Out of order');
assertEqual('no_water is de-slugged', reportTypeLabel('no_water'), 'No water');
assertEqual('refurbishment reads as a phrase', reportTypeLabel('refurbishment'), 'Under refurbishment');

// A type added server-side before the client knows about it must still read
// acceptably rather than exposing a raw identifier.
assertEqual(
  'an unknown type is de-slugged rather than shown raw',
  reportTypeLabel('some_new_state'),
  'Some new state',
);
assertEqual('an empty type falls back to a sentence', reportTypeLabel(''), 'Issue reported');

section('durations match the report form');

assertEqual('busy lasts 1 hour', reportDurationHours('busy'), 1);
assertEqual('cleaning lasts 1 hour', reportDurationHours('cleaning'), 1);
assertEqual('closed lasts 2 hours', reportDurationHours('closed'), 2);
assertEqual('out_of_order lasts 4 hours', reportDurationHours('out_of_order'), 4);
assertEqual('no_water lasts 4 hours', reportDurationHours('no_water'), 4);
assertEqual('refurbishment lasts 24 hours', reportDurationHours('refurbishment'), 24);

// An unknown type must still expire, and conservatively.
assertEqual('an unknown type gets a safe default', reportDurationHours('some_new_state'), 2);

section('transient states expire soonest');

assertTrue(
  'busy expires no later than closed',
  reportDurationHours('busy') <= reportDurationHours('closed'),
);
assertTrue(
  'refurbishment lasts longest',
  ALL_TYPES.every((t) => reportDurationHours(t) <= reportDurationHours('refurbishment')),
);

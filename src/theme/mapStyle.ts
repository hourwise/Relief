// ============================================================
// Project "Relief" — Google Maps style
// ============================================================
// "Calm Clarity & Soft Organic Guidance" applied to the map
// itself. The default Google style followed the device theme and
// rendered dark navy on this build, which fought the light mint
// chrome and made Relief look like a generic map wrapper.
//
// Rules this style follows, in priority order:
//
//   1. Legibility first. This is used in urgency, sometimes
//      one-handed, sometimes by someone who is not calm. Roads,
//      the user dot and our pins must stay unambiguous.
//   2. Recede, don't disappear. Land and secondary roads are
//      quietened so the teal facility pins and the amber selected
//      state are the brightest things on screen.
//   3. No decoration that costs information. Labels are muted,
//      never removed; POIs are restrained, not stripped, because
//      "next to the museum" is how people actually navigate.
//
// Contrast was chosen so road/land and label/background pairs
// stay legible against the pale mint surface — the pins and the
// route carry the strongest contrast on the map by design.
// ============================================================

export type MapStyleElement = {
  featureType?: string;
  elementType?: string;
  stylers: Record<string, string | number>[];
};

const LAND = '#F4F9F6'; // pale mint, matches colors.mintSurface family
const LAND_SOFT = '#EAF2ED';
const WATER = '#CFE6E0'; // muted teal, distinct from land without shouting
const ROAD_PRIMARY = '#FFFFFF';
const ROAD_PRIMARY_EDGE = '#D6E5DE';
const ROAD_SECONDARY = '#F7FBF9';
const ROAD_SECONDARY_EDGE = '#E1EDE7';
const PARK = '#DCEBE0';
const LABEL = '#4A5B54'; // muted grey-green, readable on pale mint
const LABEL_HALO = '#FFFFFF';
const LABEL_SOFT = '#6F8079';
const TRANSIT = '#DDE9E4';

export const RELIEF_MAP_STYLE: MapStyleElement[] = [
  // ── Base ────────────────────────────────────────────────
  { elementType: 'geometry', stylers: [{ color: LAND }] },
  { elementType: 'labels.text.fill', stylers: [{ color: LABEL }] },
  { elementType: 'labels.text.stroke', stylers: [{ color: LABEL_HALO }, { weight: 3 }] },
  // Icon glyphs are removed but their labels stay: the words carry the
  // wayfinding information, the coloured pins were the visual noise.
  { elementType: 'labels.icon', stylers: [{ visibility: 'off' }] },

  // ── Administrative ──────────────────────────────────────
  { featureType: 'administrative', elementType: 'geometry', stylers: [{ visibility: 'off' }] },
  { featureType: 'administrative.land_parcel', stylers: [{ visibility: 'off' }] },
  { featureType: 'administrative.neighborhood', elementType: 'labels.text.fill', stylers: [{ color: LABEL_SOFT }] },
  { featureType: 'administrative.locality', elementType: 'labels.text.fill', stylers: [{ color: LABEL }] },

  // ── Landscape ───────────────────────────────────────────
  { featureType: 'landscape.natural', elementType: 'geometry', stylers: [{ color: LAND }] },
  { featureType: 'landscape.man_made', elementType: 'geometry', stylers: [{ color: LAND_SOFT }] },

  // ── Green space: kept legible, it is a real landmark ────
  { featureType: 'poi.park', elementType: 'geometry', stylers: [{ color: PARK }] },
  { featureType: 'poi.park', elementType: 'labels.text.fill', stylers: [{ color: '#5C7A66' }] },

  // ── Other POIs: quietened so our pins win ───────────────
  { featureType: 'poi', elementType: 'geometry', stylers: [{ color: LAND_SOFT }] },
  { featureType: 'poi', elementType: 'labels.text.fill', stylers: [{ color: LABEL_SOFT }] },
  { featureType: 'poi.business', stylers: [{ visibility: 'off' }] },
  // Kept deliberately: these are places people are sent to, and are often
  // where a facility actually is.
  { featureType: 'poi.medical', elementType: 'labels', stylers: [{ visibility: 'on' }] },
  { featureType: 'poi.attraction', elementType: 'labels', stylers: [{ visibility: 'on' }] },

  // ── Roads: soft lines, clear hierarchy ──────────────────
  { featureType: 'road', elementType: 'geometry', stylers: [{ color: ROAD_SECONDARY }] },
  { featureType: 'road', elementType: 'geometry.stroke', stylers: [{ color: ROAD_SECONDARY_EDGE }] },
  { featureType: 'road', elementType: 'labels.text.fill', stylers: [{ color: LABEL_SOFT }] },
  { featureType: 'road.highway', elementType: 'geometry', stylers: [{ color: ROAD_PRIMARY }] },
  { featureType: 'road.highway', elementType: 'geometry.stroke', stylers: [{ color: ROAD_PRIMARY_EDGE }] },
  { featureType: 'road.highway', elementType: 'labels.text.fill', stylers: [{ color: LABEL }] },
  { featureType: 'road.arterial', elementType: 'geometry', stylers: [{ color: ROAD_PRIMARY }] },
  { featureType: 'road.arterial', elementType: 'geometry.stroke', stylers: [{ color: ROAD_SECONDARY_EDGE }] },
  { featureType: 'road.local', elementType: 'geometry', stylers: [{ color: ROAD_SECONDARY }] },
  // Walking routes matter for this app, so paths stay visible.
  { featureType: 'road.local', elementType: 'labels.text.fill', stylers: [{ color: LABEL_SOFT }] },

  // ── Transit: present but recessive ──────────────────────
  { featureType: 'transit', elementType: 'geometry', stylers: [{ color: TRANSIT }] },
  { featureType: 'transit', elementType: 'labels.text.fill', stylers: [{ color: LABEL_SOFT }] },
  { featureType: 'transit.station', elementType: 'labels', stylers: [{ visibility: 'on' }] },

  // ── Water ───────────────────────────────────────────────
  { featureType: 'water', elementType: 'geometry', stylers: [{ color: WATER }] },
  { featureType: 'water', elementType: 'labels.text.fill', stylers: [{ color: '#4E756D' }] },
];

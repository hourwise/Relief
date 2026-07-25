/**
 * Relief's native palette. Legacy aliases keep the existing feature surfaces
 * on one source of truth while their layouts are refreshed.
 */
export const colors = {
  primary: '#1A6B5C',
  primaryLight: '#2D8A77',
  sage: '#6CA08E',
  mintSurface: '#F3F8F5',
  secondarySurface: '#EBF3EF',
  amber: '#F4C453',
  urgent: '#E75F51',
  charcoal: '#212C28',
  muted: '#63736C',
  white: '#FFFFFF',
  transparent: 'transparent',

  background: '#F3F8F5',
  cardBackground: '#FFFFFF',
  tealSoft: '#EBF3EF',
  textPrimary: '#212C28',
  textSecondary: '#63736C',
  textMuted: '#7A8982',
  textOnPrimary: '#FFFFFF',
  border: '#D8E6DF',
  borderLight: '#E8F0EC',
  overlay: 'rgba(22, 73, 62, 0.30)',
  glassBackground: 'rgba(255, 255, 255, 0.94)',
  mapOverlay: 'rgba(255, 255, 255, 0.92)',

  success: '#1A6B5C',
  warning: '#C88418',
  error: '#E75F51',
  ratingHigh: '#1A6B5C',
  ratingMedium: '#C88418',
  ratingLow: '#E75F51',

  mapPinDefault: '#1A6B5C',
  mapPinSelected: '#F4C453',
  mapPinAccessible: '#1A6B5C',
  mapPinFamily: '#6CA08E',
  mapCluster: '#1A6B5C',
  mapPinGlow: 'rgba(45, 138, 119, 0.34)',

  black: '#212C28',
  gray50: '#F8FBF9',
  gray100: '#F0F5F2',
  gray200: '#E2ECE7',
  gray300: '#CDDAD4',
  gray400: '#AABAB2',
  gray500: '#63736C',
  gray600: '#506058',
  gray700: '#384740',
  gray800: '#2B3732',
  gray900: '#212C28',
} as const;

export type ColorKey = keyof typeof colors;

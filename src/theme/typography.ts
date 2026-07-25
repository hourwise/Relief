/** Plus Jakarta Sans is the approved Relief typeface. */
export const typography = {
  h1: { fontFamily: 'PlusJakartaSans_700Bold', fontSize: 32, fontWeight: '700', lineHeight: 40, letterSpacing: -0.5 },
  h2: { fontFamily: 'PlusJakartaSans_600SemiBold', fontSize: 24, fontWeight: '600', lineHeight: 32, letterSpacing: -0.3 },
  h3: { fontFamily: 'PlusJakartaSans_600SemiBold', fontSize: 20, fontWeight: '600', lineHeight: 28, letterSpacing: -0.2 },
  h4: { fontFamily: 'PlusJakartaSans_600SemiBold', fontSize: 17, fontWeight: '600', lineHeight: 24, letterSpacing: -0.1 },
  body: { fontFamily: 'PlusJakartaSans_400Regular', fontSize: 16, fontWeight: '400', lineHeight: 24 },
  bodySmall: { fontFamily: 'PlusJakartaSans_400Regular', fontSize: 14, fontWeight: '400', lineHeight: 20 },
  label: { fontFamily: 'PlusJakartaSans_600SemiBold', fontSize: 14, fontWeight: '600', lineHeight: 20 },
  caption: { fontFamily: 'PlusJakartaSans_400Regular', fontSize: 12, fontWeight: '400', lineHeight: 16 },
  button: { fontFamily: 'PlusJakartaSans_700Bold', fontSize: 16, fontWeight: '700', lineHeight: 24 },
  buttonSmall: { fontFamily: 'PlusJakartaSans_600SemiBold', fontSize: 14, fontWeight: '600', lineHeight: 20 },
  score: { fontFamily: 'PlusJakartaSans_700Bold', fontSize: 48, fontWeight: '700', lineHeight: 56, letterSpacing: -1 },
  emergency: { fontFamily: 'PlusJakartaSans_700Bold', fontSize: 20, fontWeight: '700', lineHeight: 28 },
} as const;

export type TypographyKey = keyof typeof typography;

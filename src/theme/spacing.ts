export const spacing = {
  xs: 4, sm: 8, md: 12, lg: 16, xl: 20, '2xl': 24, '3xl': 32,
  '4xl': 40, '5xl': 48, '6xl': 64, screen: 20,
} as const;

export const borderRadius = {
  sm: 8, md: 12, lg: 16, xl: 20, '2xl': 24, '3xl': 32, full: 9999,
} as const;

export const opacity = { disabled: 0.48, subtle: 0.72, overlay: 0.92 } as const;
export const touchTargets = { minimum: 44, comfortable: 48 } as const;

export const shadows = {
  sm: { shadowColor: '#212C28', shadowOffset: { width: 0, height: 1 }, shadowOpacity: 0.05, shadowRadius: 3, elevation: 1 },
  md: { shadowColor: '#212C28', shadowOffset: { width: 0, height: 3 }, shadowOpacity: 0.09, shadowRadius: 10, elevation: 3 },
  lg: { shadowColor: '#212C28', shadowOffset: { width: 0, height: 8 }, shadowOpacity: 0.12, shadowRadius: 20, elevation: 6 },
  xl: { shadowColor: '#212C28', shadowOffset: { width: 0, height: 12 }, shadowOpacity: 0.15, shadowRadius: 28, elevation: 8 },
  glow: { shadowColor: '#2D8A77', shadowOffset: { width: 0, height: 0 }, shadowOpacity: 0.45, shadowRadius: 10, elevation: 6 },
} as const;

export const mapOverlaySurface = {
  backgroundColor: 'rgba(255, 255, 255, 0.92)',
  borderColor: 'rgba(26, 107, 92, 0.12)',
  borderWidth: 1,
  borderRadius: borderRadius.xl,
  ...shadows.md,
} as const;

export const hitSlop = { top: 10, bottom: 10, left: 10, right: 10 } as const;

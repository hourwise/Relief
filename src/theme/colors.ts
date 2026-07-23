// ============================================================
// Project "Relief" — Color Palette
// Design System: Calm, Premium, Reassuring, Compassionate
// Inspired by Studio Ghibli warmth, watercolor textures
// ============================================================

export const colors = {
  // Brand
  background: '#F8FAFC',   // Off-white/Slate-50 (Main background)
  primary: '#0F766E',      // Deep Teal (Buttons, Headers)
  primaryLight: '#14B8A6', // Secondary Teal (Accents, Glows)
  success: '#10B981',      // Emerald (Open facilities)
  warning: '#F59E0B',      // Amber (Urgent/Closing soon)
  error: '#EF4444',        // Red (Closed/Broken)
  tealSoft: '#F0FDFA',     // Teal-50 (Icon backgrounds)

  // Neutrals
  white: '#FFFFFF',        // Card backgrounds
  black: '#0F172A',        // Slate-900
  gray50: '#F8FAFC',
  gray100: '#F1F5F9',
  gray200: '#E2E8F0',
  gray300: '#CBD5E1',
  gray400: '#94A3B8',
  gray500: '#64748B',      // Slate-500 (Body text)
  gray600: '#475569',
  gray700: '#334155',
  gray800: '#1E293B',
  gray900: '#0F172A',      // Slate-900 (Headings)

  // Semantic
  textPrimary: '#0F172A',  // Slate-900 (Headings)
  textSecondary: '#64748B', // Slate-500 (Body text)
  textMuted: '#94A3B8',
  textOnPrimary: '#FFFFFF',
  border: '#E2E8F0',
  borderLight: '#F1F5F9',
  cardBackground: '#FFFFFF',
  overlay: 'rgba(0, 0, 0, 0.5)',
  glassBackground: 'rgba(255, 255, 255, 0.8)', // Glassmorphism

  // Rating colors
  ratingHigh: '#10B981',
  ratingMedium: '#F59E0B',
  ratingLow: '#EF4444',

  // Map
  mapPinDefault: '#0F766E',
  mapPinSelected: '#14B8A6',
  mapPinAccessible: '#3B82F6',
  mapPinFamily: '#EC4899',
  mapCluster: '#0F766E',
  mapPinGlow: '#14B8A6',   // Glow color for pins
} as const;

export type ColorKey = keyof typeof colors;
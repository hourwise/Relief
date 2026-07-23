// ============================================================
// Project "Relief" — i18n Configuration
// Tagline: Find Comfort, Find Relief
// ============================================================

import i18n from 'i18next';
import { initReactI18next } from 'react-i18next';
import en from './en.json';

export const defaultNS = 'translation';
export const resources = {
  en: {
    translation: en,
  },
} as const;

i18n.use(initReactI18next).init({
  resources,
  lng: 'en',
  fallbackLng: 'en',
  ns: ['translation'],
  defaultNS: 'translation',
  interpolation: {
    escapeValue: false, // React already escapes by default
  },
  compatibilityJSON: 'v4',
});

export default i18n;
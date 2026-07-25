const googleMapsApiKey = process.env.EXPO_PUBLIC_GOOGLE_MAPS_API_KEY || '';
const supabaseUrl = process.env.EXPO_PUBLIC_SUPABASE_URL || '';
const supabaseAnonKey = process.env.EXPO_PUBLIC_SUPABASE_ANON_KEY || '';

module.exports = ({ config }) => ({
  ...config,
  android: {
    ...config.android,
    config: {
      ...config.android?.config,
      googleMaps: {
        ...config.android?.config?.googleMaps,
        apiKey: googleMapsApiKey,
      },
    },
  },
  plugins: [
    ...(config.plugins || []),
    [
      'expo-splash-screen',
      {
        backgroundColor: '#F3F8F5',
        image: './assets/branding/relief-splash-mark.png',
        imageWidth: 120,
        resizeMode: 'contain',
      },
    ],
    [
      'react-native-maps',
      {
        androidGoogleMapsApiKey: googleMapsApiKey,
      },
    ],
  ],
  extra: {
    ...config.extra,
    supabaseUrl,
    supabaseAnonKey,
  },
});

// ============================================================
// Project "Relief" — App Entry Point
// Tagline: Find Comfort, Find Relief
// Design: Studio Ghibli warmth, watercolor textures, soft edges
// ============================================================

import React from 'react';
import './src/i18n'; // Initialize i18n
import { StatusBar } from 'expo-status-bar';
import { GestureHandlerRootView } from 'react-native-gesture-handler';
import { SafeAreaProvider } from 'react-native-safe-area-context';
import { View, Text, StyleSheet, ActivityIndicator } from 'react-native';
import { AppNavigator } from './src/navigation/AppNavigator';
import { FiltersProvider } from './src/context/FiltersContext';
import { SubscriptionProvider } from './src/context/SubscriptionContext';
import { useAppFonts } from './src/hooks/useFonts';
import { colors, typography } from './src/theme';

export default function App() {
  const fontsLoaded = useAppFonts();

  if (!fontsLoaded) {
    return (
      <View style={styles.loadingContainer}>
        <Text style={styles.loadingText}>Relief</Text>
        <Text style={styles.tagline}>Find Comfort, Feel Relief</Text>
        <ActivityIndicator
          size="small"
          color={colors.primary}
          style={styles.loader}
        />
      </View>
    );
  }

  return (
    <GestureHandlerRootView style={styles.root}>
      <SafeAreaProvider>
        <FiltersProvider>
          <SubscriptionProvider>
            <StatusBar style="dark" />
            <AppNavigator />
          </SubscriptionProvider>
        </FiltersProvider>
      </SafeAreaProvider>
    </GestureHandlerRootView>
  );
}

const styles = StyleSheet.create({
  root: {
    flex: 1,
    backgroundColor: colors.background,
  },
  loadingContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    backgroundColor: colors.background,
  },
  loadingText: {
    fontFamily: 'PlusJakartaSans_700Bold',
    fontSize: 36,
    color: colors.primary,
    marginBottom: 4,
  },
  tagline: {
    fontFamily: 'Inter_400Regular',
    fontSize: 16,
    color: colors.textSecondary,
  },
  loader: {
    marginTop: 24,
  },
});
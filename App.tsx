import React, { useCallback, useState } from 'react';
import * as SplashScreen from 'expo-splash-screen';
import { StatusBar } from 'expo-status-bar';
import { View, StyleSheet } from 'react-native';
import { GestureHandlerRootView } from 'react-native-gesture-handler';
import { SafeAreaProvider } from 'react-native-safe-area-context';
import './src/i18n';
import { AppNavigator } from './src/navigation/AppNavigator';
import { FiltersProvider } from './src/context/FiltersContext';
import { SubscriptionProvider } from './src/context/SubscriptionContext';
import { useAppFonts } from './src/hooks/useFonts';
import { StartupWelcome } from './src/screens/StartupWelcome';
import { colors } from './src/theme';

// Keep the native surface visible until fonts and the first navigation decision
// are ready. This is intentionally called in module scope per Expo guidance.
SplashScreen.preventAutoHideAsync().catch(() => undefined);
SplashScreen.setOptions({ fade: true, duration: 220 });

export default function App() {
  const fontsLoaded = useAppFonts();
  const [startupResolved, setStartupResolved] = useState(false);
  const [welcomeFinished, setWelcomeFinished] = useState(false);

  const hideNativeSplash = useCallback(() => {
    if (fontsLoaded) SplashScreen.hideAsync().catch(() => undefined);
  }, [fontsLoaded]);

  const handleStartupResolved = useCallback(() => setStartupResolved(true), []);
  const handleWelcomeFinished = useCallback(() => setWelcomeFinished(true), []);

  if (!fontsLoaded) return null;

  return (
    <GestureHandlerRootView style={styles.root} onLayout={hideNativeSplash}>
      <SafeAreaProvider>
        <FiltersProvider>
          <SubscriptionProvider>
            <View style={styles.root}>
              <StatusBar style={welcomeFinished ? 'dark' : 'light'} />
              <AppNavigator onStartupResolved={handleStartupResolved} />
              {!welcomeFinished ? (
                <StartupWelcome startupReady={startupResolved} onFinished={handleWelcomeFinished} />
              ) : null}
            </View>
          </SubscriptionProvider>
        </FiltersProvider>
      </SafeAreaProvider>
    </GestureHandlerRootView>
  );
}

const styles = StyleSheet.create({ root: { flex: 1, backgroundColor: colors.mintSurface } });

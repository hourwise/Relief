// ============================================================
// Project "Relief" — App Navigator
// Tagline: Find Comfort, Find Relief
// ============================================================

import React, { useState, useEffect } from 'react';
import { NavigationContainer } from '@react-navigation/native';
import { createNativeStackNavigator } from '@react-navigation/native-stack';
import { createBottomTabNavigator } from '@react-navigation/bottom-tabs';
import { View, Text, StyleSheet } from 'react-native';
import { colors, typography } from '../theme';
import {
  LoginScreen,
  RegisterScreen,
  MapScreen,
  ListScreen,
  FacilityDetailScreen,
  ProfileScreen,
  AddFacilityScreen,
  ReportFacilityScreen,
  CorrectInfoScreen,
  AdvancedFiltersScreen,
  SavedProfilesScreen,
  FavouritesScreen,
  RoutePlanningScreen,
  OfflineMapsScreen,
  NotificationAlertsScreen,
  LocationSharingScreen,
  AIRecommendationsScreen,
  PredictiveSuggestionsScreen,
  OnboardingScreen,
  AboutReliefScreen,
} from '../screens';
import { hasCompletedOnboarding } from '../utils/onboarding';
import { onAuthStateChange, getCurrentSession } from '../services/auth';
import type {
  RootStackParamList,
  AuthStackParamList,
  MainTabParamList,
  MapStackParamList,
} from '../types';
import { Session } from '@supabase/supabase-js';

const RootStack = createNativeStackNavigator<RootStackParamList>();
const AuthStack = createNativeStackNavigator<AuthStackParamList>();
const Tab = createBottomTabNavigator<MainTabParamList>();
const MapStack = createNativeStackNavigator<MapStackParamList>();

// Simple tab icon component (replace with vector icons later)
const TabIcon: React.FC<{ label: string; focused: boolean }> = ({
  label,
  focused,
}) => {
  const icons: Record<string, string> = {
    Map: '🗺️',
    List: '📋',
    Favourites: '⭐',
    Profile: '👤',
  };
  return (
    <Text style={{ fontSize: 22, opacity: focused ? 1 : 0.5 }}>
      {icons[label] || '●'}
    </Text>
  );
};

// Map stack navigator (for Map -> FacilityDetail navigation)
const MapStackNavigator: React.FC = () => (
  <MapStack.Navigator screenOptions={{ headerShown: false }}>
    <MapStack.Screen name="MapView" component={MapScreen} />
    <MapStack.Screen
      name="FacilityDetail"
      component={FacilityDetailScreen}
      options={{ headerShown: false }}
    />
    <MapStack.Screen
      name="AddFacility"
      component={AddFacilityScreen}
      options={{
        headerShown: true,
        headerTitle: 'Add Facility',
        headerStyle: styles.header,
        headerTitleStyle: styles.headerTitle,
        headerTintColor: colors.textPrimary,
      }}
    />
    <MapStack.Screen
      name="ReportFacility"
      component={ReportFacilityScreen}
      options={{
        headerShown: true,
        headerTitle: 'Report Issue',
        headerStyle: styles.header,
        headerTitleStyle: styles.headerTitle,
        headerTintColor: colors.textPrimary,
      }}
    />
    <MapStack.Screen
      name="CorrectInfo"
      component={CorrectInfoScreen}
      options={{
        headerShown: true,
        headerTitle: 'Correct Info',
        headerStyle: styles.header,
        headerTitleStyle: styles.headerTitle,
        headerTintColor: colors.textPrimary,
      }}
    />
    <MapStack.Screen
      name="AdvancedFilters"
      component={AdvancedFiltersScreen}
      options={{ headerShown: false }}
    />
  </MapStack.Navigator>
);

// Auth Navigator
const AuthNavigator: React.FC = () => (
  <AuthStack.Navigator screenOptions={{ headerShown: false }}>
    <AuthStack.Screen name="Login" component={LoginScreen} />
    <AuthStack.Screen name="Register" component={RegisterScreen} />
  </AuthStack.Navigator>
);

// Main Tab Navigator
const MainNavigator: React.FC = () => (
  <Tab.Navigator
    screenOptions={({ route }) => ({
      tabBarIcon: ({ focused }) => (
        <TabIcon label={route.name} focused={focused} />
      ),
      tabBarActiveTintColor: colors.primary,
      tabBarInactiveTintColor: colors.gray400,
      tabBarStyle: styles.tabBar,
      tabBarLabelStyle: styles.tabBarLabel,
      headerStyle: styles.header,
      headerTitleStyle: styles.headerTitle,
      headerTintColor: colors.textPrimary,
    })}
  >
    <Tab.Screen
      name="Map"
      component={MapStackNavigator}
      options={{ title: 'Map', headerShown: false }}
    />
    <Tab.Screen
      name="List"
      component={ListScreen}
      options={{ title: 'Nearby' }}
    />
    <Tab.Screen
      name="Favourites"
      component={FavouritesScreen}
      options={{ title: 'Favourites' }}
    />
    <Tab.Screen
      name="Profile"
      component={ProfileScreen}
      options={{ title: 'Profile' }}
    />
  </Tab.Navigator>
);

const AuthenticatedEntry: React.FC<{ userId: string }> = ({ userId }) => {
  const [checkingOnboarding, setCheckingOnboarding] = useState(true);
  const [showOnboarding, setShowOnboarding] = useState(false);

  useEffect(() => {
    hasCompletedOnboarding(userId)
      .then((completed) => setShowOnboarding(!completed))
      .catch(() => setShowOnboarding(false))
      .finally(() => setCheckingOnboarding(false));
  }, [userId]);

  if (checkingOnboarding) return <View style={styles.loadingContainer} />;
  if (showOnboarding) return <OnboardingScreen userId={userId} onFinished={() => setShowOnboarding(false)} />;
  return <MainNavigator />;
};

// Root Navigator
interface AppNavigatorProps {
  onStartupResolved?: () => void;
}

export const AppNavigator: React.FC<AppNavigatorProps> = ({ onStartupResolved }) => {
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [userId, setUserId] = useState<string | null>(null);
  const [initializing, setInitializing] = useState(true);

  useEffect(() => {
    // Check for existing session on mount
    getCurrentSession()
      .then((session) => {
        setIsAuthenticated(!!session);
        setUserId(session?.user.id ?? null);
      })
      .finally(() => {
        setInitializing(false);
        onStartupResolved?.();
      });

    // Listen for auth state changes
    const subscription = onAuthStateChange((session) => {
      setIsAuthenticated(!!session);
      setUserId(session?.user.id ?? null);
    });

    return () => {
      subscription?.subscription.unsubscribe();
    };
  }, [onStartupResolved]);

  if (initializing) {
    return (
      <View style={styles.loadingContainer}>
        <Text style={styles.loadingText}>Relief</Text>
      </View>
    );
  }

  return (
    <NavigationContainer>
      <RootStack.Navigator screenOptions={{ headerShown: false }}>
        {isAuthenticated ? (
          <>
            <RootStack.Screen name="Main">
              {() => <AuthenticatedEntry userId={userId ?? 'authenticated'} />}
            </RootStack.Screen>
            <RootStack.Screen
              name="AIRecommendations"
              component={AIRecommendationsScreen}
              options={{
                headerShown: true,
                headerTitle: 'AI Recommendations',
                headerStyle: styles.header,
                headerTitleStyle: styles.headerTitle,
                headerTintColor: colors.textPrimary,
                presentation: 'modal',
              }}
            />
            <RootStack.Screen
              name="PredictiveSuggestions"
              component={PredictiveSuggestionsScreen}
              options={{
                headerShown: true,
                headerTitle: 'Predictive Suggestions',
                headerStyle: styles.header,
                headerTitleStyle: styles.headerTitle,
                headerTintColor: colors.textPrimary,
                presentation: 'modal',
              }}
            />
            <RootStack.Screen name="AboutRelief" component={AboutReliefScreen} options={{ headerShown: false }} />
          </>
        ) : (
          <RootStack.Screen name="Auth" component={AuthNavigator} />
        )}
      </RootStack.Navigator>
    </NavigationContainer>
  );
};

const styles = StyleSheet.create({
  tabBar: {
    backgroundColor: colors.white,
    borderTopColor: colors.border,
    borderTopWidth: 1,
    paddingTop: 4,
    height: 60,
  },
  tabBarLabel: {
    ...typography.caption,
    marginBottom: 4,
  },
  header: {
    backgroundColor: colors.background,
    shadowColor: 'transparent',
    elevation: 0,
  },
  headerTitle: {
    ...typography.h3,
    color: colors.textPrimary,
  },
  loadingContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    backgroundColor: colors.background,
  },
  loadingText: {
    ...typography.h1,
    color: colors.primary,
  },
});

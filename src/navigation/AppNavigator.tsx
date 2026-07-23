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
  PaywallScreen,
  AIRecommendationsScreen,
  PredictiveSuggestionsScreen,
} from '../screens';
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
      options={{
        headerShown: true,
        headerTitle: 'Facility Details',
        headerStyle: styles.header,
        headerTitleStyle: styles.headerTitle,
        headerTintColor: colors.textPrimary,
      }}
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
      options={{
        headerShown: true,
        headerTitle: 'Advanced Filters',
        headerStyle: styles.header,
        headerTitleStyle: styles.headerTitle,
        headerTintColor: colors.textPrimary,
      }}
    />
  </MapStack.Navigator>
);

// Auth Navigator
const AuthNavigator: React.FC = () => (
  <AuthStack.Navigator screenOptions={{ headerShown: false }}>
    <AuthStack.Screen name="Login" component={LoginScreen} />
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

// Root Navigator
export const AppNavigator: React.FC = () => {
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [initializing, setInitializing] = useState(true);

  useEffect(() => {
    // Check for existing session on mount
    getCurrentSession().then((session) => {
      setIsAuthenticated(!!session);
      setInitializing(false);
    });

    // Listen for auth state changes
    const subscription = onAuthStateChange((session) => {
      setIsAuthenticated(!!session);
    });

    return () => {
      subscription?.subscription.unsubscribe();
    };
  }, []);

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
            <RootStack.Screen name="Main" component={MainNavigator} />
            <RootStack.Screen
              name="Paywall"
              component={PaywallScreen}
              options={{
                headerShown: true,
                headerTitle: 'Upgrade',
                headerStyle: styles.header,
                headerTitleStyle: styles.headerTitle,
                headerTintColor: colors.textPrimary,
                presentation: 'modal',
              }}
            />
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
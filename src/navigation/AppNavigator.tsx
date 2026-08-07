// ============================================================
// Project "Relief" — App Navigator
// Tagline: Find Comfort, Find Relief
// ============================================================
// Discovery is NOT behind authentication. The root renders the
// main app whether or not a session exists; sign-in is a modal
// raised only when an account-dependent action is attempted.
//
// The previous structure rendered the Auth stack as the entire
// root for signed-out users, so nobody could reach the map or
// "Need One Now" without registering first.
// ============================================================

import React, { useCallback, useEffect, useMemo, useState } from 'react';
import { NavigationContainer } from '@react-navigation/native';
import { createNativeStackNavigator } from '@react-navigation/native-stack';
import { createBottomTabNavigator } from '@react-navigation/bottom-tabs';
import { View, Text, StyleSheet } from 'react-native';
import { Heart, Search, User } from 'lucide-react-native';
import { colors, typography } from '../theme';
import {
  LoginScreen,
  RegisterScreen,
  FindScreen,
  FacilityDetailScreen,
  ProfileScreen,
  AddFacilityScreen,
  ReportFacilityScreen,
  CorrectInfoScreen,
  AdvancedFiltersScreen,
  FavouritesScreen,
  OnboardingScreen,
  AboutReliefScreen,
} from '../screens';
import {
  hasCompletedOnboarding,
  GUEST_ONBOARDING_KEY,
  migrateGuestOnboarding,
} from '../utils/onboarding';
import { onAuthStateChange, getCurrentSession } from '../services/auth';
import { AuthContext } from '../context/AuthContext';
import type {
  RootStackParamList,
  AuthStackParamList,
  MainTabParamList,
  FindStackParamList,
} from '../types';

const RootStack = createNativeStackNavigator<RootStackParamList>();
const AuthStack = createNativeStackNavigator<AuthStackParamList>();
const Tab = createBottomTabNavigator<MainTabParamList>();
const FindStack = createNativeStackNavigator<FindStackParamList>();

const modalHeader = (title: string) => ({
  headerShown: true,
  headerTitle: title,
  headerStyle: styles.header,
  headerTitleStyle: styles.headerTitle,
  headerTintColor: colors.textPrimary,
});

/**
 * The Find tab's stack. Facility detail and the filter sheet are reachable
 * without a session; AddFacility, ReportFacility and CorrectInfo are registered
 * here but only ever navigated to after an auth check at the call site.
 */
const FindStackNavigator: React.FC = () => (
  <FindStack.Navigator screenOptions={{ headerShown: false }}>
    <FindStack.Screen name="FindHome" component={FindScreen} />
    <FindStack.Screen name="FacilityDetail" component={FacilityDetailScreen} />
    <FindStack.Screen
      name="AddFacility"
      component={AddFacilityScreen}
      options={modalHeader('Add Facility')}
    />
    <FindStack.Screen
      name="ReportFacility"
      component={ReportFacilityScreen}
      options={modalHeader('Report Issue')}
    />
    <FindStack.Screen
      name="CorrectInfo"
      component={CorrectInfoScreen}
      options={modalHeader('Correct Info')}
    />
    <FindStack.Screen
      name="AdvancedFilters"
      component={AdvancedFiltersScreen}
      options={{ headerShown: false }}
    />
  </FindStack.Navigator>
);

const AuthNavigator: React.FC = () => (
  <AuthStack.Navigator screenOptions={{ headerShown: false }}>
    <AuthStack.Screen name="Login" component={LoginScreen} />
    <AuthStack.Screen name="Register" component={RegisterScreen} />
  </AuthStack.Navigator>
);

/**
 * Three tabs, per the accessibility policy's maximum. "Nearby" is gone as a
 * separate tab because the list is now a view inside Find.
 */
const MainNavigator: React.FC = () => (
  <Tab.Navigator
    screenOptions={{
      tabBarActiveTintColor: colors.primary,
      tabBarInactiveTintColor: colors.gray400,
      tabBarStyle: styles.tabBar,
      tabBarLabelStyle: styles.tabBarLabel,
      headerStyle: styles.header,
      headerTitleStyle: styles.headerTitle,
      headerTintColor: colors.textPrimary,
    }}
  >
    <Tab.Screen
      name="Find"
      component={FindStackNavigator}
      options={{
        title: 'Find',
        headerShown: false,
        tabBarIcon: ({ color, size }) => <Search color={color} size={size} />,
      }}
    />
    <Tab.Screen
      name="Favourites"
      component={FavouritesScreen}
      options={{
        title: 'Favourites',
        tabBarIcon: ({ color, size }) => <Heart color={color} size={size} />,
      }}
    />
    <Tab.Screen
      name="Profile"
      component={ProfileScreen}
      options={{
        title: 'Profile',
        tabBarIcon: ({ color, size }) => <User color={color} size={size} />,
      }}
    />
  </Tab.Navigator>
);

/**
 * First-run preferences.
 *
 * Onboarding is stored against a guest key when there is no session, so it does
 * not force account creation before discovery. On sign-in the guest record is
 * migrated to the user, so a guest who later registers is not asked twice.
 */
const MainEntry: React.FC<{ userId: string | null }> = ({ userId }) => {
  const storageKey = userId ?? GUEST_ONBOARDING_KEY;
  const [checking, setChecking] = useState(true);
  const [showOnboarding, setShowOnboarding] = useState(false);

  useEffect(() => {
    let cancelled = false;

    // The migration is awaited HERE, immediately before the check, rather than
    // being fired from the auth listener. Doing it there raced this effect: the
    // new user id arrived, this re-ran under the user's key, and found nothing
    // written yet — so a guest who had already completed onboarding was asked
    // again the moment they signed in. Owning both steps in one place removes
    // any dependence on which callback happens to run first.
    (async () => {
      try {
        if (userId) await migrateGuestOnboarding(userId);
        const completed = await hasCompletedOnboarding(storageKey);
        if (!cancelled) setShowOnboarding(!completed);
      } catch {
        // Never block discovery because storage failed.
        if (!cancelled) setShowOnboarding(false);
      } finally {
        if (!cancelled) setChecking(false);
      }
    })();

    return () => {
      cancelled = true;
    };
  }, [storageKey, userId]);

  if (checking) return <View style={styles.loadingContainer} />;

  if (showOnboarding) {
    return (
      <OnboardingScreen
        storageKey={storageKey}
        onFinished={() => setShowOnboarding(false)}
      />
    );
  }

  return <MainNavigator />;
};

interface AppNavigatorProps {
  onStartupResolved?: () => void;
}

export const AppNavigator: React.FC<AppNavigatorProps> = ({ onStartupResolved }) => {
  const [userId, setUserId] = useState<string | null>(null);
  const [initializing, setInitializing] = useState(true);

  useEffect(() => {
    getCurrentSession()
      .then((session) => setUserId(session?.user.id ?? null))
      .catch(() => setUserId(null))
      .finally(() => {
        setInitializing(false);
        onStartupResolved?.();
      });

    // Migration is deliberately NOT done here — MainEntry awaits it before
    // checking onboarding, so there is no ordering race between the two.
    const subscription = onAuthStateChange((session) => {
      setUserId(session?.user.id ?? null);
    });

    return () => subscription?.subscription.unsubscribe();
  }, [onStartupResolved]);

  const authValue = useMemo(
    () => ({ userId, isAuthenticated: userId !== null }),
    [userId],
  );

  if (initializing) {
    return (
      <View style={styles.loadingContainer}>
        <Text style={styles.loadingText}>Relief</Text>
      </View>
    );
  }

  return (
    <AuthContext.Provider value={authValue}>
      <NavigationContainer>
        <RootStack.Navigator screenOptions={{ headerShown: false }}>
          {/* Always available, session or not. */}
          <RootStack.Screen name="Main">
            {() => <MainEntry userId={userId} />}
          </RootStack.Screen>
          {/* Raised on demand for account-dependent actions only. */}
          <RootStack.Screen
            name="Auth"
            component={AuthNavigator}
            options={{ presentation: 'modal' }}
          />
          <RootStack.Screen name="AboutRelief" component={AboutReliefScreen} />
        </RootStack.Navigator>
      </NavigationContainer>
    </AuthContext.Provider>
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

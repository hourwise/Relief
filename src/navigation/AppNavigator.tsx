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

import React, { useEffect, useMemo, useRef, useState } from 'react';
import { NavigationContainer } from '@react-navigation/native';
import { createNativeStackNavigator } from '@react-navigation/native-stack';
import { createBottomTabNavigator } from '@react-navigation/bottom-tabs';
import { View, StyleSheet } from 'react-native';
import { Home as HomeIcon, Search, User } from 'lucide-react-native';
import { colors, typography } from '../theme';
import {
  LoginScreen,
  RegisterScreen,
  HomeScreen,
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
  ForgotPasswordScreen,
  UpdatePasswordScreen,
  AccountDeletionScreen,
  PhotoFlowScreen,
  LegalInfoScreen,
  FeatureLabScreen,
  SavedProfilesScreen,
  RoutePlanningScreen,
  OfflineMapsScreen,
  NotificationAlertsScreen,
  PaywallScreen,
  AIRecommendationsScreen,
  PredictiveSuggestionsScreen,
} from '../screens';
import {
  hasCompletedOnboarding,
  GUEST_ONBOARDING_KEY,
  migrateGuestOnboarding,
} from '../utils/onboarding';
import { onAuthStateChange, getCurrentSession } from '../services/auth';
import { AuthContext } from '../context/AuthContext';
import { HandoffProvider, useHandoff } from '../context/HandoffContext';
import { BrandedHandoff } from '../components';
import { APP_SCHEME, RELIEF_TEST_MODE } from '../utils/env';
import type {
  RootStackParamList,
  AuthStackParamList,
  MainTabParamList,
  HomeStackParamList,
  FindStackParamList,
} from '../types';

const RootStack = createNativeStackNavigator<RootStackParamList>();
const AuthStack = createNativeStackNavigator<AuthStackParamList>();
const Tab = createBottomTabNavigator<MainTabParamList>();
const HomeStack = createNativeStackNavigator<HomeStackParamList>();
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
    <AuthStack.Screen name="ForgotPassword" component={ForgotPasswordScreen} />
    <AuthStack.Screen name="UpdatePassword" component={UpdatePasswordScreen} />
  </AuthStack.Navigator>
);

const HomeStackNavigator: React.FC = () => (
  <HomeStack.Navigator screenOptions={{ headerShown: false }}>
    <HomeStack.Screen name="HomeMain" component={HomeScreen} />
    <HomeStack.Screen
      name="Favourites"
      component={FavouritesScreen}
      options={{
        headerShown: true,
        title: 'Saved places',
        headerStyle: styles.header,
        headerTitleStyle: styles.headerTitle,
        headerTintColor: colors.textPrimary,
      }}
    />
  </HomeStack.Navigator>
);

/**
 * Three tabs, per the accessibility policy's maximum. "Nearby" is gone as a
 * separate tab because the list is now a view inside Find.
 */
const MainNavigator: React.FC = () => (
  <Tab.Navigator
    initialRouteName="Home"
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
      name="Home"
      component={HomeStackNavigator}
      options={{
        title: 'Home',
        headerShown: false,
        tabBarIcon: ({ color, size }) => <HomeIcon color={color} size={size} />,
      }}
    />
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
  const { reportAppReady } = useHandoff();
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
        if (!cancelled) {
          const onboardingRequired = !completed;
          setShowOnboarding(onboardingRequired);

          // The root app must own startup readiness. Find is a lazy tab and may
          // not be mounted yet, so the initial handoff cannot wait for it.
          if (onboardingRequired) reportAppReady();
        }
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
  }, [reportAppReady, storageKey, userId]);

  // Release the root handoff once the entry decision has settled. This also
  // handles a sign-in while the user is on Home: Find remains lazy and must
  // never be required just to reveal the already-mounted app.
  useEffect(() => {
    if (!checking) reportAppReady();
  }, [checking, reportAppReady, userId]);

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

const AppNavigatorInner: React.FC<AppNavigatorProps> = ({ onStartupResolved }) => {
  const { beginSignInHandoff, reason, isActive, dismissed, markDismissed } = useHandoff();
  const startupResolvedRef = useRef(false);
  const onSignedIn = beginSignInHandoff;
  const [userId, setUserId] = useState<string | null>(null);
  const [initializing, setInitializing] = useState(true);

  useEffect(() => {
    getCurrentSession()
      .then((session) => setUserId(session?.user.id ?? null))
      .catch(() => setUserId(null))
      .finally(() => {
        setInitializing(false);
        startupResolvedRef.current = true;
        onStartupResolved?.();
      });

    // Migration is deliberately NOT done here — MainEntry awaits it before
    // checking onboarding, so there is no ordering race between the two.
    const subscription = onAuthStateChange((session) => {
      const next = session?.user.id ?? null;
      setUserId((previous) => {
        // A genuine sign-in is null -> id AFTER startup has resolved. Restoring
        // an existing session on launch is not a sign-in, and signing OUT must
        // never produce a "welcome" transition.
        if (previous === null && next !== null && startupResolvedRef.current) {
          onSignedIn();
        }
        return next;
      });
    });

    return () => subscription?.subscription.unsubscribe();
  }, [onSignedIn, onStartupResolved]);

  const authValue = useMemo(
    () => ({ userId, isAuthenticated: userId !== null }),
    [userId],
  );

  // No plain "Relief" text screen any more: the branded handoff covers this
  // window, so cold start is one continuous Relief moment instead of a bare
  // word followed by a splash followed by a map.
  if (initializing) {
    return <BrandedHandoff status="Preparing Relief…" visible onFadedOut={() => {}} />;
  }

  return (
    <AuthContext.Provider value={authValue}>
      <NavigationContainer
        linking={{
          prefixes: [`${APP_SCHEME}://`],
          config: { screens: { Auth: { screens: { UpdatePassword: 'auth/callback' } } } },
        } as never}
      >
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
          {RELIEF_TEST_MODE ? <RootStack.Screen name="FeatureLab" component={FeatureLabScreen} options={modalHeader('Feature Lab')} /> : null}
          <RootStack.Screen name="AccountDeletion" component={AccountDeletionScreen} options={modalHeader('Delete account')} />
          <RootStack.Screen name="PhotoFlow" component={PhotoFlowScreen} options={modalHeader('Photo contribution')} />
          <RootStack.Screen name="LegalInfo" component={LegalInfoScreen} options={modalHeader('Legal and support')} />
          <RootStack.Screen name="SavedProfiles" component={SavedProfilesScreen} options={modalHeader('Saved profiles')} />
          <RootStack.Screen name="RoutePlanning" component={RoutePlanningScreen} options={modalHeader('Route planning')} />
          <RootStack.Screen name="OfflineMaps" component={OfflineMapsScreen} options={modalHeader('Offline facility data')} />
          <RootStack.Screen name="NotificationAlerts" component={NotificationAlertsScreen} options={modalHeader('Alerts')} />
          <RootStack.Screen name="Paywall" component={PaywallScreen} options={modalHeader('Relief Plus')} />
          <RootStack.Screen name="AIRecommendations" component={AIRecommendationsScreen} options={modalHeader('Recommendations')} />
          <RootStack.Screen name="PredictiveSuggestions" component={PredictiveSuggestionsScreen} options={modalHeader('Suggestions')} />
        </RootStack.Navigator>
      </NavigationContainer>

      {/* One overlay for both cold start and sign-in, above the navigator so a
          modal auth flow cannot hide it and Main staying mounted cannot stop it
          replaying. */}
      {!dismissed && reason ? (
        <BrandedHandoff
          status={reason === 'sign-in' ? 'Welcome back…' : 'Finding nearby facilities…'}
          visible={isActive}
          onFadedOut={markDismissed}
        />
      ) : null}
    </AuthContext.Provider>
  );
};

export const AppNavigator: React.FC<AppNavigatorProps> = (props) => (
  <HandoffProvider>
    <AppNavigatorInner {...props} />
  </HandoffProvider>
);

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

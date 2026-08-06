// ============================================================
// Project "Relief" — Auth state and the sign-in gate
// ============================================================
// Screens ask "may this user do X?" instead of "is there a
// session?", so the guest policy lives in one place
// (src/utils/guestAccess.ts) and every gated action behaves the
// same way: explain why, offer sign-in, and never dead-end.
// ============================================================

import React, { createContext, useCallback, useContext } from 'react';
import { Alert } from 'react-native';
import { useNavigation } from '@react-navigation/native';
import type { NavigationProp } from '@react-navigation/native';
import { resolveAction, signInReason, type AppAction } from '../utils/guestAccess';
import type { RootStackParamList } from '../types';

interface AuthContextValue {
  userId: string | null;
  isAuthenticated: boolean;
}

export const AuthContext = createContext<AuthContextValue>({
  userId: null,
  isAuthenticated: false,
});

export const useAuth = () => useContext(AuthContext);

/**
 * Returns a guard for account-dependent actions.
 *
 * `run(action, onAllowed)` performs the action when it is permitted, and
 * otherwise prompts the guest to sign in with the reason for the request.
 * Returns whether the action was allowed, so callers can also branch on it.
 */
export function useAuthGate() {
  const { isAuthenticated } = useAuth();
  const navigation = useNavigation<NavigationProp<RootStackParamList>>();

  const promptSignIn = useCallback(
    (action: AppAction) => {
      const reason = signInReason(action);
      Alert.alert('Sign in required', reason, [
        { text: 'Not now', style: 'cancel' },
        {
          text: 'Sign in',
          onPress: () => navigation.navigate('Auth', { reason }),
        },
      ]);
    },
    [navigation],
  );

  const run = useCallback(
    (action: AppAction, onAllowed: () => void): boolean => {
      if (resolveAction(action, isAuthenticated) === 'allow') {
        onAllowed();
        return true;
      }
      promptSignIn(action);
      return false;
    },
    [isAuthenticated, promptSignIn],
  );

  return { isAuthenticated, run, promptSignIn };
}

// ============================================================
// Project "Relief" — Login Screen
// Tagline: Find Comfort, Find Relief
// ============================================================

import React, { useEffect, useState } from 'react';
import {
  View,
  Text,
  StyleSheet,
  KeyboardAvoidingView,
  Platform,
  ScrollView,
  Alert,
  TouchableOpacity,
} from 'react-native';
import { useNavigation, useRoute } from '@react-navigation/native';
import type { RouteProp } from '@react-navigation/native';
import { NativeStackNavigationProp } from '@react-navigation/native-stack';
import { colors, typography, spacing, touchTargets } from '../theme';
import { Button, Input, Card } from '../components';
import { signInWithEmail, signInWithGoogle } from '../services/auth';
import { useAuth } from '../context/AuthContext';
import type { AuthStackParamList } from '../types';

type LoginScreenNavProp = NativeStackNavigationProp<
  AuthStackParamList,
  'Login'
>;

export const LoginScreen: React.FC = () => {
  const navigation = useNavigation<LoginScreenNavProp>();
  const route = useRoute<RouteProp<AuthStackParamList, 'Login'>>();
  const { isAuthenticated } = useAuth();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [loading, setLoading] = useState(false);

  // This screen is a modal raised over the app, not a gate in front of it.
  // Once a session exists its job is done, so it closes itself and returns the
  // user to whatever they were doing.
  useEffect(() => {
    if (isAuthenticated && navigation.canGoBack()) navigation.goBack();
  }, [isAuthenticated, navigation]);

  const handleEmailLogin = async () => {
    if (!email.trim() || !password.trim()) {
      Alert.alert('Error', 'Please enter your email and password');
      return;
    }
    setLoading(true);
    const { error } = await signInWithEmail(email.trim(), password);
    if (error) {
      Alert.alert('Sign In Failed', error.message);
    }
    setLoading(false);
  };

  const handleGoogleLogin = async () => {
    setLoading(true);
    const { error } = await signInWithGoogle();
    if (error) {
      Alert.alert('Google Sign In Failed', error.message);
    }
    setLoading(false);
  };

  return (
    <KeyboardAvoidingView
      style={styles.container}
      behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
    >
      <ScrollView
        contentContainerStyle={styles.scrollContent}
        keyboardShouldPersistTaps="handled"
      >
        <View style={styles.header}>
          <Text style={styles.appName}>Relief</Text>
          <Text style={styles.tagline}>
            Find Comfort, Find Relief
          </Text>
        </View>

        <Card variant="elevated" style={styles.card}>
          <Text style={styles.cardTitle}>Sign In</Text>

          {/* Why we are asking. A guest who arrived here from a specific action
              should not have to guess what triggered it. */}
          {route.params?.reason ? (
            <Text style={styles.reason}>{route.params.reason}</Text>
          ) : null}

          <Input
            label="Email"
            placeholder="your@email.com"
            value={email}
            onChangeText={setEmail}
            keyboardType="email-address"
            autoCapitalize="none"
            autoComplete="email"
          />

          <Input
            label="Password"
            placeholder="Enter your password"
            value={password}
            onChangeText={setPassword}
            secureTextEntry
            autoCapitalize="none"
          />

          <Button
            title="Sign In"
            onPress={handleEmailLogin}
            loading={loading}
            fullWidth
            size="lg"
          />

          <View style={styles.divider}>
            <View style={styles.dividerLine} />
            <Text style={styles.dividerText}>or continue with</Text>
            <View style={styles.dividerLine} />
          </View>

          <Button
            title="Continue with Google"
            onPress={handleGoogleLogin}
            variant="outline"
            fullWidth
            style={styles.socialButton}
          />

          {Platform.OS === 'ios' && (
            <Button
              title="Continue with Apple"
              onPress={() => {}}
              variant="outline"
              fullWidth
              style={styles.socialButton}
              disabled
            />
          )}
        </Card>

        <TouchableOpacity
          style={styles.signupLink}
          onPress={() => navigation.navigate('Register')}
        >
          <Text style={styles.signupLinkText}>
            {"Don't have an account? "}
            <Text style={styles.signupLinkBold}>Sign Up</Text>
          </Text>
        </TouchableOpacity>

        {/* Signing in is always optional: finding a facility does not need an
            account, so there must be a way back out. */}
        {navigation.canGoBack() ? (
          <TouchableOpacity
            accessibilityRole="button"
            accessibilityLabel="Continue without an account"
            style={styles.guestLink}
            onPress={() => navigation.goBack()}
          >
            <Text style={styles.guestLinkText}>Continue without an account</Text>
          </TouchableOpacity>
        ) : null}
      </ScrollView>
    </KeyboardAvoidingView>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: colors.background,
  },
  scrollContent: {
    flexGrow: 1,
    justifyContent: 'center',
    padding: spacing.xl,
  },
  header: {
    alignItems: 'center',
    marginBottom: spacing['3xl'],
  },
  appName: {
    ...typography.h1,
    color: colors.primary,
    marginBottom: spacing.sm,
  },
  tagline: {
    ...typography.body,
    color: colors.textSecondary,
    textAlign: 'center',
  },
  card: {
    width: '100%',
  },
  cardTitle: {
    ...typography.h3,
    color: colors.textPrimary,
    marginBottom: spacing.xl,
  },
  reason: {
    ...typography.bodySmall,
    color: colors.textSecondary,
    marginTop: -spacing.md,
    marginBottom: spacing.xl,
    lineHeight: 21,
  },
  divider: {
    flexDirection: 'row',
    alignItems: 'center',
    marginVertical: spacing.xl,
  },
  dividerLine: {
    flex: 1,
    height: 1,
    backgroundColor: colors.border,
  },
  dividerText: {
    ...typography.caption,
    color: colors.textMuted,
    marginHorizontal: spacing.md,
  },
  socialButton: {
    marginBottom: spacing.md,
  },
  signupLink: {
    marginTop: spacing.xl,
    alignItems: 'center',
  },
  signupLinkText: {
    ...typography.body,
    color: colors.textSecondary,
  },
  signupLinkBold: {
    color: colors.primary,
    fontWeight: '600',
  },
  guestLink: {
    minHeight: touchTargets.minimum,
    alignItems: 'center',
    justifyContent: 'center',
    marginTop: spacing.md,
  },
  guestLinkText: {
    ...typography.buttonSmall,
    color: colors.textSecondary,
  },
});
// ============================================================
// Project "Relief" — Register Screen
// Tagline: Find Comfort, Find Relief
// ============================================================

import React, { useState } from 'react';
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
import { useNavigation } from '@react-navigation/native';
import { NativeStackNavigationProp } from '@react-navigation/native-stack';
import { colors, typography, spacing } from '../theme';
import { Button, Input, Card } from '../components';
import { signUpWithEmail } from '../services/auth';
import {
  describeAuthError,
  isPlausibleEmail,
  MIN_PASSWORD_LENGTH,
} from '../utils/authErrors';
import type { AuthStackParamList } from '../types';

type RegisterScreenNavProp = NativeStackNavigationProp<
  AuthStackParamList,
  'Register'
>;

export const RegisterScreen: React.FC = () => {
  const navigation = useNavigation<RegisterScreenNavProp>();
  const [name, setName] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [loading, setLoading] = useState(false);

  const handleRegister = async () => {
    if (!name.trim()) {
      Alert.alert('Almost there', 'Please enter your name.');
      return;
    }
    if (!isPlausibleEmail(email)) {
      Alert.alert('Check your email', 'That email address does not look valid.');
      return;
    }
    if (password.length < MIN_PASSWORD_LENGTH) {
      Alert.alert(
        'Choose a longer password',
        `Please use at least ${MIN_PASSWORD_LENGTH} characters.`,
      );
      return;
    }
    if (password !== confirmPassword) {
      Alert.alert('Passwords do not match', 'Please re-enter the same password.');
      return;
    }

    setLoading(true);
    const { data, error } = await signUpWithEmail(
      email.trim(),
      password,
      name.trim(),
    );
    setLoading(false);

    if (error) {
      Alert.alert('Could not create account', describeAuthError(error, 'sign_up'));
      return;
    }

    // The outcome is read from the response rather than assumed. This screen
    // used to claim a confirmation email had been sent no matter what, which
    // would be a lie if the project ever enables auto-confirm — the user would
    // sit waiting for an email that was never going to arrive.
    if (data?.session) {
      // Already signed in; the auth listener closes this stack.
      return;
    }

    Alert.alert(
      'Check your email',
      `We have sent a confirmation link to ${email.trim()}. Open it to finish creating your account, then come back and sign in.`,
      [{ text: 'OK', onPress: () => navigation.goBack() }],
    );
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
          <Text style={styles.cardTitle}>Create Account</Text>

          <Input
            label="Name"
            placeholder="Your name"
            value={name}
            onChangeText={setName}
            autoCapitalize="words"
            autoComplete="name"
          />

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
            placeholder="At least 6 characters"
            value={password}
            onChangeText={setPassword}
            secureTextEntry
            autoCapitalize="none"
          />

          <Input
            label="Confirm Password"
            placeholder="Re-enter your password"
            value={confirmPassword}
            onChangeText={setConfirmPassword}
            secureTextEntry
            autoCapitalize="none"
          />

          <Button
            title="Create Account"
            onPress={handleRegister}
            loading={loading}
            fullWidth
            size="lg"
          />
        </Card>

        <TouchableOpacity
          style={styles.loginLink}
          onPress={() => navigation.goBack()}
        >
          <Text style={styles.loginLinkText}>
            Already have an account?{' '}
            <Text style={styles.loginLinkBold}>Sign In</Text>
          </Text>
        </TouchableOpacity>
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
  loginLink: {
    marginTop: spacing.xl,
    alignItems: 'center',
  },
  loginLinkText: {
    ...typography.body,
    color: colors.textSecondary,
  },
  loginLinkBold: {
    color: colors.primary,
    fontWeight: '600',
  },
});

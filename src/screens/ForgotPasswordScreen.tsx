import React, { useState } from 'react';
import { KeyboardAvoidingView, Platform, ScrollView, StyleSheet, Text, TouchableOpacity } from 'react-native';
import { useNavigation } from '@react-navigation/native';
import type { NativeStackNavigationProp } from '@react-navigation/native-stack';
import { Button, Card, Input } from '../components';
import { colors, spacing, touchTargets, typography } from '../theme';
import { requestPasswordReset } from '../services/auth';
import { describeAuthError, isPlausibleEmail } from '../utils/authErrors';
import type { AuthStackParamList } from '../types';

type Navigation = NativeStackNavigationProp<AuthStackParamList, 'ForgotPassword'>;

export const ForgotPasswordScreen: React.FC = () => {
  const navigation = useNavigation<Navigation>();
  const [email, setEmail] = useState('');
  const [loading, setLoading] = useState(false);
  const [sent, setSent] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const submit = async () => {
    setError(null);
    if (!isPlausibleEmail(email)) {
      setError('Enter a valid email address.');
      return;
    }
    setLoading(true);
    const result = await requestPasswordReset(email.trim());
    setLoading(false);
    if (result.error) {
      setError(describeAuthError(result.error, 'password_reset'));
      return;
    }
    setSent(true);
  };

  return (
    <KeyboardAvoidingView style={styles.container} behavior={Platform.OS === 'ios' ? 'padding' : 'height'}>
      <ScrollView contentContainerStyle={styles.content} keyboardShouldPersistTaps="handled">
        <Text style={styles.title}>Reset your password</Text>
        <Text style={styles.subtitle}>Enter your email and we’ll send a secure recovery link if an account matches.</Text>
        <Card variant="elevated" style={styles.card}>
          {sent ? (
            <>
              <Text style={styles.cardTitle}>Check your email</Text>
              <Text style={styles.body}>If an account exists for that address, a password-reset link is on its way. Open it on this device to choose a new password.</Text>
              <Button title="Back to sign in" onPress={() => navigation.navigate('Login')} fullWidth size="lg" />
            </>
          ) : (
            <>
              <Text style={styles.cardTitle}>Password recovery</Text>
              <Input label="Email" placeholder="your@email.com" value={email} onChangeText={setEmail} keyboardType="email-address" autoCapitalize="none" autoComplete="email" error={error || undefined} />
              <Button title="Send reset link" onPress={submit} loading={loading} fullWidth size="lg" />
            </>
          )}
        </Card>
        {!sent ? <TouchableOpacity style={styles.backLink} onPress={() => navigation.navigate('Login')}><Text style={styles.backText}>Back to sign in</Text></TouchableOpacity> : null}
      </ScrollView>
    </KeyboardAvoidingView>
  );
};

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: colors.background },
  content: { flexGrow: 1, justifyContent: 'center', padding: spacing.xl },
  title: { ...typography.h1, color: colors.textPrimary, textAlign: 'center' },
  subtitle: { ...typography.body, color: colors.textSecondary, textAlign: 'center', lineHeight: 22, marginTop: spacing.sm, marginBottom: spacing.xl },
  card: { width: '100%' },
  cardTitle: { ...typography.h3, color: colors.textPrimary, marginBottom: spacing.lg },
  body: { ...typography.body, color: colors.textSecondary, lineHeight: 23, marginBottom: spacing.xl },
  backLink: { alignSelf: 'center', minHeight: touchTargets.minimum, justifyContent: 'center', marginTop: spacing.md },
  backText: { ...typography.buttonSmall, color: colors.primary },
});

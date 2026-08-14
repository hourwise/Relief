import React, { useEffect, useState } from 'react';
import { KeyboardAvoidingView, Platform, ScrollView, StyleSheet, Text } from 'react-native';
import { useNavigation } from '@react-navigation/native';
import type { NativeStackNavigationProp } from '@react-navigation/native-stack';
import { Button, Card, Input } from '../components';
import { colors, spacing, typography } from '../theme';
import { getCurrentSession, subscribeToPasswordRecovery, updatePassword } from '../services/auth';
import { describeAuthError } from '../utils/authErrors';
import type { AuthStackParamList } from '../types';

type Navigation = NativeStackNavigationProp<AuthStackParamList, 'UpdatePassword'>;

export const UpdatePasswordScreen: React.FC = () => {
  const navigation = useNavigation<Navigation>();
  const [ready, setReady] = useState(false);
  const [expired, setExpired] = useState(false);
  const [password, setPassword] = useState('');
  const [confirm, setConfirm] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let mounted = true;
    getCurrentSession().then((session) => {
      if (mounted && session) setReady(true);
    }).catch(() => undefined);
    const subscription = subscribeToPasswordRecovery((valid) => {
      if (mounted && valid) { setReady(true); setExpired(false); }
    });
    const timeout = setTimeout(() => { if (mounted) setExpired((current) => !current && !ready); }, 1500);
    return () => { mounted = false; clearTimeout(timeout); subscription.unsubscribe(); };
  }, [ready]);

  const submit = async () => {
    setError(null);
    if (password.length < 6) { setError('Use at least 6 characters.'); return; }
    if (password !== confirm) { setError('Passwords do not match.'); return; }
    setLoading(true);
    const result = await updatePassword(password);
    setLoading(false);
    if (result.error) { setError(describeAuthError(result.error, 'password_update')); return; }
    navigation.navigate('Login');
  };

  return (
    <KeyboardAvoidingView style={styles.container} behavior={Platform.OS === 'ios' ? 'padding' : 'height'}>
      <ScrollView contentContainerStyle={styles.content} keyboardShouldPersistTaps="handled">
        <Card variant="elevated" style={styles.card}>
          <Text style={styles.title}>{expired && !ready ? 'Recovery link unavailable' : 'Choose a new password'}</Text>
          {expired && !ready ? <Text style={styles.body}>This recovery link is missing or has expired. Return to sign in and request a new link.</Text> : <>
            <Text style={styles.body}>Choose a new password for your Relief account.</Text>
            <Input label="New password" value={password} onChangeText={setPassword} secureTextEntry autoCapitalize="none" error={error || undefined} />
            <Input label="Confirm password" value={confirm} onChangeText={setConfirm} secureTextEntry autoCapitalize="none" />
            <Button title="Update password" onPress={submit} loading={loading} fullWidth size="lg" />
          </>}
          {expired && !ready ? <Button title="Back to sign in" onPress={() => navigation.navigate('Login')} variant="outline" fullWidth /> : null}
        </Card>
      </ScrollView>
    </KeyboardAvoidingView>
  );
};

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: colors.background },
  content: { flexGrow: 1, justifyContent: 'center', padding: spacing.xl },
  card: { width: '100%' },
  title: { ...typography.h3, color: colors.textPrimary, marginBottom: spacing.md },
  body: { ...typography.body, color: colors.textSecondary, lineHeight: 23, marginBottom: spacing.xl },
});

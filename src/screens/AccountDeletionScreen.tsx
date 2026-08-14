import React, { useState } from 'react';
import { Alert, ScrollView, StyleSheet, Text } from 'react-native';
import { useNavigation } from '@react-navigation/native';
import type { NativeStackNavigationProp } from '@react-navigation/native-stack';
import { Button, Input, ScreenBackground, SoftCard } from '../components';
import { colors, spacing, typography } from '../theme';
import { requestAccountDeletion } from '../services/accountDeletion';
import { useAuth } from '../context/AuthContext';
import { RELIEF_TEST_MODE } from '../utils/env';
import type { RootStackParamList } from '../types';

type Navigation = NativeStackNavigationProp<RootStackParamList, 'AccountDeletion'>;

export const AccountDeletionScreen: React.FC = () => {
  const navigation = useNavigation<Navigation>();
  const { isAuthenticated } = useAuth();
  const [confirmation, setConfirmation] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const submit = () => {
    Alert.alert(
      'Confirm account request',
      'This is the final confirmation step. Continue only if you intend to request account deletion.',
      [
        { text: 'Cancel', style: 'cancel' },
        {
          text: 'Confirm request',
          style: 'destructive',
          onPress: async () => {
            setError(null);
            setLoading(true);
            const result = await requestAccountDeletion(confirmation);
            setLoading(false);
            if (!result.success) { setError(result.error); return; }
            Alert.alert(RELIEF_TEST_MODE ? 'Request simulated' : 'Account deletion complete', result.message, [{ text: 'Done', onPress: navigation.goBack }]);
          },
        },
      ],
    );
  };

  return (
    <ScreenBackground>
      <ScrollView contentContainerStyle={styles.content}>
        <SoftCard style={styles.card}>
          <Text style={styles.title}>Delete your account</Text>
          <Text style={styles.body}>This is a permanent account request. Review any saved places and community contributions before continuing.</Text>
          <Text style={styles.body}>{RELIEF_TEST_MODE ? 'Test mode simulates the request only.' : 'Relief sends this request to a server-governed deletion path. The backend must be deployed and configured before this build can complete it.'}</Text>
          {!isAuthenticated ? <Text style={styles.warning}>Sign in is required to request account deletion.</Text> : null}
          <Input label="Type DELETE MY ACCOUNT to confirm" value={confirmation} onChangeText={setConfirmation} autoCapitalize="characters" error={error || undefined} />
          <Button title={RELIEF_TEST_MODE ? 'Simulate deletion request' : 'Request account deletion'} onPress={submit} loading={loading} disabled={!isAuthenticated} fullWidth />
          {!RELIEF_TEST_MODE ? <Text style={styles.note}>Deletion is transactional for current app data. Storage cleanup and Auth deletion are handled by the trusted backend; failures are reported for retry.</Text> : null}
        </SoftCard>
      </ScrollView>
    </ScreenBackground>
  );
};

const styles = StyleSheet.create({
  content: { padding: spacing.lg, paddingBottom: spacing['6xl'] },
  card: { marginTop: spacing.lg },
  title: { ...typography.h2, color: colors.textPrimary, marginBottom: spacing.md },
  body: { ...typography.body, color: colors.textSecondary, lineHeight: 23, marginBottom: spacing.md },
  warning: { ...typography.bodySmall, color: colors.warning, marginBottom: spacing.md },
  note: { ...typography.caption, color: colors.textSecondary, lineHeight: 19, marginTop: spacing.md },
});

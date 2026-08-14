import React, { useState } from 'react';
import { ScrollView, StyleSheet, Text } from 'react-native';
import { Button, ScreenBackground, SoftCard } from '../components';
import { getPhotoStorageAdapter } from '../services/photoStorage';
import { RELIEF_TEST_MODE } from '../utils/env';
import { colors, spacing, typography } from '../theme';

export const PhotoFlowScreen: React.FC = () => {
  const [status, setStatus] = useState('No photo selected.');
  const [loading, setLoading] = useState(false);

  const runFlow = async () => {
    setLoading(true);
    const adapter = getPhotoStorageAdapter();
    const selected = await adapter.selectPhoto();
    if (!selected) { setStatus('Photo upload is unavailable until storage and moderation are configured.'); setLoading(false); return; }
    const result = await adapter.uploadAndModerate(selected.uri);
    setStatus(result.success ? `Photo ${result.moderation}. ${result.simulated ? 'No file was uploaded; this was simulated.' : ''}` : result.error || 'Photo upload unavailable.');
    setLoading(false);
  };

  return <ScreenBackground><ScrollView contentContainerStyle={styles.content}><SoftCard style={styles.card}>
    <Text style={styles.title}>Photo contribution</Text>
    <Text style={styles.body}>Photos require storage, moderation, and retention controls. {RELIEF_TEST_MODE ? 'The test adapter uses a deterministic sample and never uploads a file.' : 'The production adapter is intentionally unavailable.'}</Text>
    <Text style={styles.status}>{status}</Text>
    <Button title={RELIEF_TEST_MODE ? 'Run test photo flow' : 'Photo upload unavailable'} onPress={runFlow} loading={loading} disabled={!RELIEF_TEST_MODE} fullWidth />
  </SoftCard></ScrollView></ScreenBackground>;
};

const styles = StyleSheet.create({
  content: { padding: spacing.lg, paddingBottom: spacing['6xl'] },
  card: { marginTop: spacing.lg },
  title: { ...typography.h2, color: colors.textPrimary, marginBottom: spacing.md },
  body: { ...typography.body, color: colors.textSecondary, lineHeight: 23, marginBottom: spacing.lg },
  status: { ...typography.bodySmall, color: colors.primary, marginBottom: spacing.lg },
});

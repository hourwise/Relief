import React from 'react';
import { ScrollView, StyleSheet, Text } from 'react-native';
import { useRoute } from '@react-navigation/native';
import type { RouteProp } from '@react-navigation/native';
import { ScreenBackground, SoftCard } from '../components';
import { colors, spacing, typography } from '../theme';
import type { RootStackParamList } from '../types';

export const LegalInfoScreen: React.FC = () => {
  const section = useRoute<RouteProp<RootStackParamList, 'LegalInfo'>>().params?.section;
  const title = section === 'privacy' ? 'Privacy' : section === 'terms' ? 'Terms' : section === 'support' ? 'Support' : section === 'data_request' ? 'Data request' : 'Legal and support';
  return <ScreenBackground><ScrollView contentContainerStyle={styles.content}><SoftCard style={styles.card}>
    <Text style={styles.title}>{title}</Text>
    <Text style={styles.body}>This preview build does not yet have approved public privacy, terms, support, or data-request URLs configured.</Text>
    <Text style={styles.body}>Do not treat this screen as a substitute for the production legal contract. Account deletion and data requests remain blocked until the accountable service, retention policy, and support route are configured.</Text>
    <Text style={styles.label}>CURRENT STATE</Text>
    <Text style={styles.status}>LEGAL_CONTRACT_BLOCKED</Text>
  </SoftCard></ScrollView></ScreenBackground>;
};

const styles = StyleSheet.create({
  content: { padding: spacing.lg, paddingBottom: spacing['6xl'] },
  card: { marginTop: spacing.lg },
  title: { ...typography.h2, color: colors.textPrimary, marginBottom: spacing.md },
  body: { ...typography.body, color: colors.textSecondary, lineHeight: 23, marginBottom: spacing.md },
  label: { ...typography.caption, color: colors.textSecondary, letterSpacing: 1, marginTop: spacing.md },
  status: { ...typography.buttonSmall, color: colors.warning, marginTop: spacing.xs },
});

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
    <Text style={styles.body}>Relief account deletion is available to signed-in users from Profile → Delete account. It requires recent authentication and is reported successful only after the server confirms the governed cleanup and Auth deletion.</Text>
    <Text style={styles.body}>Accounts with subscription or payment history are currently blocked from automated deletion while retention and anonymisation handling remains unresolved. No deletion outcome is promised for those accounts.</Text>
    <Text style={styles.body}>This build does not contain an approved public privacy policy, terms, support contact, or data-rights URL. Those release materials must be established before publishing the app.</Text>
    <Text style={styles.label}>CURRENT STATE</Text>
    <Text style={styles.status}>{section === 'data_request' ? 'DATA_REQUEST_CONTACT_NOT_CONFIGURED' : 'PUBLIC_LEGAL_MATERIALS_NOT_CONFIGURED'}</Text>
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

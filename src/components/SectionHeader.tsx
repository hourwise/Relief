import React from 'react';
import { StyleSheet, Text, View } from 'react-native';
import { colors, spacing, typography } from '../theme';

interface SectionHeaderProps { title: string; detail?: string; action?: React.ReactNode; }
export const SectionHeader: React.FC<SectionHeaderProps> = ({ title, detail, action }) => (
  <View style={styles.row}><View style={styles.copy}><Text style={styles.title}>{title}</Text>{detail ? <Text style={styles.detail}>{detail}</Text> : null}</View>{action}</View>
);
const styles = StyleSheet.create({
  row: { flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between', marginBottom: spacing.md },
  copy: { flex: 1, paddingRight: spacing.md },
  title: { ...typography.h4, color: colors.textPrimary },
  detail: { ...typography.bodySmall, color: colors.textSecondary, marginTop: 2 },
});

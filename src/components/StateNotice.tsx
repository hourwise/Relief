import React from 'react';
import { StyleSheet, Text, View } from 'react-native';
import { SoftCard } from './SoftCard';
import { PrimaryButton } from './PrimaryButton';
import { colors, spacing, typography } from '../theme';

interface StateNoticeProps {
  title: string;
  detail?: string;
  /** Supplying an action makes the state recoverable rather than a dead end. */
  actionLabel?: string;
  onAction?: () => void;
  tone?: 'neutral' | 'problem';
}

/**
 * A named, recoverable runtime state.
 *
 * Every failure the user can see should arrive through this component, so a
 * problem is always distinguishable from an empty result and always offers a
 * way forward.
 */
export const StateNotice: React.FC<StateNoticeProps> = ({
  title,
  detail,
  actionLabel,
  onAction,
  tone = 'neutral',
}) => (
  <SoftCard style={[styles.card, tone === 'problem' && styles.problem]}>
    <Text style={styles.title}>{title}</Text>
    {detail ? <Text style={styles.detail}>{detail}</Text> : null}
    {actionLabel && onAction ? (
      <PrimaryButton title={actionLabel} onPress={onAction} style={styles.action} />
    ) : null}
  </SoftCard>
);

const styles = StyleSheet.create({
  card: { alignItems: 'flex-start' },
  problem: { backgroundColor: '#FFF4D9' },
  title: { ...typography.label, color: colors.textPrimary },
  detail: { ...typography.bodySmall, color: colors.textSecondary, marginTop: 4, lineHeight: 21 },
  action: { alignSelf: 'stretch', marginTop: spacing.md },
});

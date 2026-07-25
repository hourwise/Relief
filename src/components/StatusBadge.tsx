import React from 'react';
import { StyleSheet, Text, View } from 'react-native';
import { borderRadius, colors, typography } from '../theme';
import type { OpenStatus } from '../utils/openingHours';

export const StatusBadge: React.FC<{ status: OpenStatus }> = ({ status }) => {
  const content = status === 'open' ? 'Open now' : status === 'closed' ? 'Closed' : 'Hours unknown';
  return <View style={[styles.badge, status === 'open' ? styles.open : status === 'closed' ? styles.closed : styles.unknown]}><Text style={styles.text}>{content}</Text></View>;
};

const styles = StyleSheet.create({
  badge: { alignSelf: 'flex-start', borderRadius: borderRadius.full, paddingHorizontal: 10, paddingVertical: 5 },
  open: { backgroundColor: colors.secondarySurface },
  closed: { backgroundColor: '#FCE7E4' },
  unknown: { backgroundColor: colors.gray100 },
  text: { ...typography.caption, color: colors.textPrimary, fontFamily: 'PlusJakartaSans_600SemiBold' },
});

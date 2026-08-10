import React from 'react';
import { StyleSheet, Text, View } from 'react-native';
import { Circle } from 'lucide-react-native';
import { borderRadius, colors, typography } from '../theme';
import type { OpenStatus } from '../utils/openingHours';

export const StatusBadge: React.FC<{ status: OpenStatus }> = ({ status }) => {
  const content = status === 'open' ? 'Open now' : status === 'closed' ? 'Closed' : 'Hours unknown';
  const isOpen = status === 'open';
  return <View style={[styles.badge, isOpen ? styles.open : status === 'closed' ? styles.closed : styles.unknown]}><Circle size={7} color={isOpen ? colors.primary : colors.textSecondary} fill={isOpen ? colors.primary : 'transparent'} /><Text style={[styles.text, isOpen && styles.openText]}>{content}</Text></View>;
};

const styles = StyleSheet.create({
  badge: { alignSelf: 'flex-start', flexDirection: 'row', alignItems: 'center', gap: 5, borderRadius: borderRadius.full, paddingHorizontal: 10, paddingVertical: 5 },
  open: { backgroundColor: '#DCEFE6', borderWidth: 1, borderColor: '#B9DCCB' },
  closed: { backgroundColor: '#FCE7E4' },
  unknown: { backgroundColor: colors.gray100 },
  text: { ...typography.caption, color: colors.textPrimary, fontFamily: 'PlusJakartaSans_600SemiBold' },
  openText: { color: colors.primary },
});

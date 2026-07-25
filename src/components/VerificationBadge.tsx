import React from 'react';
import { StyleSheet, Text, View } from 'react-native';
import { borderRadius, colors, typography } from '../theme';
import type { Facility } from '../types';

const labels: Record<Facility['verification_status'], string> = {
  source_imported: 'Source imported', source_verified: 'Source verified', community_confirmed: 'Community confirmed', staff_verified: 'Staff verified', disputed: 'Verification disputed', stale: 'Verification needs updating',
};

export const VerificationBadge: React.FC<{ status: Facility['verification_status'] }> = ({ status }) => (
  <View style={[styles.badge, status === 'staff_verified' && styles.staff]}><Text style={styles.text}>{labels[status]}</Text></View>
);

const styles = StyleSheet.create({
  badge: { alignSelf: 'flex-start', borderRadius: borderRadius.full, backgroundColor: colors.secondarySurface, paddingHorizontal: 10, paddingVertical: 5 },
  staff: { backgroundColor: '#FFF4D9' },
  text: { ...typography.caption, color: colors.primary, fontFamily: 'PlusJakartaSans_600SemiBold' },
});

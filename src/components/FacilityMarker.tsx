import React from 'react';
import { StyleSheet, View } from 'react-native';
import { MapPin } from 'lucide-react-native';
import { colors, shadows } from '../theme';

/** Static marker: only selected and urgent markers animate. */
export const FacilityMarker: React.FC = () => (
  <View style={styles.wrap} collapsable={false}>
    <View style={styles.halo} />
    <View style={styles.pin}><MapPin size={20} color={colors.white} strokeWidth={2.75} /></View>
  </View>
);

const styles = StyleSheet.create({
  wrap: { width: 44, height: 52, alignItems: 'center', justifyContent: 'center' },
  halo: { position: 'absolute', width: 34, height: 34, borderRadius: 17, backgroundColor: 'rgba(45, 138, 119, 0.18)' },
  pin: { width: 30, height: 30, borderRadius: 15, alignItems: 'center', justifyContent: 'center', backgroundColor: colors.primary, borderWidth: 3, borderColor: colors.white, ...shadows.glow },
});

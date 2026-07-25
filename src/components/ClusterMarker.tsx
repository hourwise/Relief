import React from 'react';
import { StyleSheet, Text, View } from 'react-native';
import { colors, shadows, typography } from '../theme';

export const ClusterMarker: React.FC<{ count: number }> = ({ count }) => (
  <View style={styles.wrap} collapsable={false}><View style={styles.halo} /><View style={styles.marker}><Text style={styles.text}>{count}</Text></View></View>
);

const styles = StyleSheet.create({
  wrap: { width: 48, height: 48, alignItems: 'center', justifyContent: 'center' },
  halo: { position: 'absolute', width: 44, height: 44, borderRadius: 22, backgroundColor: 'rgba(26, 107, 92, 0.15)' },
  marker: { width: 34, height: 34, borderRadius: 17, justifyContent: 'center', alignItems: 'center', backgroundColor: colors.mapCluster, borderColor: colors.white, borderWidth: 3, ...shadows.md },
  text: { ...typography.caption, color: colors.white, fontFamily: 'PlusJakartaSans_700Bold' },
});

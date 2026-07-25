import React from 'react';
import { Pressable, StyleSheet, Text, View, type StyleProp, type ViewStyle } from 'react-native';
import { borderRadius, colors, shadows, touchTargets, typography } from '../theme';

interface UrgentButtonProps { onPress: () => void; style?: StyleProp<ViewStyle>; compact?: boolean; }

export const UrgentButton: React.FC<UrgentButtonProps> = ({ onPress, style, compact = false }) => (
  <Pressable accessibilityRole="button" accessibilityLabel="Need One Now" accessibilityHint="Find the nearest suitable facility" onPress={onPress} style={({ pressed }) => [styles.button, compact && styles.compact, pressed && styles.pressed, style]}>
    <Text style={styles.title}>Need One Now</Text>
    {!compact ? <View style={styles.subtextRow}><Text style={styles.subtext}>Find the nearest facility</Text></View> : null}
  </Pressable>
);

const styles = StyleSheet.create({
  button: { minHeight: touchTargets.comfortable, alignItems: 'center', justifyContent: 'center', backgroundColor: colors.urgent, borderRadius: borderRadius.full, paddingHorizontal: 24, paddingVertical: 10, ...shadows.lg },
  compact: { paddingVertical: 8 },
  pressed: { opacity: 0.88, transform: [{ scale: 0.99 }] },
  title: { ...typography.button, color: colors.white },
  subtextRow: { marginTop: 1 },
  subtext: { ...typography.caption, color: colors.white },
});

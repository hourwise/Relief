import React from 'react';
import { ActivityIndicator, Pressable, StyleSheet, Text, type StyleProp, type ViewStyle } from 'react-native';
import { borderRadius, colors, opacity, shadows, touchTargets, typography } from '../theme';

interface PrimaryButtonProps {
  title: string;
  onPress: () => void;
  loading?: boolean;
  disabled?: boolean;
  style?: StyleProp<ViewStyle>;
  accessibilityHint?: string;
}

export const PrimaryButton: React.FC<PrimaryButtonProps> = ({ title, onPress, loading = false, disabled = false, style, accessibilityHint }) => {
  const unavailable = disabled || loading;
  return <Pressable accessibilityRole="button" accessibilityLabel={title} accessibilityHint={accessibilityHint} accessibilityState={{ disabled: unavailable, busy: loading }} disabled={unavailable} onPress={onPress} style={({ pressed }) => [styles.button, unavailable && styles.disabled, pressed && !unavailable && styles.pressed, style]}>{loading ? <ActivityIndicator color={colors.white} /> : <Text style={styles.text}>{title}</Text>}</Pressable>;
};

const styles = StyleSheet.create({
  button: { minHeight: touchTargets.comfortable, alignItems: 'center', justifyContent: 'center', borderRadius: borderRadius.full, backgroundColor: colors.primary, paddingHorizontal: 24, ...shadows.md },
  text: { ...typography.button, color: colors.white, textAlign: 'center' },
  disabled: { opacity: opacity.disabled },
  pressed: { opacity: 0.86, transform: [{ scale: 0.99 }] },
});

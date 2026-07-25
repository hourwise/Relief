import React from 'react';
import { Pressable, StyleSheet, View, type StyleProp, type ViewStyle } from 'react-native';
import { borderRadius, colors, shadows, spacing } from '../theme';

interface SoftCardProps {
  children: React.ReactNode;
  style?: StyleProp<ViewStyle>;
  onPress?: () => void;
  accessibilityLabel?: string;
}

export const SoftCard: React.FC<SoftCardProps> = ({ children, style, onPress, accessibilityLabel }) => {
  if (!onPress) return <View style={[styles.card, style]}>{children}</View>;
  return (
    <Pressable
      accessibilityRole="button"
      accessibilityLabel={accessibilityLabel}
      onPress={onPress}
      style={({ pressed }) => [styles.card, pressed && styles.pressed, style]}
    >
      {children}
    </Pressable>
  );
};

const styles = StyleSheet.create({
  card: { backgroundColor: colors.glassBackground, borderColor: colors.borderLight, borderRadius: borderRadius.xl, borderWidth: 1, padding: spacing.lg, ...shadows.md },
  pressed: { opacity: 0.88 },
});

// ============================================================
// Project "Relief" — Card Component
// Design: Very rounded corners (24px) for friendly feel
// Soft shadows, glassmorphism support
// ============================================================

import React from 'react';
import {
  View,
  StyleSheet,
  ViewStyle,
  TouchableOpacity,
} from 'react-native';
import { colors, spacing, borderRadius, shadows } from '../theme';

interface CardProps {
  children: React.ReactNode;
  onPress?: () => void;
  style?: ViewStyle;
  variant?: 'default' | 'elevated' | 'outlined' | 'glass';
}

export const Card: React.FC<CardProps> = ({
  children,
  onPress,
  style,
  variant = 'default',
}) => {
  const Container = onPress ? TouchableOpacity : View;

  return (
    <Container
      style={[styles.base, styles[`variant_${variant}`], style]}
      onPress={onPress}
      activeOpacity={0.7}
    >
      {children}
    </Container>
  );
};

const styles = StyleSheet.create({
  base: {
    backgroundColor: colors.cardBackground,
    borderRadius: borderRadius['2xl'], // 24px — very rounded for friendly feel
    padding: spacing.lg,
  },
  variant_default: {
    backgroundColor: colors.cardBackground,
  },
  variant_elevated: {
    backgroundColor: colors.cardBackground,
    ...shadows.md,
  },
  variant_outlined: {
    backgroundColor: colors.cardBackground,
    borderWidth: 1,
    borderColor: colors.border,
  },
  variant_glass: {
    backgroundColor: colors.glassBackground,
    borderRadius: borderRadius['2xl'],
    ...shadows.md,
  },
});
// ============================================================
// Project "Relief" — Badge Component
// Design: Teal-50 icon backgrounds, rounded pill shapes
// ============================================================

import React from 'react';
import { View, Text, StyleSheet } from 'react-native';
import { colors, typography, spacing, borderRadius } from '../theme';

type BadgeVariant = 'success' | 'warning' | 'error' | 'info' | 'teal';

interface BadgeProps {
  label: string;
  variant?: BadgeVariant;
  size?: 'sm' | 'md';
}

export const Badge: React.FC<BadgeProps> = ({
  label,
  variant = 'info',
  size = 'md',
}) => {
  return (
    <View style={[styles.base, styles[`variant_${variant}`], styles[`size_${size}`]]}>
      <Text style={[styles.text, styles[`text_${variant}`], styles[`textSize_${size}`]]}>
        {label}
      </Text>
    </View>
  );
};

const styles = StyleSheet.create({
  base: {
    borderRadius: borderRadius.full,
    alignSelf: 'flex-start',
  },
  variant_success: {
    backgroundColor: colors.tealSoft,
  },
  variant_warning: {
    backgroundColor: '#FEF3C7',
  },
  variant_error: {
    backgroundColor: '#FEE2E2',
  },
  variant_info: {
    backgroundColor: colors.gray100,
  },
  variant_teal: {
    backgroundColor: colors.tealSoft,
  },
  size_sm: {
    paddingVertical: 2,
    paddingHorizontal: spacing.sm,
  },
  size_md: {
    paddingVertical: spacing.xs,
    paddingHorizontal: spacing.md,
  },
  text: {
    fontFamily: 'Inter_500Medium',
    fontWeight: '500',
  },
  text_success: {
    color: colors.primary,
  },
  text_warning: {
    color: colors.warning,
  },
  text_error: {
    color: colors.error,
  },
  text_info: {
    color: colors.textSecondary,
  },
  text_teal: {
    color: colors.primary,
  },
  textSize_sm: {
    fontSize: 12,
    lineHeight: 16,
  },
  textSize_md: {
    fontSize: 14,
    lineHeight: 20,
  },
});
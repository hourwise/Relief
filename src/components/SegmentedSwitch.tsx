import React from 'react';
import { Pressable, StyleSheet, Text, View, type StyleProp, type ViewStyle } from 'react-native';
import { borderRadius, colors, mapOverlaySurface, spacing, typography } from '../theme';

export interface SegmentOption<T extends string> {
  value: T;
  label: string;
  icon?: React.ReactNode;
}

interface SegmentedSwitchProps<T extends string> {
  options: readonly SegmentOption<T>[];
  value: T;
  onChange: (value: T) => void;
  style?: StyleProp<ViewStyle>;
  accessibilityLabel?: string;
}

/**
 * Two-or-more-way view switch, used for Map/List.
 *
 * Rendered as radio-role buttons rather than tabs so screen readers announce
 * the selected state, and sized to the 44pt minimum touch target.
 */
export function SegmentedSwitch<T extends string>({
  options,
  value,
  onChange,
  style,
  accessibilityLabel,
}: SegmentedSwitchProps<T>) {
  return (
    <View
      accessibilityRole="radiogroup"
      accessibilityLabel={accessibilityLabel}
      style={[styles.track, style]}
    >
      {options.map((option) => {
        const selected = option.value === value;
        return (
          <Pressable
            key={option.value}
            accessibilityRole="radio"
            accessibilityLabel={option.label}
            accessibilityState={{ selected, checked: selected }}
            onPress={() => onChange(option.value)}
            style={[styles.segment, selected && styles.segmentSelected]}
          >
            {option.icon}
            <Text style={[styles.label, selected && styles.labelSelected]}>
              {option.label}
            </Text>
          </Pressable>
        );
      })}
    </View>
  );
}

const styles = StyleSheet.create({
  track: {
    ...mapOverlaySurface,
    flexDirection: 'row',
    alignSelf: 'center',
    padding: 4,
    gap: 4,
  },
  segment: {
    minHeight: 40,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 6,
    paddingHorizontal: spacing.lg,
    borderRadius: borderRadius.full,
  },
  segmentSelected: { backgroundColor: colors.primary },
  label: { ...typography.buttonSmall, color: colors.textSecondary },
  labelSelected: { color: colors.white },
});

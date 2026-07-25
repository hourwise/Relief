import React from 'react';
import { Pressable, StyleSheet, Text } from 'react-native';
import { borderRadius, colors, touchTargets, typography } from '../theme';

interface FilterChipProps { label: string; selected?: boolean; onPress: () => void; }

export const FilterChip: React.FC<FilterChipProps> = ({ label, selected = false, onPress }) => (
  <Pressable
    accessibilityRole="button"
    accessibilityState={{ selected }}
    accessibilityLabel={`${label}${selected ? ', selected' : ''}`}
    onPress={onPress}
    style={({ pressed }) => [styles.chip, selected && styles.selected, pressed && styles.pressed]}
  >
    <Text style={[styles.text, selected && styles.selectedText]} numberOfLines={1}>{label}</Text>
  </Pressable>
);

const styles = StyleSheet.create({
  chip: { minHeight: touchTargets.minimum, alignItems: 'center', justifyContent: 'center', borderRadius: borderRadius.full, borderWidth: 1, borderColor: colors.border, backgroundColor: colors.mapOverlay, paddingHorizontal: 15 },
  selected: { backgroundColor: colors.primary, borderColor: colors.primary },
  pressed: { opacity: 0.82 },
  text: { ...typography.buttonSmall, color: colors.textSecondary },
  selectedText: { color: colors.white },
});

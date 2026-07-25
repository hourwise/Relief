import React from 'react';
import { StyleSheet, Text, View } from 'react-native';
import { colors, spacing, typography } from '../theme';

export const EmptyValue: React.FC<{ children: string }> = ({ children }) => <View style={styles.wrap}><Text style={styles.text}>{children}</Text></View>;
const styles = StyleSheet.create({ wrap: { paddingVertical: spacing.sm }, text: { ...typography.bodySmall, color: colors.textMuted } });

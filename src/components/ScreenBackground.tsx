import React from 'react';
import { StyleSheet, View, type ViewStyle } from 'react-native';
import { colors } from '../theme';

interface ScreenBackgroundProps {
  children: React.ReactNode;
  style?: ViewStyle;
}

export const ScreenBackground: React.FC<ScreenBackgroundProps> = ({ children, style }) => (
  <View style={[styles.base, style]}>{children}</View>
);

const styles = StyleSheet.create({ base: { flex: 1, backgroundColor: colors.mintSurface } });

// ============================================================
// Project "Relief" — Animated Glowing Pin Component
// Design: Glow effect + subtle pulse animation (scale 1.0→1.1)
// Inspired by Studio Ghibli warmth, soft organic shapes
// ============================================================

import React, { useEffect, useRef } from 'react';
import { Animated, StyleSheet, View, Text } from 'react-native';
import { colors, shadows } from '../theme';

interface AnimatedPinProps {
  size?: number;
  color?: string;
  glowColor?: string;
  icon?: string;
}

export const AnimatedPin: React.FC<AnimatedPinProps> = ({
  size = 32,
  color = colors.mapPinDefault,
  glowColor = colors.mapPinGlow,
  icon = '📍',
}) => {
  const pulseAnim = useRef(new Animated.Value(1)).current;

  useEffect(() => {
    const pulse = Animated.loop(
      Animated.sequence([
        Animated.timing(pulseAnim, {
          toValue: 1.1,
          duration: 1500,
          useNativeDriver: true,
        }),
        Animated.timing(pulseAnim, {
          toValue: 1.0,
          duration: 1500,
          useNativeDriver: true,
        }),
      ]),
    );
    pulse.start();
    return () => pulse.stop();
  }, [pulseAnim]);

  return (
    <Animated.View
      style={[
        styles.container,
        {
          width: size,
          height: size,
          borderRadius: size / 2,
          backgroundColor: color,
          shadowColor: glowColor,
          transform: [{ scale: pulseAnim }],
        },
        styles.glow,
      ]}
    >
      <Text style={[styles.icon, { fontSize: size * 0.5 }]}>{icon}</Text>
    </Animated.View>
  );
};

/**
 * Glow container wrapper for any view (for map markers, buttons etc.)
 */
export const GlowContainer: React.FC<{
  children: React.ReactNode;
  color?: string;
  style?: any;
}> = ({ children, color = colors.mapPinGlow, style }) => (
  <View
    style={[
      {
        shadowColor: color,
        shadowOffset: { width: 0, height: 0 },
        shadowOpacity: 0.6,
        shadowRadius: 10,
        elevation: 6,
      },
      style,
    ]}
  >
    {children}
  </View>
);

const styles = StyleSheet.create({
  container: {
    justifyContent: 'center',
    alignItems: 'center',
    shadowOffset: { width: 0, height: 0 },
    shadowOpacity: 0.6,
    shadowRadius: 10,
    elevation: 6,
  },
  glow: {
    shadowOffset: { width: 0, height: 0 },
    shadowOpacity: 0.6,
    shadowRadius: 10,
  },
  icon: {
    textAlign: 'center',
  },
});
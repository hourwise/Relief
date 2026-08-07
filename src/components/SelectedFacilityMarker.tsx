import React, { useEffect, useMemo, useState } from 'react';
import { AccessibilityInfo, Animated, StyleSheet, View } from 'react-native';
import { MapPin } from 'lucide-react-native';
import { colors, shadows } from '../theme';

interface SelectedFacilityMarkerProps { urgent?: boolean; }

export const SelectedFacilityMarker: React.FC<SelectedFacilityMarkerProps> = ({ urgent = false }) => {
  const scale = useMemo(() => new Animated.Value(1), []);
  const [reduceMotion, setReduceMotion] = useState(false);
  useEffect(() => {
    AccessibilityInfo.isReduceMotionEnabled().then(setReduceMotion).catch(() => undefined);
  }, []);
  useEffect(() => {
    if (reduceMotion) return;
    const animation = Animated.loop(Animated.sequence([
      Animated.timing(scale, { toValue: 1.12, duration: 850, useNativeDriver: true }),
      Animated.timing(scale, { toValue: 1, duration: 850, useNativeDriver: true }),
    ]));
    animation.start();
    return () => animation.stop();
  }, [reduceMotion, scale]);
  const pinColor = urgent ? colors.urgent : colors.amber;
  return <Animated.View style={[styles.wrap, { transform: [{ scale }] }]} collapsable={false}><View style={[styles.halo, { backgroundColor: urgent ? 'rgba(231, 95, 81, 0.22)' : 'rgba(244, 196, 83, 0.30)' }]} /><View style={[styles.pin, { backgroundColor: pinColor }]}><MapPin size={24} color={colors.charcoal} strokeWidth={2.75} /></View></Animated.View>;
};

const styles = StyleSheet.create({
  wrap: { width: 56, height: 60, alignItems: 'center', justifyContent: 'center' },
  halo: { position: 'absolute', width: 54, height: 54, borderRadius: 27 },
  pin: { width: 38, height: 38, borderRadius: 19, alignItems: 'center', justifyContent: 'center', borderWidth: 3, borderColor: colors.white, ...shadows.lg },
});

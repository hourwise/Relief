import React, { useEffect, useMemo, useState } from 'react';
import { AccessibilityInfo, Animated, Easing, StyleSheet, View } from 'react-native';
import { MapPin } from 'lucide-react-native';
import { colors, shadows } from '../theme';

interface SelectedFacilityMarkerProps { urgent?: boolean; }

/**
 * The brand's "luminous wayfinding pin".
 *
 * Two concentric rings expand and fade outward from the pin — the ripple
 * signature from the Relief artwork — under a gently breathing pin. Only the
 * selected and urgent markers do this: animating every facility would turn a
 * calm map into a fairground and cost frames on a dense viewport.
 *
 * Honours reduce-motion, in which case the rings are drawn statically at rest
 * so the marker still reads as "this is the one" without any movement.
 */
export const SelectedFacilityMarker: React.FC<SelectedFacilityMarkerProps> = ({ urgent = false }) => {
  const scale = useMemo(() => new Animated.Value(1), []);
  const ripple1 = useMemo(() => new Animated.Value(0), []);
  const ripple2 = useMemo(() => new Animated.Value(0), []);
  const [reduceMotion, setReduceMotion] = useState(false);

  useEffect(() => {
    AccessibilityInfo.isReduceMotionEnabled().then(setReduceMotion).catch(() => undefined);
  }, []);

  useEffect(() => {
    if (reduceMotion) return;

    const breathe = Animated.loop(
      Animated.sequence([
        Animated.timing(scale, { toValue: 1.1, duration: 900, easing: Easing.inOut(Easing.quad), useNativeDriver: true }),
        Animated.timing(scale, { toValue: 1, duration: 900, easing: Easing.inOut(Easing.quad), useNativeDriver: true }),
      ]),
    );

    // The second ring is offset so the ripples read as a sequence rather than
    // a single thick pulse.
    const ring = (value: Animated.Value, delay: number) =>
      Animated.loop(
        Animated.sequence([
          Animated.delay(delay),
          Animated.timing(value, { toValue: 1, duration: 2000, easing: Easing.out(Easing.quad), useNativeDriver: true }),
          Animated.timing(value, { toValue: 0, duration: 0, useNativeDriver: true }),
        ]),
      );

    const animations = [breathe, ring(ripple1, 0), ring(ripple2, 1000)];
    animations.forEach((a) => a.start());
    return () => animations.forEach((a) => a.stop());
  }, [reduceMotion, scale, ripple1, ripple2]);

  const glow = urgent ? 'rgba(231, 95, 81, 0.30)' : 'rgba(244, 196, 83, 0.34)';
  const ringColor = urgent ? colors.urgent : colors.amber;
  const pinColor = urgent ? colors.urgent : colors.amber;

  const rippleStyle = (value: Animated.Value) => ({
    borderColor: ringColor,
    opacity: reduceMotion
      ? 0.18
      : value.interpolate({ inputRange: [0, 1], outputRange: [0.55, 0] }),
    transform: [
      { scale: reduceMotion ? 1.35 : value.interpolate({ inputRange: [0, 1], outputRange: [0.55, 1.85] }) },
    ],
  });

  return (
    <View style={styles.wrap} collapsable={false}>
      <Animated.View style={[styles.ripple, rippleStyle(ripple1)]} />
      <Animated.View style={[styles.ripple, rippleStyle(ripple2)]} />
      <View style={[styles.halo, { backgroundColor: glow }]} />
      <Animated.View style={[styles.pinWrap, { transform: [{ scale }] }]}>
        <View style={[styles.pin, { backgroundColor: pinColor }]}>
          <MapPin size={24} color={colors.charcoal} strokeWidth={2.75} />
        </View>
      </Animated.View>
    </View>
  );
};

const styles = StyleSheet.create({
  // Sized to contain the widest ripple so the rings are not clipped.
  wrap: { width: 92, height: 92, alignItems: 'center', justifyContent: 'center' },
  ripple: { position: 'absolute', width: 62, height: 62, borderRadius: 31, borderWidth: 2 },
  halo: { position: 'absolute', width: 54, height: 54, borderRadius: 27 },
  pinWrap: { alignItems: 'center', justifyContent: 'center' },
  pin: {
    width: 38,
    height: 38,
    borderRadius: 19,
    alignItems: 'center',
    justifyContent: 'center',
    borderWidth: 3,
    borderColor: colors.white,
    ...shadows.lg,
  },
});

import React, { useEffect, useMemo, useState } from 'react';
import {
  AccessibilityInfo,
  Animated,
  Easing,
  Image,
  StyleSheet,
  Text,
  View,
} from 'react-native';
import { colors, spacing, typography } from '../theme';

interface BrandedHandoffProps {
  /** What the app is genuinely waiting on, shown beneath the lock-up. */
  status: string;
  /** Fades out when false; unmounting is the caller's job once faded. */
  visible: boolean;
  onFadedOut?: () => void;
}

/**
 * The branded moment between "signed in / launched" and "here is the map".
 *
 * This adds NO artificial delay. It is shown only while session, location and
 * the first facility page are genuinely resolving, and it fades the instant
 * they are ready — so on a fast connection it is a blink, and on a slow one it
 * is reassurance instead of a blank map.
 *
 * The watercolour backdrop and the horizontal lock-up are the same assets the
 * website uses, which is the point: the handoff is where the app most obviously
 * either belongs to the brand or does not.
 */
export const BrandedHandoff: React.FC<BrandedHandoffProps> = ({
  status,
  visible,
  onFadedOut,
}) => {
  const opacity = useMemo(() => new Animated.Value(1), []);
  const pulse = useMemo(() => new Animated.Value(0), []);
  const [reduceMotion, setReduceMotion] = useState(false);

  useEffect(() => {
    AccessibilityInfo.isReduceMotionEnabled().then(setReduceMotion).catch(() => undefined);
  }, []);

  // A slow breath on the ring, echoing the ripple on the map pins. Skipped
  // entirely under reduce-motion.
  useEffect(() => {
    if (reduceMotion) return;
    const loop = Animated.loop(
      Animated.sequence([
        Animated.timing(pulse, { toValue: 1, duration: 1600, easing: Easing.inOut(Easing.quad), useNativeDriver: true }),
        Animated.timing(pulse, { toValue: 0, duration: 1600, easing: Easing.inOut(Easing.quad), useNativeDriver: true }),
      ]),
    );
    loop.start();
    return () => loop.stop();
  }, [pulse, reduceMotion]);

  useEffect(() => {
    if (visible) return;
    Animated.timing(opacity, {
      toValue: 0,
      duration: 420,
      easing: Easing.out(Easing.quad),
      useNativeDriver: true,
    }).start(({ finished }) => {
      if (finished) onFadedOut?.();
    });
  }, [visible, opacity, onFadedOut]);

  return (
    <Animated.View
      style={[styles.root, { opacity }]}
      pointerEvents={visible ? 'auto' : 'none'}
      accessibilityRole="progressbar"
      accessibilityLabel={`Relief. ${status}`}
      accessibilityLiveRegion="polite"
    >
      <Image
        source={require('../../assets/branding/relief-watercolor-backdrop.jpg')}
        resizeMode="cover"
        style={StyleSheet.absoluteFill}
        accessible={false}
      />
      {/* Softens the artwork so the lock-up keeps its contrast on any crop. */}
      <View style={styles.wash} pointerEvents="none" />

      <View style={styles.centre}>
        <Animated.View
          style={[
            styles.ring,
            {
              opacity: reduceMotion ? 0.35 : pulse.interpolate({ inputRange: [0, 1], outputRange: [0.18, 0.5] }),
              transform: [
                { scale: reduceMotion ? 1.1 : pulse.interpolate({ inputRange: [0, 1], outputRange: [0.94, 1.22] }) },
              ],
            },
          ]}
        />
        <Image
          source={require('../../assets/branding/relief-logo-horizontal.jpg')}
          resizeMode="contain"
          style={styles.logo}
          accessibilityRole="image"
          accessibilityLabel="Relief — Find Comfort, Feel Relief"
        />
      </View>

      <Text style={styles.status}>{status}</Text>
    </Animated.View>
  );
};

const styles = StyleSheet.create({
  root: { ...StyleSheet.absoluteFill, alignItems: 'center', justifyContent: 'center', backgroundColor: colors.mintSurface, zIndex: 100 },
  wash: { ...StyleSheet.absoluteFill, backgroundColor: 'rgba(243, 248, 245, 0.62)' },
  centre: { alignItems: 'center', justifyContent: 'center' },
  ring: { position: 'absolute', width: 300, height: 300, borderRadius: 150, borderWidth: 2, borderColor: colors.primaryLight },
  // The lock-up is a 3:1 JPEG on a warm-white ground, so it is given a matching
  // rounded surface rather than floated directly on the watercolour.
  logo: { width: 268, height: 90, borderRadius: 18 },
  status: { ...typography.bodySmall, color: colors.primary, marginTop: spacing['3xl'], letterSpacing: 0.2 },
});

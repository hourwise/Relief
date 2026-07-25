import React, { useEffect, useRef, useState } from 'react';
import { AccessibilityInfo, Animated, Pressable, StyleSheet, Text, View } from 'react-native';
import { ReliefLogo, WatercolorMapBackdrop } from '../components';
import { borderRadius, colors, spacing, typography } from '../theme';

interface StartupWelcomeProps {
  startupReady: boolean;
  onFinished: () => void;
}

/** A post-native-splash welcome surface that exits as soon as real startup is done. */
export const StartupWelcome: React.FC<StartupWelcomeProps> = ({ startupReady, onFinished }) => {
  const opacity = useRef(new Animated.Value(1)).current;
  const contentOpacity = useRef(new Animated.Value(0)).current;
  const [reduceMotion, setReduceMotion] = useState(false);
  const [skipDecoration, setSkipDecoration] = useState(false);

  useEffect(() => {
    AccessibilityInfo.isReduceMotionEnabled().then(setReduceMotion).catch(() => undefined);
  }, []);

  useEffect(() => {
    Animated.timing(contentOpacity, { toValue: 1, duration: reduceMotion ? 0 : 180, useNativeDriver: true }).start();
  }, [contentOpacity, reduceMotion]);

  useEffect(() => {
    if (!startupReady) return;
    Animated.timing(opacity, {
      toValue: 0,
      duration: reduceMotion || skipDecoration ? 0 : 220,
      useNativeDriver: true,
    }).start(({ finished }) => { if (finished) onFinished(); });
  }, [onFinished, opacity, reduceMotion, skipDecoration, startupReady]);

  return (
    <Animated.View style={[styles.root, { opacity }]} accessibilityViewIsModal>
      <WatercolorMapBackdrop />
      <View style={styles.overlay} />
      <Pressable
        accessibilityRole="button"
        accessibilityLabel="Continue to Relief"
        accessibilityHint="Skips the welcome animation when startup is ready"
        onPress={() => setSkipDecoration(true)}
        style={styles.touchLayer}
      >
        <Animated.View style={[styles.content, { opacity: contentOpacity }]}>
          <View style={styles.logoCircle}><ReliefLogo size={62} color={colors.white} /></View>
          <Text style={styles.title}>Relief</Text>
          <Text style={styles.tagline}>Find Comfort, Feel Relief.</Text>
        </Animated.View>
      </Pressable>
    </Animated.View>
  );
};

const styles = StyleSheet.create({
  root: { ...StyleSheet.absoluteFill, zIndex: 100, backgroundColor: colors.primary },
  overlay: { ...StyleSheet.absoluteFill, backgroundColor: 'rgba(16, 66, 54, 0.34)' },
  touchLayer: { flex: 1, alignItems: 'center', justifyContent: 'center', padding: spacing['3xl'] },
  content: { alignItems: 'center', width: '100%' },
  logoCircle: { width: 104, height: 104, borderRadius: borderRadius.full, alignItems: 'center', justifyContent: 'center', backgroundColor: 'rgba(255,255,255,0.16)', borderWidth: 1.5, borderColor: 'rgba(255,255,255,0.48)', marginBottom: spacing['2xl'] },
  title: { fontFamily: 'PlusJakartaSans_700Bold', fontSize: 42, lineHeight: 50, letterSpacing: -0.8, color: colors.white, textAlign: 'center' },
  tagline: { ...typography.body, color: 'rgba(255,255,255,0.94)', textAlign: 'center', marginTop: spacing.sm, fontStyle: 'italic' },
});

import React, { useCallback } from 'react';
import { Image, Pressable, ScrollView, StyleSheet, Text, View } from 'react-native';
import { useNavigation } from '@react-navigation/native';
import type { CompositeNavigationProp, NavigationProp } from '@react-navigation/native';
import type { BottomTabNavigationProp } from '@react-navigation/bottom-tabs';
import type { NativeStackNavigationProp } from '@react-navigation/native-stack';
import { Compass, Heart, Info, Search } from 'lucide-react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { ScreenBackground } from '../components';
import { borderRadius, colors, shadows, spacing, touchTargets, typography } from '../theme';
import type { HomeStackParamList, MainTabParamList, RootStackParamList } from '../types';

type HomeNavigationProp = CompositeNavigationProp<
  NativeStackNavigationProp<HomeStackParamList, 'HomeMain'>,
  CompositeNavigationProp<
    BottomTabNavigationProp<MainTabParamList, 'Home'>,
    NavigationProp<RootStackParamList>
  >
>;

export const HomeScreen: React.FC = () => {
  const navigation = useNavigation<HomeNavigationProp>();

  const openFind = useCallback(() => {
    navigation.navigate('Find', { screen: 'FindHome' });
  }, [navigation]);

  const needOneNow = useCallback(() => {
    navigation.navigate('Find', {
      screen: 'FindHome',
      params: { action: 'need_one_now', actionId: Date.now() },
    });
  }, [navigation]);

  return (
    <ScreenBackground>
      <SafeAreaView edges={['top']} style={styles.safeArea}>
        <ScrollView
          contentContainerStyle={styles.content}
          showsVerticalScrollIndicator={false}
        >
          <View style={styles.header}>
            <Image
              source={require('../../assets/branding/relief-logo-horizontal.jpg')}
              resizeMode="contain"
              style={styles.logo}
              accessibilityRole="image"
              accessibilityLabel="Relief — Find Comfort, Feel Relief"
            />
            <Text style={styles.tagline}>Find Comfort, Feel Relief</Text>
            <Text style={styles.welcomeCopy}>
              A calmer way to find a suitable facility when you need one.
            </Text>
          </View>

          <Image
            source={require('../../assets/branding/relief-street-illustration.jpg')}
            resizeMode="cover"
            style={styles.illustration}
            accessible={false}
          />

          <Text style={styles.eyebrow}>READY WHEN YOU ARE</Text>
          <Pressable
            accessibilityRole="button"
            accessibilityLabel="Find a facility"
            onPress={openFind}
            style={({ pressed }) => [styles.actionCard, pressed && styles.pressed]}
          >
            <View style={styles.iconTile}>
              <Search size={23} color={colors.primary} strokeWidth={2.4} />
            </View>
            <View style={styles.actionCopy}>
              <Text style={styles.actionTitle}>Find a facility</Text>
              <Text style={styles.actionDetail}>Browse nearby places, search, and filter.</Text>
            </View>
            <Compass size={20} color={colors.sage} />
          </Pressable>

          <Pressable
            accessibilityRole="button"
            accessibilityLabel="Need One Now"
            accessibilityHint="Find the nearest suitable facility"
            onPress={needOneNow}
            style={({ pressed }) => [styles.urgentCard, pressed && styles.pressed]}
          >
            <View style={styles.urgentIcon}>
              <Compass size={23} color={colors.white} strokeWidth={2.4} />
            </View>
            <View style={styles.actionCopy}>
              <Text style={styles.urgentTitle}>Need One Now</Text>
              <Text style={styles.urgentDetail}>Find the nearest suitable facility.</Text>
            </View>
          </Pressable>

          <Text style={styles.eyebrow}>YOUR RELIEF</Text>
          <Pressable
            accessibilityRole="button"
            accessibilityLabel="Saved places"
            onPress={() => navigation.navigate('Favourites')}
            style={({ pressed }) => [styles.secondaryCard, pressed && styles.pressed]}
          >
            <View style={styles.secondaryIcon}>
              <Heart size={21} color={colors.primary} />
            </View>
            <View style={styles.actionCopy}>
              <Text style={styles.actionTitle}>Saved places</Text>
              <Text style={styles.actionDetail}>Keep your regular facilities close by.</Text>
            </View>
          </Pressable>

          <Pressable
            accessibilityRole="button"
            accessibilityLabel="About Relief"
            onPress={() => navigation.navigate('AboutRelief')}
            style={({ pressed }) => [styles.aboutLink, pressed && styles.pressed]}
          >
            <Info size={18} color={colors.primary} />
            <Text style={styles.aboutText}>About Relief</Text>
          </Pressable>
        </ScrollView>
      </SafeAreaView>
    </ScreenBackground>
  );
};

const styles = StyleSheet.create({
  safeArea: { flex: 1 },
  content: { padding: spacing.lg, paddingBottom: spacing['5xl'] },
  header: { alignItems: 'flex-start', paddingTop: spacing.sm },
  logo: { width: 212, height: 64, borderRadius: 14 },
  tagline: { ...typography.h3, color: colors.primary, marginTop: spacing.lg },
  welcomeCopy: { ...typography.bodySmall, color: colors.textSecondary, lineHeight: 21, marginTop: spacing.xs, maxWidth: 320 },
  illustration: { width: '100%', height: 132, borderRadius: borderRadius['2xl'], marginTop: spacing.xl, backgroundColor: colors.secondarySurface },
  eyebrow: { ...typography.caption, color: colors.textSecondary, fontFamily: 'PlusJakartaSans_700Bold', letterSpacing: 1, marginTop: spacing['2xl'], marginBottom: spacing.sm },
  actionCard: { minHeight: 76, flexDirection: 'row', alignItems: 'center', padding: spacing.md, borderRadius: borderRadius.xl, backgroundColor: colors.warmWhite, borderWidth: 1, borderColor: 'rgba(26, 107, 92, 0.14)', ...shadows.sm },
  urgentCard: { minHeight: 76, flexDirection: 'row', alignItems: 'center', padding: spacing.md, borderRadius: borderRadius.xl, backgroundColor: colors.urgent, marginTop: spacing.sm, ...shadows.md },
  secondaryCard: { minHeight: 70, flexDirection: 'row', alignItems: 'center', padding: spacing.md, borderRadius: borderRadius.xl, backgroundColor: colors.secondarySurface, borderWidth: 1, borderColor: 'rgba(26, 107, 92, 0.1)' },
  iconTile: { width: 44, height: 44, borderRadius: 16, alignItems: 'center', justifyContent: 'center', backgroundColor: colors.secondarySurface, marginRight: spacing.md },
  urgentIcon: { width: 44, height: 44, borderRadius: 16, alignItems: 'center', justifyContent: 'center', backgroundColor: 'rgba(255,255,255,0.18)', marginRight: spacing.md },
  secondaryIcon: { width: 42, height: 42, borderRadius: 15, alignItems: 'center', justifyContent: 'center', backgroundColor: colors.warmWhite, marginRight: spacing.md },
  actionCopy: { flex: 1, paddingRight: spacing.sm },
  actionTitle: { ...typography.h4, color: colors.textPrimary },
  actionDetail: { ...typography.caption, color: colors.textSecondary, marginTop: 2 },
  urgentTitle: { ...typography.h4, color: colors.white },
  urgentDetail: { ...typography.caption, color: 'rgba(255,255,255,0.9)', marginTop: 2 },
  aboutLink: { minHeight: touchTargets.minimum, alignSelf: 'flex-start', flexDirection: 'row', alignItems: 'center', gap: spacing.sm, marginTop: spacing.lg, paddingHorizontal: spacing.xs },
  aboutText: { ...typography.buttonSmall, color: colors.primary },
  pressed: { opacity: 0.82 },
});

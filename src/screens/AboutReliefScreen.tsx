import React from 'react';
import { Dimensions, Image, Linking, Pressable, SafeAreaView, ScrollView, StyleSheet, Text, View } from 'react-native';
import { ArrowLeft, ExternalLink } from 'lucide-react-native';
import Constants from 'expo-constants';
import { ScreenBackground, SectionHeader, SoftCard } from '../components';
import { borderRadius, colors, spacing, touchTargets, typography } from '../theme';

interface AboutReliefScreenProps { navigation: { goBack: () => void }; }

export const AboutReliefScreen: React.FC<AboutReliefScreenProps> = ({ navigation }) => {
  const version = Constants.expoConfig?.version ?? '1.0.0';
  return <ScreenBackground>
    <SafeAreaView style={styles.safeArea}>
      <ScrollView contentContainerStyle={styles.content} showsVerticalScrollIndicator={false}>
        <View style={styles.topBar}><Pressable accessibilityRole="button" accessibilityLabel="Back" onPress={navigation.goBack} style={styles.backButton}><ArrowLeft size={23} color={colors.textPrimary} /></Pressable><Text style={styles.title}>About Relief</Text></View>
        {/* The artwork is a tall 941x1672 portrait poster. At width:'100%' its
            correct aspect ratio made it ~1.8x the content width TALL — roughly
            640dp — so it swamped the screen and pushed every card below the
            fold. The aspect ratio was never wrong; using a portrait poster at
            full bleed was.

            It is now capped by HEIGHT against the viewport and centred, with
            `contain` preserving the aspect ratio inside that box. The frame
            gives it an intentional, brand-consistent presentation rather than a
            raw bleed. */}
        {/* The horizontal lock-up is the primary brand mark; the poster is
            supporting artwork beneath it. */}
        <Image source={require('../../assets/branding/relief-logo-horizontal.jpg')} resizeMode="contain" accessibilityRole="image" accessibilityLabel="Relief — Find Comfort, Feel Relief" style={styles.lockup} />
        <View style={styles.posterFrame}>
          <Image
            source={require('../../assets/branding/relief-brand-poster.jpg')}
            resizeMode="contain"
            accessibilityRole="image"
            accessibilityLabel="Relief watercolour artwork showing a map, location pins, the Relief logo and the Find Comfort, Feel Relief tagline"
            style={styles.poster}
          />
        </View>
        <SoftCard style={styles.section}><SectionHeader title="Find comfort, feel relief" /><Text style={styles.copy}>Relief helps people find suitable facilities with the accessibility, privacy, family, and comfort information that matters in the moment.</Text></SoftCard>
        <SoftCard style={styles.section}><SectionHeader title="App information" /><Text style={styles.version}>Relief v{version}</Text><Text style={styles.copy}>This prototype uses real facility records where the connected development services are available. Details and community updates can be incomplete or unavailable.</Text></SoftCard>
        <SoftCard style={styles.section}><SectionHeader title="Data attribution" /><Text style={styles.copy}>Some imported UK facility records are attributed to Toilet Map UK under CC-BY 4.0. Check the original source for its current data and licence information.</Text><Pressable accessibilityRole="link" accessibilityLabel="Open Toilet Map UK" onPress={() => Linking.openURL('https://www.toiletmapuk.org/')} style={styles.link}><Text style={styles.linkText}>Toilet Map UK</Text><ExternalLink size={16} color={colors.primary} /></Pressable></SoftCard>
      </ScrollView>
    </SafeAreaView>
  </ScreenBackground>;
};

const styles = StyleSheet.create({
  safeArea: { flex: 1 }, content: { padding: spacing.lg, paddingBottom: spacing['6xl'] }, topBar: { minHeight: touchTargets.minimum, flexDirection: 'row', alignItems: 'center', marginBottom: spacing.md }, backButton: { width: touchTargets.minimum, height: touchTargets.minimum, borderRadius: borderRadius.full, alignItems: 'center', justifyContent: 'center', backgroundColor: colors.white, marginRight: spacing.sm }, title: { ...typography.h3, color: colors.textPrimary }, lockup: { width: '100%', aspectRatio: 3, borderRadius: borderRadius.lg, marginBottom: spacing.md }, posterFrame: { width: '100%', height: Math.min(Dimensions.get('window').height * 0.34, 320), borderRadius: borderRadius.xl, overflow: 'hidden', backgroundColor: colors.secondarySurface, borderWidth: 1, borderColor: colors.borderLight, alignItems: 'center', justifyContent: 'center', marginBottom: spacing.lg }, poster: { width: '100%', height: '100%' }, section: { marginBottom: spacing.md }, copy: { ...typography.bodySmall, color: colors.textSecondary, lineHeight: 22 }, version: { ...typography.h4, color: colors.primary, marginBottom: spacing.xs }, link: { minHeight: touchTargets.minimum, alignSelf: 'flex-start', flexDirection: 'row', alignItems: 'center', gap: spacing.xs, marginTop: spacing.sm }, linkText: { ...typography.buttonSmall, color: colors.primary },
});

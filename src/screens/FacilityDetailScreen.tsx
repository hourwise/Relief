import React, { useCallback, useEffect, useState } from 'react';
import { ActivityIndicator, Alert, Linking, Platform, Pressable, SafeAreaView, ScrollView, StyleSheet, Text, View } from 'react-native';
import { ArrowLeft, Flag, Heart, MapPin, Navigation, Pencil, Star } from 'lucide-react-native';
import { NavigationProp, RouteProp, useNavigation, useRoute } from '@react-navigation/native';
import type { TemporaryReport } from '../types/community';
import type { Facility, FindStackParamList } from '../types';
import { EmptyValue, PrimaryButton, ScreenBackground, SectionHeader, SoftCard, StateNotice, StatusBadge, VerificationBadge } from '../components';
import { getActiveReports } from '../services/community';
import { fetchFacilityById } from '../services/facilities';
import { addFavourite, isFavourite, removeFavourite } from '../services/favourites';
import { useAuthGate } from '../context/AuthContext';
import { getOpenStatus } from '../utils/openingHours';
import { borderRadius, colors, spacing, touchTargets, typography } from '../theme';

type FacilityDetailRouteProp = RouteProp<FindStackParamList, 'FacilityDetail'>;

const amenityLabels: Array<[keyof Facility, string]> = [
  ['is_accessible', 'Accessible'], ['is_disabled_access', 'Disabled access'], ['has_wheelchair_access', 'Wheelchair access'], ['requires_radar_key', 'RADAR Key'], ['has_adult_changing_place', 'Adult changing place'], ['has_grab_rails', 'Grab rails'], ['has_baby_changing', 'Baby changing'], ['has_family_room', 'Family room'], ['is_gender_neutral', 'Gender-neutral'], ['is_single_occupancy', 'Single occupancy'], ['is_24h', 'Open 24 hours'], ['is_picnic_area', 'Picnic area'],
];

/**
 * Icon and value are siblings inside a View, not an SVG nested in <Text>.
 * react-native-svg elements are native views: inside a Text they do not
 * participate in text layout and render unreliably on Android.
 */
const RatingRow: React.FC<{ label: string; value: number | null }> = ({ label, value }) => value == null ? null : (
  <View style={styles.ratingRow}>
    <Text style={styles.ratingLabel}>{label}</Text>
    <View style={styles.ratingValueRow}>
      <Star size={14} color={colors.amber} fill={colors.amber} />
      <Text style={styles.ratingValue}>{value.toFixed(1)}</Text>
    </View>
  </View>
);

export const FacilityDetailScreen: React.FC = () => {
  const route = useRoute<FacilityDetailRouteProp>();
  const navigation = useNavigation<NavigationProp<FindStackParamList>>();
  const { facilityId } = route.params;
  const { run: runGated, isAuthenticated } = useAuthGate();
  const [facility, setFacility] = useState<Facility | null>(null);
  const [loading, setLoading] = useState(true);
  const [loadError, setLoadError] = useState<string | null>(null);
  const [activeReports, setActiveReports] = useState<TemporaryReport[]>([]);
  const [favourited, setFavourited] = useState(false);
  const [favouriteBusy, setFavouriteBusy] = useState(false);

  const load = useCallback(async () => {
    setLoading(true);
    setLoadError(null);
    const result = await fetchFacilityById(facilityId);
    if (result.ok) {
      setFacility(result.data);
    } else {
      setFacility(null);
      setLoadError(result.error);
    }
    setLoading(false);
  }, [facilityId]);

  useEffect(() => {
    load();
    // Community reports are supplementary: a failure here must not block the
    // facility itself from rendering.
    getActiveReports(facilityId).then(setActiveReports).catch(() => setActiveReports([]));
  }, [facilityId, load]);

  useEffect(() => {
    if (!isAuthenticated) { setFavourited(false); return; }
    isFavourite(facilityId).then(setFavourited).catch(() => setFavourited(false));
  }, [facilityId, isAuthenticated]);

  const toggleFavourite = () => {
    runGated('save_favourite', async () => {
      setFavouriteBusy(true);
      const result = favourited ? await removeFavourite(facilityId) : await addFavourite(facilityId);
      setFavouriteBusy(false);
      if (result.success) setFavourited(!favourited);
      else Alert.alert('Favourites', result.error || 'Could not update your favourites.');
    });
  };

  const openMaps = async (provider: 'google' | 'apple' | 'waze') => {
    if (!facility) return;
    const coordinates = `${facility.latitude},${facility.longitude}`;
    const url = provider === 'google'
      ? `https://www.google.com/maps/dir/?api=1&destination=${encodeURIComponent(coordinates)}&travelmode=walking&dir_action=navigate`
      : provider === 'apple'
        ? `maps://app?daddr=${coordinates}&dirflg=w`
        : `https://waze.com/ul?ll=${coordinates}&navigate=yes`;
    if (provider === 'apple' && Platform.OS !== 'ios') { Alert.alert('Apple Maps', 'Apple Maps is only available on iOS.'); return; }
    try {
      if (await Linking.canOpenURL(url)) await Linking.openURL(url);
      else Alert.alert('Cannot open map', `No map application was found for directions to ${facility.name}.`);
    } catch { Alert.alert('Directions unavailable', 'Please check that a map app is installed.'); }
  };

  if (loading) return <ScreenBackground><View style={styles.loading}><ActivityIndicator size="large" color={colors.primary} /></View></ScreenBackground>;

  // A failed load is retryable and is stated as a failure, not as "not found".
  if (loadError) return <ScreenBackground><SafeAreaView style={styles.stateWrap}>
    <StateNotice tone="problem" title="This facility could not be loaded" detail={loadError} actionLabel="Try again" onAction={load} />
    <Pressable accessibilityRole="button" onPress={() => navigation.goBack()} style={styles.backTextButton}><Text style={styles.backText}>Go back</Text></Pressable>
  </SafeAreaView></ScreenBackground>;

  if (!facility) return <ScreenBackground><SafeAreaView style={styles.notFound}><Text style={styles.notFoundTitle}>Facility not found</Text><Pressable accessibilityRole="button" onPress={() => navigation.goBack()} style={styles.backTextButton}><Text style={styles.backText}>Go back</Text></Pressable></SafeAreaView></ScreenBackground>;

  const openStatus = getOpenStatus(facility);
  const cost = facility.is_free === true ? 'Free' : facility.is_free === false ? (facility.price_note || 'Paid') : 'Cost unknown';
  const amenities = amenityLabels.filter(([key]) => facility[key] === true).map(([, label]) => label);
  const overallScore = facility.overall_score ?? 0;
  const hasRatings = overallScore > 0 || [facility.cleanliness_rating, facility.privacy_rating, facility.accessibility_rating, facility.safety_rating, facility.noise_rating, facility.environment_rating].some((value) => value != null);

  return <ScreenBackground>
    <SafeAreaView style={styles.safeArea}>
      <ScrollView contentContainerStyle={styles.content} showsVerticalScrollIndicator={false}>
        <View style={styles.topBar}>
          <Pressable accessibilityRole="button" accessibilityLabel="Back" onPress={() => navigation.goBack()} style={styles.backButton}><ArrowLeft color={colors.textPrimary} size={23} /></Pressable>
          <Text style={styles.topLabel}>Facility details</Text>
          <Pressable accessibilityRole="button" accessibilityState={{ selected: favourited, busy: favouriteBusy }} accessibilityLabel={favourited ? `Remove ${facility.name} from favourites` : `Save ${facility.name} to favourites`} onPress={toggleFavourite} style={styles.favouriteButton}>
            <Heart size={21} color={colors.urgent} fill={favourited ? colors.urgent : 'transparent'} />
          </Pressable>
        </View>
        <SoftCard style={styles.locationHeader}>
          <View style={styles.locationIcon}><MapPin color={colors.primary} size={28} /></View>
          <View style={styles.locationCopy}><Text style={styles.locationKicker}>FACILITY LOCATION</Text><Text style={styles.locationText} numberOfLines={2}>{facility.town || facility.address || 'Location information unavailable'}</Text></View>
        </SoftCard>

        {activeReports.length ? <SoftCard style={styles.warning}><Text style={styles.warningTitle}>Recent community reports</Text>{activeReports.map((report) => <Text key={report.id} style={styles.warningText}>{report.type}: {report.notes || 'No details provided'}</Text>)}</SoftCard> : null}

        <View style={styles.hero}><View style={styles.heroCopy}><Text style={styles.name}>{facility.name}</Text><Text style={styles.address}>{facility.address || facility.town || 'Address unavailable'}</Text></View><StatusBadge status={openStatus} /></View>
        <View style={styles.metaBadges}><View style={styles.costBadge}><Text style={styles.costText}>{cost}</Text></View><VerificationBadge status={facility.verification_status} /></View>
        {facility.last_verified_at ? <Text style={styles.verifiedDate}>Last verified {new Date(facility.last_verified_at).toLocaleDateString()}</Text> : null}

        <SoftCard style={styles.section}><SectionHeader title="Accessibility and amenities" />
          {amenities.length ? <View style={styles.chips}>{amenities.map((amenity) => <View key={amenity} style={styles.chip}><Text style={styles.chipText}>{amenity}</Text></View>)}</View> : <EmptyValue>Access information unavailable</EmptyValue>}
        </SoftCard>

        <SoftCard style={styles.section}><SectionHeader title="Access notes" />
          {facility.access_notes?.trim() ? <Text style={styles.notes}>{facility.access_notes}</Text> : <EmptyValue>Access information unavailable</EmptyValue>}
        </SoftCard>

        <SoftCard style={styles.section}><SectionHeader title="Community ratings" />
          {hasRatings ? <><View style={styles.scoreRow}><Text style={styles.score}>{overallScore.toFixed(1)}</Text><View><Text style={styles.scoreCaption}>Overall score</Text><Text style={styles.scoreDetail}>Community rating data</Text></View></View><RatingRow label="Cleanliness" value={facility.cleanliness_rating} /><RatingRow label="Privacy" value={facility.privacy_rating} /><RatingRow label="Accessibility" value={facility.accessibility_rating} /><RatingRow label="Safety" value={facility.safety_rating} /><RatingRow label="Noise" value={facility.noise_rating} /><RatingRow label="Environment" value={facility.environment_rating} /></> : <EmptyValue>No community ratings yet</EmptyValue>}
        </SoftCard>

        <SoftCard style={styles.section}><SectionHeader title="Photos" />{facility.photos?.length ? <Text style={styles.photoNote}>{facility.photos.length} photo{facility.photos.length === 1 ? '' : 's'} available</Text> : <EmptyValue>No photos yet</EmptyValue>}</SoftCard>

        <SoftCard style={styles.section}><SectionHeader title="Directions" detail="Walking times are approximate. Directions use the facility’s exact coordinates." /><PrimaryButton title="Get directions" onPress={() => openMaps('google')} /><View style={styles.secondaryDirections}>{Platform.OS === 'ios' ? <Pressable accessibilityRole="button" onPress={() => openMaps('apple')} style={styles.directionOption}><Navigation size={17} color={colors.primary} /><Text style={styles.directionOptionText}>Apple Maps</Text></Pressable> : null}<Pressable accessibilityRole="button" onPress={() => openMaps('waze')} style={styles.directionOption}><Navigation size={17} color={colors.primary} /><Text style={styles.directionOptionText}>Waze</Text></Pressable></View></SoftCard>

        {/* Reporting and corrections write to the database on the user's behalf,
            so they require an account. The gate explains why before asking. */}
        <SoftCard style={styles.section}><SectionHeader title="Help keep details accurate" detail="Community updates are reviewed before publication. Signing in is required so changes can be attributed." />
          <Pressable accessibilityRole="button" accessibilityLabel="Report Issue" onPress={() => runGated('report_problem', () => navigation.navigate('ReportFacility', { facilityId }))} style={styles.actionRow}><Flag size={19} color={colors.urgent} /><Text style={styles.actionText}>Report Issue</Text></Pressable>
          <Pressable accessibilityRole="button" accessibilityLabel="Correct or Update Details" onPress={() => runGated('correct_facility_info', () => navigation.navigate('CorrectInfo', { facilityId }))} style={[styles.actionRow, styles.lastAction]}><Pencil size={19} color={colors.primary} /><Text style={styles.actionText}>Correct or Update Details</Text></Pressable>
        </SoftCard>
      </ScrollView>
    </SafeAreaView>
  </ScreenBackground>;
};

const styles = StyleSheet.create({
  safeArea: { flex: 1 }, content: { padding: spacing.lg, paddingBottom: spacing['6xl'] }, loading: { flex: 1, alignItems: 'center', justifyContent: 'center' }, stateWrap: { flex: 1, justifyContent: 'center', padding: spacing.lg }, notFound: { flex: 1, alignItems: 'center', justifyContent: 'center', padding: spacing['2xl'] }, notFoundTitle: { ...typography.h3, color: colors.textPrimary }, backTextButton: { minHeight: touchTargets.minimum, justifyContent: 'center', alignItems: 'center', marginTop: spacing.md }, backText: { ...typography.buttonSmall, color: colors.primary },
  topBar: { minHeight: touchTargets.minimum, flexDirection: 'row', alignItems: 'center', marginBottom: spacing.md }, backButton: { width: touchTargets.minimum, height: touchTargets.minimum, borderRadius: borderRadius.full, alignItems: 'center', justifyContent: 'center', backgroundColor: colors.white, marginRight: spacing.sm }, topLabel: { ...typography.buttonSmall, color: colors.textSecondary, flex: 1 }, favouriteButton: { width: touchTargets.minimum, height: touchTargets.minimum, borderRadius: borderRadius.full, alignItems: 'center', justifyContent: 'center', backgroundColor: colors.white },
  locationHeader: { flexDirection: 'row', alignItems: 'center', backgroundColor: colors.secondarySurface, marginBottom: spacing.lg }, locationIcon: { width: 52, height: 52, borderRadius: 18, alignItems: 'center', justifyContent: 'center', backgroundColor: colors.white, marginRight: spacing.md }, locationCopy: { flex: 1 }, locationKicker: { ...typography.caption, color: colors.primary, fontFamily: 'PlusJakartaSans_700Bold', letterSpacing: 0.9 }, locationText: { ...typography.bodySmall, color: colors.textPrimary, marginTop: 2 },
  warning: { backgroundColor: '#FFF4D9', marginBottom: spacing.lg }, warningTitle: { ...typography.label, color: colors.textPrimary, marginBottom: spacing.xs }, warningText: { ...typography.bodySmall, color: colors.textSecondary, marginTop: 2 }, hero: { flexDirection: 'row', alignItems: 'flex-start' }, heroCopy: { flex: 1, paddingRight: spacing.md }, name: { ...typography.h1, color: colors.textPrimary }, address: { ...typography.bodySmall, color: colors.textSecondary, marginTop: spacing.xs }, metaBadges: { flexDirection: 'row', flexWrap: 'wrap', gap: spacing.sm, marginTop: spacing.md }, costBadge: { borderRadius: borderRadius.full, backgroundColor: '#FFF4D9', paddingVertical: 5, paddingHorizontal: 10 }, costText: { ...typography.caption, color: '#8C5A0C', fontFamily: 'PlusJakartaSans_600SemiBold' }, verifiedDate: { ...typography.caption, color: colors.textMuted, marginTop: spacing.sm, marginBottom: spacing.lg },
  section: { marginBottom: spacing.md }, chips: { flexDirection: 'row', flexWrap: 'wrap', gap: spacing.sm }, chip: { borderRadius: borderRadius.full, backgroundColor: colors.secondarySurface, paddingVertical: 6, paddingHorizontal: 10 }, chipText: { ...typography.caption, color: colors.primary, fontFamily: 'PlusJakartaSans_600SemiBold' }, notes: { ...typography.bodySmall, color: colors.textPrimary, lineHeight: 22 }, scoreRow: { flexDirection: 'row', alignItems: 'center', marginBottom: spacing.lg }, score: { ...typography.score, color: colors.primary, marginRight: spacing.md }, scoreCaption: { ...typography.label, color: colors.textPrimary }, scoreDetail: { ...typography.caption, color: colors.textSecondary, marginTop: 2 }, ratingRow: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', minHeight: 35, borderTopWidth: 1, borderTopColor: colors.borderLight }, ratingLabel: { ...typography.bodySmall, color: colors.textSecondary }, ratingValueRow: { flexDirection: 'row', alignItems: 'center', gap: 5 }, ratingValue: { ...typography.label, color: colors.textPrimary }, photoNote: { ...typography.bodySmall, color: colors.textSecondary }, secondaryDirections: { flexDirection: 'row', marginTop: spacing.sm, gap: spacing.sm }, directionOption: { minHeight: touchTargets.minimum, flexDirection: 'row', alignItems: 'center', gap: 6, paddingHorizontal: spacing.md }, directionOptionText: { ...typography.buttonSmall, color: colors.primary }, actionRow: { minHeight: 52, flexDirection: 'row', alignItems: 'center', gap: spacing.md, borderTopWidth: 1, borderTopColor: colors.borderLight, marginTop: spacing.sm }, lastAction: { marginTop: 0 }, actionText: { ...typography.buttonSmall, color: colors.textPrimary },
});

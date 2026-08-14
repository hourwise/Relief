import React, { useCallback, useState } from 'react';
import Constants from 'expo-constants';
import { Alert, Linking, Pressable, ScrollView, StyleSheet, Text, View } from 'react-native';
import { useFocusEffect, useNavigation } from '@react-navigation/native';
import type { CompositeNavigationProp, NavigationProp } from '@react-navigation/native';
import type { BottomTabNavigationProp } from '@react-navigation/bottom-tabs';
import { ChevronRight, Edit3, Heart, Info, MapPin, Settings2, Trash2, FlaskConical } from 'lucide-react-native';
import type { User } from '@supabase/supabase-js';
import { Button, Input, ScreenBackground, SoftCard } from '../components';
import { colors, borderRadius, spacing, touchTargets, typography } from '../theme';
import { getAccountDetails, updateDisplayName, type AccountDetails } from '../services/account';
import { signOut } from '../services/auth';
import { useAuth } from '../context/AuthContext';
import { signInReason } from '../utils/guestAccess';
import { useLocation, type LocationStatus } from '../hooks/useLocation';
import type { MainTabParamList, RootStackParamList } from '../types';
import { RELIEF_TEST_MODE } from '../utils/env';

type ProfileNavigationProp = CompositeNavigationProp<
  BottomTabNavigationProp<MainTabParamList, 'Profile'>,
  NavigationProp<RootStackParamList>
>;

const locationStatusCopy: Record<LocationStatus, { label: string; detail: string }> = {
  loading: { label: 'Not yet resolved', detail: 'Relief has not checked this device yet.' },
  granted: { label: 'Allowed', detail: 'Relief can use your location while the app is open.' },
  denied: { label: 'Denied', detail: 'Allow location in device settings to sort by distance and use Need One Now.' },
  unavailable: { label: 'Unavailable', detail: 'Location services are off or this device could not get a fix.' },
};

function displayNameForUser(user: User | null, account: AccountDetails | null): string {
  return account?.displayName || user?.email || 'Signed in';
}

export const ProfileScreen: React.FC = () => {
  const navigation = useNavigation<ProfileNavigationProp>();
  const { isAuthenticated } = useAuth();
  const [user, setUser] = useState<User | null>(null);
  const [account, setAccount] = useState<AccountDetails | null>(null);
  const [accountError, setAccountError] = useState<string | null>(null);
  const [signingOut, setSigningOut] = useState(false);
  const [editingName, setEditingName] = useState(false);
  const [draftName, setDraftName] = useState('');
  const [savingName, setSavingName] = useState(false);
  const [nameError, setNameError] = useState<string | null>(null);
  const location = useLocation({ autoRefresh: false });

  const loadAccount = useCallback(async () => {
    if (!isAuthenticated) {
      setUser(null);
      setAccount(null);
      setAccountError(null);
      return;
    }
    const result = await getAccountDetails();
    if (result.account) {
      setUser(result.account.user);
      setAccount(result.account);
      setAccountError(null);
    } else {
      setUser(null);
      setAccount(null);
      setAccountError(result.error || 'Your account details could not be loaded.');
    }
  }, [isAuthenticated]);

  useFocusEffect(
    useCallback(() => {
      loadAccount();
    }, [loadAccount]),
  );

  const beginEditName = () => {
    setDraftName(account?.displayName || user?.email?.split('@')[0] || '');
    setNameError(null);
    setEditingName(true);
  };

  const saveName = async () => {
    setSavingName(true);
    setNameError(null);
    const result = await updateDisplayName(draftName);
    setSavingName(false);
    if (!result.success || !result.account) {
      setNameError(result.error || 'Your display name could not be saved. Please try again.');
      return;
    }
    setUser(result.account.user);
    setAccount(result.account);
    setEditingName(false);
  };

  const handleSignOut = () => {
    Alert.alert('Sign out', 'Are you sure you want to sign out?', [
      { text: 'Cancel', style: 'cancel' },
      {
        text: 'Sign out',
        style: 'destructive',
        onPress: async () => {
          setSigningOut(true);
          const result = await signOut();
          setSigningOut(false);
          if (result.error) Alert.alert('Could not sign out', 'Please try again.');
        },
      },
    ]);
  };

  const openDeviceSettings = async () => {
    try {
      await Linking.openSettings();
    } catch {
      Alert.alert('Settings unavailable', 'Open Relief in your device settings to change location permission.');
    }
  };

  const locationCopy = locationStatusCopy[location.status];
  const locationAction = location.status === 'denied' || location.status === 'unavailable'
    ? openDeviceSettings
    : location.refreshLocation;
  const locationActionLabel = location.status === 'granted' ? 'Refresh location' : location.status === 'loading' ? 'Allow location' : 'Open device settings';
  const appVersion = Constants.expoConfig?.version || 'Unavailable';
  const buildVersion = Constants.expoConfig?.android?.versionCode
    ? String(Constants.expoConfig.android.versionCode)
    : 'Not set';

  return (
    <ScreenBackground>
      <ScrollView style={styles.container} contentContainerStyle={styles.content} showsVerticalScrollIndicator={false}>
        <View style={styles.pageHeader}>
          <Text style={styles.pageTitle}>Profile</Text>
          <Text style={styles.pageSubtitle}>Your account, places, and app settings.</Text>
        </View>

        <SoftCard style={styles.accountCard}>
          <View style={styles.accountHeader}>
            <View style={styles.avatar}><Text style={styles.avatarText}>{isAuthenticated ? (displayNameForUser(user, account)[0] || 'R').toUpperCase() : 'R'}</Text></View>
            <View style={styles.accountCopy}>
              <Text style={styles.cardEyebrow}>{isAuthenticated ? 'YOUR ACCOUNT' : 'DISCOVERY WITHOUT FRICTION'}</Text>
              <Text style={styles.userName}>{isAuthenticated ? displayNameForUser(user, account) : 'Browsing as a guest'}</Text>
              {isAuthenticated && user?.email ? <Text style={styles.userMeta}>{user.email}</Text> : null}
            </View>
          </View>

          {isAuthenticated ? (
            <>
              {accountError ? <Text style={styles.errorText}>{accountError}</Text> : null}
              {editingName ? (
                <View style={styles.editForm}>
                  <Input label="Display name" value={draftName} onChangeText={setDraftName} autoFocus maxLength={80} error={nameError || undefined} />
                  <View style={styles.editActions}>
                    <Button title="Cancel" variant="ghost" size="sm" onPress={() => { setEditingName(false); setNameError(null); }} />
                    <Button title="Save name" size="sm" loading={savingName} onPress={saveName} />
                  </View>
                </View>
              ) : (
                <Pressable accessibilityRole="button" accessibilityLabel="Edit display name" onPress={beginEditName} style={styles.rowAction}>
                  <Edit3 size={18} color={colors.primary} />
                  <Text style={styles.rowActionText}>Edit display name</Text>
                  <ChevronRight size={18} color={colors.sage} />
                </Pressable>
              )}
              <Button title="Sign out" onPress={handleSignOut} variant="outline" loading={signingOut} fullWidth style={styles.accountButton} />
              <Pressable accessibilityRole="button" accessibilityLabel="Delete account" onPress={() => navigation.navigate('AccountDeletion')} style={styles.dangerAction}>
                <Trash2 size={18} color={colors.error} /><Text style={styles.dangerActionText}>Delete account</Text><ChevronRight size={18} color={colors.error} />
              </Pressable>
            </>
          ) : (
            <>
              <Text style={styles.userMeta}>Find facilities and get directions without an account. Sign in only when you want to save places or manage your account.</Text>
              <Button title="Sign in" onPress={() => navigation.navigate('Auth', { reason: signInReason('account_settings') })} variant="outline" fullWidth style={styles.accountButton} />
            </>
          )}
        </SoftCard>

        <Text style={styles.sectionLabel}>SAVED PLACES</Text>
        <SoftCard onPress={() => navigation.navigate('Home', { screen: 'Favourites' })} accessibilityLabel="Open saved places" style={styles.linkCard}>
          <View style={styles.linkIcon}><Heart size={20} color={colors.primary} /></View>
          <View style={styles.linkCopy}><Text style={styles.linkTitle}>Saved places</Text><Text style={styles.linkDetail}>Quick access to your favourite facilities.</Text></View>
          <ChevronRight size={20} color={colors.sage} />
        </SoftCard>

        <Text style={styles.sectionLabel}>LOCATION</Text>
        <SoftCard style={styles.locationCard}>
          <View style={styles.locationHeader}>
            <View style={styles.linkIcon}><MapPin size={20} color={colors.primary} /></View>
            <View style={styles.linkCopy}><Text style={styles.linkTitle}>Device location</Text><Text style={styles.linkDetail}>{locationCopy.detail}</Text></View>
          </View>
          <View style={styles.locationStatus}><View style={[styles.statusDot, location.status === 'granted' ? styles.statusDotAllowed : styles.statusDotMuted]} /><Text style={styles.statusText}>{locationCopy.label}</Text></View>
          <Button title={locationActionLabel} onPress={locationAction} variant="outline" size="sm" fullWidth style={styles.locationButton} />
        </SoftCard>

        <Text style={styles.sectionLabel}>APP INFORMATION</Text>
        <SoftCard style={styles.infoCard}>
          <View style={styles.infoRow}><View style={styles.infoIcon}><Settings2 size={18} color={colors.primary} /></View><Text style={styles.infoLabel}>Relief version</Text><Text style={styles.infoValue}>{appVersion}</Text></View>
          <View style={styles.divider} />
          <View style={styles.infoRow}><View style={styles.infoIcon}><Info size={18} color={colors.primary} /></View><Text style={styles.infoLabel}>Build</Text><Text style={styles.infoValue}>{buildVersion}</Text></View>
          <View style={styles.divider} />
          <Pressable accessibilityRole="button" accessibilityLabel="About Relief" onPress={() => navigation.navigate('AboutRelief')} style={styles.infoRow}>
            <View style={styles.infoIcon}><Info size={18} color={colors.primary} /></View><Text style={styles.infoLabel}>About Relief</Text><ChevronRight size={19} color={colors.sage} />
          </Pressable>
          <Text style={styles.previewLabel}>Preview build · core discovery is available to guests.</Text>
        </SoftCard>

        {RELIEF_TEST_MODE ? <>
          <Text style={styles.sectionLabel}>QUALITY ASSURANCE</Text>
          <SoftCard onPress={() => navigation.navigate('FeatureLab')} accessibilityLabel="Open Feature Lab" style={styles.linkCard}>
            <View style={styles.linkIcon}><FlaskConical size={20} color={colors.primary} /></View>
            <View style={styles.linkCopy}><Text style={styles.linkTitle}>Feature Lab</Text><Text style={styles.linkDetail}>Test-mode entry for readiness checks.</Text></View>
            <ChevronRight size={20} color={colors.sage} />
          </SoftCard>
        </> : null}

      </ScrollView>
    </ScreenBackground>
  );
};

const styles = StyleSheet.create({
  container: { flex: 1 },
  content: { padding: spacing.lg, paddingBottom: spacing['6xl'] },
  pageHeader: { marginBottom: spacing.lg },
  pageTitle: { ...typography.h1, color: colors.textPrimary },
  pageSubtitle: { ...typography.bodySmall, color: colors.textSecondary, marginTop: spacing.xs },
  accountCard: { backgroundColor: colors.warmWhite, borderColor: 'rgba(26, 107, 92, 0.16)', marginBottom: spacing.lg },
  accountHeader: { flexDirection: 'row', alignItems: 'center' },
  avatar: { width: 58, height: 58, borderRadius: 21, alignItems: 'center', justifyContent: 'center', backgroundColor: colors.primary, marginRight: spacing.md },
  avatarText: { ...typography.h2, color: colors.white },
  accountCopy: { flex: 1 },
  cardEyebrow: { ...typography.caption, color: colors.primary, fontFamily: 'PlusJakartaSans_700Bold', letterSpacing: 1 },
  userName: { ...typography.h3, color: colors.textPrimary, marginTop: 2 },
  userMeta: { ...typography.bodySmall, color: colors.textSecondary, lineHeight: 21, marginTop: spacing.xs },
  accountButton: { marginTop: spacing.lg },
  rowAction: { minHeight: touchTargets.minimum, flexDirection: 'row', alignItems: 'center', gap: spacing.sm, borderTopWidth: 1, borderTopColor: colors.borderLight, marginTop: spacing.lg, paddingTop: spacing.sm },
  rowActionText: { ...typography.buttonSmall, color: colors.primary, flex: 1 },
  editForm: { marginTop: spacing.lg },
  editActions: { flexDirection: 'row', justifyContent: 'flex-end', alignItems: 'center', gap: spacing.sm },
  errorText: { ...typography.caption, color: colors.error, marginTop: spacing.md },
  dangerAction: { minHeight: touchTargets.minimum, flexDirection: 'row', alignItems: 'center', gap: spacing.sm, marginTop: spacing.md },
  dangerActionText: { ...typography.buttonSmall, color: colors.error, flex: 1 },
  sectionLabel: { ...typography.caption, color: colors.textSecondary, fontFamily: 'PlusJakartaSans_700Bold', letterSpacing: 1, marginBottom: spacing.sm },
  linkCard: { minHeight: 72, flexDirection: 'row', alignItems: 'center', backgroundColor: colors.warmWhite, marginBottom: spacing.lg },
  linkIcon: { width: 42, height: 42, borderRadius: 15, alignItems: 'center', justifyContent: 'center', backgroundColor: colors.secondarySurface, marginRight: spacing.md },
  linkCopy: { flex: 1, paddingRight: spacing.sm },
  linkTitle: { ...typography.label, color: colors.textPrimary },
  linkDetail: { ...typography.caption, color: colors.textSecondary, lineHeight: 18, marginTop: 2 },
  locationCard: { backgroundColor: colors.warmWhite, marginBottom: spacing.lg },
  locationHeader: { flexDirection: 'row', alignItems: 'center' },
  locationStatus: { alignSelf: 'flex-start', flexDirection: 'row', alignItems: 'center', gap: spacing.sm, marginTop: spacing.md, paddingVertical: spacing.xs, paddingHorizontal: spacing.sm, borderRadius: borderRadius.full, backgroundColor: colors.secondarySurface },
  statusDot: { width: 8, height: 8, borderRadius: 4 },
  statusDotAllowed: { backgroundColor: colors.primary },
  statusDotMuted: { backgroundColor: colors.sage },
  statusText: { ...typography.caption, color: colors.primary, fontFamily: 'PlusJakartaSans_700Bold' },
  locationButton: { marginTop: spacing.md },
  infoCard: { backgroundColor: colors.warmWhite, marginBottom: spacing.lg },
  infoRow: { minHeight: 44, flexDirection: 'row', alignItems: 'center' },
  infoIcon: { width: 30, alignItems: 'flex-start' },
  infoLabel: { ...typography.bodySmall, color: colors.textPrimary, flex: 1 },
  infoValue: { ...typography.bodySmall, color: colors.textSecondary },
  divider: { height: 1, backgroundColor: colors.borderLight },
  previewLabel: { ...typography.caption, color: colors.textMuted, lineHeight: 18, marginTop: spacing.md },
  pressed: { opacity: 0.82 },
});

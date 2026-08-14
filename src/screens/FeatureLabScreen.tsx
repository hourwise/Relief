import React from 'react';
import { ScrollView, StyleSheet, Text, View } from 'react-native';
import { CommonActions, useNavigation } from '@react-navigation/native';
import type { NativeStackNavigationProp } from '@react-navigation/native-stack';
import { Button, ScreenBackground, SoftCard } from '../components';
import { colors, spacing, typography } from '../theme';
import { RELIEF_TEST_MODE } from '../utils/env';
import type { RootStackParamList } from '../types';

type Navigation = NativeStackNavigationProp<RootStackParamList, 'FeatureLab'>;

export const FeatureLabScreen: React.FC = () => {
  const navigation = useNavigation<Navigation>();
  if (!RELIEF_TEST_MODE) return <ScreenBackground><View style={styles.blocked}><Text style={styles.title}>Feature Lab unavailable</Text><Text style={styles.body}>Enable EXPO_PUBLIC_RELIEF_TEST_MODE only in a disposable QA build.</Text></View></ScreenBackground>;

  const openAdvancedFilters = () => navigation.dispatch(CommonActions.navigate({ name: 'Main', params: { screen: 'Find', params: { screen: 'AdvancedFilters' } } }));
  return <ScreenBackground><ScrollView contentContainerStyle={styles.content}>
    <SoftCard style={styles.card}>
      <Text style={styles.title}>Feature Lab</Text>
      <Text style={styles.badge}>TEST MODE — simulated and unavailable operations are marked</Text>
      <Text style={styles.body}>This hidden QA surface exercises existing screens without service-role credentials, auth bypasses, production uploads, or real purchases.</Text>
      <View style={styles.buttons}>
        <Button title="Advanced filters" onPress={openAdvancedFilters} variant="outline" fullWidth />
        <Button title="Saved profiles (backend-dependent)" onPress={() => navigation.navigate('SavedProfiles')} variant="outline" fullWidth />
        <Button title="Route planning (straight-line)" onPress={() => navigation.navigate('RoutePlanning')} variant="outline" fullWidth />
        <Button title="Offline facility data" onPress={() => navigation.navigate('OfflineMaps')} variant="outline" fullWidth />
        <Button title="Local notification alerts" onPress={() => navigation.navigate('NotificationAlerts')} variant="outline" fullWidth />
        <Button title="Premium test gate" onPress={() => navigation.navigate('Paywall')} variant="outline" fullWidth />
        <Button title="Photo flow" onPress={() => navigation.navigate('PhotoFlow')} variant="outline" fullWidth />
        <Button title="Account deletion request" onPress={() => navigation.navigate('AccountDeletion')} variant="outline" fullWidth />
        <Button title="Legal and support state" onPress={() => navigation.navigate('LegalInfo')} variant="outline" fullWidth />
        <Button title="Password recovery entry" onPress={() => navigation.navigate('Auth', undefined)} variant="outline" fullWidth />
      </View>
    </SoftCard>
  </ScrollView></ScreenBackground>;
};

const styles = StyleSheet.create({
  content: { padding: spacing.lg, paddingBottom: spacing['6xl'] },
  card: { marginTop: spacing.lg },
  blocked: { flex: 1, justifyContent: 'center', padding: spacing.xl },
  title: { ...typography.h2, color: colors.textPrimary, marginBottom: spacing.md },
  body: { ...typography.body, color: colors.textSecondary, lineHeight: 23 },
  badge: { ...typography.caption, color: colors.warning, marginBottom: spacing.md },
  buttons: { gap: spacing.sm, marginTop: spacing.xl },
});

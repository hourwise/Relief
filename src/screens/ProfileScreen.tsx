// ============================================================
// Project "Relief" — Profile Screen
// ============================================================
// Every action here is checked against a registered route. The
// preview build hides features that are not finished rather than
// offering buttons that navigate nowhere:
//
//   AI recommendations, predictive suggestions, route planning,
//   offline maps, notification alerts, what3words/location
//   sharing, saved profiles, purchases and paywalls, photo
//   uploads, community badges, community management.
//
// Their screens still exist in src/screens/ but are not routed.
// About Relief is kept.
// ============================================================

import React, { useCallback, useState } from 'react';
import { Alert, ScrollView, StyleSheet, Text, View } from 'react-native';
import { useFocusEffect, useNavigation } from '@react-navigation/native';
import type { NavigationProp } from '@react-navigation/native';
import type { User } from '@supabase/supabase-js';
import { colors, spacing, typography } from '../theme';
import { Button, SoftCard } from '../components';
import { getCurrentUser, signOut } from '../services/auth';
import { useAuth } from '../context/AuthContext';
import { signInReason } from '../utils/guestAccess';
import type { RootStackParamList } from '../types';

export const ProfileScreen: React.FC = () => {
  const navigation = useNavigation<NavigationProp<RootStackParamList>>();
  const { isAuthenticated } = useAuth();
  const [user, setUser] = useState<User | null>(null);
  const [signingOut, setSigningOut] = useState(false);

  useFocusEffect(
    useCallback(() => {
      let cancelled = false;
      if (!isAuthenticated) {
        setUser(null);
        return;
      }
      getCurrentUser()
        .then((current) => {
          if (!cancelled) setUser(current);
        })
        .catch(() => {
          if (!cancelled) setUser(null);
        });
      return () => {
        cancelled = true;
      };
    }, [isAuthenticated]),
  );

  const handleSignOut = () => {
    Alert.alert('Sign out', 'Are you sure you want to sign out?', [
      { text: 'Cancel', style: 'cancel' },
      {
        text: 'Sign out',
        style: 'destructive',
        onPress: async () => {
          setSigningOut(true);
          await signOut();
          setSigningOut(false);
        },
      },
    ]);
  };

  return (
    <ScrollView style={styles.container} contentContainerStyle={styles.content}>
      <SoftCard style={styles.profileCard}>
        {isAuthenticated && user ? (
          <>
            <Text style={styles.userName}>
              {user.user_metadata?.full_name || user.email || 'Signed in'}
            </Text>
            {user.email ? <Text style={styles.userMeta}>{user.email}</Text> : null}
            <Button
              title="Sign Out"
              onPress={handleSignOut}
              variant="outline"
              loading={signingOut}
              fullWidth
              style={styles.actionButton}
            />
          </>
        ) : (
          <>
            <Text style={styles.userName}>Browsing as a guest</Text>
            <Text style={styles.userMeta}>
              Finding facilities, searching and getting directions never require an
              account. {signInReason('save_favourite')}
            </Text>
            <Button
              title="Sign In"
              onPress={() =>
                navigation.navigate('Auth', {
                  reason: signInReason('account_settings'),
                })
              }
              variant="outline"
              fullWidth
              style={styles.actionButton}
            />
          </>
        )}
      </SoftCard>

      <SoftCard style={styles.section}>
        <Text style={styles.sectionTitle}>About</Text>
        <Text style={styles.sectionDescription}>
          Relief v1.0.0 — helping you find safe, clean facilities.
        </Text>
        <Button
          title="About Relief"
          onPress={() => navigation.navigate('AboutRelief')}
          variant="outline"
          fullWidth
          size="sm"
          style={styles.actionButton}
        />
      </SoftCard>

      <SoftCard style={styles.section}>
        <Text style={styles.sectionTitle}>This is a preview build</Text>
        <Text style={styles.sectionDescription}>
          Route planning, offline maps, alerts, location sharing, saved profiles and
          community badges are still in development and are hidden until they work
          end to end. Facility data comes from the live database.
        </Text>
      </SoftCard>
    </ScrollView>
  );
};

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: colors.background },
  content: { padding: spacing.lg, paddingBottom: spacing['6xl'] },
  profileCard: { alignItems: 'flex-start', marginBottom: spacing.lg },
  userName: { ...typography.h3, color: colors.textPrimary, marginBottom: spacing.xs },
  userMeta: {
    ...typography.bodySmall,
    color: colors.textSecondary,
    lineHeight: 21,
  },
  section: { marginBottom: spacing.lg },
  sectionTitle: { ...typography.h4, color: colors.textPrimary, marginBottom: spacing.xs },
  sectionDescription: {
    ...typography.bodySmall,
    color: colors.textSecondary,
    lineHeight: 21,
  },
  actionButton: { marginTop: spacing.md },
});

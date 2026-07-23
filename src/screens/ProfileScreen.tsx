// ============================================================
// Project "Relief" — Profile Screen
// ============================================================

import React, { useState, useEffect } from 'react';
import { View, Text, StyleSheet, ScrollView, Alert } from 'react-native';
import { colors, typography, spacing } from '../theme';
import { Card, Button } from '../components';
import { getCurrentUser, signOut } from '../services/auth';
import { getUserBadges } from '../services/community';
import { useSubscription } from '../context/SubscriptionContext';
import type { User } from '@supabase/supabase-js';
import type { Badge } from '../types/community';
import { useNavigation, NavigationProp } from '@react-navigation/native';

export const ProfileScreen: React.FC = () => {
  const navigation = useNavigation<NavigationProp<any>>();
  const { tier, isActive, isBasicAccess, isPlusSubscriber, isLifetime, expiresAt } = useSubscription();
  const [user, setUser] = useState<User | null>(null);
  const [badges, setBadges] = useState<Badge[]>([]);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    loadUser();
    loadBadges();
  }, []);

  const loadUser = async () => {
    const currentUser = await getCurrentUser();
    setUser(currentUser);
  };

  const loadBadges = async () => {
    const userBadges = await getUserBadges();
    setBadges(userBadges);
  };

  const handleSignOut = () => {
    Alert.alert('Sign Out', 'Are you sure you want to sign out?', [
      { text: 'Cancel', style: 'cancel' },
      {
        text: 'Sign Out',
        style: 'destructive',
        onPress: async () => {
          setLoading(true);
          await signOut();
          setLoading(false);
        },
      },
    ]);
  };

  const badgeIcons: Record<string, string> = {
    explorer: '🌍',
    community_hero: '🦸',
    accessibility_champion: '♿',
    family_helper: '👨‍👩‍👧‍👧',
  };

  return (
    <ScrollView style={styles.container} contentContainerStyle={styles.content}>
      {/* User Info */}
      <Card variant="elevated" style={styles.profileCard}>
        <View style={styles.avatar}>
          <Text style={styles.avatarText}>👤</Text>
        </View>
        {user ? (
          <>
            <Text style={styles.userName}>
              {user.user_metadata?.full_name || user.email || 'User'}
            </Text>
            <Text style={styles.userEmail}>{user.email}</Text>
            <Button
              title="Sign Out"
              onPress={handleSignOut}
              variant="outline"
              loading={loading}
              fullWidth
              style={styles.signOutButton}
            />
          </>
        ) : (
          <>
            <Text style={styles.userName}>Not signed in</Text>
            <Text style={styles.userEmail}>
              Sign in to access your favourites, saved profiles and more
            </Text>
          </>
        )}
      </Card>

      {/* AI Recommendations */}
      <Card variant="outlined" style={styles.section}>
        <Text style={styles.sectionTitle}>AI Recommendations</Text>
        <Text style={styles.sectionDescription}>
          Smart facility recommendations matched to your saved profiles and preferences.
        </Text>
        <Button
          title="Get Recommendations"
          onPress={() => navigation.navigate('AIRecommendations')}
          variant="outline"
          fullWidth
          size="sm"
        />
      </Card>

      {/* Predictive Suggestions */}
      <Card variant="outlined" style={styles.section}>
        <Text style={styles.sectionTitle}>Predictive Suggestions</Text>
        <Text style={styles.sectionDescription}>
          Find the next suitable facility ahead in your direction of travel.
        </Text>
        <Button
          title="Look Ahead"
          onPress={() => navigation.navigate('PredictiveSuggestions')}
          variant="outline"
          fullWidth
          size="sm"
        />
      </Card>

      {/* Route Planning */}
      <Card variant="outlined" style={styles.section}>
        <Text style={styles.sectionTitle}>Route Planning</Text>
        <Text style={styles.sectionDescription}>
          Plan a journey with comfort stops every 60-90 minutes.
        </Text>
        <Button
          title="Plan a Route"
          onPress={() => navigation.navigate('RoutePlanning')}
          variant="outline"
          fullWidth
          size="sm"
        />
      </Card>

      {/* Offline Maps */}
      <Card variant="outlined" style={styles.section}>
        <Text style={styles.sectionTitle}>Offline Maps</Text>
        <Text style={styles.sectionDescription}>
          Download facility data for offline use when you don't have internet.
        </Text>
        <Button
          title="Manage Offline Maps"
          onPress={() => navigation.navigate('OfflineMaps')}
          variant="outline"
          fullWidth
          size="sm"
        />
      </Card>

      {/* Notification Alerts */}
      <Card variant="outlined" style={styles.section}>
        <Text style={styles.sectionTitle}>Notification Alerts</Text>
        <Text style={styles.sectionDescription}>
          Get notified about closures and updates for your favourite facilities.
        </Text>
        <Button
          title="Manage Alerts"
          onPress={() => navigation.navigate('NotificationAlerts')}
          variant="outline"
          fullWidth
          size="sm"
        />
      </Card>

      {/* Location Sharing */}
      <Card variant="outlined" style={styles.section}>
        <Text style={styles.sectionTitle}>Location Sharing</Text>
        <Text style={styles.sectionDescription}>
          Share your location via What3Words, Plus Codes, or emergency card.
        </Text>
        <Button
          title="Share Location"
          onPress={() => navigation.navigate('LocationSharing')}
          variant="outline"
          fullWidth
          size="sm"
        />
      </Card>

      {/* Saved Profiles */}
      <Card variant="outlined" style={styles.section}>
        <Text style={styles.sectionTitle}>Saved Profiles</Text>
        <Text style={styles.sectionDescription}>
          Create preference profiles to quickly filter facilities.
        </Text>
        <Button
          title="Manage Profiles"
          onPress={() => navigation.navigate('SavedProfiles')}
          variant="outline"
          fullWidth
          size="sm"
        />
      </Card>

      {/* Badges */}
      <Card variant="outlined" style={styles.section}>
        <Text style={styles.sectionTitle}>Badges</Text>
        {badges.length > 0 ? (
          <View style={styles.badgesList}>
            {badges.map((badge) => (
              <View key={badge.id} style={styles.badgeItem}>
                <Text style={styles.badgeIcon}>
                  {badgeIcons[badge.badge_type] || '🏅'}
                </Text>
                <View style={styles.badgeInfo}>
                  <Text style={styles.badgeName}>
                    {badge.badge_type.replace(/_/g, ' ').replace(/\b\w/g, (l) => l.toUpperCase())}
                  </Text>
                  <Text style={styles.badgeSource}>{badge.source}</Text>
                </View>
              </View>
            ))}
          </View>
        ) : (
          <Text style={styles.sectionDescription}>
            Contribute to the community to earn badges
          </Text>
        )}
      </Card>

      {/* Access Level */}
      <Card variant="outlined" style={styles.section}>
        <Text style={styles.sectionTitle}>Access Level</Text>
        {isPlusSubscriber ? (
          <>
            <Text style={styles.accessLevel}>Plus</Text>
            <Text style={styles.sectionDescription}>
              {isLifetime
                ? 'Lifetime access — thank you for your support!'
                : expiresAt
                ? `Active until ${new Date(expiresAt).toLocaleDateString()}`
                : 'Active subscription'}
            </Text>
          </>
        ) : isBasicAccess ? (
          <>
            <Text style={styles.accessLevel}>Basic Access</Text>
            <Text style={styles.sectionDescription}>
              Lifetime access — thank you for your support!
            </Text>
          </>
        ) : (
          <>
            <Text style={styles.accessLevel}>Free Tier</Text>
            <Text style={styles.sectionDescription}>
              Upgrade to Plus for route planning, offline maps, AI recommendations
              and more.
            </Text>
            <Button
              title="See Plans"
              onPress={() => navigation.navigate('Paywall')}
              variant="outline"
              fullWidth
              style={styles.upgradeButton}
            />
          </>
        )}
      </Card>

      {/* App Info */}
      <Card variant="outlined" style={styles.section}>
        <Text style={styles.sectionTitle}>About</Text>
        <Text style={styles.appInfo}>Relief v1.0.0</Text>
        <Text style={styles.appInfo}>Helping you find safe, clean facilities</Text>
      </Card>
    </ScrollView>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: colors.background,
  },
  content: {
    padding: spacing.lg,
    paddingBottom: spacing['6xl'],
  },
  profileCard: {
    alignItems: 'center',
    marginBottom: spacing.lg,
  },
  avatar: {
    width: 80,
    height: 80,
    borderRadius: 40,
    backgroundColor: colors.gray100,
    justifyContent: 'center',
    alignItems: 'center',
    marginBottom: spacing.md,
  },
  avatarText: {
    fontSize: 36,
  },
  userName: {
    ...typography.h3,
    color: colors.textPrimary,
    marginBottom: spacing.xs,
  },
  userEmail: {
    ...typography.bodySmall,
    color: colors.textSecondary,
    textAlign: 'center',
    marginBottom: spacing.lg,
  },
  signOutButton: {
    marginTop: spacing.sm,
  },
  section: {
    marginBottom: spacing.lg,
  },
  sectionTitle: {
    ...typography.h4,
    color: colors.textPrimary,
    marginBottom: spacing.sm,
  },
  sectionDescription: {
    ...typography.bodySmall,
    color: colors.textSecondary,
    marginBottom: spacing.md,
  },
  accessLevel: {
    ...typography.h2,
    color: colors.primary,
    marginBottom: spacing.xs,
  },
  upgradeButton: {
    marginTop: spacing.sm,
  },
  badgesList: {
    gap: spacing.sm,
  },
  badgeItem: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingVertical: spacing.xs,
  },
  badgeIcon: {
    fontSize: 24,
    marginRight: spacing.md,
  },
  badgeInfo: {
    flex: 1,
  },
  badgeName: {
    ...typography.bodySmall,
    color: colors.textPrimary,
    fontWeight: '600',
  },
  badgeSource: {
    ...typography.caption,
    color: colors.textSecondary,
  },
  appInfo: {
    ...typography.bodySmall,
    color: colors.textSecondary,
    marginBottom: spacing.xs,
  },
});
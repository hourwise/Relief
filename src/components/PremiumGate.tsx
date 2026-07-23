// ============================================================
// Project "Relief" — PremiumGate Component (4.18)
// Paywall gating for premium features
// Shows a locked overlay with upgrade CTA when feature is locked
// ============================================================

import React from 'react';
import {
  View,
  Text,
  StyleSheet,
  TouchableOpacity,
} from 'react-native';
import { colors, typography, spacing } from '../theme';
import { useSubscription, PremiumFeature } from '../context/SubscriptionContext';
import { useNavigation, NavigationProp } from '@react-navigation/native';

interface PremiumGateProps {
  feature: PremiumFeature;
  title?: string;
  description?: string;
  icon?: string;
  children: React.ReactNode;
}

const featureLabels: Record<PremiumFeature, { title: string; description: string; icon: string }> = {
  route_planning: {
    title: 'Route Planning',
    description: 'Plan journeys with comfort stops every 60-90 minutes.',
    icon: '🗺️',
  },
  offline_maps: {
    title: 'Offline Maps',
    description: 'Download facility data for offline use.',
    icon: '📡',
  },
  saved_profiles: {
    title: 'Saved Profiles',
    description: 'Create preference profiles for quick filtering.',
    icon: '👤',
  },
  ai_recommendations: {
    title: 'AI Recommendations',
    description: 'Smart facility recommendations based on your needs.',
    icon: '🤖',
  },
  travel_support: {
    title: 'Travel Support',
    description: 'Dedicated travel assistance and support.',
    icon: '✈️',
  },
  europe_expansion: {
    title: 'Europe Expansion',
    description: 'Access facilities across Europe.',
    icon: '🌍',
  },
  smart_alerts: {
    title: 'Smart Alerts',
    description: 'Get notified about closures and updates.',
    icon: '🔔',
  },
};

export const PremiumGate: React.FC<PremiumGateProps> = ({
  feature,
  title,
  description,
  icon,
  children,
}) => {
  const { isFeatureLocked, loading } = useSubscription();
  const navigation = useNavigation<NavigationProp<any>>();

  const locked = isFeatureLocked(feature);

  if (loading) {
    return <>{children}</>;
  }

  if (!locked) {
    return <>{children}</>;
  }

  const labels = featureLabels[feature];

  return (
    <View style={styles.container}>
      {/* The actual content is rendered but blurred/overlaid */}
      <View style={styles.contentWrapper}>
        <View style={styles.blurOverlay} />
        {children}
      </View>

      {/* Lock overlay */}
      <View style={styles.lockOverlay}>
        <View style={styles.lockCard}>
          <Text style={styles.lockIcon}>{icon || labels.icon}</Text>
          <Text style={styles.lockTitle}>{title || labels.title}</Text>
          <Text style={styles.lockDescription}>
            {description || labels.description}
          </Text>
          <Text style={styles.lockSubtext}>
            This is a Plus feature. Upgrade to unlock.
          </Text>
          <TouchableOpacity
            style={styles.upgradeButton}
            onPress={() => navigation.navigate('Paywall')}
            activeOpacity={0.8}
          >
            <Text style={styles.upgradeButtonText}>See Plans</Text>
          </TouchableOpacity>
        </View>
      </View>
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    position: 'relative',
  },
  contentWrapper: {
    position: 'relative',
    opacity: 0.3,
    maxHeight: 300,
    overflow: 'hidden',
  },
  blurOverlay: {
    ...StyleSheet.absoluteFill,
    backgroundColor: 'rgba(255,255,255,0.5)',
    zIndex: 1,
  },
  lockOverlay: {
    ...StyleSheet.absoluteFill,
    justifyContent: 'center',
    alignItems: 'center',
    zIndex: 10,
  },
  lockCard: {
    backgroundColor: colors.white,
    borderRadius: 16,
    padding: spacing.xl,
    alignItems: 'center',
    marginHorizontal: spacing.xl,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.15,
    shadowRadius: 12,
    elevation: 8,
    maxWidth: 320,
  },
  lockIcon: {
    fontSize: 48,
    marginBottom: spacing.md,
  },
  lockTitle: {
    ...typography.h3,
    color: colors.textPrimary,
    textAlign: 'center',
    marginBottom: spacing.sm,
  },
  lockDescription: {
    ...typography.bodySmall,
    color: colors.textSecondary,
    textAlign: 'center',
    marginBottom: spacing.sm,
  },
  lockSubtext: {
    ...typography.caption,
    color: colors.primary,
    textAlign: 'center',
    marginBottom: spacing.lg,
    fontWeight: '600',
  },
  upgradeButton: {
    backgroundColor: colors.primary,
    paddingHorizontal: spacing.xl,
    paddingVertical: spacing.md,
    borderRadius: 12,
    minWidth: 160,
    alignItems: 'center',
  },
  upgradeButtonText: {
    ...typography.button,
    color: colors.white,
  },
});
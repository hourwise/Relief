// ============================================================
// Project "Relief" — Paywall Screen (4.13 / 4.14)
// Basic Access (£1.99 lifetime) and Plus (£1.99/mo or £14.99/yr)
// ============================================================

import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TouchableOpacity,
  Alert,
  ActivityIndicator,
} from 'react-native';
import { colors, typography, spacing } from '../theme';
import { Card, Button } from '../components';
import { useSubscription } from '../context/SubscriptionContext';
import { getOfferings } from '../services/revenuecat';
import { useNavigation } from '@react-navigation/native';
import type { PurchasesPackage, PurchasesOffering } from 'react-native-purchases';

type PlanType = 'basic' | 'plus_monthly' | 'plus_yearly';

interface PlanInfo {
  key: PlanType;
  title: string;
  price: string;
  period: string;
  description: string;
  features: string[];
  icon: string;
  isPopular?: boolean;
}

const PLANS: PlanInfo[] = [
  {
    key: 'basic',
    title: 'Basic Access',
    price: '£1.99',
    period: 'lifetime',
    description: 'Everything you need for everyday use.',
    icon: '🔑',
    features: [
      'Maps & Search',
      'Ratings & Reviews',
      'Directions (Google/Apple/Waze)',
      'Community updates',
      'Favourites',
    ],
  },
  {
    key: 'plus_monthly',
    title: 'Plus Monthly',
    price: '£1.99',
    period: '/month',
    description: 'The complete Relief experience.',
    icon: '⭐',
    isPopular: true,
    features: [
      'Everything in Basic',
      'Route Planning',
      'Offline Maps',
      'AI Recommendations',
      'Saved Profiles',
      'Travel Support',
      'Europe Expansion',
      'Smart Alerts',
    ],
  },
  {
    key: 'plus_yearly',
    title: 'Plus Yearly',
    price: '£14.99',
    period: '/year',
    description: 'Best value — save 37% vs monthly.',
    icon: '🌟',
    features: [
      'Everything in Plus Monthly',
      'Priority Support',
      'Early Access to new features',
    ],
  },
];

export const PaywallScreen: React.FC = () => {
  const navigation = useNavigation();
  const { tier, isActive, purchase, restore, loading } = useSubscription();
  const [selectedPlan, setSelectedPlan] = useState<PlanType>('plus_monthly');
  const [purchasing, setPurchasing] = useState(false);
  const [restoring, setRestoring] = useState(false);
  const [offerings, setOfferings] = useState<PurchasesOffering | null>(null);

  useEffect(() => {
    loadOfferings();
  }, []);

  const loadOfferings = async () => {
    const current = await getOfferings();
    setOfferings(current);
  };

  const handlePurchase = async () => {
    if (!offerings) {
      Alert.alert('Error', 'Unable to load purchase options. Please try again.');
      return;
    }

    setPurchasing(true);

    try {
      // Find the appropriate package from RevenueCat offerings
      let pack: PurchasesPackage | undefined;

      if (selectedPlan === 'basic') {
        pack = offerings.lifetime ?? undefined;
      } else if (selectedPlan === 'plus_monthly') {
        pack = offerings.monthly ?? undefined;
      } else if (selectedPlan === 'plus_yearly') {
        pack = offerings.annual ?? undefined;
      }

      if (!pack) {
        // Fallback: use any available package
        const allPackages = offerings.availablePackages;
        if (allPackages && allPackages.length > 0) {
          pack = allPackages[0];
        }
      }

      if (!pack) {
        Alert.alert(
          'Not Available',
          'This purchase option is not currently available. Please try again later.',
        );
        setPurchasing(false);
        return;
      }

      const result = await purchase(pack);

      if (result.success) {
        Alert.alert(
          'Welcome to Relief Plus!',
          'You now have access to all premium features.',
        );
        navigation.goBack();
      } else if (result.error !== 'Purchase cancelled') {
        Alert.alert('Purchase Failed', result.error || 'Please try again.');
      }
    } catch (error: any) {
      Alert.alert('Purchase Failed', error.message || 'Please try again.');
    } finally {
      setPurchasing(false);
    }
  };

  const handleRestore = async () => {
    setRestoring(true);
    const result = await restore();
    setRestoring(false);

    if (result.success) {
      Alert.alert(
        'Purchases Restored',
        'Your previous purchases have been restored.',
      );
      navigation.goBack();
    } else {
      Alert.alert(
        'Restore Failed',
        result.error || 'No previous purchases found.',
      );
    }
  };

  // If already subscribed, show current plan
  if (isActive && tier !== 'free') {
    return (
      <ScrollView style={styles.container} contentContainerStyle={styles.content}>
        <View style={styles.header}>
          <Text style={styles.headerIcon}>
            {tier === 'plus' ? '⭐' : '🔑'}
          </Text>
          <Text style={styles.headerTitle}>
            You're on {tier === 'plus' ? 'Plus' : 'Basic Access'}
          </Text>
          <Text style={styles.headerSubtext}>
            Thank you for supporting Relief!
          </Text>
        </View>

        <Card variant="elevated" style={styles.currentPlanCard}>
          <Text style={styles.currentPlanLabel}>Current Plan</Text>
          <Text style={styles.currentPlanName}>
            {tier === 'plus' ? 'Plus' : 'Basic Access'}
          </Text>
          {tier === 'plus' && (
            <Text style={styles.currentPlanFeatures}>
              Route Planning • Offline Maps • AI Recommendations • Saved Profiles
            </Text>
          )}
        </Card>

        <Button
          title="Restore Purchases"
          onPress={handleRestore}
          variant="outline"
          loading={restoring}
          fullWidth
        />
      </ScrollView>
    );
  }

  return (
    <ScrollView style={styles.container} contentContainerStyle={styles.content}>
      {/* Header */}
      <View style={styles.header}>
        <Text style={styles.headerIcon}>⭐</Text>
        <Text style={styles.headerTitle}>Upgrade to Plus</Text>
        <Text style={styles.headerSubtext}>
          Get the most out of Relief with premium features
        </Text>
      </View>

      {/* Plan Selection */}
      <View style={styles.plansContainer}>
        {PLANS.map((plan) => {
          const isSelected = selectedPlan === plan.key;
          return (
            <TouchableOpacity
              key={plan.key}
              style={[
                styles.planCard,
                isSelected && styles.planCardSelected,
                plan.isPopular && styles.planCardPopular,
              ]}
              onPress={() => setSelectedPlan(plan.key)}
              activeOpacity={0.7}
            >
              {plan.isPopular && (
                <View style={styles.popularBadge}>
                  <Text style={styles.popularBadgeText}>Most Popular</Text>
                </View>
              )}
              <Text style={styles.planIcon}>{plan.icon}</Text>
              <Text style={[styles.planTitle, isSelected && styles.planTitleSelected]}>
                {plan.title}
              </Text>
              <View style={styles.planPriceRow}>
                <Text style={[styles.planPrice, isSelected && styles.planPriceSelected]}>
                  {plan.price}
                </Text>
                <Text style={styles.planPeriod}>{plan.period}</Text>
              </View>
              <Text style={styles.planDescription}>{plan.description}</Text>
              <View style={styles.planFeatures}>
                {plan.features.map((feature, i) => (
                  <View key={i} style={styles.featureRow}>
                    <Text style={styles.featureBullet}>✓</Text>
                    <Text style={styles.featureText}>{feature}</Text>
                  </View>
                ))}
              </View>
            </TouchableOpacity>
          );
        })}
      </View>

      {/* Purchase Button */}
      <Button
        title={
          selectedPlan === 'basic'
            ? 'Get Basic Access — £1.99'
            : selectedPlan === 'plus_monthly'
            ? 'Subscribe — £1.99/month'
            : 'Subscribe — £14.99/year'
        }
        onPress={handlePurchase}
        loading={purchasing}
        fullWidth
        style={styles.purchaseButton}
      />

      {/* Restore */}
      <Button
        title="Restore Purchases"
        onPress={handleRestore}
        variant="outline"
        loading={restoring}
        fullWidth
        style={styles.restoreButton}
      />

      {/* Footer */}
      <Text style={styles.footerText}>
        Your purchase will be processed through your App Store or Google Play account.
        Subscriptions auto-renew unless cancelled at least 24 hours before the end of
        the current period. Manage subscriptions in your account settings.
      </Text>
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
  header: {
    alignItems: 'center',
    marginBottom: spacing.xl,
    marginTop: spacing.lg,
  },
  headerIcon: {
    fontSize: 48,
    marginBottom: spacing.md,
  },
  headerTitle: {
    ...typography.h2,
    color: colors.textPrimary,
    textAlign: 'center',
    marginBottom: spacing.xs,
  },
  headerSubtext: {
    ...typography.bodySmall,
    color: colors.textSecondary,
    textAlign: 'center',
  },
  plansContainer: {
    gap: spacing.lg,
    marginBottom: spacing.xl,
  },
  planCard: {
    backgroundColor: colors.white,
    borderRadius: 16,
    padding: spacing.lg,
    borderWidth: 2,
    borderColor: colors.border,
    position: 'relative',
  },
  planCardSelected: {
    borderColor: colors.primary,
    backgroundColor: colors.white,
  },
  planCardPopular: {
    borderColor: colors.primary,
    backgroundColor: '#FEF9F0',
  },
  popularBadge: {
    position: 'absolute',
    top: -12,
    right: spacing.lg,
    backgroundColor: colors.primary,
    paddingHorizontal: spacing.md,
    paddingVertical: spacing.xs,
    borderRadius: 20,
  },
  popularBadgeText: {
    ...typography.caption,
    color: colors.white,
    fontWeight: '700',
  },
  planIcon: {
    fontSize: 32,
    marginBottom: spacing.sm,
  },
  planTitle: {
    ...typography.h3,
    color: colors.textPrimary,
    marginBottom: spacing.xs,
  },
  planTitleSelected: {
    color: colors.primary,
  },
  planPriceRow: {
    flexDirection: 'row',
    alignItems: 'baseline',
    marginBottom: spacing.xs,
  },
  planPrice: {
    ...typography.h1,
    color: colors.textPrimary,
    fontSize: 28,
  },
  planPriceSelected: {
    color: colors.primary,
  },
  planPeriod: {
    ...typography.bodySmall,
    color: colors.textSecondary,
    marginLeft: spacing.xs,
  },
  planDescription: {
    ...typography.bodySmall,
    color: colors.textSecondary,
    marginBottom: spacing.md,
  },
  planFeatures: {
    gap: spacing.sm,
  },
  featureRow: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  featureBullet: {
    ...typography.bodySmall,
    color: colors.success || '#22C55E',
    fontWeight: '700',
    marginRight: spacing.sm,
    width: 20,
  },
  featureText: {
    ...typography.bodySmall,
    color: colors.textPrimary,
    flex: 1,
  },
  purchaseButton: {
    marginBottom: spacing.md,
  },
  restoreButton: {
    marginBottom: spacing.xl,
  },
  footerText: {
    ...typography.caption,
    color: colors.textSecondary,
    textAlign: 'center',
    lineHeight: 18,
  },
  currentPlanCard: {
    alignItems: 'center',
    marginBottom: spacing.lg,
  },
  currentPlanLabel: {
    ...typography.caption,
    color: colors.textSecondary,
    marginBottom: spacing.xs,
  },
  currentPlanName: {
    ...typography.h2,
    color: colors.primary,
    marginBottom: spacing.sm,
  },
  currentPlanFeatures: {
    ...typography.bodySmall,
    color: colors.textSecondary,
    textAlign: 'center',
  },
});
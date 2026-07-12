// ============================================================
// Project "Relief" — Report Facility Screen (2.3)
// Temporary reports: closure, out of order, cleaning, busy, etc.
// ============================================================

import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TextInput,
  TouchableOpacity,
  Alert,
} from 'react-native';
import { colors, typography, spacing, borderRadius } from '../theme';
import { Button, Card } from '../components';
import { submitTemporaryReport, getActiveReports, resolveOwnReport } from '../services/community';
import { useRoute, useNavigation, NavigationProp, RouteProp } from '@react-navigation/native';
import type { MapStackParamList } from '../types';
import type { TemporaryReport } from '../types/community';

type ReportType = TemporaryReport['type'];

const REPORT_TYPES: { type: ReportType; label: string; icon: string; description: string; durationHours: number }[] = [
  { type: 'closed', label: 'Closed', icon: '🔒', description: 'Facility is currently closed', durationHours: 2 },
  { type: 'out_of_order', label: 'Out of Order', icon: '🔧', description: 'Facility is out of service', durationHours: 4 },
  { type: 'cleaning', label: 'Cleaning', icon: '🧹', description: 'Currently being cleaned', durationHours: 1 },
  { type: 'busy', label: 'Busy', icon: '🚶', description: 'Long queue / very busy', durationHours: 1 },
  { type: 'no_water', label: 'No Water', icon: '🚱', description: 'No running water available', durationHours: 4 },
  { type: 'refurbishment', label: 'Refurbishment', icon: '🔨', description: 'Under refurbishment', durationHours: 24 },
];

export const ReportFacilityScreen: React.FC = () => {
  const route = useRoute<RouteProp<MapStackParamList, 'ReportFacility'>>();
  const navigation = useNavigation<NavigationProp<any>>();
  const { facilityId } = route.params;

  const [loading, setLoading] = useState(false);
  const [activeReports, setActiveReports] = useState<TemporaryReport[]>([]);
  const [selectedType, setSelectedType] = useState<ReportType | null>(null);
  const [notes, setNotes] = useState('');
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => {
    loadActiveReports();
  }, []);

  const loadActiveReports = async () => {
    setLoading(true);
    const reports = await getActiveReports(facilityId);
    setActiveReports(reports);
    setLoading(false);
  };

  const handleSubmit = async () => {
    if (!selectedType) {
      Alert.alert('Required', 'Please select a report type');
      return;
    }

    setSubmitting(true);
    const reportType = REPORT_TYPES.find((r) => r.type === selectedType);
    const result = await submitTemporaryReport(
      facilityId,
      selectedType,
      notes.trim(),
      reportType?.durationHours || 2,
    );
    setSubmitting(false);

    if (result.success) {
      Alert.alert('Reported', 'Thank you for your report. It will help other users.', [
        { text: 'OK', onPress: () => navigation.goBack() },
      ]);
    } else {
      Alert.alert('Error', result.error || 'Failed to submit report');
    }
  };

  return (
    <ScrollView style={styles.container} contentContainerStyle={styles.content}>
      <Text style={styles.title}>Report Facility Issue</Text>
      <Text style={styles.subtitle}>
        Help others by reporting current issues. Reports expire automatically
        after a set time.
      </Text>

      {/* Active Reports */}
      {activeReports.length > 0 && (
        <Card variant="outlined" style={styles.activeReportsCard}>
          <Text style={styles.activeReportsTitle}>Active Reports</Text>
          {activeReports.map((report) => (
            <View key={report.id} style={styles.activeReportItem}>
              <View style={styles.activeReportInfo}>
                <Text style={styles.activeReportType}>
                  {REPORT_TYPES.find((r) => r.type === report.type)?.icon}{' '}
                  {REPORT_TYPES.find((r) => r.type === report.type)?.label ||
                    report.type}
                </Text>
                <Text style={styles.activeReportTime}>
                  Expires:{' '}
                  {new Date(report.expires_at).toLocaleTimeString([], {
                    hour: '2-digit',
                    minute: '2-digit',
                  })}
                </Text>
              </View>
            </View>
          ))}
        </Card>
      )}

      {/* Report Type Selection */}
      <Text style={styles.sectionTitle}>What's the issue?</Text>
      <View style={styles.typeGrid}>
        {REPORT_TYPES.map((reportType) => {
          const isSelected = selectedType === reportType.type;
          return (
            <TouchableOpacity
              key={reportType.type}
              style={[
                styles.typeCard,
                isSelected && styles.typeCardSelected,
              ]}
              onPress={() => setSelectedType(reportType.type)}
              activeOpacity={0.7}
            >
              <Text style={styles.typeIcon}>{reportType.icon}</Text>
              <Text
                style={[
                  styles.typeLabel,
                  isSelected && styles.typeLabelSelected,
                ]}
              >
                {reportType.label}
              </Text>
              <Text style={styles.typeDescription}>
                {reportType.description}
              </Text>
            </TouchableOpacity>
          );
        })}
      </View>

      {/* Notes */}
      <Text style={styles.label}>Additional Notes (optional)</Text>
      <TextInput
        style={[styles.input, styles.textArea]}
        value={notes}
        onChangeText={setNotes}
        placeholder="e.g. The mens room on ground floor is closed for cleaning"
        placeholderTextColor={colors.textMuted}
        multiline
        numberOfLines={3}
      />

      {/* Submit */}
      <Button
        title="Submit Report"
        onPress={handleSubmit}
        loading={submitting}
        disabled={!selectedType}
        fullWidth
        style={styles.submitButton}
      />
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
  title: {
    ...typography.h2,
    color: colors.textPrimary,
    marginBottom: spacing.xs,
  },
  subtitle: {
    ...typography.body,
    color: colors.textSecondary,
    marginBottom: spacing.xl,
  },
  activeReportsCard: {
    marginBottom: spacing.lg,
    backgroundColor: '#FEF3C7',
    borderColor: colors.warning,
  },
  activeReportsTitle: {
    ...typography.h4,
    color: colors.textPrimary,
    marginBottom: spacing.sm,
  },
  activeReportItem: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingVertical: spacing.xs,
  },
  activeReportInfo: {
    flex: 1,
  },
  activeReportType: {
    ...typography.body,
    color: colors.textPrimary,
  },
  activeReportTime: {
    ...typography.caption,
    color: colors.textSecondary,
    marginTop: 2,
  },
  sectionTitle: {
    ...typography.h3,
    color: colors.textPrimary,
    marginBottom: spacing.md,
  },
  typeGrid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: spacing.sm,
    marginBottom: spacing.lg,
  },
  typeCard: {
    width: '48%',
    backgroundColor: colors.white,
    borderRadius: borderRadius.lg,
    padding: spacing.md,
    borderWidth: 2,
    borderColor: colors.gray200,
    alignItems: 'center',
  },
  typeCardSelected: {
    borderColor: colors.primary,
    backgroundColor: colors.primaryLight,
  },
  typeIcon: {
    fontSize: 28,
    marginBottom: spacing.xs,
  },
  typeLabel: {
    ...typography.bodySmall,
    fontWeight: '600',
    color: colors.textPrimary,
    marginBottom: 2,
  },
  typeLabelSelected: {
    color: colors.primary,
  },
  typeDescription: {
    ...typography.caption,
    color: colors.textSecondary,
    textAlign: 'center',
  },
  label: {
    ...typography.bodySmall,
    fontWeight: '600',
    color: colors.textPrimary,
    marginBottom: spacing.xs,
    marginTop: spacing.md,
  },
  input: {
    backgroundColor: colors.white,
    borderWidth: 1,
    borderColor: colors.gray200,
    borderRadius: borderRadius.md,
    padding: spacing.md,
    ...typography.body,
    color: colors.textPrimary,
  },
  textArea: {
    minHeight: 80,
    textAlignVertical: 'top',
  },
  submitButton: {
    marginTop: spacing.xl,
  },
});
// ============================================================
// Project "Relief" — Correct Information Screen (2.4)
// Permanent edits to facility info → moderation queue
// ============================================================

import React, { useState } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TextInput,
  Alert,
} from 'react-native';
import { colors, typography, spacing, borderRadius } from '../theme';
import { Button } from '../components';
import { submitCorrection } from '../services/community';
import { useRoute, useNavigation, NavigationProp, RouteProp } from '@react-navigation/native';
import type { MapStackParamList } from '../types';

const COMMON_FIELDS = [
  { key: 'name', label: 'Name' },
  { key: 'address', label: 'Address' },
  { key: 'postcode', label: 'Postcode' },
  { key: 'town', label: 'Town/City' },
  { key: 'access_notes', label: 'Access Notes' },
  { key: 'is_free', label: 'Free/Paid' },
  { key: 'is_accessible', label: 'Accessible' },
  { key: 'has_baby_changing', label: 'Baby Changing' },
  { key: 'has_family_room', label: 'Family Room' },
  { key: 'open_hours', label: 'Opening Hours' },
  { key: 'other', label: 'Other' },
];

export const CorrectInfoScreen: React.FC = () => {
  const route = useRoute<RouteProp<MapStackParamList, 'CorrectInfo'>>();
  const navigation = useNavigation<NavigationProp<any>>();
  const { facilityId } = route.params;

  const [selectedField, setSelectedField] = useState<string | null>(null);
  const [oldValue, setOldValue] = useState('');
  const [newValue, setNewValue] = useState('');
  const [notes, setNotes] = useState('');
  const [submitting, setSubmitting] = useState(false);

  const handleSubmit = async () => {
    if (!selectedField) {
      Alert.alert('Required', 'Please select a field to correct');
      return;
    }
    if (!newValue.trim()) {
      Alert.alert('Required', 'Please enter the correct value');
      return;
    }

    setSubmitting(true);
    const result = await submitCorrection(
      facilityId,
      selectedField,
      oldValue.trim(),
      newValue.trim(),
      notes.trim(),
    );
    setSubmitting(false);

    if (result.success) {
      Alert.alert(
        'Submitted',
        'Your correction has been submitted for review. Thank you for helping keep information accurate!',
        [{ text: 'OK', onPress: () => navigation.goBack() }],
      );
    } else {
      Alert.alert('Error', result.error || 'Failed to submit correction');
    }
  };

  return (
    <ScrollView style={styles.container} contentContainerStyle={styles.content}>
      <Text style={styles.title}>Correct Information</Text>
      <Text style={styles.subtitle}>
        Help us keep facility information accurate. Your correction will be
        reviewed before being applied.
      </Text>

      {/* Field Selection */}
      <Text style={styles.sectionTitle}>Which field needs correcting?</Text>
      <View style={styles.fieldGrid}>
        {COMMON_FIELDS.map((field) => {
          const isSelected = selectedField === field.key;
          return (
            <View key={field.key}>
              <Button
                title={field.label}
                onPress={() => setSelectedField(field.key)}
                variant={isSelected ? 'primary' : 'outline'}
                size="sm"
              />
            </View>
          );
        })}
      </View>

      {selectedField && (
        <>
          {/* Current Value */}
          <Text style={styles.label}>Current Value (if known)</Text>
          <TextInput
            style={styles.input}
            value={oldValue}
            onChangeText={setOldValue}
            placeholder="What is currently shown?"
            placeholderTextColor={colors.textMuted}
          />

          {/* Correct Value */}
          <Text style={styles.label}>Correct Value *</Text>
          <TextInput
            style={[styles.input, styles.textArea]}
            value={newValue}
            onChangeText={setNewValue}
            placeholder="What should it say instead?"
            placeholderTextColor={colors.textMuted}
            multiline
            numberOfLines={3}
          />

          {/* Notes */}
          <Text style={styles.label}>Additional Notes (optional)</Text>
          <TextInput
            style={[styles.input, styles.textArea]}
            value={notes}
            onChangeText={setNotes}
            placeholder="How do you know this is correct? Any evidence?"
            placeholderTextColor={colors.textMuted}
            multiline
            numberOfLines={3}
          />

          {/* Submit */}
          <Button
            title="Submit Correction"
            onPress={handleSubmit}
            loading={submitting}
            disabled={!newValue.trim()}
            fullWidth
            style={styles.submitButton}
          />
        </>
      )}
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
  sectionTitle: {
    ...typography.h3,
    color: colors.textPrimary,
    marginBottom: spacing.md,
  },
  fieldGrid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: spacing.sm,
    marginBottom: spacing.lg,
  },
  fieldChip: {
    marginBottom: 0,
  },
  fieldChipSelected: {},
  fieldButton: {
    paddingHorizontal: spacing.md,
    paddingVertical: spacing.xs,
  },
  fieldText: {
    ...typography.bodySmall,
  },
  fieldTextSelected: {
    ...typography.bodySmall,
    color: colors.white,
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
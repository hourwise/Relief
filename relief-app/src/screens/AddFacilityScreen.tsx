// ============================================================
// Project "Relief" — Add Facility Screen (2.1)
// User facility submission form → moderation queue, not live
// ============================================================

import React, { useState } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TextInput,
  Switch,
  Alert,
  ActivityIndicator,
  TouchableOpacity,
} from 'react-native';
import { colors, typography, spacing, borderRadius } from '../theme';
import { Button } from '../components';
import { submitFacility } from '../services/community';
import { NavigationProp, useNavigation } from '@react-navigation/native';

interface AmenityToggle {
  label: string;
  key: string;
  value: boolean;
}

const AMENITIES: AmenityToggle[] = [
  { label: 'Accessible', key: 'is_accessible', value: false },
  { label: 'Disabled Access', key: 'is_disabled_access', value: false },
  { label: 'Baby Changing', key: 'has_baby_changing', value: false },
  { label: 'Family Room', key: 'has_family_room', value: false },
  { label: 'Gender Neutral', key: 'is_gender_neutral', value: false },
  { label: 'Single Occupancy', key: 'is_single_occupancy', value: false },
  { label: 'Open 24 Hours', key: 'is_24h', value: false },
];

export const AddFacilityScreen: React.FC = () => {
  const navigation = useNavigation<NavigationProp<any>>();
  const [loading, setLoading] = useState(false);
  const [step, setStep] = useState(1); // 1: basic info, 2: amenities, 3: review
  const [name, setName] = useState('');
  const [address, setAddress] = useState('');
  const [postcode, setPostcode] = useState('');
  const [town, setTown] = useState('');
  const [accessNotes, setAccessNotes] = useState('');
  const [isFree, setIsFree] = useState(true);
  const [priceNote, setPriceNote] = useState('');
  const [notes, setNotes] = useState('');
  const [accessCodes, setAccessCodes] = useState('');
  const [submissionNotes, setSubmissionNotes] = useState('');
  const [amenities, setAmenities] = useState<Record<string, boolean>>(
    AMENITIES.reduce((acc, a) => ({ ...acc, [a.key]: false }), {}),
  );

  const toggleAmenity = (key: string) => {
    setAmenities((prev) => ({ ...prev, [key]: !prev[key] }));
  };

  const validateStep1 = (): boolean => {
    if (!name.trim()) {
      Alert.alert('Required', 'Please enter a facility name');
      return false;
    }
    if (!address.trim()) {
      Alert.alert('Required', 'Please enter the address');
      return false;
    }
    if (!postcode.trim()) {
      Alert.alert('Required', 'Please enter the postcode');
      return false;
    }
    if (!town.trim()) {
      Alert.alert('Required', 'Please enter the town/city');
      return false;
    }
    return true;
  };

  const handleSubmit = async () => {
    if (!validateStep1()) return;

    setLoading(true);

    // Use approximate coords from town for now (user can refine later)
    // In production, geocode the address
    const result = await submitFacility({
      name: name.trim(),
      address: address.trim(),
      latitude: 0, // Will be geocoded server-side
      longitude: 0,
      postcode: postcode.trim().toUpperCase(),
      town: town.trim(),
      country: 'United Kingdom',
      access_notes: accessNotes.trim(),
      is_free: isFree,
      price_note: isFree ? '' : priceNote.trim(),
      open_hours: null,
      photos: [],
      is_accessible: amenities.is_accessible,
      is_disabled_access: amenities.is_disabled_access,
      has_baby_changing: amenities.has_baby_changing,
      has_family_room: amenities.has_family_room,
      is_gender_neutral: amenities.is_gender_neutral,
      is_single_occupancy: amenities.is_single_occupancy,
      is_24h: amenities.is_24h,
      notes: notes.trim(),
      access_codes: accessCodes.trim(),
      submission_notes: submissionNotes.trim(),
    });

    setLoading(false);

    if (result.success) {
      Alert.alert(
        'Submitted',
        'Your facility has been submitted for review. It will appear on the map once approved.',
        [
          {
            text: 'OK',
            onPress: () => navigation.goBack(),
          },
        ],
      );
    } else {
      Alert.alert('Error', result.error || 'Failed to submit facility');
    }
  };

  return (
    <ScrollView style={styles.container} contentContainerStyle={styles.content}>
      {/* Step Indicator */}
      <View style={styles.stepIndicator}>
        {[1, 2, 3].map((s) => (
          <View key={s} style={styles.stepRow}>
            <View
              style={[
                styles.stepDot,
                step >= s && styles.stepDotActive,
                step > s && styles.stepDotCompleted,
              ]}
            >
              <Text
                style={[
                  styles.stepNumber,
                  step >= s && styles.stepNumberActive,
                ]}
              >
                {step > s ? '✓' : s}
              </Text>
            </View>
            {s < 3 && (
              <View
                style={[
                  styles.stepLine,
                  step > s && styles.stepLineActive,
                ]}
              />
            )}
          </View>
        ))}
      </View>

      <Text style={styles.title}>Add a Facility</Text>
      <Text style={styles.subtitle}>
        Help others by adding a facility. Your submission will be reviewed
        before going live.
      </Text>

      {/* Step 1: Basic Info */}
      {step === 1 && (
        <>
          <Text style={styles.label}>Facility Name *</Text>
          <TextInput
            style={styles.input}
            value={name}
            onChangeText={setName}
            placeholder="e.g. Costa Coffee - Manchester"
            placeholderTextColor={colors.textMuted}
          />

          <Text style={styles.label}>Address *</Text>
          <TextInput
            style={styles.input}
            value={address}
            onChangeText={setAddress}
            placeholder="e.g. 123 High Street"
            placeholderTextColor={colors.textMuted}
          />

          <View style={styles.row}>
            <View style={styles.halfField}>
              <Text style={styles.label}>Postcode *</Text>
              <TextInput
                style={styles.input}
                value={postcode}
                onChangeText={setPostcode}
                placeholder="e.g. M1 1AA"
                placeholderTextColor={colors.textMuted}
                autoCapitalize="characters"
              />
            </View>
            <View style={styles.halfField}>
              <Text style={styles.label}>Town/City *</Text>
              <TextInput
                style={styles.input}
                value={town}
                onChangeText={setTown}
                placeholder="e.g. Manchester"
                placeholderTextColor={colors.textMuted}
              />
            </View>
          </View>

          <Text style={styles.label}>Access Notes</Text>
          <TextInput
            style={[styles.input, styles.textArea]}
            value={accessNotes}
            onChangeText={setAccessNotes}
            placeholder="e.g. Key available at reception, ground floor"
            placeholderTextColor={colors.textMuted}
            multiline
            numberOfLines={3}
          />

          <View style={styles.switchRow}>
            <Text style={styles.switchLabel}>Free to use</Text>
            <Switch
              value={isFree}
              onValueChange={setIsFree}
              trackColor={{ true: colors.primaryLight, false: colors.gray200 }}
              thumbColor={isFree ? colors.primary : colors.gray400}
            />
          </View>

          {!isFree && (
            <>
              <Text style={styles.label}>Price Note</Text>
              <TextInput
                style={styles.input}
                value={priceNote}
                onChangeText={setPriceNote}
                placeholder="e.g. 50p per use"
                placeholderTextColor={colors.textMuted}
              />
            </>
          )}

          <Button
            title="Next: Amenities"
            onPress={() => {
              if (validateStep1()) setStep(2);
            }}
            fullWidth
            style={styles.nextButton}
          />
        </>
      )}

      {/* Step 2: Amenities */}
      {step === 2 && (
        <>
          <Text style={styles.sectionTitle}>Amenities</Text>
          <Text style={styles.sectionSubtitle}>
            Select which amenities this facility offers
          </Text>

          {AMENITIES.map((amenity) => (
            <View key={amenity.key} style={styles.switchRow}>
              <Text style={styles.switchLabel}>{amenity.label}</Text>
              <Switch
                value={amenities[amenity.key]}
                onValueChange={() => toggleAmenity(amenity.key)}
                trackColor={{
                  true: colors.primaryLight,
                  false: colors.gray200,
                }}
                thumbColor={
                  amenities[amenity.key] ? colors.primary : colors.gray400
                }
              />
            </View>
          ))}

          <Text style={[styles.label, { marginTop: spacing.lg }]}>
            Additional Notes
          </Text>
          <TextInput
            style={[styles.input, styles.textArea]}
            value={notes}
            onChangeText={setNotes}
            placeholder="Any other details about this facility"
            placeholderTextColor={colors.textMuted}
            multiline
            numberOfLines={3}
          />

          <Text style={styles.label}>Access Codes (if any)</Text>
          <TextInput
            style={[styles.input, styles.textArea]}
            value={accessCodes}
            onChangeText={setAccessCodes}
            placeholder="e.g. RADAR key required, door code 1234#"
            placeholderTextColor={colors.textMuted}
            multiline
            numberOfLines={2}
          />

          <View style={styles.buttonRow}>
            <Button
              title="Back"
              onPress={() => setStep(1)}
              variant="outline"
              style={styles.halfButton}
            />
            <Button
              title="Review"
              onPress={() => setStep(3)}
              style={styles.halfButton}
            />
          </View>
        </>
      )}

      {/* Step 3: Review */}
      {step === 3 && (
        <>
          <Text style={styles.sectionTitle}>Review & Submit</Text>
          <Text style={styles.sectionSubtitle}>
            Please check the details before submitting
          </Text>

          <View style={styles.reviewCard}>
            <ReviewRow label="Name" value={name} />
            <ReviewRow label="Address" value={address} />
            <ReviewRow label="Postcode" value={postcode} />
            <ReviewRow label="Town" value={town} />
            <ReviewRow label="Free" value={isFree ? 'Yes' : 'No'} />
            {!isFree && <ReviewRow label="Price" value={priceNote} />}
            <ReviewRow label="Access Notes" value={accessNotes} />
            <ReviewRow label="Amenities">
              <Text style={styles.reviewValue}>
                {AMENITIES.filter((a) => amenities[a.key])
                  .map((a) => a.label)
                  .join(', ') || 'None selected'}
              </Text>
            </ReviewRow>
          </View>

          <Text style={styles.label}>Submission Notes (optional)</Text>
          <TextInput
            style={[styles.input, styles.textArea]}
            value={submissionNotes}
            onChangeText={setSubmissionNotes}
            placeholder="Any notes for the reviewer"
            placeholderTextColor={colors.textMuted}
            multiline
            numberOfLines={3}
          />

          <View style={styles.buttonRow}>
            <Button
              title="Back"
              onPress={() => setStep(2)}
              variant="outline"
              style={styles.halfButton}
            />
            <Button
              title="Submit"
              onPress={handleSubmit}
              loading={loading}
              style={styles.halfButton}
            />
          </View>
        </>
      )}
    </ScrollView>
  );
};

const ReviewRow: React.FC<{
  label: string;
  value?: string;
  children?: React.ReactNode;
}> = ({ label, value, children }) => (
  <View style={styles.reviewRow}>
    <Text style={styles.reviewLabel}>{label}</Text>
    {children || (
      <Text style={styles.reviewValue}>{value || 'Not provided'}</Text>
    )}
  </View>
);

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: colors.background,
  },
  content: {
    padding: spacing.lg,
    paddingBottom: spacing['6xl'],
  },
  stepIndicator: {
    flexDirection: 'row',
    justifyContent: 'center',
    alignItems: 'center',
    marginBottom: spacing.xl,
  },
  stepRow: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  stepDot: {
    width: 32,
    height: 32,
    borderRadius: 16,
    backgroundColor: colors.gray100,
    justifyContent: 'center',
    alignItems: 'center',
    borderWidth: 2,
    borderColor: colors.gray200,
  },
  stepDotActive: {
    backgroundColor: colors.primary,
    borderColor: colors.primary,
  },
  stepDotCompleted: {
    backgroundColor: colors.success,
    borderColor: colors.success,
  },
  stepNumber: {
    ...typography.caption,
    fontWeight: '700',
    color: colors.textSecondary,
  },
  stepNumberActive: {
    color: colors.white,
  },
  stepLine: {
    width: 40,
    height: 2,
    backgroundColor: colors.gray200,
    marginHorizontal: spacing.xs,
  },
  stepLineActive: {
    backgroundColor: colors.success,
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
  row: {
    flexDirection: 'row',
    gap: spacing.md,
  },
  halfField: {
    flex: 1,
  },
  switchRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingVertical: spacing.sm,
    borderBottomWidth: 1,
    borderBottomColor: colors.gray100,
  },
  switchLabel: {
    ...typography.body,
    color: colors.textPrimary,
    flex: 1,
  },
  sectionTitle: {
    ...typography.h3,
    color: colors.textPrimary,
    marginBottom: spacing.xs,
  },
  sectionSubtitle: {
    ...typography.bodySmall,
    color: colors.textSecondary,
    marginBottom: spacing.lg,
  },
  nextButton: {
    marginTop: spacing.xl,
  },
  buttonRow: {
    flexDirection: 'row',
    gap: spacing.md,
    marginTop: spacing.xl,
  },
  halfButton: {
    flex: 1,
  },
  reviewCard: {
    backgroundColor: colors.white,
    borderRadius: borderRadius.lg,
    padding: spacing.lg,
    marginBottom: spacing.lg,
    borderWidth: 1,
    borderColor: colors.gray200,
  },
  reviewRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'flex-start',
    paddingVertical: spacing.sm,
    borderBottomWidth: 1,
    borderBottomColor: colors.gray100,
  },
  reviewLabel: {
    ...typography.bodySmall,
    color: colors.textSecondary,
    fontWeight: '600',
    flex: 0.4,
  },
  reviewValue: {
    ...typography.bodySmall,
    color: colors.textPrimary,
    flex: 0.6,
    textAlign: 'right',
  },
});
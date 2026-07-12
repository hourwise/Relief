// ============================================================
// Project "Relief" — AI Recommendations Service (Phase 5)
// Smart facility recommendations, predictive suggestions,
// and preference-based ranking.
// ============================================================

import { supabase } from './supabase';
import {
  fetchNearbyFacilities,
  estimateWalkingTime,
} from './facilities';
import type {
  Facility,
  FacilityFilters,
  ProfilePreferences,
  SavedProfile,
} from '../types';

// ─── Scoring Constants ───────────────────────────────────────

const WEIGHTS = {
  preferenceMatch: 40,    // 40% — how well it matches user preferences
  rating: 25,             // 25% — overall score
  distance: 20,           // 20% — proximity
  openStatus: 10,         // 10% — currently open
  verifiedFreshness: 5,   //  5% — recently verified
};

const PREFERENCE_BOOST = 15;  // Extra score per matching preference
const OPEN_BONUS = 10;        // Bonus if facility is open now
const MAX_RECOMMENDATIONS = 20;

// ─── Types ───────────────────────────────────────────────────

export interface RecommendationScore {
  facility: Facility;
  totalScore: number;
  breakdown: {
    preferenceMatch: number;
    rating: number;
    distance: number;
    openStatus: number;
    verifiedFreshness: number;
  };
  matchingPreferences: string[];
}

export interface PredictiveSuggestion {
  facility: Facility;
  distanceKm: number;
  estimatedWalkingMinutes: number;
  relevanceScore: number;
  reason: string; // e.g. "Quiet and single occupancy facility ahead"
}

// ─── Preference Mapping ──────────────────────────────────────

/**
 * Map ProfilePreferences to facility attribute checks.
 * Returns a list of (attribute, label) pairs that are required.
 */
function getPreferenceChecks(prefs: ProfilePreferences): Array<{
  field: keyof Facility;
  label: string;
}> {
  const checks: Array<{ field: keyof Facility; label: string }> = [];

  if (prefs.requires_accessible) {
    checks.push({ field: 'is_accessible', label: 'Accessible' });
    checks.push({ field: 'has_wheelchair_access', label: 'Wheelchair access' });
  }
  if (prefs.requires_baby_changing) {
    checks.push({ field: 'has_baby_changing', label: 'Baby changing' });
    checks.push({ field: 'has_baby_changing_inside', label: 'Baby changing (inside)' });
  }
  if (prefs.requires_family_room) {
    checks.push({ field: 'has_family_room', label: 'Family room' });
    checks.push({ field: 'has_family_toilet', label: 'Family toilet' });
  }
  if (prefs.requires_gender_neutral) {
    checks.push({ field: 'is_gender_neutral', label: 'Gender neutral' });
  }
  if (prefs.requires_single_occupancy) {
    checks.push({ field: 'is_single_occupancy', label: 'Single occupancy' });
    checks.push({ field: 'is_single_room', label: 'Single room' });
  }
  if (prefs.requires_quiet) {
    checks.push({ field: 'is_quiet', label: 'Quiet' });
  }
  if (prefs.requires_radar_key) {
    checks.push({ field: 'requires_radar_key', label: 'RADAR key' });
  }
  if (prefs.requires_adult_changing) {
    checks.push({ field: 'has_adult_changing_place', label: 'Adult changing place' });
  }

  return checks;
}

/**
 * Get a simple relevance reason for a facility based on its attributes.
 */
function getRelevanceReasons(facility: Facility, prefs: ProfilePreferences): string[] {
  const reasons: string[] = [];
  const checks = getPreferenceChecks(prefs);

  for (const check of checks) {
    const value = facility[check.field];
    if (value === true) {
      reasons.push(check.label);
    }
  }

  return reasons;
}

// ─── Scoring Functions ───────────────────────────────────────

/**
 * Calculate how well a facility matches a user's preferences (0-100).
 */
function scorePreferenceMatch(
  facility: Facility,
  prefs: ProfilePreferences,
): { score: number; matches: string[] } {
  const checks = getPreferenceChecks(prefs);
  if (checks.length === 0) return { score: 50, matches: [] }; // Neutral if no prefs

  let matchCount = 0;
  const matches: string[] = [];

  for (const check of checks) {
    const value = facility[check.field];
    if (value === true) {
      matchCount++;
      matches.push(check.label);
    }
  }

  // Score proportional to how many preferences are satisfied
  const ratio = matchCount / checks.length;
  const score = Math.round(ratio * 100);

  return { score, matches };
}

/**
 * Score a facility's rating quality (0-100).
 * Maps 1-5 star rating to 0-100.
 */
function scoreRating(facility: Facility): number {
  return Math.round((facility.overall_score / 5) * 100);
}

/**
 * Score a facility based on its distance from the user (0-100).
 * Closer = higher score. Distances > 10km get diminishing returns.
 */
function scoreDistance(
  userLat: number,
  userLng: number,
  facility: Facility,
): number {
  const walkingMinutes = estimateWalkingTime(
    userLat, userLng,
    facility.latitude, facility.longitude,
  );

  if (walkingMinutes <= 5) return 100;
  if (walkingMinutes <= 10) return 85;
  if (walkingMinutes <= 20) return 70;
  if (walkingMinutes <= 30) return 55;
  if (walkingMinutes <= 60) return 40;
  if (walkingMinutes <= 120) return 20;
  return 5;
}

/**
 * Score open status (0 or 100).
 */
function scoreOpenStatus(facility: Facility): number {
  if (facility.is_24h) return 100;

  if (!facility.open_hours) return 50; // Unknown = neutral

  const days = ['sunday', 'monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday'];
  const today = days[new Date().getDay()];
  const hours = facility.open_hours[today];
  if (!hours) return 0;

  const now = new Date();
  const [openH, openM] = hours.open.split(':').map(Number);
  const [closeH, closeM] = hours.close.split(':').map(Number);
  const openMinutes = openH * 60 + openM;
  const closeMinutes = closeH * 60 + closeM;
  const nowMinutes = now.getHours() * 60 + now.getMinutes();

  return nowMinutes >= openMinutes && nowMinutes <= closeMinutes ? 100 : 0;
}

/**
 * Score freshness of verification (0-100).
 * Facilities verified within last month get higher scores.
 */
function scoreVerifiedFreshness(facility: Facility): number {
  if (!facility.last_verified_at) return 50; // Unknown = neutral

  const verifiedDate = new Date(facility.last_verified_at);
  const now = new Date();
  const daysSinceVerified = Math.floor(
    (now.getTime() - verifiedDate.getTime()) / (1000 * 60 * 60 * 24),
  );

  if (daysSinceVerified <= 7) return 100;
  if (daysSinceVerified <= 30) return 80;
  if (daysSinceVerified <= 90) return 60;
  if (daysSinceVerified <= 180) return 40;
  if (daysSinceVerified <= 365) return 20;
  return 5;
}

// ─── Public API ──────────────────────────────────────────────

/**
 * 5.1 — Smart Recommendations
 *
 * Score and rank facilities by how well they match the user's needs.
 * Combines preference matching, rating, distance, open status, and freshness.
 */
export async function getSmartRecommendations(
  latitude: number,
  longitude: number,
  preferences: ProfilePreferences,
  options?: {
    radiusKm?: number;
    limit?: number;
    requireOpen?: boolean;
  },
): Promise<RecommendationScore[]> {
  const radiusKm = options?.radiusKm ?? 10;
  const limit = options?.limit ?? MAX_RECOMMENDATIONS;

  // Fetch facilities with basic filters applied
  const filters: Partial<FacilityFilters> = {};
  if (preferences.min_rating > 0) {
    filters.min_rating = preferences.min_rating;
  }
  if (options?.requireOpen) {
    // We can't filter by open-status in the DB query easily,
    // so we handle it in scoring instead.
  }

  const { facilities } = await fetchNearbyFacilities(
    latitude,
    longitude,
    radiusKm,
    filters,
  );

  if (facilities.length === 0) return [];

  // Score each facility
  const scored: RecommendationScore[] = facilities.map((facility) => {
    const { score: prefScore, matches } = scorePreferenceMatch(facility, preferences);
    const ratingScore = scoreRating(facility);
    const distScore = scoreDistance(latitude, longitude, facility);
    const openScore = scoreOpenStatus(facility);
    const freshnessScore = scoreVerifiedFreshness(facility);

    const totalScore =
      (prefScore * WEIGHTS.preferenceMatch) / 100 +
      (ratingScore * WEIGHTS.rating) / 100 +
      (distScore * WEIGHTS.distance) / 100 +
      (openScore * WEIGHTS.openStatus) / 100 +
      (freshnessScore * WEIGHTS.verifiedFreshness) / 100;

    return {
      facility,
      totalScore: Math.round(totalScore * 10) / 10,
      breakdown: {
        preferenceMatch: prefScore,
        rating: ratingScore,
        distance: distScore,
        openStatus: openScore,
        verifiedFreshness: freshnessScore,
      },
      matchingPreferences: matches,
    };
  });

  // Sort by total score descending, return top results
  return scored.sort((a, b) => b.totalScore - a.totalScore).slice(0, limit);
}

/**
 * 5.2 — Predictive Suggestions
 *
 * Find the next suitable facility ahead of the user's direction of travel.
 * Useful for long journeys or when the user is moving.
 */
export async function getPredictiveSuggestions(
  currentLat: number,
  currentLng: number,
  headingDegrees: number, // 0 = north, 90 = east, etc.
  preferences: ProfilePreferences,
  options?: {
    lookAheadRadiusKm?: number;
    minScore?: number;
    maxResults?: number;
  },
): Promise<PredictiveSuggestion[]> {
  const lookAheadRadius = options?.lookAheadRadiusKm ?? 20;
  const minScore = options?.minScore ?? 50;
  const maxResults = options?.maxResults ?? 5;

  // Calculate a point ahead in the direction of travel
  const lookAheadDistance = lookAheadRadius * 0.4; // 40% of look-ahead radius
  const headingRad = (headingDegrees * Math.PI) / 180;
  const latOffset = (lookAheadDistance / 111) * Math.cos(headingRad);
  const lngOffset =
    (lookAheadDistance / (111 * Math.cos((currentLat * Math.PI) / 180))) *
    Math.sin(headingRad);

  const aheadLat = currentLat + latOffset;
  const aheadLng = currentLng + lngOffset;

  // Fetch facilities near the ahead point
  const { facilities } = await fetchNearbyFacilities(
    aheadLat,
    aheadLng,
    lookAheadRadius * 0.6, // Search within 60% of look-ahead radius
    preferences.min_rating > 0 ? { min_rating: preferences.min_rating } : undefined,
  );

  if (facilities.length === 0) return [];

  // Score and rank
  const suggestions: PredictiveSuggestion[] = facilities.map((facility) => {
    const { score: prefScore, matches } = scorePreferenceMatch(facility, preferences);

    // Calculate distance from current position
    const distanceKm = estimateWalkingTime(
      currentLat, currentLng,
      facility.latitude, facility.longitude,
    ) * (5 / 60); // Convert walking minutes to approximate km

    const relevanceScore =
      (prefScore * 0.5) +
      (scoreRating(facility) * 0.25) +
      (scoreOpenStatus(facility) * 0.25);

    // Generate a human-readable reason
    let reason = '';
    if (matches.length > 0) {
      reason = `${matches.slice(0, 2).join(' and ')} facility ahead`;
    } else if (facility.overall_score >= 4) {
      reason = 'Highly rated facility ahead';
    } else {
      reason = 'Facility available ahead';
    }

    return {
      facility,
      distanceKm: Math.round(distanceKm * 10) / 10,
      estimatedWalkingMinutes: estimateWalkingTime(
        currentLat, currentLng,
        facility.latitude, facility.longitude,
      ),
      relevanceScore: Math.round(relevanceScore * 10) / 10,
      reason,
    };
  });

  return suggestions
    .filter((s) => s.relevanceScore >= minScore)
    .sort((a, b) => b.relevanceScore - a.relevanceScore)
    .slice(0, maxResults);
}

/**
 * 5.3 — AI Ranking by User Preferences
 *
 * Re-rank an existing list of facilities based on user preferences.
 * Useful for re-sorting search results or map pins.
 */
export function rankFacilitiesByPreferences(
  facilities: Facility[],
  userLat: number,
  userLng: number,
  preferences: ProfilePreferences,
): RecommendationScore[] {
  const scored: RecommendationScore[] = facilities.map((facility) => {
    const { score: prefScore, matches } = scorePreferenceMatch(facility, preferences);
    const ratingScore = scoreRating(facility);
    const distScore = scoreDistance(userLat, userLng, facility);
    const openScore = scoreOpenStatus(facility);
    const freshnessScore = scoreVerifiedFreshness(facility);

    const totalScore =
      (prefScore * WEIGHTS.preferenceMatch) / 100 +
      (ratingScore * WEIGHTS.rating) / 100 +
      (distScore * WEIGHTS.distance) / 100 +
      (openScore * WEIGHTS.openStatus) / 100 +
      (freshnessScore * WEIGHTS.verifiedFreshness) / 100;

    return {
      facility,
      totalScore: Math.round(totalScore * 10) / 10,
      breakdown: {
        preferenceMatch: prefScore,
        rating: ratingScore,
        distance: distScore,
        openStatus: openScore,
        verifiedFreshness: freshnessScore,
      },
      matchingPreferences: matches,
    };
  });

  return scored.sort((a, b) => b.totalScore - a.totalScore);
}

/**
 * Get recommended facilities matching a saved profile's preferences.
 * Convenience wrapper for 5.1.
 */
export async function getRecommendationsForProfile(
  latitude: number,
  longitude: number,
  profile: SavedProfile,
  options?: {
    radiusKm?: number;
    limit?: number;
  },
): Promise<RecommendationScore[]> {
  return getSmartRecommendations(latitude, longitude, profile.preferences, options);
}
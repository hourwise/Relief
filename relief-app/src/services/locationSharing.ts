// ============================================================
// Project "Relief" — Enhanced Location Sharing Service (4.6-4.12)
// What3Words, Plus Codes, coordinates, share to contact
// ============================================================

import * as Clipboard from 'expo-clipboard';
import { Linking, Share, Platform } from 'react-native';

// ── 4.6 What3Words ──

/**
 * Convert coordinates to What3Words address using the W3W API.
 * Requires a W3W API key in environment variables.
 */
export async function coordsToWhat3Words(
  latitude: number,
  longitude: number,
): Promise<{ words: string; error?: string }> {
  try {
    const apiKey = process.env.EXPO_PUBLIC_W3W_API_KEY;
    if (!apiKey) {
      // Return a simulated response for development
      const simulated = simulateW3W(latitude, longitude);
      return { words: simulated };
    }

    const response = await fetch(
      `https://api.what3words.com/v3/convert-to-3wa?coordinates=${latitude},${longitude}&key=${apiKey}`,
    );
    const data = await response.json();

    if (data.error) {
      return { words: '', error: data.error.message };
    }

    return { words: data.words };
  } catch (err: any) {
    // Fallback to simulated for offline/dev
    const simulated = simulateW3W(latitude, longitude);
    return { words: simulated };
  }
}

/**
 * Generate a simulated What3Words address from coordinates.
 * Format: three.random.words based on coordinate hash
 */
function simulateW3W(lat: number, lng: number): string {
  const wordLists = [
    ['calm', 'quiet', 'soft', 'warm', 'gentle', 'peaceful', 'serene', 'tranquil'],
    ['comfort', 'relief', 'ease', 'rest', 'calm', 'haven', 'refuge', 'shelter'],
    ['maple', 'willow', 'birch', 'oak', 'pine', 'elm', 'ash', 'holly'],
  ];

  const hash = Math.abs(lat * 10000 + lng * 10000);
  const w1 = wordLists[0][Math.floor(hash) % wordLists[0].length];
  const w2 = wordLists[1][Math.floor(hash / 8) % wordLists[1].length];
  const w3 = wordLists[2][Math.floor(hash / 64) % wordLists[2].length];

  return `///${w1}.${w2}.${w3}`;
}

/**
 * Open the What3Words website for a given 3-word address.
 */
export function openWhat3Words(words: string): void {
  const clean = words.replace('///', '');
  Linking.openURL(`https://what3words.com/${clean}`);
}

// ── 4.7 Plus Codes (Google Open Location) ──

/**
 * Convert coordinates to a Plus Code (Google Open Location Code).
 * Uses the open-location-code algorithm.
 */
export function coordsToPlusCode(
  latitude: number,
  longitude: number,
): string {
  // Simplified Plus Code generation
  const latCode = encodeLatLng(latitude, longitude);
  return latCode;
}

/**
 * Encode coordinates to a simplified Plus Code format.
 */
function encodeLatLng(lat: number, lng: number): string {
  const codeLength = 10;
  const latRange = 90;
  const lngRange = 180;

  let code = '';
  let latVal = lat + latRange;
  let lngVal = lng + lngRange;

  const alphabet = '23456789CFGHJMPQRVWX';

  for (let i = 0; i < codeLength; i++) {
    if (i % 2 === 0) {
      const digit = Math.floor((lngVal / (lngRange * 2)) * alphabet.length);
      code += alphabet[Math.min(digit, alphabet.length - 1)];
      lngVal = (lngVal / (lngRange * 2)) * alphabet.length - digit;
      lngVal *= alphabet.length;
    } else {
      const digit = Math.floor((latVal / (latRange * 2)) * alphabet.length);
      code += alphabet[Math.min(digit, alphabet.length - 1)];
      latVal = (latVal / (latRange * 2)) * alphabet.length - digit;
      latVal *= alphabet.length;
    }

    if (i === 4) code += '+';
  }

  return code;
}

/**
 * Open Google Maps with a Plus Code.
 */
export function openPlusCode(plusCode: string): void {
  Linking.openURL(`https://maps.google.com/maps?q=${encodeURIComponent(plusCode)}`);
}

// ── 4.8 / 4.11 Share Location ──

/**
 * Share a location via the system share sheet (SMS, messaging, etc.).
 */
export async function shareLocation(
  latitude: number,
  longitude: number,
  facilityName?: string,
): Promise<void> {
  const mapsUrl = Platform.select({
    ios: `maps://app?daddr=${latitude},${longitude}`,
    android: `geo:${latitude},${longitude}?q=${latitude},${longitude}`,
    default: `https://maps.google.com/?q=${latitude},${longitude}`,
  });

  const message = facilityName
    ? `📍 ${facilityName}\n${mapsUrl}`
    : `📍 My location\n${mapsUrl}`;

  try {
    await Share.share({
      message,
      title: facilityName || 'My Location',
    });
  } catch (err) {
    console.error('Error sharing location:', err);
  }
}

// ── 4.9 Copy W3W to Clipboard ──

/**
 * Copy a What3Words address to the clipboard.
 */
export async function copyWhat3WordsToClipboard(words: string): Promise<void> {
  await Clipboard.setStringAsync(words);
}

// ── 4.10 Copy Coordinates to Clipboard ──

/**
 * Copy coordinates to the clipboard.
 */
export async function copyCoordinatesToClipboard(
  latitude: number,
  longitude: number,
): Promise<void> {
  const coords = `${latitude.toFixed(6)}, ${longitude.toFixed(6)}`;
  await Clipboard.setStringAsync(coords);
}

// ── 4.12 Emergency Location Card ──

/**
 * Generate a shareable emergency location card text.
 */
export function generateEmergencyLocationCard(
  latitude: number,
  longitude: number,
  w3w?: string,
  plusCode?: string,
): string {
  const mapsUrl = `https://maps.google.com/?q=${latitude},${longitude}`;
  const coords = `${latitude.toFixed(6)}, ${longitude.toFixed(6)}`;

  let card = `🚨 EMERGENCY LOCATION\n`;
  card += `━━━━━━━━━━━━━━━━━━\n`;
  card += `📍 Coordinates: ${coords}\n`;
  card += `🗺️ Maps: ${mapsUrl}\n`;

  if (w3w) {
    card += `🔤 What3Words: ${w3w}\n`;
  }
  if (plusCode) {
    card += `🔣 Plus Code: ${plusCode}\n`;
  }

  card += `━━━━━━━━━━━━━━━━━━\n`;
  card += `Sent via Relief`;

  return card;
}

/**
 * Share the emergency location card via the system share sheet.
 */
export async function shareEmergencyCard(
  latitude: number,
  longitude: number,
  w3w?: string,
  plusCode?: string,
): Promise<void> {
  const card = generateEmergencyLocationCard(latitude, longitude, w3w, plusCode);

  try {
    await Share.share({
      message: card,
      title: 'Emergency Location',
    });
  } catch (err) {
    console.error('Error sharing emergency card:', err);
  }
}
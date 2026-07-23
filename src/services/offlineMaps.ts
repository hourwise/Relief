// ============================================================
// Project "Relief" — Offline Maps Service (4.4)
// Download facility regions for offline use
// Stores data in local SQLite via expo-sqlite
// ============================================================

import * as FileSystem from 'expo-file-system';
import * as SQLite from 'expo-sqlite';
import { supabase } from './supabase';
import type { Facility } from '../types';

export interface DownloadedRegion {
  id: string;
  name: string;
  town: string;
  facilityCount: number;
  downloadedAt: string;
  sizeBytes: number;
  latitude: number;
  longitude: number;
}

const DB_NAME = 'relief_offline.db';

async function getDb(): Promise<SQLite.SQLiteDatabase> {
  return await SQLite.openDatabaseAsync(DB_NAME);
}

/**
 * Initialize the offline database schema.
 */
export async function initOfflineDb(): Promise<void> {
  const db = await getDb();
  await db.execAsync(`
    CREATE TABLE IF NOT EXISTS offline_regions (
      id TEXT PRIMARY KEY,
      name TEXT NOT NULL,
      town TEXT NOT NULL,
      facility_count INTEGER DEFAULT 0,
      downloaded_at TEXT NOT NULL,
      size_bytes INTEGER DEFAULT 0,
      latitude REAL NOT NULL,
      longitude REAL NOT NULL
    );
    CREATE TABLE IF NOT EXISTS offline_facilities (
      id TEXT PRIMARY KEY,
      region_id TEXT NOT NULL,
      data TEXT NOT NULL,
      FOREIGN KEY (region_id) REFERENCES offline_regions(id)
    );
    CREATE INDEX IF NOT EXISTS idx_offline_facilities_region 
      ON offline_facilities(region_id);
  `);
}

/**
 * Download a region (town/city) for offline use.
 */
export async function downloadRegion(
  town: string,
  onProgress?: (current: number, total: number) => void,
): Promise<{ success: boolean; error?: string; region?: DownloadedRegion }> {
  try {
    await initOfflineDb();

    // Fetch facilities for this town
    const { data, error, count } = await supabase
      .from('facilities')
      .select('*', { count: 'exact' })
      .eq('town', town)
      .eq('is_verified', true);

    if (error) throw error;
    if (!data || data.length === 0) {
      return { success: false, error: `No facilities found in "${town}"` };
    }

    const facilities = data as unknown as Facility[];
    const db = await getDb();
    const regionId = `region_${town.toLowerCase().replace(/\s+/g, '_')}_${Date.now()}`;
    const now = new Date().toISOString();

    // Estimate size based on JSON data
    const dataStr = JSON.stringify(facilities);
    const sizeBytes = dataStr.length * 2; // Approx UTF-16 size

    // Store region metadata
    await db.runAsync(
      `INSERT INTO offline_regions (id, name, town, facility_count, downloaded_at, size_bytes, latitude, longitude) 
       VALUES (?, ?, ?, ?, ?, ?, ?, ?)`,
      [
        regionId,
        `${town} Area`,
        town,
        facilities.length,
        now,
        sizeBytes,
        facilities[0].latitude,
        facilities[0].longitude,
      ],
    );

    // Store each facility
    for (let i = 0; i < facilities.length; i++) {
      const facility = facilities[i];
      await db.runAsync(
        `INSERT OR REPLACE INTO offline_facilities (id, region_id, data) VALUES (?, ?, ?)`,
        [facility.id, regionId, JSON.stringify(facility)],
      );
      onProgress?.(i + 1, facilities.length);
    }

    const region: DownloadedRegion = {
      id: regionId,
      name: `${town} Area`,
      town,
      facilityCount: facilities.length,
      downloadedAt: now,
      sizeBytes,
      latitude: facilities[0].latitude,
      longitude: facilities[0].longitude,
    };

    return { success: true, region };
  } catch (err: any) {
    console.error('Error downloading region:', err);
    return { success: false, error: err.message || 'Failed to download region' };
  }
}

/**
 * Get all downloaded regions.
 */
export async function getDownloadedRegions(): Promise<DownloadedRegion[]> {
  try {
    await initOfflineDb();
    const db = await getDb();
    const rows = await db.getAllAsync(
      `SELECT * FROM offline_regions ORDER BY downloaded_at DESC`,
    );
    return rows.map((row: any) => ({
      id: row.id,
      name: row.name,
      town: row.town,
      facilityCount: row.facility_count,
      downloadedAt: row.downloaded_at,
      sizeBytes: row.size_bytes,
      latitude: row.latitude,
      longitude: row.longitude,
    }));
  } catch (err) {
    console.error('Error getting downloaded regions:', err);
    return [];
  }
}

/**
 * Get offline facilities for a region.
 */
export async function getOfflineFacilities(
  regionId: string,
): Promise<Facility[]> {
  try {
    const db = await getDb();
    const rows = await db.getAllAsync(
      `SELECT data FROM offline_facilities WHERE region_id = ?`,
      [regionId],
    );
    return rows.map((row: any) => JSON.parse(row.data));
  } catch (err) {
    console.error('Error getting offline facilities:', err);
    return [];
  }
}

/**
 * Search offline facilities by town or postcode.
 */
export async function searchOfflineFacilities(
  query: string,
): Promise<Facility[]> {
  try {
    const db = await getDb();
    const searchTerm = `%${query.toLowerCase()}%`;
    const rows = await db.getAllAsync(
      `SELECT data FROM offline_facilities`,
    );
    
    const results: Facility[] = [];
    for (const row of rows as any[]) {
      const facility: Facility = JSON.parse(row.data);
      if (
        facility.town.toLowerCase().includes(query.toLowerCase()) ||
        facility.postcode.toLowerCase().includes(query.toLowerCase()) ||
        facility.name.toLowerCase().includes(query.toLowerCase())
      ) {
        results.push(facility);
      }
      if (results.length >= 20) break;
    }
    
    return results;
  } catch (err) {
    console.error('Error searching offline facilities:', err);
    return [];
  }
}

/**
 * Delete a downloaded region.
 */
export async function deleteRegion(
  regionId: string,
): Promise<{ success: boolean; error?: string }> {
  try {
    const db = await getDb();
    await db.runAsync(`DELETE FROM offline_facilities WHERE region_id = ?`, [regionId]);
    await db.runAsync(`DELETE FROM offline_regions WHERE id = ?`, [regionId]);
    return { success: true };
  } catch (err: any) {
    console.error('Error deleting region:', err);
    return { success: false, error: err.message };
  }
}

/**
 * Get total storage used by offline maps.
 */
export async function getOfflineStorageSize(): Promise<number> {
  try {
    const regions = await getDownloadedRegions();
    return regions.reduce((total, r) => total + r.sizeBytes, 0);
  } catch {
    return 0;
  }
}

/**
 * Check if a region is already downloaded.
 */
export async function isRegionDownloaded(
  town: string,
): Promise<boolean> {
  try {
    const db = await getDb();
    const row = await db.getFirstAsync(
      `SELECT id FROM offline_regions WHERE town = ?`,
      [town],
    );
    return !!row;
  } catch {
    return false;
  }
}

/**
 * Format bytes to human-readable string.
 */
export function formatBytes(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}
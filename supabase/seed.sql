-- ============================================================
-- Project "Relief" — Seed Data
-- ============================================================

-- Seed Verified Facilities (London Area)
INSERT INTO facilities (
  name, address, latitude, longitude, postcode, town, country,
  is_free, is_accessible, has_baby_changing, is_verified, overall_score,
  is_picnic_area, is_gender_neutral, is_24h
) VALUES
(
  'Trafalgar Square Public Toilets',
  'Trafalgar Square, London',
  51.5081, -0.1281,
  'WC2N 5DN', 'London', 'GB',
  false, true, true, true, 4.5,
  false, false, false
),
(
  'St. James''s Park Facilities',
  'The Mall, London',
  51.5025, -0.1348,
  'SW1A 2BJ', 'London', 'GB',
  true, true, true, true, 4.8,
  true, true, false
),
(
  'Victoria Station Toilets',
  'Victoria Station, London',
  51.4952, -0.1439,
  'SW1V 1JU', 'London', 'GB',
  false, true, true, true, 3.9,
  false, false, true
),
(
  'British Museum Restrooms',
  'Great Russell St, London',
  51.5194, -0.1270,
  'WC1B 3DG', 'London', 'GB',
  true, true, true, true, 4.9,
  false, true, false
),
(
  'Southbank Centre Toilets',
  'Belvedere Rd, London',
  51.5058, -0.1164,
  'SE1 8XX', 'London', 'GB',
  true, true, true, true, 4.2,
  false, true, false
);

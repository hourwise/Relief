-- ============================================================
-- Project "Relief" — Field Provenance Tracking
-- Adds a JSONB column to track which source supplied each field.
-- ============================================================

ALTER TABLE facilities
  ADD COLUMN IF NOT EXISTS field_provenance JSONB DEFAULT '{}'::jsonb;

-- GIN index for provenance queries
CREATE INDEX IF NOT EXISTS idx_facilities_field_provenance
  ON facilities USING GIN (field_provenance);

COMMENT ON COLUMN facilities.field_provenance IS
  'Tracks which external source supplied each field value. '
  'Example: {"is_accessible": {"source": "Toilet Map UK", "field": "accessible", "at": "2026-07-25T12:00:00Z"}} '
  'Future sources check this before overwriting — community-verified data takes precedence over imports.';

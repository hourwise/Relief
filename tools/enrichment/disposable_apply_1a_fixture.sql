-- Disposable-only minimum Relief fixture for Apply 1A integration testing.
-- This file is intentionally not a production migration and contains no
-- credentials or live connection details.

BEGIN;

CREATE EXTENSION IF NOT EXISTS pgcrypto;

DO $$
BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'anon') THEN
    CREATE ROLE anon NOLOGIN NOSUPERUSER NOCREATEDB NOCREATEROLE NOINHERIT;
  END IF;
  IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'authenticated') THEN
    CREATE ROLE authenticated NOLOGIN NOSUPERUSER NOCREATEDB NOCREATEROLE NOINHERIT;
  END IF;
  IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'relief_apply_owner') THEN
    CREATE ROLE relief_apply_owner NOLOGIN NOSUPERUSER NOCREATEDB NOCREATEROLE NOINHERIT;
  ELSE
    ALTER ROLE relief_apply_owner NOLOGIN NOSUPERUSER NOCREATEDB NOCREATEROLE NOINHERIT;
  END IF;
  IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'relief_apply_operator') THEN
    CREATE ROLE relief_apply_operator NOLOGIN NOSUPERUSER NOCREATEDB NOCREATEROLE NOINHERIT;
  ELSE
    ALTER ROLE relief_apply_operator NOLOGIN NOSUPERUSER NOCREATEDB NOCREATEROLE NOINHERIT;
  END IF;
END;
$$;

CREATE TABLE IF NOT EXISTS public.import_runs (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  source_name text NOT NULL,
  source_file_name text,
  source_checksum text,
  status text NOT NULL DEFAULT 'started',
  started_at timestamptz NOT NULL DEFAULT now(),
  completed_at timestamptz,
  rows_received integer NOT NULL DEFAULT 0,
  rows_valid integer NOT NULL DEFAULT 0,
  rows_inserted integer NOT NULL DEFAULT 0,
  rows_updated integer NOT NULL DEFAULT 0,
  rows_unchanged integer NOT NULL DEFAULT 0,
  rows_quarantined integer NOT NULL DEFAULT 0,
  rows_marked_stale integer NOT NULL DEFAULT 0,
  error_summary text,
  CONSTRAINT disposable_import_runs_status_check
    CHECK (status IN ('started', 'completed', 'failed'))
);

CREATE TABLE IF NOT EXISTS public.facilities (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  name text NOT NULL,
  address text,
  latitude double precision NOT NULL,
  longitude double precision NOT NULL,
  postcode text,
  town text NOT NULL,
  country text NOT NULL DEFAULT 'GB',
  open_hours jsonb,
  is_free boolean,
  is_accessible boolean,
  has_baby_changing boolean,
  is_gender_neutral boolean,
  requires_radar_key boolean,
  updated_at timestamptz NOT NULL DEFAULT now(),
  created_at timestamptz NOT NULL DEFAULT now(),
  publication_status text NOT NULL DEFAULT 'hidden',
  verification_status text NOT NULL DEFAULT 'source_imported',
  field_provenance jsonb NOT NULL DEFAULT '{}'::jsonb,
  CONSTRAINT disposable_facilities_publication_status_check
    CHECK (publication_status IN ('published', 'hidden', 'under_review', 'removed')),
  CONSTRAINT disposable_facilities_verification_status_check
    CHECK (verification_status IN ('source_imported', 'source_verified', 'community_confirmed', 'staff_verified', 'disputed', 'stale'))
);

CREATE OR REPLACE FUNCTION public.update_updated_at()
RETURNS trigger
LANGUAGE plpgsql
AS $$
BEGIN
  NEW.updated_at := clock_timestamp();
  RETURN NEW;
END;
$$;

DROP TRIGGER IF EXISTS facilities_updated_at ON public.facilities;
CREATE TRIGGER facilities_updated_at
BEFORE UPDATE ON public.facilities
FOR EACH ROW
EXECUTE FUNCTION public.update_updated_at();

CREATE TABLE IF NOT EXISTS public.facility_sources (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  facility_id uuid NOT NULL REFERENCES public.facilities(id),
  import_run_id uuid REFERENCES public.import_runs(id),
  source_name text NOT NULL,
  source_record_id text NOT NULL,
  source_url text,
  source_licence text NOT NULL,
  source_updated_at timestamptz,
  first_seen_at timestamptz NOT NULL DEFAULT now(),
  last_seen_at timestamptz NOT NULL DEFAULT now(),
  is_current boolean NOT NULL DEFAULT true,
  raw_data jsonb,
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now(),
  CONSTRAINT disposable_facility_sources_identity_key
    UNIQUE (source_name, source_record_id)
);

INSERT INTO public.import_runs (
  id, source_name, source_file_name, source_checksum, status,
  started_at, completed_at, rows_received, rows_valid, rows_inserted
)
VALUES (
  '00000000-0000-0000-0000-000000000001'::uuid,
  'Toilet Map UK',
  'toilet-map-fixture.json',
  'f6824fdc7cd29df8c1f45ba749c1b28d319fb34803c55459bbe748ef65937624',
  'completed',
  '2026-08-11T00:00:00Z'::timestamptz,
  '2026-08-11T00:01:00Z'::timestamptz,
  48,
  48,
  48
)
ON CONFLICT (id) DO NOTHING;

COMMIT;

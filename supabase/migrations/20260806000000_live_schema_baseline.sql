-- ============================================================
-- Relief — LIVE SCHEMA BASELINE
-- ============================================================
-- Generated with pg_dump 17.10 --schema-only --schema=public
-- against the LIVE Supabase project on 2026-08-06.
-- Server: PostgreSQL 17.6.
--
-- This file is the authoritative record of the live database
-- structure. It was exported from the running database, NOT
-- reconstructed from documentation.
--
-- It intentionally captures the live state AS IT WAS, including
-- the then-broken find_nearest_facilities() function, which
-- selected six columns that do not exist on facilities:
--   is_water_refill_station, is_shower_facility,
--   is_breastfeeding_room, is_rest_area, is_changing_place,
--   is_ev_charging
-- That defect is corrected by the next migration
-- (20260806000100_repair_find_nearest_facilities.sql) so the
-- migration history stays truthful rather than retroactively
-- rewritten.
--
-- Not emitted by --schema=public, and therefore restated here:
--   * the postgis extension (installed into schema public)
--   * cluster-scoped event triggers (rls_auto_enable is dumped
--     as a function, but its EVENT TRIGGER is not schema-scoped)
--   * Supabase-managed schemas (auth, storage, vault, extensions)
-- ============================================================

CREATE EXTENSION IF NOT EXISTS postgis WITH SCHEMA public;

--
-- PostgreSQL database dump
--


-- Dumped from database version 17.6
-- Dumped by pg_dump version 17.10

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET transaction_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;

--
-- Name: public; Type: SCHEMA; Schema: -; Owner: -
--

CREATE SCHEMA IF NOT EXISTS public;


--
-- Name: expire_temporary_reports(); Type: FUNCTION; Schema: public; Owner: -
--

CREATE FUNCTION public.expire_temporary_reports() RETURNS void
    LANGUAGE plpgsql SECURITY DEFINER
    AS $$
BEGIN
  UPDATE temporary_reports
  SET is_expired = true
  WHERE is_expired = false
    AND expires_at < now();
END;
$$;


--
-- Name: find_nearest_facilities(double precision, double precision, integer, integer); Type: FUNCTION; Schema: public; Owner: -
--

CREATE FUNCTION public.find_nearest_facilities(user_latitude double precision, user_longitude double precision, search_radius_metres integer DEFAULT 5000, result_limit integer DEFAULT 1) RETURNS TABLE(facility_id uuid, name text, address text, latitude double precision, longitude double precision, postcode text, town text, country text, photos text[], open_hours jsonb, is_free boolean, price_note text, access_notes text, last_verified_at timestamp with time zone, is_accessible boolean, is_disabled_access boolean, has_baby_changing boolean, has_family_room boolean, is_gender_neutral boolean, is_single_occupancy boolean, is_24h boolean, is_single_room boolean, has_floor_to_ceiling_cubicles boolean, is_quiet boolean, has_wheelchair_access boolean, requires_radar_key boolean, has_adult_changing_place boolean, has_lift boolean, has_grab_rails boolean, has_baby_changing_inside boolean, has_separate_changing_room boolean, has_family_toilet boolean, has_pram_access boolean, has_soap boolean, has_paper_towels boolean, has_hand_dryer boolean, has_mirror boolean, has_shelf boolean, has_hooks boolean, has_sanitary_bins boolean, has_free_period_products boolean, has_drinking_water boolean, noise_level integer, temperature integer, lighting integer, smell integer, has_staff_nearby boolean, has_cctv boolean, is_women_friendly boolean, is_family_friendly boolean, is_water_refill_station boolean, is_shower_facility boolean, is_breastfeeding_room boolean, is_rest_area boolean, is_changing_place boolean, is_ev_charging boolean, is_picnic_area boolean, overall_score double precision, cleanliness_rating double precision, privacy_rating double precision, accessibility_rating double precision, safety_rating double precision, noise_rating double precision, environment_rating double precision, publication_status text, verification_status text, last_community_confirmed_at timestamp with time zone, last_staff_verified_at timestamp with time zone, created_at timestamp with time zone, updated_at timestamp with time zone, created_by uuid, is_verified boolean, field_provenance jsonb, distance_metres double precision)
    LANGUAGE plpgsql STABLE
    SET search_path TO 'public'
    AS $$
BEGIN
  -- ── Input validation ──────────────────────────────────────
  IF user_latitude IS NULL OR user_latitude < -90 OR user_latitude > 90 THEN
    RAISE EXCEPTION 'Invalid latitude: %. Must be between -90 and 90.', user_latitude;
  END IF;

  IF user_longitude IS NULL OR user_longitude < -180 OR user_longitude > 180 THEN
    RAISE EXCEPTION 'Invalid longitude: %. Must be between -180 and 180.', user_longitude;
  END IF;

  IF search_radius_metres IS NULL OR search_radius_metres <= 0 THEN
    RAISE EXCEPTION 'Invalid search_radius_metres: %. Must be positive.', search_radius_metres;
  END IF;

  IF result_limit IS NULL OR result_limit <= 0 THEN
    RAISE EXCEPTION 'Invalid result_limit: %. Must be positive.', result_limit;
  END IF;

  -- ── Query ─────────────────────────────────────────────────
  RETURN QUERY
  SELECT
    f.id,
    f.name,
    f.address,
    f.latitude,
    f.longitude,
    f.postcode,
    f.town,
    f.country,
    f.photos,
    f.open_hours,
    f.is_free,
    f.price_note,
    f.access_notes,
    f.last_verified_at,
    f.is_accessible,
    f.is_disabled_access,
    f.has_baby_changing,
    f.has_family_room,
    f.is_gender_neutral,
    f.is_single_occupancy,
    f.is_24h,
    f.is_single_room,
    f.has_floor_to_ceiling_cubicles,
    f.is_quiet,
    f.has_wheelchair_access,
    f.requires_radar_key,
    f.has_adult_changing_place,
    f.has_lift,
    f.has_grab_rails,
    f.has_baby_changing_inside,
    f.has_separate_changing_room,
    f.has_family_toilet,
    f.has_pram_access,
    f.has_soap,
    f.has_paper_towels,
    f.has_hand_dryer,
    f.has_mirror,
    f.has_shelf,
    f.has_hooks,
    f.has_sanitary_bins,
    f.has_free_period_products,
    f.has_drinking_water,
    f.noise_level,
    f.temperature,
    f.lighting,
    f.smell,
    f.has_staff_nearby,
    f.has_cctv,
    f.is_women_friendly,
    f.is_family_friendly,
    f.is_water_refill_station,
    f.is_shower_facility,
    f.is_breastfeeding_room,
    f.is_rest_area,
    f.is_changing_place,
    f.is_ev_charging,
    f.is_picnic_area,
    f.overall_score,
    f.cleanliness_rating,
    f.privacy_rating,
    f.accessibility_rating,
    f.safety_rating,
    f.noise_rating,
    f.environment_rating,
    f.publication_status,
    f.verification_status,
    f.last_community_confirmed_at,
    f.last_staff_verified_at,
    f.created_at,
    f.updated_at,
    f.created_by,
    f.is_verified,
    f.field_provenance,
    ST_Distance(
      f.location,
      ST_SetSRID(ST_MakePoint(user_longitude, user_latitude), 4326)::geography
    ) AS distance_metres
  FROM facilities f
  WHERE f.publication_status = 'published'
    AND ST_DWithin(
          f.location,
          ST_SetSRID(ST_MakePoint(user_longitude, user_latitude), 4326)::geography,
          search_radius_metres
        )
  ORDER BY
    distance_metres ASC,
    f.name ASC           -- stable tiebreaker
  LIMIT result_limit;
END;
$$;


--
-- Name: handle_new_user(); Type: FUNCTION; Schema: public; Owner: -
--

CREATE FUNCTION public.handle_new_user() RETURNS trigger
    LANGUAGE plpgsql SECURITY DEFINER
    AS $$
BEGIN
  INSERT INTO public.user_profiles (id, email, display_name)
  VALUES (
    NEW.id,
    NEW.email,
    COALESCE(NEW.raw_user_meta_data->>'full_name', NEW.email)
  );
  RETURN NEW;
END;
$$;


--
-- Name: rls_auto_enable(); Type: FUNCTION; Schema: public; Owner: -
--

CREATE FUNCTION public.rls_auto_enable() RETURNS event_trigger
    LANGUAGE plpgsql SECURITY DEFINER
    SET search_path TO 'pg_catalog'
    AS $$
DECLARE
  cmd record;
BEGIN
  FOR cmd IN
    SELECT *
    FROM pg_event_trigger_ddl_commands()
    WHERE command_tag IN ('CREATE TABLE', 'CREATE TABLE AS', 'SELECT INTO')
      AND object_type IN ('table','partitioned table')
  LOOP
     IF cmd.schema_name IS NOT NULL AND cmd.schema_name IN ('public') AND cmd.schema_name NOT IN ('pg_catalog','information_schema') AND cmd.schema_name NOT LIKE 'pg_toast%' AND cmd.schema_name NOT LIKE 'pg_temp%' THEN
      BEGIN
        EXECUTE format('alter table if exists %s enable row level security', cmd.object_identity);
        RAISE LOG 'rls_auto_enable: enabled RLS on %', cmd.object_identity;
      EXCEPTION
        WHEN OTHERS THEN
          RAISE LOG 'rls_auto_enable: failed to enable RLS on %', cmd.object_identity;
      END;
     ELSE
        RAISE LOG 'rls_auto_enable: skip % (either system schema or not in enforced list: %.)', cmd.object_identity, cmd.schema_name;
     END IF;
  END LOOP;
END;
$$;


--
-- Name: sync_subscription_from_revenuecat(uuid, text, boolean, timestamp with time zone, timestamp with time zone, timestamp with time zone, boolean, boolean, timestamp with time zone, timestamp with time zone, timestamp with time zone, jsonb, text, text); Type: FUNCTION; Schema: public; Owner: -
--

CREATE FUNCTION public.sync_subscription_from_revenuecat(p_user_id uuid, p_tier text, p_is_active boolean, p_lifetime_purchase_at timestamp with time zone, p_current_period_start timestamp with time zone, p_current_period_end timestamp with time zone, p_will_renew boolean, p_is_grace_period boolean, p_cancellation_at timestamp with time zone, p_cancelled_at timestamp with time zone, p_refunded_at timestamp with time zone, p_raw_json jsonb, p_event_type text, p_previous_tier text DEFAULT NULL::text) RETURNS void
    LANGUAGE plpgsql SECURITY DEFINER
    AS $$
BEGIN
  -- Upsert the subscription record
  INSERT INTO user_subscriptions (
    user_id,
    tier,
    is_active,
    lifetime_purchase_at,
    current_period_start,
    current_period_end,
    will_renew,
    is_grace_period,
    cancellation_at,
    cancelled_at,
    refunded_at,
    raw_revenuecat_json,
    updated_at
  ) VALUES (
    p_user_id,
    p_tier,
    p_is_active,
    p_lifetime_purchase_at,
    p_current_period_start,
    p_current_period_end,
    p_will_renew,
    p_is_grace_period,
    p_cancellation_at,
    p_cancelled_at,
    p_refunded_at,
    p_raw_json,
    now()
  )
  ON CONFLICT (user_id) DO UPDATE SET
    tier = EXCLUDED.tier,
    is_active = EXCLUDED.is_active,
    lifetime_purchase_at = EXCLUDED.lifetime_purchase_at,
    current_period_start = EXCLUDED.current_period_start,
    current_period_end = EXCLUDED.current_period_end,
    will_renew = EXCLUDED.will_renew,
    is_grace_period = EXCLUDED.is_grace_period,
    cancellation_at = EXCLUDED.cancellation_at,
    cancelled_at = EXCLUDED.cancelled_at,
    refunded_at = EXCLUDED.refunded_at,
    raw_revenuecat_json = EXCLUDED.raw_revenuecat_json,
    updated_at = now();

  -- Log the event
  INSERT INTO subscription_events (
    user_id,
    event_type,
    tier,
    previous_tier,
    details,
    revenuecat_event_id
  ) VALUES (
    p_user_id,
    p_event_type,
    p_tier,
    p_previous_tier,
    p_raw_json,
    p_raw_json->>'event_id'
  );
END;
$$;


--
-- Name: update_updated_at(); Type: FUNCTION; Schema: public; Owner: -
--

CREATE FUNCTION public.update_updated_at() RETURNS trigger
    LANGUAGE plpgsql
    AS $$
BEGIN
  NEW.updated_at = NOW();
  RETURN NEW;
END;
$$;


SET default_tablespace = '';

SET default_table_access_method = heap;

--
-- Name: access_codes; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.access_codes (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    facility_id uuid NOT NULL,
    user_id uuid NOT NULL,
    code text NOT NULL,
    description text DEFAULT ''::text,
    is_verified boolean DEFAULT false,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL
);


--
-- Name: correction_requests; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.correction_requests (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    facility_id uuid NOT NULL,
    user_id uuid NOT NULL,
    field text NOT NULL,
    old_value text DEFAULT ''::text NOT NULL,
    new_value text NOT NULL,
    notes text DEFAULT ''::text,
    status text DEFAULT 'pending'::text NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    reviewed_at timestamp with time zone,
    reviewed_by uuid,
    CONSTRAINT correction_requests_status_check CHECK ((status = ANY (ARRAY['pending'::text, 'approved'::text, 'rejected'::text])))
);


--
-- Name: facilities; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.facilities (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    name text NOT NULL,
    address text,
    latitude double precision NOT NULL,
    longitude double precision NOT NULL,
    postcode text,
    town text NOT NULL,
    country text DEFAULT 'GB'::text NOT NULL,
    photos text[] DEFAULT '{}'::text[],
    open_hours jsonb,
    is_free boolean,
    price_note text,
    access_notes text DEFAULT ''::text,
    last_verified_at timestamp with time zone,
    is_accessible boolean,
    is_disabled_access boolean,
    has_baby_changing boolean,
    has_family_room boolean,
    is_gender_neutral boolean,
    is_single_occupancy boolean,
    is_24h boolean,
    is_single_room boolean,
    has_floor_to_ceiling_cubicles boolean,
    is_quiet boolean,
    has_wheelchair_access boolean,
    requires_radar_key boolean,
    has_adult_changing_place boolean,
    has_lift boolean,
    has_grab_rails boolean,
    has_baby_changing_inside boolean,
    has_separate_changing_room boolean,
    has_family_toilet boolean,
    has_pram_access boolean,
    has_soap boolean,
    has_paper_towels boolean,
    has_hand_dryer boolean,
    has_mirror boolean,
    has_shelf boolean,
    has_hooks boolean,
    has_sanitary_bins boolean,
    has_free_period_products boolean,
    has_drinking_water boolean,
    noise_level integer,
    temperature integer,
    lighting integer,
    smell integer,
    has_staff_nearby boolean,
    has_cctv boolean,
    is_women_friendly boolean,
    is_family_friendly boolean,
    is_picnic_area boolean,
    overall_score double precision DEFAULT 0,
    cleanliness_rating double precision DEFAULT 0,
    privacy_rating double precision DEFAULT 0,
    accessibility_rating double precision DEFAULT 0,
    safety_rating double precision DEFAULT 0,
    noise_rating double precision DEFAULT 0,
    environment_rating double precision DEFAULT 0,
    created_at timestamp with time zone DEFAULT now(),
    updated_at timestamp with time zone DEFAULT now(),
    created_by uuid,
    is_verified boolean DEFAULT false,
    publication_status text DEFAULT 'hidden'::text NOT NULL,
    verification_status text DEFAULT 'source_imported'::text NOT NULL,
    last_community_confirmed_at timestamp with time zone,
    last_staff_verified_at timestamp with time zone,
    location public.geography(Point,4326) GENERATED ALWAYS AS ((public.st_setsrid(public.st_makepoint(longitude, latitude), 4326))::public.geography) STORED,
    field_provenance jsonb DEFAULT '{}'::jsonb,
    CONSTRAINT facilities_lighting_check CHECK (((lighting >= 1) AND (lighting <= 5))),
    CONSTRAINT facilities_noise_level_check CHECK (((noise_level >= 1) AND (noise_level <= 5))),
    CONSTRAINT facilities_publication_status_check CHECK ((publication_status = ANY (ARRAY['published'::text, 'hidden'::text, 'under_review'::text, 'removed'::text]))),
    CONSTRAINT facilities_smell_check CHECK (((smell >= 1) AND (smell <= 5))),
    CONSTRAINT facilities_temperature_check CHECK (((temperature >= 1) AND (temperature <= 5))),
    CONSTRAINT facilities_verification_status_check CHECK ((verification_status = ANY (ARRAY['source_imported'::text, 'source_verified'::text, 'community_confirmed'::text, 'staff_verified'::text, 'disputed'::text, 'stale'::text])))
);


--
-- Name: facility_reports; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.facility_reports (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    facility_id uuid NOT NULL,
    user_id uuid NOT NULL,
    type text NOT NULL,
    reason text NOT NULL,
    notes text DEFAULT ''::text,
    expires_at timestamp with time zone,
    created_at timestamp with time zone DEFAULT now(),
    CONSTRAINT facility_reports_reason_check CHECK ((reason = ANY (ARRAY['out_of_order'::text, 'no_water'::text, 'cleaning'::text, 'busy'::text, 'closed_permanently'::text, 'refurbishment'::text]))),
    CONSTRAINT facility_reports_type_check CHECK ((type = ANY (ARRAY['temporary'::text, 'permanent'::text])))
);


--
-- Name: facility_sources; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.facility_sources (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    facility_id uuid NOT NULL,
    import_run_id uuid,
    source_name text NOT NULL,
    source_record_id text NOT NULL,
    source_url text,
    source_licence text NOT NULL,
    source_updated_at timestamp with time zone,
    first_seen_at timestamp with time zone DEFAULT now() NOT NULL,
    last_seen_at timestamp with time zone DEFAULT now() NOT NULL,
    is_current boolean DEFAULT true NOT NULL,
    raw_data jsonb,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL
);


--
-- Name: facility_submissions; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.facility_submissions (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    user_id uuid NOT NULL,
    status text DEFAULT 'pending'::text NOT NULL,
    name text NOT NULL,
    address text NOT NULL,
    latitude double precision NOT NULL,
    longitude double precision NOT NULL,
    postcode text NOT NULL,
    town text NOT NULL,
    country text DEFAULT 'United Kingdom'::text NOT NULL,
    access_notes text DEFAULT ''::text,
    is_free boolean DEFAULT true,
    price_note text DEFAULT ''::text,
    open_hours jsonb,
    photos jsonb DEFAULT '[]'::jsonb,
    is_accessible boolean DEFAULT false,
    is_disabled_access boolean DEFAULT false,
    has_baby_changing boolean DEFAULT false,
    has_family_room boolean DEFAULT false,
    is_gender_neutral boolean DEFAULT false,
    is_single_occupancy boolean DEFAULT false,
    is_24h boolean DEFAULT false,
    notes text DEFAULT ''::text,
    access_codes text DEFAULT ''::text,
    submission_notes text DEFAULT ''::text,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    reviewed_at timestamp with time zone,
    reviewed_by uuid,
    rejection_reason text,
    CONSTRAINT facility_submissions_status_check CHECK ((status = ANY (ARRAY['pending'::text, 'approved'::text, 'rejected'::text])))
);


--
-- Name: favourites; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.favourites (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    user_id uuid NOT NULL,
    facility_id uuid NOT NULL,
    created_at timestamp with time zone DEFAULT now()
);


--
-- Name: import_runs; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.import_runs (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    source_name text NOT NULL,
    source_file_name text,
    source_checksum text,
    status text DEFAULT 'started'::text NOT NULL,
    started_at timestamp with time zone DEFAULT now() NOT NULL,
    completed_at timestamp with time zone,
    rows_received integer DEFAULT 0 NOT NULL,
    rows_valid integer DEFAULT 0 NOT NULL,
    rows_inserted integer DEFAULT 0 NOT NULL,
    rows_updated integer DEFAULT 0 NOT NULL,
    rows_unchanged integer DEFAULT 0 NOT NULL,
    rows_quarantined integer DEFAULT 0 NOT NULL,
    rows_marked_stale integer DEFAULT 0 NOT NULL,
    error_summary text,
    CONSTRAINT import_runs_status_check CHECK ((status = ANY (ARRAY['started'::text, 'completed'::text, 'failed'::text])))
);


--
-- Name: photo_moderation; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.photo_moderation (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    facility_id uuid NOT NULL,
    user_id uuid NOT NULL,
    url text NOT NULL,
    thumbnail_url text NOT NULL,
    status text DEFAULT 'pending'::text NOT NULL,
    exif_stripped boolean DEFAULT false,
    faces_blurred boolean DEFAULT false,
    reported_by uuid,
    report_reason text,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    CONSTRAINT photo_moderation_status_check CHECK ((status = ANY (ARRAY['pending'::text, 'approved'::text, 'rejected'::text, 'reported'::text])))
);


--
-- Name: rate_limits; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.rate_limits (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    user_id uuid NOT NULL,
    action text NOT NULL,
    "timestamp" timestamp with time zone DEFAULT now() NOT NULL
);


--
-- Name: review_reports; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.review_reports (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    review_id uuid NOT NULL,
    user_id uuid NOT NULL,
    reason text NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL
);


--
-- Name: saved_profiles; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.saved_profiles (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    user_id uuid NOT NULL,
    mode text NOT NULL,
    name text NOT NULL,
    preferences jsonb DEFAULT '{}'::jsonb NOT NULL,
    created_at timestamp with time zone DEFAULT now(),
    CONSTRAINT saved_profiles_mode_check CHECK ((mode = ANY (ARRAY['ibs'::text, 'family'::text, 'accessibility'::text, 'pregnancy'::text, 'neurodivergent'::text, 'elderly'::text])))
);


--
-- Name: subscription_events; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.subscription_events (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    user_id uuid NOT NULL,
    event_type text NOT NULL,
    tier text NOT NULL,
    previous_tier text,
    details jsonb,
    revenuecat_event_id text,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    CONSTRAINT subscription_events_event_type_check CHECK ((event_type = ANY (ARRAY['purchase_initial'::text, 'purchase_renewal'::text, 'cancellation'::text, 'expiration'::text, 'refund'::text, 'restore'::text, 'grace_period_start'::text, 'grace_period_end'::text, 'tier_change'::text, 'lifetime_purchase'::text])))
);


--
-- Name: temporary_reports; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.temporary_reports (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    facility_id uuid NOT NULL,
    user_id uuid NOT NULL,
    type text NOT NULL,
    notes text DEFAULT ''::text,
    expires_at timestamp with time zone NOT NULL,
    is_expired boolean DEFAULT false,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    CONSTRAINT temporary_reports_type_check CHECK ((type = ANY (ARRAY['out_of_order'::text, 'no_water'::text, 'cleaning'::text, 'busy'::text, 'closed'::text, 'refurbishment'::text])))
);


--
-- Name: toilet_map_import_staging; Type: TABLE; Schema: public; Owner: -
--

CREATE UNLOGGED TABLE public.toilet_map_import_staging (
    import_run_id uuid NOT NULL,
    source_record_id text NOT NULL,
    name text,
    latitude double precision,
    longitude double precision,
    address text,
    postcode text,
    town text,
    is_accessible boolean,
    has_baby_changing boolean,
    requires_radar_key boolean,
    is_free boolean,
    opening_hours jsonb,
    source_updated_at timestamp with time zone,
    raw_data jsonb,
    validation_errors text[]
);


--
-- Name: user_badges; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.user_badges (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    user_id uuid NOT NULL,
    badge_type text NOT NULL,
    awarded_at timestamp with time zone DEFAULT now(),
    CONSTRAINT user_badges_badge_type_check CHECK ((badge_type = ANY (ARRAY['explorer'::text, 'community_hero'::text, 'accessibility_champion'::text, 'family_helper'::text])))
);


--
-- Name: user_profiles; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.user_profiles (
    id uuid NOT NULL,
    email text,
    display_name text,
    avatar_url text,
    created_at timestamp with time zone DEFAULT now(),
    has_lifetime_access boolean DEFAULT false,
    subscription_tier text DEFAULT 'free'::text,
    subscription_expires_at timestamp with time zone,
    CONSTRAINT user_profiles_subscription_tier_check CHECK ((subscription_tier = ANY (ARRAY['free'::text, 'plus'::text])))
);


--
-- Name: user_subscriptions; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.user_subscriptions (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    user_id uuid NOT NULL,
    revenuecat_id text,
    tier text DEFAULT 'free'::text NOT NULL,
    is_active boolean DEFAULT false NOT NULL,
    lifetime_purchase_at timestamp with time zone,
    plus_monthly_purchase_at timestamp with time zone,
    plus_yearly_purchase_at timestamp with time zone,
    current_period_start timestamp with time zone,
    current_period_end timestamp with time zone,
    will_renew boolean DEFAULT true NOT NULL,
    is_grace_period boolean DEFAULT false NOT NULL,
    cancellation_at timestamp with time zone,
    cancelled_at timestamp with time zone,
    refunded_at timestamp with time zone,
    raw_revenuecat_json jsonb,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL,
    CONSTRAINT user_subscriptions_tier_check CHECK ((tier = ANY (ARRAY['free'::text, 'basic'::text, 'plus'::text])))
);


--
-- Name: access_codes access_codes_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.access_codes
    ADD CONSTRAINT access_codes_pkey PRIMARY KEY (id);


--
-- Name: correction_requests correction_requests_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.correction_requests
    ADD CONSTRAINT correction_requests_pkey PRIMARY KEY (id);


--
-- Name: facilities facilities_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.facilities
    ADD CONSTRAINT facilities_pkey PRIMARY KEY (id);


--
-- Name: facility_reports facility_reports_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.facility_reports
    ADD CONSTRAINT facility_reports_pkey PRIMARY KEY (id);


--
-- Name: facility_sources facility_sources_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.facility_sources
    ADD CONSTRAINT facility_sources_pkey PRIMARY KEY (id);


--
-- Name: facility_sources facility_sources_source_name_source_record_id_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.facility_sources
    ADD CONSTRAINT facility_sources_source_name_source_record_id_key UNIQUE (source_name, source_record_id);


--
-- Name: facility_submissions facility_submissions_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.facility_submissions
    ADD CONSTRAINT facility_submissions_pkey PRIMARY KEY (id);


--
-- Name: favourites favourites_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.favourites
    ADD CONSTRAINT favourites_pkey PRIMARY KEY (id);


--
-- Name: favourites favourites_user_id_facility_id_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.favourites
    ADD CONSTRAINT favourites_user_id_facility_id_key UNIQUE (user_id, facility_id);


--
-- Name: import_runs import_runs_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.import_runs
    ADD CONSTRAINT import_runs_pkey PRIMARY KEY (id);


--
-- Name: photo_moderation photo_moderation_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.photo_moderation
    ADD CONSTRAINT photo_moderation_pkey PRIMARY KEY (id);


--
-- Name: rate_limits rate_limits_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.rate_limits
    ADD CONSTRAINT rate_limits_pkey PRIMARY KEY (id);


--
-- Name: review_reports review_reports_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.review_reports
    ADD CONSTRAINT review_reports_pkey PRIMARY KEY (id);


--
-- Name: saved_profiles saved_profiles_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.saved_profiles
    ADD CONSTRAINT saved_profiles_pkey PRIMARY KEY (id);


--
-- Name: subscription_events subscription_events_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.subscription_events
    ADD CONSTRAINT subscription_events_pkey PRIMARY KEY (id);


--
-- Name: temporary_reports temporary_reports_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.temporary_reports
    ADD CONSTRAINT temporary_reports_pkey PRIMARY KEY (id);


--
-- Name: user_badges user_badges_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.user_badges
    ADD CONSTRAINT user_badges_pkey PRIMARY KEY (id);


--
-- Name: user_badges user_badges_user_id_badge_type_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.user_badges
    ADD CONSTRAINT user_badges_user_id_badge_type_key UNIQUE (user_id, badge_type);


--
-- Name: user_profiles user_profiles_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.user_profiles
    ADD CONSTRAINT user_profiles_pkey PRIMARY KEY (id);


--
-- Name: user_subscriptions user_subscriptions_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.user_subscriptions
    ADD CONSTRAINT user_subscriptions_pkey PRIMARY KEY (id);


--
-- Name: user_subscriptions user_subscriptions_revenuecat_id_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.user_subscriptions
    ADD CONSTRAINT user_subscriptions_revenuecat_id_key UNIQUE (revenuecat_id);


--
-- Name: facilities_location_gix; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX facilities_location_gix ON public.facilities USING gist (location);


--
-- Name: idx_access_codes_facility; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_access_codes_facility ON public.access_codes USING btree (facility_id);


--
-- Name: idx_correction_requests_facility; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_correction_requests_facility ON public.correction_requests USING btree (facility_id);


--
-- Name: idx_correction_requests_status; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_correction_requests_status ON public.correction_requests USING btree (status);


--
-- Name: idx_facilities_country; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_facilities_country ON public.facilities USING btree (country);


--
-- Name: idx_facilities_created_at; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_facilities_created_at ON public.facilities USING btree (created_at DESC);


--
-- Name: idx_facilities_field_provenance; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_facilities_field_provenance ON public.facilities USING gin (field_provenance);


--
-- Name: idx_facilities_is_verified; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_facilities_is_verified ON public.facilities USING btree (is_verified);


--
-- Name: idx_facilities_location; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_facilities_location ON public.facilities USING btree (latitude, longitude);


--
-- Name: idx_facilities_overall_score; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_facilities_overall_score ON public.facilities USING btree (overall_score DESC);


--
-- Name: idx_facilities_postcode; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_facilities_postcode ON public.facilities USING btree (postcode);


--
-- Name: idx_facilities_publication_status; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_facilities_publication_status ON public.facilities USING btree (publication_status);


--
-- Name: idx_facilities_town; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_facilities_town ON public.facilities USING btree (town);


--
-- Name: idx_facilities_verification_status; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_facilities_verification_status ON public.facilities USING btree (verification_status);


--
-- Name: idx_facility_sources_current; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_facility_sources_current ON public.facility_sources USING btree (source_name, is_current);


--
-- Name: idx_facility_sources_facility; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_facility_sources_facility ON public.facility_sources USING btree (facility_id);


--
-- Name: idx_facility_submissions_created; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_facility_submissions_created ON public.facility_submissions USING btree (created_at DESC);


--
-- Name: idx_facility_submissions_status; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_facility_submissions_status ON public.facility_submissions USING btree (status);


--
-- Name: idx_facility_submissions_user; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_facility_submissions_user ON public.facility_submissions USING btree (user_id);


--
-- Name: idx_favourites_facility; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_favourites_facility ON public.favourites USING btree (facility_id);


--
-- Name: idx_favourites_user; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_favourites_user ON public.favourites USING btree (user_id);


--
-- Name: idx_photo_moderation_facility; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_photo_moderation_facility ON public.photo_moderation USING btree (facility_id);


--
-- Name: idx_photo_moderation_status; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_photo_moderation_status ON public.photo_moderation USING btree (status);


--
-- Name: idx_rate_limits_lookup; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_rate_limits_lookup ON public.rate_limits USING btree (user_id, action, "timestamp" DESC);


--
-- Name: idx_reports_expires; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_reports_expires ON public.facility_reports USING btree (expires_at);


--
-- Name: idx_reports_facility; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_reports_facility ON public.facility_reports USING btree (facility_id);


--
-- Name: idx_saved_profiles_user; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_saved_profiles_user ON public.saved_profiles USING btree (user_id);


--
-- Name: idx_subscription_events_type; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_subscription_events_type ON public.subscription_events USING btree (event_type);


--
-- Name: idx_subscription_events_user; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_subscription_events_user ON public.subscription_events USING btree (user_id);


--
-- Name: idx_temporary_reports_active; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_temporary_reports_active ON public.temporary_reports USING btree (facility_id, is_expired, expires_at);


--
-- Name: idx_temporary_reports_expires; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_temporary_reports_expires ON public.temporary_reports USING btree (expires_at);


--
-- Name: idx_temporary_reports_facility; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_temporary_reports_facility ON public.temporary_reports USING btree (facility_id);


--
-- Name: idx_user_subscriptions_active; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_user_subscriptions_active ON public.user_subscriptions USING btree (is_active);


--
-- Name: idx_user_subscriptions_tier; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_user_subscriptions_tier ON public.user_subscriptions USING btree (tier);


--
-- Name: idx_user_subscriptions_user; Type: INDEX; Schema: public; Owner: -
--

CREATE UNIQUE INDEX idx_user_subscriptions_user ON public.user_subscriptions USING btree (user_id);


--
-- Name: facilities facilities_updated_at; Type: TRIGGER; Schema: public; Owner: -
--

CREATE TRIGGER facilities_updated_at BEFORE UPDATE ON public.facilities FOR EACH ROW EXECUTE FUNCTION public.update_updated_at();


--
-- Name: access_codes access_codes_facility_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.access_codes
    ADD CONSTRAINT access_codes_facility_id_fkey FOREIGN KEY (facility_id) REFERENCES public.facilities(id) ON DELETE CASCADE;


--
-- Name: access_codes access_codes_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.access_codes
    ADD CONSTRAINT access_codes_user_id_fkey FOREIGN KEY (user_id) REFERENCES auth.users(id) ON DELETE CASCADE;


--
-- Name: correction_requests correction_requests_facility_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.correction_requests
    ADD CONSTRAINT correction_requests_facility_id_fkey FOREIGN KEY (facility_id) REFERENCES public.facilities(id) ON DELETE CASCADE;


--
-- Name: correction_requests correction_requests_reviewed_by_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.correction_requests
    ADD CONSTRAINT correction_requests_reviewed_by_fkey FOREIGN KEY (reviewed_by) REFERENCES auth.users(id);


--
-- Name: correction_requests correction_requests_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.correction_requests
    ADD CONSTRAINT correction_requests_user_id_fkey FOREIGN KEY (user_id) REFERENCES auth.users(id) ON DELETE CASCADE;


--
-- Name: facilities facilities_created_by_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.facilities
    ADD CONSTRAINT facilities_created_by_fkey FOREIGN KEY (created_by) REFERENCES auth.users(id) ON DELETE SET NULL;


--
-- Name: facility_reports facility_reports_facility_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.facility_reports
    ADD CONSTRAINT facility_reports_facility_id_fkey FOREIGN KEY (facility_id) REFERENCES public.facilities(id) ON DELETE CASCADE;


--
-- Name: facility_reports facility_reports_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.facility_reports
    ADD CONSTRAINT facility_reports_user_id_fkey FOREIGN KEY (user_id) REFERENCES auth.users(id) ON DELETE CASCADE;


--
-- Name: facility_sources facility_sources_facility_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.facility_sources
    ADD CONSTRAINT facility_sources_facility_id_fkey FOREIGN KEY (facility_id) REFERENCES public.facilities(id) ON DELETE CASCADE;


--
-- Name: facility_sources facility_sources_import_run_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.facility_sources
    ADD CONSTRAINT facility_sources_import_run_id_fkey FOREIGN KEY (import_run_id) REFERENCES public.import_runs(id);


--
-- Name: facility_submissions facility_submissions_reviewed_by_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.facility_submissions
    ADD CONSTRAINT facility_submissions_reviewed_by_fkey FOREIGN KEY (reviewed_by) REFERENCES auth.users(id);


--
-- Name: facility_submissions facility_submissions_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.facility_submissions
    ADD CONSTRAINT facility_submissions_user_id_fkey FOREIGN KEY (user_id) REFERENCES auth.users(id) ON DELETE CASCADE;


--
-- Name: favourites favourites_facility_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.favourites
    ADD CONSTRAINT favourites_facility_id_fkey FOREIGN KEY (facility_id) REFERENCES public.facilities(id) ON DELETE CASCADE;


--
-- Name: favourites favourites_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.favourites
    ADD CONSTRAINT favourites_user_id_fkey FOREIGN KEY (user_id) REFERENCES auth.users(id) ON DELETE CASCADE;


--
-- Name: photo_moderation photo_moderation_facility_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.photo_moderation
    ADD CONSTRAINT photo_moderation_facility_id_fkey FOREIGN KEY (facility_id) REFERENCES public.facilities(id) ON DELETE CASCADE;


--
-- Name: photo_moderation photo_moderation_reported_by_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.photo_moderation
    ADD CONSTRAINT photo_moderation_reported_by_fkey FOREIGN KEY (reported_by) REFERENCES auth.users(id);


--
-- Name: photo_moderation photo_moderation_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.photo_moderation
    ADD CONSTRAINT photo_moderation_user_id_fkey FOREIGN KEY (user_id) REFERENCES auth.users(id) ON DELETE CASCADE;


--
-- Name: rate_limits rate_limits_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.rate_limits
    ADD CONSTRAINT rate_limits_user_id_fkey FOREIGN KEY (user_id) REFERENCES auth.users(id) ON DELETE CASCADE;


--
-- Name: review_reports review_reports_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.review_reports
    ADD CONSTRAINT review_reports_user_id_fkey FOREIGN KEY (user_id) REFERENCES auth.users(id) ON DELETE CASCADE;


--
-- Name: saved_profiles saved_profiles_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.saved_profiles
    ADD CONSTRAINT saved_profiles_user_id_fkey FOREIGN KEY (user_id) REFERENCES auth.users(id) ON DELETE CASCADE;


--
-- Name: subscription_events subscription_events_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.subscription_events
    ADD CONSTRAINT subscription_events_user_id_fkey FOREIGN KEY (user_id) REFERENCES auth.users(id) ON DELETE CASCADE;


--
-- Name: temporary_reports temporary_reports_facility_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.temporary_reports
    ADD CONSTRAINT temporary_reports_facility_id_fkey FOREIGN KEY (facility_id) REFERENCES public.facilities(id) ON DELETE CASCADE;


--
-- Name: temporary_reports temporary_reports_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.temporary_reports
    ADD CONSTRAINT temporary_reports_user_id_fkey FOREIGN KEY (user_id) REFERENCES auth.users(id) ON DELETE CASCADE;


--
-- Name: toilet_map_import_staging toilet_map_import_staging_import_run_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.toilet_map_import_staging
    ADD CONSTRAINT toilet_map_import_staging_import_run_id_fkey FOREIGN KEY (import_run_id) REFERENCES public.import_runs(id);


--
-- Name: user_badges user_badges_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.user_badges
    ADD CONSTRAINT user_badges_user_id_fkey FOREIGN KEY (user_id) REFERENCES auth.users(id) ON DELETE CASCADE;


--
-- Name: user_profiles user_profiles_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.user_profiles
    ADD CONSTRAINT user_profiles_id_fkey FOREIGN KEY (id) REFERENCES auth.users(id) ON DELETE CASCADE;


--
-- Name: user_subscriptions user_subscriptions_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.user_subscriptions
    ADD CONSTRAINT user_subscriptions_user_id_fkey FOREIGN KEY (user_id) REFERENCES auth.users(id) ON DELETE CASCADE;


--
-- Name: facility_submissions Admins can update submissions; Type: POLICY; Schema: public; Owner: -
--

CREATE POLICY "Admins can update submissions" ON public.facility_submissions FOR UPDATE TO service_role USING (true);


--
-- Name: facility_submissions Admins can view all submissions; Type: POLICY; Schema: public; Owner: -
--

CREATE POLICY "Admins can view all submissions" ON public.facility_submissions FOR SELECT TO service_role USING (true);


--
-- Name: temporary_reports Anyone can view active reports; Type: POLICY; Schema: public; Owner: -
--

CREATE POLICY "Anyone can view active reports" ON public.temporary_reports FOR SELECT TO authenticated, anon USING (((is_expired = false) AND (expires_at > now())));


--
-- Name: photo_moderation Anyone can view approved photos; Type: POLICY; Schema: public; Owner: -
--

CREATE POLICY "Anyone can view approved photos" ON public.photo_moderation FOR SELECT TO authenticated, anon USING ((status = 'approved'::text));


--
-- Name: access_codes Anyone can view verified access codes; Type: POLICY; Schema: public; Owner: -
--

CREATE POLICY "Anyone can view verified access codes" ON public.access_codes FOR SELECT TO authenticated, anon USING (((is_verified = true) AND (EXISTS ( SELECT 1
   FROM public.facilities f
  WHERE ((f.id = access_codes.facility_id) AND (f.publication_status = 'published'::text))))));


--
-- Name: facility_reports Authenticated users can create reports; Type: POLICY; Schema: public; Owner: -
--

CREATE POLICY "Authenticated users can create reports" ON public.facility_reports FOR INSERT TO authenticated WITH CHECK ((user_id = auth.uid()));


--
-- Name: user_badges Badges are viewable by everyone; Type: POLICY; Schema: public; Owner: -
--

CREATE POLICY "Badges are viewable by everyone" ON public.user_badges FOR SELECT USING (true);


--
-- Name: facilities Published facilities are viewable by everyone; Type: POLICY; Schema: public; Owner: -
--

CREATE POLICY "Published facilities are viewable by everyone" ON public.facilities FOR SELECT USING ((publication_status = 'published'::text));


--
-- Name: facility_sources Published facility sources are viewable; Type: POLICY; Schema: public; Owner: -
--

CREATE POLICY "Published facility sources are viewable" ON public.facility_sources FOR SELECT USING ((EXISTS ( SELECT 1
   FROM public.facilities
  WHERE ((facilities.id = facility_sources.facility_id) AND (facilities.publication_status = 'published'::text)))));


--
-- Name: facility_reports Reports are viewable by everyone; Type: POLICY; Schema: public; Owner: -
--

CREATE POLICY "Reports are viewable by everyone" ON public.facility_reports FOR SELECT USING (true);


--
-- Name: subscription_events Service role manages events; Type: POLICY; Schema: public; Owner: -
--

CREATE POLICY "Service role manages events" ON public.subscription_events FOR INSERT TO service_role WITH CHECK (true);


--
-- Name: rate_limits Service role manages rate limits; Type: POLICY; Schema: public; Owner: -
--

CREATE POLICY "Service role manages rate limits" ON public.rate_limits TO service_role USING (true);


--
-- Name: user_subscriptions Service role manages subscriptions; Type: POLICY; Schema: public; Owner: -
--

CREATE POLICY "Service role manages subscriptions" ON public.user_subscriptions TO service_role USING (true) WITH CHECK (true);


--
-- Name: access_codes Users can insert access codes; Type: POLICY; Schema: public; Owner: -
--

CREATE POLICY "Users can insert access codes" ON public.access_codes FOR INSERT TO authenticated WITH CHECK ((auth.uid() = user_id));


--
-- Name: correction_requests Users can insert corrections; Type: POLICY; Schema: public; Owner: -
--

CREATE POLICY "Users can insert corrections" ON public.correction_requests FOR INSERT TO authenticated WITH CHECK ((auth.uid() = user_id));


--
-- Name: temporary_reports Users can insert reports; Type: POLICY; Schema: public; Owner: -
--

CREATE POLICY "Users can insert reports" ON public.temporary_reports FOR INSERT TO authenticated WITH CHECK ((auth.uid() = user_id));


--
-- Name: photo_moderation Users can insert their own photos; Type: POLICY; Schema: public; Owner: -
--

CREATE POLICY "Users can insert their own photos" ON public.photo_moderation FOR INSERT TO authenticated WITH CHECK ((auth.uid() = user_id));


--
-- Name: rate_limits Users can insert their own rate limits; Type: POLICY; Schema: public; Owner: -
--

CREATE POLICY "Users can insert their own rate limits" ON public.rate_limits FOR INSERT TO authenticated WITH CHECK ((auth.uid() = user_id));


--
-- Name: facility_submissions Users can insert their own submissions; Type: POLICY; Schema: public; Owner: -
--

CREATE POLICY "Users can insert their own submissions" ON public.facility_submissions FOR INSERT TO authenticated WITH CHECK ((auth.uid() = user_id));


--
-- Name: favourites Users can manage own favourites; Type: POLICY; Schema: public; Owner: -
--

CREATE POLICY "Users can manage own favourites" ON public.favourites TO authenticated USING ((auth.uid() = user_id)) WITH CHECK ((auth.uid() = user_id));


--
-- Name: saved_profiles Users can manage own profiles; Type: POLICY; Schema: public; Owner: -
--

CREATE POLICY "Users can manage own profiles" ON public.saved_profiles TO authenticated USING ((auth.uid() = user_id)) WITH CHECK ((auth.uid() = user_id));


--
-- Name: subscription_events Users can read own events; Type: POLICY; Schema: public; Owner: -
--

CREATE POLICY "Users can read own events" ON public.subscription_events FOR SELECT TO authenticated USING ((auth.uid() = user_id));


--
-- Name: user_subscriptions Users can read own subscription; Type: POLICY; Schema: public; Owner: -
--

CREATE POLICY "Users can read own subscription" ON public.user_subscriptions FOR SELECT TO authenticated USING ((auth.uid() = user_id));


--
-- Name: rate_limits Users can read their own rate limits; Type: POLICY; Schema: public; Owner: -
--

CREATE POLICY "Users can read their own rate limits" ON public.rate_limits FOR SELECT TO authenticated USING ((auth.uid() = user_id));


--
-- Name: review_reports Users can report reviews; Type: POLICY; Schema: public; Owner: -
--

CREATE POLICY "Users can report reviews" ON public.review_reports FOR INSERT TO authenticated WITH CHECK ((auth.uid() = user_id));


--
-- Name: temporary_reports Users can resolve their own reports; Type: POLICY; Schema: public; Owner: -
--

CREATE POLICY "Users can resolve their own reports" ON public.temporary_reports FOR UPDATE TO authenticated USING ((auth.uid() = user_id)) WITH CHECK ((is_expired = true));


--
-- Name: access_codes Users can update their own access codes; Type: POLICY; Schema: public; Owner: -
--

CREATE POLICY "Users can update their own access codes" ON public.access_codes FOR UPDATE TO authenticated USING ((auth.uid() = user_id));


--
-- Name: user_profiles Users can update their own profile; Type: POLICY; Schema: public; Owner: -
--

CREATE POLICY "Users can update their own profile" ON public.user_profiles FOR UPDATE TO authenticated USING ((( SELECT auth.uid() AS uid) = id)) WITH CHECK ((( SELECT auth.uid() AS uid) = id));


--
-- Name: access_codes Users can view their own access codes; Type: POLICY; Schema: public; Owner: -
--

CREATE POLICY "Users can view their own access codes" ON public.access_codes FOR SELECT TO authenticated USING ((( SELECT auth.uid() AS uid) = user_id));


--
-- Name: correction_requests Users can view their own corrections; Type: POLICY; Schema: public; Owner: -
--

CREATE POLICY "Users can view their own corrections" ON public.correction_requests FOR SELECT TO authenticated USING ((auth.uid() = user_id));


--
-- Name: photo_moderation Users can view their own pending photos; Type: POLICY; Schema: public; Owner: -
--

CREATE POLICY "Users can view their own pending photos" ON public.photo_moderation FOR SELECT TO authenticated USING ((auth.uid() = user_id));


--
-- Name: user_profiles Users can view their own profile; Type: POLICY; Schema: public; Owner: -
--

CREATE POLICY "Users can view their own profile" ON public.user_profiles FOR SELECT USING ((id = auth.uid()));


--
-- Name: facility_submissions Users can view their own submissions; Type: POLICY; Schema: public; Owner: -
--

CREATE POLICY "Users can view their own submissions" ON public.facility_submissions FOR SELECT TO authenticated USING ((auth.uid() = user_id));


--
-- Name: access_codes; Type: ROW SECURITY; Schema: public; Owner: -
--

ALTER TABLE public.access_codes ENABLE ROW LEVEL SECURITY;

--
-- Name: correction_requests; Type: ROW SECURITY; Schema: public; Owner: -
--

ALTER TABLE public.correction_requests ENABLE ROW LEVEL SECURITY;

--
-- Name: facilities; Type: ROW SECURITY; Schema: public; Owner: -
--

ALTER TABLE public.facilities ENABLE ROW LEVEL SECURITY;

--
-- Name: facility_reports; Type: ROW SECURITY; Schema: public; Owner: -
--

ALTER TABLE public.facility_reports ENABLE ROW LEVEL SECURITY;

--
-- Name: facility_sources; Type: ROW SECURITY; Schema: public; Owner: -
--

ALTER TABLE public.facility_sources ENABLE ROW LEVEL SECURITY;

--
-- Name: facility_submissions; Type: ROW SECURITY; Schema: public; Owner: -
--

ALTER TABLE public.facility_submissions ENABLE ROW LEVEL SECURITY;

--
-- Name: favourites; Type: ROW SECURITY; Schema: public; Owner: -
--

ALTER TABLE public.favourites ENABLE ROW LEVEL SECURITY;

--
-- Name: import_runs; Type: ROW SECURITY; Schema: public; Owner: -
--

ALTER TABLE public.import_runs ENABLE ROW LEVEL SECURITY;

--
-- Name: photo_moderation; Type: ROW SECURITY; Schema: public; Owner: -
--

ALTER TABLE public.photo_moderation ENABLE ROW LEVEL SECURITY;

--
-- Name: rate_limits; Type: ROW SECURITY; Schema: public; Owner: -
--

ALTER TABLE public.rate_limits ENABLE ROW LEVEL SECURITY;

--
-- Name: review_reports; Type: ROW SECURITY; Schema: public; Owner: -
--

ALTER TABLE public.review_reports ENABLE ROW LEVEL SECURITY;

--
-- Name: saved_profiles; Type: ROW SECURITY; Schema: public; Owner: -
--

ALTER TABLE public.saved_profiles ENABLE ROW LEVEL SECURITY;

--
-- Name: subscription_events; Type: ROW SECURITY; Schema: public; Owner: -
--

ALTER TABLE public.subscription_events ENABLE ROW LEVEL SECURITY;

--
-- Name: temporary_reports; Type: ROW SECURITY; Schema: public; Owner: -
--

ALTER TABLE public.temporary_reports ENABLE ROW LEVEL SECURITY;

--
-- Name: toilet_map_import_staging; Type: ROW SECURITY; Schema: public; Owner: -
--

ALTER TABLE public.toilet_map_import_staging ENABLE ROW LEVEL SECURITY;

--
-- Name: user_badges; Type: ROW SECURITY; Schema: public; Owner: -
--

ALTER TABLE public.user_badges ENABLE ROW LEVEL SECURITY;

--
-- Name: user_profiles; Type: ROW SECURITY; Schema: public; Owner: -
--

ALTER TABLE public.user_profiles ENABLE ROW LEVEL SECURITY;

--
-- Name: user_subscriptions; Type: ROW SECURITY; Schema: public; Owner: -
--

ALTER TABLE public.user_subscriptions ENABLE ROW LEVEL SECURITY;

--
-- Name: SCHEMA public; Type: ACL; Schema: -; Owner: -
--

GRANT USAGE ON SCHEMA public TO postgres;
GRANT USAGE ON SCHEMA public TO anon;
GRANT USAGE ON SCHEMA public TO authenticated;
GRANT USAGE ON SCHEMA public TO service_role;


--
-- Name: FUNCTION expire_temporary_reports(); Type: ACL; Schema: public; Owner: -
--

GRANT ALL ON FUNCTION public.expire_temporary_reports() TO anon;
GRANT ALL ON FUNCTION public.expire_temporary_reports() TO authenticated;
GRANT ALL ON FUNCTION public.expire_temporary_reports() TO service_role;


--
-- Name: FUNCTION find_nearest_facilities(user_latitude double precision, user_longitude double precision, search_radius_metres integer, result_limit integer); Type: ACL; Schema: public; Owner: -
--

GRANT ALL ON FUNCTION public.find_nearest_facilities(user_latitude double precision, user_longitude double precision, search_radius_metres integer, result_limit integer) TO anon;
GRANT ALL ON FUNCTION public.find_nearest_facilities(user_latitude double precision, user_longitude double precision, search_radius_metres integer, result_limit integer) TO authenticated;
GRANT ALL ON FUNCTION public.find_nearest_facilities(user_latitude double precision, user_longitude double precision, search_radius_metres integer, result_limit integer) TO service_role;


--
-- Name: FUNCTION handle_new_user(); Type: ACL; Schema: public; Owner: -
--

GRANT ALL ON FUNCTION public.handle_new_user() TO anon;
GRANT ALL ON FUNCTION public.handle_new_user() TO authenticated;
GRANT ALL ON FUNCTION public.handle_new_user() TO service_role;


--
-- Name: FUNCTION rls_auto_enable(); Type: ACL; Schema: public; Owner: -
--

GRANT ALL ON FUNCTION public.rls_auto_enable() TO anon;
GRANT ALL ON FUNCTION public.rls_auto_enable() TO authenticated;
GRANT ALL ON FUNCTION public.rls_auto_enable() TO service_role;


--
-- Name: FUNCTION sync_subscription_from_revenuecat(p_user_id uuid, p_tier text, p_is_active boolean, p_lifetime_purchase_at timestamp with time zone, p_current_period_start timestamp with time zone, p_current_period_end timestamp with time zone, p_will_renew boolean, p_is_grace_period boolean, p_cancellation_at timestamp with time zone, p_cancelled_at timestamp with time zone, p_refunded_at timestamp with time zone, p_raw_json jsonb, p_event_type text, p_previous_tier text); Type: ACL; Schema: public; Owner: -
--

REVOKE ALL ON FUNCTION public.sync_subscription_from_revenuecat(p_user_id uuid, p_tier text, p_is_active boolean, p_lifetime_purchase_at timestamp with time zone, p_current_period_start timestamp with time zone, p_current_period_end timestamp with time zone, p_will_renew boolean, p_is_grace_period boolean, p_cancellation_at timestamp with time zone, p_cancelled_at timestamp with time zone, p_refunded_at timestamp with time zone, p_raw_json jsonb, p_event_type text, p_previous_tier text) FROM PUBLIC;
GRANT ALL ON FUNCTION public.sync_subscription_from_revenuecat(p_user_id uuid, p_tier text, p_is_active boolean, p_lifetime_purchase_at timestamp with time zone, p_current_period_start timestamp with time zone, p_current_period_end timestamp with time zone, p_will_renew boolean, p_is_grace_period boolean, p_cancellation_at timestamp with time zone, p_cancelled_at timestamp with time zone, p_refunded_at timestamp with time zone, p_raw_json jsonb, p_event_type text, p_previous_tier text) TO anon;
GRANT ALL ON FUNCTION public.sync_subscription_from_revenuecat(p_user_id uuid, p_tier text, p_is_active boolean, p_lifetime_purchase_at timestamp with time zone, p_current_period_start timestamp with time zone, p_current_period_end timestamp with time zone, p_will_renew boolean, p_is_grace_period boolean, p_cancellation_at timestamp with time zone, p_cancelled_at timestamp with time zone, p_refunded_at timestamp with time zone, p_raw_json jsonb, p_event_type text, p_previous_tier text) TO authenticated;
GRANT ALL ON FUNCTION public.sync_subscription_from_revenuecat(p_user_id uuid, p_tier text, p_is_active boolean, p_lifetime_purchase_at timestamp with time zone, p_current_period_start timestamp with time zone, p_current_period_end timestamp with time zone, p_will_renew boolean, p_is_grace_period boolean, p_cancellation_at timestamp with time zone, p_cancelled_at timestamp with time zone, p_refunded_at timestamp with time zone, p_raw_json jsonb, p_event_type text, p_previous_tier text) TO service_role;


--
-- Name: FUNCTION update_updated_at(); Type: ACL; Schema: public; Owner: -
--

GRANT ALL ON FUNCTION public.update_updated_at() TO anon;
GRANT ALL ON FUNCTION public.update_updated_at() TO authenticated;
GRANT ALL ON FUNCTION public.update_updated_at() TO service_role;


--
-- Name: TABLE access_codes; Type: ACL; Schema: public; Owner: -
--

GRANT SELECT,REFERENCES,DELETE,TRIGGER,TRUNCATE,MAINTAIN ON TABLE public.access_codes TO anon;
GRANT SELECT,REFERENCES,DELETE,TRIGGER,TRUNCATE,MAINTAIN ON TABLE public.access_codes TO authenticated;
GRANT ALL ON TABLE public.access_codes TO service_role;


--
-- Name: COLUMN access_codes.facility_id; Type: ACL; Schema: public; Owner: -
--

GRANT INSERT(facility_id) ON TABLE public.access_codes TO authenticated;


--
-- Name: COLUMN access_codes.user_id; Type: ACL; Schema: public; Owner: -
--

GRANT INSERT(user_id) ON TABLE public.access_codes TO authenticated;


--
-- Name: COLUMN access_codes.code; Type: ACL; Schema: public; Owner: -
--

GRANT INSERT(code),UPDATE(code) ON TABLE public.access_codes TO authenticated;


--
-- Name: COLUMN access_codes.description; Type: ACL; Schema: public; Owner: -
--

GRANT INSERT(description),UPDATE(description) ON TABLE public.access_codes TO authenticated;


--
-- Name: TABLE correction_requests; Type: ACL; Schema: public; Owner: -
--

GRANT ALL ON TABLE public.correction_requests TO anon;
GRANT ALL ON TABLE public.correction_requests TO authenticated;
GRANT ALL ON TABLE public.correction_requests TO service_role;


--
-- Name: TABLE facilities; Type: ACL; Schema: public; Owner: -
--

GRANT ALL ON TABLE public.facilities TO anon;
GRANT ALL ON TABLE public.facilities TO authenticated;
GRANT ALL ON TABLE public.facilities TO service_role;


--
-- Name: TABLE facility_reports; Type: ACL; Schema: public; Owner: -
--

GRANT ALL ON TABLE public.facility_reports TO anon;
GRANT ALL ON TABLE public.facility_reports TO authenticated;
GRANT ALL ON TABLE public.facility_reports TO service_role;


--
-- Name: TABLE facility_sources; Type: ACL; Schema: public; Owner: -
--

GRANT ALL ON TABLE public.facility_sources TO anon;
GRANT ALL ON TABLE public.facility_sources TO authenticated;
GRANT ALL ON TABLE public.facility_sources TO service_role;


--
-- Name: TABLE facility_submissions; Type: ACL; Schema: public; Owner: -
--

GRANT ALL ON TABLE public.facility_submissions TO anon;
GRANT ALL ON TABLE public.facility_submissions TO authenticated;
GRANT ALL ON TABLE public.facility_submissions TO service_role;


--
-- Name: TABLE favourites; Type: ACL; Schema: public; Owner: -
--

GRANT ALL ON TABLE public.favourites TO anon;
GRANT ALL ON TABLE public.favourites TO authenticated;
GRANT ALL ON TABLE public.favourites TO service_role;


--
-- Name: TABLE import_runs; Type: ACL; Schema: public; Owner: -
--

GRANT ALL ON TABLE public.import_runs TO anon;
GRANT ALL ON TABLE public.import_runs TO authenticated;
GRANT ALL ON TABLE public.import_runs TO service_role;


--
-- Name: TABLE photo_moderation; Type: ACL; Schema: public; Owner: -
--

GRANT ALL ON TABLE public.photo_moderation TO anon;
GRANT ALL ON TABLE public.photo_moderation TO authenticated;
GRANT ALL ON TABLE public.photo_moderation TO service_role;


--
-- Name: TABLE rate_limits; Type: ACL; Schema: public; Owner: -
--

GRANT ALL ON TABLE public.rate_limits TO anon;
GRANT ALL ON TABLE public.rate_limits TO authenticated;
GRANT ALL ON TABLE public.rate_limits TO service_role;


--
-- Name: TABLE review_reports; Type: ACL; Schema: public; Owner: -
--

GRANT ALL ON TABLE public.review_reports TO anon;
GRANT ALL ON TABLE public.review_reports TO authenticated;
GRANT ALL ON TABLE public.review_reports TO service_role;


--
-- Name: TABLE saved_profiles; Type: ACL; Schema: public; Owner: -
--

GRANT ALL ON TABLE public.saved_profiles TO anon;
GRANT ALL ON TABLE public.saved_profiles TO authenticated;
GRANT ALL ON TABLE public.saved_profiles TO service_role;


--
-- Name: TABLE subscription_events; Type: ACL; Schema: public; Owner: -
--

GRANT ALL ON TABLE public.subscription_events TO anon;
GRANT ALL ON TABLE public.subscription_events TO authenticated;
GRANT ALL ON TABLE public.subscription_events TO service_role;


--
-- Name: TABLE temporary_reports; Type: ACL; Schema: public; Owner: -
--

GRANT ALL ON TABLE public.temporary_reports TO anon;
GRANT ALL ON TABLE public.temporary_reports TO authenticated;
GRANT ALL ON TABLE public.temporary_reports TO service_role;


--
-- Name: TABLE toilet_map_import_staging; Type: ACL; Schema: public; Owner: -
--

GRANT ALL ON TABLE public.toilet_map_import_staging TO anon;
GRANT ALL ON TABLE public.toilet_map_import_staging TO authenticated;
GRANT ALL ON TABLE public.toilet_map_import_staging TO service_role;


--
-- Name: TABLE user_badges; Type: ACL; Schema: public; Owner: -
--

GRANT ALL ON TABLE public.user_badges TO anon;
GRANT ALL ON TABLE public.user_badges TO authenticated;
GRANT ALL ON TABLE public.user_badges TO service_role;


--
-- Name: TABLE user_profiles; Type: ACL; Schema: public; Owner: -
--

GRANT SELECT,INSERT,REFERENCES,DELETE,TRIGGER,TRUNCATE,MAINTAIN ON TABLE public.user_profiles TO anon;
GRANT SELECT,INSERT,REFERENCES,DELETE,TRIGGER,TRUNCATE,MAINTAIN ON TABLE public.user_profiles TO authenticated;
GRANT ALL ON TABLE public.user_profiles TO service_role;


--
-- Name: COLUMN user_profiles.display_name; Type: ACL; Schema: public; Owner: -
--

GRANT UPDATE(display_name) ON TABLE public.user_profiles TO authenticated;


--
-- Name: COLUMN user_profiles.avatar_url; Type: ACL; Schema: public; Owner: -
--

GRANT UPDATE(avatar_url) ON TABLE public.user_profiles TO authenticated;


--
-- Name: TABLE user_subscriptions; Type: ACL; Schema: public; Owner: -
--

GRANT ALL ON TABLE public.user_subscriptions TO anon;
GRANT ALL ON TABLE public.user_subscriptions TO authenticated;
GRANT ALL ON TABLE public.user_subscriptions TO service_role;


--
-- Name: DEFAULT PRIVILEGES FOR SEQUENCES; Type: DEFAULT ACL; Schema: public; Owner: -
--

ALTER DEFAULT PRIVILEGES FOR ROLE postgres IN SCHEMA public GRANT ALL ON SEQUENCES TO postgres;
ALTER DEFAULT PRIVILEGES FOR ROLE postgres IN SCHEMA public GRANT ALL ON SEQUENCES TO anon;
ALTER DEFAULT PRIVILEGES FOR ROLE postgres IN SCHEMA public GRANT ALL ON SEQUENCES TO authenticated;
ALTER DEFAULT PRIVILEGES FOR ROLE postgres IN SCHEMA public GRANT ALL ON SEQUENCES TO service_role;


--
-- Name: DEFAULT PRIVILEGES FOR SEQUENCES; Type: DEFAULT ACL; Schema: public; Owner: -
--

ALTER DEFAULT PRIVILEGES FOR ROLE supabase_admin IN SCHEMA public GRANT ALL ON SEQUENCES TO postgres;
ALTER DEFAULT PRIVILEGES FOR ROLE supabase_admin IN SCHEMA public GRANT ALL ON SEQUENCES TO anon;
ALTER DEFAULT PRIVILEGES FOR ROLE supabase_admin IN SCHEMA public GRANT ALL ON SEQUENCES TO authenticated;
ALTER DEFAULT PRIVILEGES FOR ROLE supabase_admin IN SCHEMA public GRANT ALL ON SEQUENCES TO service_role;


--
-- Name: DEFAULT PRIVILEGES FOR FUNCTIONS; Type: DEFAULT ACL; Schema: public; Owner: -
--

ALTER DEFAULT PRIVILEGES FOR ROLE postgres IN SCHEMA public GRANT ALL ON FUNCTIONS TO postgres;
ALTER DEFAULT PRIVILEGES FOR ROLE postgres IN SCHEMA public GRANT ALL ON FUNCTIONS TO anon;
ALTER DEFAULT PRIVILEGES FOR ROLE postgres IN SCHEMA public GRANT ALL ON FUNCTIONS TO authenticated;
ALTER DEFAULT PRIVILEGES FOR ROLE postgres IN SCHEMA public GRANT ALL ON FUNCTIONS TO service_role;


--
-- Name: DEFAULT PRIVILEGES FOR FUNCTIONS; Type: DEFAULT ACL; Schema: public; Owner: -
--

ALTER DEFAULT PRIVILEGES FOR ROLE supabase_admin IN SCHEMA public GRANT ALL ON FUNCTIONS TO postgres;
ALTER DEFAULT PRIVILEGES FOR ROLE supabase_admin IN SCHEMA public GRANT ALL ON FUNCTIONS TO anon;
ALTER DEFAULT PRIVILEGES FOR ROLE supabase_admin IN SCHEMA public GRANT ALL ON FUNCTIONS TO authenticated;
ALTER DEFAULT PRIVILEGES FOR ROLE supabase_admin IN SCHEMA public GRANT ALL ON FUNCTIONS TO service_role;


--
-- Name: DEFAULT PRIVILEGES FOR TABLES; Type: DEFAULT ACL; Schema: public; Owner: -
--

ALTER DEFAULT PRIVILEGES FOR ROLE postgres IN SCHEMA public GRANT ALL ON TABLES TO postgres;
ALTER DEFAULT PRIVILEGES FOR ROLE postgres IN SCHEMA public GRANT ALL ON TABLES TO anon;
ALTER DEFAULT PRIVILEGES FOR ROLE postgres IN SCHEMA public GRANT ALL ON TABLES TO authenticated;
ALTER DEFAULT PRIVILEGES FOR ROLE postgres IN SCHEMA public GRANT ALL ON TABLES TO service_role;


--
-- Name: DEFAULT PRIVILEGES FOR TABLES; Type: DEFAULT ACL; Schema: public; Owner: -
--

ALTER DEFAULT PRIVILEGES FOR ROLE supabase_admin IN SCHEMA public GRANT ALL ON TABLES TO postgres;
ALTER DEFAULT PRIVILEGES FOR ROLE supabase_admin IN SCHEMA public GRANT ALL ON TABLES TO anon;
ALTER DEFAULT PRIVILEGES FOR ROLE supabase_admin IN SCHEMA public GRANT ALL ON TABLES TO authenticated;
ALTER DEFAULT PRIVILEGES FOR ROLE supabase_admin IN SCHEMA public GRANT ALL ON TABLES TO service_role;


--
-- PostgreSQL database dump complete
--



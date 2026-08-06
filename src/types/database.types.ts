// ============================================================
// Project "Relief" — Generated Supabase Database Types
// ============================================================
// GENERATED FILE — do not edit by hand.
//
// Source: the LIVE Supabase project, introspected from
// pg_catalog on 2026-08-06 (PostgreSQL 17.6).
//
// Regenerate with:
//   npm run gen:types      (requires SUPABASE_DB_URL)
//
// Note: `supabase gen types typescript` requires Docker. Where
// Docker is unavailable, tools/generate-database-types.mjs
// performs the same introspection over a direct connection and
// emits this file. Extension-owned objects (PostGIS) are
// excluded; geography/geometry columns are typed `unknown`
// because they are not consumed by the client.
// ============================================================

export type Json =
  | string
  | number
  | boolean
  | null
  | { [key: string]: Json | undefined }
  | Json[];

export type Database = {
  public: {
    Tables: {
      access_codes: {
        Row: {
          id: string;
          facility_id: string;
          user_id: string;
          code: string;
          description: string | null;
          is_verified: boolean | null;
          created_at: string;
          updated_at: string;
        };
        Insert: {
          id?: string;
          facility_id: string;
          user_id: string;
          code: string;
          description?: string | null;
          is_verified?: boolean | null;
          created_at?: string;
          updated_at?: string;
        };
        Update: {
          id?: string;
          facility_id?: string;
          user_id?: string;
          code?: string;
          description?: string | null;
          is_verified?: boolean | null;
          created_at?: string;
          updated_at?: string;
        };
        Relationships: [];
      };
      correction_requests: {
        Row: {
          id: string;
          facility_id: string;
          user_id: string;
          field: string;
          old_value: string;
          new_value: string;
          notes: string | null;
          status: string;
          created_at: string;
          reviewed_at: string | null;
          reviewed_by: string | null;
        };
        Insert: {
          id?: string;
          facility_id: string;
          user_id: string;
          field: string;
          old_value?: string;
          new_value: string;
          notes?: string | null;
          status?: string;
          created_at?: string;
          reviewed_at?: string | null;
          reviewed_by?: string | null;
        };
        Update: {
          id?: string;
          facility_id?: string;
          user_id?: string;
          field?: string;
          old_value?: string;
          new_value?: string;
          notes?: string | null;
          status?: string;
          created_at?: string;
          reviewed_at?: string | null;
          reviewed_by?: string | null;
        };
        Relationships: [];
      };
      facilities: {
        Row: {
          id: string;
          name: string;
          address: string | null;
          latitude: number;
          longitude: number;
          postcode: string | null;
          town: string;
          country: string;
          photos: string[] | null;
          open_hours: Json | null;
          is_free: boolean | null;
          price_note: string | null;
          access_notes: string | null;
          last_verified_at: string | null;
          is_accessible: boolean | null;
          is_disabled_access: boolean | null;
          has_baby_changing: boolean | null;
          has_family_room: boolean | null;
          is_gender_neutral: boolean | null;
          is_single_occupancy: boolean | null;
          is_24h: boolean | null;
          is_single_room: boolean | null;
          has_floor_to_ceiling_cubicles: boolean | null;
          is_quiet: boolean | null;
          has_wheelchair_access: boolean | null;
          requires_radar_key: boolean | null;
          has_adult_changing_place: boolean | null;
          has_lift: boolean | null;
          has_grab_rails: boolean | null;
          has_baby_changing_inside: boolean | null;
          has_separate_changing_room: boolean | null;
          has_family_toilet: boolean | null;
          has_pram_access: boolean | null;
          has_soap: boolean | null;
          has_paper_towels: boolean | null;
          has_hand_dryer: boolean | null;
          has_mirror: boolean | null;
          has_shelf: boolean | null;
          has_hooks: boolean | null;
          has_sanitary_bins: boolean | null;
          has_free_period_products: boolean | null;
          has_drinking_water: boolean | null;
          noise_level: number | null;
          temperature: number | null;
          lighting: number | null;
          smell: number | null;
          has_staff_nearby: boolean | null;
          has_cctv: boolean | null;
          is_women_friendly: boolean | null;
          is_family_friendly: boolean | null;
          is_picnic_area: boolean | null;
          overall_score: number | null;
          cleanliness_rating: number | null;
          privacy_rating: number | null;
          accessibility_rating: number | null;
          safety_rating: number | null;
          noise_rating: number | null;
          environment_rating: number | null;
          created_at: string | null;
          updated_at: string | null;
          created_by: string | null;
          is_verified: boolean | null;
          publication_status: string;
          verification_status: string;
          last_community_confirmed_at: string | null;
          last_staff_verified_at: string | null;
          location: unknown | null;
          field_provenance: Json | null;
        };
        Insert: {
          id?: string;
          name: string;
          address?: string | null;
          latitude: number;
          longitude: number;
          postcode?: string | null;
          town: string;
          country?: string;
          photos?: string[] | null;
          open_hours?: Json | null;
          is_free?: boolean | null;
          price_note?: string | null;
          access_notes?: string | null;
          last_verified_at?: string | null;
          is_accessible?: boolean | null;
          is_disabled_access?: boolean | null;
          has_baby_changing?: boolean | null;
          has_family_room?: boolean | null;
          is_gender_neutral?: boolean | null;
          is_single_occupancy?: boolean | null;
          is_24h?: boolean | null;
          is_single_room?: boolean | null;
          has_floor_to_ceiling_cubicles?: boolean | null;
          is_quiet?: boolean | null;
          has_wheelchair_access?: boolean | null;
          requires_radar_key?: boolean | null;
          has_adult_changing_place?: boolean | null;
          has_lift?: boolean | null;
          has_grab_rails?: boolean | null;
          has_baby_changing_inside?: boolean | null;
          has_separate_changing_room?: boolean | null;
          has_family_toilet?: boolean | null;
          has_pram_access?: boolean | null;
          has_soap?: boolean | null;
          has_paper_towels?: boolean | null;
          has_hand_dryer?: boolean | null;
          has_mirror?: boolean | null;
          has_shelf?: boolean | null;
          has_hooks?: boolean | null;
          has_sanitary_bins?: boolean | null;
          has_free_period_products?: boolean | null;
          has_drinking_water?: boolean | null;
          noise_level?: number | null;
          temperature?: number | null;
          lighting?: number | null;
          smell?: number | null;
          has_staff_nearby?: boolean | null;
          has_cctv?: boolean | null;
          is_women_friendly?: boolean | null;
          is_family_friendly?: boolean | null;
          is_picnic_area?: boolean | null;
          overall_score?: number | null;
          cleanliness_rating?: number | null;
          privacy_rating?: number | null;
          accessibility_rating?: number | null;
          safety_rating?: number | null;
          noise_rating?: number | null;
          environment_rating?: number | null;
          created_at?: string | null;
          updated_at?: string | null;
          created_by?: string | null;
          is_verified?: boolean | null;
          publication_status?: string;
          verification_status?: string;
          last_community_confirmed_at?: string | null;
          last_staff_verified_at?: string | null;
          field_provenance?: Json | null;
        };
        Update: {
          id?: string;
          name?: string;
          address?: string | null;
          latitude?: number;
          longitude?: number;
          postcode?: string | null;
          town?: string;
          country?: string;
          photos?: string[] | null;
          open_hours?: Json | null;
          is_free?: boolean | null;
          price_note?: string | null;
          access_notes?: string | null;
          last_verified_at?: string | null;
          is_accessible?: boolean | null;
          is_disabled_access?: boolean | null;
          has_baby_changing?: boolean | null;
          has_family_room?: boolean | null;
          is_gender_neutral?: boolean | null;
          is_single_occupancy?: boolean | null;
          is_24h?: boolean | null;
          is_single_room?: boolean | null;
          has_floor_to_ceiling_cubicles?: boolean | null;
          is_quiet?: boolean | null;
          has_wheelchair_access?: boolean | null;
          requires_radar_key?: boolean | null;
          has_adult_changing_place?: boolean | null;
          has_lift?: boolean | null;
          has_grab_rails?: boolean | null;
          has_baby_changing_inside?: boolean | null;
          has_separate_changing_room?: boolean | null;
          has_family_toilet?: boolean | null;
          has_pram_access?: boolean | null;
          has_soap?: boolean | null;
          has_paper_towels?: boolean | null;
          has_hand_dryer?: boolean | null;
          has_mirror?: boolean | null;
          has_shelf?: boolean | null;
          has_hooks?: boolean | null;
          has_sanitary_bins?: boolean | null;
          has_free_period_products?: boolean | null;
          has_drinking_water?: boolean | null;
          noise_level?: number | null;
          temperature?: number | null;
          lighting?: number | null;
          smell?: number | null;
          has_staff_nearby?: boolean | null;
          has_cctv?: boolean | null;
          is_women_friendly?: boolean | null;
          is_family_friendly?: boolean | null;
          is_picnic_area?: boolean | null;
          overall_score?: number | null;
          cleanliness_rating?: number | null;
          privacy_rating?: number | null;
          accessibility_rating?: number | null;
          safety_rating?: number | null;
          noise_rating?: number | null;
          environment_rating?: number | null;
          created_at?: string | null;
          updated_at?: string | null;
          created_by?: string | null;
          is_verified?: boolean | null;
          publication_status?: string;
          verification_status?: string;
          last_community_confirmed_at?: string | null;
          last_staff_verified_at?: string | null;
          field_provenance?: Json | null;
        };
        Relationships: [];
      };
      facility_reports: {
        Row: {
          id: string;
          facility_id: string;
          user_id: string;
          type: string;
          reason: string;
          notes: string | null;
          expires_at: string | null;
          created_at: string | null;
        };
        Insert: {
          id?: string;
          facility_id: string;
          user_id: string;
          type: string;
          reason: string;
          notes?: string | null;
          expires_at?: string | null;
          created_at?: string | null;
        };
        Update: {
          id?: string;
          facility_id?: string;
          user_id?: string;
          type?: string;
          reason?: string;
          notes?: string | null;
          expires_at?: string | null;
          created_at?: string | null;
        };
        Relationships: [];
      };
      facility_sources: {
        Row: {
          id: string;
          facility_id: string;
          import_run_id: string | null;
          source_name: string;
          source_record_id: string;
          source_url: string | null;
          source_licence: string;
          source_updated_at: string | null;
          first_seen_at: string;
          last_seen_at: string;
          is_current: boolean;
          raw_data: Json | null;
          created_at: string;
          updated_at: string;
        };
        Insert: {
          id?: string;
          facility_id: string;
          import_run_id?: string | null;
          source_name: string;
          source_record_id: string;
          source_url?: string | null;
          source_licence: string;
          source_updated_at?: string | null;
          first_seen_at?: string;
          last_seen_at?: string;
          is_current?: boolean;
          raw_data?: Json | null;
          created_at?: string;
          updated_at?: string;
        };
        Update: {
          id?: string;
          facility_id?: string;
          import_run_id?: string | null;
          source_name?: string;
          source_record_id?: string;
          source_url?: string | null;
          source_licence?: string;
          source_updated_at?: string | null;
          first_seen_at?: string;
          last_seen_at?: string;
          is_current?: boolean;
          raw_data?: Json | null;
          created_at?: string;
          updated_at?: string;
        };
        Relationships: [];
      };
      facility_submissions: {
        Row: {
          id: string;
          user_id: string;
          status: string;
          name: string;
          address: string;
          latitude: number;
          longitude: number;
          postcode: string;
          town: string;
          country: string;
          access_notes: string | null;
          is_free: boolean | null;
          price_note: string | null;
          open_hours: Json | null;
          photos: Json | null;
          is_accessible: boolean | null;
          is_disabled_access: boolean | null;
          has_baby_changing: boolean | null;
          has_family_room: boolean | null;
          is_gender_neutral: boolean | null;
          is_single_occupancy: boolean | null;
          is_24h: boolean | null;
          notes: string | null;
          access_codes: string | null;
          submission_notes: string | null;
          created_at: string;
          reviewed_at: string | null;
          reviewed_by: string | null;
          rejection_reason: string | null;
        };
        Insert: {
          id?: string;
          user_id: string;
          status?: string;
          name: string;
          address: string;
          latitude: number;
          longitude: number;
          postcode: string;
          town: string;
          country?: string;
          access_notes?: string | null;
          is_free?: boolean | null;
          price_note?: string | null;
          open_hours?: Json | null;
          photos?: Json | null;
          is_accessible?: boolean | null;
          is_disabled_access?: boolean | null;
          has_baby_changing?: boolean | null;
          has_family_room?: boolean | null;
          is_gender_neutral?: boolean | null;
          is_single_occupancy?: boolean | null;
          is_24h?: boolean | null;
          notes?: string | null;
          access_codes?: string | null;
          submission_notes?: string | null;
          created_at?: string;
          reviewed_at?: string | null;
          reviewed_by?: string | null;
          rejection_reason?: string | null;
        };
        Update: {
          id?: string;
          user_id?: string;
          status?: string;
          name?: string;
          address?: string;
          latitude?: number;
          longitude?: number;
          postcode?: string;
          town?: string;
          country?: string;
          access_notes?: string | null;
          is_free?: boolean | null;
          price_note?: string | null;
          open_hours?: Json | null;
          photos?: Json | null;
          is_accessible?: boolean | null;
          is_disabled_access?: boolean | null;
          has_baby_changing?: boolean | null;
          has_family_room?: boolean | null;
          is_gender_neutral?: boolean | null;
          is_single_occupancy?: boolean | null;
          is_24h?: boolean | null;
          notes?: string | null;
          access_codes?: string | null;
          submission_notes?: string | null;
          created_at?: string;
          reviewed_at?: string | null;
          reviewed_by?: string | null;
          rejection_reason?: string | null;
        };
        Relationships: [];
      };
      favourites: {
        Row: {
          id: string;
          user_id: string;
          facility_id: string;
          created_at: string | null;
        };
        Insert: {
          id?: string;
          user_id: string;
          facility_id: string;
          created_at?: string | null;
        };
        Update: {
          id?: string;
          user_id?: string;
          facility_id?: string;
          created_at?: string | null;
        };
        Relationships: [];
      };
      import_runs: {
        Row: {
          id: string;
          source_name: string;
          source_file_name: string | null;
          source_checksum: string | null;
          status: string;
          started_at: string;
          completed_at: string | null;
          rows_received: number;
          rows_valid: number;
          rows_inserted: number;
          rows_updated: number;
          rows_unchanged: number;
          rows_quarantined: number;
          rows_marked_stale: number;
          error_summary: string | null;
        };
        Insert: {
          id?: string;
          source_name: string;
          source_file_name?: string | null;
          source_checksum?: string | null;
          status?: string;
          started_at?: string;
          completed_at?: string | null;
          rows_received?: number;
          rows_valid?: number;
          rows_inserted?: number;
          rows_updated?: number;
          rows_unchanged?: number;
          rows_quarantined?: number;
          rows_marked_stale?: number;
          error_summary?: string | null;
        };
        Update: {
          id?: string;
          source_name?: string;
          source_file_name?: string | null;
          source_checksum?: string | null;
          status?: string;
          started_at?: string;
          completed_at?: string | null;
          rows_received?: number;
          rows_valid?: number;
          rows_inserted?: number;
          rows_updated?: number;
          rows_unchanged?: number;
          rows_quarantined?: number;
          rows_marked_stale?: number;
          error_summary?: string | null;
        };
        Relationships: [];
      };
      photo_moderation: {
        Row: {
          id: string;
          facility_id: string;
          user_id: string;
          url: string;
          thumbnail_url: string;
          status: string;
          exif_stripped: boolean | null;
          faces_blurred: boolean | null;
          reported_by: string | null;
          report_reason: string | null;
          created_at: string;
        };
        Insert: {
          id?: string;
          facility_id: string;
          user_id: string;
          url: string;
          thumbnail_url: string;
          status?: string;
          exif_stripped?: boolean | null;
          faces_blurred?: boolean | null;
          reported_by?: string | null;
          report_reason?: string | null;
          created_at?: string;
        };
        Update: {
          id?: string;
          facility_id?: string;
          user_id?: string;
          url?: string;
          thumbnail_url?: string;
          status?: string;
          exif_stripped?: boolean | null;
          faces_blurred?: boolean | null;
          reported_by?: string | null;
          report_reason?: string | null;
          created_at?: string;
        };
        Relationships: [];
      };
      rate_limits: {
        Row: {
          id: string;
          user_id: string;
          action: string;
          timestamp: string;
        };
        Insert: {
          id?: string;
          user_id: string;
          action: string;
          timestamp?: string;
        };
        Update: {
          id?: string;
          user_id?: string;
          action?: string;
          timestamp?: string;
        };
        Relationships: [];
      };
      review_reports: {
        Row: {
          id: string;
          review_id: string;
          user_id: string;
          reason: string;
          created_at: string;
        };
        Insert: {
          id?: string;
          review_id: string;
          user_id: string;
          reason: string;
          created_at?: string;
        };
        Update: {
          id?: string;
          review_id?: string;
          user_id?: string;
          reason?: string;
          created_at?: string;
        };
        Relationships: [];
      };
      saved_profiles: {
        Row: {
          id: string;
          user_id: string;
          mode: string;
          name: string;
          preferences: Json;
          created_at: string | null;
        };
        Insert: {
          id?: string;
          user_id: string;
          mode: string;
          name: string;
          preferences?: Json;
          created_at?: string | null;
        };
        Update: {
          id?: string;
          user_id?: string;
          mode?: string;
          name?: string;
          preferences?: Json;
          created_at?: string | null;
        };
        Relationships: [];
      };
      subscription_events: {
        Row: {
          id: string;
          user_id: string;
          event_type: string;
          tier: string;
          previous_tier: string | null;
          details: Json | null;
          revenuecat_event_id: string | null;
          created_at: string;
        };
        Insert: {
          id?: string;
          user_id: string;
          event_type: string;
          tier: string;
          previous_tier?: string | null;
          details?: Json | null;
          revenuecat_event_id?: string | null;
          created_at?: string;
        };
        Update: {
          id?: string;
          user_id?: string;
          event_type?: string;
          tier?: string;
          previous_tier?: string | null;
          details?: Json | null;
          revenuecat_event_id?: string | null;
          created_at?: string;
        };
        Relationships: [];
      };
      temporary_reports: {
        Row: {
          id: string;
          facility_id: string;
          user_id: string;
          type: string;
          notes: string | null;
          expires_at: string;
          is_expired: boolean | null;
          created_at: string;
        };
        Insert: {
          id?: string;
          facility_id: string;
          user_id: string;
          type: string;
          notes?: string | null;
          expires_at: string;
          is_expired?: boolean | null;
          created_at?: string;
        };
        Update: {
          id?: string;
          facility_id?: string;
          user_id?: string;
          type?: string;
          notes?: string | null;
          expires_at?: string;
          is_expired?: boolean | null;
          created_at?: string;
        };
        Relationships: [];
      };
      toilet_map_import_staging: {
        Row: {
          import_run_id: string;
          source_record_id: string;
          name: string | null;
          latitude: number | null;
          longitude: number | null;
          address: string | null;
          postcode: string | null;
          town: string | null;
          is_accessible: boolean | null;
          has_baby_changing: boolean | null;
          requires_radar_key: boolean | null;
          is_free: boolean | null;
          opening_hours: Json | null;
          source_updated_at: string | null;
          raw_data: Json | null;
          validation_errors: string[] | null;
        };
        Insert: {
          import_run_id: string;
          source_record_id: string;
          name?: string | null;
          latitude?: number | null;
          longitude?: number | null;
          address?: string | null;
          postcode?: string | null;
          town?: string | null;
          is_accessible?: boolean | null;
          has_baby_changing?: boolean | null;
          requires_radar_key?: boolean | null;
          is_free?: boolean | null;
          opening_hours?: Json | null;
          source_updated_at?: string | null;
          raw_data?: Json | null;
          validation_errors?: string[] | null;
        };
        Update: {
          import_run_id?: string;
          source_record_id?: string;
          name?: string | null;
          latitude?: number | null;
          longitude?: number | null;
          address?: string | null;
          postcode?: string | null;
          town?: string | null;
          is_accessible?: boolean | null;
          has_baby_changing?: boolean | null;
          requires_radar_key?: boolean | null;
          is_free?: boolean | null;
          opening_hours?: Json | null;
          source_updated_at?: string | null;
          raw_data?: Json | null;
          validation_errors?: string[] | null;
        };
        Relationships: [];
      };
      user_badges: {
        Row: {
          id: string;
          user_id: string;
          badge_type: string;
          awarded_at: string | null;
        };
        Insert: {
          id?: string;
          user_id: string;
          badge_type: string;
          awarded_at?: string | null;
        };
        Update: {
          id?: string;
          user_id?: string;
          badge_type?: string;
          awarded_at?: string | null;
        };
        Relationships: [];
      };
      user_profiles: {
        Row: {
          id: string;
          email: string | null;
          display_name: string | null;
          avatar_url: string | null;
          created_at: string | null;
          has_lifetime_access: boolean | null;
          subscription_tier: string | null;
          subscription_expires_at: string | null;
        };
        Insert: {
          id: string;
          email?: string | null;
          display_name?: string | null;
          avatar_url?: string | null;
          created_at?: string | null;
          has_lifetime_access?: boolean | null;
          subscription_tier?: string | null;
          subscription_expires_at?: string | null;
        };
        Update: {
          id?: string;
          email?: string | null;
          display_name?: string | null;
          avatar_url?: string | null;
          created_at?: string | null;
          has_lifetime_access?: boolean | null;
          subscription_tier?: string | null;
          subscription_expires_at?: string | null;
        };
        Relationships: [];
      };
      user_subscriptions: {
        Row: {
          id: string;
          user_id: string;
          revenuecat_id: string | null;
          tier: string;
          is_active: boolean;
          lifetime_purchase_at: string | null;
          plus_monthly_purchase_at: string | null;
          plus_yearly_purchase_at: string | null;
          current_period_start: string | null;
          current_period_end: string | null;
          will_renew: boolean;
          is_grace_period: boolean;
          cancellation_at: string | null;
          cancelled_at: string | null;
          refunded_at: string | null;
          raw_revenuecat_json: Json | null;
          created_at: string;
          updated_at: string;
        };
        Insert: {
          id?: string;
          user_id: string;
          revenuecat_id?: string | null;
          tier?: string;
          is_active?: boolean;
          lifetime_purchase_at?: string | null;
          plus_monthly_purchase_at?: string | null;
          plus_yearly_purchase_at?: string | null;
          current_period_start?: string | null;
          current_period_end?: string | null;
          will_renew?: boolean;
          is_grace_period?: boolean;
          cancellation_at?: string | null;
          cancelled_at?: string | null;
          refunded_at?: string | null;
          raw_revenuecat_json?: Json | null;
          created_at?: string;
          updated_at?: string;
        };
        Update: {
          id?: string;
          user_id?: string;
          revenuecat_id?: string | null;
          tier?: string;
          is_active?: boolean;
          lifetime_purchase_at?: string | null;
          plus_monthly_purchase_at?: string | null;
          plus_yearly_purchase_at?: string | null;
          current_period_start?: string | null;
          current_period_end?: string | null;
          will_renew?: boolean;
          is_grace_period?: boolean;
          cancellation_at?: string | null;
          cancelled_at?: string | null;
          refunded_at?: string | null;
          raw_revenuecat_json?: Json | null;
          created_at?: string;
          updated_at?: string;
        };
        Relationships: [];
      };
    };
    Views: {
      [_ in never]: never;
    };
    Functions: {
      expire_temporary_reports: {
        Args: { [_ in never]: never };
        Returns: undefined;
      };
      find_nearest_facilities: {
        Args: {
          user_latitude: number;
          user_longitude: number;
          search_radius_metres?: number;
          result_limit?: number;
        };
        Returns: {
            facility_id: string | null;
            name: string | null;
            address: string | null;
            latitude: number | null;
            longitude: number | null;
            town: string | null;
            postcode: string | null;
            open_hours: Json | null;
            is_free: boolean | null;
            is_accessible: boolean | null;
            overall_score: number | null;
            verification_status: string | null;
            distance_metres: number | null;
        }[];
      };
      handle_new_user: {
        Args: { [_ in never]: never };
        Returns: unknown;
      };
      rls_auto_enable: {
        Args: { [_ in never]: never };
        Returns: unknown;
      };
      sync_subscription_from_revenuecat: {
        Args: {
          p_user_id: string;
          p_tier: string;
          p_is_active: boolean;
          p_lifetime_purchase_at: string;
          p_current_period_start: string;
          p_current_period_end: string;
          p_will_renew: boolean;
          p_is_grace_period: boolean;
          p_cancellation_at: string;
          p_cancelled_at: string;
          p_refunded_at: string;
          p_raw_json: Json;
          p_event_type: string;
          p_previous_tier?: string;
        };
        Returns: undefined;
      };
      update_updated_at: {
        Args: { [_ in never]: never };
        Returns: unknown;
      };
    };
    Enums: {
      [_ in never]: never;
    };
    CompositeTypes: {
      [_ in never]: never;
    };
  };
};

// ── Convenience aliases ─────────────────────────────────────
export type Tables<T extends keyof Database['public']['Tables']> =
  Database['public']['Tables'][T]['Row'];
export type TablesInsert<T extends keyof Database['public']['Tables']> =
  Database['public']['Tables'][T]['Insert'];
export type TablesUpdate<T extends keyof Database['public']['Tables']> =
  Database['public']['Tables'][T]['Update'];
export type Functions<T extends keyof Database['public']['Functions']> =
  Database['public']['Functions'][T];

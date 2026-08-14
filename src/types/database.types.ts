export type Json =
  | string
  | number
  | boolean
  | null
  | { [key: string]: Json | undefined }
  | Json[]

export type Database = {
  // Allows to automatically instantiate createClient with right options
  // instead of createClient<Database, { PostgrestVersion: 'XX' }>(URL, KEY)
  __InternalSupabase: {
    PostgrestVersion: "14.5"
  }
  public: {
    Tables: {
      access_codes: {
        Row: {
          code: string
          created_at: string
          description: string | null
          facility_id: string
          id: string
          is_verified: boolean | null
          updated_at: string
          user_id: string
        }
        Insert: {
          code: string
          created_at?: string
          description?: string | null
          facility_id: string
          id?: string
          is_verified?: boolean | null
          updated_at?: string
          user_id: string
        }
        Update: {
          code?: string
          created_at?: string
          description?: string | null
          facility_id?: string
          id?: string
          is_verified?: boolean | null
          updated_at?: string
          user_id?: string
        }
        Relationships: [
          {
            foreignKeyName: "access_codes_facility_id_fkey"
            columns: ["facility_id"]
            isOneToOne: false
            referencedRelation: "facilities"
            referencedColumns: ["id"]
          },
        ]
      }
      correction_requests: {
        Row: {
          created_at: string
          facility_id: string
          field: string
          id: string
          new_value: string
          notes: string | null
          old_value: string
          reviewed_at: string | null
          reviewed_by: string | null
          status: string
          user_id: string
        }
        Insert: {
          created_at?: string
          facility_id: string
          field: string
          id?: string
          new_value: string
          notes?: string | null
          old_value?: string
          reviewed_at?: string | null
          reviewed_by?: string | null
          status?: string
          user_id: string
        }
        Update: {
          created_at?: string
          facility_id?: string
          field?: string
          id?: string
          new_value?: string
          notes?: string | null
          old_value?: string
          reviewed_at?: string | null
          reviewed_by?: string | null
          status?: string
          user_id?: string
        }
        Relationships: [
          {
            foreignKeyName: "correction_requests_facility_id_fkey"
            columns: ["facility_id"]
            isOneToOne: false
            referencedRelation: "facilities"
            referencedColumns: ["id"]
          },
        ]
      }
      facilities: {
        Row: {
          access_notes: string | null
          accessibility_rating: number | null
          address: string | null
          cleanliness_rating: number | null
          country: string
          created_at: string | null
          created_by: string | null
          environment_rating: number | null
          field_provenance: Json | null
          has_adult_changing_place: boolean | null
          has_baby_changing: boolean | null
          has_baby_changing_inside: boolean | null
          has_cctv: boolean | null
          has_drinking_water: boolean | null
          has_family_room: boolean | null
          has_family_toilet: boolean | null
          has_floor_to_ceiling_cubicles: boolean | null
          has_free_period_products: boolean | null
          has_grab_rails: boolean | null
          has_hand_dryer: boolean | null
          has_hooks: boolean | null
          has_lift: boolean | null
          has_mirror: boolean | null
          has_paper_towels: boolean | null
          has_pram_access: boolean | null
          has_sanitary_bins: boolean | null
          has_separate_changing_room: boolean | null
          has_shelf: boolean | null
          has_soap: boolean | null
          has_staff_nearby: boolean | null
          has_wheelchair_access: boolean | null
          id: string
          is_24h: boolean | null
          is_accessible: boolean | null
          is_disabled_access: boolean | null
          is_family_friendly: boolean | null
          is_free: boolean | null
          is_gender_neutral: boolean | null
          is_picnic_area: boolean | null
          is_quiet: boolean | null
          is_single_occupancy: boolean | null
          is_single_room: boolean | null
          is_verified: boolean | null
          is_women_friendly: boolean | null
          last_community_confirmed_at: string | null
          last_staff_verified_at: string | null
          last_verified_at: string | null
          latitude: number
          lighting: number | null
          location: unknown
          longitude: number
          name: string
          noise_level: number | null
          noise_rating: number | null
          open_hours: Json | null
          overall_score: number | null
          photos: string[] | null
          postcode: string | null
          price_note: string | null
          privacy_rating: number | null
          publication_status: string
          requires_radar_key: boolean | null
          safety_rating: number | null
          smell: number | null
          temperature: number | null
          town: string
          updated_at: string | null
          verification_status: string
        }
        Insert: {
          access_notes?: string | null
          accessibility_rating?: number | null
          address?: string | null
          cleanliness_rating?: number | null
          country?: string
          created_at?: string | null
          created_by?: string | null
          environment_rating?: number | null
          field_provenance?: Json | null
          has_adult_changing_place?: boolean | null
          has_baby_changing?: boolean | null
          has_baby_changing_inside?: boolean | null
          has_cctv?: boolean | null
          has_drinking_water?: boolean | null
          has_family_room?: boolean | null
          has_family_toilet?: boolean | null
          has_floor_to_ceiling_cubicles?: boolean | null
          has_free_period_products?: boolean | null
          has_grab_rails?: boolean | null
          has_hand_dryer?: boolean | null
          has_hooks?: boolean | null
          has_lift?: boolean | null
          has_mirror?: boolean | null
          has_paper_towels?: boolean | null
          has_pram_access?: boolean | null
          has_sanitary_bins?: boolean | null
          has_separate_changing_room?: boolean | null
          has_shelf?: boolean | null
          has_soap?: boolean | null
          has_staff_nearby?: boolean | null
          has_wheelchair_access?: boolean | null
          id?: string
          is_24h?: boolean | null
          is_accessible?: boolean | null
          is_disabled_access?: boolean | null
          is_family_friendly?: boolean | null
          is_free?: boolean | null
          is_gender_neutral?: boolean | null
          is_picnic_area?: boolean | null
          is_quiet?: boolean | null
          is_single_occupancy?: boolean | null
          is_single_room?: boolean | null
          is_verified?: boolean | null
          is_women_friendly?: boolean | null
          last_community_confirmed_at?: string | null
          last_staff_verified_at?: string | null
          last_verified_at?: string | null
          latitude: number
          lighting?: number | null
          location?: unknown
          longitude: number
          name: string
          noise_level?: number | null
          noise_rating?: number | null
          open_hours?: Json | null
          overall_score?: number | null
          photos?: string[] | null
          postcode?: string | null
          price_note?: string | null
          privacy_rating?: number | null
          publication_status?: string
          requires_radar_key?: boolean | null
          safety_rating?: number | null
          smell?: number | null
          temperature?: number | null
          town: string
          updated_at?: string | null
          verification_status?: string
        }
        Update: {
          access_notes?: string | null
          accessibility_rating?: number | null
          address?: string | null
          cleanliness_rating?: number | null
          country?: string
          created_at?: string | null
          created_by?: string | null
          environment_rating?: number | null
          field_provenance?: Json | null
          has_adult_changing_place?: boolean | null
          has_baby_changing?: boolean | null
          has_baby_changing_inside?: boolean | null
          has_cctv?: boolean | null
          has_drinking_water?: boolean | null
          has_family_room?: boolean | null
          has_family_toilet?: boolean | null
          has_floor_to_ceiling_cubicles?: boolean | null
          has_free_period_products?: boolean | null
          has_grab_rails?: boolean | null
          has_hand_dryer?: boolean | null
          has_hooks?: boolean | null
          has_lift?: boolean | null
          has_mirror?: boolean | null
          has_paper_towels?: boolean | null
          has_pram_access?: boolean | null
          has_sanitary_bins?: boolean | null
          has_separate_changing_room?: boolean | null
          has_shelf?: boolean | null
          has_soap?: boolean | null
          has_staff_nearby?: boolean | null
          has_wheelchair_access?: boolean | null
          id?: string
          is_24h?: boolean | null
          is_accessible?: boolean | null
          is_disabled_access?: boolean | null
          is_family_friendly?: boolean | null
          is_free?: boolean | null
          is_gender_neutral?: boolean | null
          is_picnic_area?: boolean | null
          is_quiet?: boolean | null
          is_single_occupancy?: boolean | null
          is_single_room?: boolean | null
          is_verified?: boolean | null
          is_women_friendly?: boolean | null
          last_community_confirmed_at?: string | null
          last_staff_verified_at?: string | null
          last_verified_at?: string | null
          latitude?: number
          lighting?: number | null
          location?: unknown
          longitude?: number
          name?: string
          noise_level?: number | null
          noise_rating?: number | null
          open_hours?: Json | null
          overall_score?: number | null
          photos?: string[] | null
          postcode?: string | null
          price_note?: string | null
          privacy_rating?: number | null
          publication_status?: string
          requires_radar_key?: boolean | null
          safety_rating?: number | null
          smell?: number | null
          temperature?: number | null
          town?: string
          updated_at?: string | null
          verification_status?: string
        }
        Relationships: []
      }
      facility_reports: {
        Row: {
          created_at: string | null
          expires_at: string | null
          facility_id: string
          id: string
          notes: string | null
          reason: string
          type: string
          user_id: string
        }
        Insert: {
          created_at?: string | null
          expires_at?: string | null
          facility_id: string
          id?: string
          notes?: string | null
          reason: string
          type: string
          user_id: string
        }
        Update: {
          created_at?: string | null
          expires_at?: string | null
          facility_id?: string
          id?: string
          notes?: string | null
          reason?: string
          type?: string
          user_id?: string
        }
        Relationships: [
          {
            foreignKeyName: "facility_reports_facility_id_fkey"
            columns: ["facility_id"]
            isOneToOne: false
            referencedRelation: "facilities"
            referencedColumns: ["id"]
          },
        ]
      }
      facility_sources: {
        Row: {
          created_at: string
          facility_id: string
          first_seen_at: string
          id: string
          import_run_id: string | null
          is_current: boolean
          last_seen_at: string
          raw_data: Json | null
          source_licence: string
          source_name: string
          source_record_id: string
          source_updated_at: string | null
          source_url: string | null
          updated_at: string
        }
        Insert: {
          created_at?: string
          facility_id: string
          first_seen_at?: string
          id?: string
          import_run_id?: string | null
          is_current?: boolean
          last_seen_at?: string
          raw_data?: Json | null
          source_licence: string
          source_name: string
          source_record_id: string
          source_updated_at?: string | null
          source_url?: string | null
          updated_at?: string
        }
        Update: {
          created_at?: string
          facility_id?: string
          first_seen_at?: string
          id?: string
          import_run_id?: string | null
          is_current?: boolean
          last_seen_at?: string
          raw_data?: Json | null
          source_licence?: string
          source_name?: string
          source_record_id?: string
          source_updated_at?: string | null
          source_url?: string | null
          updated_at?: string
        }
        Relationships: [
          {
            foreignKeyName: "facility_sources_facility_id_fkey"
            columns: ["facility_id"]
            isOneToOne: false
            referencedRelation: "facilities"
            referencedColumns: ["id"]
          },
          {
            foreignKeyName: "facility_sources_import_run_id_fkey"
            columns: ["import_run_id"]
            isOneToOne: false
            referencedRelation: "import_runs"
            referencedColumns: ["id"]
          },
        ]
      }
      facility_submissions: {
        Row: {
          access_codes: string | null
          access_notes: string | null
          address: string
          country: string
          created_at: string
          has_baby_changing: boolean | null
          has_family_room: boolean | null
          id: string
          is_24h: boolean | null
          is_accessible: boolean | null
          is_disabled_access: boolean | null
          is_free: boolean | null
          is_gender_neutral: boolean | null
          is_single_occupancy: boolean | null
          latitude: number
          longitude: number
          name: string
          notes: string | null
          open_hours: Json | null
          photos: Json | null
          postcode: string
          price_note: string | null
          rejection_reason: string | null
          reviewed_at: string | null
          reviewed_by: string | null
          status: string
          submission_notes: string | null
          town: string
          user_id: string
        }
        Insert: {
          access_codes?: string | null
          access_notes?: string | null
          address: string
          country?: string
          created_at?: string
          has_baby_changing?: boolean | null
          has_family_room?: boolean | null
          id?: string
          is_24h?: boolean | null
          is_accessible?: boolean | null
          is_disabled_access?: boolean | null
          is_free?: boolean | null
          is_gender_neutral?: boolean | null
          is_single_occupancy?: boolean | null
          latitude: number
          longitude: number
          name: string
          notes?: string | null
          open_hours?: Json | null
          photos?: Json | null
          postcode: string
          price_note?: string | null
          rejection_reason?: string | null
          reviewed_at?: string | null
          reviewed_by?: string | null
          status?: string
          submission_notes?: string | null
          town: string
          user_id: string
        }
        Update: {
          access_codes?: string | null
          access_notes?: string | null
          address?: string
          country?: string
          created_at?: string
          has_baby_changing?: boolean | null
          has_family_room?: boolean | null
          id?: string
          is_24h?: boolean | null
          is_accessible?: boolean | null
          is_disabled_access?: boolean | null
          is_free?: boolean | null
          is_gender_neutral?: boolean | null
          is_single_occupancy?: boolean | null
          latitude?: number
          longitude?: number
          name?: string
          notes?: string | null
          open_hours?: Json | null
          photos?: Json | null
          postcode?: string
          price_note?: string | null
          rejection_reason?: string | null
          reviewed_at?: string | null
          reviewed_by?: string | null
          status?: string
          submission_notes?: string | null
          town?: string
          user_id?: string
        }
        Relationships: []
      }
      favourites: {
        Row: {
          created_at: string | null
          facility_id: string
          id: string
          user_id: string
        }
        Insert: {
          created_at?: string | null
          facility_id: string
          id?: string
          user_id: string
        }
        Update: {
          created_at?: string | null
          facility_id?: string
          id?: string
          user_id?: string
        }
        Relationships: [
          {
            foreignKeyName: "favourites_facility_id_fkey"
            columns: ["facility_id"]
            isOneToOne: false
            referencedRelation: "facilities"
            referencedColumns: ["id"]
          },
        ]
      }
      import_runs: {
        Row: {
          applied_count: number
          apply_engine_version: string | null
          approved_manifest_sha256: string | null
          approved_plan_sha256: string | null
          approved_review_commit: string | null
          completed_at: string | null
          error_summary: string | null
          failed_count: number
          id: string
          project_ref: string | null
          ready_count: number
          requested_operation_count: number
          rollback_summary: string | null
          rows_inserted: number
          rows_marked_stale: number
          rows_quarantined: number
          rows_received: number
          rows_unchanged: number
          rows_updated: number
          rows_valid: number
          run_kind: string
          source_checksum: string | null
          source_file_name: string | null
          source_name: string
          stale_count: number
          started_at: string
          status: string
          transaction_outcome: string
        }
        Insert: {
          applied_count?: number
          apply_engine_version?: string | null
          approved_manifest_sha256?: string | null
          approved_plan_sha256?: string | null
          approved_review_commit?: string | null
          completed_at?: string | null
          error_summary?: string | null
          failed_count?: number
          id?: string
          project_ref?: string | null
          ready_count?: number
          requested_operation_count?: number
          rollback_summary?: string | null
          rows_inserted?: number
          rows_marked_stale?: number
          rows_quarantined?: number
          rows_received?: number
          rows_unchanged?: number
          rows_updated?: number
          rows_valid?: number
          run_kind?: string
          source_checksum?: string | null
          source_file_name?: string | null
          source_name: string
          stale_count?: number
          started_at?: string
          status?: string
          transaction_outcome?: string
        }
        Update: {
          applied_count?: number
          apply_engine_version?: string | null
          approved_manifest_sha256?: string | null
          approved_plan_sha256?: string | null
          approved_review_commit?: string | null
          completed_at?: string | null
          error_summary?: string | null
          failed_count?: number
          id?: string
          project_ref?: string | null
          ready_count?: number
          requested_operation_count?: number
          rollback_summary?: string | null
          rows_inserted?: number
          rows_marked_stale?: number
          rows_quarantined?: number
          rows_received?: number
          rows_unchanged?: number
          rows_updated?: number
          rows_valid?: number
          run_kind?: string
          source_checksum?: string | null
          source_file_name?: string | null
          source_name?: string
          stale_count?: number
          started_at?: string
          status?: string
          transaction_outcome?: string
        }
        Relationships: []
      }
      photo_moderation: {
        Row: {
          created_at: string
          exif_stripped: boolean | null
          faces_blurred: boolean | null
          facility_id: string
          id: string
          report_reason: string | null
          reported_by: string | null
          status: string
          thumbnail_url: string
          url: string
          user_id: string
        }
        Insert: {
          created_at?: string
          exif_stripped?: boolean | null
          faces_blurred?: boolean | null
          facility_id: string
          id?: string
          report_reason?: string | null
          reported_by?: string | null
          status?: string
          thumbnail_url: string
          url: string
          user_id: string
        }
        Update: {
          created_at?: string
          exif_stripped?: boolean | null
          faces_blurred?: boolean | null
          facility_id?: string
          id?: string
          report_reason?: string | null
          reported_by?: string | null
          status?: string
          thumbnail_url?: string
          url?: string
          user_id?: string
        }
        Relationships: [
          {
            foreignKeyName: "photo_moderation_facility_id_fkey"
            columns: ["facility_id"]
            isOneToOne: false
            referencedRelation: "facilities"
            referencedColumns: ["id"]
          },
        ]
      }
      rate_limits: {
        Row: {
          action: string
          id: string
          timestamp: string
          user_id: string
        }
        Insert: {
          action: string
          id?: string
          timestamp?: string
          user_id: string
        }
        Update: {
          action?: string
          id?: string
          timestamp?: string
          user_id?: string
        }
        Relationships: []
      }
      review_reports: {
        Row: {
          created_at: string
          id: string
          reason: string
          review_id: string
          user_id: string
        }
        Insert: {
          created_at?: string
          id?: string
          reason: string
          review_id: string
          user_id: string
        }
        Update: {
          created_at?: string
          id?: string
          reason?: string
          review_id?: string
          user_id?: string
        }
        Relationships: []
      }
      saved_profiles: {
        Row: {
          created_at: string | null
          id: string
          mode: string
          name: string
          preferences: Json
          user_id: string
        }
        Insert: {
          created_at?: string | null
          id?: string
          mode: string
          name: string
          preferences?: Json
          user_id: string
        }
        Update: {
          created_at?: string | null
          id?: string
          mode?: string
          name?: string
          preferences?: Json
          user_id?: string
        }
        Relationships: []
      }
      spatial_ref_sys: {
        Row: {
          auth_name: string | null
          auth_srid: number | null
          proj4text: string | null
          srid: number
          srtext: string | null
        }
        Insert: {
          auth_name?: string | null
          auth_srid?: number | null
          proj4text?: string | null
          srid: number
          srtext?: string | null
        }
        Update: {
          auth_name?: string | null
          auth_srid?: number | null
          proj4text?: string | null
          srid?: number
          srtext?: string | null
        }
        Relationships: []
      }
      subscription_events: {
        Row: {
          created_at: string
          details: Json | null
          event_type: string
          id: string
          previous_tier: string | null
          revenuecat_event_id: string | null
          tier: string
          user_id: string
        }
        Insert: {
          created_at?: string
          details?: Json | null
          event_type: string
          id?: string
          previous_tier?: string | null
          revenuecat_event_id?: string | null
          tier: string
          user_id: string
        }
        Update: {
          created_at?: string
          details?: Json | null
          event_type?: string
          id?: string
          previous_tier?: string | null
          revenuecat_event_id?: string | null
          tier?: string
          user_id?: string
        }
        Relationships: []
      }
      temporary_reports: {
        Row: {
          created_at: string
          expires_at: string
          facility_id: string
          id: string
          is_expired: boolean | null
          notes: string | null
          type: string
          user_id: string
        }
        Insert: {
          created_at?: string
          expires_at: string
          facility_id: string
          id?: string
          is_expired?: boolean | null
          notes?: string | null
          type: string
          user_id: string
        }
        Update: {
          created_at?: string
          expires_at?: string
          facility_id?: string
          id?: string
          is_expired?: boolean | null
          notes?: string | null
          type?: string
          user_id?: string
        }
        Relationships: [
          {
            foreignKeyName: "temporary_reports_facility_id_fkey"
            columns: ["facility_id"]
            isOneToOne: false
            referencedRelation: "facilities"
            referencedColumns: ["id"]
          },
        ]
      }
      toilet_map_import_staging: {
        Row: {
          address: string | null
          has_baby_changing: boolean | null
          import_run_id: string
          is_accessible: boolean | null
          is_free: boolean | null
          latitude: number | null
          longitude: number | null
          name: string | null
          opening_hours: Json | null
          postcode: string | null
          raw_data: Json | null
          requires_radar_key: boolean | null
          source_record_id: string
          source_updated_at: string | null
          town: string | null
          validation_errors: string[] | null
        }
        Insert: {
          address?: string | null
          has_baby_changing?: boolean | null
          import_run_id: string
          is_accessible?: boolean | null
          is_free?: boolean | null
          latitude?: number | null
          longitude?: number | null
          name?: string | null
          opening_hours?: Json | null
          postcode?: string | null
          raw_data?: Json | null
          requires_radar_key?: boolean | null
          source_record_id: string
          source_updated_at?: string | null
          town?: string | null
          validation_errors?: string[] | null
        }
        Update: {
          address?: string | null
          has_baby_changing?: boolean | null
          import_run_id?: string
          is_accessible?: boolean | null
          is_free?: boolean | null
          latitude?: number | null
          longitude?: number | null
          name?: string | null
          opening_hours?: Json | null
          postcode?: string | null
          raw_data?: Json | null
          requires_radar_key?: boolean | null
          source_record_id?: string
          source_updated_at?: string | null
          town?: string | null
          validation_errors?: string[] | null
        }
        Relationships: [
          {
            foreignKeyName: "toilet_map_import_staging_import_run_id_fkey"
            columns: ["import_run_id"]
            isOneToOne: false
            referencedRelation: "import_runs"
            referencedColumns: ["id"]
          },
        ]
      }
      user_badges: {
        Row: {
          awarded_at: string | null
          badge_type: string
          id: string
          source: string
          user_id: string
        }
        Insert: {
          awarded_at?: string | null
          badge_type: string
          id?: string
          source?: string
          user_id: string
        }
        Update: {
          awarded_at?: string | null
          badge_type?: string
          id?: string
          source?: string
          user_id?: string
        }
        Relationships: []
      }
      user_profiles: {
        Row: {
          avatar_url: string | null
          created_at: string | null
          display_name: string | null
          email: string | null
          has_lifetime_access: boolean | null
          id: string
          subscription_expires_at: string | null
          subscription_tier: string | null
        }
        Insert: {
          avatar_url?: string | null
          created_at?: string | null
          display_name?: string | null
          email?: string | null
          has_lifetime_access?: boolean | null
          id: string
          subscription_expires_at?: string | null
          subscription_tier?: string | null
        }
        Update: {
          avatar_url?: string | null
          created_at?: string | null
          display_name?: string | null
          email?: string | null
          has_lifetime_access?: boolean | null
          id?: string
          subscription_expires_at?: string | null
          subscription_tier?: string | null
        }
        Relationships: []
      }
      user_subscriptions: {
        Row: {
          cancellation_at: string | null
          cancelled_at: string | null
          created_at: string
          current_period_end: string | null
          current_period_start: string | null
          id: string
          is_active: boolean
          is_grace_period: boolean
          lifetime_purchase_at: string | null
          plus_monthly_purchase_at: string | null
          plus_yearly_purchase_at: string | null
          raw_revenuecat_json: Json | null
          refunded_at: string | null
          revenuecat_id: string | null
          tier: string
          updated_at: string
          user_id: string
          will_renew: boolean
        }
        Insert: {
          cancellation_at?: string | null
          cancelled_at?: string | null
          created_at?: string
          current_period_end?: string | null
          current_period_start?: string | null
          id?: string
          is_active?: boolean
          is_grace_period?: boolean
          lifetime_purchase_at?: string | null
          plus_monthly_purchase_at?: string | null
          plus_yearly_purchase_at?: string | null
          raw_revenuecat_json?: Json | null
          refunded_at?: string | null
          revenuecat_id?: string | null
          tier?: string
          updated_at?: string
          user_id: string
          will_renew?: boolean
        }
        Update: {
          cancellation_at?: string | null
          cancelled_at?: string | null
          created_at?: string
          current_period_end?: string | null
          current_period_start?: string | null
          id?: string
          is_active?: boolean
          is_grace_period?: boolean
          lifetime_purchase_at?: string | null
          plus_monthly_purchase_at?: string | null
          plus_yearly_purchase_at?: string | null
          raw_revenuecat_json?: Json | null
          refunded_at?: string | null
          revenuecat_id?: string | null
          tier?: string
          updated_at?: string
          user_id?: string
          will_renew?: boolean
        }
        Relationships: []
      }
    }
    Views: {
      geography_columns: {
        Row: {
          coord_dimension: number | null
          f_geography_column: unknown
          f_table_catalog: unknown
          f_table_name: unknown
          f_table_schema: unknown
          srid: number | null
          type: string | null
        }
        Relationships: []
      }
      geometry_columns: {
        Row: {
          coord_dimension: number | null
          f_geometry_column: unknown
          f_table_catalog: string | null
          f_table_name: unknown
          f_table_schema: unknown
          srid: number | null
          type: string | null
        }
        Insert: {
          coord_dimension?: number | null
          f_geometry_column?: unknown
          f_table_catalog?: string | null
          f_table_name?: unknown
          f_table_schema?: unknown
          srid?: number | null
          type?: string | null
        }
        Update: {
          coord_dimension?: number | null
          f_geometry_column?: unknown
          f_table_catalog?: string | null
          f_table_name?: unknown
          f_table_schema?: unknown
          srid?: number | null
          type?: string | null
        }
        Relationships: []
      }
    }
    Functions: {
      _postgis_deprecate: {
        Args: { newname: string; oldname: string; version: string }
        Returns: undefined
      }
      _postgis_index_extent: {
        Args: { col: string; tbl: unknown }
        Returns: unknown
      }
      _postgis_pgsql_version: { Args: never; Returns: string }
      _postgis_scripts_pgsql_version: { Args: never; Returns: string }
      _postgis_selectivity: {
        Args: { att_name: string; geom: unknown; mode?: string; tbl: unknown }
        Returns: number
      }
      _postgis_stats: {
        Args: { ""?: string; att_name: string; tbl: unknown }
        Returns: string
      }
      _st_3dintersects: {
        Args: { geom1: unknown; geom2: unknown }
        Returns: boolean
      }
      _st_contains: {
        Args: { geom1: unknown; geom2: unknown }
        Returns: boolean
      }
      _st_containsproperly: {
        Args: { geom1: unknown; geom2: unknown }
        Returns: boolean
      }
      _st_coveredby:
        | { Args: { geog1: unknown; geog2: unknown }; Returns: boolean }
        | { Args: { geom1: unknown; geom2: unknown }; Returns: boolean }
      _st_covers:
        | { Args: { geog1: unknown; geog2: unknown }; Returns: boolean }
        | { Args: { geom1: unknown; geom2: unknown }; Returns: boolean }
      _st_crosses: {
        Args: { geom1: unknown; geom2: unknown }
        Returns: boolean
      }
      _st_dwithin: {
        Args: {
          geog1: unknown
          geog2: unknown
          tolerance: number
          use_spheroid?: boolean
        }
        Returns: boolean
      }
      _st_equals: { Args: { geom1: unknown; geom2: unknown }; Returns: boolean }
      _st_intersects: {
        Args: { geom1: unknown; geom2: unknown }
        Returns: boolean
      }
      _st_linecrossingdirection: {
        Args: { line1: unknown; line2: unknown }
        Returns: number
      }
      _st_longestline: {
        Args: { geom1: unknown; geom2: unknown }
        Returns: unknown
      }
      _st_maxdistance: {
        Args: { geom1: unknown; geom2: unknown }
        Returns: number
      }
      _st_orderingequals: {
        Args: { geom1: unknown; geom2: unknown }
        Returns: boolean
      }
      _st_overlaps: {
        Args: { geom1: unknown; geom2: unknown }
        Returns: boolean
      }
      _st_sortablehash: { Args: { geom: unknown }; Returns: number }
      _st_touches: {
        Args: { geom1: unknown; geom2: unknown }
        Returns: boolean
      }
      _st_voronoi: {
        Args: {
          clip?: unknown
          g1: unknown
          return_polygons?: boolean
          tolerance?: number
        }
        Returns: unknown
      }
      _st_within: { Args: { geom1: unknown; geom2: unknown }; Returns: boolean }
      addauth: { Args: { "": string }; Returns: boolean }
      addgeometrycolumn:
        | {
            Args: {
              catalog_name: string
              column_name: string
              new_dim: number
              new_srid_in: number
              new_type: string
              schema_name: string
              table_name: string
              use_typmod?: boolean
            }
            Returns: string
          }
        | {
            Args: {
              column_name: string
              new_dim: number
              new_srid: number
              new_type: string
              schema_name: string
              table_name: string
              use_typmod?: boolean
            }
            Returns: string
          }
        | {
            Args: {
              column_name: string
              new_dim: number
              new_srid: number
              new_type: string
              table_name: string
              use_typmod?: boolean
            }
            Returns: string
          }
      disablelongtransactions: { Args: never; Returns: string }
      dropgeometrycolumn:
        | {
            Args: {
              catalog_name: string
              column_name: string
              schema_name: string
              table_name: string
            }
            Returns: string
          }
        | {
            Args: {
              column_name: string
              schema_name: string
              table_name: string
            }
            Returns: string
          }
        | { Args: { column_name: string; table_name: string }; Returns: string }
      dropgeometrytable:
        | {
            Args: {
              catalog_name: string
              schema_name: string
              table_name: string
            }
            Returns: string
          }
        | { Args: { schema_name: string; table_name: string }; Returns: string }
        | { Args: { table_name: string }; Returns: string }
      enablelongtransactions: { Args: never; Returns: string }
      equals: { Args: { geom1: unknown; geom2: unknown }; Returns: boolean }
      expire_temporary_reports: { Args: never; Returns: undefined }
      find_nearest_facilities: {
        Args: {
          result_limit?: number
          search_radius_metres?: number
          user_latitude: number
          user_longitude: number
        }
        Returns: {
          address: string
          distance_metres: number
          facility_id: string
          is_accessible: boolean
          is_free: boolean
          latitude: number
          longitude: number
          name: string
          open_hours: Json
          overall_score: number
          postcode: string
          town: string
          verification_status: string
        }[]
      }
      geometry: { Args: { "": string }; Returns: unknown }
      geometry_above: {
        Args: { geom1: unknown; geom2: unknown }
        Returns: boolean
      }
      geometry_below: {
        Args: { geom1: unknown; geom2: unknown }
        Returns: boolean
      }
      geometry_cmp: {
        Args: { geom1: unknown; geom2: unknown }
        Returns: number
      }
      geometry_contained_3d: {
        Args: { geom1: unknown; geom2: unknown }
        Returns: boolean
      }
      geometry_contains: {
        Args: { geom1: unknown; geom2: unknown }
        Returns: boolean
      }
      geometry_contains_3d: {
        Args: { geom1: unknown; geom2: unknown }
        Returns: boolean
      }
      geometry_distance_box: {
        Args: { geom1: unknown; geom2: unknown }
        Returns: number
      }
      geometry_distance_centroid: {
        Args: { geom1: unknown; geom2: unknown }
        Returns: number
      }
      geometry_eq: {
        Args: { geom1: unknown; geom2: unknown }
        Returns: boolean
      }
      geometry_ge: {
        Args: { geom1: unknown; geom2: unknown }
        Returns: boolean
      }
      geometry_gt: {
        Args: { geom1: unknown; geom2: unknown }
        Returns: boolean
      }
      geometry_le: {
        Args: { geom1: unknown; geom2: unknown }
        Returns: boolean
      }
      geometry_left: {
        Args: { geom1: unknown; geom2: unknown }
        Returns: boolean
      }
      geometry_lt: {
        Args: { geom1: unknown; geom2: unknown }
        Returns: boolean
      }
      geometry_overabove: {
        Args: { geom1: unknown; geom2: unknown }
        Returns: boolean
      }
      geometry_overbelow: {
        Args: { geom1: unknown; geom2: unknown }
        Returns: boolean
      }
      geometry_overlaps: {
        Args: { geom1: unknown; geom2: unknown }
        Returns: boolean
      }
      geometry_overlaps_3d: {
        Args: { geom1: unknown; geom2: unknown }
        Returns: boolean
      }
      geometry_overleft: {
        Args: { geom1: unknown; geom2: unknown }
        Returns: boolean
      }
      geometry_overright: {
        Args: { geom1: unknown; geom2: unknown }
        Returns: boolean
      }
      geometry_right: {
        Args: { geom1: unknown; geom2: unknown }
        Returns: boolean
      }
      geometry_same: {
        Args: { geom1: unknown; geom2: unknown }
        Returns: boolean
      }
      geometry_same_3d: {
        Args: { geom1: unknown; geom2: unknown }
        Returns: boolean
      }
      geometry_within: {
        Args: { geom1: unknown; geom2: unknown }
        Returns: boolean
      }
      geomfromewkt: { Args: { "": string }; Returns: unknown }
      gettransactionid: { Args: never; Returns: unknown }
      longtransactionsenabled: { Args: never; Returns: boolean }
      populate_geometry_columns:
        | { Args: { tbl_oid: unknown; use_typmod?: boolean }; Returns: number }
        | { Args: { use_typmod?: boolean }; Returns: string }
      postgis_constraint_dims: {
        Args: { geomcolumn: string; geomschema: string; geomtable: string }
        Returns: number
      }
      postgis_constraint_srid: {
        Args: { geomcolumn: string; geomschema: string; geomtable: string }
        Returns: number
      }
      postgis_constraint_type: {
        Args: { geomcolumn: string; geomschema: string; geomtable: string }
        Returns: string
      }
      postgis_extensions_upgrade: { Args: never; Returns: string }
      postgis_full_version: { Args: never; Returns: string }
      postgis_geos_version: { Args: never; Returns: string }
      postgis_lib_build_date: { Args: never; Returns: string }
      postgis_lib_revision: { Args: never; Returns: string }
      postgis_lib_version: { Args: never; Returns: string }
      postgis_libjson_version: { Args: never; Returns: string }
      postgis_liblwgeom_version: { Args: never; Returns: string }
      postgis_libprotobuf_version: { Args: never; Returns: string }
      postgis_libxml_version: { Args: never; Returns: string }
      postgis_proj_version: { Args: never; Returns: string }
      postgis_scripts_build_date: { Args: never; Returns: string }
      postgis_scripts_installed: { Args: never; Returns: string }
      postgis_scripts_released: { Args: never; Returns: string }
      postgis_svn_version: { Args: never; Returns: string }
      postgis_type_name: {
        Args: {
          coord_dimension: number
          geomname: string
          use_new_name?: boolean
        }
        Returns: string
      }
      postgis_version: { Args: never; Returns: string }
      postgis_wagyu_version: { Args: never; Returns: string }
      st_3dclosestpoint: {
        Args: { geom1: unknown; geom2: unknown }
        Returns: unknown
      }
      st_3ddistance: {
        Args: { geom1: unknown; geom2: unknown }
        Returns: number
      }
      st_3dintersects: {
        Args: { geom1: unknown; geom2: unknown }
        Returns: boolean
      }
      st_3dlongestline: {
        Args: { geom1: unknown; geom2: unknown }
        Returns: unknown
      }
      st_3dmakebox: {
        Args: { geom1: unknown; geom2: unknown }
        Returns: unknown
      }
      st_3dmaxdistance: {
        Args: { geom1: unknown; geom2: unknown }
        Returns: number
      }
      st_3dshortestline: {
        Args: { geom1: unknown; geom2: unknown }
        Returns: unknown
      }
      st_addpoint: {
        Args: { geom1: unknown; geom2: unknown }
        Returns: unknown
      }
      st_angle:
        | { Args: { line1: unknown; line2: unknown }; Returns: number }
        | {
            Args: { pt1: unknown; pt2: unknown; pt3: unknown; pt4?: unknown }
            Returns: number
          }
      st_area:
        | { Args: { geog: unknown; use_spheroid?: boolean }; Returns: number }
        | { Args: { "": string }; Returns: number }
      st_asencodedpolyline: {
        Args: { geom: unknown; nprecision?: number }
        Returns: string
      }
      st_asewkt: { Args: { "": string }; Returns: string }
      st_asgeojson:
        | {
            Args: { geog: unknown; maxdecimaldigits?: number; options?: number }
            Returns: string
          }
        | {
            Args: { geom: unknown; maxdecimaldigits?: number; options?: number }
            Returns: string
          }
        | {
            Args: {
              geom_column?: string
              maxdecimaldigits?: number
              pretty_bool?: boolean
              r: Record<string, unknown>
            }
            Returns: string
          }
        | { Args: { "": string }; Returns: string }
      st_asgml:
        | {
            Args: {
              geog: unknown
              id?: string
              maxdecimaldigits?: number
              nprefix?: string
              options?: number
            }
            Returns: string
          }
        | {
            Args: { geom: unknown; maxdecimaldigits?: number; options?: number }
            Returns: string
          }
        | { Args: { "": string }; Returns: string }
        | {
            Args: {
              geog: unknown
              id?: string
              maxdecimaldigits?: number
              nprefix?: string
              options?: number
              version: number
            }
            Returns: string
          }
        | {
            Args: {
              geom: unknown
              id?: string
              maxdecimaldigits?: number
              nprefix?: string
              options?: number
              version: number
            }
            Returns: string
          }
      st_askml:
        | {
            Args: { geog: unknown; maxdecimaldigits?: number; nprefix?: string }
            Returns: string
          }
        | {
            Args: { geom: unknown; maxdecimaldigits?: number; nprefix?: string }
            Returns: string
          }
        | { Args: { "": string }; Returns: string }
      st_aslatlontext: {
        Args: { geom: unknown; tmpl?: string }
        Returns: string
      }
      st_asmarc21: { Args: { format?: string; geom: unknown }; Returns: string }
      st_asmvtgeom: {
        Args: {
          bounds: unknown
          buffer?: number
          clip_geom?: boolean
          extent?: number
          geom: unknown
        }
        Returns: unknown
      }
      st_assvg:
        | {
            Args: { geog: unknown; maxdecimaldigits?: number; rel?: number }
            Returns: string
          }
        | {
            Args: { geom: unknown; maxdecimaldigits?: number; rel?: number }
            Returns: string
          }
        | { Args: { "": string }; Returns: string }
      st_astext: { Args: { "": string }; Returns: string }
      st_astwkb:
        | {
            Args: {
              geom: unknown
              prec?: number
              prec_m?: number
              prec_z?: number
              with_boxes?: boolean
              with_sizes?: boolean
            }
            Returns: string
          }
        | {
            Args: {
              geom: unknown[]
              ids: number[]
              prec?: number
              prec_m?: number
              prec_z?: number
              with_boxes?: boolean
              with_sizes?: boolean
            }
            Returns: string
          }
      st_asx3d: {
        Args: { geom: unknown; maxdecimaldigits?: number; options?: number }
        Returns: string
      }
      st_azimuth:
        | { Args: { geog1: unknown; geog2: unknown }; Returns: number }
        | { Args: { geom1: unknown; geom2: unknown }; Returns: number }
      st_boundingdiagonal: {
        Args: { fits?: boolean; geom: unknown }
        Returns: unknown
      }
      st_buffer:
        | {
            Args: { geom: unknown; options?: string; radius: number }
            Returns: unknown
          }
        | {
            Args: { geom: unknown; quadsegs: number; radius: number }
            Returns: unknown
          }
      st_centroid: { Args: { "": string }; Returns: unknown }
      st_clipbybox2d: {
        Args: { box: unknown; geom: unknown }
        Returns: unknown
      }
      st_closestpoint: {
        Args: { geom1: unknown; geom2: unknown }
        Returns: unknown
      }
      st_collect: { Args: { geom1: unknown; geom2: unknown }; Returns: unknown }
      st_concavehull: {
        Args: {
          param_allow_holes?: boolean
          param_geom: unknown
          param_pctconvex: number
        }
        Returns: unknown
      }
      st_contains: {
        Args: { geom1: unknown; geom2: unknown }
        Returns: boolean
      }
      st_containsproperly: {
        Args: { geom1: unknown; geom2: unknown }
        Returns: boolean
      }
      st_coorddim: { Args: { geometry: unknown }; Returns: number }
      st_coveredby:
        | { Args: { geog1: unknown; geog2: unknown }; Returns: boolean }
        | { Args: { geom1: unknown; geom2: unknown }; Returns: boolean }
      st_covers:
        | { Args: { geog1: unknown; geog2: unknown }; Returns: boolean }
        | { Args: { geom1: unknown; geom2: unknown }; Returns: boolean }
      st_crosses: { Args: { geom1: unknown; geom2: unknown }; Returns: boolean }
      st_curvetoline: {
        Args: { flags?: number; geom: unknown; tol?: number; toltype?: number }
        Returns: unknown
      }
      st_delaunaytriangles: {
        Args: { flags?: number; g1: unknown; tolerance?: number }
        Returns: unknown
      }
      st_difference: {
        Args: { geom1: unknown; geom2: unknown; gridsize?: number }
        Returns: unknown
      }
      st_disjoint: {
        Args: { geom1: unknown; geom2: unknown }
        Returns: boolean
      }
      st_distance:
        | {
            Args: { geog1: unknown; geog2: unknown; use_spheroid?: boolean }
            Returns: number
          }
        | { Args: { geom1: unknown; geom2: unknown }; Returns: number }
      st_distancesphere:
        | { Args: { geom1: unknown; geom2: unknown }; Returns: number }
        | {
            Args: { geom1: unknown; geom2: unknown; radius: number }
            Returns: number
          }
      st_distancespheroid: {
        Args: { geom1: unknown; geom2: unknown }
        Returns: number
      }
      st_dwithin: {
        Args: {
          geog1: unknown
          geog2: unknown
          tolerance: number
          use_spheroid?: boolean
        }
        Returns: boolean
      }
      st_equals: { Args: { geom1: unknown; geom2: unknown }; Returns: boolean }
      st_expand:
        | { Args: { box: unknown; dx: number; dy: number }; Returns: unknown }
        | {
            Args: { box: unknown; dx: number; dy: number; dz?: number }
            Returns: unknown
          }
        | {
            Args: {
              dm?: number
              dx: number
              dy: number
              dz?: number
              geom: unknown
            }
            Returns: unknown
          }
      st_force3d: { Args: { geom: unknown; zvalue?: number }; Returns: unknown }
      st_force3dm: {
        Args: { geom: unknown; mvalue?: number }
        Returns: unknown
      }
      st_force3dz: {
        Args: { geom: unknown; zvalue?: number }
        Returns: unknown
      }
      st_force4d: {
        Args: { geom: unknown; mvalue?: number; zvalue?: number }
        Returns: unknown
      }
      st_generatepoints:
        | { Args: { area: unknown; npoints: number }; Returns: unknown }
        | {
            Args: { area: unknown; npoints: number; seed: number }
            Returns: unknown
          }
      st_geogfromtext: { Args: { "": string }; Returns: unknown }
      st_geographyfromtext: { Args: { "": string }; Returns: unknown }
      st_geohash:
        | { Args: { geog: unknown; maxchars?: number }; Returns: string }
        | { Args: { geom: unknown; maxchars?: number }; Returns: string }
      st_geomcollfromtext: { Args: { "": string }; Returns: unknown }
      st_geometricmedian: {
        Args: {
          fail_if_not_converged?: boolean
          g: unknown
          max_iter?: number
          tolerance?: number
        }
        Returns: unknown
      }
      st_geometryfromtext: { Args: { "": string }; Returns: unknown }
      st_geomfromewkt: { Args: { "": string }; Returns: unknown }
      st_geomfromgeojson:
        | { Args: { "": Json }; Returns: unknown }
        | { Args: { "": Json }; Returns: unknown }
        | { Args: { "": string }; Returns: unknown }
      st_geomfromgml: { Args: { "": string }; Returns: unknown }
      st_geomfromkml: { Args: { "": string }; Returns: unknown }
      st_geomfrommarc21: { Args: { marc21xml: string }; Returns: unknown }
      st_geomfromtext: { Args: { "": string }; Returns: unknown }
      st_gmltosql: { Args: { "": string }; Returns: unknown }
      st_hasarc: { Args: { geometry: unknown }; Returns: boolean }
      st_hausdorffdistance: {
        Args: { geom1: unknown; geom2: unknown }
        Returns: number
      }
      st_hexagon: {
        Args: { cell_i: number; cell_j: number; origin?: unknown; size: number }
        Returns: unknown
      }
      st_hexagongrid: {
        Args: { bounds: unknown; size: number }
        Returns: Record<string, unknown>[]
      }
      st_interpolatepoint: {
        Args: { line: unknown; point: unknown }
        Returns: number
      }
      st_intersection: {
        Args: { geom1: unknown; geom2: unknown; gridsize?: number }
        Returns: unknown
      }
      st_intersects:
        | { Args: { geog1: unknown; geog2: unknown }; Returns: boolean }
        | { Args: { geom1: unknown; geom2: unknown }; Returns: boolean }
      st_isvaliddetail: {
        Args: { flags?: number; geom: unknown }
        Returns: Database["public"]["CompositeTypes"]["valid_detail"]
        SetofOptions: {
          from: "*"
          to: "valid_detail"
          isOneToOne: true
          isSetofReturn: false
        }
      }
      st_length:
        | { Args: { geog: unknown; use_spheroid?: boolean }; Returns: number }
        | { Args: { "": string }; Returns: number }
      st_letters: { Args: { font?: Json; letters: string }; Returns: unknown }
      st_linecrossingdirection: {
        Args: { line1: unknown; line2: unknown }
        Returns: number
      }
      st_linefromencodedpolyline: {
        Args: { nprecision?: number; txtin: string }
        Returns: unknown
      }
      st_linefromtext: { Args: { "": string }; Returns: unknown }
      st_linelocatepoint: {
        Args: { geom1: unknown; geom2: unknown }
        Returns: number
      }
      st_linetocurve: { Args: { geometry: unknown }; Returns: unknown }
      st_locatealong: {
        Args: { geometry: unknown; leftrightoffset?: number; measure: number }
        Returns: unknown
      }
      st_locatebetween: {
        Args: {
          frommeasure: number
          geometry: unknown
          leftrightoffset?: number
          tomeasure: number
        }
        Returns: unknown
      }
      st_locatebetweenelevations: {
        Args: { fromelevation: number; geometry: unknown; toelevation: number }
        Returns: unknown
      }
      st_longestline: {
        Args: { geom1: unknown; geom2: unknown }
        Returns: unknown
      }
      st_makebox2d: {
        Args: { geom1: unknown; geom2: unknown }
        Returns: unknown
      }
      st_makeline: {
        Args: { geom1: unknown; geom2: unknown }
        Returns: unknown
      }
      st_makevalid: {
        Args: { geom: unknown; params: string }
        Returns: unknown
      }
      st_maxdistance: {
        Args: { geom1: unknown; geom2: unknown }
        Returns: number
      }
      st_minimumboundingcircle: {
        Args: { inputgeom: unknown; segs_per_quarter?: number }
        Returns: unknown
      }
      st_mlinefromtext: { Args: { "": string }; Returns: unknown }
      st_mpointfromtext: { Args: { "": string }; Returns: unknown }
      st_mpolyfromtext: { Args: { "": string }; Returns: unknown }
      st_multilinestringfromtext: { Args: { "": string }; Returns: unknown }
      st_multipointfromtext: { Args: { "": string }; Returns: unknown }
      st_multipolygonfromtext: { Args: { "": string }; Returns: unknown }
      st_node: { Args: { g: unknown }; Returns: unknown }
      st_normalize: { Args: { geom: unknown }; Returns: unknown }
      st_offsetcurve: {
        Args: { distance: number; line: unknown; params?: string }
        Returns: unknown
      }
      st_orderingequals: {
        Args: { geom1: unknown; geom2: unknown }
        Returns: boolean
      }
      st_overlaps: {
        Args: { geom1: unknown; geom2: unknown }
        Returns: boolean
      }
      st_perimeter: {
        Args: { geog: unknown; use_spheroid?: boolean }
        Returns: number
      }
      st_pointfromtext: { Args: { "": string }; Returns: unknown }
      st_pointm: {
        Args: {
          mcoordinate: number
          srid?: number
          xcoordinate: number
          ycoordinate: number
        }
        Returns: unknown
      }
      st_pointz: {
        Args: {
          srid?: number
          xcoordinate: number
          ycoordinate: number
          zcoordinate: number
        }
        Returns: unknown
      }
      st_pointzm: {
        Args: {
          mcoordinate: number
          srid?: number
          xcoordinate: number
          ycoordinate: number
          zcoordinate: number
        }
        Returns: unknown
      }
      st_polyfromtext: { Args: { "": string }; Returns: unknown }
      st_polygonfromtext: { Args: { "": string }; Returns: unknown }
      st_project: {
        Args: { azimuth: number; distance: number; geog: unknown }
        Returns: unknown
      }
      st_quantizecoordinates: {
        Args: {
          g: unknown
          prec_m?: number
          prec_x: number
          prec_y?: number
          prec_z?: number
        }
        Returns: unknown
      }
      st_reduceprecision: {
        Args: { geom: unknown; gridsize: number }
        Returns: unknown
      }
      st_relate: { Args: { geom1: unknown; geom2: unknown }; Returns: string }
      st_removerepeatedpoints: {
        Args: { geom: unknown; tolerance?: number }
        Returns: unknown
      }
      st_segmentize: {
        Args: { geog: unknown; max_segment_length: number }
        Returns: unknown
      }
      st_setsrid:
        | { Args: { geog: unknown; srid: number }; Returns: unknown }
        | { Args: { geom: unknown; srid: number }; Returns: unknown }
      st_sharedpaths: {
        Args: { geom1: unknown; geom2: unknown }
        Returns: unknown
      }
      st_shortestline: {
        Args: { geom1: unknown; geom2: unknown }
        Returns: unknown
      }
      st_simplifypolygonhull: {
        Args: { geom: unknown; is_outer?: boolean; vertex_fraction: number }
        Returns: unknown
      }
      st_split: { Args: { geom1: unknown; geom2: unknown }; Returns: unknown }
      st_square: {
        Args: { cell_i: number; cell_j: number; origin?: unknown; size: number }
        Returns: unknown
      }
      st_squaregrid: {
        Args: { bounds: unknown; size: number }
        Returns: Record<string, unknown>[]
      }
      st_srid:
        | { Args: { geog: unknown }; Returns: number }
        | { Args: { geom: unknown }; Returns: number }
      st_subdivide: {
        Args: { geom: unknown; gridsize?: number; maxvertices?: number }
        Returns: unknown[]
      }
      st_swapordinates: {
        Args: { geom: unknown; ords: unknown }
        Returns: unknown
      }
      st_symdifference: {
        Args: { geom1: unknown; geom2: unknown; gridsize?: number }
        Returns: unknown
      }
      st_symmetricdifference: {
        Args: { geom1: unknown; geom2: unknown }
        Returns: unknown
      }
      st_tileenvelope: {
        Args: {
          bounds?: unknown
          margin?: number
          x: number
          y: number
          zoom: number
        }
        Returns: unknown
      }
      st_touches: { Args: { geom1: unknown; geom2: unknown }; Returns: boolean }
      st_transform:
        | {
            Args: { from_proj: string; geom: unknown; to_proj: string }
            Returns: unknown
          }
        | {
            Args: { from_proj: string; geom: unknown; to_srid: number }
            Returns: unknown
          }
        | { Args: { geom: unknown; to_proj: string }; Returns: unknown }
      st_triangulatepolygon: { Args: { g1: unknown }; Returns: unknown }
      st_union:
        | { Args: { geom1: unknown; geom2: unknown }; Returns: unknown }
        | {
            Args: { geom1: unknown; geom2: unknown; gridsize: number }
            Returns: unknown
          }
      st_voronoilines: {
        Args: { extend_to?: unknown; g1: unknown; tolerance?: number }
        Returns: unknown
      }
      st_voronoipolygons: {
        Args: { extend_to?: unknown; g1: unknown; tolerance?: number }
        Returns: unknown
      }
      st_within: { Args: { geom1: unknown; geom2: unknown }; Returns: boolean }
      st_wkbtosql: { Args: { wkb: string }; Returns: unknown }
      st_wkttosql: { Args: { "": string }; Returns: unknown }
      st_wrapx: {
        Args: { geom: unknown; move: number; wrap: number }
        Returns: unknown
      }
      sync_subscription_from_revenuecat: {
        Args: {
          p_cancellation_at: string
          p_cancelled_at: string
          p_current_period_end: string
          p_current_period_start: string
          p_event_type: string
          p_is_active: boolean
          p_is_grace_period: boolean
          p_lifetime_purchase_at: string
          p_previous_tier?: string
          p_raw_json: Json
          p_refunded_at: string
          p_tier: string
          p_user_id: string
          p_will_renew: boolean
        }
        Returns: undefined
      }
      unlockrows: { Args: { "": string }; Returns: number }
      updategeometrysrid: {
        Args: {
          catalogn_name: string
          column_name: string
          new_srid_in: number
          schema_name: string
          table_name: string
        }
        Returns: string
      }
    }
    Enums: {
      [_ in never]: never
    }
    CompositeTypes: {
      geometry_dump: {
        path: number[] | null
        geom: unknown
      }
      valid_detail: {
        valid: boolean | null
        reason: string | null
        location: unknown
      }
    }
  }
}

type DatabaseWithoutInternals = Omit<Database, "__InternalSupabase">

type DefaultSchema = DatabaseWithoutInternals[Extract<keyof Database, "public">]

export type Tables<
  DefaultSchemaTableNameOrOptions extends
    | keyof (DefaultSchema["Tables"] & DefaultSchema["Views"])
    | { schema: keyof DatabaseWithoutInternals },
  TableName extends DefaultSchemaTableNameOrOptions extends {
    schema: keyof DatabaseWithoutInternals
  }
    ? keyof (DatabaseWithoutInternals[DefaultSchemaTableNameOrOptions["schema"]]["Tables"] &
        DatabaseWithoutInternals[DefaultSchemaTableNameOrOptions["schema"]]["Views"])
    : never = never,
> = DefaultSchemaTableNameOrOptions extends {
  schema: keyof DatabaseWithoutInternals
}
  ? (DatabaseWithoutInternals[DefaultSchemaTableNameOrOptions["schema"]]["Tables"] &
      DatabaseWithoutInternals[DefaultSchemaTableNameOrOptions["schema"]]["Views"])[TableName] extends {
      Row: infer R
    }
    ? R
    : never
  : DefaultSchemaTableNameOrOptions extends keyof (DefaultSchema["Tables"] &
        DefaultSchema["Views"])
    ? (DefaultSchema["Tables"] &
        DefaultSchema["Views"])[DefaultSchemaTableNameOrOptions] extends {
        Row: infer R
      }
      ? R
      : never
    : never

export type TablesInsert<
  DefaultSchemaTableNameOrOptions extends
    | keyof DefaultSchema["Tables"]
    | { schema: keyof DatabaseWithoutInternals },
  TableName extends DefaultSchemaTableNameOrOptions extends {
    schema: keyof DatabaseWithoutInternals
  }
    ? keyof DatabaseWithoutInternals[DefaultSchemaTableNameOrOptions["schema"]]["Tables"]
    : never = never,
> = DefaultSchemaTableNameOrOptions extends {
  schema: keyof DatabaseWithoutInternals
}
  ? DatabaseWithoutInternals[DefaultSchemaTableNameOrOptions["schema"]]["Tables"][TableName] extends {
      Insert: infer I
    }
    ? I
    : never
  : DefaultSchemaTableNameOrOptions extends keyof DefaultSchema["Tables"]
    ? DefaultSchema["Tables"][DefaultSchemaTableNameOrOptions] extends {
        Insert: infer I
      }
      ? I
      : never
    : never

export type TablesUpdate<
  DefaultSchemaTableNameOrOptions extends
    | keyof DefaultSchema["Tables"]
    | { schema: keyof DatabaseWithoutInternals },
  TableName extends DefaultSchemaTableNameOrOptions extends {
    schema: keyof DatabaseWithoutInternals
  }
    ? keyof DatabaseWithoutInternals[DefaultSchemaTableNameOrOptions["schema"]]["Tables"]
    : never = never,
> = DefaultSchemaTableNameOrOptions extends {
  schema: keyof DatabaseWithoutInternals
}
  ? DatabaseWithoutInternals[DefaultSchemaTableNameOrOptions["schema"]]["Tables"][TableName] extends {
      Update: infer U
    }
    ? U
    : never
  : DefaultSchemaTableNameOrOptions extends keyof DefaultSchema["Tables"]
    ? DefaultSchema["Tables"][DefaultSchemaTableNameOrOptions] extends {
        Update: infer U
      }
      ? U
      : never
    : never

export type Enums<
  DefaultSchemaEnumNameOrOptions extends
    | keyof DefaultSchema["Enums"]
    | { schema: keyof DatabaseWithoutInternals },
  EnumName extends DefaultSchemaEnumNameOrOptions extends {
    schema: keyof DatabaseWithoutInternals
  }
    ? keyof DatabaseWithoutInternals[DefaultSchemaEnumNameOrOptions["schema"]]["Enums"]
    : never = never,
> = DefaultSchemaEnumNameOrOptions extends {
  schema: keyof DatabaseWithoutInternals
}
  ? DatabaseWithoutInternals[DefaultSchemaEnumNameOrOptions["schema"]]["Enums"][EnumName]
  : DefaultSchemaEnumNameOrOptions extends keyof DefaultSchema["Enums"]
    ? DefaultSchema["Enums"][DefaultSchemaEnumNameOrOptions]
    : never

export type CompositeTypes<
  PublicCompositeTypeNameOrOptions extends
    | keyof DefaultSchema["CompositeTypes"]
    | { schema: keyof DatabaseWithoutInternals },
  CompositeTypeName extends PublicCompositeTypeNameOrOptions extends {
    schema: keyof DatabaseWithoutInternals
  }
    ? keyof DatabaseWithoutInternals[PublicCompositeTypeNameOrOptions["schema"]]["CompositeTypes"]
    : never = never,
> = PublicCompositeTypeNameOrOptions extends {
  schema: keyof DatabaseWithoutInternals
}
  ? DatabaseWithoutInternals[PublicCompositeTypeNameOrOptions["schema"]]["CompositeTypes"][CompositeTypeName]
  : PublicCompositeTypeNameOrOptions extends keyof DefaultSchema["CompositeTypes"]
    ? DefaultSchema["CompositeTypes"][PublicCompositeTypeNameOrOptions]
    : never

export const Constants = {
  public: {
    Enums: {},
  },
} as const

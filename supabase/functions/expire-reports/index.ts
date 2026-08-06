// ============================================================
// Project "Relief" — Report Expiry Edge Function (2.7)
// Called by Supabase cron job every 15 minutes to expire
// temporary reports that have passed their expiry time.
// ============================================================

import { serve } from 'https://deno.land/std@0.168.0/http/server.ts';
import { createClient } from 'https://esm.sh/@supabase/supabase-js@2';

interface ExpireResult {
  expired_count: number;
  timestamp: string;
}

serve(async (_req) => {
  try {
    // Create Supabase client with service role key
    const supabaseUrl = Deno.env.get('SUPABASE_URL') ?? '';
    const supabaseServiceKey = Deno.env.get('SUPABASE_SERVICE_ROLE_KEY') ?? '';

    if (!supabaseUrl || !supabaseServiceKey) {
      throw new Error('Missing environment variables');
    }

    const supabase = createClient(supabaseUrl, supabaseServiceKey, {
      auth: {
        autoRefreshToken: false,
        persistSession: false,
      },
    });

    // Call the database function to expire reports
    const { data, error } = await supabase.rpc('expire_temporary_reports');

    if (error) {
      throw error;
    }

    // Get count of expired reports
    const { count, error: countError } = await supabase
      .from('temporary_reports')
      .select('id', { count: 'exact', head: true })
      .eq('is_expired', true)
      .gte('expires_at', new Date(Date.now() - 15 * 60 * 1000).toISOString()) // Last 15 mins
      .lte('expires_at', new Date().toISOString());

    const result: ExpireResult = {
      expired_count: count ?? 0,
      timestamp: new Date().toISOString(),
    };

    return new Response(JSON.stringify(result), {
      headers: { 'Content-Type': 'application/json' },
      status: 200,
    });
  } catch (error) {
    console.error('Error expiring reports:', error);
    return new Response(
      JSON.stringify({ error: 'Failed to expire reports' }),
      {
        headers: { 'Content-Type': 'application/json' },
        status: 500,
      },
    );
  }
});
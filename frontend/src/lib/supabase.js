import { createClient } from '@supabase/supabase-js'

// We expose these via Vite env vars
// Note: VITE_ variables are public. In a real app with RLS, this is perfectly safe.
const supabaseUrl = import.meta.env.VITE_SUPABASE_URL
const supabaseAnonKey = import.meta.env.VITE_SUPABASE_ANON_KEY

if (!supabaseUrl || !supabaseAnonKey) {
    console.error("Missing Supabase environment variables. Please add VITE_SUPABASE_URL and VITE_SUPABASE_ANON_KEY to frontend/.env")
}

export const supabase = createClient(supabaseUrl || '', supabaseAnonKey || '')

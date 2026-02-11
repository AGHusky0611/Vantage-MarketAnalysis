/**
 * Vantage Frontend - Supabase Client
 * Singleton client for Supabase Auth & future DB usage.
 */
import { createClient } from "@supabase/supabase-js";

const SUPABASE_URL = process.env.NEXT_PUBLIC_SUPABASE_URL || "https://rgfaadheklseexqyqmai.supabase.co";
const SUPABASE_ANON_KEY =
  process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY ||
  "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InJnZmFhZGhla2xzZWV4cXlxbWFpIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzA4MzA2MzEsImV4cCI6MjA4NjQwNjYzMX0.FNo4upPavq3AQzJDbpXXPCUFDdVplOIG76kxglEO8cQ";

export const supabase = createClient(SUPABASE_URL, SUPABASE_ANON_KEY);

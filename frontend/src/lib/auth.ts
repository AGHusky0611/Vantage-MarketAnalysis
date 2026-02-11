/**
 * Vantage Frontend - Auth (Supabase)
 * Thin wrapper around Supabase Auth for register, login, logout.
 */
import { supabase } from "./supabase";

// ── Types ────────────────────────────────────────────────────

export interface User {
  id: string;
  email: string;
  username: string;
}

// ── Helpers ──────────────────────────────────────────────────

/** Map a Supabase user object to our app User shape. */
function toUser(supaUser: { id: string; email?: string; user_metadata?: Record<string, unknown> }): User {
  return {
    id: supaUser.id,
    email: supaUser.email ?? "",
    username: (supaUser.user_metadata?.username as string) || supaUser.email?.split("@")[0] || "User",
  };
}

// ── Auth actions ─────────────────────────────────────────────

export async function registerUser(email: string, username: string, password: string): Promise<User> {
  const { data, error } = await supabase.auth.signUp({
    email,
    password,
    options: { data: { username } },
  });
  if (error) throw new Error(error.message);
  if (!data.user) throw new Error("Registration failed — please try again");
  return toUser(data.user);
}

export async function loginUser(email: string, password: string): Promise<User> {
  const { data, error } = await supabase.auth.signInWithPassword({ email, password });
  if (error) throw new Error(error.message);
  return toUser(data.user);
}

export async function logoutUser(): Promise<void> {
  const { error } = await supabase.auth.signOut();
  if (error) throw new Error(error.message);
}

export async function getCurrentUser(): Promise<User | null> {
  const { data: { session } } = await supabase.auth.getSession();
  if (!session?.user) return null;
  return toUser(session.user);
}

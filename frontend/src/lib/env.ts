class EnvError extends Error {
  constructor(key: string) {
    super(`Missing required env var: ${key}`);
    this.name = "EnvError";
  }
}

function requireEnv(key: string): string {
  const value = import.meta.env[key] as string | undefined;
  if (!value) throw new EnvError(key);
  return value;
}

export const env = {
  apiBaseUrl: requireEnv("VITE_API_BASE_URL"),
  supabaseUrl: requireEnv("VITE_SUPABASE_URL"),
  supabaseAnonKey: requireEnv("VITE_SUPABASE_ANON_KEY"),
};

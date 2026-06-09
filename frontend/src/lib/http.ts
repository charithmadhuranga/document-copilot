import { supabase } from "./supabase";

export class ApiError extends Error {
  constructor(
    message: string,
    public status: number,
    public isNetworkError: boolean
  ) {
    super(message);
    this.name = "ApiError";
  }
}

async function getAccessToken(): Promise<string | null> {
  const {
    data: { session },
  } = await supabase.auth.getSession();
  return session?.access_token ?? null;
}

export async function apiFetch<T>(
  url: string,
  options: RequestInit = {}
): Promise<T> {
  const token = await getAccessToken();
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    ...(options.headers as Record<string, string>),
  };
  if (token) headers["Authorization"] = `Bearer ${token}`;

  let response: Response;
  try {
    response = await fetch(url, { ...options, headers });
  } catch {
    throw new ApiError("Network error", 0, true);
  }

  if (!response.ok) {
    const body = await response.text().catch(() => "");
    throw new ApiError(body || response.statusText, response.status, false);
  }

  return response.json() as Promise<T>;
}

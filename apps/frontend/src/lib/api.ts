const API_BASE =
  process.env.NEXT_PUBLIC_API_URL?.replace(/\/$/, "") ||
  "http://localhost:8000";
const AUTH_TOKEN = process.env.NEXT_PUBLIC_AUTH_TOKEN;
const AUTH_TOKEN_STORAGE_KEY = "auth_token";

type ApiFetchOptions = RequestInit & {
  next?: {
    revalidate?: number;
  };
};

export async function apiFetch<T>(
  path: string,
  options: ApiFetchOptions = {},
): Promise<T> {
  const url = `${API_BASE}${path}`;
  const authToken = getAuthToken();
  const res = await fetch(url, {
    cache: "no-store",
    ...options,
    headers: {
      "Content-Type": "application/json",
      ...(authToken ? { Authorization: `Bearer ${authToken}` } : {}),
      ...(options.headers ?? {}),
    },
  });

  if (!res.ok) {
    const text = await res.text();
    throw new Error(
      `Request failed (${res.status}) for ${path}: ${text || "Unknown error"}`,
    );
  }

  return res.json() as Promise<T>;
}

export function getAuthToken(): string | null {
  if (typeof window !== "undefined") {
    const stored = window.localStorage.getItem(AUTH_TOKEN_STORAGE_KEY);
    if (stored) {
      return stored;
    }
  }
  return AUTH_TOKEN ?? null;
}

export function setAuthToken(token: string): void {
  if (typeof window === "undefined") {
    return;
  }
  window.localStorage.setItem(AUTH_TOKEN_STORAGE_KEY, token);
}

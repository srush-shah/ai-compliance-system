// Use API_URL for server-side (SSR) calls, NEXT_PUBLIC_API_URL for client-side calls
// In Docker, API_URL should be set to the service name (e.g., http://api:8000)
// NEXT_PUBLIC_API_URL should be the public URL (e.g., http://localhost:8000)
const API_BASE =
  (typeof window === "undefined"
    ? process.env.API_URL
    : process.env.NEXT_PUBLIC_API_URL
  )?.replace(/\/$/, "") || "http://localhost:8000";

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
  const res = await fetch(url, {
    cache: "no-store",
    ...options,
    headers: {
      "Content-Type": "application/json",
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

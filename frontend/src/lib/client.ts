"use client";

export type Role = "community" | "officer" | "admin";

export type AuthUser = {
  id: number;
  name: string;
  email: string;
  role: Role;
};

const TOKEN_KEY = "cw_token";
const USER_KEY = "cw_user";

export function getToken(): string | null {
  if (typeof window === "undefined") return null;
  return localStorage.getItem(TOKEN_KEY);
}

export function getStoredUser(): AuthUser | null {
  if (typeof window === "undefined") return null;
  const raw = localStorage.getItem(USER_KEY);
  if (!raw) return null;
  try {
    return JSON.parse(raw) as AuthUser;
  } catch {
    return null;
  }
}

export function setAuth(token: string, user: AuthUser) {
  localStorage.setItem(TOKEN_KEY, token);
  localStorage.setItem(USER_KEY, JSON.stringify(user));
}

export function clearAuth() {
  localStorage.removeItem(TOKEN_KEY);
  localStorage.removeItem(USER_KEY);
}

export function isPatrolAllowed(user: AuthUser | null): boolean {
  return user?.role === "officer" || user?.role === "admin";
}

const API_BASE = process.env.NEXT_PUBLIC_API_BASE_URL || "http://127.0.0.1:5000/api/v1";

export async function api<T = unknown>(
  path: string,
  options: RequestInit = {}
): Promise<T> {
  const token = getToken();
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    ...(options.headers as Record<string, string> | undefined),
  };
  if (token) headers.Authorization = `Bearer ${token}`;

  // Route all API calls through the Next.js API routes which proxy to the backend
  let targetUrl = path;
  if (path.startsWith("http://") || path.startsWith("https://")) {
    targetUrl = path;
  } else if (path.startsWith("/api/")) {
    // Keep as-is - will be handled by Next.js API routes
    targetUrl = path;
  } else {
    targetUrl = `/api${path}`;
  }

  const res = await fetch(targetUrl, { ...options, headers });
  const data = await res.json().catch(() => ({}));
  if (!res.ok) {
    throw new Error(
      (data as { error?: string }).error || `Request failed (${res.status})`
    );
  }
  return data as T;
}


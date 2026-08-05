import api from './api';

export type Role = "community" | "officer" | "admin";

export type SafeUser = {
  id: number;
  name: string;
  email: string;
  role: Role;
};

export type AuthResponse = {
  token: string;
  access_token: string;
  user: SafeUser;
};

export async function login(email: string, password: string): Promise<AuthResponse> {
  const response = await api.post<AuthResponse>('/auth/login', { email, password });
  
  // Store token in localStorage
  if (typeof window !== 'undefined') {
    localStorage.setItem('token', response.token || response.access_token);
    localStorage.setItem('user', JSON.stringify(response.user));
  }
  
  return response;
}

export async function register(name: string, email: string, password: string, role?: Role): Promise<AuthResponse> {
  const response = await api.post<AuthResponse>('/auth/register', { name, email, password, role });
  
  // Store token in localStorage
  if (typeof window !== 'undefined') {
    localStorage.setItem('token', response.token || response.access_token);
    localStorage.setItem('user', JSON.stringify(response.user));
  }
  
  return response;
}

export async function getCurrentUser(): Promise<SafeUser | null> {
  try {
    const response = await api.get<{ user: SafeUser }>('/auth/me');
    return response.user;
  } catch (error) {
    return null;
  }
}

export function getStoredUser(): SafeUser | null {
  if (typeof window === 'undefined') return null;
  
  const userStr = localStorage.getItem('user');
  if (!userStr) return null;
  
  try {
    return JSON.parse(userStr);
  } catch {
    return null;
  }
}

export function getToken(): string | null {
  if (typeof window === 'undefined') return null;
  return localStorage.getItem('token');
}

export function logout(): void {
  if (typeof window !== 'undefined') {
    localStorage.removeItem('token');
    localStorage.removeItem('user');
  }
}

export function isAuthenticated(): boolean {
  return !!getToken();
}

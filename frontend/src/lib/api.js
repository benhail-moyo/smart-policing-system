const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "/api/v1";

async function request(path, options = {}) {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    headers: {
      "Content-Type": "application/json",
      ...(options.headers || {}),
    },
    ...options,
  });

  const contentType = response.headers.get("content-type") || "";
  const payload = contentType.includes("application/json") ? await response.json() : await response.text();

  if (!response.ok) {
    throw new Error(payload?.error || payload || `API request failed: ${response.status}`);
  }

  return payload;
}

export async function apiRequest(path, options = {}) {
  return request(path, options);
}

export const authAPI = {
  login: async (email, password) => request("/auth/login", {
    method: "POST",
    body: JSON.stringify({ email, password }),
  }),
  register: async (email, password) => request("/auth/register", {
    method: "POST",
    body: JSON.stringify({ email, password }),
  }),
};

const configuredOrigin =
  process.env.BACKEND_API_URL ??
  process.env.NEXT_PUBLIC_API_HOST ??
  "http://localhost:5000";

export const backendOrigin = configuredOrigin.replace(/\/+$/, "");
export const backendApiUrl = `${backendOrigin}/api/v1`;

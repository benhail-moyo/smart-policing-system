function getValidOrigin(): string {
  const envCandidates = [
    process.env.BACKEND_API_URL,
    process.env.BACKEND_API,
    process.env.NEXT_PUBLIC_API_HOST,
    process.env.NEXT_PUBLIC_API_BASE_URL,
  ];

  for (const candidate of envCandidates) {
    if (candidate && (candidate.startsWith("http://") || candidate.startsWith("https://"))) {
      return candidate.replace(/\/+$/, "").replace(/\/api\/v1$/, "");
    }
  }

  return "http://localhost:5000";
}

export const backendOrigin = getValidOrigin();
export const backendApiUrl = `${backendOrigin}/api/v1`;


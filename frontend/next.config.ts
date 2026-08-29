import type { NextConfig } from "next";

function getBackendHost(): string {
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

  return "http://127.0.0.1:5000";
}

const nextConfig: NextConfig = {
  async rewrites() {
    const apiHost = getBackendHost();
    return [
      {
        source: "/api/v1/:path*",
        destination: `${apiHost}/api/v1/:path*`,
      },
      {
        source: "/api/:path*",
        destination: `${apiHost}/api/v1/:path*`,
      },
    ];
  },
};

export default nextConfig;

import { backendApiUrl } from "@/lib/backend-api";

export const dynamic = "force-dynamic";

export async function POST(request: Request) {
  const header = request.headers.get("authorization");
  const token = header?.startsWith("Bearer ") ? header.slice(7) : header;
  const body = await request.json().catch(() => ({}));

  try {
    const response = await fetch(`${backendApiUrl}/analysis/report`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        ...(token && { Authorization: `Bearer ${token}` }),
      },
      body: JSON.stringify(body),
    });
    const data = await response.json();

    if (!response.ok) {
      return Response.json(data, { status: response.status });
    }
    return Response.json(data);
  } catch {
    return Response.json(
      { error: "Failed to connect to analysis service" },
      { status: 500 }
    );
  }
}

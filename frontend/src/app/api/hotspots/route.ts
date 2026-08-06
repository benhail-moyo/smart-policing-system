import { backendApiUrl } from "@/lib/backend-api";
export const dynamic = "force-dynamic";

export async function GET(request: Request) {
  const header = request.headers.get("authorization");
  const token = header?.startsWith("Bearer ") ? header.slice(7) : header;

  try {
    const response = await fetch(`${backendApiUrl}/hotspots`, {
      method: 'GET',
      headers: { 
        'Content-Type': 'application/json',
        ...(token && { 'Authorization': `Bearer ${token}` }),
      },
    });

    const data = await response.json();

    if (!response.ok) {
      return Response.json(data, { status: response.status });
    }

    return Response.json(data);
  } catch (error) {
    return Response.json(
      { error: "Failed to connect to hotspots service" },
      { status: 500 }
    );
  }
}

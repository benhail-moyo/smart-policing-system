import { backendApiUrl } from "@/lib/backend-api";
export const dynamic = "force-dynamic";

export async function GET(request: Request) {
  const url = new URL(request.url);
  const header = request.headers.get("authorization");
  const token = header?.startsWith("Bearer ") ? header.slice(7) : header;

  // Build query params for backend
  const params = new URLSearchParams();
  const severity = url.searchParams.get("severity");
  const limit = url.searchParams.get("limit");
  const offset = url.searchParams.get("offset");
  
  if (severity) params.append("severity", severity);
  if (limit) params.append("limit", limit);
  if (offset) params.append("offset", offset);

  try {
    const response = await fetch(`${backendApiUrl}/incidents/?${params.toString()}`, {
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

    return Response.json(data, { status: response.status });
  } catch (error) {
    return Response.json(
      { error: "Failed to connect to incidents service" },
      { status: 500 }
    );
  }
}

export async function POST(request: Request) {
  const header = request.headers.get("authorization");
  const token = header?.startsWith("Bearer ") ? header.slice(7) : header;

  const body = await request.json().catch(() => null);
  if (
    !body?.type ||
    !body?.description ||
    typeof body?.lat !== "number" ||
    typeof body?.lng !== "number"
  ) {
    return Response.json(
      { error: "type, description, lat and lng are required" },
      { status: 400 }
    );
  }

  try {
    const response = await fetch(`${backendApiUrl}/incidents/`, {
      method: 'POST',
      headers: { 
        'Content-Type': 'application/json',
        ...(token && { 'Authorization': `Bearer ${token}` }),
      },
      body: JSON.stringify({
        type: String(body.type),
        description: String(body.description),
        lat: Number(body.lat),
        lng: Number(body.lng),
        severity: body.severity,
        suburb: body.suburb,
        occurredAt: body.occurredAt,
      }),
    });

    const data = await response.json();

    if (!response.ok) {
      return Response.json(data, { status: response.status });
    }

    return Response.json(data, { status: response.status });
  } catch (error) {
    return Response.json(
      { error: "Failed to connect to incidents service" },
      { status: 500 }
    );
  }
}

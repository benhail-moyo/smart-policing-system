import { backendApiUrl } from "@/lib/backend-api";
export const dynamic = "force-dynamic";

export async function POST(request: Request) {
  const body = await request.json().catch(() => null);
  if (!body?.name || !body?.email || !body?.password) {
    return Response.json(
      { error: "Name, email and password are required" },
      { status: 400 }
    );
  }

  try {
    const response = await fetch(`${backendApiUrl}/auth/register`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        name: String(body.name),
        email: String(body.email).toLowerCase(),
        password: String(body.password),
        role: body.role === "officer" || body.role === "admin" ? body.role : "community",
      }),
    });

    const data = await response.json();

    if (!response.ok) {
      return Response.json(data, { status: response.status });
    }

    return Response.json(data);
  } catch (error) {
    return Response.json(
      { error: "Failed to connect to authentication service" },
      { status: 500 }
    );
  }
}

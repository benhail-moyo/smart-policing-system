import { backendApiUrl } from "@/lib/backend-api";

export const dynamic = "force-dynamic";

export async function POST(request: Request) {
  const body = await request.json().catch(() => null);
  if (!body?.email || !body?.password) {
    return Response.json(
      { error: "Email and password are required" },
      { status: 400 }
    );
  }

  try {
    const response = await fetch(`${backendApiUrl}/auth/login`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        // Backend expects 'identifier' (accepts email OR officer_id)
        identifier: String(body.email).toLowerCase(),
        password: String(body.password),
        ...(body.totp_code && { totp_code: String(body.totp_code) }),
      }),
    });

    const data = await response.json();

    if (!response.ok) {
      return Response.json(data, { status: response.status });
    }

    // Normalise response: expose both 'token' and 'access_token' so the
    // frontend can use either key without caring which one the backend sends.
    return Response.json({ ...data, token: data.access_token ?? data.token });
  } catch (error) {
    return Response.json(
      { error: "Failed to connect to authentication service" },
      { status: 500 }
    );
  }
}

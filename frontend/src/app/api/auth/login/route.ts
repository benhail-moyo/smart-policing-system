import { backendApiUrl } from "@/lib/backend-api";

export const dynamic = "force-dynamic";

export async function POST(request: Request) {
  const body = await request.json().catch(() => null);
  const force_number = body?.force_number ? String(body.force_number).trim().toUpperCase() : null;
  const email = body?.email ? String(body.email).trim().toLowerCase() : null;
  const identifier = body?.identifier ? String(body.identifier).trim() : null;
  const password = body?.password ? String(body.password) : null;

  if ((!force_number && !email && !identifier) || !password) {
    return Response.json(
      { error: "Force Number or Email and Password are required" },
      { status: 400 }
    );
  }

  try {
    const response = await fetch(`${backendApiUrl}/auth/login`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        ...(force_number && { force_number }),
        ...(email && { email }),
        ...(identifier && { identifier }),
        password,
        ...(body.totp_code && { totp_code: String(body.totp_code).trim() }),
        ...(body.otp_code && { otp_code: String(body.otp_code).trim() }),
      }),
    });

    const data = await response.json();

    if (!response.ok) {
      return Response.json(data, { status: response.status });
    }

    // Normalise response: expose both 'token' and 'access_token'
    return Response.json({ ...data, token: data.access_token ?? data.token });
  } catch (error) {
    return Response.json(
      { error: "Failed to connect to authentication service" },
      { status: 500 }
    );
  }
}


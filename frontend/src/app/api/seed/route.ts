import { backendApiUrl } from "@/lib/backend-api";
export const dynamic = "force-dynamic";

export async function POST() {
  try {
    const response = await fetch(`${backendApiUrl}/seed`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
    });

    const data = await response.json();

    if (!response.ok) {
      return Response.json(data, { status: response.status });
    }

    return Response.json(data);
  } catch (error) {
    return Response.json(
      { error: "Failed to connect to seed service" },
      { status: 500 }
    );
  }
}

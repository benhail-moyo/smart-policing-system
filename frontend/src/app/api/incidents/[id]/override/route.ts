import { backendApiUrl } from "@/lib/backend-api";
export const dynamic = "force-dynamic";

export async function PUT(
  request: Request,
  { params }: { params: Promise<{ id: string }> }
) {
  const { id } = await params;
  const header = request.headers.get("authorization");
  const token = header?.startsWith("Bearer ") ? header.slice(7) : header;

  try {
    const body = await request.json();
    const response = await fetch(`${backendApiUrl}/incidents/${id}/override`, {
      method: 'PUT',
      headers: { 
        'Content-Type': 'application/json',
        ...(token && { 'Authorization': `Bearer ${token}` }),
      },
      body: JSON.stringify(body),
    });

    const data = await response.json();

    if (!response.ok) {
      return Response.json(data, { status: response.status });
    }

    return Response.json(data);
  } catch (error) {
    return Response.json(
      { error: "Failed to connect to incidents service" },
      { status: 500 }
    );
  }
}
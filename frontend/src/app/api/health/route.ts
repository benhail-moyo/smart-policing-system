export const dynamic = "force-dynamic";

export async function GET() {
  try {
    const response = await fetch(`${process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:5000'}/health`, {
      method: 'GET',
      headers: { 'Content-Type': 'application/json' },
    });

    if (response.ok) {
      const data = await response.json();
      return Response.json({ ok: true, backend: data });
    } else {
      return Response.json({ ok: false, backend: false }, { status: 500 });
    }
  } catch (error) {
    return Response.json({ ok: false, backend: false }, { status: 500 });
  }
}

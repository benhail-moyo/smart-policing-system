import { backendApiUrl } from "@/lib/backend-api";

export const dynamic = "force-dynamic";

async function proxy(request: Request, context: { params: Promise<{ path: string[] }> }) {
  const { path } = await context.params;
  const token = request.headers.get("authorization");
  const response = await fetch(`${backendApiUrl}/command/${path.join("/")}`, {
    method: request.method,
    headers: { "Content-Type": "application/json", ...(token ? { Authorization: token } : {}) },
    body: request.method === "GET" ? undefined : await request.text(),
  });
  return new Response(await response.text(), { status: response.status, headers: { "Content-Type": "application/json" } });
}

export const GET = proxy;
export const POST = proxy;

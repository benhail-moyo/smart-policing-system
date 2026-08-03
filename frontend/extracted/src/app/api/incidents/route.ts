import { db } from "@/db";
import { incidents } from "@/db/schema";
import { desc, gte, lte, and, sql } from "drizzle-orm";
import { requireUser } from "@/lib/auth";
import { triage } from "@/lib/crime";

export const dynamic = "force-dynamic";

export async function GET(request: Request) {
  const url = new URL(request.url);
  const from = url.searchParams.get("from"); // ISO date string
  const to = url.searchParams.get("to");
  const hourFrom = url.searchParams.get("hourFrom"); // 0-23
  const hourTo = url.searchParams.get("hourTo"); // 0-23
  const period = url.searchParams.get("period"); // "24h" | "7d" | "30d"

  const conditions = [];

  if (from) {
    conditions.push(gte(incidents.createdAt, new Date(from)));
  }
  if (to) {
    conditions.push(lte(incidents.createdAt, new Date(to)));
  }

  if (period) {
    const now = new Date();
    if (period === "24h") {
      conditions.push(gte(incidents.createdAt, new Date(now.getTime() - 86400000)));
    } else if (period === "7d") {
      conditions.push(gte(incidents.createdAt, new Date(now.getTime() - 7 * 86400000)));
    } else if (period === "30d") {
      conditions.push(gte(incidents.createdAt, new Date(now.getTime() - 30 * 86400000)));
    } else if (period === "90d") {
      conditions.push(gte(incidents.createdAt, new Date(now.getTime() - 90 * 86400000)));
    }
  }

  let query = db.select().from(incidents).$dynamic();
  if (conditions.length > 0) {
    query = query.where(and(...conditions));
  }
  query = query.orderBy(desc(incidents.createdAt)).limit(500);

  let rows = await query;

  // client-side hour filtering (db-agnostic)
  if (hourFrom !== null || hourTo !== null) {
    const hf = hourFrom !== null ? parseInt(hourFrom, 10) : 0;
    const ht = hourTo !== null ? parseInt(hourTo, 10) : 23;
    rows = rows.filter((r) => {
      const h = new Date(r.createdAt).getHours();
      if (hf <= ht) return h >= hf && h <= ht;
      // wraps around midnight e.g. 20-4
      return h >= hf || h <= ht;
    });
  }

  return Response.json({ incidents: rows });
}

export async function POST(request: Request) {
  const user = await requireUser(request);
  if (!user) {
    return Response.json({ error: "Unauthorized" }, { status: 401 });
  }

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

  const severity = Math.min(5, Math.max(1, Number(body.severity) || 3));
  const result = triage(String(body.type), severity);

  const inserted = await db
    .insert(incidents)
    .values({
      type: String(body.type),
      description: String(body.description),
      lat: Number(body.lat),
      lng: Number(body.lng),
      severity,
      priority: result.priority,
      triageScore: result.score,
      suburb: body.suburb ? String(body.suburb) : null,
      reportedBy: user.name,
      status: "reported",
    })
    .returning();

  return Response.json({ incident: inserted[0], triage: result });
}

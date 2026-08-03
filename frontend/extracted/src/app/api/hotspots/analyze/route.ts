import { db } from "@/db";
import { incidents, hotspots } from "@/db/schema";
import { requireUser } from "@/lib/auth";
import { analyzeHotspots } from "@/lib/crime";

export const dynamic = "force-dynamic";

export async function POST(request: Request) {
  const user = await requireUser(request);
  if (!user) {
    return Response.json({ error: "Unauthorized" }, { status: 401 });
  }

  const rows = await db.select().from(incidents);
  const points = rows.map((r) => ({
    lat: r.lat,
    lng: r.lng,
    severity: r.severity,
    priority: r.priority,
    type: r.type,
  }));

  const results = analyzeHotspots(points);

  // replace existing hotspots
  await db.delete(hotspots);
  if (results.length > 0) {
    await db.insert(hotspots).values(
      results.map((h) => ({
        lat: h.lat,
        lng: h.lng,
        count: h.count,
        weight: h.weight,
        radius: h.radius,
        level: h.level,
        topTypes: h.topTypes,
      }))
    );
  }

  return Response.json({
    analyzed: points.length,
    hotspots: results.length,
    results,
  });
}

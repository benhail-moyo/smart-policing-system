import { db } from "@/db";
import { incidents } from "@/db/schema";

export const dynamic = "force-dynamic";

export async function GET() {
  const rows = await db.select().from(incidents);

  const total = rows.length;
  const byPriority: Record<string, number> = {
    critical: 0,
    high: 0,
    medium: 0,
    low: 0,
  };
  const byStatus: Record<string, number> = {
    reported: 0,
    dispatched: 0,
    resolved: 0,
  };
  const byType: Record<string, number> = {};

  const dayMs = 24 * 60 * 60 * 1000;
  const now = Date.now();
  let last24h = 0;
  let last7d = 0;

  for (const r of rows) {
    byPriority[r.priority] = (byPriority[r.priority] ?? 0) + 1;
    byStatus[r.status] = (byStatus[r.status] ?? 0) + 1;
    byType[r.type] = (byType[r.type] ?? 0) + 1;
    const age = now - new Date(r.createdAt).getTime();
    if (age <= dayMs) last24h++;
    if (age <= 7 * dayMs) last7d++;
  }

  const topTypes = Object.entries(byType)
    .sort((a, b) => b[1] - a[1])
    .slice(0, 6)
    .map(([type, count]) => ({ type, count }));

  // simple 7-day trend
  const trend: { day: string; count: number }[] = [];
  for (let i = 6; i >= 0; i--) {
    const start = now - (i + 1) * dayMs;
    const end = now - i * dayMs;
    const count = rows.filter((r) => {
      const t = new Date(r.createdAt).getTime();
      return t > start && t <= end;
    }).length;
    const label = new Date(end).toLocaleDateString("en-US", {
      weekday: "short",
    });
    trend.push({ day: label, count });
  }

  const openCases = (byStatus.reported ?? 0) + (byStatus.dispatched ?? 0);
  const resolutionRate =
    total > 0 ? Math.round(((byStatus.resolved ?? 0) / total) * 100) : 0;

  return Response.json({
    total,
    openCases,
    resolutionRate,
    last24h,
    last7d,
    byPriority,
    byStatus,
    topTypes,
    trend,
  });
}

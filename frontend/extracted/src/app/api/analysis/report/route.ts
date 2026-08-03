import { db } from "@/db";
import { incidents, hotspots } from "@/db/schema";
import { desc, gte } from "drizzle-orm";
import { requireUser } from "@/lib/auth";

export const dynamic = "force-dynamic";

// ---- Analysis engine ----

type IncidentRow = typeof incidents.$inferSelect;
type HotspotRow = typeof hotspots.$inferSelect;

interface AnalysisReport {
  generatedAt: string;
  period: string;
  summary: {
    totalIncidents: number;
    activeHotspots: number;
    resolutionRate: number;
    mostDangerousTime: string;
    mostDangerousDay: string;
    mostReportedType: string;
    trendDirection: "rising" | "falling" | "stable";
    trendPercent: number;
  };
  priorityBreakdown: { critical: number; high: number; medium: number; low: number };
  statusBreakdown: { reported: number; dispatched: number; resolved: number };
  timeAnalysis: {
    hourlyDistribution: { hour: number; count: number }[];
    peakHours: string;
    quietHours: string;
    weekdayDistribution: { day: string; count: number }[];
    weekendVsWeekday: { weekendPct: number; weekdayPct: number };
  };
  geographicAnalysis: {
    topSuburbs: { name: string; count: number; riskLevel: string }[];
    emergingHotspots: { name: string; count: number; trend: string }[];
    safestSuburbs: { name: string; count: number }[];
    geographicSpread: string;
  };
  crimeTypeAnalysis: {
    topTypes: { type: string; count: number; trend: string }[];
    shifts: { type: string; change: string }[];
    dominantPattern: string;
  };
  hotspotCorrelation: {
    topHotspots: { lat: number; lng: number; level: string; topTypes: string[]; count: number; weight: number }[];
    hotspotDensity: string;
    clusterSummary: string;
  };
  riskForecast: {
    nextWeekRisk: "critical" | "high" | "medium" | "low";
    confidence: number;
    factors: string[];
    predictedHotspotAreas: string[];
  };
  recommendations: {
    priority: "critical" | "high" | "medium" | "low";
    action: string;
    rationale: string;
    timeframe: string;
  }[];
  narrative: string;
}

// Helpers
function hourLabel(h: number): string {
  return `${String(h).padStart(2, "0")}:00`;
}

function getTrend(
  current: { count: number }[],
  previous: { count: number }[]
): { direction: "rising" | "falling" | "stable"; pct: number } {
  const cSum = current.reduce((s, x) => s + x.count, 0);
  const pSum = previous.reduce((s, x) => s + x.count, 0);
  if (pSum === 0 && cSum === 0) return { direction: "stable", pct: 0 };
  if (pSum === 0) return { direction: "rising", pct: 100 };
  const pct = Math.round(((cSum - pSum) / pSum) * 100);
  const direction = pct > 10 ? "rising" : pct < -10 ? "falling" : "stable";
  return { direction, pct };
}

function buildNarrative(
  rpt: Omit<AnalysisReport, "narrative">
): string {
  const { summary, timeAnalysis, geographicAnalysis, crimeTypeAnalysis, riskForecast } = rpt;
  const lines = [
    `Harare Crime Intelligence Report — Generated ${rpt.generatedAt.split("T")[0]}.`,
    ``,
    `OVERVIEW: A total of ${summary.totalIncidents} incidents were analysed across the reporting period, with ${summary.activeHotspots} active crime hotspots identified. The resolution rate stands at ${summary.resolutionRate}%, and the overall crime trend is ${summary.trendDirection} (${summary.trendPercent > 0 ? "+" : ""}${summary.trendPercent}% vs previous period).`,
    ``,
    `TEMPORAL PATTERNS: Crime activity peaks during ${timeAnalysis.peakHours}, with the quietest period being ${timeAnalysis.quietHours}. The most dangerous day is ${summary.mostDangerousDay}. ${timeAnalysis.weekendVsWeekday.weekendPct > timeAnalysis.weekendVsWeekday.weekdayPct ? "Weekends show elevated criminal activity compared to weekdays." : "Weekdays see higher incident rates than weekends."}`,
    ``,
    `GEOGRAPHIC DISTRIBUTION: ${geographicAnalysis.geographicSpread} The highest-risk areas are ${geographicAnalysis.topSuburbs.slice(0, 3).map((s) => s.name).join(", ")}. ${geographicAnalysis.emergingHotspots.length > 0 ? `Emerging concerns noted in ${geographicAnalysis.emergingHotspots.map((h) => h.name).join(", ")}.` : ""}`,
    ``,
    `CRIME TYPE ANALYSIS: ${crimeTypeAnalysis.dominantPattern} The most frequently reported type is ${summary.mostReportedType}. ${crimeTypeAnalysis.shifts.length > 0 ? `Notable shifts: ${crimeTypeAnalysis.shifts.map((s) => `${s.type} ${s.change}`).join("; ")}.` : ""}`,
    ``,
    `RISK ASSESSMENT: The forecast for the coming week indicates a ${riskForecast.nextWeekRisk.toUpperCase()} risk level with ${riskForecast.confidence}% confidence. Key risk factors include ${riskForecast.factors.join(", ")}. Areas to monitor: ${riskForecast.predictedHotspotAreas.join(", ")}.`,
  ];
  return lines.join("\n");
}

// ---- Route handler ----

export async function POST(request: Request) {
  const user = await requireUser(request);
  if (!user) {
    return Response.json({ error: "Unauthorized" }, { status: 401 });
  }

  const body = await request.json().catch(() => ({}));
  const periodDays = Math.min(90, Math.max(1, Number(body.periodDays) || 30));

  const since = new Date(Date.now() - periodDays * 86400000);
  const prevSince = new Date(since.getTime() - periodDays * 86400000);

  const rows = await db
    .select()
    .from(incidents)
    .where(gte(incidents.createdAt, since))
    .orderBy(desc(incidents.createdAt));

  const prevRows = await db
    .select()
    .from(incidents)
    .where(gte(incidents.createdAt, prevSince))
    .orderBy(desc(incidents.createdAt));

  const hotRows = await db.select().from(hotspots);

  const periodLabel = periodDays === 1 ? "24 hours" : periodDays === 7 ? "7 days" : periodDays === 30 ? "30 days" : `${periodDays} days`;

  // ---- SUMMARY ----
  const total = rows.length;
  const resolved = rows.filter((r) => r.status === "resolved").length;
  const resolutionRate = total > 0 ? Math.round((resolved / total) * 100) : 0;

  const byPriority = { critical: 0, high: 0, medium: 0, low: 0 };
  const byStatus = { reported: 0, dispatched: 0, resolved: 0 };
  const byType: Record<string, number> = {};
  const bySuburb: Record<string, number> = {};
  const byHour: number[] = new Array(24).fill(0);
  const byWeekday: number[] = new Array(7).fill(0);
  let weekendCount = 0;
  let weekdayCount = 0;

  const weekdayNames = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"];

  for (const r of rows) {
    const p = r.priority as keyof typeof byPriority;
    byPriority[p] = (byPriority[p] ?? 0) + 1;
    const st = r.status as keyof typeof byStatus;
    byStatus[st] = (byStatus[st] ?? 0) + 1;
    byType[r.type] = (byType[r.type] ?? 0) + 1;
    const sub = r.suburb ?? "Unknown";
    bySuburb[sub] = (bySuburb[sub] ?? 0) + 1;
    const d = new Date(r.createdAt);
    byHour[d.getHours()]++;
    byWeekday[d.getDay()]++;
    if (d.getDay() === 0 || d.getDay() === 6) weekendCount++;
    else weekdayCount++;
  }

  const totalDOW = weekendCount + weekdayCount;
  const weekendPct = totalDOW > 0 ? Math.round((weekendCount / totalDOW) * 100) : 0;
  const weekdayPct = 100 - weekendPct;

  // top crime type
  const sortedTypes = Object.entries(byType).sort((a, b) => b[1] - a[1]);
  const mostReportedType = sortedTypes[0]?.[0] ?? "N/A";

  // most dangerous hour
  let maxHour = 0;
  for (let h = 1; h < 24; h++) if (byHour[h] > byHour[maxHour]) maxHour = h;
  const mostDangerousTime = hourLabel(maxHour);

  // most dangerous day
  let maxDay = 0;
  for (let d = 1; d < 7; d++) if (byWeekday[d] > byWeekday[maxDay]) maxDay = d;
  const mostDangerousDay = weekdayNames[maxDay];

  // peak/quiet hours
  const sortedHours = byHour.map((c, h) => ({ hour: h, count: c })).sort((a, b) => b.count - a.count);
  const peakHours = sortedHours.slice(0, 3).map((h) => hourLabel(h.hour)).join(", ");
  const quietHours = sortedHours.slice(-3).reverse().map((h) => hourLabel(h.hour)).join(", ");

  // trend
  const currTypeEntries = sortedTypes.slice(0, 6).map(([type, count]) => ({ type, count }));
  const prevByType: Record<string, number> = {};
  for (const r of prevRows) {
    prevByType[r.type] = (prevByType[r.type] ?? 0) + 1;
  }
  const prevTypeEntries = currTypeEntries.map(({ type }) => ({
    type,
    count: prevByType[type] ?? 0,
  }));
  const trend = getTrend(currTypeEntries.map(({ count }) => ({ count })), prevTypeEntries.map(({ count }) => ({ count })));

  // ---- TIME ANALYSIS ----
  const hourlyDistribution = byHour.map((count, hour) => ({ hour, count }));
  const weekdayDistribution = byWeekday.map((count, i) => ({
    day: weekdayNames[i],
    count,
  }));

  // ---- GEOGRAPHIC ----
  const sortedSuburbs = Object.entries(bySuburb).sort((a, b) => b[1] - a[1]);
  const topSuburbs = sortedSuburbs.slice(0, 8).map(([name, count]) => ({
    name,
    count,
    riskLevel: count >= 15 ? "high" : count >= 8 ? "medium" : "low",
  }));

  // emerging hotspots: compare current vs previous
  const prevSuburbCounts: Record<string, number> = {};
  for (const r of prevRows) {
    const sub = r.suburb ?? "Unknown";
    prevSuburbCounts[sub] = (prevSuburbCounts[sub] ?? 0) + 1;
  }
  const emergingHotspots = sortedSuburbs
    .filter(([name, count]) => {
      const prev = prevSuburbCounts[name] ?? 0;
      return prev > 0 && count > prev * 1.4 && count >= 3;
    })
    .slice(0, 5)
    .map(([name, count]) => ({
      name,
      count,
      trend: `+${Math.round(((count - (prevSuburbCounts[name] ?? 0)) / (prevSuburbCounts[name] ?? 1)) * 100)}%`,
    }));

  const safestSuburbs = sortedSuburbs
    .slice(-5)
    .reverse()
    .map(([name, count]) => ({ name, count }));

  const geographicSpread =
    topSuburbs.length >= 3
      ? `Crime is concentrated in ${topSuburbs.slice(0, 3).map((s) => `${s.name} (${s.count} incidents)`).join(", ")} and ${topSuburbs.length - 3} other suburbs.`
      : "Crime is spread across multiple areas with no single dominant cluster.";

  // ---- CRIME TYPE ANALYSIS ----
  const topTypes = sortedTypes.slice(0, 6).map(([type, count]) => {
    const prev = prevByType[type] ?? 0;
    const change = prev > 0 ? Math.round(((count - prev) / prev) * 100) : 0;
    return {
      type,
      count,
      trend: change > 15 ? `+${change}% ↑` : change < -15 ? `${change}% ↓` : `${change > 0 ? "+" : ""}${change}% →`,
    };
  });

  const shifts = topTypes
    .filter((t) => {
      const pct = parseInt(t.trend, 10);
      return !isNaN(pct) && Math.abs(pct) > 20;
    })
    .map((t) => ({ type: t.type, change: t.trend }));

  const dominantPattern =
    sortedTypes.length >= 2
      ? `${sortedTypes[0][0]} (${sortedTypes[0][1]} cases) dominates the crime profile, ${sortedTypes[0][1] > sortedTypes.slice(1).reduce((s, x) => s + x[1], 0) ? "accounting for the majority of all reported incidents" : `closely followed by ${sortedTypes[1][0]} (${sortedTypes[1][1]} cases)`}.`
      : "Insufficient data for pattern analysis.";

  // ---- HOTSPOT CORRELATION ----
  const topHotspots = hotRows
    .slice(0, 6)
    .map((h) => ({
      lat: h.lat,
      lng: h.lng,
      level: h.level,
      topTypes: (h.topTypes as string[]) ?? [],
      count: h.count,
      weight: h.weight,
    }));

  const highHotspots = hotRows.filter((h) => h.level === "high").length;
  const medHotspots = hotRows.filter((h) => h.level === "medium").length;
  const hotspotDensity =
    hotRows.length >= 10
      ? "Dense clustering of hotspots across the city, with particular concentration in central and southern suburbs."
      : hotRows.length >= 5
      ? "Moderate hotspot distribution with identifiable clusters."
      : "Low hotspot density; incidents are more scattered.";

  const clusterSummary =
    highHotspots > 0
      ? `${highHotspots} high-risk ${highHotspots === 1 ? "cluster dominates" : "clusters dominate"} the threat landscape. ${medHotspots} medium-risk ${medHotspots === 1 ? "area requires" : "areas require"} monitoring.`
      : `${medHotspots} medium-risk clusters detected, suggesting emerging patterns that warrant proactive patrols.`;

  // ---- RISK FORECAST ----
  let nextWeekRisk: "critical" | "high" | "medium" | "low" = "low";
  const factors: string[] = [];

  if (trend.direction === "rising" && trend.pct > 20) {
    nextWeekRisk = "critical";
    factors.push("Significant upward trend in crime reports");
  } else if (trend.direction === "rising" && trend.pct > 5) {
    nextWeekRisk = "high";
    factors.push("Moderate upward trend in crime reports");
  } else if (trend.direction === "stable") {
    nextWeekRisk = "medium";
    factors.push("Stable crime levels overall");
  } else {
    nextWeekRisk = "low";
    factors.push("Declining crime trend");
  }

  if (emergingHotspots.length > 0) {
    factors.push(`${emergingHotspots.length} emerging hotspot areas`);
    if (nextWeekRisk === "low") nextWeekRisk = "medium";
  }
  if (highHotspots >= 2) {
    factors.push(`${highHotspots} active high-risk clusters`);
    if (nextWeekRisk === "low" || nextWeekRisk === "medium") nextWeekRisk = "high";
  }
  if (byPriority.critical + byPriority.high >= 10) {
    factors.push("Elevated volume of critical/high priority incidents");
    if (nextWeekRisk === "low" || nextWeekRisk === "medium") nextWeekRisk = "high";
  }
  if (weekendPct > 55) {
    factors.push("Weekend crime spike pattern detected");
  }

  const confidence = Math.min(95, Math.max(40, 50 + (total > 100 ? 30 : total > 50 ? 20 : 10)));

  const predictedHotspotAreas = topSuburbs.slice(0, 4).map((s) => s.name);

  // ---- RECOMMENDATIONS ----
  const recommendations: AnalysisReport["recommendations"] = [];

  if (byPriority.critical > 0 || byPriority.high > 5) {
    recommendations.push({
      priority: "critical",
      action: "Increase armed patrol presence in identified high-risk zones during peak hours.",
      rationale: `Critical and high-priority incidents are concentrated during ${peakHours}. Focused patrols can act as a deterrent.`,
      timeframe: "Immediate — within 24 hours",
    });
  }

  if (emergingHotspots.length > 0) {
    recommendations.push({
      priority: "high",
      action: `Deploy mobile surveillance units to ${emergingHotspots.slice(0, 3).map((h) => h.name).join(", ")}.`,
      rationale: "These areas show sharp increases in incident frequency and may become entrenched hotspots.",
      timeframe: "Within 48 hours",
    });
  }

  if (resolutionRate < 50) {
    recommendations.push({
      priority: "high",
      action: "Establish a dedicated follow-up unit to improve case resolution rates.",
      rationale: `Current resolution rate of ${resolutionRate}% is below target. Faster resolution deters repeat offences.`,
      timeframe: "Within 1 week",
    });
  }

  recommendations.push({
    priority: "medium",
    action: `Schedule community engagement meetings in ${topSuburbs.slice(0, 3).map((s) => s.name).join(", ")}.`,
    rationale: "Community intelligence is critical for early warning and prevention.",
    timeframe: "Within 2 weeks",
  });

  if (weekendPct > 50) {
    recommendations.push({
      priority: "medium",
      action: "Adjust shift patterns to allocate more resources on weekend nights.",
      rationale: `Weekends account for ${weekendPct}% of incidents — current staffing may be inadequate.`,
      timeframe: "Next shift cycle",
    });
  }

  recommendations.push({
    priority: "low",
    action: `Increase public awareness campaigns around ${mostReportedType} prevention.`,
    rationale: `As the most frequently reported crime type, public education on prevention tactics can reduce incident volume.`,
    timeframe: "Ongoing — monthly",
  });

  // ---- NARRATIVE ----
  const report: AnalysisReport = {
    generatedAt: new Date().toISOString(),
    period: periodLabel,
    summary: {
      totalIncidents: total,
      activeHotspots: hotRows.length,
      resolutionRate,
      mostDangerousTime,
      mostDangerousDay,
      mostReportedType,
      trendDirection: trend.direction,
      trendPercent: trend.pct,
    },
    priorityBreakdown: byPriority,
    statusBreakdown: byStatus,
    timeAnalysis: {
      hourlyDistribution,
      peakHours,
      quietHours,
      weekdayDistribution,
      weekendVsWeekday: { weekendPct, weekdayPct },
    },
    geographicAnalysis: {
      topSuburbs,
      emergingHotspots,
      safestSuburbs,
      geographicSpread,
    },
    crimeTypeAnalysis: {
      topTypes,
      shifts,
      dominantPattern,
    },
    hotspotCorrelation: {
      topHotspots,
      hotspotDensity,
      clusterSummary,
    },
    riskForecast: {
      nextWeekRisk,
      confidence,
      factors,
      predictedHotspotAreas,
    },
    recommendations,
    narrative: "", // filled below
  };

  report.narrative = buildNarrative(report);

  return Response.json({ report });
}

export const dynamic = "force-dynamic";

export async function POST(request: Request) {
  const header = request.headers.get("authorization");
  const token = header?.startsWith("Bearer ") ? header.slice(7) : header;

  const body = await request.json().catch(() => ({}));

  try {
    const response = await fetch(`${process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:5000/api/v1'}/analysis/report`, {
      method: 'POST',
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
      { error: "Failed to connect to analysis service" },
      { status: 500 }
    );
  }
}kdayDistribution = byWeekday.map((count, i) => ({
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

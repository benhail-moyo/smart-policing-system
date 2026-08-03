import { db } from "@/db";
import { incidents, hotspots } from "@/db/schema";
import { requireUser } from "@/lib/auth";
import {
  PATROL_ROUTES,
  routeLengthKm,
  haversineKm,
  type PatrolRoute,
} from "@/lib/crime";

export const dynamic = "force-dynamic";

// Count how many points fall within `coverageKm` of any waypoint on the route.
function coverage(
  route: PatrolRoute,
  points: { lat: number; lng: number; weight: number }[],
  coverageKm: number
) {
  let covered = 0;
  let weightCovered = 0;
  for (const p of points) {
    const near = route.waypoints.some(
      (w) => haversineKm(w, p) <= coverageKm
    );
    if (near) {
      covered++;
      weightCovered += p.weight;
    }
  }
  return { covered, weightCovered };
}

export async function POST(request: Request) {
  const user = await requireUser(request);
  if (!user) {
    return Response.json({ error: "Unauthorized" }, { status: 401 });
  }
  if (user.role !== "officer" && user.role !== "admin") {
    return Response.json({ error: "Forbidden" }, { status: 403 });
  }

  const incRows = await db.select().from(incidents);
  const hotRows = await db.select().from(hotspots);

  const incPoints = incRows.map((r) => ({
    lat: r.lat,
    lng: r.lng,
    weight: r.triageScore || 1,
  }));
  const hotPoints = hotRows.map((r) => ({
    lat: r.lat,
    lng: r.lng,
    weight: r.weight || 1,
  }));

  const COVERAGE_KM = 0.8;
  const totalHotWeight = hotPoints.reduce((s, p) => s + p.weight, 0) || 1;

  const comparison = PATROL_ROUTES.map((route) => {
    const distanceKm = routeLengthKm(route);
    const inc = coverage(route, incPoints, COVERAGE_KM);
    const hot = coverage(route, hotPoints, COVERAGE_KM);
    const hotCoveragePct = Math.round(
      (hot.weightCovered / totalHotWeight) * 100
    );
    // estimate patrol time at avg 30 km/h + 4 min per hotspot stop
    const estMinutes = Math.round(
      (distanceKm / 30) * 60 + hot.covered * 4
    );
    // score: reward hotspot coverage & incidents, penalize distance
    const efficiencyScore = Math.round(
      hot.weightCovered * 2 + inc.covered * 3 - distanceKm * 1.5
    );

    return {
      id: route.id,
      name: route.name,
      color: route.color,
      distanceKm,
      incidentsCovered: inc.covered,
      hotspotsCovered: hot.covered,
      hotCoveragePct,
      estMinutes,
      efficiencyScore,
    };
  });

  const best = comparison.reduce((a, b) =>
    b.efficiencyScore > a.efficiencyScore ? b : a
  );

  return Response.json({
    comparison,
    recommendedRouteId: best.id,
    routes: PATROL_ROUTES,
  });
}

import { PATROL_ROUTES, routeLengthKm } from "@/lib/crime";

export const dynamic = "force-dynamic";

export async function GET() {
  return Response.json({
    routes: PATROL_ROUTES.map((r) => ({
      ...r,
      distanceKm: routeLengthKm(r),
    })),
  });
}

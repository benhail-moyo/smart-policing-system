import { db } from "@/db";
import { hotspots } from "@/db/schema";
import { desc } from "drizzle-orm";

export const dynamic = "force-dynamic";

export async function GET() {
  const rows = await db
    .select()
    .from(hotspots)
    .orderBy(desc(hotspots.weight));
  return Response.json({ hotspots: rows });
}

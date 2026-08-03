import { db } from "@/db";
import { users } from "@/db/schema";
import { eq } from "drizzle-orm";
import { hashPassword, generateToken } from "@/lib/auth";

export const dynamic = "force-dynamic";

export async function POST(request: Request) {
  const body = await request.json().catch(() => null);
  if (!body?.name || !body?.email || !body?.password) {
    return Response.json(
      { error: "Name, email and password are required" },
      { status: 400 }
    );
  }

  const email = String(body.email).toLowerCase();
  const existing = await db
    .select()
    .from(users)
    .where(eq(users.email, email))
    .limit(1);
  if (existing[0]) {
    return Response.json(
      { error: "An account with that email already exists" },
      { status: 409 }
    );
  }

  const role =
    body.role === "officer" || body.role === "admin"
      ? body.role
      : "community";
  const token = generateToken();

  const inserted = await db
    .insert(users)
    .values({
      name: String(body.name),
      email,
      password: hashPassword(String(body.password)),
      role,
      token,
    })
    .returning();

  const user = inserted[0];
  return Response.json({
    token,
    user: {
      id: user.id,
      name: user.name,
      email: user.email,
      role: user.role,
    },
  });
}

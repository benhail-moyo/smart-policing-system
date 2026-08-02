import { db } from "@/db";
import { users } from "@/db/schema";
import { eq } from "drizzle-orm";
import { verifyPassword, generateToken } from "@/lib/auth";

export const dynamic = "force-dynamic";

export async function POST(request: Request) {
  const body = await request.json().catch(() => null);
  if (!body?.email || !body?.password) {
    return Response.json(
      { error: "Email and password are required" },
      { status: 400 }
    );
  }

  const rows = await db
    .select()
    .from(users)
    .where(eq(users.email, String(body.email).toLowerCase()))
    .limit(1);
  const user = rows[0];

  if (!user || !verifyPassword(String(body.password), user.password)) {
    return Response.json({ error: "Invalid credentials" }, { status: 401 });
  }

  const token = generateToken();
  await db.update(users).set({ token }).where(eq(users.id, user.id));

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

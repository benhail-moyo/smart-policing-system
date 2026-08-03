import { db } from "@/db";
import { users } from "@/db/schema";
import { eq } from "drizzle-orm";
import { randomBytes, scryptSync, timingSafeEqual } from "crypto";

export type Role = "community" | "officer" | "admin";

export type SafeUser = {
  id: number;
  name: string;
  email: string;
  role: Role;
};

export function hashPassword(password: string): string {
  const salt = randomBytes(16).toString("hex");
  const hash = scryptSync(password, salt, 64).toString("hex");
  return `${salt}:${hash}`;
}

export function verifyPassword(password: string, stored: string): boolean {
  const [salt, hash] = stored.split(":");
  if (!salt || !hash) return false;
  const hashBuffer = Buffer.from(hash, "hex");
  const test = scryptSync(password, salt, 64);
  if (hashBuffer.length !== test.length) return false;
  return timingSafeEqual(hashBuffer, test);
}

export function generateToken(): string {
  return randomBytes(32).toString("hex");
}

export async function getUserFromToken(
  token: string | null | undefined
): Promise<SafeUser | null> {
  if (!token) return null;
  const rows = await db
    .select()
    .from(users)
    .where(eq(users.token, token))
    .limit(1);
  const u = rows[0];
  if (!u) return null;
  return { id: u.id, name: u.name, email: u.email, role: u.role as Role };
}

export async function requireUser(
  request: Request
): Promise<SafeUser | null> {
  const header = request.headers.get("authorization");
  const token = header?.startsWith("Bearer ")
    ? header.slice(7)
    : header ?? null;
  return getUserFromToken(token);
}

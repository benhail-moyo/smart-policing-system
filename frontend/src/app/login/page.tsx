"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { api, setAuth, getStoredUser, type AuthUser } from "@/lib/client";
import { Shield, UserPlus, LogIn, Car, Users, Loader2, User } from "lucide-react";

type AuthResponse = { token: string; user: AuthUser };

export default function LoginPage() {
  const router = useRouter();
  const [mode, setMode] = useState<"login" | "register">("login");
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [role, setRole] = useState<"community" | "officer">("community");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [seeding, setSeeding] = useState(false);

  useEffect(() => {
    if (getStoredUser()) router.replace("/");
    api("/api/seed", { method: "POST" }).catch(() => {});
  }, [router]);

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    setLoading(true);
    try {
      const path =
        mode === "login" ? "/api/auth/login" : "/api/auth/register";
      const payload =
        mode === "login"
          ? { email, password }
          : { name, email, password, role };
      const res = await api<AuthResponse>(path, {
        method: "POST",
        body: JSON.stringify(payload),
      });
      setAuth(res.token, res.user);
      router.replace("/");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Something went wrong");
    } finally {
      setLoading(false);
    }
  }

  async function demoLogin(demoEmail: string) {
    setError(null);
    setSeeding(true);
    try {
      await api("/api/seed", { method: "POST" }).catch(() => {});
      const role = demoEmail.includes("officer") ? "officer" : demoEmail.includes("admin") ? "admin" : "community";
      const name = demoEmail.includes("officer") ? "Officer Chikwava" : demoEmail.includes("admin") ? "Command Admin" : "Tendai Moyo";

      let res: AuthResponse;
      try {
        res = await api<AuthResponse>("/api/auth/login", {
          method: "POST",
          body: JSON.stringify({ email: demoEmail, password: "password123" }),
        });
      } catch {
        res = await api<AuthResponse>("/api/auth/register", {
          method: "POST",
          body: JSON.stringify({ name, email: demoEmail, password: "password123", role }),
        });
      }

      setAuth(res.token, res.user);
      router.replace("/");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Something went wrong");
    } finally {
      setSeeding(false);
    }
  }

  return (
    <div className="flex min-h-screen items-center justify-center bg-slate-950 px-4 py-10 text-slate-100">
      <div className="w-full max-w-md">
        <div className="mb-6 text-center">
          <div className="flex justify-center">
            <Shield className="h-12 w-12 text-blue-400" />
          </div>
          <h1 className="mt-2 text-2xl font-bold">Harare Crime Watch</h1>
          <p className="text-sm text-slate-400">
            Community safety intelligence platform
          </p>
        </div>

        <div className="rounded-2xl border border-slate-800 bg-slate-900/70 p-6 shadow-xl">
          <div className="mb-5 flex rounded-lg bg-slate-800 p-1">
            {(["login", "register"] as const).map((m) => {
              const active = mode === m;
              const Icon = m === "login" ? LogIn : UserPlus;
              return (
                <button
                  key={m}
                  onClick={() => {
                    setMode(m);
                    setError(null);
                  }}
                  className={`flex flex-1 items-center justify-center gap-1.5 rounded-md py-2 text-sm font-medium capitalize transition ${
                    active
                      ? "bg-blue-600 text-white"
                      : "text-slate-300"
                  }`}
                >
                  <Icon className="h-3.5 w-3.5" />
                  {m === "login" ? "Sign in" : "Register"}
                </button>
              );
            })}
          </div>

          <form onSubmit={submit} className="space-y-3">
            {mode === "register" && (
              <input
                value={name}
                onChange={(e) => setName(e.target.value)}
                placeholder="Full name"
                required
                className="w-full rounded-lg border border-slate-700 bg-slate-800 px-3 py-2.5 text-sm outline-none focus:border-blue-500"
              />
            )}
            <input
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="Email"
              required
              className="w-full rounded-lg border border-slate-700 bg-slate-800 px-3 py-2.5 text-sm outline-none focus:border-blue-500"
            />
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="Password"
              required
              className="w-full rounded-lg border border-slate-700 bg-slate-800 px-3 py-2.5 text-sm outline-none focus:border-blue-500"
            />
            {mode === "register" && (
              <select
                value={role}
                onChange={(e) =>
                  setRole(e.target.value as "community" | "officer")
                }
                className="w-full rounded-lg border border-slate-700 bg-slate-800 px-3 py-2.5 text-sm outline-none focus:border-blue-500"
              >
                <option value="community">Community member</option>
                <option value="officer">Patrol officer</option>
              </select>
            )}

            {error && (
              <div className="rounded-lg bg-red-500/15 px-3 py-2 text-sm text-red-300">
                {error}
              </div>
            )}

            <button
              type="submit"
              disabled={loading}
              className="flex w-full items-center justify-center gap-2 rounded-lg bg-blue-600 py-2.5 text-sm font-semibold text-white hover:bg-blue-500 disabled:opacity-50"
            >
              {loading ? (
                <Loader2 className="h-4 w-4 animate-spin" />
              ) : mode === "login" ? (
                <LogIn className="h-4 w-4" />
              ) : (
                <UserPlus className="h-4 w-4" />
              )}
              {loading
                ? "Please wait…"
                : mode === "login"
                ? "Sign in"
                : "Create account"}
            </button>
          </form>

          <div className="mt-6 border-t border-slate-800 pt-4">
            <p className="mb-2 text-center text-xs uppercase tracking-wide text-slate-500">
              Quick demo access
            </p>
            <div className="grid gap-2">
              <button
                disabled={seeding}
                onClick={() => demoLogin("officer@harare.gov.zw")}
                className="flex items-center justify-center gap-2 rounded-lg border border-slate-700 bg-slate-800 py-2 text-sm hover:border-blue-500 disabled:opacity-50"
              >
                {seeding ? (
                  <Loader2 className="h-4 w-4 animate-spin" />
                ) : (
                  <Car className="h-4 w-4" />
                )}
                Patrol Officer
              </button>
              <button
                disabled={seeding}
                onClick={() => demoLogin("admin@harare.gov.zw")}
                className="flex items-center justify-center gap-2 rounded-lg border border-slate-700 bg-slate-800 py-2 text-sm hover:border-blue-500 disabled:opacity-50"
              >
                {seeding ? (
                  <Loader2 className="h-4 w-4 animate-spin" />
                ) : (
                  <User className="h-4 w-4" />
                )}
                Admin
              </button>
              <button
                disabled={seeding}
                onClick={() => demoLogin("community@harare.gov.zw")}
                className="flex items-center justify-center gap-2 rounded-lg border border-slate-700 bg-slate-800 py-2 text-sm hover:border-blue-500 disabled:opacity-50"
              >
                {seeding ? (
                  <Loader2 className="h-4 w-4 animate-spin" />
                ) : (
                  <Users className="h-4 w-4" />
                )}
                Community Member
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

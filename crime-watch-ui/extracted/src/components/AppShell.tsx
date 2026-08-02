"use client";

import { useEffect, useState } from "react";
import { usePathname, useRouter } from "next/navigation";
import Link from "next/link";
import {
  getStoredUser,
  clearAuth,
  isPatrolAllowed,
  type AuthUser,
} from "@/lib/client";
import {
  LayoutDashboard,
  Map,
  Siren,
  Car,
  BrainCircuit,
  Shield,
  LogOut,
  ChevronRight,
} from "lucide-react";

const NAV = [
  { href: "/", label: "Dashboard", Icon: LayoutDashboard, patrolOnly: false },
  { href: "/map", label: "Crime Map", Icon: Map, patrolOnly: false },
  { href: "/report", label: "Report Incident", Icon: Siren, patrolOnly: false },
  { href: "/patrol", label: "Patrol Routes", Icon: Car, patrolOnly: true },
  { href: "/analysis", label: "AI Analysis", Icon: BrainCircuit, patrolOnly: false },
];

export default function AppShell({ children }: { children: React.ReactNode }) {
  const router = useRouter();
  const pathname = usePathname();
  const [user, setUser] = useState<AuthUser | null>(null);
  const [ready, setReady] = useState(false);

  useEffect(() => {
    const u = getStoredUser();
    if (!u) {
      router.replace("/login");
      return;
    }
    setUser(u);
    setReady(true);
  }, [router]);

  function logout() {
    clearAuth();
    router.replace("/login");
  }

  if (!ready || !user) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-slate-950 text-slate-400">
        Loading…
      </div>
    );
  }

  const items = NAV.filter((n) => !n.patrolOnly || isPatrolAllowed(user));

  return (
    <div className="flex min-h-screen bg-slate-950 text-slate-100">
      {/* Desktop sidebar */}
      <aside className="hidden w-64 flex-col border-r border-slate-800 bg-slate-900/60 md:flex">
        <div className="flex items-center gap-3 border-b border-slate-800 px-5 py-5">
          <Shield className="h-7 w-7 text-blue-400" />
          <div>
            <div className="text-sm font-bold tracking-wide">HARARE</div>
            <div className="text-xs text-slate-400">Crime Watch</div>
          </div>
        </div>
        <nav className="flex-1 space-y-1 p-3">
          {items.map((n) => {
            const active =
              n.href === "/"
                ? pathname === "/"
                : pathname.startsWith(n.href);
            const Icon = n.Icon;
            return (
              <Link
                key={n.href}
                href={n.href}
                className={`flex items-center gap-3 rounded-lg px-3 py-2.5 text-sm font-medium transition ${
                  active
                    ? "bg-blue-600 text-white"
                    : "text-slate-300 hover:bg-slate-800"
                }`}
              >
                <Icon className="h-4 w-4" />
                {n.label}
                {active && (
                  <ChevronRight className="ml-auto h-3 w-3 opacity-70" />
                )}
              </Link>
            );
          })}
        </nav>
        <div className="border-t border-slate-800 p-4">
          <div className="mb-3">
            <div className="text-sm font-semibold">{user.name}</div>
            <div className="text-xs capitalize text-slate-400">{user.role}</div>
          </div>
          <button
            onClick={logout}
            className="flex w-full items-center gap-2 rounded-lg bg-slate-800 px-3 py-2 text-sm font-medium text-slate-200 hover:bg-red-600 hover:text-white"
          >
            <LogOut className="h-4 w-4" />
            Log out
          </button>
        </div>
      </aside>

      {/* Mobile layout */}
      <div className="flex flex-1 flex-col">
        <header className="flex items-center justify-between border-b border-slate-800 bg-slate-900/60 px-4 py-3 md:hidden">
          <div className="flex items-center gap-2">
            <Shield className="h-5 w-5 text-blue-400" />
            <span className="font-bold">Crime Watch</span>
          </div>
          <button
            onClick={logout}
            className="flex items-center gap-1.5 rounded-md bg-slate-800 px-3 py-1.5 text-sm"
          >
            <LogOut className="h-3.5 w-3.5" />
            Log out
          </button>
        </header>
        <nav className="flex gap-1 overflow-x-auto border-b border-slate-800 bg-slate-900/40 px-2 py-2 md:hidden">
          {items.map((n) => {
            const Icon = n.Icon;
            return (
              <Link
                key={n.href}
                href={n.href}
                className="flex items-center gap-1.5 whitespace-nowrap rounded-md px-3 py-1.5 text-xs font-medium text-slate-300 hover:bg-slate-800"
              >
                <Icon className="h-3.5 w-3.5" />
                {n.label}
              </Link>
            );
          })}
        </nav>
        <main className="flex-1 overflow-auto">{children}</main>
      </div>
    </div>
  );
}

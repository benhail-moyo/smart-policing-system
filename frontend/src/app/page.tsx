"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import AppShell from "@/components/AppShell";
import { api, getStoredUser } from "@/lib/client";
import {
  BarChart3,
  Siren,
  Clock,
  CheckCircle2,
  ArrowRight,
  FolderOpen,
  MapPin,
  Radio,
  ShieldCheck,
} from "lucide-react";

type Stats = {
  total: number;
  openCases: number;
  resolutionRate: number;
  last24h: number;
  last7d: number;
  byPriority: Record<string, number>;
  byStatus: Record<string, number>;
  topTypes: { type: string; count: number }[];
  trend: { day: string; count: number }[];
};

const PRIORITY_STYLE: Record<string, string> = {
  critical: "bg-red-500",
  high: "bg-orange-500",
  medium: "bg-yellow-500",
  low: "bg-green-500",
};

function DashboardInner() {
  const [stats, setStats] = useState<Stats | null>(null);
  const [error, setError] = useState<string | null>(null);
  const user = getStoredUser();

  useEffect(() => {
    api<Stats>("/api/incidents/stats")
      .then(setStats)
      .catch((e) => setError(e.message));
  }, []);

  const maxTrend = stats
    ? Math.max(1, ...stats.trend.map((t) => t.count))
    : 1;

  if (user?.role === "community") {
    return (
      <div className="mx-auto max-w-4xl p-5 md:p-10">
        <div className="rounded-3xl border border-blue-400/20 bg-gradient-to-br from-blue-600/20 via-slate-900 to-slate-900 p-7 md:p-10">
          <div className="mb-5 flex h-12 w-12 items-center justify-center rounded-2xl bg-blue-500 text-white"><ShieldCheck className="h-7 w-7" /></div>
          <h1 className="text-3xl font-bold">Your safety, connected.</h1>
          <p className="mt-3 max-w-xl text-slate-300">Report an incident directly to the Harare Crime Watch team. Pin its exact location on the map so responders can act faster.</p>
          <Link href="/report" className="mt-6 inline-flex items-center gap-2 rounded-xl bg-red-600 px-5 py-3 text-sm font-bold hover:bg-red-500"><Siren className="h-4 w-4" />Report an incident <ArrowRight className="h-4 w-4" /></Link>
        </div>
        <div className="mt-5 grid gap-4 sm:grid-cols-3">
          <InfoCard icon={<MapPin className="h-5 w-5 text-blue-300" />} title="Pin the location" text="Select the precise place where it happened." />
          <InfoCard icon={<Siren className="h-5 w-5 text-red-300" />} title="Share the details" text="Tell us what happened and the severity." />
          <InfoCard icon={<ShieldCheck className="h-5 w-5 text-emerald-300" />} title="Receive triage" text="Your report is prioritised for the right response." />
        </div>
      </div>
    );
  }

  return (
    <div className="p-4 md:p-8">
      <div className="mb-6 flex flex-wrap items-center justify-between gap-3">
        <div>
          <h1 className="text-2xl font-bold">{user?.role === "admin" ? "Command Overview" : "Officer Dashboard"}</h1>
          <p className="text-sm text-slate-400">
            Real-time crime overview for Harare
          </p>
        </div>
        <Link href={user?.role === "admin" ? "/command" : "/map"} className="flex items-center gap-1.5 rounded-lg bg-blue-600 px-4 py-2 text-sm font-semibold hover:bg-blue-500">{user?.role === "admin" ? <><Radio className="h-4 w-4" />Open Command Centre</> : <>Open Crime Map <ArrowRight className="h-4 w-4" /></>}</Link>
      </div>

      {error && (
        <div className="mb-4 rounded-lg bg-red-500/15 px-4 py-3 text-sm text-red-300">
          {error}
        </div>
      )}

      {!stats ? (
        <div className="text-slate-400">Loading stats…</div>
      ) : (
        <>
          <div className="grid grid-cols-2 gap-4 lg:grid-cols-4">
            <StatCard
              label="Total incidents"
              value={stats.total}
              icon={<FolderOpen className="h-6 w-6 text-blue-400" />}
            />
            <StatCard
              label="Open cases"
              value={stats.openCases}
              icon={<Siren className="h-6 w-6 text-red-400" />}
            />
            <StatCard
              label="Last 24 hours"
              value={stats.last24h}
              icon={<Clock className="h-6 w-6 text-yellow-400" />}
            />
            <StatCard
              label="Resolution rate"
              value={`${stats.resolutionRate}%`}
              icon={<CheckCircle2 className="h-6 w-6 text-green-400" />}
            />
          </div>

          <div className="mt-6 grid gap-4 lg:grid-cols-2">
            <div className="rounded-2xl border border-slate-800 bg-slate-900/60 p-5">
              <h2 className="mb-4 flex items-center gap-2 text-sm font-semibold text-slate-300">
                <BarChart3 className="h-4 w-4 text-blue-400" />
                Incidents by priority
              </h2>
              <div className="space-y-3">
                {(["critical", "high", "medium", "low"] as const).map((p) => {
                  const count = stats.byPriority[p] ?? 0;
                  const pct = stats.total
                    ? Math.round((count / stats.total) * 100)
                    : 0;
                  return (
                    <div key={p}>
                      <div className="mb-1 flex justify-between text-xs">
                        <span className="capitalize text-slate-300">{p}</span>
                        <span className="text-slate-400">
                          {count} ({pct}%)
                        </span>
                      </div>
                      <div className="h-2.5 w-full overflow-hidden rounded-full bg-slate-800">
                        <div
                          className={`h-full ${PRIORITY_STYLE[p]}`}
                          style={{ width: `${pct}%` }}
                        />
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>

            <div className="rounded-2xl border border-slate-800 bg-slate-900/60 p-5">
              <h2 className="mb-4 flex items-center gap-2 text-sm font-semibold text-slate-300">
                <Clock className="h-4 w-4 text-yellow-400" />
                7-day trend
              </h2>
              <div className="flex h-40 items-end gap-2">
                {stats.trend.map((t, i) => (
                  <div
                    key={i}
                    className="flex flex-1 flex-col items-center gap-1"
                  >
                    <div
                      className="w-full rounded-t bg-blue-500/80"
                      style={{
                        height: `${(t.count / maxTrend) * 100}%`,
                        minHeight: t.count > 0 ? "6px" : "2px",
                      }}
                      title={`${t.count} incidents`}
                    />
                    <span className="text-[10px] text-slate-400">{t.day}</span>
                  </div>
                ))}
              </div>
            </div>
          </div>

          <div className="mt-6 rounded-2xl border border-slate-800 bg-slate-900/60 p-5">
            <h2 className="mb-4 flex items-center gap-2 text-sm font-semibold text-slate-300">
              <Siren className="h-4 w-4 text-red-400" />
              Top crime categories
            </h2>
            <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
              {stats.topTypes.map((t) => (
                <div
                  key={t.type}
                  className="flex items-center justify-between rounded-lg border border-slate-800 bg-slate-950/50 px-4 py-3"
                >
                  <span className="text-sm text-slate-200">{t.type}</span>
                  <span className="rounded-full bg-blue-600/20 px-2.5 py-0.5 text-sm font-semibold text-blue-300">
                    {t.count}
                  </span>
                </div>
              ))}
            </div>
          </div>
        </>
      )}
    </div>
  );
}

function InfoCard({ icon, title, text }: { icon: React.ReactNode; title: string; text: string }) {
  return <div className="rounded-2xl border border-slate-800 bg-slate-900/60 p-5"><div className="mb-3">{icon}</div><h2 className="font-semibold">{title}</h2><p className="mt-1 text-sm text-slate-400">{text}</p></div>;
}

function StatCard({
  label,
  value,
  icon,
}: {
  label: string;
  value: number | string;
  icon: React.ReactNode;
}) {
  return (
    <div className="rounded-2xl border border-slate-800 bg-slate-900/60 p-5">
      <div className="mb-2">{icon}</div>
      <div className="text-3xl font-bold">{value}</div>
      <div className="text-xs text-slate-400">{label}</div>
    </div>
  );
}

export default function DashboardPage() {
  return (
    <AppShell>
      <DashboardInner />
    </AppShell>
  );
}

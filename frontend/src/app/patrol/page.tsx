"use client";

import { useEffect, useState } from "react";
import dynamic from "next/dynamic";
import { useRouter } from "next/navigation";
import AppShell from "@/components/AppShell";
import { api, getStoredUser, isPatrolAllowed } from "@/lib/client";
import type { MapRoute } from "@/components/CrimeMap";
import {
  Car,
  Play,
  ShieldAlert,
  Loader2,
  ArrowLeft,
  CheckCircle2,
  Route,
  Star,
} from "lucide-react";

const CrimeMap = dynamic(() => import("@/components/CrimeMap"), {
  ssr: false,
  loading: () => (
    <div className="flex h-full items-center justify-center text-slate-400">
      Loading map…
    </div>
  ),
});

type Comparison = {
  id: string;
  name: string;
  color: string;
  distanceKm: number;
  incidentsCovered: number;
  hotspotsCovered: number;
  hotCoveragePct: number;
  estMinutes: number;
  efficiencyScore: number;
};

type CompareResponse = {
  comparison: Comparison[];
  recommendedRouteId: string;
  routes: MapRoute[];
};

function PatrolInner() {
  const router = useRouter();
  const [allowed, setAllowed] = useState<boolean | null>(null);
  const [routes, setRoutes] = useState<MapRoute[]>([]);
  const [comparison, setComparison] = useState<Comparison[] | null>(null);
  const [recommended, setRecommended] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const ok = isPatrolAllowed(getStoredUser());
    setAllowed(ok);
    if (!ok) return;
    api<{ routes: MapRoute[] }>("/api/patrol/routes")
      .then((r) => setRoutes(r.routes))
      .catch((e) => setError(e.message));
  }, []);

  async function runComparison() {
    setLoading(true);
    setError(null);
    try {
      const res = await api<CompareResponse>("/api/patrol/compare", { method: "POST" });
      setComparison(res.comparison);
      setRecommended(res.recommendedRouteId);
      if (res.routes && res.routes.length > 0) {
        setRoutes(res.routes);
      }
    } catch (e) {
      setError(e instanceof Error ? e.message : "Comparison failed");
    } finally {
      setLoading(false);
    }
  }

  if (allowed === false) {
    return (
      <div className="flex h-full flex-col items-center justify-center gap-3 p-8 text-center">
        <div className="rounded-full bg-red-500/10 p-4">
          <ShieldAlert className="h-10 w-10 text-red-400" />
        </div>
        <h1 className="text-xl font-bold">Access restricted</h1>
        <p className="text-sm text-slate-400">
          Patrol route planning is available to officers and admins only.
        </p>
        <button
          onClick={() => router.replace("/")}
          className="flex items-center gap-1.5 rounded-lg bg-blue-600 px-4 py-2 text-sm font-semibold"
        >
          <ArrowLeft className="h-4 w-4" />
          Back to dashboard
        </button>
      </div>
    );
  }

  return (
    <div className="grid h-full grid-rows-[1fr_auto] lg:grid-cols-[1fr_460px] lg:grid-rows-1">
      <div className="min-h-[300px] border-b border-slate-800 lg:border-b-0 lg:border-r">
        <CrimeMap routes={routes} showIncidents={false} height="100%" />
      </div>

      <div className="overflow-auto p-5">
        <h1 className="flex items-center gap-2 text-xl font-bold">
          <Route className="h-5 w-5 text-blue-400" />
          Patrol Route Planner
        </h1>
        <p className="mb-4 text-sm text-slate-400">
          Compare candidate patrol routes by hotspot & incident coverage.
        </p>

        <div className="mb-4 space-y-2">
          {routes.map((r) => (
            <div
              key={r.id}
              className="flex items-center gap-2 text-sm text-slate-300"
            >
              <span
                className="inline-block h-3 w-6 rounded"
                style={{ background: r.color }}
              />
              {r.name}
            </div>
          ))}
        </div>

        <button
          onClick={runComparison}
          disabled={loading}
          className="flex w-full items-center justify-center gap-2 rounded-lg bg-blue-600 py-2.5 text-sm font-semibold hover:bg-blue-500 disabled:opacity-50"
        >
          {loading ? (
            <Loader2 className="h-4 w-4 animate-spin" />
          ) : (
            <Play className="h-4 w-4" />
          )}
          {loading ? "Comparing…" : "Run Comparison"}
        </button>

        {error && (
          <div className="mb-4 rounded-lg bg-red-500/15 px-3 py-2 text-sm text-red-300">
            {error}
          </div>
        )}

        {comparison && (
          <div className="overflow-hidden rounded-xl border border-slate-800">
            <table className="w-full text-left text-sm">
              <thead className="bg-slate-800/70 text-xs uppercase text-slate-400">
                <tr>
                  <th className="px-3 py-2">Metric</th>
                  {comparison.map((c) => (
                    <th key={c.id} className="px-3 py-2">
                      <span
                        className="mr-1 inline-block h-2 w-2 rounded-full align-middle"
                        style={{ background: c.color }}
                      />
                      {c.name.split("—")[0].trim()}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800">
                <Row
                  label="Distance (km)"
                  vals={comparison.map((c) => c.distanceKm)}
                />
                <Row
                  label="Incidents covered"
                  vals={comparison.map((c) => c.incidentsCovered)}
                />
                <Row
                  label="Hotspots covered"
                  vals={comparison.map((c) => c.hotspotsCovered)}
                />
                <Row
                  label="Hotspot coverage %"
                  vals={comparison.map((c) => `${c.hotCoveragePct}%`)}
                />
                <Row
                  label="Est. time (min)"
                  vals={comparison.map((c) => c.estMinutes)}
                />
                <Row
                  label="Efficiency score"
                  vals={comparison.map((c) => c.efficiencyScore)}
                  highlightId={recommended}
                  ids={comparison.map((c) => c.id)}
                />
              </tbody>
            </table>
          </div>
        )}

        {recommended && comparison && (
          <div className="mt-4 flex items-start gap-2 rounded-xl border border-green-600/40 bg-green-500/10 p-4 text-sm">
            <CheckCircle2 className="mt-0.5 h-4 w-4 shrink-0 text-green-400" />
            <span>
              Recommended:{" "}
              <b>
                {comparison.find((c) => c.id === recommended)?.name}
              </b>{" "}
              offers the best coverage-to-distance efficiency.
            </span>
          </div>
        )}
      </div>
    </div>
  );
}

function Row({
  label,
  vals,
  highlightId,
  ids,
}: {
  label: string;
  vals: (string | number)[];
  highlightId?: string | null;
  ids?: string[];
}) {
  return (
    <tr>
      <td className="px-3 py-2 text-slate-400">{label}</td>
      {vals.map((v, i) => {
        const isBest = ids && highlightId && ids[i] === highlightId;
        return (
          <td
            key={i}
            className={`px-3 py-2 font-semibold ${
              isBest ? "text-green-400" : "text-slate-100"
            }`}
          >
            {v}
            {isBest && (
              <Star className="ml-1 inline h-3 w-3 fill-current text-yellow-400" />
            )}
          </td>
        );
      })}
    </tr>
  );
}

export default function PatrolPage() {
  return (
    <AppShell>
      <PatrolInner />
    </AppShell>
  );
}

"use client";

import { useEffect, useState, useCallback } from "react";
import dynamic from "next/dynamic";
import AppShell from "@/components/AppShell";
import { api, getStoredUser, isPatrolAllowed } from "@/lib/client";
import type {
  MapIncident,
  MapHotspot,
  MapRoute,
} from "@/components/CrimeMap";
import {
  MapPin,
  Car,
  Zap,
  Filter,
  Calendar,
  Clock,
  Layers,
  Loader2,
} from "lucide-react";

const CrimeMap = dynamic(() => import("@/components/CrimeMap"), {
  ssr: false,
  loading: () => (
    <div className="flex h-full items-center justify-center text-slate-400">
      Loading map…
    </div>
  ),
});

type TimeFilter = {
  period: "all" | "24h" | "7d" | "30d" | "custom";
  hourFrom: string; // "all" | "0"-"23"
  hourTo: string;
  customFrom: string;
  customTo: string;
};

const PERIOD_LABELS: { value: TimeFilter["period"]; label: string }[] = [
  { value: "all", label: "All time" },
  { value: "24h", label: "Last 24h" },
  { value: "7d", label: "Last 7 days" },
  { value: "30d", label: "Last 30 days" },
  { value: "custom", label: "Custom" },
];

function MapInner() {
  const [allIncidents, setAllIncidents] = useState<MapIncident[]>([]);
  const [incidents, setIncidents] = useState<MapIncident[]>([]);
  const [hotspots, setHotspots] = useState<MapHotspot[]>([]);
  const [routes, setRoutes] = useState<MapRoute[]>([]);
  const [showIncidents, setShowIncidents] = useState(true);
  const [showRoutes, setShowRoutes] = useState(false);
  const [analyzing, setAnalyzing] = useState(false);
  const [msg, setMsg] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [filter, setFilter] = useState<TimeFilter>({
    period: "all",
    hourFrom: "all",
    hourTo: "all",
    customFrom: "",
    customTo: "",
  });
  const [showFilters, setShowFilters] = useState(false);
  const canPatrol = isPatrolAllowed(getStoredUser());

  const applyFilter = useCallback(
    (raw: MapIncident[]) => {
      let filtered = [...raw];

      // time period
      const now = Date.now();
      const getTs = (r: MapIncident) =>
        r.createdAt ? new Date(r.createdAt).getTime() : 0;

      if (filter.period === "24h") {
        const cutoff = now - 86400000;
        filtered = filtered.filter((r) => getTs(r) >= cutoff);
      } else if (filter.period === "7d") {
        const cutoff = now - 7 * 86400000;
        filtered = filtered.filter((r) => getTs(r) >= cutoff);
      } else if (filter.period === "30d") {
        const cutoff = now - 30 * 86400000;
        filtered = filtered.filter((r) => getTs(r) >= cutoff);
      } else if (
        filter.period === "custom" &&
        (filter.customFrom || filter.customTo)
      ) {
        if (filter.customFrom) {
          const from = new Date(filter.customFrom).getTime();
          filtered = filtered.filter((r) => getTs(r) >= from);
        }
        if (filter.customTo) {
          const to = new Date(filter.customTo).getTime() + 86400000;
          filtered = filtered.filter((r) => getTs(r) <= to);
        }
      }

      // hour filter
      if (filter.hourFrom !== "all" || filter.hourTo !== "all") {
        const hf = filter.hourFrom !== "all" ? parseInt(filter.hourFrom, 10) : 0;
        const ht = filter.hourTo !== "all" ? parseInt(filter.hourTo, 10) : 23;
        filtered = filtered.filter((r) => {
          if (!r.createdAt) return false;
          const h = new Date(r.createdAt).getHours();
          if (hf <= ht) return h >= hf && h <= ht;
          return h >= hf || h <= ht;
        });
      }

      setIncidents(filtered);
    },
    [filter]
  );

  async function load() {
    const [inc, hot, rt] = await Promise.all([
      api<{ incidents: MapIncident[] }>("/api/incidents"),
      api<{ hotspots: MapHotspot[] }>("/api/hotspots"),
      api<{ routes: MapRoute[] }>("/api/patrol/routes").catch(() => ({
        routes: [],
      })),
    ]);
    setAllIncidents(inc.incidents);
    setHotspots(hot.hotspots);
    setRoutes(rt.routes);
  }

  useEffect(() => {
    load().catch((e) => setError(e.message));
  }, []);

  useEffect(() => {
    applyFilter(allIncidents);
  }, [allIncidents, applyFilter]);

  async function runAnalysis() {
    setAnalyzing(true);
    setError(null);
    setMsg(null);
    try {
      const res = await api<{ analyzed: number; hotspots: MapHotspot[] }>(
        "/api/hotspots/analyze",
        { method: "POST" }
      );
      await load();
      setMsg(
        `Analysis complete: ${res.hotspots.length} hotspots from ${res.analyzed} incidents.`
      );
    } catch (e) {
      setError(e instanceof Error ? e.message : "Analysis failed");
    } finally {
      setAnalyzing(false);
    }
  }

  return (
    <div className="flex h-full flex-col">
      {/* Top bar */}
      <div className="flex flex-wrap items-center justify-between gap-3 border-b border-slate-800 bg-slate-900/60 px-4 py-3">
        <div>
          <h1 className="text-lg font-bold">Crime Map — Harare</h1>
          <p className="text-xs text-slate-400">
            {incidents.length} incidents · {hotspots.length} hotspots
            {filter.period !== "all" && (
              <span className="ml-2 text-blue-400">
                (filtered from {allIncidents.length})
              </span>
            )}
          </p>
        </div>
        <div className="flex flex-wrap items-center gap-2">
          <ToggleChip
            active={showIncidents}
            onClick={() => setShowIncidents((v) => !v)}
          >
            <MapPin className="h-3.5 w-3.5" />
            Incidents
          </ToggleChip>
          <ToggleChip
            active={showRoutes}
            onClick={() => setShowRoutes((v) => !v)}
          >
            <Car className="h-3.5 w-3.5" />
            Patrol routes
          </ToggleChip>
          <button
            onClick={() => setShowFilters((v) => !v)}
            className={`rounded-lg border px-3 py-2 text-sm font-medium transition ${
              showFilters
                ? "border-blue-500 bg-blue-600/20 text-blue-200"
                : "border-slate-700 bg-slate-800 text-slate-300"
            }`}
          >
            <Filter className="h-3.5 w-3.5" />
          </button>
          <button
            onClick={runAnalysis}
            disabled={analyzing || !canPatrol}
            title={
              canPatrol
                ? "Cluster incidents into hotspots"
                : "Only officers can run analysis"
            }
            className="flex items-center gap-1.5 rounded-lg bg-red-600 px-4 py-2 text-sm font-semibold hover:bg-red-500 disabled:opacity-50"
          >
            {analyzing ? (
              <Loader2 className="h-4 w-4 animate-spin" />
            ) : (
              <Zap className="h-4 w-4" />
            )}
            {analyzing ? "Analysing…" : "Run Hotspot Analysis"}
          </button>
        </div>
      </div>

      {/* Filter bar */}
      {showFilters && (
        <div className="flex flex-wrap items-center gap-3 border-b border-slate-800 bg-slate-900/40 px-4 py-2.5">
          <div className="flex items-center gap-1.5">
            <Calendar className="h-3.5 w-3.5 text-slate-400" />
            <span className="text-xs text-slate-400">Period:</span>
          </div>
          {PERIOD_LABELS.map((p) => (
            <button
              key={p.value}
              onClick={() =>
                setFilter((f) => ({ ...f, period: p.value }))
              }
              className={`rounded-md px-2.5 py-1 text-xs font-medium ${
                filter.period === p.value
                  ? "bg-blue-600 text-white"
                  : "bg-slate-800 text-slate-300 hover:bg-slate-700"
              }`}
            >
              {p.label}
            </button>
          ))}

          <div className="mx-2 h-5 w-px bg-slate-700" />

          <div className="flex items-center gap-1.5">
            <Clock className="h-3.5 w-3.5 text-slate-400" />
            <span className="text-xs text-slate-400">Hour:</span>
          </div>
          <select
            value={filter.hourFrom}
            onChange={(e) =>
              setFilter((f) => ({ ...f, hourFrom: e.target.value }))
            }
            className="rounded-md border border-slate-700 bg-slate-800 px-2 py-1 text-xs"
          >
            <option value="all">Any start</option>
            {Array.from({ length: 24 }, (_, i) => (
              <option key={i} value={String(i)}>
                {String(i).padStart(2, "0")}:00
              </option>
            ))}
          </select>
          <span className="text-xs text-slate-500">to</span>
          <select
            value={filter.hourTo}
            onChange={(e) =>
              setFilter((f) => ({ ...f, hourTo: e.target.value }))
            }
            className="rounded-md border border-slate-700 bg-slate-800 px-2 py-1 text-xs"
          >
            <option value="all">Any end</option>
            {Array.from({ length: 24 }, (_, i) => (
              <option key={i} value={String(i)}>
                {String(i).padStart(2, "0")}:59
              </option>
            ))}
          </select>

          {filter.period === "custom" && (
            <>
              <div className="mx-2 h-5 w-px bg-slate-700" />
              <input
                type="date"
                value={filter.customFrom}
                onChange={(e) =>
                  setFilter((f) => ({ ...f, customFrom: e.target.value }))
                }
                className="rounded-md border border-slate-700 bg-slate-800 px-2 py-1 text-xs text-slate-200"
              />
              <span className="text-xs text-slate-500">to</span>
              <input
                type="date"
                value={filter.customTo}
                onChange={(e) =>
                  setFilter((f) => ({ ...f, customTo: e.target.value }))
                }
                className="rounded-md border border-slate-700 bg-slate-800 px-2 py-1 text-xs text-slate-200"
              />
            </>
          )}

          <button
            onClick={() =>
              setFilter({
                period: "all",
                hourFrom: "all",
                hourTo: "all",
                customFrom: "",
                customTo: "",
              })
            }
            className="ml-auto rounded-md bg-slate-800 px-2.5 py-1 text-xs text-slate-400 hover:text-slate-200"
          >
            Reset filters
          </button>
        </div>
      )}

      {(msg || error) && (
        <div
          className={`px-4 py-2 text-sm ${
            error
              ? "bg-red-500/15 text-red-300"
              : "bg-green-500/15 text-green-300"
          }`}
        >
          {error || msg}
        </div>
      )}

      <div className="relative flex-1">
        <CrimeMap
          incidents={incidents}
          hotspots={hotspots}
          routes={showRoutes ? routes : []}
          showIncidents={showIncidents}
        />
        <div className="pointer-events-none absolute bottom-4 left-4 z-[1000] rounded-xl border border-slate-700 bg-slate-900/90 p-3 text-xs">
          <div className="mb-1 flex items-center gap-1.5 font-semibold text-slate-200">
            <Layers className="h-3.5 w-3.5" />
            Legend
          </div>
          <LegendRow color="#dc2626" label="Critical / High-risk hotspot" />
          <LegendRow color="#f97316" label="High / Medium hotspot" />
          <LegendRow color="#eab308" label="Medium / Low hotspot" />
          <LegendRow color="#22c55e" label="Low priority incident" />
        </div>
      </div>
    </div>
  );
}

function ToggleChip({
  active,
  onClick,
  children,
}: {
  active: boolean;
  onClick: () => void;
  children: React.ReactNode;
}) {
  return (
    <button
      onClick={onClick}
      className={`flex items-center gap-1.5 rounded-lg border px-3 py-2 text-sm font-medium transition ${
        active
          ? "border-blue-500 bg-blue-600/20 text-blue-200"
          : "border-slate-700 bg-slate-800 text-slate-300"
      }`}
    >
      {children}
    </button>
  );
}

function LegendRow({ color, label }: { color: string; label: string }) {
  return (
    <div className="flex items-center gap-2 py-0.5">
      <span
        className="inline-block h-3 w-3 rounded-full"
        style={{ background: color }}
      />
      <span className="text-slate-300">{label}</span>
    </div>
  );
}

export default function MapPage() {
  return (
    <AppShell>
      <MapInner />
    </AppShell>
  );
}

"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import AppShell from "@/components/AppShell";
import { api, getStoredUser } from "@/lib/client";
import { TrendingUp, MapPin, AlertTriangle, Clock, Filter } from "lucide-react";
import { TableSkeleton } from "@/components/ui/SkeletonLoader";

type Hotspot = {
  hotspot_id: string;
  centroid: { lat: number; lng: number };
  dominant_category: string | null;
  risk_score: number;
  status: string;
  incident_count: number;
  first_detected_at: string;
  last_matched_at: string;
};

function HotspotTrendsInner() {
  const [hotspots, setHotspots] = useState<Hotspot[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [statusFilter, setStatusFilter] = useState<string>("all");
  const [categoryFilter, setCategoryFilter] = useState<string>("all");
  const user = getStoredUser();

  useEffect(() => {
    async function loadHotspots() {
      try {
        const data = await api<{ hotspots: Hotspot[] }>("/api/hotspots/all");
        setHotspots(data.hotspots);
      } catch (e) {
        setError(e instanceof Error ? e.message : "Failed to load hotspots");
      } finally {
        setLoading(false);
      }
    }

    if (user?.role === "admin" || user?.role === "officer") {
      loadHotspots();
    } else {
      setError("Access restricted to administrators and officers");
      setLoading(false);
    }
  }, [user]);

  const filteredHotspots = hotspots.filter(hotspot => {
    if (statusFilter !== "all" && hotspot.status !== statusFilter) return false;
    if (categoryFilter !== "all" && hotspot.dominant_category !== categoryFilter) return false;
    return true;
  });

  const categories = Array.from(new Set(hotspots.map(h => h.dominant_category).filter(Boolean)));

  const getStatusColor = (status: string) => {
    switch (status) {
      case "active": return "bg-red-500/15 text-red-300 border-red-500/30";
      case "emerging": return "bg-yellow-500/15 text-yellow-300 border-yellow-500/30";
      case "cooling": return "bg-orange-500/15 text-orange-300 border-orange-500/30";
      case "dormant": return "bg-slate-500/15 text-slate-300 border-slate-500/30";
      default: return "bg-slate-500/15 text-slate-300 border-slate-500/30";
    }
  };

  const getRiskLevel = (score: number) => {
    if (score >= 0.6) return "high";
    if (score >= 0.3) return "medium";
    return "low";
  };

  const getRiskColor = (level: string) => {
    switch (level) {
      case "high": return "text-red-400";
      case "medium": return "text-orange-400";
      default: return "text-emerald-400";
    }
  };

  if (loading) {
    return (
      <div className="min-h-full bg-slate-950 p-4 md:p-7">
        <div className="mb-6">
          <div className="mb-2 flex items-center gap-2 text-cyan-300">
            <TrendingUp className="h-5 w-5" />
            <span className="text-xs font-bold uppercase tracking-[0.24em]">
              Hotspot Analysis
            </span>
          </div>
          <h1 className="text-3xl font-bold">Hotspot Trends</h1>
          <p className="mt-1 text-sm text-slate-400">
            Track hotspot evolution and risk patterns over time
          </p>
        </div>
        <TableSkeleton rows={8} columns={8} />
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-full bg-slate-950 p-4 md:p-7">
        <div className="rounded-2xl border border-red-500/30 bg-red-500/10 p-6 text-red-200">
          {error}
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-full bg-slate-950 p-4 md:p-7">
      <div className="mb-6">
        <div className="mb-2 flex items-center gap-2 text-cyan-300">
          <TrendingUp className="h-5 w-5" />
          <span className="text-xs font-bold uppercase tracking-[0.24em]">
            Hotspot Analysis
          </span>
        </div>
        <h1 className="text-3xl font-bold">Hotspot Trends</h1>
        <p className="mt-1 text-sm text-slate-400">
          Track hotspot evolution and risk patterns over time
        </p>
      </div>

      <div className="mb-6 flex flex-wrap gap-4">
        <div className="flex items-center gap-2">
          <Filter className="h-4 w-4 text-slate-400" />
          <select
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
            className="rounded-lg border border-slate-700 bg-slate-800 px-3 py-2 text-sm"
          >
            <option value="all">All Statuses</option>
            <option value="active">Active</option>
            <option value="emerging">Emerging</option>
            <option value="cooling">Cooling</option>
            <option value="dormant">Dormant</option>
          </select>
        </div>

        <div className="flex items-center gap-2">
          <select
            value={categoryFilter}
            onChange={(e) => setCategoryFilter(e.target.value)}
            className="rounded-lg border border-slate-700 bg-slate-800 px-3 py-2 text-sm"
          >
            <option value="all">All Categories</option>
            {categories.map(cat => (
              <option key={cat} value={cat}>{cat}</option>
            ))}
          </select>
        </div>

        <div className="ml-auto text-sm text-slate-400">
          Showing {filteredHotspots.length} of {hotspots.length} hotspots
        </div>
      </div>

      <div className="overflow-x-auto rounded-2xl border border-slate-800 bg-slate-900/70">
        <table className="w-full">
          <thead>
            <tr className="border-b border-slate-800 text-left text-xs font-semibold uppercase text-slate-400">
              <th className="px-4 py-3">Status</th>
              <th className="px-4 py-3">Category</th>
              <th className="px-4 py-3">Risk Score</th>
              <th className="px-4 py-3">Incidents</th>
              <th className="px-4 py-3">Location</th>
              <th className="px-4 py-3">First Detected</th>
              <th className="px-4 py-3">Last Matched</th>
              <th className="px-4 py-3">Actions</th>
            </tr>
          </thead>
          <tbody>
            {filteredHotspots.map((hotspot) => (
              <tr key={hotspot.hotspot_id} className="border-b border-slate-800/50 hover:bg-slate-800/30">
                <td className="px-4 py-3">
                  <span className={`rounded-full border px-2 py-1 text-xs font-semibold ${getStatusColor(hotspot.status)}`}>
                    {hotspot.status}
                  </span>
                </td>
                <td className="px-4 py-3 text-sm">
                  {hotspot.dominant_category || "Unknown"}
                </td>
                <td className="px-4 py-3">
                  <div className="flex items-center gap-2">
                    <span className={`text-sm font-semibold ${getRiskColor(getRiskLevel(hotspot.risk_score))}`}>
                      {hotspot.risk_score.toFixed(2)}
                    </span>
                    <span className="text-xs text-slate-400">
                      ({getRiskLevel(hotspot.risk_score)})
                    </span>
                  </div>
                </td>
                <td className="px-4 py-3 text-sm">
                  {hotspot.incident_count}
                </td>
                <td className="px-4 py-3 text-sm">
                  <div className="flex items-center gap-1 text-slate-400">
                    <MapPin className="h-3 w-3" />
                    {hotspot.centroid.lat.toFixed(4)}, {hotspot.centroid.lng.toFixed(4)}
                  </div>
                </td>
                <td className="px-4 py-3 text-sm text-slate-400">
                  <div className="flex items-center gap-1">
                    <Clock className="h-3 w-3" />
                    {new Date(hotspot.first_detected_at).toLocaleDateString()}
                  </div>
                </td>
                <td className="px-4 py-3 text-sm text-slate-400">
                  <div className="flex items-center gap-1">
                    <Clock className="h-3 w-3" />
                    {new Date(hotspot.last_matched_at).toLocaleDateString()}
                  </div>
                </td>
                <td className="px-4 py-3">
                  <Link
                    href={`/hotspots/trends/${hotspot.hotspot_id}`}
                    className="rounded-lg border border-cyan-500/30 bg-cyan-500/10 px-3 py-1.5 text-xs font-semibold text-cyan-300 hover:bg-cyan-500/20"
                  >
                    View Trends
                  </Link>
                </td>
              </tr>
            ))}
          </tbody>
        </table>

        {filteredHotspots.length === 0 && (
          <div className="p-8 text-center text-slate-400">
            No hotspots match the current filters
          </div>
        )}
      </div>
    </div>
  );
}

export default function HotspotTrendsPage() {
  return <AppShell><HotspotTrendsInner /></AppShell>;
}
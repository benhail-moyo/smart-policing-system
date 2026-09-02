"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import AppShell from "@/components/AppShell";
import { api, getStoredUser } from "@/lib/client";
import { TrendingUp, ArrowLeft, MapPin, AlertTriangle, Clock, Activity, BarChart3 } from "lucide-react";
import {
  LineChart,
  Line,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from "recharts";

type HotspotDetail = {
  hotspot: {
    hotspot_id: string;
    centroid: { lat: number; lng: number };
    dominant_category: string | null;
    risk_score: number;
    status: string;
    incident_count: number;
    first_detected_at: string;
    last_matched_at: string;
  };
  summary: {
    total_runs_tracked: number;
    first_detected_at: string;
    last_matched_at: string;
    current_streak: number;
  };
};

type HistoryEntry = {
  history_id: number;
  hotspot_id: string;
  run_timestamp: string;
  centroid: { lat: number; lng: number };
  incident_count: number;
  risk_score: number;
  volume_score: number;
  severity_score: number;
  recency_score: number;
  status: string;
  dominant_category: string | null;
};

function HotspotDetailInner({ hotspot_id }: { hotspot_id: string }) {
  const [hotspotData, setHotspotData] = useState<HotspotDetail | null>(null);
  const [history, setHistory] = useState<HistoryEntry[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const user = getStoredUser();

  useEffect(() => {
    async function loadData() {
      try {
        const [detailResp, historyResp] = await Promise.all([
          api<HotspotDetail>(`/api/hotspots/${hotspot_id}`),
          api<{ history: HistoryEntry[] }>(`/api/hotspots/${hotspot_id}/history`)
        ]);
        setHotspotData(detailResp);
        setHistory(historyResp.history);
      } catch (e) {
        setError(e instanceof Error ? e.message : "Failed to load hotspot data");
      } finally {
        setLoading(false);
      }
    }

    if (user?.role === "admin" || user?.role === "officer") {
      loadData();
    } else {
      setError("Access restricted to administrators and officers");
      setLoading(false);
    }
  }, [hotspot_id, user]);

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

  // Prepare chart data
  const chartData = history.map(entry => ({
    timestamp: new Date(entry.run_timestamp).toLocaleDateString(),
    riskScore: entry.risk_score,
    incidentCount: entry.incident_count,
    volumeScore: entry.volume_score,
    severityScore: entry.severity_score,
    recencyScore: entry.recency_score,
    status: entry.status,
  }));

  // Calculate summary statistics
  const peakRisk = history.length > 0 ? Math.max(...history.map(h => h.risk_score)) : 0;
  const peakRiskDate = history.length > 0 
    ? history.find(h => h.risk_score === peakRisk)?.run_timestamp 
    : null;
  const reactivations = history.filter((h, i) => 
    i > 0 && h.status === 'active' && history[i-1].status !== 'active'
  ).length;

  if (loading) {
    return (
      <div className="min-h-full bg-slate-950 p-4 md:p-7">
        <div className="flex h-full items-center justify-center text-slate-400">
          Loading hotspot details...
        </div>
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

  if (!hotspotData) {
    return (
      <div className="min-h-full bg-slate-950 p-4 md:p-7">
        <div className="rounded-2xl border border-slate-800 bg-slate-900/70 p-6 text-slate-400">
          Hotspot not found
        </div>
      </div>
    );
  }

  const hotspot = hotspotData.hotspot;
  const summary = hotspotData.summary;

  return (
    <div className="min-h-full bg-slate-950 p-4 md:p-7">
      <div className="mb-6">
        <Link 
          href="/hotspots/trends" 
          className="mb-4 inline-flex items-center gap-2 text-sm text-slate-400 hover:text-slate-200"
        >
          <ArrowLeft className="h-4 w-4" />
          Back to Trends
        </Link>

        <div className="mb-2 flex items-center gap-2 text-cyan-300">
          <TrendingUp className="h-5 w-5" />
          <span className="text-xs font-bold uppercase tracking-[0.24em]">
            Hotspot Analysis
          </span>
        </div>
        <h1 className="text-3xl font-bold">Hotspot Detail</h1>
        <p className="mt-1 text-sm text-slate-400">
          Track risk patterns and status evolution for this specific hotspot
        </p>
      </div>

      {/* Summary Statistics */}
      <div className="mb-6 grid gap-4 md:grid-cols-4">
        <div className="rounded-xl border border-slate-800 bg-slate-900/70 p-4">
          <div className="mb-2 flex items-center gap-2 text-slate-400">
            <Activity className="h-4 w-4" />
            <span className="text-xs font-semibold uppercase">Status</span>
          </div>
          <span className={`rounded-full border px-3 py-1 text-sm font-semibold ${getStatusColor(hotspot.status)}`}>
            {hotspot.status}
          </span>
        </div>

        <div className="rounded-xl border border-slate-800 bg-slate-900/70 p-4">
          <div className="mb-2 flex items-center gap-2 text-slate-400">
            <Clock className="h-4 w-4" />
            <span className="text-xs font-semibold uppercase">Days Tracked</span>
          </div>
          <div className="text-2xl font-bold">{summary.total_runs_tracked}</div>
        </div>

        <div className="rounded-xl border border-slate-800 bg-slate-900/70 p-4">
          <div className="mb-2 flex items-center gap-2 text-slate-400">
            <AlertTriangle className="h-4 w-4" />
            <span className="text-xs font-semibold uppercase">Peak Risk</span>
          </div>
          <div className={`text-2xl font-bold ${getRiskColor(getRiskLevel(peakRisk))}`}>
            {peakRisk.toFixed(2)}
          </div>
          {peakRiskDate && (
            <div className="text-xs text-slate-400">
              {new Date(peakRiskDate).toLocaleDateString()}
            </div>
          )}
        </div>

        <div className="rounded-xl border border-slate-800 bg-slate-900/70 p-4">
          <div className="mb-2 flex items-center gap-2 text-slate-400">
            <BarChart3 className="h-4 w-4" />
            <span className="text-xs font-semibold uppercase">Reactivations</span>
          </div>
          <div className="text-2xl font-bold">{reactivations}</div>
        </div>
      </div>

      {/* Current State */}
      <div className="mb-6 rounded-2xl border border-slate-800 bg-slate-900/70 p-5">
        <h2 className="mb-4 flex items-center gap-2 font-semibold">
          <MapPin className="h-4 w-4 text-cyan-400" />
          Current State
        </h2>
        <div className="grid gap-4 md:grid-cols-3">
          <div>
            <div className="text-xs text-slate-400">Risk Score</div>
            <div className={`text-lg font-semibold ${getRiskColor(getRiskLevel(hotspot.risk_score))}`}>
              {hotspot.risk_score.toFixed(2)} ({getRiskLevel(hotspot.risk_score)})
            </div>
          </div>
          <div>
            <div className="text-xs text-slate-400">Incident Count</div>
            <div className="text-lg font-semibold">{hotspot.incident_count}</div>
          </div>
          <div>
            <div className="text-xs text-slate-400">Dominant Category</div>
            <div className="text-lg font-semibold">{hotspot.dominant_category || "Unknown"}</div>
          </div>
          <div>
            <div className="text-xs text-slate-400">Location</div>
            <div className="text-sm text-slate-300">
              {hotspot.centroid.lat.toFixed(4)}, {hotspot.centroid.lng.toFixed(4)}
            </div>
          </div>
          <div>
            <div className="text-xs text-slate-400">Current Streak</div>
            <div className="text-lg font-semibold">{summary.current_streak} misses</div>
          </div>
          <div>
            <div className="text-xs text-slate-400">Last Matched</div>
            <div className="text-sm text-slate-300">
              {new Date(summary.last_matched_at).toLocaleString()}
            </div>
          </div>
        </div>
      </div>

      {/* Charts */}
      {history.length > 0 && (
        <div className="space-y-6">
          {/* Risk Score Over Time */}
          <div className="rounded-2xl border border-slate-800 bg-slate-900/70 p-5">
            <h2 className="mb-4 flex items-center gap-2 font-semibold">
              <TrendingUp className="h-4 w-4 text-cyan-400" />
              Risk Score Over Time
            </h2>
            <div className="h-80">
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={chartData}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
                  <XAxis 
                    dataKey="timestamp" 
                    stroke="#94a3b8"
                    fontSize={12}
                  />
                  <YAxis 
                    stroke="#94a3b8"
                    fontSize={12}
                    domain={[0, 1]}
                  />
                  <Tooltip 
                    contentStyle={{ 
                      backgroundColor: '#0f172a', 
                      border: '1px solid #334155',
                      borderRadius: '8px'
                    }}
                    itemStyle={{ color: '#e2e8f0' }}
                  />
                  <Legend />
                  <Line 
                    type="monotone" 
                    dataKey="riskScore" 
                    stroke="#06b6d4" 
                    strokeWidth={2}
                    name="Risk Score"
                    dot={{ fill: '#06b6d4' }}
                  />
                </LineChart>
              </ResponsiveContainer>
            </div>
          </div>

          {/* Incident Count Over Time */}
          <div className="rounded-2xl border border-slate-800 bg-slate-900/70 p-5">
            <h2 className="mb-4 flex items-center gap-2 font-semibold">
              <BarChart3 className="h-4 w-4 text-cyan-400" />
              Incident Count Over Time
            </h2>
            <div className="h-80">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={chartData}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
                  <XAxis 
                    dataKey="timestamp" 
                    stroke="#94a3b8"
                    fontSize={12}
                  />
                  <YAxis 
                    stroke="#94a3b8"
                    fontSize={12}
                  />
                  <Tooltip 
                    contentStyle={{ 
                      backgroundColor: '#0f172a', 
                      border: '1px solid #334155',
                      borderRadius: '8px'
                    }}
                    itemStyle={{ color: '#e2e8f0' }}
                  />
                  <Legend />
                  <Bar 
                    dataKey="incidentCount" 
                    fill="#f97316"
                    name="Incident Count"
                  />
                </BarChart>
              </ResponsiveContainer>
            </div>
          </div>

          {/* Risk Component Breakdown */}
          <div className="rounded-2xl border border-slate-800 bg-slate-900/70 p-5">
            <h2 className="mb-4 flex items-center gap-2 font-semibold">
              <Activity className="h-4 w-4 text-cyan-400" />
              Risk Component Breakdown
            </h2>
            <div className="h-80">
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={chartData}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
                  <XAxis 
                    dataKey="timestamp" 
                    stroke="#94a3b8"
                    fontSize={12}
                  />
                  <YAxis 
                    stroke="#94a3b8"
                    fontSize={12}
                    domain={[0, 1]}
                  />
                  <Tooltip 
                    contentStyle={{ 
                      backgroundColor: '#0f172a', 
                      border: '1px solid #334155',
                      borderRadius: '8px'
                    }}
                    itemStyle={{ color: '#e2e8f0' }}
                  />
                  <Legend />
                  <Line 
                    type="monotone" 
                    dataKey="volumeScore" 
                    stroke="#10b981" 
                    strokeWidth={2}
                    name="Volume"
                    dot={{ fill: '#10b981' }}
                  />
                  <Line 
                    type="monotone" 
                    dataKey="severityScore" 
                    stroke="#f59e0b" 
                    strokeWidth={2}
                    name="Severity"
                    dot={{ fill: '#f59e0b' }}
                  />
                  <Line 
                    type="monotone" 
                    dataKey="recencyScore" 
                    stroke="#8b5cf6" 
                    strokeWidth={2}
                    name="Recency"
                    dot={{ fill: '#8b5cf6' }}
                  />
                </LineChart>
              </ResponsiveContainer>
            </div>
          </div>

          {/* Status Timeline */}
          <div className="rounded-2xl border border-slate-800 bg-slate-900/70 p-5">
            <h2 className="mb-4 flex items-center gap-2 font-semibold">
              <Clock className="h-4 w-4 text-cyan-400" />
              Status Timeline
            </h2>
            <div className="flex flex-wrap gap-2">
              {history.map((entry, index) => (
                <div
                  key={entry.history_id}
                  className={`rounded px-3 py-2 text-xs font-semibold ${getStatusColor(entry.status)}`}
                  title={`${new Date(entry.run_timestamp).toLocaleString()}: ${entry.status}`}
                >
                  {entry.status}
                </div>
              ))}
            </div>
          </div>
        </div>
      )}

      {history.length === 0 && (
        <div className="rounded-2xl border border-slate-800 bg-slate-900/70 p-8 text-center text-slate-400">
          No history data available for this hotspot yet
        </div>
      )}
    </div>
  );
}

export default function HotspotDetailPage({ params }: { params: { hotspot_id: string } }) {
  return <AppShell><HotspotDetailInner hotspot_id={params.hotspot_id} /></AppShell>;
}
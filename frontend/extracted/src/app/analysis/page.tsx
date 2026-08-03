"use client";

import { useState } from "react";
import AppShell from "@/components/AppShell";
import { api } from "@/lib/client";
import {
  BrainCircuit,
  TrendingUp,
  TrendingDown,
  Minus,
  AlertTriangle,
  Clock,
  MapPin,
  BarChart3,
  ShieldAlert,
  Lightbulb,
  Download,
  Loader2,
  Calendar,
  AlertCircle,
  CheckCircle2,
} from "lucide-react";

type Report = {
  generatedAt: string;
  period: string;
  summary: {
    totalIncidents: number;
    activeHotspots: number;
    resolutionRate: number;
    mostDangerousTime: string;
    mostDangerousDay: string;
    mostReportedType: string;
    trendDirection: "rising" | "falling" | "stable";
    trendPercent: number;
  };
  priorityBreakdown: Record<string, number>;
  statusBreakdown: Record<string, number>;
  timeAnalysis: {
    hourlyDistribution: { hour: number; count: number }[];
    peakHours: string;
    quietHours: string;
    weekdayDistribution: { day: string; count: number }[];
    weekendVsWeekday: { weekendPct: number; weekdayPct: number };
  };
  geographicAnalysis: {
    topSuburbs: { name: string; count: number; riskLevel: string }[];
    emergingHotspots: { name: string; count: number; trend: string }[];
    safestSuburbs: { name: string; count: number }[];
    geographicSpread: string;
  };
  crimeTypeAnalysis: {
    topTypes: { type: string; count: number; trend: string }[];
    shifts: { type: string; change: string }[];
    dominantPattern: string;
  };
  hotspotCorrelation: {
    topHotspots: { lat: number; lng: number; level: string; topTypes: string[]; count: number; weight: number }[];
    hotspotDensity: string;
    clusterSummary: string;
  };
  riskForecast: {
    nextWeekRisk: string;
    confidence: number;
    factors: string[];
    predictedHotspotAreas: string[];
  };
  recommendations: {
    priority: string;
    action: string;
    rationale: string;
    timeframe: string;
  }[];
  narrative: string;
};

const RISK_BADGE: Record<string, string> = {
  critical: "bg-red-600 text-white",
  high: "bg-orange-500 text-white",
  medium: "bg-yellow-500 text-slate-900",
  low: "bg-green-600 text-white",
};

const PRIORITY_ICON: Record<string, React.ReactNode> = {
  critical: <AlertTriangle className="h-4 w-4 text-red-400" />,
  high: <AlertTriangle className="h-4 w-4 text-orange-400" />,
  medium: <AlertCircle className="h-4 w-4 text-yellow-400" />,
  low: <CheckCircle2 className="h-4 w-4 text-green-400" />,
};

function AnalysisInner() {
  const [periodDays, setPeriodDays] = useState(30);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [report, setReport] = useState<Report | null>(null);

  async function generate() {
    setLoading(true);
    setError(null);
    try {
      const res = await api<{ report: Report }>("/api/analysis/report", {
        method: "POST",
        body: JSON.stringify({ periodDays }),
      });
      setReport(res.report);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Analysis failed");
    } finally {
      setLoading(false);
    }
  }

  function downloadReport() {
    if (!report) return;
    const blob = new Blob([report.narrative], { type: "text/plain" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `crime-analysis-${report.generatedAt.split("T")[0]}.txt`;
    a.click();
    URL.revokeObjectURL(url);
  }

  const TrendIcon =
    report?.summary.trendDirection === "rising"
      ? TrendingUp
      : report?.summary.trendDirection === "falling"
      ? TrendingDown
      : Minus;

  const trendColor =
    report?.summary.trendDirection === "rising"
      ? "text-red-400"
      : report?.summary.trendDirection === "falling"
      ? "text-green-400"
      : "text-yellow-400";

  return (
    <div className="overflow-auto p-4 md:p-8">
      <div className="mb-6 flex flex-wrap items-center justify-between gap-3">
        <div>
          <h1 className="flex items-center gap-2 text-2xl font-bold">
            <BrainCircuit className="h-7 w-7 text-purple-400" />
            AI Crime Analysis
          </h1>
          <p className="text-sm text-slate-400">
            Advanced crime intelligence and predictive analytics for Harare
          </p>
        </div>
        <div className="flex items-center gap-2">
          <select
            value={periodDays}
            onChange={(e) => setPeriodDays(Number(e.target.value))}
            className="rounded-lg border border-slate-700 bg-slate-800 px-3 py-2 text-sm"
          >
            <option value={7}>Last 7 days</option>
            <option value={14}>Last 14 days</option>
            <option value={30}>Last 30 days</option>
            <option value={60}>Last 60 days</option>
            <option value={90}>Last 90 days</option>
          </select>
          <button
            onClick={generate}
            disabled={loading}
            className="flex items-center gap-2 rounded-lg bg-purple-600 px-4 py-2 text-sm font-semibold hover:bg-purple-500 disabled:opacity-50"
          >
            {loading ? (
              <Loader2 className="h-4 w-4 animate-spin" />
            ) : (
              <BrainCircuit className="h-4 w-4" />
            )}
            {loading ? "Analysing…" : "Run Analysis"}
          </button>
          {report && (
            <button
              onClick={downloadReport}
              className="flex items-center gap-2 rounded-lg border border-slate-700 bg-slate-800 px-4 py-2 text-sm font-semibold hover:bg-slate-700"
            >
              <Download className="h-4 w-4" />
              Export
            </button>
          )}
        </div>
      </div>

      {error && (
        <div className="mb-4 rounded-lg bg-red-500/15 px-4 py-3 text-sm text-red-300">
          {error}
        </div>
      )}

      {!report && !loading && !error && (
        <div className="flex flex-col items-center justify-center gap-4 rounded-2xl border border-slate-800 bg-slate-900/60 py-20 text-center">
          <BrainCircuit className="h-16 w-16 text-slate-600" />
          <div>
            <h2 className="text-lg font-semibold text-slate-300">
              Generate an AI Analysis Report
            </h2>
            <p className="mt-1 max-w-md text-sm text-slate-500">
              Select a time period and run the analysis engine to generate a
              comprehensive crime intelligence report with hotspot
              correlations, temporal patterns, geographic breakdowns, risk
              forecasts, and strategic recommendations.
            </p>
          </div>
        </div>
      )}

      {loading && (
        <div className="flex flex-col items-center justify-center gap-4 rounded-2xl border border-slate-800 bg-slate-900/60 py-20 text-center">
          <Loader2 className="h-12 w-12 animate-spin text-purple-400" />
          <div className="text-sm text-slate-400">
            Running intelligence analysis across {periodDays} days of data…
          </div>
        </div>
      )}

      {report && (
        <div className="space-y-6">
          {/* SUMMARY CARDS */}
          <div className="grid grid-cols-2 gap-4 md:grid-cols-3 lg:grid-cols-6">
            <MiniCard
              label="Incidents"
              value={report.summary.totalIncidents}
              icon={<BarChart3 className="h-5 w-5 text-blue-400" />}
            />
            <MiniCard
              label="Hotspots"
              value={report.summary.activeHotspots}
              icon={<MapPin className="h-5 w-5 text-red-400" />}
            />
            <MiniCard
              label="Resolution"
              value={`${report.summary.resolutionRate}%`}
              icon={<CheckCircle2 className="h-5 w-5 text-green-400" />}
            />
            <MiniCard
              label="Trend"
              value={`${report.summary.trendPercent > 0 ? "+" : ""}${report.summary.trendPercent}%`}
              icon={<TrendIcon className={`h-5 w-5 ${trendColor}`} />}
            />
            <MiniCard
              label="Peak time"
              value={report.summary.mostDangerousTime}
              icon={<Clock className="h-5 w-5 text-yellow-400" />}
            />
            <MiniCard
              label="Top crime"
              value={report.summary.mostReportedType}
              icon={<AlertTriangle className="h-5 w-5 text-orange-400" />}
              small
            />
          </div>

          {/* NARRATIVE */}
          <div className="rounded-2xl border border-slate-800 bg-slate-900/60 p-5">
            <h2 className="mb-3 flex items-center gap-2 text-sm font-semibold text-slate-300">
              <BrainCircuit className="h-4 w-4 text-purple-400" />
              Executive Summary
            </h2>
            <pre className="whitespace-pre-wrap font-sans text-sm leading-relaxed text-slate-300">
              {report.narrative}
            </pre>
          </div>

          {/* GRID: Risk + Time */}
          <div className="grid gap-4 lg:grid-cols-2">
            {/* RISK FORECAST */}
            <div className="rounded-2xl border border-slate-800 bg-slate-900/60 p-5">
              <h2 className="mb-3 flex items-center gap-2 text-sm font-semibold text-slate-300">
                <ShieldAlert className="h-4 w-4 text-red-400" />
                Risk Forecast
              </h2>
              <div className="mb-3 flex items-center gap-3">
                <span
                  className={`rounded-full px-4 py-1.5 text-sm font-bold uppercase ${
                    RISK_BADGE[report.riskForecast.nextWeekRisk]
                  }`}
                >
                  {report.riskForecast.nextWeekRisk}
                </span>
                <span className="text-sm text-slate-400">
                  Confidence: {report.riskForecast.confidence}%
                </span>
              </div>
              <div className="mt-3 space-y-1.5">
                <p className="text-xs font-medium text-slate-400">
                  Contributing factors:
                </p>
                {report.riskForecast.factors.map((f, i) => (
                  <div
                    key={i}
                    className="flex items-start gap-2 rounded-lg bg-slate-800/50 px-3 py-2 text-sm text-slate-300"
                  >
                    <AlertTriangle className="mt-0.5 h-3.5 w-3.5 shrink-0 text-yellow-400" />
                    {f}
                  </div>
                ))}
              </div>
              <div className="mt-3">
                <p className="text-xs font-medium text-slate-400">
                  Areas to monitor:
                </p>
                <div className="mt-1 flex flex-wrap gap-1.5">
                  {report.riskForecast.predictedHotspotAreas.map((a) => (
                    <span
                      key={a}
                      className="rounded-full bg-red-500/15 px-3 py-1 text-xs text-red-300"
                    >
                      {a}
                    </span>
                  ))}
                </div>
              </div>
            </div>

            {/* TIME ANALYSIS */}
            <div className="rounded-2xl border border-slate-800 bg-slate-900/60 p-5">
              <h2 className="mb-3 flex items-center gap-2 text-sm font-semibold text-slate-300">
                <Clock className="h-4 w-4 text-blue-400" />
                Temporal Analysis
              </h2>

              {/* Hourly heatmap */}
              <div className="mb-4">
                <p className="mb-2 text-xs text-slate-400">Hourly distribution</p>
                <div className="flex h-28 items-end gap-1">
                  {report.timeAnalysis.hourlyDistribution.map((h) => {
                    const max = Math.max(
                      ...report.timeAnalysis.hourlyDistribution.map(
                        (x) => x.count
                      ),
                      1
                    );
                    const pct = (h.count / max) * 100;
                    const intense =
                      pct > 70
                        ? "bg-red-500"
                        : pct > 40
                        ? "bg-orange-500"
                        : "bg-slate-600";
                    return (
                      <div
                        key={h.hour}
                        className="flex flex-1 flex-col items-center gap-1"
                        title={`${h.hour}:00 — ${h.count} incidents`}
                      >
                        <div
                          className={`w-full rounded-t ${intense}`}
                          style={{
                            height: `${Math.max(pct, 3)}%`,
                          }}
                        />
                        {h.hour % 4 === 0 && (
                          <span className="text-[9px] text-slate-500">
                            {String(h.hour).padStart(2, "0")}
                          </span>
                        )}
                      </div>
                    );
                  })}
                </div>
              </div>

              <div className="grid grid-cols-2 gap-3 text-sm">
                <div className="rounded-lg bg-slate-800/50 p-3">
                  <p className="mb-1 text-xs text-slate-400">Peak hours</p>
                  <p className="font-semibold text-red-300">
                    {report.timeAnalysis.peakHours}
                  </p>
                </div>
                <div className="rounded-lg bg-slate-800/50 p-3">
                  <p className="mb-1 text-xs text-slate-400">Quiet hours</p>
                  <p className="font-semibold text-green-300">
                    {report.timeAnalysis.quietHours}
                  </p>
                </div>
                <div className="rounded-lg bg-slate-800/50 p-3">
                  <p className="mb-1 text-xs text-slate-400">Most active day</p>
                  <p className="font-semibold text-yellow-300">
                    {report.summary.mostDangerousDay}
                  </p>
                </div>
                <div className="rounded-lg bg-slate-800/50 p-3">
                  <p className="mb-1 text-xs text-slate-400">Weekend split</p>
                  <p className="font-semibold">
                    <span className="text-red-300">
                      {report.timeAnalysis.weekendVsWeekday.weekendPct}%
                    </span>{" "}
                    /{" "}
                    <span className="text-blue-300">
                      {report.timeAnalysis.weekendVsWeekday.weekdayPct}%
                    </span>
                  </p>
                </div>
              </div>
            </div>
          </div>

          {/* GEOGRAPHIC + CRIME TYPE */}
          <div className="grid gap-4 lg:grid-cols-2">
            <div className="rounded-2xl border border-slate-800 bg-slate-900/60 p-5">
              <h2 className="mb-3 flex items-center gap-2 text-sm font-semibold text-slate-300">
                <MapPin className="h-4 w-4 text-green-400" />
                Geographic Breakdown
              </h2>
              <p className="mb-3 text-sm text-slate-400">
                {report.geographicAnalysis.geographicSpread}
              </p>
              {report.geographicAnalysis.emergingHotspots.length > 0 && (
                <div className="mb-3">
                  <p className="mb-1 text-xs font-medium text-orange-400">
                    Emerging hotspots:
                  </p>
                  {report.geographicAnalysis.emergingHotspots.map((h) => (
                    <div
                      key={h.name}
                      className="flex items-center justify-between py-1 text-sm"
                    >
                      <span className="text-slate-300">{h.name}</span>
                      <span className="text-orange-400">
                        {h.count} ({h.trend})
                      </span>
                    </div>
                  ))}
                </div>
              )}
              <p className="mb-2 text-xs font-medium text-slate-400">
                Highest risk areas:
              </p>
              {report.geographicAnalysis.topSuburbs.slice(0, 8).map((s) => (
                <div
                  key={s.name}
                  className="flex items-center justify-between rounded-lg bg-slate-800/50 px-3 py-2 text-sm"
                >
                  <div className="flex items-center gap-2">
                    <span
                      className={`inline-block h-2 w-2 rounded-full ${
                        s.riskLevel === "high"
                          ? "bg-red-500"
                          : s.riskLevel === "medium"
                          ? "bg-orange-500"
                          : "bg-yellow-500"
                      }`}
                    />
                    <span className="text-slate-300">{s.name}</span>
                  </div>
                  <span className="font-semibold text-slate-400">
                    {s.count}
                  </span>
                </div>
              ))}
            </div>

            <div className="rounded-2xl border border-slate-800 bg-slate-900/60 p-5">
              <h2 className="mb-3 flex items-center gap-2 text-sm font-semibold text-slate-300">
                <BarChart3 className="h-4 w-4 text-blue-400" />
                Crime Type Analysis
              </h2>
              <p className="mb-3 text-sm text-slate-400">
                {report.crimeTypeAnalysis.dominantPattern}
              </p>
              {report.crimeTypeAnalysis.topTypes.map((t) => (
                <div
                  key={t.type}
                  className="flex items-center justify-between rounded-lg bg-slate-800/50 px-3 py-2 text-sm"
                >
                  <span className="text-slate-300">{t.type}</span>
                  <div className="flex items-center gap-2">
                    <span className="font-semibold text-slate-200">
                      {t.count}
                    </span>
                    <span
                      className={`text-xs ${
                        t.trend.includes("↑")
                          ? "text-red-400"
                          : t.trend.includes("↓")
                          ? "text-green-400"
                          : "text-slate-500"
                      }`}
                    >
                      {t.trend}
                    </span>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* RECOMMENDATIONS */}
          <div className="rounded-2xl border border-slate-800 bg-slate-900/60 p-5">
            <h2 className="mb-3 flex items-center gap-2 text-sm font-semibold text-slate-300">
              <Lightbulb className="h-4 w-4 text-yellow-400" />
              Strategic Recommendations
            </h2>
            <div className="grid gap-3 md:grid-cols-2">
              {report.recommendations.map((rec, i) => (
                <div
                  key={i}
                  className="rounded-xl border border-slate-700 bg-slate-800/40 p-4"
                >
                  <div className="mb-2 flex items-start gap-2">
                    {PRIORITY_ICON[rec.priority] ?? null}
                    <div>
                      <p className="text-sm font-semibold text-slate-200">
                        {rec.action}
                      </p>
                      <p className="mt-1 text-xs leading-relaxed text-slate-400">
                        {rec.rationale}
                      </p>
                    </div>
                  </div>
                  <div className="flex items-center gap-2">
                    <span
                      className={`rounded-full px-2.5 py-0.5 text-[10px] font-bold uppercase ${
                        RISK_BADGE[rec.priority]
                      }`}
                    >
                      {rec.priority}
                    </span>
                    <span className="flex items-center gap-1 text-xs text-slate-500">
                      <Calendar className="h-3 w-3" />
                      {rec.timeframe}
                    </span>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

function MiniCard({
  label,
  value,
  icon,
  small,
}: {
  label: string;
  value: number | string;
  icon: React.ReactNode;
  small?: boolean;
}) {
  return (
    <div className="rounded-xl border border-slate-800 bg-slate-900/60 p-4">
      <div className="mb-1">{icon}</div>
      <div
        className={`font-bold ${small ? "text-base" : "text-2xl"}`}
      >
        {value}
      </div>
      <div className="text-[10px] text-slate-400">{label}</div>
    </div>
  );
}

export default function AnalysisPage() {
  return (
    <AppShell>
      <AnalysisInner />
    </AppShell>
  );
}

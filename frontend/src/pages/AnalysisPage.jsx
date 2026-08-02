/**
 * AnalysisPage — mirrors prototype app/analysis/page.tsx
 *
 * AI Crime Analysis with:
 *  - Period selector (7/14/30/60/90 days)
 *  - "Run Analysis" button → POST /api/v1/analysis/report
 *  - Summary mini-cards, narrative, risk forecast, temporal, geographic,
 *    crime-type, and strategic recommendations sections
 *  - Export button (downloads narrative as .txt)
 */
import { useState } from "react";
import {
  BrainCircuit, TrendingUp, TrendingDown, Minus, AlertTriangle,
  Clock, MapPin, BarChart3, ShieldAlert, Lightbulb, Download,
  Loader2, Calendar, AlertCircle, CheckCircle2,
} from "lucide-react";
import { api } from "../lib/client";

const API = import.meta.env.VITE_API_BASE_URL || "/api/v1";

const RISK_BADGE = {
  critical: { bg: "#dc2626", color: "#fff" },
  high:     { bg: "#f97316", color: "#fff" },
  medium:   { bg: "#eab308", color: "#1e293b" },
  low:      { bg: "#16a34a", color: "#fff" },
};

const PRIORITY_ICON = {
  critical: <AlertTriangle size={16} color="#f87171" />,
  high:     <AlertTriangle size={16} color="#fb923c" />,
  medium:   <AlertCircle  size={16} color="#facc15" />,
  low:      <CheckCircle2 size={16} color="#4ade80" />,
};

function MiniCard({ label, value, icon, small }) {
  return (
    <div className="cw-mini-card">
      <div className="cw-mini-card-icon">{icon}</div>
      <div className="cw-mini-card-value" style={{ fontSize: small ? "1rem" : "1.5rem" }}>
        {value}
      </div>
      <div className="cw-mini-card-label">{label}</div>
    </div>
  );
}

export default function AnalysisPage() {
  const [periodDays, setPeriodDays] = useState(30);
  const [loading,    setLoading]    = useState(false);
  const [error,      setError]      = useState(null);
  const [report,     setReport]     = useState(null);

  async function generate() {
    setLoading(true);
    setError(null);
    try {
      const res = await api(`${API}/analysis/report`, {
        method: "POST",
        body: JSON.stringify({ periodDays }),
      });
      setReport(res.report ?? res);
    } catch (e) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  }

  function downloadReport() {
    if (!report) return;
    const blob = new Blob([report.narrative ?? JSON.stringify(report, null, 2)], { type: "text/plain" });
    const url  = URL.createObjectURL(blob);
    const a    = document.createElement("a");
    a.href     = url;
    a.download = `crime-analysis-${(report.generatedAt ?? new Date().toISOString()).split("T")[0]}.txt`;
    a.click();
    URL.revokeObjectURL(url);
  }

  const summary = report?.summary ?? {};
  const TrendIcon =
    summary.trendDirection === "rising"  ? TrendingUp  :
    summary.trendDirection === "falling" ? TrendingDown : Minus;
  const trendColor =
    summary.trendDirection === "rising"  ? "#f87171"   :
    summary.trendDirection === "falling" ? "#4ade80"   : "#facc15";

  const riskBadge = RISK_BADGE[(report?.riskForecast?.nextWeekRisk ?? "").toLowerCase()] ?? RISK_BADGE.low;

  return (
    <div className="cw-analysis-page">
      {/* Header */}
      <div className="cw-analysis-header">
        <div>
          <h1 className="cw-analysis-title">
            <BrainCircuit size={28} color="#c084fc" />
            AI Crime Analysis
          </h1>
          <p style={{ fontSize: "0.875rem", color: "#94a3b8", marginTop: "4px" }}>
            Advanced crime intelligence and predictive analytics for Harare
          </p>
        </div>
        <div className="cw-analysis-actions">
          <select
            value={periodDays}
            onChange={(e) => setPeriodDays(Number(e.target.value))}
            className="cw-analysis-select"
          >
            <option value={7}>Last 7 days</option>
            <option value={14}>Last 14 days</option>
            <option value={30}>Last 30 days</option>
            <option value={60}>Last 60 days</option>
            <option value={90}>Last 90 days</option>
          </select>
          <button onClick={generate} disabled={loading} className="cw-purple-btn">
            {loading ? <Loader2 size={16} className="cw-spin" /> : <BrainCircuit size={16} />}
            {loading ? "Analysing…" : "Run Analysis"}
          </button>
          {report && (
            <button onClick={downloadReport} className="cw-outline-btn">
              <Download size={16} />
              Export
            </button>
          )}
        </div>
      </div>

      {error && <div className="cw-error-box">{error}</div>}

      {/* Empty state */}
      {!report && !loading && !error && (
        <div className="cw-empty-state">
          <BrainCircuit size={64} color="#334155" />
          <div>
            <h2>Generate an AI Analysis Report</h2>
            <p>
              Select a time period and run the analysis engine to generate a comprehensive
              crime intelligence report with hotspot correlations, temporal patterns,
              geographic breakdowns, risk forecasts, and strategic recommendations.
            </p>
          </div>
        </div>
      )}

      {/* Loading state */}
      {loading && (
        <div className="cw-loading-state">
          <Loader2 size={48} color="#c084fc" className="cw-spin" />
          <div>Running intelligence analysis across {periodDays} days of data…</div>
        </div>
      )}

      {/* Report */}
      {report && (
        <div style={{ display: "flex", flexDirection: "column", gap: "24px" }}>
          {/* Summary mini-cards */}
          <div className="cw-mini-grid">
            <MiniCard
              label="Incidents"
              value={summary.totalIncidents ?? 0}
              icon={<BarChart3 size={20} color="#60a5fa" />}
            />
            <MiniCard
              label="Hotspots"
              value={summary.activeHotspots ?? 0}
              icon={<MapPin size={20} color="#f87171" />}
            />
            <MiniCard
              label="Resolution"
              value={`${summary.resolutionRate ?? 0}%`}
              icon={<CheckCircle2 size={20} color="#4ade80" />}
            />
            <MiniCard
              label="Trend"
              value={`${(summary.trendPercent ?? 0) > 0 ? "+" : ""}${summary.trendPercent ?? 0}%`}
              icon={<TrendIcon size={20} color={trendColor} />}
            />
            <MiniCard
              label="Peak time"
              value={summary.mostDangerousTime ?? "—"}
              icon={<Clock size={20} color="#facc15" />}
            />
            <MiniCard
              label="Top crime"
              value={summary.mostReportedType ?? "—"}
              icon={<AlertTriangle size={20} color="#fb923c" />}
              small
            />
          </div>

          {/* Narrative */}
          {report.narrative && (
            <div className="cw-panel">
              <div className="cw-panel-title">
                <BrainCircuit size={16} color="#c084fc" />
                Executive Summary
              </div>
              <pre className="cw-narrative">{report.narrative}</pre>
            </div>
          )}

          {/* Risk + Time */}
          <div className="cw-grid-2">
            {/* Risk Forecast */}
            {report.riskForecast && (
              <div className="cw-panel">
                <div className="cw-panel-title">
                  <ShieldAlert size={16} color="#f87171" />
                  Risk Forecast
                </div>
                <div style={{ display: "flex", alignItems: "center", gap: "12px", marginBottom: "12px" }}>
                  <span
                    className="cw-risk-badge"
                    style={{ background: riskBadge.bg, color: riskBadge.color }}
                  >
                    {report.riskForecast.nextWeekRisk}
                  </span>
                  <span style={{ fontSize: "0.875rem", color: "#94a3b8" }}>
                    Confidence: {report.riskForecast.confidence}%
                  </span>
                </div>
                {(report.riskForecast.factors ?? []).map((f, i) => (
                  <div key={i} className="cw-factor-item">
                    <AlertTriangle size={14} color="#facc15" style={{ flexShrink: 0, marginTop: 1 }} />
                    {f}
                  </div>
                ))}
                {(report.riskForecast.predictedHotspotAreas ?? []).length > 0 && (
                  <div style={{ marginTop: "8px" }}>
                    <p style={{ fontSize: "0.75rem", color: "#94a3b8", marginBottom: "6px" }}>Areas to monitor:</p>
                    <div style={{ display: "flex", flexWrap: "wrap", gap: "6px" }}>
                      {report.riskForecast.predictedHotspotAreas.map((a) => (
                        <span key={a} className="cw-tag cw-tag-red">{a}</span>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            )}

            {/* Temporal Analysis */}
            {report.timeAnalysis && (
              <div className="cw-panel">
                <div className="cw-panel-title">
                  <Clock size={16} color="#60a5fa" />
                  Temporal Analysis
                </div>
                {/* Hourly distribution bars */}
                {(report.timeAnalysis.hourlyDistribution ?? []).length > 0 && (
                  <div style={{ marginBottom: "16px" }}>
                    <p style={{ fontSize: "0.75rem", color: "#94a3b8", marginBottom: "8px" }}>Hourly distribution</p>
                    <div className="cw-hour-chart">
                      {report.timeAnalysis.hourlyDistribution.map((h) => {
                        const max = Math.max(
                          ...report.timeAnalysis.hourlyDistribution.map((x) => x.count),
                          1
                        );
                        const pct     = (h.count / max) * 100;
                        const barBg   = pct > 70 ? "#ef4444" : pct > 40 ? "#f97316" : "#475569";
                        return (
                          <div key={h.hour} className="cw-hour-col" title={`${h.hour}:00 — ${h.count} incidents`}>
                            <div
                              className="cw-hour-bar"
                              style={{ height: `${Math.max(pct, 3)}%`, background: barBg }}
                            />
                            {h.hour % 4 === 0 && (
                              <span className="cw-hour-label">{String(h.hour).padStart(2, "0")}</span>
                            )}
                          </div>
                        );
                      })}
                    </div>
                  </div>
                )}
                <div className="cw-quad-grid">
                  <div className="cw-quad-cell">
                    <p className="cw-quad-cell-label">Peak hours</p>
                    <p style={{ fontWeight: 600, color: "#fca5a5" }}>{report.timeAnalysis.peakHours ?? "—"}</p>
                  </div>
                  <div className="cw-quad-cell">
                    <p className="cw-quad-cell-label">Quiet hours</p>
                    <p style={{ fontWeight: 600, color: "#86efac" }}>{report.timeAnalysis.quietHours ?? "—"}</p>
                  </div>
                  <div className="cw-quad-cell">
                    <p className="cw-quad-cell-label">Most active day</p>
                    <p style={{ fontWeight: 600, color: "#fde047" }}>{summary.mostDangerousDay ?? "—"}</p>
                  </div>
                  <div className="cw-quad-cell">
                    <p className="cw-quad-cell-label">Weekend split</p>
                    <p style={{ fontWeight: 600 }}>
                      <span style={{ color: "#fca5a5" }}>{report.timeAnalysis.weekendVsWeekday?.weekendPct ?? "—"}%</span>
                      {" / "}
                      <span style={{ color: "#93c5fd" }}>{report.timeAnalysis.weekendVsWeekday?.weekdayPct ?? "—"}%</span>
                    </p>
                  </div>
                </div>
              </div>
            )}
          </div>

          {/* Geographic + Crime Types */}
          <div className="cw-grid-2">
            {report.geographicAnalysis && (
              <div className="cw-panel">
                <div className="cw-panel-title">
                  <MapPin size={16} color="#4ade80" />
                  Geographic Breakdown
                </div>
                <p style={{ fontSize: "0.875rem", color: "#94a3b8", marginBottom: "12px" }}>
                  {report.geographicAnalysis.geographicSpread}
                </p>
                {(report.geographicAnalysis.topSuburbs ?? []).slice(0, 8).map((s) => {
                  const dotBg = s.riskLevel === "high" ? "#ef4444" : s.riskLevel === "medium" ? "#f97316" : "#eab308";
                  return (
                    <div key={s.name} className="cw-data-row">
                      <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
                        <span style={{ display: "inline-block", width: 8, height: 8, borderRadius: "50%", background: dotBg }} />
                        <span style={{ color: "#cbd5e1" }}>{s.name}</span>
                      </div>
                      <span style={{ fontWeight: 600, color: "#94a3b8" }}>{s.count}</span>
                    </div>
                  );
                })}
              </div>
            )}

            {report.crimeTypeAnalysis && (
              <div className="cw-panel">
                <div className="cw-panel-title">
                  <BarChart3 size={16} color="#60a5fa" />
                  Crime Type Analysis
                </div>
                <p style={{ fontSize: "0.875rem", color: "#94a3b8", marginBottom: "12px" }}>
                  {report.crimeTypeAnalysis.dominantPattern}
                </p>
                {(report.crimeTypeAnalysis.topTypes ?? []).map((t) => (
                  <div key={t.type} className="cw-data-row">
                    <span style={{ color: "#cbd5e1" }}>{t.type}</span>
                    <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
                      <span style={{ fontWeight: 600 }}>{t.count}</span>
                      <span style={{
                        fontSize: "0.75rem",
                        color: t.trend?.includes("↑") ? "#f87171"
                              : t.trend?.includes("↓") ? "#4ade80"
                              : "#475569",
                      }}>
                        {t.trend}
                      </span>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* Recommendations */}
          {(report.recommendations ?? []).length > 0 && (
            <div className="cw-panel">
              <div className="cw-panel-title">
                <Lightbulb size={16} color="#facc15" />
                Strategic Recommendations
              </div>
              <div className="cw-rec-grid">
                {report.recommendations.map((rec, i) => {
                  const badge = RISK_BADGE[(rec.priority ?? "").toLowerCase()] ?? RISK_BADGE.low;
                  return (
                    <div key={i} className="cw-rec-card">
                      <div className="cw-rec-head">
                        {PRIORITY_ICON[(rec.priority ?? "").toLowerCase()] ?? null}
                        <div>
                          <p className="cw-rec-action">{rec.action}</p>
                          <p className="cw-rec-rationale">{rec.rationale}</p>
                        </div>
                      </div>
                      <div className="cw-rec-foot">
                        <span
                          className="cw-risk-badge"
                          style={{ background: badge.bg, color: badge.color, fontSize: "0.625rem", padding: "2px 10px" }}
                        >
                          {rec.priority}
                        </span>
                        <span className="cw-rec-time">
                          <Calendar size={12} />
                          {rec.timeframe}
                        </span>
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

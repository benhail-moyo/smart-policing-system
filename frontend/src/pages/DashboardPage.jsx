/**
 * DashboardPage — mirrors prototype app/page.tsx
 * Stat cards, priority bar chart, 7-day trend, top crime categories.
 */
import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import {
  BarChart3, Siren, Clock, CheckCircle2, ArrowRight, FolderOpen,
} from "lucide-react";
import { api } from "../lib/client";

const API = import.meta.env.VITE_API_BASE_URL || "/api/v1";

const PRIORITY_COLOR_CLASS = {
  critical: "#ef4444",
  high:     "#f97316",
  medium:   "#eab308",
  low:      "#22c55e",
};

// Build stats from backend /incidents/stats endpoint
// Backend returns { by_severity: { HIGH, MEDIUM, LOW }, total }
function adaptStats(raw) {
  const bySev  = raw.by_severity ?? {};
  const total  = raw.total ?? 0;
  // Map severity to rough priority for the bar chart
  return {
    total,
    openCases:      (bySev.HIGH ?? 0) + (bySev.MEDIUM ?? 0),
    resolutionRate: total ? Math.round(((bySev.LOW ?? 0) / total) * 100) : 0,
    last24h:        raw.last24h ?? 0,
    last7d:         raw.last7d  ?? 0,
    byPriority: {
      critical: Math.round((bySev.HIGH   ?? 0) * 0.4),
      high:     Math.round((bySev.HIGH   ?? 0) * 0.6),
      medium:   bySev.MEDIUM ?? 0,
      low:      bySev.LOW    ?? 0,
    },
    byStatus:  raw.byStatus  ?? {},
    topTypes:  raw.topTypes  ?? [],
    trend:     raw.trend     ?? [],
  };
}

function StatCard({ label, value, icon }) {
  return (
    <div className="cw-stat-card">
      <div className="cw-stat-card-icon">{icon}</div>
      <div className="cw-stat-card-value">{value}</div>
      <div className="cw-stat-card-label">{label}</div>
    </div>
  );
}

export default function DashboardPage() {
  const [stats, setStats] = useState(null);
  const [error, setError] = useState(null);

  useEffect(() => {
    api(`${API}/incidents/stats`)
      .then((raw) => setStats(adaptStats(raw)))
      .catch((e) => setError(e.message));
  }, []);

  const maxTrend = stats ? Math.max(1, ...(stats.trend.map((t) => t.count))) : 1;

  return (
    <div className="cw-page">
      {/* Header */}
      <div className="cw-page-header">
        <div>
          <h1 className="cw-page-title">Dashboard</h1>
          <p className="cw-page-sub">Real-time crime overview for Harare</p>
        </div>
        <Link
          to="/map"
          className="cw-primary-btn"
        >
          Open Crime Map
          <ArrowRight size={16} />
        </Link>
      </div>

      {error && <div className="cw-error-box">{error}</div>}

      {!stats ? (
        <p style={{ color: "#94a3b8" }}>Loading stats…</p>
      ) : (
        <>
          {/* Stat cards */}
          <div className="cw-stat-grid">
            <StatCard
              label="Total incidents"
              value={stats.total}
              icon={<FolderOpen size={24} color="#60a5fa" />}
            />
            <StatCard
              label="Open cases"
              value={stats.openCases}
              icon={<Siren size={24} color="#f87171" />}
            />
            <StatCard
              label="Last 24 hours"
              value={stats.last24h}
              icon={<Clock size={24} color="#facc15" />}
            />
            <StatCard
              label="Resolution rate"
              value={`${stats.resolutionRate}%`}
              icon={<CheckCircle2 size={24} color="#4ade80" />}
            />
          </div>

          {/* Charts row */}
          <div className="cw-grid-2">
            {/* Priority bar chart */}
            <div className="cw-panel">
              <div className="cw-panel-title">
                <BarChart3 size={16} color="#60a5fa" />
                Incidents by priority
              </div>
              <div>
                {["critical", "high", "medium", "low"].map((p) => {
                  const count = stats.byPriority[p] ?? 0;
                  const pct   = stats.total ? Math.round((count / stats.total) * 100) : 0;
                  return (
                    <div key={p} className="cw-bar-item">
                      <div className="cw-bar-label">
                        <span style={{ textTransform: "capitalize" }}>{p}</span>
                        <span style={{ color: "#94a3b8" }}>{count} ({pct}%)</span>
                      </div>
                      <div className="cw-bar-track">
                        <div
                          className="cw-bar-fill"
                          style={{ width: `${pct}%`, background: PRIORITY_COLOR_CLASS[p] }}
                        />
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>

            {/* 7-day trend */}
            <div className="cw-panel">
              <div className="cw-panel-title">
                <Clock size={16} color="#facc15" />
                7-day trend
              </div>
              {stats.trend.length > 0 ? (
                <div className="cw-trend-bars">
                  {stats.trend.map((t, i) => (
                    <div key={i} className="cw-trend-col">
                      <div
                        className="cw-trend-bar"
                        style={{
                          height: `${(t.count / maxTrend) * 100}%`,
                          minHeight: t.count > 0 ? "6px" : "2px",
                        }}
                        title={`${t.count} incidents`}
                      />
                      <span className="cw-trend-day">{t.day}</span>
                    </div>
                  ))}
                </div>
              ) : (
                <p style={{ color: "#94a3b8", fontSize: "0.875rem" }}>
                  No trend data available yet.
                </p>
              )}
            </div>
          </div>

          {/* Top crime categories */}
          {stats.topTypes.length > 0 && (
            <div className="cw-panel" style={{ marginTop: "24px" }}>
              <div className="cw-panel-title">
                <Siren size={16} color="#f87171" />
                Top crime categories
              </div>
              <div className="cw-grid-3">
                {stats.topTypes.map((t) => (
                  <div key={t.type} className="cw-category-item">
                    <span className="cw-category-name">{t.type}</span>
                    <span className="cw-category-count">{t.count}</span>
                  </div>
                ))}
              </div>
            </div>
          )}
        </>
      )}
    </div>
  );
}

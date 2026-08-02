/**
 * MapPage — mirrors prototype app/map/page.tsx
 *
 * Features:
 *  - Leaflet map with raw Leaflet (not react-leaflet)
 *  - Incidents (colour-coded by severity from GIS module)
 *  - Hotspots (coloured circles from DBSCAN analysis)
 *  - Patrol routes toggle
 *  - Time-period filter (all / 24h / 7d / 30d / custom)
 *  - Hour-of-day filter
 *  - "Run Hotspot Analysis" button (POST /api/v1/hotspots/analyze)
 *  - Legend overlay
 */
import { useEffect, useState, useCallback, useRef } from "react";
import {
  MapPin, Car, Zap, Filter, Calendar, Clock, Layers, Loader2,
} from "lucide-react";
import CrimeMap from "../components/map/CrimeMap";
import { api, getStoredUser, isPatrolAllowed } from "../lib/client";
import { PATROL_ROUTES } from "../lib/crime";

const API = import.meta.env.VITE_API_BASE_URL || "/api/v1";

const PERIOD_LABELS = [
  { value: "all",    label: "All time"     },
  { value: "24h",    label: "Last 24h"     },
  { value: "7d",     label: "Last 7 days"  },
  { value: "30d",    label: "Last 30 days" },
  { value: "custom", label: "Custom"       },
];

// Adapt backend incident to the shape CrimeMap expects.
// Backend to_dict() returns: { location: {lat, lng}, severity, category, ... }
function adaptIncident(i) {
  // location is a nested {lat, lng} object from to_dict()
  const lat = i.location?.lat ?? i.lat ?? i.location_lat ?? null;
  const lng = i.location?.lng ?? i.lng ?? i.location_lng ?? null;
  return {
    id:          i.id,
    type:        i.category ?? "Incident",
    description: i.triage_summary ?? i.raw_text ?? "",
    lat,
    lng,
    severity:    i.severity ?? "MEDIUM",
    priority:    severityToPriority(i.severity),
    status:      i.status ?? "",
    suburb:      i.location_description ?? "",
    createdAt:   i.created_at ?? i.createdAt ?? null,
  };
}

function severityToPriority(severity) {
  const map = { HIGH: "critical", MEDIUM: "medium", LOW: "low", CRITICAL: "critical" };
  return map[(severity ?? "").toUpperCase()] ?? "low";
}

// Adapt backend hotspot to the shape CrimeMap expects.
// Backend to_dict() returns: { centroid: {lat, lng}, risk_score, incident_count, dominant_category }
function adaptHotspot(h) {
  // centroid is a nested {lat, lng} object from Hotspot.to_dict()
  const lat = h.centroid?.lat ?? h.lat ?? h.latitude ?? null;
  const lng = h.centroid?.lng ?? h.lng ?? h.longitude ?? null;

  const riskScore = h.risk_score ?? h.riskScore ?? 0.5;
  // Backend risk_score formula: 0.4*volume + 0.4*severity + 0.2*recency → typically 0.1–1.0
  const level = riskScore >= 0.7 ? "high" : riskScore >= 0.45 ? "medium" : "low";
  const count = h.incident_count ?? h.count ?? 0;

  return {
    id:       h.id,
    lat,
    lng,
    count,
    weight:   riskScore,
    radius:   Math.min(1200, 350 + count * 60),
    level,
    topTypes: h.dominant_category ? [h.dominant_category] : (h.topTypes ?? []),
  };
}

function ToggleChip({ active, onClick, children }) {
  return (
    <button
      onClick={onClick}
      className={`cw-toggle-chip ${active ? "active" : "inactive"}`}
    >
      {children}
    </button>
  );
}

function LegendRow({ color, label }) {
  return (
    <div className="cw-legend-row">
      <span className="cw-legend-dot" style={{ background: color }} />
      <span>{label}</span>
    </div>
  );
}

export default function MapPage() {
  const [allIncidents, setAllIncidents] = useState([]);
  const [incidents,    setIncidents]    = useState([]);
  const [hotspots,     setHotspots]     = useState([]);
  const [routes,       setRoutes]       = useState([]);

  const [showIncidents, setShowIncidents] = useState(true);
  const [showRoutes,    setShowRoutes]    = useState(false);
  const [analyzing,     setAnalyzing]    = useState(false);
  const [msg,           setMsg]          = useState(null);
  const [error,         setError]        = useState(null);
  const [showFilters,   setShowFilters]  = useState(false);

  const [filter, setFilter] = useState({
    period:     "all",
    hourFrom:   "all",
    hourTo:     "all",
    customFrom: "",
    customTo:   "",
  });

  const canPatrol = isPatrolAllowed(getStoredUser());

  // ── Filter logic ────────────────────────────────────────────────────────
  const applyFilter = useCallback((raw) => {
    let filtered = [...raw];
    const now = Date.now();
    const getTs = (r) => r.createdAt ? new Date(r.createdAt).getTime() : 0;

    if (filter.period === "24h") {
      filtered = filtered.filter((r) => getTs(r) >= now - 86400000);
    } else if (filter.period === "7d") {
      filtered = filtered.filter((r) => getTs(r) >= now - 7 * 86400000);
    } else if (filter.period === "30d") {
      filtered = filtered.filter((r) => getTs(r) >= now - 30 * 86400000);
    } else if (filter.period === "custom" && (filter.customFrom || filter.customTo)) {
      if (filter.customFrom) {
        const from = new Date(filter.customFrom).getTime();
        filtered = filtered.filter((r) => getTs(r) >= from);
      }
      if (filter.customTo) {
        const to = new Date(filter.customTo).getTime() + 86400000;
        filtered = filtered.filter((r) => getTs(r) <= to);
      }
    }

    if (filter.hourFrom !== "all" || filter.hourTo !== "all") {
      const hf = filter.hourFrom !== "all" ? parseInt(filter.hourFrom, 10) : 0;
      const ht = filter.hourTo   !== "all" ? parseInt(filter.hourTo,   10) : 23;
      filtered = filtered.filter((r) => {
        if (!r.createdAt) return false;
        const h = new Date(r.createdAt).getHours();
        if (hf <= ht) return h >= hf && h <= ht;
        return h >= hf || h <= ht;
      });
    }

    setIncidents(filtered);
  }, [filter]);

  // ── Load data ───────────────────────────────────────────────────────────
  async function load() {
    const [incRes, hotRes] = await Promise.allSettled([
      api(`${API}/incidents/?limit=200`),
      api(`${API}/hotspots/`),
    ]);

    const rawInc  = incRes.status  === "fulfilled" ? (incRes.value.incidents  ?? []) : [];
    const rawHot  = hotRes.status  === "fulfilled" ? (Array.isArray(hotRes.value) ? hotRes.value : []) : [];

    const adapted = rawInc.map(adaptIncident).filter((i) => i.lat && i.lng);
    setAllIncidents(adapted);
    setHotspots(rawHot.map(adaptHotspot).filter((h) => h.lat && h.lng));
    // Use static patrol routes (same as prototype) — backend route compare is on PatrolPage
    setRoutes(PATROL_ROUTES);
  }

  useEffect(() => { load().catch((e) => setError(e.message)); }, []);
  useEffect(() => { applyFilter(allIncidents); }, [allIncidents, applyFilter]);

  // ── Run hotspot analysis ─────────────────────────────────────────────────
  async function runAnalysis() {
    setAnalyzing(true);
    setError(null);
    setMsg(null);
    try {
      const res = await api(`${API}/hotspots/analyze`, { method: "POST", body: JSON.stringify({ days_back: 30 }) });
      await load();
      setMsg(`Analysis complete: ${res.hotspots_generated ?? 0} hotspots from ${res.source_count ?? 0} incidents.`);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Analysis failed");
    } finally {
      setAnalyzing(false);
    }
  }

  const resetFilters = () => setFilter({ period: "all", hourFrom: "all", hourTo: "all", customFrom: "", customTo: "" });

  return (
    <div className="cw-map-page">
      {/* Top bar */}
      <div className="cw-map-topbar">
        <div>
          <div className="cw-map-title">Crime Map — Harare</div>
          <p className="cw-map-sub">
            {incidents.length} incidents · {hotspots.length} hotspots
            {filter.period !== "all" && (
              <span className="cw-map-sub-accent">(filtered from {allIncidents.length})</span>
            )}
          </p>
        </div>

        <div className="cw-map-controls">
          <ToggleChip active={showIncidents} onClick={() => setShowIncidents((v) => !v)}>
            <MapPin size={14} />
            Incidents
          </ToggleChip>

          <ToggleChip active={showRoutes} onClick={() => setShowRoutes((v) => !v)}>
            <Car size={14} />
            Patrol routes
          </ToggleChip>

          <button
            onClick={() => setShowFilters((v) => !v)}
            className={`cw-filter-btn ${showFilters ? "active" : "inactive"}`}
          >
            <Filter size={14} />
          </button>

          <button
            onClick={runAnalysis}
            disabled={analyzing || !canPatrol}
            title={canPatrol ? "Cluster incidents into hotspots" : "Only officers can run analysis"}
            className="cw-run-btn"
          >
            {analyzing
              ? <Loader2 size={16} className="cw-spin" />
              : <Zap size={16} />
            }
            {analyzing ? "Analysing…" : "Run Hotspot Analysis"}
          </button>
        </div>
      </div>

      {/* Filter bar */}
      {showFilters && (
        <div className="cw-filter-bar">
          <span className="cw-filter-label">
            <Calendar size={14} color="#94a3b8" />
            Period:
          </span>
          {PERIOD_LABELS.map((p) => (
            <button
              key={p.value}
              onClick={() => setFilter((f) => ({ ...f, period: p.value }))}
              className={`cw-period-btn ${filter.period === p.value ? "active" : "inactive"}`}
            >
              {p.label}
            </button>
          ))}

          <div className="cw-filter-divider" />

          <span className="cw-filter-label">
            <Clock size={14} color="#94a3b8" />
            Hour:
          </span>
          <select
            value={filter.hourFrom}
            onChange={(e) => setFilter((f) => ({ ...f, hourFrom: e.target.value }))}
            className="cw-filter-select"
          >
            <option value="all">Any start</option>
            {Array.from({ length: 24 }, (_, i) => (
              <option key={i} value={String(i)}>{String(i).padStart(2, "0")}:00</option>
            ))}
          </select>
          <span style={{ fontSize: "0.75rem", color: "#475569" }}>to</span>
          <select
            value={filter.hourTo}
            onChange={(e) => setFilter((f) => ({ ...f, hourTo: e.target.value }))}
            className="cw-filter-select"
          >
            <option value="all">Any end</option>
            {Array.from({ length: 24 }, (_, i) => (
              <option key={i} value={String(i)}>{String(i).padStart(2, "0")}:59</option>
            ))}
          </select>

          {filter.period === "custom" && (
            <>
              <div className="cw-filter-divider" />
              <input
                type="date"
                value={filter.customFrom}
                onChange={(e) => setFilter((f) => ({ ...f, customFrom: e.target.value }))}
                className="cw-filter-select"
              />
              <span style={{ fontSize: "0.75rem", color: "#475569" }}>to</span>
              <input
                type="date"
                value={filter.customTo}
                onChange={(e) => setFilter((f) => ({ ...f, customTo: e.target.value }))}
                className="cw-filter-select"
              />
            </>
          )}

          <button onClick={resetFilters} className="cw-filter-reset">
            Reset filters
          </button>
        </div>
      )}

      {/* Status bar */}
      {(msg || error) && (
        <div className={`cw-status-bar ${error ? "error" : "success"}`}>
          {error || msg}
        </div>
      )}

      {/* Map + Legend */}
      <div className="cw-map-wrap">
        <CrimeMap
          incidents={incidents}
          hotspots={hotspots}
          routes={showRoutes ? routes : []}
          showIncidents={showIncidents}
          height="100%"
        />

        {/* Legend overlay */}
        <div className="cw-legend">
          <div className="cw-legend-title">
            <Layers size={14} />
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

/**
 * PatrolPage — mirrors prototype app/patrol/page.tsx
 *
 * Layout:
 *  Left:  Leaflet map showing patrol routes
 *  Right: Route list + Run Comparison button + results table + recommendation
 *
 * Wired to:
 *  GET  /api/v1/patrol/routes   — load route geometries
 *  POST /api/v1/patrol/compare  — run comparison
 */
import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import {
  Car, Play, ShieldAlert, Loader2, ArrowLeft,
  CheckCircle2, Route, Star,
} from "lucide-react";
import CrimeMap from "../components/map/CrimeMap";
import { api, getStoredUser, isPatrolAllowed } from "../lib/client";
import { PATROL_ROUTES } from "../lib/crime";

const API = import.meta.env.VITE_API_BASE_URL || "/api/v1";

// Adapt backend route format to CrimeMap format
function adaptRoute(r) {
  // Backend returns waypoints as array of [lat, lng] or {lat, lng}
  const waypoints = (r.waypoints ?? []).map((w) =>
    Array.isArray(w) ? { lat: w[0], lng: w[1] } : w
  );
  return {
    id:       r.id,
    name:     r.name ?? r.label ?? `Route ${r.id}`,
    color:    r.color ?? "#2563eb",
    waypoints,
  };
}

function Row({ label, vals, highlightId, ids }) {
  return (
    <tr>
      <td className="cw-table-dt">{label}</td>
      {vals.map((v, i) => {
        const isBest = ids && highlightId && ids[i] === highlightId;
        return (
          <td key={i} className={isBest ? "cw-table-dd highlight" : "cw-table-dd"}>
            {v}
            {isBest && <Star size={12} style={{ marginLeft: 4, display: "inline", color: "#facc15" }} />}
          </td>
        );
      })}
    </tr>
  );
}

export default function PatrolPage() {
  const navigate  = useNavigate();
  const [allowed, setAllowed]     = useState(null);
  const [routes,  setRoutes]      = useState(PATROL_ROUTES); // default static
  const [comparison, setComparison] = useState(null);
  const [recommended, setRecommended] = useState(null);
  const [loading, setLoading]     = useState(false);
  const [error,   setError]       = useState(null);

  useEffect(() => {
    const ok = isPatrolAllowed(getStoredUser());
    setAllowed(ok);
    if (!ok) return;

    // Try to load routes from backend; fall back to static
    api(`${API}/patrol/routes`)
      .then((r) => {
        const adapted = (r.routes ?? r ?? []).map(adaptRoute).filter((rt) => rt.waypoints.length);
        if (adapted.length) setRoutes(adapted);
      })
      .catch(() => {}); // silent — keep static routes
  }, []);

  async function runComparison() {
    setLoading(true);
    setError(null);
    try {
      const res = await api(`${API}/patrol/compare`, { method: "POST" });
      const cmp = res.comparison ?? res;
      setComparison(Array.isArray(cmp) ? cmp : Object.values(cmp));
      setRecommended(res.recommendedRouteId ?? res.recommended_route_id ?? null);
    } catch (e) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  }

  if (allowed === false) {
    return (
      <div className="cw-access-denied">
        <div className="cw-access-icon-wrap">
          <ShieldAlert size={40} color="#f87171" />
        </div>
        <h1 style={{ fontSize: "1.25rem", fontWeight: 700 }}>Access restricted</h1>
        <p style={{ fontSize: "0.875rem", color: "#94a3b8" }}>
          Patrol route planning is available to officers and admins only.
        </p>
        <button
          onClick={() => navigate("/")}
          className="cw-primary-btn"
        >
          <ArrowLeft size={16} />
          Back to dashboard
        </button>
      </div>
    );
  }

  return (
    <div className="cw-patrol-layout">
      {/* Map */}
      <div className="cw-patrol-map">
        <CrimeMap routes={routes} showIncidents={false} height="100%" />
      </div>

      {/* Right panel */}
      <div className="cw-patrol-panel">
        <h1 className="cw-patrol-title">
          <Route size={20} color="#60a5fa" />
          Patrol Route Planner
        </h1>
        <p className="cw-patrol-sub">
          Compare candidate patrol routes by hotspot &amp; incident coverage.
        </p>

        {/* Route list */}
        <div className="cw-route-list">
          {routes.map((r) => (
            <div key={r.id} className="cw-route-chip">
              <span className="cw-route-color-swatch" style={{ background: r.color }} />
              {r.name}
            </div>
          ))}
        </div>

        {/* Run comparison button */}
        <button
          onClick={runComparison}
          disabled={loading}
          className="cw-primary-btn"
          style={{ width: "100%", justifyContent: "center" }}
        >
          {loading ? <Loader2 size={16} className="cw-spin" /> : <Play size={16} />}
          {loading ? "Comparing…" : "Run Comparison"}
        </button>

        {error && <div className="cw-error-box" style={{ marginTop: "12px" }}>{error}</div>}

        {/* Comparison table */}
        {comparison && (
          <div className="cw-table-wrap">
            <table className="cw-table">
              <thead>
                <tr>
                  <th>Metric</th>
                  {comparison.map((c) => (
                    <th key={c.id}>
                      <span
                        style={{
                          display: "inline-block",
                          width: 8,
                          height: 8,
                          borderRadius: "50%",
                          background: c.color,
                          marginRight: 4,
                          verticalAlign: "middle",
                        }}
                      />
                      {(c.name ?? "").split("—")[0].trim()}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                <Row label="Distance (km)"      vals={comparison.map((c) => c.distanceKm ?? c.distance_km ?? "—")} />
                <Row label="Incidents covered"  vals={comparison.map((c) => c.incidentsCovered ?? c.incidents_covered ?? "—")} />
                <Row label="Hotspots covered"   vals={comparison.map((c) => c.hotspotsCovered ?? c.hotspots_covered ?? "—")} />
                <Row label="Hotspot coverage %" vals={comparison.map((c) => `${c.hotCoveragePct ?? c.hot_coverage_pct ?? "—"}%`)} />
                <Row label="Est. time (min)"    vals={comparison.map((c) => c.estMinutes ?? c.est_minutes ?? "—")} />
                <Row
                  label="Efficiency score"
                  vals={comparison.map((c) => c.efficiencyScore ?? c.efficiency_score ?? "—")}
                  highlightId={recommended}
                  ids={comparison.map((c) => c.id)}
                />
              </tbody>
            </table>
          </div>
        )}

        {/* Recommended banner */}
        {recommended && comparison && (
          <div className="cw-recommended">
            <CheckCircle2 size={16} style={{ flexShrink: 0, marginTop: 2, color: "#4ade80" }} />
            <span>
              Recommended:{" "}
              <b>{comparison.find((c) => c.id === recommended)?.name}</b>{" "}
              offers the best coverage-to-distance efficiency.
            </span>
          </div>
        )}
      </div>
    </div>
  );
}

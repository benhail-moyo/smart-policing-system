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
import { useAppContext } from "../store/AppContext";
import { buildDashboardDataset } from "../lib/dataset";

const baseDataset = buildDashboardDataset([], [], null);
const dijkstraRoute = {
  id: "dijkstra",
  label: "Dijkstra",
  distanceKm: 14.2,
  fuelLitres: 3.4,
  timeMinutes: 48,
  computeMs: 124,
  waypoints: baseDataset.route.dijkstra.waypoints,
};

const geneticRoute = {
  id: "genetic",
  label: "Genetic Algorithm",
  distanceKm: 12.8,
  fuelLitres: 2.7,
  timeMinutes: 54,
  computeMs: 318,
  waypoints: baseDataset.route.genetic.waypoints,
};

export default function PatrolPage() {
  const { setRoute, hotspots, incidents } = useAppContext();

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

      <div className="map-shell">
        <CrimeMap hotspots={hotspots} incidents={incidents} patrolRoute={{ dijkstra: dijkstraRoute, genetic: geneticRoute }} />
      </div>
    </div>
  );
}
